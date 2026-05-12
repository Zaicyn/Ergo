// minimal_slab_test.cu - Minimal test to isolate hang
#include <stdio.h>
#include <cuda_runtime.h>

#include "V8/aizawa.cuh"
#include "V8/aizawa_slab.cuh"
// V9 not included - testing V8 only

__global__ void simple_kernel(SlabPool* pool, uint32_t iters, uint32_t* success_count) {
    uint32_t sb_base[SLAB_CLASSES];
    uint32_t sb_cursor[SLAB_CLASSES];

    for (int c = 0; c < SLAB_CLASSES; c++) {
        sb_base[c] = 0xFFFFFFFFu;
        sb_cursor[c] = 0;
    }

    uint32_t tid = blockIdx.x * blockDim.x + threadIdx.x;
    uint32_t local_success = 0;

    void* held[SLAB_CLASSES] = {nullptr};

    // Multiple iterations like the stress test
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

int main() {
    printf("Minimal V8 slab test\n");
    fflush(stdout);

    int device;
    cudaGetDevice(&device);
    cudaDeviceProp props;
    cudaGetDeviceProperties(&props, device);
    printf("GPU: %s\n", props.name);
    fflush(stdout);

    // Try pool 128
    const uint32_t pool_depth = 65;
    printf("Pool depth: %u (%u MB per class)\n",
           pool_depth, pool_depth * 4096 / 1024 / 1024);
    fflush(stdout);

    VivianiSlabContext ctx;
    printf("Initializing...\n"); fflush(stdout);
    cudaError_t err = viviani_slab_init(&ctx, pool_depth);
    if (err != cudaSuccess) {
        printf("Init failed: %s\n", cudaGetErrorString(err));
        return 1;
    }
    printf("Init OK\n"); fflush(stdout);

    uint32_t* d_success;
    cudaMalloc((void**)&d_success, sizeof(uint32_t));
    cudaMemset(d_success, 0, sizeof(uint32_t));

    // Test with 64 threads like v8_only_test
    printf("Launching 1 block x 64 threads x 10 iters...\n"); fflush(stdout);
    simple_kernel<<<1, 64>>>(&ctx.pool, 10, d_success);
    err = cudaDeviceSynchronize();
    if (err != cudaSuccess) {
        printf("Kernel failed: %s\n", cudaGetErrorString(err));
    } else {
        printf("Kernel completed\n"); fflush(stdout);
    }

    uint32_t success = 0;
    cudaMemcpy(&success, d_success, sizeof(uint32_t), cudaMemcpyDeviceToHost);
    printf("Success count: %u\n", success);

    cudaFree(d_success);
    viviani_slab_destroy(&ctx);
    printf("Done\n");
    return 0;
}
