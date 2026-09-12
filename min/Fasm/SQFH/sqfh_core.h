/* SQF-H — lazy GPU→CPU handoff with an analytic waveform prior.
 *
 * The design conversation: the forward pass (GPU) is raw from the
 * source and needs no correction.  The CPU receives tiles (4-8 units
 * per batch), and validates them against the bound physics: the
 * tracked waveform's (scale, A, k, phi).  Validation = lock-in
 * quadrature demodulation — one pass, the same read the handoff
 * already pays for.
 *
 * Three lanes (the quaternion structure: scalar amplitude, I/Q
 * rotation plane):
 *   1. LINEAR  — I matches, Q ~ 0: constructive superposition,
 *      predictable flow.  Archive raw, advance the phase ledger.
 *   2. SLIP    — Q/I = tan(dphi): the tile is the same waveform at a
 *      dilated phase.  Rotation on the imaginary axis, not damage.
 *      Adopt phi += dphi (phase/time dilation to stay synced), loud.
 *   3. SHEAR   — residual energy no rotation can absorb: curl, a
 *      bifurcation, a new degree of freedom.  THE OFF-RAMP: archive
 *      RAW AND COMPLETE under an episode tag (never clamped, never
 *      corrected — it is physical data), suspend the analytic prior,
 *      track locally until Q collapses back (on-ramp), resync the
 *      ledger with the measured phase the episode consumed.
 *   Transport spike (localized garbage) is separated from shear by
 *   concentration: one sample carrying >50% of residual energy is a
 *   spike (quarantine the sample, tile stays tracked); distributed
 *   residual is true shear.
 *
 * Extended prior (model M): a real-engine wave packet is NOT a bare
 * sinusoid per tile — it carries analytic envelope and wavefront
 * curvature.  Model M adds two closed-form terms to the reference:
 *   theta_i = phi + k*scale*i + chirp*(x0+i)^2   (quadratic phase)
 *   env_i   = exp(-(x0+i)^2 / env_sig^2)         (Gaussian envelope)
 *   w_i = env_i * (alpha*sin(theta_i) + beta*cos(theta_i)),  LS fit.
 * The journal tuple becomes (scale, A, k, chirp, env_sig, x_c, phi).
 * With chirp == 0 and env_sig == 0 the cell is BIT-IDENTICAL to the
 * bare-sinusoid cell (dispatch in sqfh_handoff); sqfh_cert.c is the
 * regression net.  Cost discipline: both terms are exact under
 * second-order recurrences (the rotation step itself rotates by
 * 2*chirp per sample; the envelope ratio by exp(-2/env_sig^2)) —
 * one shared per-tile context: 3 sincos + 3 exp per TILE, no
 * transcendentals per sample.
 *
 * Nothing upstream has to know anything: no GPU flags, no feedback
 * to the forward path.  Shear is self-announcing on the Q axis.
 */
/* for sincos(3) — must precede any libc header (this header is
 * included first in its benchmark drivers) */
#if defined(__GNUC__) && !defined(_GNU_SOURCE)
#define _GNU_SOURCE
#endif
#ifndef SQFH_CORE_H
#define SQFH_CORE_H

#include <stdint.h>
#include <string.h>
#include <math.h>

#if defined(__GNUC__)
#define SQFH_SINCOS(x, sp, cp) sincos(x, sp, cp)
#else
#define SQFH_SINCOS(x, sp, cp) do { *(sp) = sin(x); *(cp) = cos(x); } while (0)
#endif

#define SQFH_N      64        /* samples per tile (one unit) */
#define SQFH_BATCH  8         /* tiles per handoff batch */

/* lane codes */
#define SQFH_LINEAR   0
#define SQFH_SLIP     1
#define SQFH_SHEAR    2
#define SQFH_SPIKE    3
#define SQFH_OVERFLOW 4

/* thresholds (physical, not clamps: they route, they never alter) */
#define SQFH_RES_SHEAR   0.02   /* residual/E beyond any rotation */
#define SQFH_SLIP_TOL    0.01   /* rad: below this, ledger noise   */
#define SQFH_SPIKE_SHARE 0.50   /* one sample > 50% residual = spike */
#define SQFH_RAIL_FRAC   0.05   /* >5% of samples pinned at rail = overflow */
#define SQFH_RAIL_TOL    0.98   /* |w| >= 0.98*A_env counts as railed */
/* numerical silence floor (model M only): below this tile energy the
 * f32 stream is quantization/underflow garbage and classification is
 * meaningless.  Scale: f32 roundoff over a tile is ~N*(2^-24*A)^2 ~
 * 2e-13*A^2; real packet tails in the schrod engine are >= 1e-7.
 * Measured: every spike false positive on the real stream had
 * E < 4e-14.  The floor is a property of the f32 wire format, not a
 * physics tuning knob.  (A second effect: denormal f64 arithmetic in
 * the recurrences is microcoded on this CPU — the gate also removes
 * that 5-10x slow path.) */
#define SQFH_E_FLOOR     1e-12

typedef struct {
    /* the analytic prior — the journal is four wave parameters */
    double scale;          /* GPU grid → CPU grid scaling */
    double A, k, phi;      /* amplitude, wavenumber, phase ledger */

    /* model M extension: quadratic phase + Gaussian envelope.
     * chirp == 0 && env_sig == 0 selects the legacy bare-sinusoid
     * path (bit-identical).  x0 is the envelope-relative coordinate
     * (x - x_c) of the CURRENT tile's first sample; sqfh_advance
     * carries it by SQFH_N*scale like the phase ledger. */
    double chirp;          /* theta += chirp * (x0+i)^2 */
    double env_sig;        /* Gaussian envelope sigma, 0 = flat */
    double x0;             /* x' of first sample of current tile */
    /* row-constant recurrence seeds cached by sqfh_init_m (never read
     * on the legacy path): step-of-step rotator and envelope ratio */
    double qc, qs, rho;

    int     episode;       /* 0 = tracking, 1 = shear episode */
    double  ep_phi0;       /* ledger phase at episode open */
    double  ep_phi_used;   /* measured phase the episode consumed */

    /* stats */
    uint64_t tiles, linear, slips, shear_tiles, spikes, overflows;
    uint64_t ep_open, ep_close;
    int      last_lane;
    double   last_dphi, last_resid_share;
    int      last_spike_idx;
    double   last_excess;    /* recovered amplitude beyond the envelope */
} sqfh_t;

/* Clipper describing function: fundamental surviving a rail at A_env
 * when the true amplitude is A.  Phase and zero-crossings survive
 * clipping, so the excess is INVERTIBLE from the measured
 * fundamental M = 2*sqrt(I^2+Q^2)/N. */
static inline double sqfh_clip_fundamental(double A, double A_env) {
    if (A <= A_env) return A;
    double r = A_env / A;
    return A * (2.0 / M_PI) * (asin(r) + r * sqrt(1.0 - r * r));
}

/* bisection inversion: recover true A from measured fundamental M */
/* M range is [0, 4/pi * A_env]: a fully squared-off wave's
 * fundamental is 4/pi x rail.  (The earlier "M >= A_env -> deeply
 * railed" shortcut was wrong: M legitimately exceeds A_env for any
 * real clipping.)  Beyond 4/pi: unbounded amplitude, return the
 * loudest lower bound. */
static inline double sqfh_recover_amplitude(double M, double A_env) {
    double lo = A_env, hi = A_env * 2.0;
    while (sqfh_clip_fundamental(hi, A_env) < M && hi < 1e9) hi *= 2.0;
    for (int it = 0; it < 60; it++) {
        double mid = 0.5 * (lo + hi);
        if (sqfh_clip_fundamental(mid, A_env) < M) lo = mid; else hi = mid;
    }
    return 0.5 * (lo + hi);
}

static void sqfh_init(sqfh_t *t, double scale, double A, double k, double phi) {
    memset(t, 0, sizeof *t);
    t->scale = scale; t->A = A; t->k = k; t->phi = phi;
}

/* model M init: chirp (rad/cell^2), env_sig (cells), x0 = (x_first - x_c).
 * Caches the row-constant recurrence seeds so the per-tile context
 * setup is 2 sincos + 2 exp (not 3 + 3). */
static void sqfh_init_m(sqfh_t *t, double scale, double A, double k, double phi,
                        double chirp, double env_sig, double x0) {
    sqfh_init(t, scale, A, k, phi);
    t->chirp = chirp; t->env_sig = env_sig; t->x0 = x0;
    SQFH_SINCOS(2.0 * chirp, &t->qs, &t->qc);
    t->rho = exp(-2.0 / (env_sig * env_sig));
}

/* lock-in demodulation: one pass over the tile.
 * I, Q   — projections onto the reference at (k, phi)
 * dphi   — rotation that best explains the tile (atan2(Q,I))
 * resid  — energy no sinusoid at (k, any phase) can explain
 * E      — total tile energy                                          */
static inline void sqfh_lockin(const float *w, double k, double phi,
                               double scale,
                               double *I, double *Q, double *dphi,
                               double *resid, double *E) {
    /* per-sample phase step is constant -> Chebyshev rotation
     * recurrence instead of 64 cos/sin calls (the serial-latency
     * lesson again: transcendentals on the hot path).  Two trig
     * calls per TILE, f64 drift over 64 steps ~1e-14. */
    double cd = cos(k * scale), sd = sin(k * scale);
    double c = cos(phi), s = sin(phi);
    double sI = 0, sQ = 0, sE = 0;
    for (int i = 0; i < SQFH_N; i++) {
        sI += w[i] * c;
        sQ += w[i] * s;
        sE += (double)w[i] * w[i];
        double cn = c * cd - s * sd;
        s = s * cd + c * sd;
        c = cn;
    }
    double explained = 2.0 * (sI * sI + sQ * sQ) / SQFH_N;
    *I = sI; *Q = sQ;
    /* sin-reference convention: w = sin(th + slip) gives
     * Q ~ (N/2)cos(slip), I ~ (N/2)sin(slip) -> dphi = atan2(I, Q).
     * (atan2(Q,I) = pi/2 - slip was the swapped-quadrature bug:
     * the ledger chased pi/2 forever and never settled.) */
    *dphi = atan2(sI, sQ);
    *resid = sE - explained;
    *E = sE;
}

/* per-sample residual after removing the best-fit sinusoid — used to
 * separate a transport spike (localized) from shear (distributed) */
static inline int sqfh_spike_localize(const float *w, double Afit,
                                      double k, double phi_eff, double scale,
                                      double *share_out) {
    double cd = cos(k * scale), sd = sin(k * scale);
    double c = cos(phi_eff), s = sin(phi_eff);
    double worst = 0, total = 0;
    int wi = -1;
    for (int i = 0; i < SQFH_N; i++) {
        double r = w[i] - Afit * s;
        double r2 = r * r;
        total += r2;
        if (r2 > worst) { worst = r2; wi = i; }
        double cn = c * cd - s * sd;
        s = s * cd + c * sd;
        c = cn;
    }
    *share_out = (total > 0) ? worst / total : 0;
    return wi;
}

/* ---- model M: chirped, enveloped reference ---------------------------
 * theta_i = phi + k*scale*i + chirp*(x0+i)^2
 * env_i   = exp(-(x0+i)^2 / env_sig^2)
 * fit w_i = env_i*(alpha*sin(theta_i) + beta*cos(theta_i)) by least
 * squares: 2x2 normal system on the env^2-weighted basis moments,
 * summed in the SAME single pass.
 *
 * Both terms are EXACT under second-order recurrences:
 *   the per-sample phase step grows linearly -> the step rotator
 *     (mc,ms) itself rotates by the constant 2*chirp per sample;
 *   env_{i+1} = env_i*r_i with r_{i+1} = r_i*rho, rho = exp(-2/sig^2)
 *     constant — a Gaussian is exact under a rotating ratio.
 * The env^2-weighted moments need cos/sin of 2*theta: obtained per
 * sample from the theta rotator by squaring (c^2-s^2, 2sc) — no
 * double-angle rotators, no extra trig.
 *
 * Cost discipline: the per-tile setup is a context (sqfh_mctx_t) —
 * 3 sincos + 3 exp TOTAL per tile, shared by the lock-in, the rail
 * scan, the spike localizer and the overflow re-fit (each works on a
 * local copy).  Per sample: ~30 flops, zero transcendentals.
 * alpha = sine-basis coefficient, beta = cosine-basis coefficient;
 * dphi = atan2(beta, alpha) matches the legacy atan2(I, Q). */
typedef struct {
    double c, s;         /* theta rotator at sample 0 (ledger phi) */
    double mc, ms;       /* per-sample step rotator */
    double qc, qs;       /* step-of-step (constant angle 2*chirp) */
    double env, r, rho;  /* Gaussian envelope recurrence */
} sqfh_mctx_t;

static inline void sqfh_mctx_init(sqfh_mctx_t *m, const sqfh_t *t) {
    double th0 = t->phi + t->chirp * t->x0 * t->x0;
    double d0  = t->k * t->scale + t->chirp * (2.0 * t->x0 + 1.0);
    SQFH_SINCOS(th0, &m->s, &m->c);
    SQFH_SINCOS(d0, &m->ms, &m->mc);
    m->qc = t->qc;  m->qs = t->qs;             /* cached at init_m */
    double is2 = 1.0 / (t->env_sig * t->env_sig);
    m->env = exp(-t->x0 * t->x0 * is2);
    m->r   = exp(-(2.0 * t->x0 + 1.0) * is2);
    m->rho = t->rho;                           /* cached at init_m */
}

static inline void sqfh_lockin_m(const sqfh_mctx_t *m0, const float *w,
                                 double *al, double *be, double *dphi,
                                 double *resid, double *E) {
    sqfh_mctx_t m = *m0;                 /* local copy: ctx is reusable */
    double sI = 0, sQ = 0, sE = 0, G = 0, C2s = 0, S2s = 0;
    for (int i = 0; i < SQFH_N; i++) {
        double we = w[i] * m.env;
        sQ += we * m.s;
        sI += we * m.c;
        sE += (double)w[i] * w[i];
        double env2 = m.env * m.env;
        G   += env2;
        C2s += env2 * (m.c * m.c - m.s * m.s);   /* cos 2theta */
        S2s += env2 * (2.0 * m.s * m.c);         /* sin 2theta */
        double cn = m.c * m.mc - m.s * m.ms;
        m.s = m.s * m.mc + m.c * m.ms;  m.c = cn;
        cn = m.mc * m.qc - m.ms * m.qs;
        m.ms = m.ms * m.qc + m.mc * m.qs;  m.mc = cn;
        m.env *= m.r;  m.r *= m.rho;
    }
    /* normal matrix of the env-weighted (sin, cos) basis:
     * u2 = sum env^2 sin^2, v2 = sum env^2 cos^2, uv = sum env^2 sin cos */
    double u2 = 0.5 * (G - C2s), v2 = 0.5 * (G + C2s), uv = 0.5 * S2s;
    double det = u2 * v2 - uv * uv;
    double a = 0, b = 0;
    if (det > 0.0) {
        a = (v2 * sQ - uv * sI) / det;   /* sine coefficient   */
        b = (u2 * sI - uv * sQ) / det;   /* cosine coefficient */
    }
    double explained = a * sQ + b * sI;
    if (explained < 0) explained = 0;          /* fp guard */
    if (explained > sE) explained = sE;
    *al = a; *be = b;
    *dphi = (det > 0.0) ? atan2(b, a) : 0.0;
    *resid = sE - explained;
    *E = sE;
}

/* per-sample residual against the fitted model-M wave — same role as
 * sqfh_spike_localize on the legacy path.  (al, be) are evaluated at
 * the ledger phase, so the context is reused as-is: no extra trig. */
static inline int sqfh_spike_localize_m(const sqfh_mctx_t *m0, const float *w,
                                        double al, double be,
                                        double *share_out) {
    sqfh_mctx_t m = *m0;
    double worst = 0, total = 0;
    int wi = -1;
    for (int i = 0; i < SQFH_N; i++) {
        double rr = w[i] - m.env * (al * m.s + be * m.c);
        double r2 = rr * rr;
        total += r2;
        if (r2 > worst) { worst = r2; wi = i; }
        double cn = m.c * m.mc - m.s * m.ms;
        m.s = m.s * m.mc + m.c * m.ms;  m.c = cn;
        cn = m.mc * m.qc - m.ms * m.qs;
        m.ms = m.ms * m.qc + m.mc * m.qs;  m.mc = cn;
        m.env *= m.r;  m.r *= m.rho;
    }
    *share_out = (total > 0) ? worst / total : 0;
    return wi;
}

/* the handoff verdict for one tile — legacy bare-sinusoid path.
 * Verbatim pre-model-M logic; the regression net (sqfh_cert.c) runs
 * through here bit-identically whenever chirp == 0 && env_sig == 0. */
static inline int sqfh_handoff_legacy(sqfh_t *t, const float *w) {
    t->tiles++;
    double I, Q, dphi, resid, E;
    sqfh_lockin(w, t->k, t->phi, t->scale, &I, &Q, &dphi, &resid, &E);

    double share = (E > 0) ? resid / E : 0;

    if (t->episode) {
        if (share < SQFH_RES_SHEAR) {
            /* on-ramp: Q collapsed, analytic prior resumes.
             * Resync: adopt the rotation the episode left us at. */
            t->episode = 0;
            t->ep_close++;
            t->ep_phi_used = dphi;
            t->phi += dphi;
            t->last_lane = SQFH_LINEAR;
            t->linear++;
            return SQFH_LINEAR;
        }
        t->shear_tiles++;
        t->last_lane = SQFH_SHEAR;
        t->last_resid_share = share;
        return SQFH_SHEAR;             /* raw archive, episode continues */
    }

    if (share > SQFH_RES_SHEAR) {
        /* non-rotational content.  Three suspects, one pass:
         * OVERFLOW — excess is peak-ALIGNED (in-phase): samples pinned
         *   at the envelope rail.  The wave is fine; the cone was too
         *   small.  Excess is analytically invertible (describing
         *   function).  Archive raw + tag; the excess is DATA — it
         *   goes back as the resubmission parameter or carries to the
         *   neighboring tiles (conservation: nothing vanishes at the
         *   rail).
         * SPIKE — one sample holds the residual (transport garbage).
         * SHEAR — distributed quadrature growth (true curl). */
        int railed = 0;
        for (int i = 0; i < SQFH_N; i++)
            if (fabs(w[i]) >= SQFH_RAIL_TOL * t->A) railed++;
        if ((double)railed / SQFH_N > SQFH_RAIL_FRAC) {
            /* candidate overflow.  Confirm: does a CLIPPED sinusoid at
             * the recovered true amplitude actually explain the tile?
             * Overflow: yes (the wave is fine, the cone was small).
             * Shear piling samples on the rail: no — fall through. */
            double M = 2.0 * hypot(I, Q) / SQFH_N;
            double A_true = sqfh_recover_amplitude(M, t->A);
            double cd = cos(t->k * t->scale), sd = sin(t->k * t->scale);
            double cc = cos(t->phi + dphi), ss = sin(t->phi + dphi);
            double r2 = 0;
            for (int i = 0; i < SQFH_N; i++) {
                double v = A_true * ss;
                if (v > t->A) v = t->A; else if (v < -t->A) v = -t->A;
                double d = w[i] - v;
                r2 += d * d;
                double cn = cc * cd - ss * sd;
                ss = ss * cd + cc * sd;
                cc = cn;
            }
            if (E > 0 && r2 / E < SQFH_RES_SHEAR) {
                t->overflows++;
                t->last_lane = SQFH_OVERFLOW;
                t->last_excess = A_true - t->A;
                t->last_resid_share = share;
                return SQFH_OVERFLOW;  /* tag: cone clipped, excess=delta */
            }
        }
        /* spike or true shear? */
        double Afit = 2.0 * hypot(I, Q) / SQFH_N;
        double sshare;
        int si = sqfh_spike_localize(w, Afit, t->k, t->phi + dphi,
                                     t->scale, &sshare);
        if (sshare > SQFH_SPIKE_SHARE) {
            t->spikes++;
            t->last_lane = SQFH_SPIKE;
            t->last_spike_idx = si;
            t->last_resid_share = sshare;
            return SQFH_SPIKE;         /* quarantine sample, stay tracked */
        }
        t->episode = 1;                /* off-ramp */
        t->ep_open++;
        t->ep_phi0 = t->phi;
        t->shear_tiles++;
        t->last_lane = SQFH_SHEAR;
        t->last_resid_share = share;
        return SQFH_SHEAR;
    }

    if (fabs(dphi) > SQFH_SLIP_TOL) {
        t->slips++;                    /* rotation, not damage */
        t->phi += dphi;                /* phase/time dilation resync */
        t->last_dphi = dphi;
        t->last_lane = SQFH_SLIP;
        return SQFH_SLIP;
    }

    t->linear++;
    t->last_lane = SQFH_LINEAR;
    return SQFH_LINEAR;
}

/* model-M handoff: identical lane logic, extended reference.
 * Only the reference generation and the fit differ; thresholds,
 * episode machine, spike/overflow separation are unchanged.
 * On SLIP: t->phi is dilated by the measured rotation.
 * On SHEAR: episode opens (or continues); tile must be archived raw.
 * On episode close: ledger resyncs with the measured phase consumed. */
static inline int sqfh_handoff_m(sqfh_t *t, const float *w) {
    t->tiles++;
    /* silence gate, before ANY model work: cheap raw-energy check.
     * A silent tile is trivially consistent with the prior (the
     * envelope says nothing is there); route LINEAR, skip
     * classification, close any open episode WITHOUT phase adoption
     * (silence measured nothing, the ledger keeps its phase). */
    double sE0 = 0, wpeak = 0;
    for (int i = 0; i < SQFH_N; i++) {
        sE0 += (double)w[i] * w[i];
        double a = fabs(w[i]);
        if (a > wpeak) wpeak = a;
    }
    if (sE0 < SQFH_E_FLOOR) {
        if (t->episode) { t->episode = 0; t->ep_close++; t->ep_phi_used = 0; }
        t->linear++;
        t->last_lane = SQFH_LINEAR;
        t->last_resid_share = 0;
        return SQFH_LINEAR;
    }
    sqfh_mctx_t m;                 /* one setup per tile, shared below */
    sqfh_mctx_init(&m, t);
    double al, be, dphi, resid, E;
    sqfh_lockin_m(&m, w, &al, &be, &dphi, &resid, &E);

    double share = (E > 0) ? resid / E : 0;

    if (t->episode) {
        if (share < SQFH_RES_SHEAR) {
            t->episode = 0;
            t->ep_close++;
            t->ep_phi_used = dphi;
            t->phi += dphi;
            t->last_lane = SQFH_LINEAR;
            t->linear++;
            return SQFH_LINEAR;
        }
        t->shear_tiles++;
        t->last_lane = SQFH_SHEAR;
        t->last_resid_share = share;
        return SQFH_SHEAR;             /* raw archive, episode continues */
    }

    if (share > SQFH_RES_SHEAR) {
        /* OVERFLOW candidate: samples pinned at the rail.  Under the
         * envelope prior the cone scales with the envelope: the rail
         * at sample i is env_i * A.  Cheap peak pre-check first: if no
         * sample can touch the highest rail in the tile, skip the scan.
         * The describing-function inversion is the flat-amplitude one —
         * APPROXIMATE under an envelope (documented in SQFH_DESIGN.md);
         * never triggered on the schrod_2d stream.  The re-fit wave
         * reuses the ctx and the fitted (al, be):
         * A_true*sin(theta+dphi) = (A_true/Afit)*(al*sin + be*cos) —
         * no extra transcendentals. */
        int railed = 0;
        if (wpeak >= SQFH_RAIL_TOL * t->A) {   /* conservative: env<=1 */
            sqfh_mctx_t mr = m;
            for (int i = 0; i < SQFH_N; i++) {
                if (fabs(w[i]) >= SQFH_RAIL_TOL * t->A * mr.env) railed++;
                mr.env *= mr.r;  mr.r *= mr.rho;
            }
        }
        if ((double)railed / SQFH_N > SQFH_RAIL_FRAC) {
            double M = hypot(al, be);    /* fitted peak amplitude */
            double A_true = sqfh_recover_amplitude(M, t->A);
            double sc = (M > 0) ? A_true / M : 0.0;
            sqfh_mctx_t mo = m;
            double r2 = 0;
            for (int i = 0; i < SQFH_N; i++) {
                double rail = t->A * mo.env;
                double v = sc * mo.env * (al * mo.s + be * mo.c);
                if (v > rail) v = rail; else if (v < -rail) v = -rail;
                double d = w[i] - v;
                r2 += d * d;
                double cn = mo.c * mo.mc - mo.s * mo.ms;
                mo.s = mo.s * mo.mc + mo.c * mo.ms;  mo.c = cn;
                cn = mo.mc * mo.qc - mo.ms * mo.qs;
                mo.ms = mo.ms * mo.qc + mo.mc * mo.qs;  mo.mc = cn;
                mo.env *= mo.r;  mo.r *= mo.rho;
            }
            if (E > 0 && r2 / E < SQFH_RES_SHEAR) {
                t->overflows++;
                t->last_lane = SQFH_OVERFLOW;
                t->last_excess = A_true - t->A;
                t->last_resid_share = share;
                return SQFH_OVERFLOW;  /* tag: cone clipped, excess=delta */
            }
        }
        /* spike or true shear?  (al, be) are the best-fit wave already */
        double sshare;
        int si = sqfh_spike_localize_m(&m, w, al, be, &sshare);
        if (sshare > SQFH_SPIKE_SHARE) {
            t->spikes++;
            t->last_lane = SQFH_SPIKE;
            t->last_spike_idx = si;
            t->last_resid_share = sshare;
            return SQFH_SPIKE;         /* quarantine sample, stay tracked */
        }
        t->episode = 1;                /* off-ramp */
        t->ep_open++;
        t->ep_phi0 = t->phi;
        t->shear_tiles++;
        t->last_lane = SQFH_SHEAR;
        t->last_resid_share = share;
        return SQFH_SHEAR;
    }

    if (fabs(dphi) > SQFH_SLIP_TOL) {
        t->slips++;                    /* rotation, not damage */
        t->phi += dphi;                /* phase/time dilation resync */
        t->last_dphi = dphi;
        t->last_lane = SQFH_SLIP;
        return SQFH_SLIP;
    }

    t->linear++;
    t->last_lane = SQFH_LINEAR;
    return SQFH_LINEAR;
}

/* the handoff verdict for one tile.  Dispatches on the prior class:
 * chirp == 0 && env_sig == 0 is the legacy cell, bit-identical. */
static inline int sqfh_handoff(sqfh_t *t, const float *w) {
    if (t->chirp == 0.0 && t->env_sig == 0.0)
        return sqfh_handoff_legacy(t, w);
    return sqfh_handoff_m(t, w);
}

/* ledger advance between tiles (continuous bound physics) */
static inline void sqfh_advance(sqfh_t *t) {
    t->phi += t->k * SQFH_N * t->scale;
    t->x0 += SQFH_N * t->scale;        /* envelope/chirp coordinate */
}

#endif /* SQFH_CORE_H */
