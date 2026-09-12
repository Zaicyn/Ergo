/* sq5_cert.c — SQ5 certification driver.
 *
 * Implements the four Wigner-pattern fixes for the SQ5 prototype:
 *   1. audit dump for the independent Python mirror (sq5_mirror.py)
 *   2. full-range injection: payload + stamp + journal bytes
 *   3. pre-registered oracle table (SQ5OR lines, counting vs measurement)
 *   4. collision mapping: crafted moment-preserving corruptions
 *      (3rd-difference quads) to chart the algebraic blindness boundary
 *
 * Two phases, pre-registered:
 *   Phase A (isolated): exactly 1 event per round — the SEC/DED design
 *     point.  O1-O5 oracles are scored here with exact expectations.
 *   Phase B (poisson): 12 events/round over 8 bins — multi-hit tail,
 *     reported as aux statistics, never folded into the counting oracles.
 *
 * Build: gcc -O2 -mavx2 -msse4.1 -o sq5_cert sq5_cert.c -lm
 * Run:   ./sq5_cert [roundsA] > sq5_cert.txt   (writes sq5_audit.txt)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "common.h"
#include "sq5_core.h"

enum { SQ5E_PAY = 0, SQ5E_STAMP = 1, SQ5E_JOUR = 2 };
typedef struct {
    int cat, b, g, shell, i, nbytes;
    uint8_t m[2];
} sq5_evt_t;

static void sq5_apply_event(sq5_torus_t *t, const sq5_evt_t *e) {
    if (e->cat == SQ5E_PAY) {
        for (int k = 0; k < e->nbytes; k++)
            t->pay[e->b][e->g][e->shell][(e->i + k * 7) % SQ5_PAY] ^= e->m[k];
    } else if (e->cat == SQ5E_STAMP) {
        ((uint8_t *)&t->stamp[e->b][e->g][e->shell])[e->i & 3] ^= e->m[0];
    } else {
        ((uint8_t *)&t->jr[e->b][e->shell])[e->i % (int)sizeof(sq5_journal_t)] ^= e->m[0];
    }
}

/* ---------------- audit dump (mirror input) ---------------- */
static void dump_hex(FILE *f, const char *tag, const void *p, size_t nb) {
    const uint8_t *b = (const uint8_t *)p;
    fprintf(f, "%s ", tag);
    for (size_t i = 0; i < nb; i++) fprintf(f, "%02x", b[i]);
    fputc('\n', f);
}

static void sq5_audit_dump(const char *path, const sq5_torus_t *clean,
                           const sq5_torus_t *corrupt, const sq5_torus_t *repaired,
                           const sq5_evt_t *evts, long long nev,
                           const sq5_decision_t *dec, long long stamp_flagged) {
    FILE *f = fopen(path, "w");
    if (!f) { perror("audit"); return; }
    fprintf(f, "HDR %d %d %d\n", SQ5_NB, SQ5_NR, SQ5_PAY);
    dump_hex(f, "CLEAN_OCC",   clean->occ,   sizeof(clean->occ));
    dump_hex(f, "CLEAN_PAY",   clean->pay,   sizeof(clean->pay));
    dump_hex(f, "CLEAN_STAMP", clean->stamp, sizeof(clean->stamp));
    dump_hex(f, "CLEAN_JR",    clean->jr,    sizeof(clean->jr));
    fprintf(f, "EVENTS %lld\n", nev);
    for (long long e = 0; e < nev; e++)
        fprintf(f, "EV %d %d %d %d %d %d %u %u\n",
                evts[e].cat, evts[e].b, evts[e].g, evts[e].shell,
                evts[e].i, evts[e].nbytes, evts[e].m[0], evts[e].m[1]);
    dump_hex(f, "CORR_PAY",   corrupt->pay,   sizeof(corrupt->pay));
    dump_hex(f, "CORR_STAMP", corrupt->stamp, sizeof(corrupt->stamp));
    dump_hex(f, "CORR_JR",    corrupt->jr,    sizeof(corrupt->jr));
    for (int b = 0; b < SQ5_NB; b++)
        fprintf(f, "DEC %d %d %d %d %d %d %d %d\n", b,
                dec[b].flags, dec[b].cls,
                dec[b].sec_p[0], dec[b].sec_p[1],
                dec[b].tier[0], dec[b].tier[1], dec[b].unresolved);
    fprintf(f, "STAMP_FLAGGED %lld\n", stamp_flagged);
    dump_hex(f, "REP_PAY",   repaired->pay,   sizeof(repaired->pay));
    dump_hex(f, "REP_STAMP", repaired->stamp, sizeof(repaired->stamp));
    dump_hex(f, "REP_JR",    repaired->jr,    sizeof(repaired->jr));
    fclose(f);
}

/* ---------------- collision mapping ----------------
 * A 3rd-difference quad at consecutive linear positions o..o+3 with
 * deltas (d, -3d, 3d, -d) preserves s0, s1 AND s2 exactly (4th finite
 * difference of a quadratic is zero), hence is invisible to every
 * residual — both streams AND the cross-shell residual are built from
 * the same three moments.  Realizable when all four shifted bytes stay
 * in [0,255].  We scan, apply, and confirm flags == 0. */
static long long sq5_collision_pass(sq5_torus_t *t, long long *applied,
                                    long long *realizable_quads) {
    long long blind = 0;
    *applied = 0;
    *realizable_quads = 0;
    for (int b = 0; b < SQ5_NB; b++) {
        for (int s = 0; s < 2; s++) {
            for (int o = 0; o + 3 < SQ5_BINBYTES; o++) {
                if (!t->occ[b][(o + 3) / SQ5_PAY][s]) continue;
                uint8_t *p0 = &t->pay[b][o / SQ5_PAY][s][o % SQ5_PAY];
                uint8_t *p1 = &t->pay[b][(o + 1) / SQ5_PAY][s][(o + 1) % SQ5_PAY];
                uint8_t *p2 = &t->pay[b][(o + 2) / SQ5_PAY][s][(o + 2) % SQ5_PAY];
                uint8_t *p3 = &t->pay[b][(o + 3) / SQ5_PAY][s][(o + 3) % SQ5_PAY];
                for (int d = 1; d <= 8; d++) {
                    if ((int)*p0 + d > 255 || (int)*p1 < 3 * d ||
                        (int)*p2 + 3 * d > 255 || (int)*p3 < d) continue;
                    (*realizable_quads)++;
                    if (*applied < 2000) {
                        *p0 = (uint8_t)(*p0 + d);
                        *p1 = (uint8_t)(*p1 - 3 * d);
                        *p2 = (uint8_t)(*p2 + 3 * d);
                        *p3 = (uint8_t)(*p3 - d);
                        (*applied)++;
                        uint32_t ds[2][3];
                        if (sq5_flux_bin(t, b, ds) == 0) blind++;
                        *p0 = (uint8_t)(*p0 - d);
                        *p1 = (uint8_t)(*p1 + 3 * d);
                        *p2 = (uint8_t)(*p2 - 3 * d);
                        *p3 = (uint8_t)(*p3 + d);
                    }
                    break;
                }
            }
        }
    }
    return blind;
}

typedef struct {
    long long cnt[3], det[3], rep_ok[3];
    long long jour_arb_ok, coh_fail, unresolved, anomalies, stamp_flag;
    double t_full, t_simple;
    int rounds;
} cert_acc_t;

/* one round: inject nev events into a fresh copy of clean, run full
 * validation + repair, score every event; also time legacy validation
 * on the identical corrupted state. */
static void cert_round(sq5_torus_t *torus, const sq5_torus_t *clean,
                       uint64_t *rng, int nev, int cat_cycle, int round_idx,
                       cert_acc_t *A, sq5_torus_t *scratch, int do_dump) {
    *torus = *clean;
    static sq5_evt_t evts[64];
    for (int e = 0; e < nev; e++) {
        sq5_evt_t *ev = &evts[e];
        int cat;
        if (cat_cycle >= 0)
            cat = cat_cycle;                 /* phase A: forced category */
        else {
            double u = cmp_rand01(rng);      /* phase B: 70/15/15 */
            cat = (u < 0.70) ? SQ5E_PAY : (u < 0.85) ? SQ5E_STAMP : SQ5E_JOUR;
        }
        ev->cat = cat;
        if (cat == SQ5E_PAY) {
            ev->b = (int)(cmp_rand_u32(rng) % SQ5_NB);
            ev->g = (int)(cmp_rand_u32(rng) % SQ5_NR);
            ev->shell = (int)(cmp_rand_u32(rng) & 1);
            ev->nbytes = (cmp_rand01(rng) < 0.8) ? 1 : 2;
            ev->i = (int)(cmp_rand_u32(rng) % SQ5_PAY);
            for (int k = 0; k < ev->nbytes; k++)
                ev->m[k] = (uint8_t)(1 + (cmp_rand_u32(rng) % 255));
        } else if (cat == SQ5E_STAMP) {
            ev->b = (int)(cmp_rand_u32(rng) % SQ5_NB);
            ev->g = (int)(cmp_rand_u32(rng) % SQ5_NR);
            ev->shell = (int)(cmp_rand_u32(rng) & 1);
            ev->nbytes = 1;
            ev->i = (int)(cmp_rand_u32(rng) % 4);
            ev->m[0] = (uint8_t)(1 + (cmp_rand_u32(rng) % 255));
        } else {
            ev->b = (int)(cmp_rand_u32(rng) % SQ5_NB);
            ev->g = 0;
            ev->shell = (int)(cmp_rand_u32(rng) & 1);
            ev->nbytes = 1;
            ev->i = (int)(cmp_rand_u32(rng) % sizeof(sq5_journal_t));
            ev->m[0] = (uint8_t)(1 + (cmp_rand_u32(rng) % 255));
        }
        sq5_apply_event(torus, ev);
        A->cnt[cat]++;
    }

    static sq5_decision_t dec[SQ5_NB];
    uint64_t stamp_badmap[8];

    double t0 = cmp_now_sec();
    memset(stamp_badmap, 0, sizeof(stamp_badmap));
    for (int b = 0; b < SQ5_NB; b++)
        sq5_classify_bin(torus, b, &dec[b], 1);
    long long sflag = sq5_stamp_check(torus, 0, stamp_badmap);
    double t1 = cmp_now_sec();
    for (int b = 0; b < SQ5_NB; b++)
        sq5_apply_repair(torus, b, &dec[b]);
    sq5_stamp_check(torus, 1, NULL);
    double t2 = cmp_now_sec();
    A->t_full += (t1 - t0) + (t2 - t1);
    A->stamp_flag += sflag;

    /* legacy validation on the identical corrupted state (timing only) */
    *scratch = *clean;
    for (int e = 0; e < nev; e++) sq5_apply_event(scratch, &evts[e]);
    double t3 = cmp_now_sec();
    static sq5_decision_t dec0[SQ5_NB];
    for (int b = 0; b < SQ5_NB; b++) {
        sq5_classify_bin(scratch, b, &dec0[b], 0);
        sq5_apply_repair(scratch, b, &dec0[b]);
    }
    double t4 = cmp_now_sec();
    A->t_simple += (t4 - t3);

    if (do_dump) {
        static sq5_torus_t corrupt_snap;
        corrupt_snap = *clean;
        for (int e = 0; e < nev; e++) sq5_apply_event(&corrupt_snap, &evts[e]);
        sq5_audit_dump("sq5_audit.txt", clean, &corrupt_snap, torus,
                       evts, nev, dec, sflag);
    }

    for (int e = 0; e < nev; e++) {
        sq5_evt_t *ev = &evts[e];
        int d0 = 0, rp = 0;
        if (ev->cat == SQ5E_PAY) {
            const sq5_decision_t *dd = &dec[ev->b];
            if ((ev->shell == 0 &&
                 (dd->cls == SQ5C_PAY0 || dd->cls == SQ5C_PAY_BOTH)) ||
                (ev->shell == 1 &&
                 (dd->cls == SQ5C_PAY1 || dd->cls == SQ5C_PAY_BOTH)))
                d0 = 1;
            rp = sq5_pay_ok(torus->pay[ev->b][ev->g][ev->shell],
                            sq5_item_at[ev->b][ev->g]);
        } else if (ev->cat == SQ5E_STAMP) {
            int slot = (ev->b * SQ5_NR + ev->g) * 2 + ev->shell;
            d0 = (int)((stamp_badmap[slot >> 6] >> (slot & 63)) & 1ULL);
            rp = (torus->stamp[ev->b][ev->g][ev->shell] ==
                  sq5_stamp(ev->b, ev->g, ev->shell));
        } else {
            const sq5_decision_t *dd = &dec[ev->b];
            if (dd->flags & (ev->shell == 0 ? SQ5F_R0 : SQ5F_R1)) d0 = 1;
            sq5_journal_t want = {0, 0, 0};
            for (int g = 0; g < SQ5_NR; g++)
                if (torus->occ[ev->b][g][ev->shell])
                    sq5_journal_add(&want, torus->pay[ev->b][g][ev->shell], g);
            rp = (want.s0 == torus->jr[ev->b][ev->shell].s0 &&
                  want.s1 == torus->jr[ev->b][ev->shell].s1 &&
                  want.s2 == torus->jr[ev->b][ev->shell].s2);
            if (ev->shell == 0 && dd->cls == SQ5C_JOUR0) A->jour_arb_ok++;
            if (ev->shell == 1 && dd->cls == SQ5C_JOUR1) A->jour_arb_ok++;
        }
        A->det[ev->cat] += d0;
        A->rep_ok[ev->cat] += rp;
    }

    for (int b = 0; b < SQ5_NB; b++) {
        A->unresolved += dec[b].unresolved;
        if (dec[b].cls == SQ5C_ANOMALY) A->anomalies++;
    }

    for (int b = 0; b < SQ5_NB; b++)
        for (int g = 0; g < SQ5_NR; g++)
            for (int s = 0; s < 2; s++)
                if (torus->occ[b][g][s] &&
                    !sq5_pay_ok(torus->pay[b][g][s], sq5_item_at[b][g]))
                    A->coh_fail++;
    A->rounds++;
}

int main(int argc, char **argv) {
    int roundsA = (argc > 1) ? atoi(argv[1]) : 1500;
    int roundsB = roundsA / 3;
    uint64_t rng[4];
    cmp_seed(rng, 0xCE27U);

    static sq5_torus_t torus, clean, scratch;
    sq5_tin(&torus);
    for (int i = 0; i < SQ5_CAPACITY; i++) sq5_alloc(&torus, i, i);
    long long fb = 0;
    sq5_rep(&torus, &fb);
    clean = torus;

    cert_acc_t A = {{0}}, B = {{0}};

    /* ---- Phase A: isolated events (design point), categories cycled
     * deterministically: 3 payload / 1 stamp / 1 journal per 5 ---- */
    for (int r = 0; r < roundsA; r++) {
        int cat = (r % 5 < 3) ? SQ5E_PAY : (r % 5 == 3) ? SQ5E_STAMP : SQ5E_JOUR;
        cert_round(&torus, &clean, rng, 1, cat, r, &A, &scratch, 0);
    }

    /* ---- Phase B: poisson tail, 12 events/round; audit dump on the
     * first round feeds the independent mirror ---- */
    for (int r = 0; r < roundsB; r++)
        cert_round(&torus, &clean, rng, 12, -1, r, &B, &scratch, r == 0);

    /* ---- collision mapping ---- */
    torus = clean;
    long long col_applied = 0, col_quads = 0;
    long long col_blind = sq5_collision_pass(&torus, &col_applied, &col_quads);

    /* ---------------- pre-registered oracle table ---------------- */
    printf("SQ5OR O1_payload_det  %lld/%lld = %.6f  expect=1.000000 counting [A]\n",
           A.det[0], A.cnt[0], A.cnt[0] ? (double)A.det[0] / A.cnt[0] : 0.0);
    printf("SQ5OR O2_stamp_det    %lld/%lld = %.6f  expect=1.000000 counting [A]\n",
           A.det[1], A.cnt[1], A.cnt[1] ? (double)A.det[1] / A.cnt[1] : 0.0);
    printf("SQ5OR O3_journal_det  %lld/%lld = %.6f  expect=1.000000 counting [A]\n",
           A.det[2], A.cnt[2], A.cnt[2] ? (double)A.det[2] / A.cnt[2] : 0.0);
    printf("SQ5OR O4_payload_rep  %lld/%lld = %.6f  expect>=0.990000 measurement [A]\n",
           A.rep_ok[0], A.cnt[0], A.cnt[0] ? (double)A.rep_ok[0] / A.cnt[0] : 0.0);
    printf("SQ5OR O5_arbitration  %lld/%lld = %.6f  expect=1.000000 measurement [A isolated]\n",
           A.jour_arb_ok, A.cnt[2], A.cnt[2] ? (double)A.jour_arb_ok / A.cnt[2] : 0.0);
    printf("SQ5OR O6_coh_fail     %lld slots [A]  expect=0\n", A.coh_fail);
    printf("SQ5OR O7_collision    %lld/%lld blind of applied; %lld realizable quads mapped  expect=all-blind documented-exclusion\n",
           col_blind, col_applied, col_quads);
    printf("SQ5OR O8_mirror_diff  see sq5_mirror.py verdict  expect=0 construction\n");
    printf("SQ5OR auxB_det        %lld/%lld = %.6f  poisson tail, no expectation\n",
           B.det[0] + B.det[1] + B.det[2], B.cnt[0] + B.cnt[1] + B.cnt[2],
           (B.cnt[0] + B.cnt[1] + B.cnt[2])
               ? (double)(B.det[0] + B.det[1] + B.det[2]) /
                 (B.cnt[0] + B.cnt[1] + B.cnt[2]) : 0.0);
    printf("SQ5OR auxB_rep        %lld/%lld = %.6f  poisson tail (multi-hit DED limit)\n",
           B.rep_ok[0] + B.rep_ok[1] + B.rep_ok[2], B.cnt[0] + B.cnt[1] + B.cnt[2],
           (B.cnt[0] + B.cnt[1] + B.cnt[2])
               ? (double)(B.rep_ok[0] + B.rep_ok[1] + B.rep_ok[2]) /
                 (B.cnt[0] + B.cnt[1] + B.cnt[2]) : 0.0);
    printf("SQ5OR auxB_coh_fail   %lld slots  auxB_unresolved %lld  auxB_anomalies %lld  auxB_stamp_flagged %lld\n",
           B.coh_fail, B.unresolved, B.anomalies, B.stamp_flag);
    printf("SQ5T full_A=%.0f legacy_A=%.0f full_B=%.0f legacy_B=%.0f ns_per_round roundsA=%d roundsB=%d\n",
           A.t_full * 1e9 / A.rounds, A.t_simple * 1e9 / A.rounds,
           B.t_full * 1e9 / B.rounds, B.t_simple * 1e9 / B.rounds,
           roundsA, roundsB);
    return 0;
}
