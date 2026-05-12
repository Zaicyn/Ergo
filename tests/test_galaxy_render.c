/*
 * test_galaxy_render.c — Galaxy simulation with live 3D point cloud rendering
 *
 * Includes the compiler-generated galaxy simulation code, then runs it
 * with a render loop that uploads particle positions to GPU each frame
 * and renders them as a 3D point cloud with orbit camera.
 *
 * Build:
 *   # First generate the galaxy C code:
 *   python -m mcl --emit-c galaxy/galaxy_full.mcl > galaxy/galaxy_full_gen.c
 *
 *   # Then rename main so we can provide our own:
 *   sed -i 's/^int main(void)/int galaxy_main(void)/' galaxy/galaxy_full_gen.c
 *
 *   # Build:
 *   gcc -std=c99 -O2 -o test_galaxy_render tests/test_galaxy_render.c \
 *       mcl/runtime/vk_host.c -lvulkan -lglfw -lm -Imcl/runtime
 */

/* Include the generated galaxy simulation (with main renamed) */
#include "../galaxy/galaxy_full_gen.c"

#include "ergo_vk.h"

int main(void) {
    /* Init Vulkan with window */
    if (ergo_vk_init(0) != 0) {
        fprintf(stderr, "Vulkan init failed\n");
        return 1;
    }

    /* Init galaxy simulation */
    SIM_INIT(DEFAULT_N, MAXPART, 42);
    SIM_SEED_SHELL();
    fprintf(stderr, "[galaxy] Initial particles: %d\n", NPART);

    /* Allocate GPU buffers for particle positions + color */
    ErgoVkBuf d_px = ergo_vk_create_buffer(MAXPART * sizeof(double));
    ErgoVkBuf d_py = ergo_vk_create_buffer(MAXPART * sizeof(double));
    ErgoVkBuf d_pz = ergo_vk_create_buffer(MAXPART * sizeof(double));
    ErgoVkBuf d_omega = ergo_vk_create_buffer(MAXPART * sizeof(double));

    int frame = 0;
    while (!ergo_vk_should_close()) {
        /* Run one sim step on CPU */
        CLEAR_GRID();
        SCATTER_GRID();
        STENCIL_GRID();
        SIM_PHYSICS_STEP(DEFAULT_DT);

        /* Spawn every 100 frames */
        if (frame > 0 && frame % 100 == 0) {
            SIM_SPAWN(MAXPART, 0);
        }

        /* Upload particle data to GPU */
        ergo_vk_upload(d_px, POS_X, NPART * sizeof(double));
        ergo_vk_upload(d_py, POS_Y, NPART * sizeof(double));
        ergo_vk_upload(d_pz, POS_Z, NPART * sizeof(double));
        ergo_vk_upload(d_omega, OMEGA_NAT, NPART * sizeof(double));

        /* Render point cloud.
         * DISK_OUTER_R = 1200, so world_scale = 1/1200 maps to ~[-1,1].
         * Color by OMEGA_NAT: range [0, 2.0] (OMEGA_MAX). */
        ergo_vk_render_points(d_px, d_py, d_pz, d_omega, NPART,
                              3.0f,        /* point_size */
                              0.0f, 2.0f,  /* val_min, val_max (omega range) */
                              1.0f / 1200.0f); /* world_scale */

        frame++;
        if (frame % 500 == 0) {
            fprintf(stderr, "[frame %d] particles: %d\n", frame, NPART);
        }
    }

    fprintf(stderr, "Window closed after %d frames, %d particles\n", frame, NPART);
    ergo_vk_shutdown();
    return 0;
}
