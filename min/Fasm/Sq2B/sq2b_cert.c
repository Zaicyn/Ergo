/* sq2b_cert.c — SQ2B certification driver.
 *
 * Pre-registered oracle table for the biologically-revised cell:
 *   Phase A (isolated): 1 event/round, design point — exact expectations.
 *   Phase B (poisson):  12 events/round — multi-hit tail, aux only.
 *   Blind-class mapping: coordinated dual-strand consistent corruption
 *   (the duplex analogue of the SQ5 moment collision), demonstrated.
 *   Determinism: full runs are byte-identical modulo the SQ2BT line.
 *
 * Build: gcc -O2 -o sq2b_cert sq2b_cert.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "common.h"
#include "squaragon_v2_bio.h"

enum { SQBE_PAY = 0, SQBE_SYN = 1, SQBE_META = 2 };
typedef struct { int cat, b, g, strand, i; uint8_t m; } sqb_evt_t;

static void sqb_apply_event(sqb_cell_t *t, const sqb_evt_t *e) {
    sqb_codon_t *c = &t->c[e->b][e->g][e->strand];
    if (e->cat == SQBE_PAY)      c->g[e->i % SQB_PAY] ^= e->m;
    else if (e->cat == SQBE_SYN) ((uint8_t *)&c->syn0)[e->i % 8] ^= e->m;
    else                         ((uint8_t *)&c->age)[e->i % 8] ^= e->m;
}

typedef struct {
    long long cnt[3], det[3], rep[3];
    long long tombs, slippage, unresolved, retries;
    long long coh_fail;
    int rounds;
} acc_t;

static void cert_round(sqb_cell_t *cell, const sqb_cell_t *clean, uint64_t *rng,
                       int nev, int forced_cat, acc_t *A) {
    *cell = *clean;
    sqb_evt_t evts[64];
    for (int e = 0; e < nev; e++) {
        sqb_evt_t *ev = &evts[e];
        int cat = (forced_cat >= 0) ? forced_cat
                  : (cmp_rand01(rng) < 0.85 ? SQBE_PAY
                     : (cmp_rand01(rng) < 0.60 ? SQBE_SYN : SQBE_META));
        ev->cat = cat;
        ev->b = (int)(cmp_rand_u32(rng) % SQB_NB);
        ev->g = (int)(cmp_rand_u32(rng) % SQB_NR);
        ev->strand = (int)(cmp_rand_u32(rng) & 1);
        ev->i = (int)(cmp_rand_u32(rng) % SQB_PAY);
        ev->m = (uint8_t)(1 + (cmp_rand_u32(rng) % 255));
        sqb_apply_event(cell, ev);
        A->cnt[cat]++;
    }
    static uint8_t action[SQB_NB * SQB_NR];
    A->unresolved += sqb_sweep(cell, action);
    A->tombs += cell->tombstones;
    A->slippage += cell->slippage;
    A->retries += cell->proofread_retries;

    for (int e = 0; e < nev; e++) {
        sqb_evt_t *ev = &evts[e];
        int act = action[ev->b * SQB_NR + ev->g];
        if (ev->cat == SQBE_PAY) {
            if (act) A->det[0]++;
            uint8_t dec[SQB_PAY];
            const sqb_codon_t *c = &cell->c[ev->b][ev->g][ev->strand];
            if (ev->strand == 0) memcpy(dec, c->g, SQB_PAY);
            else for (int i = 0; i < SQB_PAY; i++)
                dec[i] = (uint8_t)(c->g[i] ^ SQB_COMPLEMENT);
            A->rep[0] += sqb_pay_ok(dec, sqb_item_at[ev->b][ev->g]);
        } else if (ev->cat == SQBE_SYN) {
            if (act) A->det[1]++;
            A->rep[1] += sqb_strand_ok(&cell->c[ev->b][ev->g][ev->strand],
                                       ev->strand);
        }
        /* META inert by design */
    }
    for (int b = 0; b < SQB_NB; b++)
        for (int g = 0; g < SQB_NR; g++) {
            if (!cell->occ[b][g]) continue;
            if (cell->c[b][g][0].tomb == SQB_TOMB_MAGIC) { A->coh_fail++; continue; }
            uint8_t rna[SQB_PAY];
            if (sqb_transcribe(cell, b, g, rna) != 0 ||
                !sqb_pay_ok(rna, sqb_item_at[b][g]))
                A->coh_fail++;
        }
    A->rounds++;
}

/* Blind-class mapping: a coordinated hit that corrupts the SAME byte of
 * both strands with the SAME mask keeps the duplex consistent
 * (s1 = v^0x55, s1^m = (v^m)^0x55) — but both stored syndromes then
 * disagree, so a random coordinated hit is DETECTED and apoptosed, never
 * silent.  True blindness requires additionally fixing both syndrome
 * words consistently — a 6-target coordinated attack, constructively
 * demonstrated here (we know the content; a random process does not). */
static void sq2b_blind_pass(const sqb_cell_t *clean, long long *coord_rand_det,
                            long long *coord_rand_tomb, long long *crafted_blind,
                            int trials) {
    sqb_cell_t cell;
    *coord_rand_det = *coord_rand_tomb = *crafted_blind = 0;
    uint64_t rng[4];
    cmp_seed(rng, 0xB11DU);
    for (int t = 0; t < trials; t++) {
        int b = (int)(cmp_rand_u32(rng) % SQB_NB);
        int g = (int)(cmp_rand_u32(rng) % SQB_NR);
        int i = (int)(cmp_rand_u32(rng) % SQB_PAY);
        uint8_t m = (uint8_t)(1 + (cmp_rand_u32(rng) % 255));

        /* (a) random coordinated dual-strand hit */
        cell = *clean;
        cell.c[b][g][0].g[i] ^= m;
        cell.c[b][g][1].g[i] ^= m;
        (void)sqb_sweep(&cell, NULL);
        /* detected if tombstoned or action was taken: tomb is the only
         * possible outcome since both syndromes now disagree */
        if (cell.c[b][g][0].tomb == SQB_TOMB_MAGIC) {
            (*coord_rand_det)++;
            (*coord_rand_tomb)++;
        }

        /* (b) crafted fully-consistent hit: both strands + both
         * syndromes updated to match the corrupted content */
        cell = *clean;
        cell.c[b][g][0].g[i] ^= m;
        cell.c[b][g][1].g[i] ^= m;
        uint8_t dec[SQB_PAY];
        memcpy(dec, cell.c[b][g][0].g, SQB_PAY);
        uint32_t a0, a1;
        sqb_syn(dec, &a0, &a1);
        cell.c[b][g][0].syn0 = a0; cell.c[b][g][0].syn1 = a1;
        cell.c[b][g][1].syn0 = a0; cell.c[b][g][1].syn1 = a1;
        long long un = sqb_sweep(&cell, NULL);
        if (un == 0 && cell.c[b][g][0].tomb != SQB_TOMB_MAGIC)
            (*crafted_blind)++;
    }
}

int main(int argc, char **argv) {
    int roundsA = (argc > 1) ? atoi(argv[1]) : 1500;
    int roundsB = roundsA / 3;
    uint64_t rng[4];
    cmp_seed(rng, 0xCE27U);

    static sqb_cell_t cell, clean;
    sqb_init(&cell);
    for (int i = 0; i < SQB_CAPACITY; i++) sqb_alloc(&cell, i, i);
    clean = cell;

    acc_t A = {{0}}, B = {{0}};
    for (int r = 0; r < roundsA; r++) {
        int cat = (r % 5 < 3) ? SQBE_PAY : (r % 5 == 3) ? SQBE_SYN : SQBE_META;
        cert_round(&cell, &clean, rng, 1, cat, &A);
    }
    for (int r = 0; r < roundsB; r++)
        cert_round(&cell, &clean, rng, 12, -1, &B);

    long long crd = 0, crt = 0, cfb = 0;
    sq2b_blind_pass(&clean, &crd, &crt, &cfb, 2000);

    printf("SQ2BOR O1_payload_det   %lld/%lld = %.6f  expect=1.000000 counting [A]\n",
           A.det[0], A.cnt[0], A.cnt[0] ? (double)A.det[0] / A.cnt[0] : 0.0);
    printf("SQ2BOR O2_payload_rep   %lld/%lld = %.6f  expect>=0.990 measurement [A]\n",
           A.rep[0], A.cnt[0], A.cnt[0] ? (double)A.rep[0] / A.cnt[0] : 0.0);
    printf("SQ2BOR O3_syndrome_det  %lld/%lld = %.6f  expect=1.000000 counting [A]\n",
           A.det[1], A.cnt[1], A.cnt[1] ? (double)A.det[1] / A.cnt[1] : 0.0);
    printf("SQ2BOR O4_syndrome_rep  %lld/%lld = %.6f  expect=1.000000 measurement [A]\n",
           A.rep[1], A.cnt[1], A.cnt[1] ? (double)A.rep[1] / A.cnt[1] : 0.0);
    printf("SQ2BOR O5_closure       %lld unresolved [A]  expect=0\n", A.unresolved);
    printf("SQ2BOR O6_apoptosis     %lld [A]  expect=0 isolated\n", A.tombs);
    printf("SQ2BOR O7_blind_random  %lld/%lld detected+tombstoned (never silent)  expect=1.000000\n",
           crd, (long long)2000, (double)crd / 2000);
    printf("SQ2BOR O8_blind_crafted %lld/%lld blind  expect=all-blind documented-exclusion\n",
           cfb, (long long)2000);
    printf("SQ2BOR auxB_det         %lld/%lld = %.6f  poisson tail\n",
           B.det[0] + B.det[1], B.cnt[0] + B.cnt[1],
           (B.cnt[0] + B.cnt[1]) ? (double)(B.det[0] + B.det[1]) / (B.cnt[0] + B.cnt[1]) : 0.0);
    printf("SQ2BOR auxB_rep         %lld/%lld = %.6f  poisson tail\n",
           B.rep[0] + B.rep[1], B.cnt[0] + B.cnt[1],
           (B.cnt[0] + B.cnt[1]) ? (double)(B.rep[0] + B.rep[1]) / (B.cnt[0] + B.cnt[1]) : 0.0);
    printf("SQ2BOR auxB_tombs       %lld  auxB_coh_fail %lld  auxB_slippage %lld  auxB_unresolved %lld\n",
           B.tombs, B.coh_fail, B.slippage, B.unresolved);
    printf("SQ2BOR aux_proofread_retries %lld (GTP bill, should be 0 absent injection)\n",
           A.retries + B.retries);
    return 0;
}
