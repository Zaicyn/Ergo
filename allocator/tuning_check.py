#!/usr/bin/env python3
"""tuning_check.py — Squaragon allocator tuning audit, Levels 1+3
(and driver for the Level 2 Ergo geodesy binary).

Oracle discipline:
  - every LUT verdict is a diff of an analytic regeneration against the
    baked DATA tables in BOTH allocator/sq2core.f and tests/sq3core.ergo,
    cross-checked against the production V22 header (compiled C driver);
  - runtime cross-port: F77 driver (sq2core.f) and Ergo binary
    (tests/sq3core.ergo) must agree on TTOTAL / zone / state hash with
    an independent Python model;
  - determinism: every driver run twice, byte-identical output;
  - every tuning claim gets a measured sweep or is reported as folklore.

Run from repo root:  python allocator/tuning_check.py
"""
import os
import re
import subprocess
import sys

import numpy as np

f32 = np.float32
TWOPI_F = f32(6.28318530718)

# ==========================================================================
# Analytic regenerators (definitions from Testing/V22/squaragon_v2.h)
# ==========================================================================

def viviani_z_x(theta):
    """sq2_viviani_z + x-component, float32 pipeline."""
    th = f32(theta)
    s, c = f32(np.sin(th)), f32(np.cos(th))
    s3, c3 = f32(np.sin(f32(3.0) * th)), f32(np.cos(f32(3.0) * th))
    x = f32(s - f32(0.5) * s3)
    y = f32(-c + f32(0.5) * c3)
    z = f32(c * c3)
    n = f32(np.sqrt(f32(x * x + y * y + z * z)))
    nz = f32(0.0) if n < f32(1e-6) else f32(z / n)
    return nz, x


def gen_scatlt(hopfq=1.97, total=32, n=32):
    """sq2_viviani_scatter_full(id, total), LUT-indexed id in [0,n)."""
    hq = f32(hopfq)
    out = []
    for i in range(n):
        th = f32(TWOPI_F * f32(i) / f32(total))
        nz, x = viviani_z_x(th)
        proj = f32(f32(np.abs(nz)) * hq)
        q = int(f32(proj * f32(8.0))) % 8
        xc = int(f32(np.abs(x) * f32(4.0))) & 3
        out.append((q ^ xc) % 8)
    return out


def gen_floww(n=32):
    """w(theta) = sin(3t)/3 + sin(9t)/9 + sin(27t)/27, theta=2pi i/32."""
    out = []
    for i in range(n):
        th = f32(TWOPI_F * f32(i) / f32(32))
        w = f32(f32(np.sin(f32(3.0) * th)) / f32(3.0)
                + f32(np.sin(f32(9.0) * th)) / f32(9.0)
                + f32(np.sin(f32(27.0) * th)) / f32(27.0))
        out.append(float(w))
    return out


def gen_flowm(w):
    """sq2_flow_detect: >0.30 FLOW(2), >0.22 ACTIVE(1), else COAST(0).
    NOTE: the V22 header COMMENT says ACTIVE is 0.15-0.30, but the code
    branches on SQ2_FLOW_THRESHOLD_MID = 0.22 (0.15 is only used for the
    quality output). The LUT matches the code, not the comment."""
    return [2 if abs(v) > 0.30 else (1 if abs(v) > 0.22 else 0) for v in w]


def gen_solton(w):
    return [1 if abs(v) > 0.30 else 0 for v in w]


def gen_bingeo():
    """sq2_shadow_invariant geo byte: (uint32)(|nz(2pi b/8)| * 255)."""
    out = []
    for b in range(8):
        th = f32(TWOPI_F * f32(b) / f32(8))
        nz, _ = viviani_z_x(th)
        out.append(int(f32(np.abs(nz) * f32(255.0))))
    return out


def gen_seed():
    s = 0.7071067811865475
    V = [(s, s, 0), (s, -s, 0), (-s, s, 0), (-s, -s, 0),
         (s, 0, s), (s, 0, -s), (-s, 0, s), (-s, 0, -s),
         (0, s, s), (0, s, -s), (0, -s, s), (0, -s, -s)]
    return np.array(V, dtype=float)


# ==========================================================================
# Baked-table parsers
# ==========================================================================

def parse_f77_table(text, name, count):
    m = re.search(rf"DATA {name}\s*/(.+?)/", text, re.S)
    assert m, f"{name} not found in F77"
    body = re.sub(r"[&\n]", " ", m.group(1))
    vals = [v for v in re.split(r"[,\s]+", body) if v]
    vals = vals[:count]
    return [float(v) if ("." in v or "e" in v.lower()) else int(v)
            for v in vals]


def parse_ergo_table(text, name, count):
    m = re.search(rf"DATA {name}\s*/(.+?)/", text, re.S)
    assert m, f"{name} not found in ergo"
    vals = [v for v in re.split(r"[,\s]+", m.group(1)) if v]
    vals = vals[:count]
    return [float(v) if ("." in v or "e" in v.lower()) else int(v)
            for v in vals]


# ==========================================================================
# Drivers
# ==========================================================================

def sh(cmd, **kw):
    r = subprocess.run(cmd, shell=isinstance(cmd, str),
                       capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"driver failed: {cmd}\n{r.stderr[-2000:]}")
    return r.stdout


F77_DRIVER = r"""
      PROGRAM SQ2DRV
      IMPLICIT NONE
      INTEGER I, ERR
      INTEGER SQ2SCT, SQ2FLM, SQ2SOL, SQ2ZON
      REAL SQ2FLW
      REAL    GATES(3,12,32,8,2)
      REAL    TINVAR(32,8,2)
      INTEGER TOCC(32,8,2), TFROZ(32,8,2)
      INTEGER TWHEAD(8,2), TLEN(8,2), TALLOC(8,2)
      INTEGER TTOTAL, TPHASE, TGEN
      COMMON /SQ2TOR/ GATES, TINVAR, TOCC, TFROZ,
     &                 TWHEAD, TLEN, TALLOC,
     &                 TTOTAL, TPHASE, TGEN
      INTEGER HASH, HI, HJ, HK
      INTEGER NCOPY
      CALL SQ2TIN
      DO 10 I = 1, 64
        WRITE(*,'(A,I4,A,I4)') 'SCT ', I, ' ', SQ2SCT(I)
   10 CONTINUE
      DO 20 I = 1, 32
        WRITE(*,'(A,I4,A,F12.6,A,I4,A,I4)') 'FLW ', I, ' ',
     &   SQ2FLW(I), ' ', SQ2FLM(I), ' ', SQ2SOL(I)
   20 CONTINUE
      ERR = 0
      DO 30 I = 1, 400
        CALL SQ2FAL(I, ERR)
   30 CONTINUE
      WRITE(*,'(A,I8)') 'TTOTAL ', TTOTAL
      WRITE(*,'(A,I4)') 'ZONE ', SQ2ZON(TTOTAL)
      HASH = 166136261
      DO 50 HK = 1, 2
        DO 45 HJ = 1, 8
          HASH = IEOR(HASH, TWHEAD(HJ,HK))
          HASH = IEOR(ISHFT(HASH,13), ISHFT(HASH,-19))
          HASH = IEOR(HASH, TLEN(HJ,HK))
          HASH = IEOR(ISHFT(HASH,13), ISHFT(HASH,-19))
          HASH = IEOR(HASH, TALLOC(HJ,HK))
          HASH = IEOR(ISHFT(HASH,13), ISHFT(HASH,-19))
          DO 40 HI = 1, 32
            HASH = IEOR(HASH, TOCC(HI,HJ,HK))
            HASH = IEOR(ISHFT(HASH,13), ISHFT(HASH,-19))
            HASH = IEOR(HASH, TFROZ(HI,HJ,HK))
            HASH = IEOR(ISHFT(HASH,13), ISHFT(HASH,-19))
   40     CONTINUE
   45   CONTINUE
   50 CONTINUE
      HASH = IEOR(HASH, TTOTAL)
      HASH = IEOR(ISHFT(HASH,13), ISHFT(HASH,-19))
      WRITE(*,'(A,I12)') 'HASH ', HASH
      CALL SQ2REP(NCOPY)
      WRITE(*,'(A,I8)') 'NCOPY ', NCOPY
      WRITE(*,'(A,I8)') 'TTOTAL2 ', TTOTAL
      WRITE(*,'(A,I4)') 'ZONE2 ', SQ2ZON(TTOTAL)
      END
"""

C_DRIVER = r"""
#include <stdio.h>
#include <math.h>
#include "squaragon_v2.h"

static unsigned long long rng_state = 0x123456789ULL;
static float frand(void) {  /* deterministic LCG -> [-1,1] */
    rng_state = rng_state * 6364136223846793005ULL + 1442695040888963407ULL;
    return 2.0f * (float)((rng_state >> 33) & 0xFFFFFF) / 16777216.0f - 1.0f;
}

int main(void) {
    /* L1 production cross-checks */
    for (int i = 0; i < 32; i++)
        printf("SCAT %d %u\n", i, sq2_viviani_scatter_full((uint32_t)i, 32u));
    for (int i = 0; i < 32; i++) {
        float th = 6.28318530718f * (float)i / 32.0f;
        printf("FLOWW %d %.6f\n", i, sq2_flow_w(th));
        printf("FLOWM %d %d\n", i, sq2_flow_detect(th, NULL, NULL));
        printf("SOLTON %d %d\n", i, sq2_is_soliton_window(th));
    }
    for (int b = 0; b < 8; b++) {
        float th = 6.28318530718f * (float)b / 8.0f;
        printf("GEO %d %u\n", b,
               (uint32_t)(fabsf(sq2_viviani_z(th)) * 255.0f));
    }
    /* L3d: triple-XOR residual */
    sq2_gate_t g;
    sq2_init(&g, 1.0f);
    printf("RESID_SHORTCUT %.9g\n", sq2_triple_xor_residual(&g));
    printf("RESID_FULL_ZERO %.9g\n", sq2_triple_xor_residual_full(&g));
    for (int v = 0; v < 12; v++) {
        for (int ax = 0; ax < 3; ax++) {
            sq2_init(&g, 1.0f);
            float eps = 1.0e-3f;
            if (ax == 0) g.vertices[v].x += eps;
            if (ax == 1) g.vertices[v].y += eps;
            if (ax == 2) g.vertices[v].z += eps;
            printf("PERT %d %d %.9g\n", v, ax,
                   sq2_triple_xor_residual_full(&g));
        }
    }
    int undetected = 0;
    for (int t = 0; t < 100; t++) {
        sq2_init(&g, 1.0f);
        int v = (int)(frand() * 6.0f + 6.0f) % 12;
        float dx = frand(), dy = frand(), dz = frand();
        float n = sqrtf(dx * dx + dy * dy + dz * dz);
        if (n < 1e-9f) { t--; continue; }
        g.vertices[v].x += 1.0e-3f * dx / n;
        g.vertices[v].y += 1.0e-3f * dy / n;
        g.vertices[v].z += 1.0e-3f * dz / n;
        float r = sq2_triple_xor_residual_full(&g);
        printf("RAND %d %.9g\n", t, r);
        if (r < 1.0e-6f) undetected++;
    }
    printf("RAND_UNDETECTED %d\n", undetected);
    return 0;
}
"""


# ==========================================================================
# Python allocation-state model (validated against the Ergo binary's hash)
# ==========================================================================

def simulate_state(scat, nalloc=400):
    head = [[1] * 8 for _ in range(2)]
    tlen = [[0] * 8 for _ in range(2)]
    talloc = [[0] * 8 for _ in range(2)]
    occ = [[[0] * 32 for _ in range(8)] for _ in range(2)]
    froz = [[[0] * 32 for _ in range(8)] for _ in range(2)]
    ttotal = 0
    for ID in range(1, nalloc + 1):
        b = scat[(ID - 1) % 32]
        g = head[0][b]
        if g > 32:
            continue
        occ[0][b][g - 1] = 1
        talloc[0][b] += 1
        froz[0][b][g - 1] = 1 if talloc[0][b] % 4 == 0 else 0
        head[0][b] = g + 1
        tlen[0][b] += 1
        ttotal += 1
    return head, tlen, talloc, occ, froz, ttotal


def state_hash(state):
    head, tlen, talloc, occ, froz, ttotal = state
    M = 0xFFFFFFFF

    def mix(h):
        return ((h << 13) & M) ^ (h >> 19)

    h = 166136261
    for hk in range(2):
        for hj in range(8):
            for arr in (head, tlen, talloc):
                h = (h ^ arr[hk][hj]) & M
                h = mix(h)
            for hi in range(32):
                h = (h ^ occ[hk][hj][hi]) & M
                h = mix(h)
                h = (h ^ froz[hk][hj][hi]) & M
                h = mix(h)
    h = (h ^ ttotal) & M
    h = mix(h)
    return h - 2**32 if h >= 2**31 else h


# ==========================================================================
# Torus geodesy replica (must match tuning_relax.ergo's DD)
# ==========================================================================

def torus_dd(floww, gamma=1.0, wb=27.0 / 16.0):
    """All-pairs Dijkstra on the 8x32 torus.
    ring step r->r+1: 1 + gamma*(|w_r|+|w_{r+1}|)/2 ; bin step: wb."""
    import heapq
    NP = 256
    aw = [abs(v) for v in floww]
    wr = [1.0 + gamma * 0.5 * (aw[r] + aw[(r + 1) % 32]) for r in range(32)]
    DD = np.zeros((NP, NP))
    for s in range(NP):
        dist = [np.inf] * NP
        dist[s] = 0.0
        pq = [(0.0, s)]
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]:
                continue
            b, r = divmod(u, 32)
            for v, w in ((b * 32 + (r + 1) % 32, wr[r]),
                         (b * 32 + (r - 1) % 32, wr[(r - 1) % 32]),
                         (((b + 1) % 8) * 32 + r, wb),
                         (((b - 1) % 8) * 32 + r, wb)):
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(pq, (nd, v))
        DD[s] = dist
    return DD


def walk_nodes(seq):
    """Node indices for a 32-step bin sequence (per-bin visit ordinals)."""
    cnt = [0] * 8
    nodes = []
    for b in seq:
        nodes.append(b * 32 + cnt[b])
        cnt[b] += 1
    return nodes


def action(seq, DD):
    n = walk_nodes(seq)
    e = sum(1.0 / (1.0 + DD[n[i], n[i + 1]]) for i in range(len(seq) - 1))
    dsum = sum(DD[n[i], n[i + 1]] for i in range(len(seq) - 1))
    return e, dsum


def separations(seq32, DD, nids=512):
    """Adjacent-ID torus distances over a stream of nids IDs."""
    cnt = [0] * 8
    prev = None
    out = []
    for i in range(nids):
        b = seq32[i % 32]
        node = b * 32 + (cnt[b] % 32)
        cnt[b] += 1
        if prev is not None:
            out.append(DD[prev, node])
        prev = node
    return np.array(out)


def swap_descent(seq, DD, max_sweeps=200):
    seq = list(seq)
    eb, _ = action(seq, DD)
    for _ in range(max_sweeps):
        changed = False
        for i in range(31):
            for j in range(i + 1, 32):
                seq[i], seq[j] = seq[j], seq[i]
                e2, _ = action(seq, DD)
                if e2 < eb - 1e-12:
                    eb = e2
                    changed = True
                else:
                    seq[i], seq[j] = seq[j], seq[i]
        if not changed:
            break
    return seq, eb


# ==========================================================================
# Driver runners
# ==========================================================================

def run_twice(cmd, **kw):
    o1 = sh(cmd, **kw)
    o2 = sh(cmd, **kw)
    return o1, o1 == o2


def run_f77():
    with open("/tmp/sq2drv.f", "w") as f:
        f.write(F77_DRIVER)
    sh("gfortran -std=legacy -O2 allocator/sq2core.f /tmp/sq2drv.f "
       "-o /tmp/sq2drv")
    return run_twice("/tmp/sq2drv")


def run_c():
    with open("/tmp/sq2audit.c", "w") as f:
        f.write(C_DRIVER)
    sh("gcc -O2 -I Testing/V22 /tmp/sq2audit.c -lm -o /tmp/sq2audit")
    return run_twice("/tmp/sq2audit")


def run_ergo():
    sh([sys.executable, "-m", "core", "tests/sq3core.ergo", "-o",
        "/tmp/sq3audit"])
    return run_twice("/tmp/sq3audit")


def run_l2():
    if not os.path.exists("allocator/tuning_relax.ergo"):
        sh([sys.executable, "allocator/gen_tuning_relax.py"])
    sh([sys.executable, "-m", "core", "allocator/tuning_relax.ergo",
        "-o", "/tmp/trelax"])
    return run_twice("/tmp/trelax")


# ==========================================================================
# Audit sections
# ==========================================================================

def lvl(line=""):
    print(line)


def section_l1(f77_text, ergo_text, c_out):
    lvl("=" * 70)
    lvl("LEVEL 1 — static LUT self-consistency")
    lvl("=" * 70)
    c_scat = [int(m.group(2)) for m in re.finditer(r"SCAT (\d+) (\d+)", c_out)]
    c_floww = [float(m.group(2))
               for m in re.finditer(r"FLOWW (\d+) (\S+)", c_out)]
    c_flowm = [int(m.group(2)) for m in re.finditer(r"FLOWM (\d+) (\d+)", c_out)]
    c_solton = [int(m.group(2)) for m in re.finditer(r"SOLTON (\d+) (\d+)", c_out)]
    c_geo = [int(m.group(2)) for m in re.finditer(r"GEO (\d+) (\d+)", c_out)]

    regen = {
        "SCATLT": gen_scatlt(),
        "FLOWW": gen_floww(),
        "FLOWM": gen_flowm(gen_floww()),
        "SOLTON": gen_solton(gen_floww()),
        "BINGEO": gen_bingeo(),
    }
    prod = {"SCATLT": c_scat, "FLOWW": c_floww, "FLOWM": c_flowm,
            "SOLTON": c_solton, "BINGEO": c_geo}
    baked_f77 = {
        "SCATLT": parse_f77_table(f77_text, "SCATLT", 32),
        "FLOWW": parse_f77_table(f77_text, "FLOWW", 32),
        "FLOWM": parse_f77_table(f77_text, "FLOWM", 32),
        "SOLTON": parse_f77_table(f77_text, "SOLTON", 32),
        "BINGEO": parse_f77_table(f77_text, "BINGEO", 8),
    }
    baked_ergo = {
        "SCATLT": parse_ergo_table(ergo_text, "SCATLT", 32),
        "BINGEO": parse_ergo_table(ergo_text, "BINGEO", 8),
    }

    verdicts = {}
    for name, rg in regen.items():
        pr = prod[name]
        bf = baked_f77[name]
        if name in ("FLOWW",):
            gen_vs_prod = max(abs(a - b) for a, b in zip(rg, pr))
            prod_vs_baked = max(abs(a - b) for a, b in zip(pr, bf))
            ok = gen_vs_prod < 2e-6 and prod_vs_baked <= 5e-7
            lvl(f"[{name}] regen-vs-production(C sinf) maxdiff "
                f"{gen_vs_prod:.2e}; production-vs-baked(F77) maxdiff "
                f"{prod_vs_baked:.2e}")
            lvl(f"  generator: w(t)=sin(3t)/3+sin(9t)/9+sin(27t)/27, "
                f"t=2pi*i/32 (squaragon_v2.h:829)")
            verdicts[name] = ("exact-match" if ok else "MISMATCH")
        else:
            ok_gp = list(map(int, rg)) == list(map(int, pr))
            ok_bf = list(map(int, pr)) == list(map(int, bf))
            lvl(f"[{name}] regen==production: {ok_gp}; "
                f"production==baked-F77: {ok_bf}")
            verdicts[name] = "exact-match" if (ok_gp and ok_bf) else "MISMATCH"
        if name in baked_ergo:
            ok_e = list(map(int, baked_ergo[name])) == list(map(int, pr))
            lvl(f"  baked-ergo==production: {ok_e}")
            if not ok_e:
                verdicts[name] += " (ergo MISMATCH)"

    # SCATLT truncation margins (how knife-edged is the bake?)
    lvl("  SCATLT truncation margins (fractional parts at int boundaries):")
    worst = 1.0
    for i in range(16):
        th = f32(TWOPI_F * f32(i) / f32(32))
        nz, x = viviani_z_x(th)
        p = float(np.abs(nz)) * 1.97 * 8.0
        xm = float(np.abs(x)) * 4.0
        fp = min(p % 1, 1 - p % 1)
        fx = min(xm % 1, 1 - xm % 1)
        worst = min(worst, fp, fx)
        if fp < 0.1 or fx < 0.1:
            lvl(f"    id={i}: proj8={p:.4f} xc4={xm:.4f}  <-- near boundary")
    lvl(f"    min margin over 16 ids: {worst:.4f}")
    lvl("  SCATLT bin histogram per 32 IDs: "
        + str({b: regen['SCATLT'].count(b) for b in range(8)}))

    # SEED vertices
    seed_ref = gen_seed()
    maxerr = 0.0
    for i in range(1, 13):
        for j in range(1, 4):
            m = re.search(rf"DATA SEED\({j},{i}\)\s*/\s*([\d.Ee+-]+)", f77_text)
            maxerr = max(maxerr, abs(float(m.group(1)) - seed_ref[i - 1, j - 1]))
    lvl(f"[SEED] 12 unit-cuboctahedron vertices vs exact 1/sqrt(2): "
        f"max abs err {maxerr:.2e}")
    verdicts["SEED"] = "exact-match" if maxerr == 0.0 else "reconstructed"
    return verdicts, regen["SCATLT"]


def section_l2(l2_out, scat):
    lvl()
    lvl("=" * 70)
    lvl("LEVEL 2 — geodesy: visitation-walk action deficit")
    lvl("=" * 70)
    DD = np.zeros((256, 256))
    for m in re.finditer(r"DD (\d+) (\d+) (\S+)", l2_out):
        DD[int(m.group(1)) - 1, int(m.group(2)) - 1] = float(m.group(3))
    e_design = float(re.search(r"EDESIGN (\S+)", l2_out).group(1))
    dsum = float(re.search(r"DSUM (\S+)", l2_out).group(1))
    e_relaxed = float(re.search(r"ERELAXED (\S+)", l2_out).group(1))
    conv = int(re.search(r"converged at sweep (\d+)", l2_out).group(1))
    rseq = [int(m.group(2)) for m in re.finditer(r"RSEQ (\d+) (\d+)", l2_out)]

    DDp = torus_dd(gen_floww())
    dd_diff = np.abs(DD - DDp).max()
    lvl(f"[cross-check] Ergo DD vs Python Dijkstra replica: "
        f"max abs diff {dd_diff:.2e}")
    e_py, d_py = action(scat, DD)
    lvl(f"[cross-check] design action recomputed from Ergo DD: "
        f"{e_py:.6f} (Ergo printed {e_design:.6f})")
    lvl(f"metric: ring WR=1+(|FLOWW_r|+|FLOWW_r+1|)/2, bin WB=27/16; "
        f"E = sum 1/(1+d)")
    lvl(f"design walk:  E={e_design:.6f}  DSUM={dsum:.3f}")
    lvl(f"relaxed walk: E={e_relaxed:.6f}  (swap descent converged "
        f"sweep {conv})")
    lvl(f"DEFICIT: (E_design - E_relaxed)/E_design = "
        f"{(e_design - e_relaxed) / e_design:.2%}")
    lvl(f"retune candidate sequence (relaxed): {rseq}")

    # 100 random single-swap perturbations
    rng = np.random.default_rng(20260804)
    rose, fell = 0, 0
    deltas = []
    for _ in range(100):
        s = list(scat)
        i, j = rng.choice(32, size=2, replace=False)
        s[i], s[j] = s[j], s[i]
        e2, _ = action(s, DD)
        deltas.append(e2 - e_design)
        if e2 > e_design + 1e-12:
            rose += 1
        elif e2 < e_design - 1e-12:
            fell += 1
    lvl(f"100 random single-swap perturbations: rose {rose}, fell {fell}, "
        f"unchanged {100 - rose - fell}; dE mean {np.mean(deltas):+.4f}, "
        f"min {np.min(deltas):+.4f}, max {np.max(deltas):+.4f}")

    # multistart descents (Python) — is the Ergo relaxed value global-ish?
    best = (1e9, None)
    for _ in range(16):
        s = list(scat)
        rng.shuffle(s)
        s, e = swap_descent(s, DD)
        if e < best[0]:
            best = (e, list(s))
    lvl(f"16 random-init swap descents: best E={best[0]:.6f} "
        f"(design {e_design:.6f}, ergo-relaxed {e_relaxed:.6f})")

    # metric sensitivity: gamma (FLOWW weight) and WB (bin step)
    lvl("metric sensitivity (design E vs best-of-8-descents E):")
    for gamma in (0.0, 0.5, 1.0, 2.0):
        for wb in (1.0, 27.0 / 16.0, 1.6180339887, 2.0):
            Dv = torus_dd(gen_floww(), gamma=gamma, wb=wb)
            ed, _ = action(scat, Dv)
            b = 1e9
            rng2 = np.random.default_rng(7)
            for _ in range(8):
                s = list(scat)
                rng2.shuffle(s)
                s, e = swap_descent(s, Dv)
                b = min(b, e)
            flag = "DESIGN-OPTIMAL" if ed <= b + 1e-12 else \
                f"deficit {(ed - b) / ed:.1%}"
            lvl(f"  gamma={gamma:.1f} WB={wb:.4f}: design {ed:.4f} "
                f"vs best {b:.4f} -> {flag}")
    return DD, e_design


def section_l3(scat, DD, f77_out, ergo_out, c_out):
    lvl()
    lvl("=" * 70)
    lvl("LEVEL 3 — runtime properties")
    lvl("=" * 70)

    # ---- cross-port runtime agreement ----
    f77_ttotal = int(re.search(r"TTOTAL\s+(\d+)", f77_out).group(1))
    f77_zone = int(re.search(r"ZONE\s+(\d+)", f77_out).group(1))
    f77_hash = int(re.search(r"HASH\s+(-?\d+)", f77_out).group(1))
    f77_sct = [int(m.group(2)) for m in re.finditer(r"SCT\s+(\d+)\s+(\d+)",
                                                    f77_out)]
    ergo_lines = ergo_out.split()
    e_ttotal, e_zone, e_nbad, e_hash = map(int, ergo_lines[:4])
    py_state = simulate_state(scat)
    py_hash = state_hash(py_state)
    lvl(f"[cross-port] TTOTAL: F77={f77_ttotal} ergo={e_ttotal} "
        f"py={py_state[5]}")
    lvl(f"[cross-port] ZONE:   F77={f77_zone} ergo={e_zone}")
    lvl(f"[cross-port] HASH:   F77={f77_hash} ergo={e_hash} py={py_hash} "
        f"-> {'AGREE' if f77_hash == e_hash == py_hash else 'DISAGREE'}")
    lvl(f"[cross-port] ergo SQ3VAL mismatches: {e_nbad}")
    lvl(f"[cross-port] F77 SQ2SCT(ID=1..64) == design LUT repeated "
        f"(1-based): {[s - 1 for s in f77_sct] == scat * 2}")
    lvl(f"[note] TTOTAL=192 < 400 attempted: bins fill at 32 ring slots; "
        f"bins 1,5 never receive allocations (see L3b)")
    ncopy = int(re.search(r"NCOPY\s+(\d+)", f77_out).group(1))
    ttotal2 = int(re.search(r"TTOTAL2\s+(\d+)", f77_out).group(1))
    zone2 = int(re.search(r"ZONE2\s+(\d+)", f77_out).group(1))
    lvl(f"[capacity] after SQ2REP: NCOPY={ncopy} TTOTAL={ttotal2} "
        f"ZONE={zone2}")
    lvl(f"  -> max reachable occupancy is 2*192=384 (6 active bins); "
        f"THRESHOLD_BIAS=384 is hit EXACTLY at full replication;")
    lvl(f"     THRESHOLD_WORKING=432 and THRESHOLD_MAX=496 are "
        f"UNREACHABLE. Zones 3/4 (OVERDRIVE/DIVIDE) are dead states.")

    # ---- L3a: adjacent-ID separation distribution ----
    lvl()
    lvl("[L3a] adjacent-ID torus-distance separation over 512-ID stream")
    rng = np.random.default_rng(11587)

    def stats(s):
        d = separations(s, DD)
        return d.min(), np.percentile(d, 5), d.mean()

    dmin, d5, dmean = stats(scat)
    lvl(f"  design: min={dmin:.4f} p5={d5:.4f} mean={dmean:.4f}")
    swap_stats = np.array([stats(_swapped(scat, rng)) for _ in range(100)])
    lvl(f"  100 single-swap perturbations: min in "
        f"[{swap_stats[:,0].min():.4f}, {swap_stats[:,0].max():.4f}] "
        f"(worse-than-design min: {(swap_stats[:,0] < dmin - 1e-12).sum()}, "
        f"better: {(swap_stats[:,0] > dmin + 1e-12).sum()})")
    lvl(f"    mean in [{swap_stats[:,2].min():.4f}, "
        f"{swap_stats[:,2].max():.4f}] (design {dmean:.4f})")
    multiset = list(scat)
    rand_stats = []
    for _ in range(100):
        s = list(multiset)
        rng.shuffle(s)
        rand_stats.append(stats(s))
    rand_stats = np.array(rand_stats)
    lvl(f"  100 random same-multiset LUTs: min in "
        f"[{rand_stats[:,0].min():.4f}, {rand_stats[:,0].max():.4f}], "
        f"mean in [{rand_stats[:,2].min():.4f}, {rand_stats[:,2].max():.4f}]")
    lvl(f"    design min rank vs random: "
        f"{(rand_stats[:,0] < dmin - 1e-12).sum()} worse / "
        f"{(rand_stats[:,0] > dmin + 1e-12).sum()} better; mean: "
        f"{(rand_stats[:,2] < dmean - 1e-12).sum()} worse / "
        f"{(rand_stats[:,2] > dmean + 1e-12).sum()} better")

    # ---- L3b: rolling bin-load uniformity ----
    lvl()
    lvl("[L3b] bin loads: static per-period histogram + rolling windows")
    hist = {b: scat.count(b) for b in range(8)}
    lvl(f"  per 32-ID period: {hist}  <-- bins 1,5 EMPTY by design")
    for W in (32, 128, 512):
        seq = [scat[i % 32] for i in range(512 + W)]
        worst = 0
        for start in range(512):
            loads = np.bincount(seq[start:start + W], minlength=8)
            worst = max(worst, int(loads.max() - loads.min()))
        # uniform-random LUTs over all 8 bins (different multiset)
        uloads = []
        for _ in range(20):
            s = list(rng.integers(0, 8, size=32))
            useq = [s[i % 32] for i in range(512 + W)]
            w = 0
            for start in range(0, 512, 17):
                loads = np.bincount(useq[start:start + W], minlength=8)
                w = max(w, int(loads.max() - loads.min()))
            uloads.append(w)
        lvl(f"  window {W:3d}: design max-min={worst} "
            f"(structural: bins 1,5 empty); uniform-random-8-bin LUT "
            f"max-min mean={np.mean(uloads):.1f} min={min(uloads)}")
    lvl("  note: same-multiset random LUTs give identical window spreads")
    lvl("  (the spread is set by the histogram, not the order); the")
    lvl("  design's imbalance is the empty bins 1,5 + the 4:6:8 ratio.")

    # ---- L3c: constant usage map + sweeps ----
    lvl()
    lvl("[L3c] constant usage map (traced through SQ2INI/SQ2FLD/gate ops)")
    lvl("  SCLRAT=27/16: only in SQ2SCL (scale-by-ratio); SQ2SCL is never")
    lvl("    called by SQ2ALC/SQ2FAL (alloc hardcodes SCALE=1.0). In V22 it")
    lvl("    sets shell-1 scale, but shell-1 strands are written only by")
    lvl("    copy. -> INERT in the allocation path (bites only the L2")
    lvl("    metric here, sensitivity-checked in L2).")
    lvl("  BIAS=0.75: stored in gate.bias; used only in sq2_inefficiency()")
    lvl("    = residual*bias with residual identically 0. In F77 declared")
    lvl("    (BIASV) but never referenced. -> INERT.")
    lvl("  HOPFQ=1.97: bites ONLY through SCATLT generation "
        "(proj=|nz|*HOPFQ*8);")
    lvl("    the LUT fast paths never see it. Sweep below.")
    lvl("  SEMSTR=0.03: bites via round(64*SEMSTR)=SEAM_PHASE_SHIFT_BITS=2")
    lvl("    (SQ3FAL TBITS shift). Sweep below.")
    lvl()
    lvl("  HOPFQ sweep (separation min/mean over 512-ID stream, "
        "unused-bin count):")
    base_min, _, base_mean = stats(scat)
    lvl(f"    design 1.97: min={base_min:.4f} mean={base_mean:.4f} "
        f"unused=2")
    opt = []
    for h in np.linspace(0.8, 1.2, 9) * 1.97:
        s = gen_scatlt(hopfq=float(h))
        unused = 8 - len(set(s))
        d = separations(s, DD)
        opt.append((h, d.min(), d.mean(), unused))
        lvl(f"    HOPFQ={h:.4f}: min={d.min():.4f} mean={d.mean():.4f} "
            f"unused_bins={unused}")
    lvl("  SEMSTR sweep: round(64*s) for s in [0.024, 0.036] -> "
        + str(sorted(set(round(64 * s) for s in
                         np.linspace(0.024, 0.036, 13))))
        + " (const 2 in whole ±20% band; flips at s<=0.0234 / s>=0.0391, "
          "i.e. -22% / +30%)")

    # ---- L3d: triple-XOR residual sensitivity ----
    lvl()
    lvl("[L3d] triple-XOR residual (production V22 header, C driver)")
    lvl(f"  shortcut (unperturbed): "
        f"{re.search(r'RESID_SHORTCUT (\S+)', c_out).group(1)}")
    lvl(f"  full, unperturbed:      "
        f"{re.search(r'RESID_FULL_ZERO (\S+)', c_out).group(1)}")
    pert = {}
    for m in re.finditer(r"PERT (\d+) (\d+) (\S+)", c_out):
        pert.setdefault(int(m.group(2)), []).append(float(m.group(3)))
    for ax, name in ((0, "x"), (1, "y"), (2, "z")):
        v = np.array(pert[ax])
        lvl(f"  per-vertex eps=1e-3 along {name}: residual max={v.max():.3e} "
            f"mean={v.mean():.3e}")
    lvl("  theory: (I+R120+R240)d = (0,0,3*dz) — the residual is BLIND to")
    lvl("  any in-plane (x/y) perturbation and to any perturbation set with")
    lvl("  zero total z. It is exactly 3*|z-centroid|/scale.")
    undet = int(re.search(r"RAND_UNDETECTED (\d+)", c_out).group(1))
    rvals = [float(m.group(1))
             for m in re.finditer(r"RAND \d+ (\S+)", c_out)]
    lvl(f"  100 random-dir eps=1e-3 single-vertex perturbations: "
        f"residual min={min(rvals):.3e} max={max(rvals):.3e}; "
        f"undetected (<1e-6): {undet}/100")
    lvl("  NOTE: the V22 data imprint perturbs .x and .y of two vertices")
    lvl("  (invisible to the residual) and .z of one (visible). 2/3 of the")
    lvl("  imprint channel is undetectable by this metric.")
    lvl("  NOTE: the F77 port has NO residual routine at all.")


def _swapped(seq, rng):
    s = list(seq)
    i, j = rng.choice(32, size=2, replace=False)
    s[i], s[j] = s[j], s[i]
    return s


def main():
    with open("allocator/sq2core.f") as f:
        f77_text = f.read()
    with open("tests/sq3core.ergo") as f:
        ergo_text = f.read()

    c_out, c_det = run_c()
    f77_out, f77_det = run_f77()
    ergo_out, ergo_det = run_ergo()
    l2_out, l2_det = run_l2()
    lvl(f"[determinism] C driver twice byte-identical: {c_det}; "
        f"F77: {f77_det}; ergo: {ergo_det}; L2 relax: {l2_det}")

    verdicts, scat = section_l1(f77_text, ergo_text, c_out)
    DD, _ = section_l2(l2_out, scat)
    section_l3(scat, DD, f77_out, ergo_out, c_out)

    lvl()
    lvl("=" * 70)
    lvl("LEVEL 1 VERDICTS")
    lvl("=" * 70)
    for k, v in verdicts.items():
        lvl(f"  {k:8s} {v}")


if __name__ == "__main__":
    main()
