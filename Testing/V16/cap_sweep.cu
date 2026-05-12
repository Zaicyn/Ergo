// cap_sweep.cu - V16 CAP sensitivity sweep
#include <stdio.h>
#include <stdint.h>
#include <cuda_runtime.h>

#define TEST_POOL_DEPTH 64
#define TEST_ITERS 100

typedef struct {
    float time_ms;
    float throughput;
    uint64_t contention;
    uint32_t exclusive_count;
} Result;

#include "viviani_v16_gpu.cuh"

__global__ void test_kernel(V16_SlabPool* pool, uint32_t iters, uint32_t* success) {
    uint32_t sb_base[V16_SLAB_CLASSES], sb_cursor[V16_SLAB_CLASSES];
    for (int c = 0; c < V16_SLAB_CLASSES; c++) { sb_base[c] = 0xFFFFFFFFu; sb_cursor[c] = 0; }

    uint32_t tid = blockIdx.x * blockDim.x + threadIdx.x;
    uint32_t local_success = 0;
    void* held[V16_SLAB_CLASSES] = {nullptr};

    for (uint32_t i = 0; i < iters; i++) {
        int cls = (tid + i) % V16_SLAB_CLASSES;
        if (held[cls]) { v16_slab_free(pool, held[cls], cls); held[cls] = nullptr; }
        void* ptr = v16_slab_alloc(pool, cls, &sb_base[cls], &sb_cursor[cls]);
        if (ptr) { *((volatile uint8_t*)ptr) = (uint8_t)(tid ^ i); held[cls] = ptr; local_success++; }
    }
    for (int c = 0; c < V16_SLAB_CLASSES; c++) if (held[c]) v16_slab_free(pool, held[c], c);
    atomicAdd(success, local_success);
}

Result run_benchmark(int blocks, int threads) {
    Result r = {0};
    
    V16_SlabContext ctx;
    v16_slab_init(&ctx, TEST_POOL_DEPTH);
    
    V16_SlabPool* d_pool;
    cudaMalloc(&d_pool, sizeof(V16_SlabPool));
    cudaMemcpy(d_pool, &ctx.pool, sizeof(V16_SlabPool), cudaMemcpyHostToDevice);
    
    uint32_t* d_success;
    cudaMalloc(&d_success, sizeof(uint32_t));
    cudaMemset(d_success, 0, sizeof(uint32_t));
    
    cudaEvent_t start, stop;
    cudaEventCreate(&start);
    cudaEventCreate(&stop);
    
    // Warmup
    test_kernel<<<blocks, threads>>>(d_pool, TEST_ITERS, d_success);
    cudaDeviceSynchronize();
    
    v16_slab_reset(&ctx);
    cudaMemcpy(d_pool, &ctx.pool, sizeof(V16_SlabPool), cudaMemcpyHostToDevice);
    cudaMemset(d_success, 0, sizeof(uint32_t));
    
    // Timed run
    cudaEventRecord(start);
    test_kernel<<<blocks, threads>>>(d_pool, TEST_ITERS, d_success);
    cudaEventRecord(stop);
    cudaEventSynchronize(stop);
    cudaEventElapsedTime(&r.time_ms, start, stop);
    
    V16_SlabStats stats = v16_slab_stats(&ctx);
    for (int c = 0; c < V16_SLAB_CLASSES; c++) {
        r.contention += stats.contention[c];
        r.exclusive_count += stats.exclusive_mode_count[c];
    }
    
    uint64_t total = (uint64_t)blocks * threads * TEST_ITERS;
    r.throughput = (float)total / (r.time_ms / 1000.0f) / 1e6f;
    
    cudaFree(d_success);
    cudaFree(d_pool);
    cudaEventDestroy(start);
    cudaEventDestroy(stop);
    v16_slab_destroy(&ctx);
    
    return r;
}

int main() {
    printf("\nTesting CAP=%d:\n", V16_EXCLUSIVE_CAP);
    printf("┌─────────────┬────────────┬────────────┬────────────┐\n");
    printf("│ Scenario    │ Tput (M/s) │ Contention │ Exclusive  │\n");
    printf("├─────────────┼────────────┼────────────┼────────────┤\n");
    
    struct { const char* name; int blocks; int threads; } scenarios[] = {
        {"2 warps",   1,   64},
        {"8 warps",   2,  128},
        {"16 warps",  4,  128},
        {"32 warps",  4,  256},
        {"64 warps",  8,  256},
        {"128 warps", 16, 256},
        {"256 warps", 32, 256},
    };
    int num = sizeof(scenarios) / sizeof(scenarios[0]);
    
    float total_tput = 0;
    uint64_t total_cont = 0;
    uint32_t total_excl = 0;
    
    for (int i = 0; i < num; i++) {
        Result r = run_benchmark(scenarios[i].blocks, scenarios[i].threads);
        printf("│ %-11s │ %10.1f │ %10llu │ %10u │\n",
               scenarios[i].name, r.throughput, 
               (unsigned long long)r.contention, r.exclusive_count);
        total_tput += r.throughput;
        total_cont += r.contention;
        total_excl += r.exclusive_count;
    }
    
    printf("├─────────────┼────────────┼────────────┼────────────┤\n");
    printf("│ AVERAGE     │ %10.1f │ %10llu │ %10u │\n",
           total_tput / num, (unsigned long long)(total_cont / num), total_excl / num);
    printf("└─────────────┴────────────┴────────────┴────────────┘\n");
    
    return 0;
}
