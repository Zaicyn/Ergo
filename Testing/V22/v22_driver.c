/*
 * v22_driver.c - Minimal driver that forces codegen of the V22 squaragon API.
 *
 * The V22 headers are all `static inline`, so nothing is emitted unless we
 * call it from a TU. This driver calls a representative slice of the API
 * and prints a checksum so the optimizer can't strip everything.
 */

#include <math.h>   /* V22 headers call sinf/fabsf/sqrtf without including math.h */
#include <stdio.h>
#include <stdint.h>

#include "squaragon_v2.h"
#include "squaragon_v2_forces.h"
#include "squaragon_v2_dna.h"

int main(int argc, char **argv) {
    sq2_gate_t gate;
    /* scale is runtime-dependent so the optimizer cannot fold the whole
     * SIMD residual computation into a single constant. */
    float runtime_scale = 1.0f + 0.01f * (float)argc;
    sq2_init(&gate, runtime_scale);

    sq2_scale_coherent(&gate);
    sq2_scale_phi(&gate);

    float r1 = sq2_triple_xor_residual(&gate);
    float r2 = sq2_triple_xor_residual_full(&gate);
    float ineff = sq2_inefficiency(&gate);

    /* Force the SIMD residual variants into codegen.
     * The SSE flavor returns a splatted __m128; any lane is the residual. */
    float r_simd = 0.0f;
#if defined(__SSE__)
    {
        __m128 v = sq2_simd_triple_xor_residual_sse(gate.scale);
        r_simd = _mm_cvtss_f32(v);
    }
#elif defined(__ARM_NEON)
    r_simd = sq2_simd_triple_xor_residual_neon(gate.scale);
#endif

    /* sq2_quat_t layout is {w, x, y, z} */
    sq2_quat_t q = (sq2_quat_t){1.0f, 0.0f, 0.0f, 0.0f};
    sq2_quat_t q2 = sq2_quat_mul(q, q);
    sq2_rotate(&gate, q2);

    uint8_t buf[SQ2_SERIALIZED_SIZE];
    sq2_serialize(&gate, buf);
    sq2_gate_t gate2;
    sq2_deserialize(&gate2, buf);

    uint64_t seam = sq2_seam_forward_shift(0xDEADBEEFCAFEBABEull);
    seam = sq2_seam_inverse_shift(seam);

    uint32_t scatter = sq2_viviani_scatter(argc, 1024);
    uint32_t scatter_full = sq2_viviani_scatter_full(argc, 1024);

    sq2_closed_gate_t closed;
    sq2_close_gate(&gate, &closed);

    float w, qual;
    int mode = sq2_flow_detect((float)argc * 0.1f, &w, &qual);
    int soliton = sq2_is_soliton_window((float)argc * 0.1f);

    sq2_topo_node_t a = {0, 0, 0, 0};
    sq2_topo_node_t b = {3, 2, 1, 0};
    float td = sq2_topo_dist(a, b);
    float al = sq2_alignment(a, b);
    sq2_force_result_t fr = sq2_compute_force(a, b, 1.0f, 1.0f);

    sq2_strand_t strand;
    sq2_strand_init(&strand, 0, 0);
    sq2_strand_write(&strand, 0.5f);

    sq2_cell_t cell;
    sq2_cell_init(&cell);
    sq2_cell_alloc(&cell, argc, 1024, 0.25f);

    /* Combine everything so DCE can't kill the calls. */
    volatile double sink =
        (double)r1 + r2 + ineff + r_simd
        + (double)q2.x + q2.y + q2.z + q2.w
        + (double)(seam & 0xFFFF)
        + (double)scatter + scatter_full
        + (double)closed.scale
        + mode + soliton + w + qual
        + td + al + fr.total + fr.gravity
        + (double)strand.length + strand.alloc_count
        + (double)cell.generation + cell.total_occupied;

    printf("V22 sink = %f\n", (double)sink);
    return 0;
}
