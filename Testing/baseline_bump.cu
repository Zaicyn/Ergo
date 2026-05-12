/*
 * baseline_bump.cu — GPU bump-allocator floor measurement (initial version).
 *
 * Establishes the "do nothing" baseline for GPU allocation cost. The hot path
 * is a single atomicAdd on a global 64-bit counter; every lane in the warp
 * requests the same 64B allocation size.
 *
 * NOTE on methodology — read before interpreting the numbers:
 *
 * nvcc 13.1 with sm_75 applies *warp aggregation* automatically when all
 * lanes in a warp request the same uniform allocation size. SASS shows
 * VOTEU.ANY + UPOPC + one @P0 ATOMG.E.ADD per warp, with the result
 * broadcast to all lanes. That means this kernel measures ~one atomic
 * per warp, not per lane. The reported per-lane cost is the warp cost
 * divided by 32.
 *
 * This is *a* legitimate floor (matches what nvcc emits for compiler-
 * aggregated bump), but it's not the per-lane-contention floor — V8's
 * actual comparison point. The non-aggregated floor (where per-lane
 * sizes vary to defeat the fold) is added in a subsequent commit.
 *
 * Methodology (matches V8's micro-bench geometry exactly so the numbers are
 * directly comparable):
 *   - 256 blocks × 256 threads = 65,536 launched threads.
 *     RTX 2060 runs ~30,720 concurrent (30 SMs × 32 warps × 32 lanes).
 *   - 1000 alloc cycles per lane in the inner kernel loop.
 *   - No frees — bump-only floor measurement.
 *   - 5 repetitions. Counter reset to 0 between reps.
 *   - 1 GB device arena, wrapping when full.
 *   - __launch_bounds__(256, 3) to match V8's measured kernel exactly.
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
    if (p + sz > ARENA_BYTES) {
        atomicExch(&d_offset, 0ULL);
        p = 0;
    }
    return (void*)(d_arena + p);
}

__global__ __launch_bounds__(256, 3)
void bump_stress_kernel(uint32_t iters, uint32_t* d_cnt) {
    uint32_t local_n = 0;
    uintptr_t local_sink = 0;
    for (uint32_t i = 0; i < iters; i++) {
        void* p = gpu_bump_alloc(ALLOC_SIZE);
        local_sink ^= (uintptr_t)p;
        local_n++;
    }
    atomicMax((unsigned long long*)d_cnt, (unsigned long long)local_sink);
    atomicAdd(d_cnt + 1, local_n);
}

int main(void) {
    cudaDeviceProp prop; cudaGetDeviceProperties(&prop, 0);
    printf("GPU: %s | SM %d.%d | %d SMs | %.1f GB\n",
           prop.name, prop.major, prop.minor, prop.multiProcessorCount,
           prop.totalGlobalMem / 1e9);
    printf("Geometry: 256 blocks × 256 threads, 1000 iters/lane, 5 reps\n");
    printf("Kernel: __launch_bounds__(256, 3), single global atomicAdd counter\n");
    printf("NOTE: nvcc warp-aggregates per-warp; this measures the aggregated floor.\n\n");

    uint32_t* d_cnt;
    CUDA_CHECK(cudaMalloc((void**)&d_cnt, 2 * sizeof(uint32_t)));

    cudaEvent_t t0, t1;
    CUDA_CHECK(cudaEventCreate(&t0));
    CUDA_CHECK(cudaEventCreate(&t1));

    for (int rep = 0; rep < 5; rep++) {
        unsigned long long zero = 0;
        CUDA_CHECK(cudaMemcpyToSymbol(d_offset, &zero, sizeof(zero)));
        CUDA_CHECK(cudaMemset(d_cnt, 0, 2 * sizeof(uint32_t)));
        CUDA_CHECK(cudaDeviceSynchronize());

        CUDA_CHECK(cudaEventRecord(t0));
        bump_stress_kernel<<<256, 256>>>(ITERS, d_cnt);
        CUDA_CHECK(cudaEventRecord(t1));
        CUDA_CHECK(cudaEventSynchronize(t1));

        float ms = 0.f;
        CUDA_CHECK(cudaEventElapsedTime(&ms, t0, t1));
        uint32_t cnt[2] = {0, 0};
        CUDA_CHECK(cudaMemcpy(cnt, d_cnt, 2 * sizeof(uint32_t),
                              cudaMemcpyDeviceToHost));

        double secs   = ms / 1000.0;
        uint64_t allocs = (uint64_t)cnt[1];
        double mps    = (double)allocs / secs / 1.0e6;
        double ns     = (secs * 1.0e9) / (double)allocs;
        printf("rep %d: %lu allocs in %.4f s = %7.1f M/s, %5.2f ns/alloc\n",
               rep, (unsigned long)allocs, secs, mps, ns);
    }

    cudaEventDestroy(t0);
    cudaEventDestroy(t1);
    cudaFree(d_cnt);
    return 0;
}
