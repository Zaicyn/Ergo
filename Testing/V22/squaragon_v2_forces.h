/*
 * SQUARAGON V2 FORCES — Topological Force Kernels
 * =================================================
 *
 * Three interaction channels gated by flow harmonics, propagating
 * along topological distance (ring + bin + branch), not Euclidean.
 *
 * Strong (3θ):  local, within-branch, bunching
 * EM (1θ):      long-range, propagates along rings, 1/r²
 * Weak (9θ/27θ): ultra-short, branch-crossing, flow-gated
 *
 * Gravity = residual bias after harmonic cancellation.
 * Not a separate force — emerges from imbalance.
 *
 * Depends on: squaragon_v2.h
 *
 * License: Public domain / CC0
 */

#ifndef SQUARAGON_V2_FORCES_H
#define SQUARAGON_V2_FORCES_H

#include "squaragon_v2.h"

#ifdef __cplusplus
extern "C" {
#endif

/*============================================================================
 * TOPOLOGICAL NODE — position in the torus + branch tree
 *============================================================================*/

typedef struct {
    uint8_t  bin;           /* 0-7: which fiber */
    uint8_t  gen;           /* 0-31: ring position (torus) */
    uint16_t branch_id;     /* which branch (0 = trunk) */
    uint8_t  depth;         /* branch depth (0 = substrate) */
    uint8_t  flow_mode;     /* 0=COAST, 1=ACTIVE, 2=FLOW */
    float    flow_w;        /* w-component at this ring position */
} sq2_topo_node_t;

/*============================================================================
 * TOPOLOGICAL DISTANCE
 *
 * Distance measured along the fabric, not through space.
 * Three components with different weights:
 *   ring:   primary axis, cyclic (period 32)
 *   bin:    secondary, cyclic (period 8), weighted lower
 *   branch: tree distance, weighted higher (branches are "far")
 *============================================================================*/

#define SQ2_WEIGHT_RING   1.0f
#define SQ2_WEIGHT_BIN    0.5f
#define SQ2_WEIGHT_BRANCH 2.0f

/* Ring distance (cyclic, period 32) */
static inline int sq2_ring_dist(int g1, int g2) {
    int d = abs(g1 - g2);
    return (d < 16) ? d : 32 - d;
}

/* Bin distance (cyclic, period 8) */
static inline int sq2_bin_dist(int b1, int b2) {
    int d = abs(b1 - b2);
    return (d < 4) ? d : 8 - d;
}

/* Branch distance (tree metric) */
static inline int sq2_branch_dist(sq2_topo_node_t a, sq2_topo_node_t b) {
    if (a.branch_id == b.branch_id) return 0;
    /* Different branches: go up to common ancestor + down.
     * Cheap approximation: sum of depths + 1 */
    return abs((int)a.depth - (int)b.depth) + 1;
}

/* Combined topological distance */
static inline float sq2_topo_dist(sq2_topo_node_t a, sq2_topo_node_t b) {
    return SQ2_WEIGHT_RING   * (float)sq2_ring_dist(a.gen, b.gen)
         + SQ2_WEIGHT_BIN    * (float)sq2_bin_dist(a.bin, b.bin)
         + SQ2_WEIGHT_BRANCH * (float)sq2_branch_dist(a, b);
}

/*============================================================================
 * DIRECTIONAL ALIGNMENT
 *
 * Forces flow along topology. Alignment biases propagation direction.
 * Returns [-1, +1]: aligned = same direction, opposed = opposite.
 *============================================================================*/

/* Ring direction: which way around the ring from a to b */
static inline int sq2_ring_direction(int g1, int g2) {
    int d = g2 - g1;
    if (d > 16) d -= 32;
    if (d < -16) d += 32;
    return (d > 0) ? 1 : (d < 0) ? -1 : 0;
}

/* Alignment factor for EM propagation */
static inline float sq2_alignment(sq2_topo_node_t a, sq2_topo_node_t b) {
    /* Ring alignment dominates */
    int ring_dir = sq2_ring_direction(a.gen, b.gen);
    /* Branch alignment: toward parent = +1, toward child = -1 */
    int branch_dir = (b.depth < a.depth) ? 1 : (b.depth > a.depth) ? -1 : 0;

    float ring_align = (ring_dir != 0) ? 1.0f : 0.5f;
    float branch_align = (branch_dir != 0) ? 0.5f * (float)branch_dir : 0.0f;

    return 0.5f + 0.5f * (ring_align + branch_align * 0.3f);
}

/*============================================================================
 * FORCE KERNELS — spatial falloff along topology
 *
 * Each kernel defines how influence decays with topological distance.
 * The harmonic coefficients (1/3, 1/9, 1/27) define coupling strength.
 * The kernels define reach.
 *============================================================================*/

/* Strong force: local, within-branch only.
 * The z-component coupling: cos(θ)·cos(3θ) = bunching.
 * Does not cross branch boundaries. Ring range ≤ 1. */
static inline float sq2_kernel_strong(sq2_topo_node_t a, sq2_topo_node_t b) {
    /* No cross-branch strong force */
    if (a.branch_id != b.branch_id) return 0.0f;
    /* Local only: ring neighbors */
    if (sq2_ring_dist(a.gen, b.gen) > 1) return 0.0f;
    /* Bin distance weakens but doesn't kill */
    int bd = sq2_bin_dist(a.bin, b.bin);
    if (bd > 2) return 0.0f;
    return 1.0f / (1.0f + (float)bd);
}

/* Electromagnetic: long-range, propagates along rings.
 * The 1θ harmonic: the carrier field.
 * 1/r² falloff along topological distance. Alignment-biased. */
static inline float sq2_kernel_em(sq2_topo_node_t a, sq2_topo_node_t b) {
    float r = sq2_topo_dist(a, b);
    float align = sq2_alignment(a, b);
    return (1.0f / (r * r + 1.0f)) * align;
}

/* Weak force: ultra-short range, branch-crossing, flow-gated.
 * The 9θ/27θ harmonics: only fire in soliton windows.
 * Only at branch boundaries, only when both nodes are in FLOW mode. */
static inline float sq2_kernel_weak(sq2_topo_node_t a, sq2_topo_node_t b) {
    /* Both must be in FLOW mode */
    if (a.flow_mode != SQ2_FLOW_MODE_FLOW) return 0.0f;
    if (b.flow_mode != SQ2_FLOW_MODE_FLOW) return 0.0f;
    /* Must be at branch boundary (adjacent branches) */
    int bd = sq2_branch_dist(a, b);
    if (bd != 1) return 0.0f;
    /* Ring proximity required */
    if (sq2_ring_dist(a.gen, b.gen) > 2) return 0.0f;
    return 0.2f;
}

/*============================================================================
 * COMBINED FORCE
 *
 * F_total = A_strong * K_strong * sin(3θ)/3
 *         + A_em     * K_em     * sin(θ)
 *         + A_weak   * K_weak   * sin(9θ)/9
 *
 * Mode gating:
 *   COAST:  EM only
 *   ACTIVE: EM + strong
 *   FLOW:   all three
 *============================================================================*/

typedef struct {
    float strong;       /* strong force contribution */
    float em;           /* electromagnetic contribution */
    float weak;         /* weak force contribution */
    float total;        /* combined */
    float gravity;      /* residual (imbalance) */
} sq2_force_result_t;

/* Compute interaction between two topological nodes.
 * theta_a, theta_b are the fiber phases of the two nodes. */
static inline sq2_force_result_t sq2_compute_force(
    sq2_topo_node_t a, sq2_topo_node_t b,
    float theta_a, float theta_b)
{
    sq2_force_result_t f = {0};

    /* Relative phase drives the harmonic content */
    float dtheta = theta_b - theta_a;

    /* Harmonic components at the relative phase */
    float h1 = sinf(dtheta);                      /* 1θ carrier */
    float h3 = sinf(3.0f * dtheta) * SQ2_FLOW_C1; /* 3θ strong */
    float h9 = sinf(9.0f * dtheta) * SQ2_FLOW_C2; /* 9θ weak */

    /* Kernel weights (spatial falloff along topology) */
    float k_strong = sq2_kernel_strong(a, b);
    float k_em     = sq2_kernel_em(a, b);
    float k_weak   = sq2_kernel_weak(a, b);

    /* Mode gating: only compute active channels */
    int mode = (a.flow_mode > b.flow_mode) ? b.flow_mode : a.flow_mode;

    /* EM always active */
    f.em = SQ2_FLOW_C1 * k_em * h1;

    /* Strong: active in ACTIVE and FLOW modes */
    if (mode >= SQ2_FLOW_MODE_ACTIVE) {
        f.strong = SQ2_FLOW_C1 * k_strong * h3;
    }

    /* Weak: only in FLOW mode */
    if (mode >= SQ2_FLOW_MODE_FLOW) {
        f.weak = SQ2_FLOW_C2 * k_weak * h9;
    }

    f.total = f.strong + f.em + f.weak;

    /* Gravity = residual imbalance.
     * Perfect balance → total ≈ 0. Asymmetry → net drift.
     * Always attractive (toward higher density / lower potential). */
    f.gravity = f.total * f.total;  /* squared residual = always positive */

    return f;
}

/*============================================================================
 * FORCE FIELD AT A NODE — sum interactions with neighbors
 *
 * For a given node, compute the total force from all nearby nodes
 * within interaction range. Returns the net force vector in
 * topological coordinates (ring direction, bin direction, branch direction).
 *============================================================================*/

typedef struct {
    float f_ring;       /* force along ring (tangential) */
    float f_bin;        /* force across bins (cross-fiber) */
    float f_branch;     /* force along branch (radial in tree) */
    float f_gravity;    /* gravitational drift (always toward accumulation) */
    float total_strong;
    float total_em;
    float total_weak;
} sq2_field_result_t;

/* Compute force field at node 'self' from an array of neighbors.
 * This is the N-body interaction in topological space. */
static inline sq2_field_result_t sq2_compute_field(
    sq2_topo_node_t self, float theta_self,
    const sq2_topo_node_t* neighbors, const float* thetas,
    int n_neighbors)
{
    sq2_field_result_t field = {0};

    for (int j = 0; j < n_neighbors; j++) {
        sq2_force_result_t f = sq2_compute_force(self, neighbors[j],
                                                  theta_self, thetas[j]);

        /* Project force onto topological directions */
        int ring_dir = sq2_ring_direction(self.gen, neighbors[j].gen);
        int bin_dir = neighbors[j].bin - self.bin;
        if (bin_dir > 4) bin_dir -= 8;
        if (bin_dir < -4) bin_dir += 8;
        int branch_dir = (int)neighbors[j].depth - (int)self.depth;

        float r = sq2_topo_dist(self, neighbors[j]);
        float inv_r = 1.0f / (r + 0.1f);

        field.f_ring   += f.total * (float)ring_dir * inv_r;
        field.f_bin    += f.total * (float)bin_dir * inv_r;
        field.f_branch += f.total * (float)branch_dir * inv_r;
        field.f_gravity += f.gravity;

        field.total_strong += fabsf(f.strong);
        field.total_em     += fabsf(f.em);
        field.total_weak   += fabsf(f.weak);
    }

    return field;
}

/*============================================================================
 * SPATIAL FORCE PROJECTION
 *
 * Convert topological force to Cartesian acceleration for the sim.
 * Maps ring direction → tangential, bin direction → cross-plane,
 * branch direction → radial.
 *============================================================================*/

static inline void sq2_project_to_cartesian(
    sq2_field_result_t field,
    float px, float py, float pz,
    float theta_fiber,
    float* ax, float* ay, float* az)
{
    float r_xz = sqrtf(px*px + pz*pz);
    if (r_xz < 0.01f) return;
    float inv_r = 1.0f / r_xz;

    /* Tangential direction (ring → rotation) */
    float tang_x = -pz * inv_r;
    float tang_z =  px * inv_r;

    /* Radial direction (branch → inward/outward) */
    float rad_x = px * inv_r;
    float rad_z = pz * inv_r;

    /* Ring force → tangential acceleration */
    *ax += field.f_ring * tang_x;
    *az += field.f_ring * tang_z;

    /* Branch force → radial acceleration */
    *ax += field.f_branch * rad_x;
    *az += field.f_branch * rad_z;

    /* Bin force → vertical (cross-plane) */
    *ay += field.f_bin;

    /* Gravity → always radially inward (accumulation drift) */
    *ax -= field.f_gravity * rad_x * 0.01f;
    *az -= field.f_gravity * rad_z * 0.01f;
}

#ifdef __cplusplus
}
#endif

#endif /* SQUARAGON_V2_FORCES_H */
