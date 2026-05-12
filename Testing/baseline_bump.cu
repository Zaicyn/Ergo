/*
 * baseline_bump.cu — GPU bump-allocator floor measurements.
 *
 * Establishes two "do nothing" GPU allocation floors. Both kernels do the
 * same fundamental operation — atomicAdd on a global counter, return a
 * pointer — but differ in whether nvcc applies warp aggregation:
 *
 *   Floor A (warp-aggregated): all 32 lanes in a warp request the same
 *     allocation size, so nvcc rewrites the per-lane atomicAdd into one
 *     per-warp atomicAdd of (popcount(activemask) * size), then broadcasts
 *     the base back to all lanes. SASS pattern: VOTEU.ANY + UPOPC + one
 *     ATOM.E.ADD per warp. This is what V8 achieves manually through its
 *     warp-cooperative design.
 *
 *   Floor B (non-aggregated): per-lane allocation sizes vary, defeating
 *     the warp-aggregation fold. SASS pattern: ATOM.E.ADD per lane in the
 *     loop body. This is the "30K lanes hammering one counter" worst case
 *     that V8's geometric design exists to escape.
 *
 * Reporting both floors lets the comparison table say:
 *   - V8 sits between Floor B (escapes worst case) and Floor A (matches
 *     the compiler-aggregated ceiling for one-counter bump).
 *   - V8's geometry buys you the slab structure (size classes,
 *     recycling) at no per-lane cost beyond Floor A.
 *
 * Methodology (matches V8's micro-bench geometry exactly so the numbers are
 * directly comparable):
 *   - 256 blocks × 256 threads = 65,536 launched threads.
 *     RTX 2060 runs ~30,720 concurrent (30 SMs × 32 warps × 32 lanes).
 *   - 1000 alloc cycles per lane in the inner kernel loop.
 *   - No frees — bump-only floor measurement. V8's bench does alloc+free in
 *     pairs; we measure alloc cost in isolation, which is the floor.
 *   - 5 repetitions. Counter reset to 0 between reps.
 *   - 1 GB device arena, wrapping when full.
 *   - __launch_bounds__(256, 3) to match V8's measured kernel exactly.
 *
 * For Floor B (non-aggregated), per-lane sizes vary as
 *   sz = 64 + (lane_id & 7) * 8  ∈ {64, 72, 80, ..., 120}
 * This produces 8 distinct sizes across the warp; the compiler cannot fold
 * the warp's atomicAdds into one because the sum depends on which lanes are
 * active. Throughput is reported as (total-bytes-allocated / time / 64) to
 * give a "64-byte-equivalent allocations per second" number that's
 * comparable to V8 and Floor A. The conversion is conservative: real
 * average size per lane is (64+72+...+120)/8 = 92, so dividing total bytes
 * by 64 slightly overstates the equivalent alloc count, making Floor B
 * look ~1.4× faster than it would if all sizes were 64. Document at use
 * site.
 *
 * Build: nvcc -arch=sm_75 -O3 baseline_bump.cu -o baseline_bump
 *        (-arch=sm_75 matches RTX 2060; adjust for other GPUs but report it)
 */

#include <cuda_runtime.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#define CUDA_CHECK(call) do { cudaError_t _e=(call);                    \
    if(_e!=cudaSuccess){fprintf(stderr,"CUDA %s:%d %s\n",              \
    __FILE__,__LINE__,cudaGetErrorString(_e));exit(1);} } while(0)

#define ARENA_BYTES   (1ULL << 30)   /* 1 GB */
#define ALLOC_SIZE    64
#define ITERS         1000

__device__ unsigned long long d_offset = 0;
__device__ char               d_arena[ARENA_BYTES];

__device__ __forceinline__ void* gpu_bump_alloc(size_t sz) {
    unsigned long long p = atomicAdd(&d_offset, (unsigned long long)sz);
    /* Wrap so we don't overflow on long runs. The wrap is racy under
     * contention but it doesn't matter — this is a floor measurement, not a
     * correctness benchmark. The bump cost is unaffected. */
    if (p + sz > ARENA_BYTES) {
        atomicExch(&d_offset, 0ULL);
        p = 0;
    }
    return (void*)(d_arena + p);
}

/* Floor A: warp-aggregated. All lanes call gpu_bump_alloc(64) — nvcc
 * detects the uniform size and folds the per-lane atomicAdds into one
 * per-warp atomicAdd. SASS will show VOTEU.ANY + UPOPC + one ATOM.E.ADD.
 */
__global__ __launch_bounds__(256, 3)
void bump_stress_aggregated(uint32_t iters, uint32_t* d_cnt,
                             unsigned long long* d_total_bytes) {
    uint32_t local_n = 0;
    uintptr_t local_sink = 0;
    for (uint32_t i = 0; i < iters; i++) {
        void* p = gpu_bump_alloc(ALLOC_SIZE);
        local_sink ^= (uintptr_t)p;
        local_n++;
    }
    atomicMax((unsigned long long*)d_cnt, (unsigned long long)local_sink);
    atomicAdd(d_cnt + 1, local_n);
    atomicAdd(d_total_bytes, (unsigned long long)local_n * ALLOC_SIZE);
}

/* Floor B: non-aggregated. Per-lane size varies by lane_id & 7 → eight
 * distinct sizes across the warp. The per-warp sum depends on the active
 * mask AND the per-lane sizes, so the compiler cannot precompute it as
 * popc(active) * const — it falls back to per-lane atomicAdd. SASS will
 * show ATOM.E.ADD per lane in the loop body, with no VOTEU/UPOPC folding.
 */
__global__ __launch_bounds__(256, 3)
void bump_stress_nonaggregated(uint32_t iters, uint32_t* d_cnt,
                                unsigned long long* d_total_bytes) {
    uint32_t lane = threadIdx.x & 31u;
    uint32_t my_sz = ALLOC_SIZE + (lane & 7u) * 8u;  /* {64, 72, 80, ..., 120} */
    uint32_t local_n = 0;
    uintptr_t local_sink = 0;
    unsigned long long local_bytes = 0;
    for (uint32_t i = 0; i < iters; i++) {
        void* p = gpu_bump_alloc(my_sz);
        local_sink ^= (uintptr_t)p;
        local_bytes += my_sz;
        local_n++;
    }
    atomicMax((unsigned long long*)d_cnt, (unsigned long long)local_sink);
    atomicAdd(d_cnt + 1, local_n);
    atomicAdd(d_total_bytes, local_bytes);
}

typedef void (*kernel_fn)(uint32_t, uint32_t*, unsigned long long*);

static void run_floor(const char* name, kernel_fn k, int normalize_by_64) {
    printf("--- %s ---\n", name);

    uint32_t* d_cnt;
    unsigned long long* d_total_bytes;
    CUDA_CHECK(cudaMalloc((void**)&d_cnt, 2 * sizeof(uint32_t)));
    CUDA_CHECK(cudaMalloc((void**)&d_total_bytes, sizeof(unsigned long long)));

    cudaEvent_t t0, t1;
    CUDA_CHECK(cudaEventCreate(&t0));
    CUDA_CHECK(cudaEventCreate(&t1));

    for (int rep = 0; rep < 5; rep++) {
        unsigned long long zero = 0;
        CUDA_CHECK(cudaMemcpyToSymbol(d_offset, &zero, sizeof(zero)));
        CUDA_CHECK(cudaMemset(d_cnt, 0, 2 * sizeof(uint32_t)));
        CUDA_CHECK(cudaMemset(d_total_bytes, 0, sizeof(unsigned long long)));
        CUDA_CHECK(cudaDeviceSynchronize());

        CUDA_CHECK(cudaEventRecord(t0));
        k<<<256, 256>>>(ITERS, d_cnt, d_total_bytes);
        CUDA_CHECK(cudaEventRecord(t1));
        CUDA_CHECK(cudaEventSynchronize(t1));

        float ms = 0.f;
        CUDA_CHECK(cudaEventElapsedTime(&ms, t0, t1));
        uint32_t cnt[2] = {0, 0};
        unsigned long long total_bytes = 0;
        CUDA_CHECK(cudaMemcpy(cnt, d_cnt, 2 * sizeof(uint32_t),
                              cudaMemcpyDeviceToHost));
        CUDA_CHECK(cudaMemcpy(&total_bytes, d_total_bytes,
                              sizeof(unsigned long long),
                              cudaMemcpyDeviceToHost));

        double secs   = ms / 1000.0;
        uint64_t allocs = (uint64_t)cnt[1];
        /* For the non-aggregated floor, report a 64-byte-equivalent rate
         * by dividing total bytes allocated by 64. For the aggregated
         * floor (all sizes are 64), this equals allocs exactly. */
        uint64_t eq_allocs = normalize_by_64 ? (total_bytes / 64) : allocs;
        double mps    = (double)eq_allocs / secs / 1.0e6;
        double ns     = (secs * 1.0e9) / (double)eq_allocs;
        printf("rep %d: %lu lane-allocs, %lu bytes in %.4f s = %7.1f M 64B-eq/s, %5.2f ns/64B-eq\n",
               rep, (unsigned long)allocs, (unsigned long)total_bytes,
               secs, mps, ns);
    }

    cudaEventDestroy(t0);
    cudaEventDestroy(t1);
    cudaFree(d_cnt);
    cudaFree(d_total_bytes);
    printf("\n");
}

int main(void) {
    cudaDeviceProp prop; cudaGetDeviceProperties(&prop, 0);
    printf("GPU: %s | SM %d.%d | %d SMs | %.1f GB\n",
           prop.name, prop.major, prop.minor, prop.multiProcessorCount,
           prop.totalGlobalMem / 1e9);
    printf("Geometry: 256 blocks × 256 threads, 1000 iters/lane, 5 reps\n");
    printf("Kernel: __launch_bounds__(256, 3), single global atomicAdd counter\n\n");

    run_floor("Floor A: warp-aggregated (uniform 64B → nvcc folds per-warp)",
              bump_stress_aggregated, 1);
    run_floor("Floor B: non-aggregated (per-lane sz=64+(lane&7)*8 defeats fold)",
              bump_stress_nonaggregated, 1);

    return 0;
}
