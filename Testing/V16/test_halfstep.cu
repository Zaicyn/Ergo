// test_halfstep.cu - Quick V16 half-step pattern verification
#include <stdio.h>
#include <cuda_runtime.h>

#define V16_EXCLUSIVE_CAP 24
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

int main() {
    printf("\n╔═══════════════════════════════════════════════════════════════════╗\n");
    printf("║     V16 HALF-STEP PATTERN TEST (0010 ↔ 1000)                      ║\n");
    printf("╚═══════════════════════════════════════════════════════════════════╝\n\n");
    
    V16_SlabContext ctx;
    v16_slab_init(&ctx, 64);
    
    V16_SlabPool* d_pool;
    cudaMalloc(&d_pool, sizeof(V16_SlabPool));
    cudaMemcpy(d_pool, &ctx.pool, sizeof(V16_SlabPool), cudaMemcpyHostToDevice);
    
    uint32_t* d_success;
    cudaMalloc(&d_success, sizeof(uint32_t));
    
    // Test with various warp counts
    struct { const char* name; int blocks; int threads; } tests[] = {
        {"32 warps (shared mode)", 4, 256},
        {"64 warps (shared mode)", 8, 256},
        {"128 warps (shared mode)", 16, 256},
    };
    
    for (int t = 0; t < 3; t++) {
        printf("━━━ %s ━━━\n", tests[t].name);
        v16_slab_reset(&ctx);
        cudaMemset(d_success, 0, sizeof(uint32_t));
        cudaMemcpy(d_pool, &ctx.pool, sizeof(V16_SlabPool), cudaMemcpyHostToDevice);
        
        test_kernel<<<tests[t].blocks, tests[t].threads>>>(d_pool, 1000, d_success);
        cudaDeviceSynchronize();
        
        uint32_t h_success;
        cudaMemcpy(&h_success, d_success, sizeof(uint32_t), cudaMemcpyDeviceToHost);
        
        V16_SlabStats s = v16_slab_stats(&ctx);
        v16_slab_print_stats(&s);
        
        uint64_t total_allocs = 0, total_contention = 0;
        for (int c = 0; c < V16_SLAB_CLASSES; c++) {
            total_allocs += s.allocs[c];
            total_contention += s.contention[c];
        }
        
        printf("\n  Total: %llu allocs, %llu contention events\n\n",
               (unsigned long long)total_allocs, (unsigned long long)total_contention);
    }
    
    cudaFree(d_success);
    cudaFree(d_pool);
    v16_slab_destroy(&ctx);
    
    return 0;
}
