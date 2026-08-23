/*
 * test_vk_particle.c — Phase B test: particle kernel via Vulkan compute
 *
 * Manually written host code that:
 *   1. Initializes Vulkan via ergo_vk_init
 *   2. Allocates buffers for px[] and vx[]
 *   3. Uploads initial data (px=0, vx=1)
 *   4. Loads the compiled SPIR-V kernel (kernel_1: px[i] += vx[i] * DT)
 *   5. Dispatches the kernel
 *   6. Downloads and verifies results
 *
 * Expected output: px[0] = 0.001 (one step of DT=0.001 with vx=1.0)
 *
 * Build:
 *   # First, generate and assemble the SPIR-V:
 *   python -m core tests/gpu_particle.mcl --target spirv
 *   spirv-as --target-env spv1.3 a.out_kernel_1.spvasm -o kernel_1.spv
 *
 *   # Then compile and link:
 *   gcc -std=c99 -o test_vk_particle tests/test_vk_particle.c \
 *       core/runtime/vk_host.c -lvulkan -Icore/runtime
 *
 *   # Run:
 *   ./test_vk_particle kernel_1.spv
 */

#include "ergo_vk.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define N 1024
#define DT 0.001

/* Read a file into a malloc'd buffer. Returns size via *out_size. */
static void *read_file(const char *path, size_t *out_size) {
    FILE *f = fopen(path, "rb");
    if (!f) {
        fprintf(stderr, "Cannot open %s\n", path);
        exit(1);
    }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    void *buf = malloc(sz);
    if (fread(buf, 1, sz, f) != (size_t)sz) {
        fprintf(stderr, "Short read on %s\n", path);
        exit(1);
    }
    fclose(f);
    *out_size = (size_t)sz;
    return buf;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <kernel_1.spv>\n", argv[0]);
        return 1;
    }

    /* Load SPIR-V binary */
    size_t spv_size;
    void *spv_data = read_file(argv[1], &spv_size);

    /* Initialize Vulkan (headless) */
    if (ergo_vk_init(1) != 0) {
        fprintf(stderr, "Vulkan init failed\n");
        return 1;
    }

    /* Allocate device buffers */
    ErgoVkBuf d_px = ergo_vk_create_buffer(N * sizeof(double));
    ErgoVkBuf d_vx = ergo_vk_create_buffer(N * sizeof(double));

    /* Prepare host data */
    double px[N], vx[N];
    for (int i = 0; i < N; i++) {
        px[i] = 0.0;
        vx[i] = 1.0;
    }

    /* Upload */
    ergo_vk_upload(d_px, px, N * sizeof(double));
    ergo_vk_upload(d_vx, vx, N * sizeof(double));

    /*
     * Load the kernel.
     * kernel_1 has 2 storage buffers (px @ binding 0, vx @ binding 1)
     * and push constants: { double DT; int N; } = 12 bytes
     */
    ErgoVkPipe pipe = ergo_vk_load_shader(spv_data, spv_size, 2,
                                           sizeof(double) + sizeof(int));

    /* Bind buffers */
    ergo_vk_bind_buffer(pipe, 0, d_px);
    ergo_vk_bind_buffer(pipe, 1, d_vx);

    /* Push constants: { double DT, int N } matching SPIR-V layout */
    struct {
        double dt;
        int    n;
    } pc = { DT, N };
    ergo_vk_push_constants(pipe, &pc, sizeof(pc));

    /* Dispatch */
    int n_groups = (N + 255) / 256;
    ergo_vk_dispatch(pipe, n_groups);

    /* Download results */
    ergo_vk_download(d_px, px, N * sizeof(double));

    /* Verify */
    int pass = 1;
    double expected = DT;  /* 0.0 + 1.0 * 0.001 = 0.001 */
    for (int i = 0; i < N; i++) {
        if (fabs(px[i] - expected) > 1e-12) {
            fprintf(stderr, "FAIL: px[%d] = %.15g, expected %.15g\n",
                    i, px[i], expected);
            pass = 0;
            break;
        }
    }

    if (pass) {
        printf("PASS: px[0] = %f (all %d elements correct)\n", px[0], N);
    }

    /* Cleanup */
    free(spv_data);
    ergo_vk_shutdown();
    return pass ? 0 : 1;
}
