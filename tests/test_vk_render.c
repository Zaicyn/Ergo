/*
 * test_vk_render.c — Phase E test: 3D heightfield visualization
 *
 * Creates a 2D grid of simulation values, dispatches a compute kernel
 * each frame, and renders the data as a 3D surface with orbit camera.
 *
 * Build:
 *   gcc -std=c99 -o test_vk_render tests/test_vk_render.c \
 *       mcl/runtime/vk_host.c -lvulkan -lglfw -lm -Imcl/runtime
 */

#include "ergo_vk.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define NX 64
#define NY 64
#define N  (NX * NY)
#define DT 0.002

static void *read_file(const char *path, size_t *out_size) {
    FILE *f = fopen(path, "rb");
    if (!f) { fprintf(stderr, "Cannot open %s\n", path); exit(1); }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    void *buf = malloc(sz);
    if (fread(buf, 1, sz, f) != (size_t)sz) {
        fprintf(stderr, "Short read on %s\n", path); exit(1);
    }
    fclose(f);
    *out_size = (size_t)sz;
    return buf;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <kernel.spv>\n", argv[0]);
        return 1;
    }

    size_t spv_size;
    void *spv_data = read_file(argv[1], &spv_size);

    /* Init Vulkan with window */
    if (ergo_vk_init(0) != 0) {
        fprintf(stderr, "Vulkan init failed\n");
        return 1;
    }

    /* Buffers: 2D grid of f64 values */
    ErgoVkBuf d_val = ergo_vk_create_buffer(N * sizeof(double));
    ErgoVkBuf d_vel = ergo_vk_create_buffer(N * sizeof(double));

    /* Init data: ripple pattern */
    double val[N], vel[N];
    for (int j = 0; j < NY; j++) {
        for (int i = 0; i < NX; i++) {
            double cx = (double)i / NX - 0.5;
            double cy = (double)j / NY - 0.5;
            double r = sqrt(cx*cx + cy*cy);
            val[j * NX + i] = sin(r * 20.0) * exp(-r * 4.0);
            vel[j * NX + i] = 0.0;
        }
    }

    ergo_vk_upload(d_val, val, N * sizeof(double));
    ergo_vk_upload(d_vel, vel, N * sizeof(double));

    /* Load compute kernel */
    ErgoVkPipe pipe = ergo_vk_load_shader(spv_data, spv_size, 2,
                                           sizeof(double) + sizeof(int));
    ergo_vk_bind_buffer(pipe, 0, d_val);
    ergo_vk_bind_buffer(pipe, 1, d_vel);

    struct { double dt; int n; } pc = { DT, N };
    ergo_vk_push_constants(pipe, &pc, sizeof(pc));

    /* Main loop */
    int frame = 0;
    while (!ergo_vk_should_close()) {
        ergo_vk_dispatch(pipe, (N + 255) / 256);

        /* Render as 3D heightfield: NX x NY grid, height_scale 0.3 */
        ergo_vk_render_frame(d_val, NX, NY, -1.0f, 1.0f, 0.3f);

        frame++;
        if (frame % 1000 == 0) {
            fprintf(stderr, "[frame %d]\n", frame);
        }
    }

    fprintf(stderr, "Window closed after %d frames\n", frame);
    free(spv_data);
    ergo_vk_shutdown();
    return 0;
}
