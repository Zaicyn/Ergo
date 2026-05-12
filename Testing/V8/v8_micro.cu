// v8_micro.cu — V8 steady-state throughput micro-benchmark.
//
// Companion to aizawa_slab_test.cu, which runs a full 5-test suite.
// This file isolates the throughput hot path so the 1.9 G/s number cited in
// Testing/V8_VS_V22_HEAD_TO_HEAD.md is reproducible from the in-tree source.
//
// Methodology (matches the original micro-benchmark exactly):
//   - 256 blocks × 256 threads = 65,536 launched threads.
//     RTX 2060 runs ~30,720 of them truly concurrent (30 SMs × 32 warps × 32 lanes).
//   - 1000 alloc/free cycles per lane in the inner kernel loop.
//   - 5 repetitions. Pool state is reset (zeroed) between reps so each rep
//     starts from a known cold-pool state; rep 0 is cold-L2/cold-Viviani-scatter,
//     reps 2–4 are the reported steady-state numbers.
//   - __launch_bounds__(256, 3) per the launch-bounds experiment finding.
//
// Build: nvcc -arch=sm_75 -O3 -I. v8_micro.cu -o v8_micro
//        (-arch=sm_75 matches RTX 2060; adjust for other GPUs but report it)
//
// The kernel body is byte-identical to slab_stress_kernel in aizawa_slab_test.cu;
// only the launch-bounds annotation and the timing harness differ. Keeping
// the kernel definitions in sync is a manual responsibility — if the test
// suite's kernel changes, this one should too.

#include <cuda_runtime.h>
#include <cooperative_groups.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "aizawa.cuh"
#include "aizawa_slab.cuh"

#define CUDA_CHECK(call) do { cudaError_t _e=(call);                    \
    if(_e!=cudaSuccess){fprintf(stderr,"CUDA %s:%d %s\n",              \
    __FILE__,__LINE__,cudaGetErrorString(_e));exit(1);} } while(0)

__global__ __launch_bounds__(256, 3)
void slab_stress_micro_kernel(SlabPool* pool, uint32_t iters,
                              uint32_t* d_cnt) {
    const uint32_t warps_per_block = blockDim.x / 32u;
    const uint32_t warp_id         = threadIdx.x / 32u;

    extern __shared__ uint32_t smem[];
    uint32_t* warp_sb_base   = smem + warp_id * SLAB_CLASSES;
    uint32_t* warp_sb_cursor = smem + warps_per_block * SLAB_CLASSES
                                    + warp_id * SLAB_CLASSES;

    if ((threadIdx.x & 31u) == 0) {
        for (int c = 0; c < SLAB_CLASSES; c++) {
            warp_sb_base[c]   = 0xFFFFFFFFu;
            warp_sb_cursor[c] = 0;
        }
    }
    __syncthreads();

    void*    held[4] = {nullptr}; int hcls[4] = {0};
    int      hcnt = 0; uint32_t local_n = 0;
    uint32_t global_warp_id = blockIdx.x * warps_per_block + warp_id;

    for (uint32_t i = 0; i < iters; i++) {
        int c = (int)((global_warp_id + i) % (uint32_t)SLAB_CLASSES);
        void* ptr = viviani_slab_alloc(pool, c,
                                        &warp_sb_base[c],
                                        &warp_sb_cursor[c]);
        if (ptr) {
            local_n++;
            if (hcnt < 4) {
                held[hcnt] = ptr; hcls[hcnt] = c; hcnt++;
            } else {
                viviani_slab_free(pool, held[0], hcls[0]);
                for (int j = 0; j < 3; j++) { held[j]=held[j+1]; hcls[j]=hcls[j+1]; }
                held[3] = ptr; hcls[3] = c;
            }
        }
    }
    for (int j = 0; j < hcnt; j++)
        if (held[j]) viviani_slab_free(pool, held[j], hcls[j]);
    atomicAdd(d_cnt, local_n);
}

int main(void) {
    cudaDeviceProp prop; cudaGetDeviceProperties(&prop,0);
    printf("GPU: %s | SM %d.%d | %d SMs | %.1f GB\n",
           prop.name,prop.major,prop.minor,prop.multiProcessorCount,
           prop.totalGlobalMem/1e9);
    printf("Geometry: 256 blocks × 256 threads, 1000 iters/lane, 5 reps\n");
    printf("Kernel: __launch_bounds__(256, 3)\n\n");

    VivianiSlabContext ctx;
    cudaError_t err = viviani_slab_init(&ctx, SLAB_POOL_DEPTH);
    if (err != cudaSuccess) {
        fprintf(stderr, "FATAL slab_init: %s\n", cudaGetErrorString(err));
        return 1;
    }

    uint32_t* d_cnt;
    CUDA_CHECK(cudaMalloc((void**)&d_cnt, sizeof(uint32_t)));
    size_t smem_sz = 2u * (256u/32u) * (size_t)SLAB_CLASSES * sizeof(uint32_t);

    cudaEvent_t t0, t1;
    CUDA_CHECK(cudaEventCreate(&t0));
    CUDA_CHECK(cudaEventCreate(&t1));

    for (int rep = 0; rep < 5; rep++) {
        viviani_slab_reset(&ctx);
        CUDA_CHECK(cudaMemset(d_cnt, 0, sizeof(uint32_t)));
        CUDA_CHECK(cudaDeviceSynchronize());

        CUDA_CHECK(cudaEventRecord(t0));
        slab_stress_micro_kernel<<<256, 256, smem_sz>>>(&ctx.pool, 1000, d_cnt);
        CUDA_CHECK(cudaEventRecord(t1));
        CUDA_CHECK(cudaEventSynchronize(t1));

        float ms = 0.f;
        CUDA_CHECK(cudaEventElapsedTime(&ms, t0, t1));
        uint32_t allocs = 0;
        CUDA_CHECK(cudaMemcpy(&allocs, d_cnt, sizeof(uint32_t),
                              cudaMemcpyDeviceToHost));

        double secs = ms / 1000.0;
        double mps  = (double)allocs / secs / 1.0e6;
        double ns   = (secs * 1.0e9) / (double)allocs;
        printf("rep %d: %u allocs in %.4f s = %.1f M/s, %.2f ns/alloc\n",
               rep, allocs, secs, mps, ns);
    }

    cudaEventDestroy(t0);
    cudaEventDestroy(t1);
    cudaFree(d_cnt);
    return 0;
}
