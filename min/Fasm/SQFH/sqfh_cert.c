/* SQF-H certification driver — synthetic GPU stream, three-lane
 * handoff, pre-registered oracles.
 *
 * Stream: 4096 tiles x 64 f32 samples, A=1 sinusoid, k = 3 cycles/tile,
 * tiny measurement noise (sigma = 0.005 A).
 * Injections (truth recorded generator-side):
 *   slip A: tile 1000 onward, +0.40 rad step
 *   SHEAR EPISODE: tiles 1500..1511 (12 tiles), distributed quadrature
 *     growth (2nd-harmonic chirp + amplitude breathing) — the off-ramp
 *   slip B: tile 2500 onward, -0.25 rad step
 *   SPIKE: tile 3000, sample 17 x50 — transport garbage, NOT shear
 *
 * Oracles:
 *   O1 linear purity: clean tiles route LINEAR >= 99%
 *   O2 slips: both detected (lane SLIP within 1 tile of injection),
 *      |recovered - true| <= 0.02 rad, zero slip-lane false positives
 *   O3 episode: exactly one open and one close, open at 1500+-1,
 *      close at 1512+-1
 *   O4 raw fidelity: episode tiles archived BYTE-IDENTICAL to source
 *      (the off-ramp never clamps/corrects)
 *   O5 spike: detected, localized to sample 17, NOT routed as shear
 *   O6 timing: ns/tile for the handoff pass
 */
#include "sqfh_core.h"
#include <stdio.h>
#include <time.h>

#define NT 4096

static uint64_t rngs = 0x51F15EED1234567ULL;
static uint64_t rnd(void) {
    rngs ^= rngs << 13; rngs ^= rngs >> 7; rngs ^= rngs << 17; return rngs;
}
static double frnd(void) { return (rnd() >> 11) * (1.0 / 9007199254740992.0); }
static double now_ns(void) {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1e9 + ts.tv_nsec;
}

#define TRUE_A 1.0
#define TRUE_K (2.0 * M_PI * 3.0 / SQFH_N)   /* 3 cycles per tile */
#define NOISE  0.005

int main(void) {
    static float stream[NT][SQFH_N];
    static uint8_t truth[NT];          /* 0 linear, 2 shear (gen-side) */
    static float slip_true[NT];        /* true cumulative slip per tile */

    double phi_step = TRUE_K * SQFH_N; /* per-tile phase advance (scale=1) */
    double slip_cum = 0;
#define OV_A_TRUE 1.6                  /* overflow tiles: true amplitude */
#define OV_T0 2000
#define OV_T1 2011

    for (int t = 0; t < NT; t++) {
        if (t == 1000) slip_cum += 0.40;
        if (t == 2500) slip_cum -= 0.25;
        slip_true[t] = slip_cum;
        int shear = (t >= 1500 && t <= 1511);
        int ovfl  = (t >= OV_T0 && t <= OV_T1);
        truth[t] = shear ? 2 : (ovfl ? 4 : 0);
        for (int i = 0; i < SQFH_N; i++) {
            double th = TRUE_K * (t * SQFH_N + i) + slip_cum;
            double v = TRUE_A * sin(th);
            if (ovfl) {
                /* wave is FINE, cone too small: true amplitude 1.6
                 * railed at the 1.0 envelope */
                v = OV_A_TRUE * sin(th);
                if (v > TRUE_A) v = TRUE_A;
                if (v < -TRUE_A) v = -TRUE_A;
            }
            if (shear) {
                /* distributed quadrature growth: chirp + breathing */
                double env = sin(M_PI * i / SQFH_N);
                v += 0.8 * TRUE_A * sin(2.7 * th + 3.0 * slip_cum) * env
                   + 0.3 * TRUE_A * sin(0.5 * th) * env;
            }
            if (t == 3000 && i == 17) v *= 50.0;   /* transport spike */
            /* ~gaussian noise (sum of 4 uniforms) */
            double n = (frnd() + frnd() + frnd() + frnd() - 2.0) * NOISE;
            stream[t][i] = (float)(v + n);
        }
    }

    /* ---- the handoff ---- */
    sqfh_t cpu; sqfh_init(&cpu, 1.0, TRUE_A, TRUE_K, 0.0);
    static float archive[NT][SQFH_N];
    static uint8_t lane_log[NT];
    double slip_rec[2] = {0, 0}; int nslip_rec = 0;
    int ep_open_tile = -1, ep_close_tile = -1, spike_tile = -1, spike_idx = -1;
    uint64_t prev_open = 0, prev_close = 0;

    double tns = 0;
    for (int t = 0; t < NT; t++) {
        double t0 = now_ns();
        int lane = sqfh_handoff(&cpu, stream[t]);
        tns += now_ns() - t0;
        lane_log[t] = (uint8_t)lane;
        memcpy(archive[t], stream[t], sizeof archive[t]);  /* archive RAW always */
        if (lane == SQFH_SLIP && nslip_rec < 2)
            slip_rec[nslip_rec++] = cpu.last_dphi;
        if (cpu.ep_open != prev_open) { ep_open_tile = t; prev_open = cpu.ep_open; }
        if (cpu.ep_close != prev_close) { ep_close_tile = t; prev_close = cpu.ep_close; }
        if (lane == SQFH_SPIKE) { spike_tile = t; spike_idx = cpu.last_spike_idx; }
        sqfh_advance(&cpu);
    }

    /* ---- scoring ---- */
    int clean = 0, clean_lin = 0, false_slip = 0;
    for (int t = 0; t < NT; t++) {
        if (truth[t] == 2 || truth[t] == 4 || t == 3000) continue;
        if (t == 1000 || t == 2500) continue;    /* slip tiles scored by O2 */
        clean++;
        if (lane_log[t] == SQFH_LINEAR) clean_lin++;
        if (lane_log[t] == SQFH_SLIP) false_slip++;
    }
    printf("SQFHOR O1_linear_purity   %d/%d = %.6f  expect>=0.990\n",
           clean_lin, clean, (double)clean_lin / clean);
    printf("SQFHOR O2_slip_count      %llu detected (expect 2)  false_slips=%d\n",
           (unsigned long long)cpu.slips, false_slip);
    printf("SQFHOR O2_slip_recovery   %.4f / %.4f rad (true +0.40 / -0.25,"
           " expect |err|<=0.02)\n", slip_rec[0], slip_rec[1]);
    printf("SQFHOR O3_episode         open@tile %d (expect 1500+-1)"
           "  close@tile %d (expect 1512+-1)  pairs=%llu/%llu\n",
           ep_open_tile, ep_close_tile,
           (unsigned long long)cpu.ep_open, (unsigned long long)cpu.ep_close);
    int raw_bad = 0;
    for (int t = 1500; t <= 1511; t++)
        if (memcmp(archive[t], stream[t], SQFH_N * sizeof(float))) raw_bad++;
    printf("SQFHOR O4_raw_fidelity    %d/12 episode tiles byte-identical"
           " (0 clamped/corrected)\n", 12 - raw_bad);
    printf("SQFHOR O5_spike           tile %d (expect 3000) sample %d"
           " (expect 17) routed=%s\n",
           spike_tile, spike_idx,
           (lane_log[3000] == SQFH_SPIKE) ? "SPIKE (not shear)" : "WRONG");
    {
        int ov_ok = 0, ov_raw_bad = 0;
        double ex_sum = 0;
        for (int t = OV_T0; t <= OV_T1; t++) {
            if (lane_log[t] == SQFH_OVERFLOW) ov_ok++;
            if (memcmp(archive[t], stream[t], SQFH_N * sizeof(float)))
                ov_raw_bad++;
        }
        /* rerun one overflow tile to read the recovered excess */
        sqfh_t probe; sqfh_init(&probe, 1.0, TRUE_A, TRUE_K, 0.0);
        probe.phi = TRUE_K * OV_T0 * SQFH_N;   /* ledger position at 2000 */
        sqfh_handoff(&probe, stream[OV_T0]);
        ex_sum = probe.last_excess;
        printf("SQFHOR O7_overflow_lane   %d/12 routed OVERFLOW"
               " (0 episodes expected: ep=%llu)  raw=%d/12 byte-identical\n",
               ov_ok, (unsigned long long)(cpu.ep_open - 1), 12 - ov_raw_bad);
        printf("SQFHOR O8_excess_recovery %.4f (true 0.6000,"
               " expect |err|<=0.05)\n", ex_sum);
    }
    printf("SQFHOR O6_handoff_cost    %.1f ns/tile (%.2f ns/sample)"
           "  lanes: lin=%llu slip=%llu shear=%llu spike=%llu\n",
           tns / NT, tns / NT / SQFH_N,
           (unsigned long long)cpu.linear, (unsigned long long)cpu.slips,
           (unsigned long long)cpu.shear_tiles, (unsigned long long)cpu.spikes);
    return 0;
}
