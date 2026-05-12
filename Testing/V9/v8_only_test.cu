// v8_only_test.cu - Test V8 allocator only
#include <stdio.h>
#include <cuda_runtime.h>

#include "V8/aizawa.cuh"
#include "V8/aizawa_slab.cuh"

#define TEST_POOL_DEPTH 72

__global__ void stress_kernel(SlabPool* pool, uint32_t iters, uint32_t* success_count) {
    uint32_t sb_base[SLAB_CLASSES];
    uint32_t sb_cursor[SLAB_CLASSES];

    for (int c = 0; c < SLAB_CLASSES; c++) {
        sb_base[c] = 0xFFFFFFFFu;
        sb_cursor[c] = 0;
    }

    uint32_t tid = blockIdx.x * blockDim.x + threadIdx.x;
    uint32_t local_success = 0;
    void* held[SLAB_CLASSES] = {nullptr};

    for (uint32_t i = 0; i < iters; i++) {
        int cls = (tid + i) % SLAB_CLASSES;

        if (held[cls]) {
            viviani_slab_free(pool, held[cls], cls);
            held[cls] = nullptr;
        }

        void* ptr = viviani_slab_alloc(pool, cls, &sb_base[cls], &sb_cursor[cls]);
        if (ptr) {
            *((volatile uint8_t*)ptr) = (uint8_t)(tid ^ i);
            held[cls] = ptr;
            local_success++;
        }
    }

    for (int c = 0; c < SLAB_CLASSES; c++) {
        if (held[c]) viviani_slab_free(pool, held[c], c);
    }

    atomicAdd(success_count, local_success);
}

typedef struct {
    float time_ms;
    uint64_t allocs;
    float throughput_mops;
} BenchResult;

BenchResult benchmark(uint32_t blocks, uint32_t threads_per_block, uint32_t iters) {
    BenchResult result = {0};

    VivianiSlabContext ctx;
    cudaError_t err = viviani_slab_init(&ctx, TEST_POOL_DEPTH);
    if (err != cudaSuccess) {
        printf("Init failed: %s\n", cudaGetErrorString(err));
        return result;
    }
    cudaDeviceSynchronize();

    uint32_t* d_success;
    cudaMalloc((void**)&d_success, sizeof(uint32_t));

    // Skip warmup for debugging

    // Benchmark
    cudaMemset(d_success, 0, sizeof(uint32_t));

    stress_kernel<<<blocks, threads_per_block>>>(&ctx.pool, iters, d_success);
    cudaDeviceSynchronize();

    float ms = 1.0f;  // placeholder

    uint32_t success = 0;
    cudaMemcpy(&success, d_success, sizeof(uint32_t), cudaMemcpyDeviceToHost);

    uint64_t total_ops = (uint64_t)blocks * threads_per_block * iters;
    result.time_ms = ms;
    result.allocs = success;
    result.throughput_mops = (float)total_ops / (ms / 1000.0f) / 1e6f;

    cudaFree(d_success);
    viviani_slab_destroy(&ctx);

    return result;
}

int main() {
    printf("V8 Only Test\n");

    int device;
    cudaGetDevice(&device);
    cudaDeviceProp props;
    cudaGetDeviceProperties(&props, device);
    printf("GPU: %s\n", props.name);

    // Single test
    printf("Running single test: 2 warps (64 threads), 10 iters\n"); fflush(stdout);
    BenchResult r = benchmark(1, 64, 10);
    printf("Result: %.2f ms, %llu allocs\n", r.time_ms, (unsigned long long)r.allocs);

    printf("Test complete!\n");
    return 0;
}
