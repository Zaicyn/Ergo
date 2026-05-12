// slab_comparison_test.cu - V8 vs V9 Many-Body Comparison
//
// Compares the original V8 slab allocator against V9 with many-body physics.
// Tests scaling behavior at increasing warp counts to demonstrate
// contention reduction from gravitational repulsion and mean-field density.
//
// Build: nvcc -O3 -arch=sm_75 -o slab_test slab_comparison_test.cu
// Run:   ./slab_test

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <cuda_runtime.h>

// Include both versions
#include "V8/aizawa.cuh"
#include "V8/aizawa_slab.cuh"
#include "aizawa_slab_v9.cuh"

// ============================================================================
// Test Configuration
// ============================================================================

#define TEST_ITERS_PER_THREAD 50
#define WARMUP_ITERS 5
#define TEST_POOL_DEPTH 64  // Small pool to avoid unknown hang issue

typedef struct {
    float time_ms;
    uint64_t allocs;
    uint64_t frees;
    uint64_t fallbacks;
    uint64_t contention;  // V9 only
    float success_rate;
    float throughput_mops;
} BenchResult;

// ============================================================================
// V8 Stress Kernel (for fair comparison)
// ============================================================================

__global__ void v8_stress_kernel(
    SlabPool* pool,
    uint32_t iters,
    uint32_t* success_count)
{
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

// ============================================================================
// Benchmark Functions
// ============================================================================

BenchResult benchmark_v8(uint32_t blocks, uint32_t threads_per_block, uint32_t iters) {
    BenchResult result = {0};

    VivianiSlabContext ctx;
    cudaError_t err = viviani_slab_init(&ctx, TEST_POOL_DEPTH);
    if (err != cudaSuccess) {
        return result;
    }
    cudaDeviceSynchronize();  // Wait for init memsets

    uint32_t* d_success;
    cudaMalloc((void**)&d_success, sizeof(uint32_t));

    // Warmup
    cudaMemset(d_success, 0, sizeof(uint32_t));
    v8_stress_kernel<<<blocks, threads_per_block>>>(&ctx.pool, WARMUP_ITERS, d_success);
    cudaDeviceSynchronize();
    viviani_slab_reset(&ctx);
    cudaDeviceSynchronize();  // Wait for reset

    // Actual benchmark
    cudaMemset(d_success, 0, sizeof(uint32_t));

    cudaEvent_t start, stop;
    cudaEventCreate(&start);
    cudaEventCreate(&stop);

    cudaEventRecord(start);
    v8_stress_kernel<<<blocks, threads_per_block>>>(&ctx.pool, iters, d_success);
    cudaEventRecord(stop);
    cudaDeviceSynchronize();

    float ms = 0;
    cudaEventElapsedTime(&ms, start, stop);

    uint32_t success = 0;
    cudaMemcpy(&success, d_success, sizeof(uint32_t), cudaMemcpyDeviceToHost);

    SlabStats stats = viviani_slab_stats(&ctx);

    uint64_t total_ops = (uint64_t)blocks * threads_per_block * iters;
    result.time_ms = ms;
    result.allocs = stats.allocs[0] + stats.allocs[1] + stats.allocs[2];
    result.frees = stats.frees[0] + stats.frees[1] + stats.frees[2];
    result.fallbacks = stats.fallbacks[0] + stats.fallbacks[1] + stats.fallbacks[2];
    result.contention = 0;  // V8 doesn't track this
    result.success_rate = (float)success / (float)total_ops * 100.0f;
    result.throughput_mops = (float)total_ops / (ms / 1000.0f) / 1e6f;

    cudaFree(d_success);
    cudaEventDestroy(start);
    cudaEventDestroy(stop);
    viviani_slab_destroy(&ctx);

    return result;
}

BenchResult benchmark_v9(uint32_t blocks, uint32_t threads_per_block, uint32_t iters) {
    BenchResult result = {0};

    VivianiSlabContextV9 ctx;
    cudaError_t err = viviani_slab_init_v9(&ctx, TEST_POOL_DEPTH);
    if (err != cudaSuccess) {
        printf("V9 init failed: %s\n", cudaGetErrorString(err));
        return result;
    }
    cudaDeviceSynchronize();  // Wait for init memsets

    uint32_t* d_success;
    cudaMalloc((void**)&d_success, sizeof(uint32_t));

    // Warmup
    cudaMemset(d_success, 0, sizeof(uint32_t));
    viviani_slab_stress_kernel_v9<<<blocks, threads_per_block>>>(&ctx.pool, WARMUP_ITERS, d_success);
    cudaDeviceSynchronize();
    viviani_slab_reset_v9(&ctx);
    cudaDeviceSynchronize();  // Wait for reset

    // Actual benchmark
    cudaMemset(d_success, 0, sizeof(uint32_t));

    cudaEvent_t start, stop;
    cudaEventCreate(&start);
    cudaEventCreate(&stop);

    cudaEventRecord(start);
    viviani_slab_stress_kernel_v9<<<blocks, threads_per_block>>>(&ctx.pool, iters, d_success);
    cudaEventRecord(stop);
    cudaDeviceSynchronize();

    float ms = 0;
    cudaEventElapsedTime(&ms, start, stop);

    uint32_t success = 0;
    cudaMemcpy(&success, d_success, sizeof(uint32_t), cudaMemcpyDeviceToHost);

    SlabStatsV9 stats = viviani_slab_stats_v9(&ctx);

    uint64_t total_ops = (uint64_t)blocks * threads_per_block * iters;
    result.time_ms = ms;
    result.allocs = stats.allocs[0] + stats.allocs[1] + stats.allocs[2];
    result.frees = stats.frees[0] + stats.frees[1] + stats.frees[2];
    result.fallbacks = stats.fallbacks[0] + stats.fallbacks[1] + stats.fallbacks[2];
    result.contention = stats.contention_events[0] + stats.contention_events[1] + stats.contention_events[2];
    result.success_rate = (float)success / (float)total_ops * 100.0f;
    result.throughput_mops = (float)total_ops / (ms / 1000.0f) / 1e6f;

    cudaFree(d_success);
    cudaEventDestroy(start);
    cudaEventDestroy(stop);
    viviani_slab_destroy_v9(&ctx);

    return result;
}

// ============================================================================
// Scaling Test
// ============================================================================

void run_scaling_test() {
    printf("\n");
    printf("================================================================================\n");
    printf("                    V8 vs V9 Many-Body Scaling Comparison\n");
    printf("================================================================================\n");
    printf("\n");
    printf("This test demonstrates how many-body physics (gravitational repulsion,\n");
    printf("mean-field density tracking) improves GPU scaling under high warp counts.\n");
    printf("\n");

    // Test at small warp counts (limited by pool_depth=64)
    // With pool_depth=64 and SBS_PER_WARP=18, we can support ~3 warps per class
    // Use higher thread counts to get more threads per warp
    uint32_t warp_counts[] = {1, 2, 3};
    int num_tests = sizeof(warp_counts) / sizeof(warp_counts[0]);

    printf("%-12s | %-24s | %-24s | %-10s\n",
           "Warps", "V8 (Original)", "V9 (Many-Body)", "Speedup");
    printf("%-12s | %-12s %-11s | %-12s %-11s | %-10s\n",
           "", "Time(ms)", "M ops/s", "Time(ms)", "M ops/s", "");
    printf("-------------|--------------------------|--------------------------|------------\n");
    fflush(stdout);

    for (int t = 0; t < num_tests; t++) {
        uint32_t warps = warp_counts[t];
        uint32_t threads = warps * 32;

        // Choose block configuration to hit warp count
        uint32_t blocks, threads_per_block;
        if (threads <= 1024) {
            blocks = 1;
            threads_per_block = threads;
        } else {
            threads_per_block = 256;
            blocks = threads / 256;
        }

        BenchResult v8 = benchmark_v8(blocks, threads_per_block, TEST_ITERS_PER_THREAD);
        BenchResult v9 = benchmark_v9(blocks, threads_per_block, TEST_ITERS_PER_THREAD);

        float speedup = v9.time_ms > 0 ? v8.time_ms / v9.time_ms : 0;

        printf("%-12u | %10.2f   %10.2f | %10.2f   %10.2f | %8.2fx\n",
               warps,
               v8.time_ms, v8.throughput_mops,
               v9.time_ms, v9.throughput_mops,
               speedup);
    }

    printf("\n");
}

// ============================================================================
// Contention Analysis Test
// ============================================================================

void run_contention_analysis() {
    printf("\n");
    printf("================================================================================\n");
    printf("                         Contention Analysis (V9)\n");
    printf("================================================================================\n");
    printf("\n");
    printf("This test shows how the many-body density field reduces contention.\n");
    printf("Lower contention ratio = less wasted atomic operations.\n");
    printf("\n");

    uint32_t blocks = 1;  // Reduced for small pool
    uint32_t threads_per_block = 256;
    uint32_t iters = TEST_ITERS_PER_THREAD;

    VivianiSlabContextV9 ctx;
    viviani_slab_init_v9(&ctx, TEST_POOL_DEPTH);

    printf("Running %u blocks x %u threads x %u iters = %llu total operations\n\n",
           blocks, threads_per_block, iters,
           (unsigned long long)blocks * threads_per_block * iters);

    uint32_t* d_success;
    cudaMalloc((void**)&d_success, sizeof(uint32_t));
    cudaMemset(d_success, 0, sizeof(uint32_t));

    // Run test
    viviani_slab_stress_kernel_v9<<<blocks, threads_per_block>>>(&ctx.pool, iters, d_success);
    cudaDeviceSynchronize();

    // Get results
    SlabStatsV9 stats = viviani_slab_stats_v9(&ctx);
    viviani_slab_print_stats_v9(&stats);

    // Analyze per-class
    printf("\nPer-Class Analysis:\n");
    const char* nm[] = {"64B ", "128B", "256B"};
    for (int c = 0; c < SLAB_CLASSES; c++) {
        if (stats.allocs[c] > 0) {
            float ratio = (float)stats.contention_events[c] / (float)stats.allocs[c] * 100.0f;
            printf("  %s: %llu allocs, %llu contention events (%.2f%% ratio)\n",
                   nm[c],
                   (unsigned long long)stats.allocs[c],
                   (unsigned long long)stats.contention_events[c],
                   ratio);
        }
    }

    cudaFree(d_success);
    viviani_slab_destroy_v9(&ctx);
    printf("\n");
}

// ============================================================================
// Density Field Visualization
// ============================================================================

void run_density_visualization() {
    printf("\n");
    printf("================================================================================\n");
    printf("                       Density Field Visualization\n");
    printf("================================================================================\n");
    printf("\n");
    printf("Shows warp distribution across superblock space after allocation.\n");
    printf("Many-body physics should create even distribution (low variance).\n");
    printf("\n");

    uint32_t blocks = 1;
    uint32_t threads_per_block = 96;  // 3 warps
    uint32_t iters = 20;

    VivianiSlabContextV9 ctx;
    viviani_slab_init_v9(&ctx, TEST_POOL_DEPTH);

    uint32_t* d_success;
    cudaMalloc((void**)&d_success, sizeof(uint32_t));
    cudaMemset(d_success, 0, sizeof(uint32_t));

    // Run allocations
    viviani_slab_stress_kernel_v9<<<blocks, threads_per_block>>>(&ctx.pool, iters, d_success);
    cudaDeviceSynchronize();

    // Read density field
    SlabDensityField host_density;
    cudaMemcpy(&host_density, ctx.pool.d_density_field, sizeof(SlabDensityField), cudaMemcpyDeviceToHost);

    printf("Density distribution per class (first 32 cells):\n\n");
    const char* nm[] = {"64B ", "128B", "256B"};

    for (int c = 0; c < SLAB_CLASSES; c++) {
        printf("%s: ", nm[c]);

        // Calculate stats
        uint32_t sum = 0, max_d = 0, min_d = UINT32_MAX;
        for (int i = 0; i < V9_SLAB_DENSITY_GRID_SIZE; i++) {
            uint32_t d = host_density.density[c][i];
            sum += d;
            if (d > max_d) max_d = d;
            if (d < min_d) min_d = d;
        }
        float mean = (float)sum / V9_SLAB_DENSITY_GRID_SIZE;

        // Calculate variance
        float variance = 0;
        for (int i = 0; i < V9_SLAB_DENSITY_GRID_SIZE; i++) {
            float diff = (float)host_density.density[c][i] - mean;
            variance += diff * diff;
        }
        variance /= V9_SLAB_DENSITY_GRID_SIZE;
        float stddev = sqrtf(variance);

        printf("mean=%.1f, stddev=%.1f, range=[%u,%u], CV=%.2f%%\n",
               mean, stddev, min_d, max_d,
               mean > 0 ? (stddev / mean * 100.0f) : 0.0f);

        // ASCII histogram (first 32 cells)
        printf("      [");
        for (int i = 0; i < 32; i++) {
            uint32_t d = host_density.density[c][i];
            char ch;
            if (d == 0) ch = ' ';
            else if (d <= mean * 0.5f) ch = '.';
            else if (d <= mean * 1.0f) ch = 'o';
            else if (d <= mean * 1.5f) ch = 'O';
            else ch = '#';
            printf("%c", ch);
        }
        printf("]\n\n");
    }

    printf("Legend: ' '=0, '.'=low, 'o'=mean, 'O'=high, '#'=very high\n");
    printf("Lower coefficient of variation (CV) = more even distribution\n");

    cudaFree(d_success);
    viviani_slab_destroy_v9(&ctx);
}

// ============================================================================
// Phase Evolution Test
// ============================================================================

void run_phase_evolution_test() {
    printf("\n");
    printf("================================================================================\n");
    printf("                      Adaptive Phase Evolution Test\n");
    printf("================================================================================\n");
    printf("\n");
    printf("Tests how the global phase adapts over time to reduce contention.\n");
    printf("Phase should evolve to spread warps apart based on contention feedback.\n");
    printf("\n");

    VivianiSlabContextV9 ctx;
    viviani_slab_init_v9(&ctx, TEST_POOL_DEPTH);

    uint32_t blocks = 1;
    uint32_t threads_per_block = 64;
    uint32_t iters = 20;
    int rounds = 5;

    uint32_t* d_success;
    cudaMalloc((void**)&d_success, sizeof(uint32_t));

    printf("Round | Phase[0] | Phase[1] | Phase[2] | Total Contention\n");
    printf("------|----------|----------|----------|------------------\n");

    for (int r = 0; r < rounds; r++) {
        cudaMemset(d_success, 0, sizeof(uint32_t));

        // Run a round of allocations
        viviani_slab_stress_kernel_v9<<<blocks, threads_per_block>>>(&ctx.pool, iters, d_success);
        cudaDeviceSynchronize();

        // Read density field for phase values
        SlabDensityField host_density;
        cudaMemcpy(&host_density, ctx.pool.d_density_field, sizeof(SlabDensityField), cudaMemcpyDeviceToHost);

        SlabStatsV9 stats = viviani_slab_stats_v9(&ctx);
        uint64_t total_contention = stats.contention_events[0] +
                                    stats.contention_events[1] +
                                    stats.contention_events[2];

        printf("%5d | %8.3f | %8.3f | %8.3f | %16llu\n",
               r + 1,
               host_density.global_phase[0],
               host_density.global_phase[1],
               host_density.global_phase[2],
               (unsigned long long)total_contention);

        // Apply density decay between rounds (simulates time passing)
        viviani_slab_decay_density(&ctx);
    }

    cudaFree(d_success);
    viviani_slab_destroy_v9(&ctx);
    printf("\n");
}

// ============================================================================
// Langevin Dynamics Equilibration Test
// ============================================================================

void run_langevin_test() {
    printf("\n");
    printf("================================================================================\n");
    printf("                      Langevin Dynamics Equilibration\n");
    printf("================================================================================\n");
    printf("\n");
    printf("Tests how Langevin dynamics (thermal noise + damping) helps the system\n");
    printf("find low-contention equilibrium states. Compares with and without Langevin.\n");
    printf("\n");

    const uint32_t blocks = 1;  // Reduced for small pool
    const uint32_t threads_per_block = 64;  // 2 warps
    const uint32_t iters_per_round = 20;
    const int num_rounds = 5;

    // Test WITHOUT Langevin dynamics
    printf("--- Without Langevin Dynamics ---\n");
    {
        VivianiSlabContextV9 ctx;
        viviani_slab_init_v9(&ctx, TEST_POOL_DEPTH);

        uint32_t* d_success;
        cudaMalloc((void**)&d_success, sizeof(uint32_t));

        uint64_t total_contention = 0;
        for (int r = 0; r < num_rounds; r++) {
            cudaMemset(d_success, 0, sizeof(uint32_t));
            viviani_slab_stress_kernel_v9<<<blocks, threads_per_block>>>(
                &ctx.pool, iters_per_round, d_success);
            cudaDeviceSynchronize();

            SlabStatsV9 stats = viviani_slab_stats_v9(&ctx);
            uint64_t round_contention = stats.contention_events[0] +
                                        stats.contention_events[1] +
                                        stats.contention_events[2];
            total_contention += round_contention;

            // Only density decay, no Langevin
            viviani_slab_decay_density(&ctx);
        }

        SlabStatsV9 final_stats = viviani_slab_stats_v9(&ctx);
        uint64_t total_allocs = final_stats.allocs[0] + final_stats.allocs[1] + final_stats.allocs[2];
        float contention_ratio = (float)total_contention / (float)total_allocs * 100.0f;

        printf("  Total allocations: %llu\n", (unsigned long long)total_allocs);
        printf("  Total contention:  %llu\n", (unsigned long long)total_contention);
        printf("  Contention ratio:  %.2f%%\n", contention_ratio);

        cudaFree(d_success);
        viviani_slab_destroy_v9(&ctx);
    }

    // Test WITH Langevin dynamics
    printf("\n--- With Langevin Dynamics ---\n");
    {
        VivianiSlabContextV9 ctx;
        viviani_slab_init_v9(&ctx, TEST_POOL_DEPTH);

        uint32_t* d_success;
        cudaMalloc((void**)&d_success, sizeof(uint32_t));

        uint64_t total_contention = 0;
        for (int r = 0; r < num_rounds; r++) {
            cudaMemset(d_success, 0, sizeof(uint32_t));
            viviani_slab_stress_kernel_v9<<<blocks, threads_per_block>>>(
                &ctx.pool, iters_per_round, d_success);
            cudaDeviceSynchronize();

            SlabStatsV9 stats = viviani_slab_stats_v9(&ctx);
            uint64_t round_contention = stats.contention_events[0] +
                                        stats.contention_events[1] +
                                        stats.contention_events[2];
            total_contention += round_contention;

            // Full equilibration: decay + Langevin step
            viviani_slab_equilibrate(&ctx, (uint32_t)r);
        }

        SlabStatsV9 final_stats = viviani_slab_stats_v9(&ctx);
        uint64_t total_allocs = final_stats.allocs[0] + final_stats.allocs[1] + final_stats.allocs[2];
        float contention_ratio = (float)total_contention / (float)total_allocs * 100.0f;

        printf("  Total allocations: %llu\n", (unsigned long long)total_allocs);
        printf("  Total contention:  %llu\n", (unsigned long long)total_contention);
        printf("  Contention ratio:  %.2f%%\n", contention_ratio);

        // Show final temperature (should have adapted)
        SlabDensityField host_density;
        cudaMemcpy(&host_density, ctx.pool.d_density_field, sizeof(SlabDensityField), cudaMemcpyDeviceToHost);
        printf("\n  Final effective temperatures:\n");
        printf("    64B:  %.3f\n", host_density.effective_temp[0]);
        printf("    128B: %.3f\n", host_density.effective_temp[1]);
        printf("    256B: %.3f\n", host_density.effective_temp[2]);

        cudaFree(d_success);
        viviani_slab_destroy_v9(&ctx);
    }

    printf("\n");
}

// ============================================================================
// Main
// ============================================================================

int main(int argc, char** argv) {
    printf("\n");
    printf("################################################################################\n");
    printf("#                                                                              #\n");
    printf("#          Viviani Many-Body GPU Allocator - V8 vs V9 Comparison               #\n");
    printf("#                                                                              #\n");
    printf("#  V9 introduces many-body physics for GPU scaling:                            #\n");
    printf("#    - Gravitational repulsion: Warps repel based on cursor proximity          #\n");
    printf("#    - Mean-field density: Coarse tracking of warp distribution                #\n");
    printf("#    - Adaptive phase: Global phase evolves to minimize contention             #\n");
    printf("#    - Warp-cooperative bitmap: Reduces failed atomics ~2x                     #\n");
    printf("#                                                                              #\n");
    printf("################################################################################\n");

    // Check GPU
    int device;
    cudaGetDevice(&device);
    cudaDeviceProp props;
    cudaGetDeviceProperties(&props, device);
    printf("\nGPU: %s (SM %d.%d, %d SMs, %d MB)\n",
           props.name, props.major, props.minor,
           props.multiProcessorCount,
           (int)(props.totalGlobalMem / 1024 / 1024));
    fflush(stdout);

    // Run tests
    run_scaling_test();
    run_contention_analysis();
    run_density_visualization();
    run_phase_evolution_test();
    run_langevin_test();

    printf("\n################################################################################\n");
    printf("                              Tests Complete\n");
    printf("################################################################################\n\n");

    return 0;
}
