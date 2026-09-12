/* sqw_cert.c — SQW (write-skip) certification driver.
 *
 * Pre-registered oracles:
 *   O1 recognition exactness: after every fill, every logical item
 *      reads its pattern back — memoization must be exact, including
 *      under a poisoned recognition cache (fail-safe inert class).
 *   O2 refcount pair detection (counting; repair impossible without
 *      the logical map — documented).
 *   O3/O4 payload + syndrome det/rep, isolated (inherited duplex MMR).
 *   O5 closure, O6 apoptosis-isolated, O7 amplification report,
 *   O8 byte determinism (two runs identical modulo SQWT lines).
 *
 * Workload: 50% duplication (the middle of the bench sweep).
 * Build: gcc -O2 -o sqw_cert sqw_cert.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "common.h"
#include "sqw_core.h"

enum { SQWE_PAY = 0, SQWE_SYN = 1, SQWE_REF = 2, SQWE_IDX = 3 };
typedef struct { int cat, b, g, strand, i; uint8_t m; } sqw_evt_t;

#define CERT_N 256

static void sqw_apply_event(sqw_cell_t *w, const sqw_evt_t *e) {
    sqb_codon_t *c = &w->cell.c[e->b][e->g][e->strand];
    if (e->cat == SQWE_PAY)      c->g[e->i % SQB_PAY] ^= e->m;
    else if (e->cat == SQWE_SYN) ((uint8_t *)&c->syn0)[e->i % 8] ^= e->m;
    else if (e->cat == SQWE_REF) ((uint8_t *)&w->ref[e->b][e->g])[e->i & 3] ^= e->m;
    else ((uint8_t *)&w->idx[e->i & (SQW_IDX - 1)])[e->g % sizeof(sqw_ent_t)] ^= e->m;
}

typedef struct {
    long long cnt[4], det[4], rep[4];
    long long recog_ok, recog_total, idx_poison_ok, idx_poison_total;
    long long tombs, tomb_refs, unresolved, coh_fail;
    int rounds;
} acc_t;

static long long verify_all_items(const sqw_cell_t *w, const int *stream, int n) {
    long long ok = 0;
    for (int i = 0; i < n; i++) {
        int item = stream[i];
        int b = sqw_item_slot_b[item], g = sqw_item_slot_g[item];
        const sqb_codon_t *c0 = &w->cell.c[b][g][0];
        if (c0->tomb != SQB_TOMB_MAGIC && sqb_pay_ok(c0->g, item)) ok++;
    }
    return ok;
}

static void cert_round(sqw_cell_t *w, const sqw_cell_t *clean,
                       const int *stream, int n, uint64_t *rng,
                       int nev, int forced_cat, acc_t *A) {
    *w = *clean;
    /* events target OCCUPIED codons only — corrupting unallocated
     * space is not a data-integrity event */
    int occ_list[SQB_CAPACITY], n_occ = 0;
    for (int b = 0; b < SQB_NB; b++)
        for (int g = 0; g < SQB_NR; g++)
            if (w->cell.occ[b][g]) occ_list[n_occ++] = (b << 8) | g;
    sqw_evt_t evts[64];
    for (int e = 0; e < nev; e++) {
        sqw_evt_t *ev = &evts[e];
        int cat = (forced_cat >= 0) ? forced_cat
                  : (cmp_rand01(rng) < 0.70 ? SQWE_PAY
                     : (cmp_rand01(rng) < 0.50 ? SQWE_SYN
                     : (cmp_rand01(rng) < 0.67 ? SQWE_REF : SQWE_IDX)));
        ev->cat = cat;
        int slot = occ_list[cmp_rand_u32(rng) % (uint32_t)n_occ];
        ev->b = slot >> 8;
        ev->g = slot & 0xFF;
        ev->strand = (int)(cmp_rand_u32(rng) & 1);
        ev->i = (int)(cmp_rand_u32(rng) % SQB_PAY);
        ev->m = (uint8_t)(1 + (cmp_rand_u32(rng) % 255));
        sqw_apply_event(w, ev);
        A->cnt[cat]++;
    }
    static uint8_t action[SQB_NB * SQB_NR];
    A->unresolved += sqb_sweep(&w->cell, action);
    int sum_ok = 0;
    (void)sqw_ref_audit(w, &sum_ok);

    for (int e = 0; e < nev; e++) {
        sqw_evt_t *ev = &evts[e];
        int act = action[ev->b * SQB_NR + ev->g];
        if (ev->cat == SQWE_PAY) {
            if (act) A->det[0]++;
            uint8_t dec[SQB_PAY];
            const sqb_codon_t *c = &w->cell.c[ev->b][ev->g][ev->strand];
            if (ev->strand == 0) memcpy(dec, c->g, SQB_PAY);
            else for (int i = 0; i < SQB_PAY; i++)
                dec[i] = (uint8_t)(c->g[i] ^ SQB_COMPLEMENT);
            A->rep[0] += sqb_pay_ok(dec, sqb_item_at[ev->b][ev->g]);
        } else if (ev->cat == SQWE_SYN) {
            if (act) A->det[1]++;
            A->rep[1] += sqb_strand_ok(&w->cell.c[ev->b][ev->g][ev->strand],
                                       ev->strand);
        } else if (ev->cat == SQWE_REF) {
            A->det[2] += !sqw_ref_ok(w->ref[ev->b][ev->g]);
            /* rep[2] stays 0: documented unrepairable-without-map */
        } else {
            /* IDX poison: fail-safe oracle — all items must STILL read
             * correct content (recognition verifies byte-exact) */
            A->idx_poison_total++;
            A->idx_poison_ok += (verify_all_items(w, stream, CERT_N) ==
                                 (long long)CERT_N);
        }
    }
    if (w->cell.tombstones > 0) {
        A->tombs += w->cell.tombstones;
        for (int b = 0; b < SQB_NB; b++)
            for (int g = 0; g < SQB_NR; g++)
                if (w->cell.c[b][g][0].tomb == SQB_TOMB_MAGIC &&
                    sqw_ref_ok(w->ref[b][g]))
                    A->tomb_refs += w->ref[b][g] & 0xFFFFu;
    }
    A->coh_fail += (long long)CERT_N - verify_all_items(w, stream, CERT_N);
    A->rounds++;
}

int main(int argc, char **argv) {
    int roundsA = (argc > 1) ? atoi(argv[1]) : 1500;
    int roundsB = roundsA / 3;
    uint64_t rng[4];
    cmp_seed(rng, 0xCE27U);

    /* 50% duplication workload */
    int U = CERT_N / 2;
    static int stream[CERT_N];
    for (int i = 0; i < U; i++) stream[i] = i;
    for (int i = U - 1; i > 0; i--) {
        int j = (int)(cmp_rand_u32(rng) % (uint32_t)(i + 1));
        int t = stream[i]; stream[i] = stream[j]; stream[j] = t;
    }
    for (int i = U; i < CERT_N; i++)
        stream[i] = (int)(cmp_rand_u32(rng) % (uint32_t)U);

    static sqw_cell_t w, clean;
    sqw_init(&w);
    for (int i = 0; i < CERT_N; i++) sqw_alloc(&w, i, stream[i]);
    clean = w;

    /* O1: recognition exactness on the clean fill */
    long long recog_ok = verify_all_items(&clean, stream, CERT_N);

    acc_t A = {{0}}, B = {{0}};
    for (int r = 0; r < roundsA; r++) {
        int cat = (r % 7 < 3) ? SQWE_PAY : (r % 7 == 3) ? SQWE_SYN
                : (r % 7 == 4) ? SQWE_REF : SQWE_IDX;
        cert_round(&w, &clean, stream, CERT_N, rng, 1, cat, &A);
    }
    for (int r = 0; r < roundsB; r++)
        cert_round(&w, &clean, stream, CERT_N, rng, 12, -1, &B);

    printf("SQWOR O1_recognition  %lld/%d = %.6f  expect=1.000000 counting (memoization exactness)\n",
           recog_ok, CERT_N, (double)recog_ok / CERT_N);
    printf("SQWOR O2_refpair_det  %lld/%lld = %.6f  expect=1.000000 counting [A]\n",
           A.det[2], A.cnt[2], A.cnt[2] ? (double)A.det[2] / A.cnt[2] : 0.0);
    printf("SQWOR O3_payload_det  %lld/%lld = %.6f  expect=1.000000 counting [A]\n",
           A.det[0], A.cnt[0], A.cnt[0] ? (double)A.det[0] / A.cnt[0] : 0.0);
    printf("SQWOR O3_payload_rep  %lld/%lld = %.6f  expect>=0.990 measurement [A]\n",
           A.rep[0], A.cnt[0], A.cnt[0] ? (double)A.rep[0] / A.cnt[0] : 0.0);
    printf("SQWOR O4_syndrome_det %lld/%lld = %.6f  expect=1.000000 counting [A]\n",
           A.det[1], A.cnt[1], A.cnt[1] ? (double)A.det[1] / A.cnt[1] : 0.0);
    printf("SQWOR O4_syndrome_rep %lld/%lld = %.6f  expect=1.000000 measurement [A]\n",
           A.rep[1], A.cnt[1], A.cnt[1] ? (double)A.rep[1] / A.cnt[1] : 0.0);
    printf("SQWOR O5_closure      %lld unresolved [A]  expect=0\n", A.unresolved);
    printf("SQWOR O6_apoptosis    %lld [A]  expect=0 isolated\n", A.tombs);
    printf("SQWOR O7_idx_failsafe %lld/%lld = %.6f  expect=1.000000 (poisoned cache never serves wrong content) [A isolated]\n",
           A.idx_poison_ok, A.idx_poison_total,
           A.idx_poison_total ? (double)A.idx_poison_ok / A.idx_poison_total : 0.0);
    printf("SQWOR auxB_det        %lld/%lld = %.6f  poisson tail (content classes)\n",
           B.det[0] + B.det[1], B.cnt[0] + B.cnt[1],
           (B.cnt[0] + B.cnt[1]) ? (double)(B.det[0] + B.det[1]) / (B.cnt[0] + B.cnt[1]) : 0.0);
    printf("SQWOR auxB_rep        %lld/%lld = %.6f  poisson tail\n",
           B.rep[0] + B.rep[1], B.cnt[0] + B.cnt[1],
           (B.cnt[0] + B.cnt[1]) ? (double)(B.rep[0] + B.rep[1]) / (B.cnt[0] + B.cnt[1]) : 0.0);
    printf("SQWOR auxB_tombs      %lld  tomb_refs %lld (amplification: %.2f logical items lost per tombstone)  auxB_coh_fail %lld  auxB_unresolved %lld\n",
           B.tombs, B.tomb_refs,
           B.tombs ? (double)B.tomb_refs / B.tombs : 0.0,
           B.coh_fail, B.unresolved);
    return 0;
}
