/* bench_sqfh_ab.c — SQF-H lazy handoff vs a REAL ergo waveform stream.
 *
 * Stream: /tmp/schrod_stream.bin, produced by min/ab/schrod_2d_stream.ergo
 * (identical physics to the AB campaign's stage-1 schrod_2d.ergo, compiled
 * --precision f32): 1600 records x 512 f32 = the row y=Y0 of Re(psi) after
 * each leapfrog step.  A Gaussian packet (SIG0=16, K0=0.4, X0=140) spreads
 * and propagates at v_group ~ 0.155 cells/step across the row.
 *
 * Handoff model: each row is a fresh 8-tile batch (SQFH_BATCH=8) handed
 * over with a journal derived from the BOUND PHYSICS, not fitted:
 *   scale = 1.0                          (same grid, same units)
 *   k     = K0 = 0.4                     (packet mean momentum, program PARAMETER)
 *   A(T)  = 1/sqrt(1 + (T/320)^2)        (2D Gaussian spreading, s0 = SIG0/2 = 8)
 *   phi(T)= K0*(1-X0) - omega*T + pi/2   (cos carrier -> sin reference;
 *          omega = AA*K0^2 = 0.032/step, continuum dispersion E=k^2/2
 *          as stated in the program header)
 * The journal does NOT know the lattice dispersion correction or the
 * spreading chirp; what the tracker does with them IS the measurement.
 *
 * Timing methodology identical to sqfh_cert.c (CLOCK_MONOTONIC per tile),
 * comparable to the 278 ns/tile synthetic baseline.
 *
 * Modes:
 *   (no args)      full logging run: lanes, shares, CSV, in-process counters
 *   --quiet        pure handoff+advance loop only (for perf stat / counters:
 *                  no CSV, no logging lock-in pass)
 *   --filter L     two-pass replay for per-lane counter isolation.
 *                  Pass 1 records lanes (deterministic).  Pass 2 re-runs
 *                  every handoff (tracker state must evolve identically)
 *                  but only tiles whose pass-1 lane == L are timed and
 *                  counted (cp_start/cp_stop bracket just those tiles).
 */
#include "sqfh_core.h"
#include "cache_perf.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define NROWS 1600
#define NX    512
#define NTILES_PER_ROW (NX / SQFH_N)          /* 8 */
#define NTOT  (NROWS * NTILES_PER_ROW)        /* 12800 */

/* stream constants (from min/ab/schrod_2d_stream.ergo PARAMETERs) */
#define K0   0.4
#define AA   0.20
#define X0   140
#define SIG0 16.0                             /* field-envelope sigma at T=0 */
#define S0   8.0                              /* intensity sigma = SIG0/2 */
#define OMEGA (AA * K0 * K0)                  /* 0.032 rad/step (continuum) */
#define VGRP 0.1547                           /* measured lattice v_group,
                                                 AB_FINDINGS.md stage 1 */
/* model-M journal, all closed-form in T from the program PARAMETERs:
 *   t_s    = 2*AA*T                       (Schroedinger time)
 *   chirp  = 2 t_s / (SIG0^4 + 4 t_s^2)   (spreading wavefront curvature;
 *                                          exact Gaussian-packet solution,
 *                                          CONFIRMED against the stream by
 *                                          Hilbert phase fits: c_meas/c is
 *                                          0.95-1.08 over T=100..1600)
 *   sig(T) = SIG0*sqrt(1+(T/320)^2)       (field-envelope spreading law;
 *                                          320 = 2*S0^2/AA ... = sigma0^2/(2*AA)/2)
 *   A(T)   = SIG0/sig(T)                  (2D amplitude decay)
 *   x_c(T) = X0 + VGRP*T                  (measured centroid law)
 *   phi(T) = K0*(1-X0) - OMEGA*T + pi/2   (cos carrier -> sin reference;
 *          continuum omega — lattice dispersion deliberately NOT in
 *          the journal: if it dominates the residual, that is the
 *          next finding) */

static double now_ns(void) {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1e9 + ts.tv_nsec;
}
static int cmpd(const void *a, const void *b) {
    double d = *(const double *)a - *(const double *)b;
    return (d > 0) - (d < 0);
}

static void row_journal(int r, double *A, double *phi, double *chirp,
                        double *esig, double *x0) {
    double T = (double)(r + 1);
    double ts = 2.0 * AA * T;
    double s4 = SIG0 * SIG0 * SIG0 * SIG0;
    *chirp = 2.0 * ts / (s4 + 4.0 * ts * ts);
    double spread = sqrt(1.0 + (T / 320.0) * (T / 320.0));
    *A = 1.0 / spread;
    *esig = SIG0 * spread;
    *x0 = 1.0 - (X0 + VGRP * T);              /* x' of global x=1 */
    *phi = K0 * (1.0 - X0) - OMEGA * T + M_PI / 2.0;
}

static float stream[NROWS][NX];
static uint8_t lane_log[NTOT];

/* one full deterministic pass over the stream.  If lane_filter >= 0,
 * only tiles whose recorded lane matches are timed/counted. */
static double run_pass(int lane_filter, cp_ctx_t *cp, uint64_t cp_acc[CP_NCOUNTERS],
                       uint64_t *lane_counts, double *per_lane_ns,
                       uint64_t per_tile_lane[NTILES_PER_ROW][5],
                       double per_tile_share[NTILES_PER_ROW],
                       uint64_t *silent, FILE *csv) {
    double total_ns = 0;
    for (int r = 0; r < NROWS; r++) {
        double A, phi, chirp, esig, x0;
        row_journal(r, &A, &phi, &chirp, &esig, &x0);
        sqfh_t cpu; sqfh_init_m(&cpu, 1.0, A, K0, phi, chirp, esig, x0);
        for (int j = 0; j < NTILES_PER_ROW; j++) {
            int g = r * NTILES_PER_ROW + j;
            /* -2 = record-only pass (no timing); -1 = full timed pass;
             * >= 0 = timed/counted only on tiles with that lane */
            int count_this = (lane_filter == -1) ||
                             (lane_filter >= 0 &&
                              lane_log[g] == (uint8_t)lane_filter);
            double phi0 = cpu.phi;
            double t0 = 0;
            if (count_this) {
                if (cp && cp->available) cp_start(cp);
                t0 = now_ns();
            }
            int lane = sqfh_handoff(&cpu, &stream[r][j * SQFH_N]);
            if (count_this) {
                double dt = now_ns() - t0;
                total_ns += dt;
                if (per_lane_ns) per_lane_ns[lane] += dt;
                if (cp && cp->available) {
                    cp_stop(cp);
                    for (int c = 0; c < CP_NCOUNTERS; c++)
                        cp_acc[c] += cp->after[c];
                }
            }
            if (lane_filter < 0) lane_log[g] = (uint8_t)lane;
            if (lane_counts) lane_counts[lane]++;
            if (csv) {
                sqfh_t probe = cpu;      /* replay the handoff's own
                                          * lock-in at the pre-handoff
                                          * ledger phase */
                probe.phi = phi0;
                sqfh_mctx_t pm; sqfh_mctx_init(&pm, &probe);
                double al, be, dphi, resid, E;
                sqfh_lockin_m(&pm, &stream[r][j * SQFH_N],
                              &al, &be, &dphi, &resid, &E);
                double share = (E > 0) ? resid / E : 0;
                if (E < 1e-12) (*silent)++;
                per_tile_lane[j][lane]++;
                per_tile_share[j] += share;
                fprintf(csv, "%d,%d,%d,%.6g,%.6g,%.6g\n",
                        r, j, lane, share, dphi, E);
            }
            sqfh_advance(&cpu);
        }
    }
    return total_ns;
}

int main(int argc, char **argv) {
    int quiet = 0, lane_filter = -1;
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--quiet")) quiet = 1;
        else if (!strcmp(argv[i], "--filter") && i + 1 < argc)
            lane_filter = atoi(argv[++i]);
    }

    FILE *f = fopen("/tmp/schrod_stream.bin", "rb");
    if (!f) { perror("open /tmp/schrod_stream.bin"); return 1; }
    if (fread(stream, sizeof(float), (size_t)NROWS * NX, f) != (size_t)NROWS * NX) {
        fprintf(stderr, "short read\n"); return 1;
    }
    fclose(f);

    cp_ctx_t cp; int have_cp = (cp_open(&cp) == 0);
    if (!have_cp)
        fprintf(stderr, "note: perf counters unavailable"
                " (kernel.perf_event_paranoid > 1)\n");

    uint64_t cp_acc[CP_NCOUNTERS] = {0};
    uint64_t lane_counts[5] = {0};
    double per_lane_ns[5] = {0};
    static uint64_t per_tile_lane[NTILES_PER_ROW][5];
    double per_tile_share[NTILES_PER_ROW] = {0};
    uint64_t silent = 0;

    if (lane_filter >= 0) {
        /* pass 1: lane record only (no timing, no counters) */
        run_pass(-2, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
        uint64_t n = 0;
        for (int g = 0; g < NTOT; g++)
            if (lane_log[g] == (uint8_t)lane_filter) n++;
        double tns = run_pass(lane_filter, have_cp ? &cp : NULL, cp_acc,
                              NULL, NULL, NULL, NULL, NULL, NULL);
        const char *nm[5] = {"LINEAR", "SLIP", "SHEAR", "SPIKE", "OVFL"};
        printf("SQFHAB filter=%s n=%llu  mean %.1f ns/tile\n", nm[lane_filter],
               (unsigned long long)n, tns / (n ? n : 1));
        if (have_cp && n) {
            printf("SQFHAB filter_cache  L1d/tile: loads=%.0f misses=%.2f"
                   " (%.3f%%)  LLC/tile: refs=%.1f misses=%.3f"
                   "  instr/tile=%llu\n",
                   (double)cp_acc[CP_L1D_LOADS] / n,
                   (double)cp_acc[CP_L1D_MISSES] / n,
                   100.0 * cp_acc[CP_L1D_MISSES] / (cp_acc[CP_L1D_LOADS] + 1),
                   (double)cp_acc[CP_LLC_REFS] / n,
                   (double)cp_acc[CP_LLC_MISSES] / n,
                   (unsigned long long)(cp_acc[CP_INSTRS] / n));
        }
        if (have_cp) cp_close(&cp);
        return 0;
    }

    FILE *csv = NULL;
    if (!quiet) {
        csv = fopen("/tmp/ab_lanes.csv", "w");
        fprintf(csv, "row,tile,lane,share,dphi,E\n");
    }

    static double tns[NTOT];
    double total_ns;
    if (quiet) {
        total_ns = run_pass(-1, have_cp ? &cp : NULL, cp_acc,
                            lane_counts, per_lane_ns, NULL, NULL, NULL, NULL);
    } else {
        /* full logging pass with per-tile timing recorded */
        total_ns = 0;
        for (int r = 0; r < NROWS; r++) {
            double A, phi, chirp, esig, x0;
            row_journal(r, &A, &phi, &chirp, &esig, &x0);
            sqfh_t cpu; sqfh_init_m(&cpu, 1.0, A, K0, phi, chirp, esig, x0);
            for (int j = 0; j < NTILES_PER_ROW; j++) {
                int g = r * NTILES_PER_ROW + j;
                double phi0 = cpu.phi;
                double t0 = now_ns();
                int lane = sqfh_handoff(&cpu, &stream[r][j * SQFH_N]);
                tns[g] = now_ns() - t0;
                total_ns += tns[g];
                lane_log[g] = (uint8_t)lane;
                lane_counts[lane]++;
                per_lane_ns[lane] += tns[g];
                sqfh_t probe = cpu;
                probe.phi = phi0;
                sqfh_mctx_t pm; sqfh_mctx_init(&pm, &probe);
                double al, be, dphi, resid, E;
                sqfh_lockin_m(&pm, &stream[r][j * SQFH_N],
                              &al, &be, &dphi, &resid, &E);
                double share = (E > 0) ? resid / E : 0;
                if (E < 1e-12) silent++;
                per_tile_lane[j][lane]++;
                per_tile_share[j] += share;
                fprintf(csv, "%d,%d,%d,%.6g,%.6g,%.6g\n",
                        r, j, lane, share, dphi, E);
                sqfh_advance(&cpu);
            }
        }
    }

    printf("SQFHAB stream        %d rows x %d tiles = %d tiles"
           " (ergo schrod_2d f32, row y=Y0)%s\n",
           NROWS, NTILES_PER_ROW, NTOT, quiet ? " [quiet]" : "");
    printf("SQFHAB lanes         lin=%llu slip=%llu shear=%llu spike=%llu"
           " ovfl=%llu  (silent E~0: %llu)\n",
           (unsigned long long)lane_counts[0], (unsigned long long)lane_counts[1],
           (unsigned long long)lane_counts[2], (unsigned long long)lane_counts[3],
           (unsigned long long)lane_counts[4], (unsigned long long)silent);
    printf("SQFHAB cost          mean %.1f ns/tile (synthetic baseline 278)\n",
           total_ns / NTOT);
    if (!quiet) {
        static double sorted[NTOT];
        memcpy(sorted, tns, sizeof sorted);
        qsort(sorted, NTOT, sizeof(double), cmpd);
        printf("SQFHAB cost_dist     median %.1f  p99 %.1f  max %.1f ns/tile\n",
               sorted[NTOT / 2], sorted[(NTOT * 99) / 100], sorted[NTOT - 1]);
        printf("SQFHAB cost_by_lane  ");
        const char *nm[5] = {"LINEAR", "SLIP", "SHEAR", "SPIKE", "OVFL"};
        for (int l = 0; l < 5; l++)
            if (lane_counts[l])
                printf("%s=%.0fns(n=%llu)  ", nm[l],
                       per_lane_ns[l] / lane_counts[l],
                       (unsigned long long)lane_counts[l]);
        printf("\nSQFHAB per_tile_index (x-range -> lane mix, mean resid share):\n");
        for (int j = 0; j < NTILES_PER_ROW; j++) {
            printf("  tile %d x=%3d..%3d  lin=%4llu slip=%4llu shear=%4llu"
                   " oth=%4llu  share=%.4f\n", j, j * 64 + 1, j * 64 + 64,
                   (unsigned long long)per_tile_lane[j][0],
                   (unsigned long long)per_tile_lane[j][1],
                   (unsigned long long)per_tile_lane[j][2],
                   (unsigned long long)(per_tile_lane[j][3] + per_tile_lane[j][4]),
                   per_tile_share[j] / NROWS);
        }
    }
    if (have_cp) {
        printf("SQFHAB cache         L1d loads=%llu misses=%llu (%.3f%%)"
               "  LLC refs=%llu misses=%llu (%.3f%%)  instr/tile=%llu\n",
               (unsigned long long)cp_acc[CP_L1D_LOADS],
               (unsigned long long)cp_acc[CP_L1D_MISSES],
               100.0 * cp_acc[CP_L1D_MISSES] / (cp_acc[CP_L1D_LOADS] + 1),
               (unsigned long long)cp_acc[CP_LLC_REFS],
               (unsigned long long)cp_acc[CP_LLC_MISSES],
               100.0 * cp_acc[CP_LLC_MISSES] / (cp_acc[CP_LLC_REFS] + 1),
               (unsigned long long)(cp_acc[CP_INSTRS] / NTOT));
        cp_close(&cp);
    }
    if (csv) { fclose(csv); printf("SQFHAB lane_log      /tmp/ab_lanes.csv\n"); }
    return 0;
}
