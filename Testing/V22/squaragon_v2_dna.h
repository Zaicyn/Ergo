/*
 * SQUARAGON V2 DNA — Strand/Cell/Cycle API
 * ==========================================
 *
 * A prototype DNA system that is simultaneously a minimal torus allocator.
 *
 * Biology view:  strand → codon → replicate → compare → repair → divide
 * Allocator view: ring → slot → copy → verify → fix → split
 *
 * Same code. Same geometry. Two interpretations.
 *
 * Depends on: squaragon_v2.h (gate, seam shift, serialization)
 *
 * License: Public domain / CC0
 */

#ifndef SQUARAGON_V2_DNA_H
#define SQUARAGON_V2_DNA_H

#include "squaragon_v2.h"
#include <string.h>

#ifdef __cplusplus
extern "C" {
#endif

/*============================================================================
 * CONSTANTS
 *============================================================================*/

#define SQ2_DNA_BINS        8
#define SQ2_DNA_SHELLS      2
#define SQ2_DNA_RING_SIZE   32    /* slots per ring (torus period) */
#define SQ2_DNA_UNIQUE_GENS 31    /* 32 - 1 closure */
#define SQ2_DNA_TOTAL_SLOTS (SQ2_DNA_SHELLS * SQ2_DNA_BINS * SQ2_DNA_RING_SIZE) /* 512 */

/* Cell cycle phases */
#define SQ2_PHASE_G1  0   /* growth, writing codons */
#define SQ2_PHASE_S   1   /* replication (copy shell 0 → shell 1) */
#define SQ2_PHASE_G2  2   /* comparison + repair */
#define SQ2_PHASE_M   3   /* division */

/* Capacity thresholds */
#define SQ2_THRESHOLD_BIAS    384   /* 75% of 512, equilibrium */
#define SQ2_THRESHOLD_WORKING 432   /* interference cycle limit */
#define SQ2_THRESHOLD_MAX     496   /* redline, must divide */

/* Recombination pressure threshold (3x fair share, from Test P) */
#define SQ2_RECOMBINE_SKEW    3.0f

/*============================================================================
 * TYPES
 *============================================================================*/

typedef struct {
    sq2_gate_t gate;        /* crystallized data (152 bytes) */
    uint64_t   invariant;   /* index (8 bytes) */
    int        occupied;    /* slot written? */
    int        frozen;      /* period-4 protected? */
} sq2_codon_t;

typedef struct {
    sq2_codon_t codons[SQ2_DNA_RING_SIZE];
    int         bin;
    int         shell;
    int         write_head;  /* next slot to write (replication fork) */
    int         length;      /* occupied codons */
    int         alloc_count; /* total writes (for period-4) */
} sq2_strand_t;

typedef struct {
    int gen;        /* which codon position */
    int bin;        /* which strand */
    int shell;      /* which shell */
    uint64_t delta; /* XOR of content (low 40 bits) */
    int bits;       /* popcount of delta */
} sq2_mismatch_t;

typedef struct {
    sq2_strand_t strands[SQ2_DNA_SHELLS][SQ2_DNA_BINS];
    int          total_occupied;
    int          phase;
    int          generation;     /* cell generation (division count) */

    /* Cycle stats */
    int          codons_replicated;
    int          mismatches_found;
    int          repairs_applied;
    int          recombinations;
    int          divisions;
} sq2_cell_t;

/*============================================================================
 * INVARIANT COMPUTATION
 *
 * Delegates to canonical functions in squaragon_v2.h:
 *   sq2_shadow_invariant()   — full invariant with shell encoding
 *   sq2_invariant_content()  — extract low 40 bits for comparison
 *   sq2_gate_fold()          — XOR fold of vertex data
 *============================================================================*/

/* Thin wrapper for DNA-specific naming */
static inline uint64_t sq2_dna_invariant(const sq2_gate_t *gate, int bin, int shell) {
    return sq2_shadow_invariant(gate, bin, shell);
}

static inline uint64_t sq2_dna_content(uint64_t invariant) {
    return sq2_invariant_content(invariant);
}

/*============================================================================
 * STRAND OPERATIONS
 *============================================================================*/

static inline void sq2_strand_init(sq2_strand_t *s, int bin, int shell) {
    memset(s, 0, sizeof(sq2_strand_t));
    s->bin = bin;
    s->shell = shell;
}

/* Write a codon: initialize gate with data, compute invariant, crystallize.
 * The data_seed is used to create unique gate perturbations per codon. */
static inline int sq2_strand_write(sq2_strand_t *s, float data_seed) {
    if (s->write_head >= SQ2_DNA_RING_SIZE) return -1; /* strand full */

    int gen = s->write_head;
    sq2_codon_t *codon = &s->codons[gen];

    /* Initialize gate at shell's scale */
    float scale = 1.0f;
    for (int i = 0; i < s->shell; i++) scale *= SQ2_SCALE_RATIO;
    sq2_init(&codon->gate, scale);

    /* Imprint data: perturb vertices based on data_seed and generation.
     * Each codon gets a unique perturbation pattern. */
    int v_idx = gen % 12;
    codon->gate.vertices[v_idx].x += 0.001f * data_seed;
    codon->gate.vertices[(v_idx + 4) % 12].y += 0.0005f * data_seed * (float)(gen + 1);
    codon->gate.vertices[(v_idx + 8) % 12].z -= 0.0003f * (float)(gen + 1);

    /* Compute invariant */
    codon->invariant = sq2_dna_invariant(&codon->gate, s->bin, s->shell);

    /* Apply seam shift for generational position */
    for (int shift = 0; shift < gen; shift++) {
        codon->invariant = sq2_seam_forward_shift(codon->invariant);
    }

    /* Period-4 protection */
    s->alloc_count++;
    codon->frozen = ((s->alloc_count % 4) == 0) ? 1 : 0;
    codon->occupied = 1;

    s->write_head++;
    s->length++;

    return gen;
}

/* Read a codon: verify invariant, return gate data */
static inline int sq2_strand_read(const sq2_strand_t *s, int gen,
                                   sq2_gate_t *out_gate, uint64_t *out_invariant) {
    if (gen < 0 || gen >= SQ2_DNA_RING_SIZE) return -1;
    if (!s->codons[gen].occupied) return -1;

    if (out_gate) *out_gate = s->codons[gen].gate;
    if (out_invariant) *out_invariant = s->codons[gen].invariant;
    return 0;
}

/* Copy strand (replication): source → destination, seam-shifting invariants */
static inline int sq2_strand_copy(const sq2_strand_t *src, sq2_strand_t *dst) {
    int copied = 0;
    for (int gen = 0; gen < SQ2_DNA_RING_SIZE; gen++) {
        if (!src->codons[gen].occupied) continue;

        sq2_codon_t *d = &dst->codons[gen];

        /* Copy gate data bit-perfect */
        d->gate = src->codons[gen].gate;

        /* Shift invariant to mark as copy (mRNA marker) */
        d->invariant = sq2_seam_forward_shift(src->codons[gen].invariant);

        d->occupied = 1;
        d->frozen = 0;
        dst->length++;
        copied++;
    }
    dst->write_head = src->write_head;
    return copied;
}

/* Compare two strands: XOR content of corresponding codons.
 * Returns number of mismatches found. */
static inline int sq2_strand_compare(const sq2_strand_t *a, const sq2_strand_t *b,
                                      sq2_mismatch_t *mismatches, int max_mismatches) {
    int count = 0;
    for (int gen = 0; gen < SQ2_DNA_RING_SIZE; gen++) {
        if (!a->codons[gen].occupied || !b->codons[gen].occupied) continue;

        /* Compare gate folds directly (not invariants, which differ by seam shift).
         * This is base-pair matching: compare content, ignore frame. */
        uint64_t fold_a = sq2_gate_fold(&a->codons[gen].gate);
        uint64_t fold_b = sq2_gate_fold(&b->codons[gen].gate);
        uint64_t delta = fold_a ^ fold_b;
        if (delta != 0 && count < max_mismatches) {
            mismatches[count].gen = gen;
            mismatches[count].bin = a->bin;
            mismatches[count].shell = a->shell;
            mismatches[count].delta = delta;
            /* popcount */
            int bits = 0;
            uint64_t tmp = delta;
            while (tmp) { bits += tmp & 1; tmp >>= 1; }
            mismatches[count].bits = bits;
            count++;
        }
    }
    return count;
}

/* Repair a mismatch: overwrite destination codon with source's data */
static inline void sq2_strand_repair(const sq2_strand_t *src, sq2_strand_t *dst, int gen) {
    if (gen < 0 || gen >= SQ2_DNA_RING_SIZE) return;
    if (!src->codons[gen].occupied) return;

    dst->codons[gen].gate = src->codons[gen].gate;
    /* Keep the destination's seam-shifted invariant, but recompute from repaired gate */
    dst->codons[gen].invariant = sq2_seam_forward_shift(
        sq2_dna_invariant(&dst->codons[gen].gate, dst->bin, dst->shell)
    );
    for (int shift = 0; shift < gen; shift++) {
        dst->codons[gen].invariant = sq2_seam_forward_shift(dst->codons[gen].invariant);
    }
}

/* Recombine two strands: splice at crossover point.
 * Result gets codons 0..crossover-1 from strand A, crossover..end from strand B. */
static inline void sq2_strand_recombine(const sq2_strand_t *a, const sq2_strand_t *b,
                                         sq2_strand_t *result, int crossover) {
    sq2_strand_init(result, a->bin, a->shell);

    for (int gen = 0; gen < SQ2_DNA_RING_SIZE; gen++) {
        const sq2_strand_t *src = (gen < crossover) ? a : b;
        if (!src->codons[gen].occupied) continue;

        result->codons[gen] = src->codons[gen];
        result->length++;
        if (gen >= result->write_head) result->write_head = gen + 1;
    }
}

/*============================================================================
 * CELL OPERATIONS
 *============================================================================*/

static inline void sq2_cell_init(sq2_cell_t *cell) {
    memset(cell, 0, sizeof(sq2_cell_t));
    cell->phase = SQ2_PHASE_G1;
    for (int shell = 0; shell < SQ2_DNA_SHELLS; shell++) {
        for (int bin = 0; bin < SQ2_DNA_BINS; bin++) {
            sq2_strand_init(&cell->strands[shell][bin], bin, shell);
        }
    }
}

/* Allocate: scatter to bin, write codon on shell 0.
 * Returns total occupied count. */
static inline int sq2_cell_alloc(sq2_cell_t *cell, uint32_t id, uint32_t total,
                                  float data_seed) {
    uint32_t bin = sq2_viviani_scatter_full(id, total);
    sq2_strand_t *s = &cell->strands[0][bin];

    int gen = sq2_strand_write(s, data_seed);
    if (gen >= 0) {
        cell->total_occupied++;
    }
    return cell->total_occupied;
}

/* Replicate: copy all shell 0 strands to shell 1 (S phase) */
static inline int sq2_cell_replicate(sq2_cell_t *cell) {
    cell->phase = SQ2_PHASE_S;
    int total_copied = 0;

    for (int bin = 0; bin < SQ2_DNA_BINS; bin++) {
        sq2_strand_t *src = &cell->strands[0][bin];
        sq2_strand_t *dst = &cell->strands[1][bin];

        int copied = sq2_strand_copy(src, dst);
        total_copied += copied;
        cell->total_occupied += copied;
    }

    cell->codons_replicated = total_copied;
    cell->phase = SQ2_PHASE_G2;
    return total_copied;
}

/* Verify: compare shell 0 vs shell 1, report and repair mismatches (G2 phase) */
static inline int sq2_cell_verify(sq2_cell_t *cell,
                                   sq2_mismatch_t *mismatches, int max_mismatches) {
    cell->phase = SQ2_PHASE_G2;
    int total_mismatches = 0;

    for (int bin = 0; bin < SQ2_DNA_BINS; bin++) {
        sq2_strand_t *src = &cell->strands[0][bin];
        sq2_strand_t *dst = &cell->strands[1][bin];

        int remaining = max_mismatches - total_mismatches;
        if (remaining <= 0) remaining = 0;

        int found = sq2_strand_compare(src, dst,
                                        mismatches + total_mismatches, remaining);
        total_mismatches += found;
    }

    cell->mismatches_found = total_mismatches;
    return total_mismatches;
}

/* Repair all detected mismatches */
static inline int sq2_cell_repair(sq2_cell_t *cell,
                                   const sq2_mismatch_t *mismatches, int count) {
    int repaired = 0;
    for (int i = 0; i < count; i++) {
        int bin = mismatches[i].bin;
        int gen = mismatches[i].gen;
        sq2_strand_repair(&cell->strands[0][bin], &cell->strands[1][bin], gen);
        repaired++;
    }
    cell->repairs_applied += repaired;
    return repaired;
}

/* Divide: split into two daughter cells (M phase).
 * Parent keeps shell 0, daughter gets shell 1. */
static inline void sq2_cell_divide(sq2_cell_t *parent, sq2_cell_t *daughter) {
    parent->phase = SQ2_PHASE_M;

    sq2_cell_init(daughter);
    daughter->generation = parent->generation + 1;

    /* Daughter gets parent's shell 1 as its shell 0 */
    for (int bin = 0; bin < SQ2_DNA_BINS; bin++) {
        daughter->strands[0][bin] = parent->strands[1][bin];
        daughter->strands[0][bin].shell = 0;  /* renumber */
        daughter->total_occupied += daughter->strands[0][bin].length;
    }

    /* Parent keeps shell 0, clears shell 1 */
    int parent_occupied = 0;
    for (int bin = 0; bin < SQ2_DNA_BINS; bin++) {
        sq2_strand_init(&parent->strands[1][bin], bin, 1);
        parent_occupied += parent->strands[0][bin].length;
    }
    parent->total_occupied = parent_occupied;
    parent->generation++;
    parent->divisions++;

    /* Both return to G1 */
    parent->phase = SQ2_PHASE_G1;
    daughter->phase = SQ2_PHASE_G1;
}

/* Query: current capacity metrics */
typedef struct {
    int total_occupied;
    int phase;
    int generation;
    float fill_ratio;
    const char *zone;
} sq2_cell_status_t;

static inline sq2_cell_status_t sq2_cell_status(const sq2_cell_t *cell) {
    sq2_cell_status_t s;
    s.total_occupied = cell->total_occupied;
    s.phase = cell->phase;
    s.generation = cell->generation;
    s.fill_ratio = (float)cell->total_occupied / (float)SQ2_DNA_TOTAL_SLOTS;

    if (cell->total_occupied < SQ2_THRESHOLD_BIAS) s.zone = "G1 (coasting)";
    else if (cell->total_occupied < SQ2_THRESHOLD_WORKING) s.zone = "G1 (active)";
    else if (cell->total_occupied < SQ2_THRESHOLD_MAX) s.zone = "G1 (overdrive)";
    else s.zone = "MUST DIVIDE";

    return s;
}

#ifdef __cplusplus
}
#endif

#endif /* SQUARAGON_V2_DNA_H */
