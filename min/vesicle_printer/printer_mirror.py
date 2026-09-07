#!/usr/bin/env python3
"""
PRINTER_MIRROR — independent mirror of vesicle_printer.ergo (Project CELL, M2)

Three-type monomer printer driven by real Syn3 tapes:
  acpA (Lipid class, 73 codons)  -> species A amphiphile (head sigma 1.05)
  sepF (Membrane, 138 codons)    -> species B amphiphile (head sigma 0.95, r0 0.45)
  crr  (Transport, 154 codons)   -> inclusion bead (PtsG-like transmembrane)

Print program: emission k reads tape PROG[k mod 10] (5A:4B:1INC per decade),
codons consumed sequentially per tape (wrap). Codon pole c//32 selects leaflet,
ring c%32 wobbles azimuth by WW*w(c).

Modes:
  --fd            finite-difference validation of every force term
  --cert ring|patch   static certification config, forces once, dump
  --run  ring|patch [steps]   dynamic smoke run
"""
import numpy as np
import math, sys

# ── exact RAND lowering (codegen.py: Weyl +phi FIRST, then Stafford) ──
M64 = (1 << 64) - 1
def _h64(seed):
    x = (int(seed) & M64)
    x = (x + 0x9E3779B97F4A7C15) & M64
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & M64
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & M64
    return x ^ (x >> 31)
def RAND(seed): return (_h64(seed) >> 11) * (2.0 ** -53)
def HASH(seed): return _h64(seed) >> 33

# ── Syn3 tapes (boundary-aware extraction; stop codon dropped) ──
TAPE_A = [6, 45, 5, 17, 1, 48, 5, 37, 0, 32, 20, 0, 9, 8, 41, 45, 2, 41, 1, 5, 12, 0, 33, 11, 32, 23, 0, 29, 52, 41, 20, 33, 29, 20, 35, 20, 6, 33, 6, 36, 37, 12, 20, 32, 32, 0, 20, 1, 5, 8, 7, 9, 33, 35, 48, 20, 52, 11, 20, 57, 13, 5, 33, 33, 20, 20, 0, 39, 4, 34, 32, 20, 48]
TAPE_B = [6, 21, 21, 0, 2, 0, 2, 1, 21, 21, 0, 48, 3, 32, 48, 33, 48, 33, 48, 5, 32, 52, 32, 20, 13, 33, 29, 33, 5, 21, 32, 48, 32, 9, 61, 37, 20, 0, 33, 9, 17, 13, 50, 12, 29, 1, 48, 21, 1, 48, 1, 49, 48, 12, 1, 13, 28, 1, 6, 3, 48, 13, 33, 6, 1, 0, 9, 61, 5, 3, 13, 17, 36, 21, 9, 61, 6, 0, 21, 29, 32, 37, 48, 28, 5, 36, 33, 13, 20, 20, 33, 48, 0, 37, 37, 37, 36, 33, 21, 0, 3, 20, 33, 33, 1, 0, 45, 0, 57, 21, 0, 33, 21, 53, 29, 40, 37, 20, 17, 5, 0, 0, 41, 32, 19, 7, 8, 53, 1, 32, 1, 5, 17, 0, 21, 4, 5, 1]
TAPE_T = [6, 24, 21, 21, 1, 0, 1, 20, 0, 37, 20, 45, 61, 25, 33, 40, 0, 4, 5, 12, 20, 33, 32, 37, 32, 33, 33, 37, 21, 8, 32, 8, 6, 20, 41, 33, 40, 21, 44, 5, 17, 60, 12, 28, 3, 33, 21, 49, 45, 60, 37, 9, 41, 0, 20, 36, 13, 45, 21, 60, 12, 2, 49, 45, 21, 40, 5, 48, 12, 0, 1, 41, 37, 32, 7, 20, 20, 49, 5, 41, 20, 33, 12, 36, 9, 20, 33, 41, 1, 41, 21, 34, 28, 17, 36, 5, 48, 33, 48, 32, 37, 1, 45, 40, 35, 0, 20, 36, 13, 37, 33, 20, 48, 32, 36, 29, 0, 0, 37, 60, 28, 5, 0, 29, 60, 7, 5, 21, 12, 3, 1, 41, 40, 0, 13, 20, 32, 5, 36, 0, 6, 40, 32, 37, 0, 0, 43, 33, 37, 37, 45, 5, 20, 0]
TAPES = {0: TAPE_A, 1: TAPE_B, 2: TAPE_T}
TAPE_LEN = {k: len(v) for k, v in TAPES.items()}
PROG = [0, 0, 1, 0, 1, 0, 0, 1, 0, 2]     # per-decade: 5 A, 4 B, 1 inclusion

def codon_w(c):
    ring = c % 32; pole = c // 32
    th = ring * 2.0 * math.pi / 32.0
    return (1.0 if pole == 0 else -1.0) * (1.0 / 3.0) * math.sin(5.0 * th)

# ── model parameters (must match vesicle_printer.ergo exactly) ──
LBOX   = 36.0
RCTT   = 2.6
KBOND  = 100.0
R0A, R0B = 0.5, 0.45
HSA, HSB = 1.05, 0.95
KAL    = 1.5
RB     = 2.6
BENDMODE = 1                            # 1 = nematic q^2, 0 = polar
SIG_IT = 1.3; SIG_IH = 1.3; SIG_II = 1.5; RCINC = 2.6
FCAP   = 500.0
XWALL, KWALL = 0.5, 100.0
DT     = 0.002
GAMMA, GAMMA_HOT, KT = 0.5, 10.0, 0.2
KANC   = 50.0
WW     = 0.02
K_EMIT = 25
NDECAY = 3000
SEED   = 77031
C216   = 2.0 ** (1.0 / 6.0)

# blueprint geometry
# Ring radius chosen so same-leaflet neighbor chord ~1.18 sigma (outside WCA
# core) and nearest cross-leaflet tail-tail ~1.28 sigma (outside LJ minimum):
# RING_R=12, N=64 -> chord 1.178; inner leaflet at R-1.0.
RING_R, RING_N = 12.0, 64
# M3 cheap closure (mode 'shrink'): after printing, anchor sites march
# inward RING_R -> SHRINK_R_END over N_SHRINK steps, then release as usual.
# The bilayer keeps its material; the shrinking circumference must buckle
# out of plane — geometry self-aligns, no Helfrich machinery.
SHRINK_R_END = 3.0
N_SHRINK = 4000
# M3b (mode 'stack'): two rings at z = cz +- RING_HZ, emission k alternates
# rings (k mod 2), site index k//2. Gap 2.5 sits just inside the tail LJ
# range so the seam welds during closure. Inclusions ride ZI outward of
# their ring plane (docking pose): same-plane printing puts the nearest
# belt tails at d~1.0, inside the IT LJ core -> capped forces, FD-invalid.
RING_HZ = 1.25
ZI = 0.7
# Inclusion anchor schedule: inclusions ride the rail at full KANC through
# print AND shrink (marching with the scaffold, at their ring's plane z),
# then release over N_SEAT steps into the closed structure's belt — dock
# after closure. (Releasing them early loses them: the ring marches away
# inward faster than the IT attraction drags them.)
N_SEAT = 500
PATCH_N, PATCH_SP, PATCH_Z = 12, 1.15, 0.55    # 12x12 sites, leaflet gap

NMAX  = 320          # amph capacity
NBM   = 2 * NMAX
NINCM = 64           # inclusion capacity

# ══════════════════════════════════════════════════════════════
# STATE
# ══════════════════════════════════════════════════════════════
class State:
    def __init__(self, mode):
        self.mode = mode                      # 'ring' or 'patch'
        self.pos = np.zeros((NBM, 3))         # amph beads (head 2i, tail 2i+1, 0-based)
        self.vel = np.zeros((NBM, 3))
        self.f   = np.zeros((NBM, 3))
        self.sigb = np.zeros(NBM)             # per-bead sigma (heads HSx, tails 1.0)
        self.r0m  = np.zeros(NMAX)            # per-amph bond length
        self.anchor = np.zeros((NBM, 3))
        self.has_anchor = np.zeros(NBM, dtype=bool)
        self.nact = 0                         # active beads
        self.namph = 0
        self.ipos = np.zeros((NINCM, 3))      # inclusions
        self.ivel = np.zeros((NINCM, 3))
        self.ifc  = np.zeros((NINCM, 3))
        self.ianchor = np.zeros((NINCM, 3))
        self.i_anchor_on = np.zeros(NINCM, dtype=bool)
        self.ninc = 0
        self.cursors = {0: 0, 1: 0, 2: 0}
        self.events = []
        self.site_th = np.zeros(NBM)          # blueprint azimuth per bead
        self.site_roff = np.zeros(NBM)        # radial offset rel. RING_R
        self.site_z = np.full(NBM, LBOX * 0.5)  # blueprint plane z per bead
        self.i_site_th = np.zeros(NINCM)
        self.i_site_roff = np.zeros(NINCM)
        self.i_site_z = np.full(NINCM, LBOX * 0.5)

    # ── emission ────────────────────────────────────────────
    def emit(self, k):
        """Emit monomer k (0-based). Returns event tuple."""
        seg = PROG[k % 10]
        cur = self.cursors[seg]
        c = TAPES[seg][cur % TAPE_LEN[seg]]
        self.cursors[seg] = cur + 1
        pole = c // 32
        wob = WW * codon_w(c)
        cx, cy, cz = LBOX * 0.5, LBOX * 0.5, LBOX * 0.5
        if seg == 2:
            # inclusion bead — occupies the current site (head advances per codon)
            i = self.ninc; self.ninc += 1
            if self.mode in ('ring', 'shrink'):
                th = 2.0 * math.pi * k / RING_N + wob
                p = np.array([cx + (RING_R - 0.5) * math.cos(th),
                              cy + (RING_R - 0.5) * math.sin(th), cz])   # midplane
            elif self.mode == 'stack':
                ks, kr = k // 2, k % 2
                th = 2.0 * math.pi * ks / RING_N + wob
                z0 = cz + (RING_HZ + ZI) if kr == 0 else cz - (RING_HZ + ZI)
                p = np.array([cx + (RING_R - 0.5) * math.cos(th),
                              cy + (RING_R - 0.5) * math.sin(th), z0])
            else:
                gx, gy = k % PATCH_N, (k // PATCH_N) % PATCH_N
                p = np.array([cx + (gx - (PATCH_N - 1) / 2.0) * PATCH_SP,
                              cy + (gy - (PATCH_N - 1) / 2.0) * PATCH_SP, cz])
            self.ipos[i] = p; self.ivel[i] = 0.0
            self.ianchor[i] = p; self.i_anchor_on[i] = True
            if self.mode in ('ring', 'shrink'):
                self.i_site_th[i] = 2.0 * math.pi * k / RING_N + wob
                self.i_site_roff[i] = -0.5
            elif self.mode == 'stack':
                self.i_site_th[i] = th
                self.i_site_roff[i] = -0.5
                # march target sits in the belt (ring plane), not the
                # outward ZI print pose: the first march step slides it in.
                self.i_site_z[i] = cz + RING_HZ if kr == 0 else cz - RING_HZ
            self.events.append((k, seg, c, pole))
            return
        # amphiphile
        a = self.namph; self.namph += 1; self.nact += 2
        hs = HSA if seg == 0 else HSB
        r0 = R0A if seg == 0 else R0B
        self.sigb[2 * a] = hs; self.sigb[2 * a + 1] = 1.0
        self.r0m[a] = r0
        if self.mode in ('ring', 'shrink', 'stack'):
            if self.mode == 'stack':
                ks, kr = k // 2, k % 2
                th = 2.0 * math.pi * ks / RING_N + wob
                zpl = cz + RING_HZ if kr == 0 else cz - RING_HZ
            else:
                th = 2.0 * math.pi * k / RING_N + wob   # site index = emission index
                zpl = cz
            if pole == 0:   # outer leaflet: head radially out
                rs, sgn = RING_R, 1.0
            else:           # inner leaflet: head radially in
                rs, sgn = RING_R - 1.0, -1.0
            rhat = np.array([math.cos(th), math.sin(th), 0.0])
            base = np.array([cx + rs * rhat[0], cy + rs * rhat[1], zpl])
        else:
            gx, gy = k % PATCH_N, (k // PATCH_N) % PATCH_N
            if pole == 0:
                zs, sgn = cz + PATCH_Z, 1.0    # upper leaflet: head up
            else:
                zs, sgn = cz - PATCH_Z, -1.0   # lower leaflet: head down
            base = np.array([cx + (gx - (PATCH_N - 1) / 2.0) * PATCH_SP,
                             cy + (gy - (PATCH_N - 1) / 2.0) * PATCH_SP,
                             zs + wob])
            rhat = np.array([0.0, 0.0, sgn])
        if self.mode in ('ring', 'shrink', 'stack'):
            hoff = 0.5 * r0 * sgn     # inner leaflet: head toward center
        else:
            hoff = 0.5 * r0           # patch: sgn carried by rhat (z-axis)
        head = base + hoff * rhat; tail = base - hoff * rhat
        if self.mode in ('ring', 'shrink', 'stack'):
            self.site_th[2 * a] = th; self.site_th[2 * a + 1] = th
            self.site_roff[2 * a] = (rs - RING_R) + hoff      # head
            self.site_roff[2 * a + 1] = (rs - RING_R) - hoff  # tail
            self.site_z[2 * a] = zpl; self.site_z[2 * a + 1] = zpl
        self.pos[2 * a] = head; self.pos[2 * a + 1] = tail
        self.vel[2 * a] = 0.0; self.vel[2 * a + 1] = 0.0
        self.anchor[2 * a] = head; self.anchor[2 * a + 1] = tail
        self.has_anchor[2 * a] = True; self.has_anchor[2 * a + 1] = True
        self.events.append((k, seg, c, pole))

    def print_all(self, nmono):
        for k in range(nmono):
            self.emit(k)

# ══════════════════════════════════════════════════════════════
# ENERGY + FORCES  (single source of truth; forces = analytic)
# ══════════════════════════════════════════════════════════════
def lj_pair(d2, sig, attractive, rc):
    """Return (E, dE/dd) for 4[(s/d)^12-(s/d)^6]; WCA = attractive=False,
    cutoff at 2^(1/6)s; LJ cutoff rc. d2 = d^2."""
    d = math.sqrt(d2)
    cut = rc if attractive else C216 * sig
    if d >= cut or d < 1e-12:
        return 0.0, 0.0
    sr = sig / d
    b6 = sr ** 6
    e = 4.0 * (b6 * b6 - b6)
    fm = 24.0 * (2.0 * b6 * b6 - b6) / (d * d)   # F = fm * dvec
    return e, fm

def cap_fm(fm, d):
    m = min(1.0, FCAP / max(abs(fm) * d, 1e-16))
    return fm * m

def compute_forces(st, kanc, kanc_i=None, compute_energy=False):
    if kanc_i is None:
        kanc_i = kanc
    st.f[:] = 0.0; st.ifc[:] = 0.0
    E = dict(pair=0.0, bond=0.0, bend=0.0, inc=0.0, anch=0.0, wall=0.0)
    P = st.pos; n = st.nact
    # ── bead-bead pairs (skip self + bonded partner) ──
    for i in range(n):
        ai = i // 2
        pi = P[i]
        for j in range(i + 1, n):
            if j // 2 == ai:
                continue
            dvec = pi - P[j]
            d2 = float(dvec @ dvec)
            if d2 > RCTT * RCTT or d2 < 1e-24:
                continue
            d = math.sqrt(d2)
            hi = i % 2 == 0; hj = j % 2 == 0
            if not hi and not hj:
                e, fm = lj_pair(d2, 1.0, True, RCTT)
            else:
                sig = 0.5 * (st.sigb[i] + st.sigb[j])
                if hi != hj:
                    sig = sig - 0.10
                e, fm = lj_pair(d2, sig, False, 0.0)
            fm = cap_fm(fm, d)
            E['pair'] += e
            fv = fm * dvec
            st.f[i] += fv; st.f[j] -= fv
    # ── bonds + axes + bending ──
    na = st.namph
    if na > 0:
        axes = np.zeros((na, 3)); alen = np.zeros(na); cen = np.zeros((na, 3))
        fbnd = np.zeros((na, 3))
        for a in range(na):
            b = P[2 * a] - P[2 * a + 1]
            L = math.sqrt(float(b @ b)); Ld = max(L, 1e-16)
            fsc = 2.0 * KBOND * (Ld - st.r0m[a]) / Ld
            fbnd[a] = -fsc * b
            E['bond'] += KBOND * (Ld - st.r0m[a]) ** 2
            axes[a] = b / Ld; alen[a] = Ld
            cen[a] = 0.5 * (P[2 * a] + P[2 * a + 1])
        sums = np.zeros((na, 3))
        for a in range(na):
            for b2 in range(a + 1, na):
                dc = cen[a] - cen[b2]
                d2 = float(dc @ dc)
                if d2 > RB * RB or d2 < 1e-24:
                    continue
                q = float(axes[a] @ axes[b2])
                if BENDMODE == 1:
                    E['bend'] += -KAL * q * q
                    qa = 2.0 * q * (axes[b2] - q * axes[a])
                    qb = 2.0 * q * (axes[a] - q * axes[b2])
                else:
                    E['bend'] += -KAL * q
                    qa = axes[b2] - q * axes[a]
                    qb = axes[a] - q * axes[b2]
                sums[a] += qa; sums[b2] += qb
        for a in range(na):
            fd = KAL * sums[a] / alen[a]
            st.f[2 * a] += fbnd[a] + fd
            st.f[2 * a + 1] -= fbnd[a] + fd
    # ── inclusions ──
    for i in range(st.ninc):
        pi = st.ipos[i]
        # inclusion-inclusion WCA
        for j in range(i + 1, st.ninc):
            dv = pi - st.ipos[j]; d2 = float(dv @ dv)
            e, fm = lj_pair(d2, SIG_II, False, 0.0)
            d = math.sqrt(d2) if d2 > 0 else 0.0
            fm = cap_fm(fm, max(d, 1e-16))
            E['inc'] += e
            fv = fm * dv
            st.ifc[i] += fv; st.ifc[j] -= fv
        # inclusion-bead
        for b in range(n):
            dv = pi - P[b]; d2 = float(dv @ dv)
            head = b % 2 == 0
            if head:
                e, fm = lj_pair(d2, SIG_IH, False, 0.0)
            else:
                e, fm = lj_pair(d2, SIG_IT, True, RCINC)
            d = math.sqrt(d2) if d2 > 0 else 0.0
            fm = cap_fm(fm, max(d, 1e-16))
            E['inc'] += e
            fv = fm * dv
            st.ifc[i] += fv; st.f[b] -= fv
    # ── anchors ──
    if kanc > 0.0:
        for b in range(n):
            if st.has_anchor[b]:
                dvec = st.anchor[b] - P[b]
                st.f[b] += 2.0 * kanc * dvec
                E['anch'] += kanc * float(dvec @ dvec)
        for i in range(st.ninc):
            if st.i_anchor_on[i]:
                dvec = st.ianchor[i] - st.ipos[i]
                st.ifc[i] += 2.0 * kanc_i * dvec
                E['anch'] += kanc_i * float(dvec @ dvec)
    # ── walls ──
    for b in range(n):
        for cax in range(3):
            x = P[b, cax]
            if x < XWALL:
                st.f[b, cax] += 2.0 * KWALL * (XWALL - x)
                E['wall'] += KWALL * (XWALL - x) ** 2
            elif x > LBOX - XWALL:
                st.f[b, cax] -= 2.0 * KWALL * (x - (LBOX - XWALL))
                E['wall'] += KWALL * (x - (LBOX - XWALL)) ** 2
    for i in range(st.ninc):
        for cax in range(3):
            x = st.ipos[i, cax]
            if x < XWALL:
                st.ifc[i, cax] += 2.0 * KWALL * (XWALL - x)
                E['wall'] += KWALL * (XWALL - x) ** 2
            elif x > LBOX - XWALL:
                st.ifc[i, cax] -= 2.0 * KWALL * (x - (LBOX - XWALL))
                E['wall'] += KWALL * (x - (LBOX - XWALL)) ** 2
    return E

# ══════════════════════════════════════════════════════════════
# TOTAL ENERGY (for FD validation) — mirrors compute_forces exactly
# ══════════════════════════════════════════════════════════════
def total_energy(st, kanc):
    # perturbation-safe: recompute energies only (same formulas)
    E = 0.0
    P = st.pos; n = st.nact
    for i in range(n):
        for j in range(i + 1, n):
            if j // 2 == i // 2:
                continue
            dv = P[i] - P[j]; d2 = float(dv @ dv)
            if d2 > RCTT * RCTT or d2 < 1e-24:
                continue
            hi = i % 2 == 0; hj = j % 2 == 0
            if not hi and not hj:
                e, _ = lj_pair(d2, 1.0, True, RCTT)
            else:
                sig = 0.5 * (st.sigb[i] + st.sigb[j])
                if hi != hj:
                    sig -= 0.10
                e, _ = lj_pair(d2, sig, False, 0.0)
            E += e
    na = st.namph
    if na > 0:
        axes = np.zeros((na, 3)); cen = np.zeros((na, 3))
        for a in range(na):
            b = P[2 * a] - P[2 * a + 1]
            L = max(math.sqrt(float(b @ b)), 1e-16)
            E += KBOND * (L - st.r0m[a]) ** 2
            axes[a] = b / L; cen[a] = 0.5 * (P[2 * a] + P[2 * a + 1])
        for a in range(na):
            for b2 in range(a + 1, na):
                dc = cen[a] - cen[b2]; d2 = float(dc @ dc)
                if d2 > RB * RB or d2 < 1e-24:
                    continue
                q = float(axes[a] @ axes[b2])
                E += -KAL * q * q if BENDMODE == 1 else -KAL * q
    for i in range(st.ninc):
        for j in range(i + 1, st.ninc):
            dv = st.ipos[i] - st.ipos[j]
            e, _ = lj_pair(float(dv @ dv), SIG_II, False, 0.0); E += e
        for b in range(n):
            dv = st.ipos[i] - P[b]; d2 = float(dv @ dv)
            if b % 2 == 0:
                e, _ = lj_pair(d2, SIG_IH, False, 0.0)
            else:
                e, _ = lj_pair(d2, SIG_IT, True, RCINC)
            E += e
    if kanc > 0:
        for b in range(n):
            if st.has_anchor[b]:
                dv = st.anchor[b] - P[b]; E += kanc * float(dv @ dv)
        for i in range(st.ninc):
            if st.i_anchor_on[i]:
                dv = st.ianchor[i] - st.ipos[i]; E += kanc * float(dv @ dv)
    for b in range(n):
        for cax in range(3):
            x = P[b, cax]
            if x < XWALL: E += KWALL * (XWALL - x) ** 2
            elif x > LBOX - XWALL: E += KWALL * (x - (LBOX - XWALL)) ** 2
    for i in range(st.ninc):
        for cax in range(3):
            x = st.ipos[i, cax]
            if x < XWALL: E += KWALL * (XWALL - x) ** 2
            elif x > LBOX - XWALL: E += KWALL * (x - (LBOX - XWALL)) ** 2
    return E

# ══════════════════════════════════════════════════════════════
# FD VALIDATION
# ══════════════════════════════════════════════════════════════
def fd_check(mode='ring', nmono=32, eps=1e-6):
    st = State(mode)
    st.print_all(nmono)
    # jitter off-anchor so anchor/bond/bend gradients are nonzero
    k = 0
    for b in range(st.nact):
        for cax in range(3):
            st.pos[b, cax] += 0.03 * (RAND(991 + 7 * k) - 0.5); k += 1
    for i in range(st.ninc):
        for cax in range(3):
            st.ipos[i, cax] += 0.03 * (RAND(991 + 7 * k) - 0.5); k += 1
    compute_forces(st, KANC)
    max_rel = 0.0; max_abs = 0.0
    # bead forces
    for b in range(st.nact):
        for cax in range(3):
            dp = st.pos[b, cax]
            st.pos[b, cax] = dp + eps; ep = total_energy(st, KANC)
            st.pos[b, cax] = dp - eps; em = total_energy(st, KANC)
            st.pos[b, cax] = dp
            fd = -(ep - em) / (2 * eps)
            an = st.f[b, cax]
            d_abs = abs(fd - an); d_rel = d_abs / max(abs(fd), abs(an), 1e-9)
            max_abs = max(max_abs, d_abs); max_rel = max(max_rel, d_rel)
    for i in range(st.ninc):
        for cax in range(3):
            dp = st.ipos[i, cax]
            st.ipos[i, cax] = dp + eps; ep = total_energy(st, KANC)
            st.ipos[i, cax] = dp - eps; em = total_energy(st, KANC)
            st.ipos[i, cax] = dp
            fd = -(ep - em) / (2 * eps)
            an = st.ifc[i, cax]
            d_abs = abs(fd - an); d_rel = d_abs / max(abs(fd), abs(an), 1e-9)
            max_abs = max(max_abs, d_abs); max_rel = max(max_rel, d_rel)
    print(f"printer FD ({mode}, nmono={nmono}): max_abs={max_abs:.6e} max_rel={max_rel:.6e}")
    return max_rel

# ══════════════════════════════════════════════════════════════
# DYNAMICS
# ══════════════════════════════════════════════════════════════
def integrate(st, step, kanc):
    gr = GAMMA_HOT if step <= N_HOT_RUN else GAMMA
    na_ = math.sqrt(12.0 * KT * (1.0 - (1.0 - gr * DT) * (1.0 - gr * DT)))
    sn = HASH(SEED + step)
    n = st.nact
    for b in range(n):
        for cax in range(3):
            st.vel[b, cax] = (st.vel[b, cax] * (1.0 - gr * DT) + st.f[b, cax] * DT
                              + na_ * (RAND(sn + 3 * b + cax) - 0.5))
            st.pos[b, cax] += st.vel[b, cax] * DT
    for i in range(st.ninc):
        for cax in range(3):
            st.ivel[i, cax] = (st.ivel[i, cax] * (1.0 - gr * DT) + st.ifc[i, cax] * DT
                               + na_ * (RAND(sn + 300000 + 3 * i + cax) - 0.5))
            st.ipos[i, cax] += st.ivel[i, cax] * DT

N_HOT_RUN = 10 ** 9   # set per-run below

def march_anchors(st, r_now):
    """Move ring-mode anchor sites to radius r_now (plane z is the site's own)."""
    cx, cy = LBOX * 0.5, LBOX * 0.5
    for b in range(st.nact):
        th = st.site_th[b]; rr = r_now + st.site_roff[b]
        st.anchor[b] = (cx + rr * math.cos(th), cy + rr * math.sin(th), st.site_z[b])
    for i in range(st.ninc):
        th = st.i_site_th[i]; rr = r_now + st.i_site_roff[i]
        st.ianchor[i] = (cx + rr * math.cos(th), cy + rr * math.sin(th), st.i_site_z[i])


def run(mode='ring', nmono=64, nsteps=2500, verbose=True):
    global N_HOT_RUN
    nprint = nmono * K_EMIT
    nshr = N_SHRINK if mode in ('shrink', 'stack') else 0
    N_HOT_RUN = nprint + nshr + NDECAY  # hot damping until anchors fully released
    st = State(mode)
    kemit = 0
    hist = []
    for step in range(1, nsteps + 1):
        integrate(st, step, 0.0 if step == 1 else kanc_prev)
        # emission after integrate
        if kemit < nmono and step % K_EMIT == 0:
            st.emit(kemit); kemit += 1
        # anchor stiffness schedule: print -> shrink (full KANC) -> release
        if step <= nprint + nshr:
            kanc_prev = KANC
        else:
            kanc_prev = KANC * max(0.0, 1.0 - (step - nprint - nshr) / NDECAY)
        # inclusions: hold through print+shrink, dock after closure
        if step <= nprint + nshr:
            kanc_i = KANC
        else:
            kanc_i = KANC * max(0.0, 1.0 - (step - nprint - nshr) / N_SEAT)
        if mode in ('shrink', 'stack') and step > nprint and step <= nprint + nshr:
            r_now = RING_R + (SHRINK_R_END - RING_R) * (step - nprint) / N_SHRINK
            march_anchors(st, r_now)
        E = compute_forces(st, kanc_prev, kanc_i)
        if step % 250 == 0 or step == nsteps:
            t2 = float((st.vel[:st.nact] ** 2).sum()) / max(3 * st.nact, 1)
            fmax = float(np.abs(st.f[:st.nact]).max()) if st.nact else 0.0
            hist.append((step, t2, E, fmax, st.nact, st.ninc))
            if verbose:
                print(f"step {step:6d} kt {t2:.4f} epair {E['pair']:.6e} "
                      f"ebond {E['bond']:.6e} ebend {E['bend']:.6e} "
                      f"einc {E['inc']:.6e} eanch {E['anch']:.6e} "
                      f"nact {st.nact} ninc {st.ninc} fmax {fmax:.3e} kanc {kanc_prev:.2f}")
    return st, hist

def closure_metrics(st):
    """Ring/patch quality: radius stats of tails, exposed-tail count."""
    n = st.nact
    if n == 0:
        return {}
    cen = st.pos[:n].mean(axis=0)
    tails = st.pos[1:n:2]
    rr = np.linalg.norm(tails - cen, axis=1)
    zsp = float(np.std(tails[:, 2]))
    # tail coordination (LJ pairs)
    zt = np.zeros(n, dtype=int)
    for i in range(n):
        for j in range(i + 1, n):
            if j // 2 == i // 2:
                continue
            if i % 2 == 1 and j % 2 == 1:
                d2 = float(((st.pos[i] - st.pos[j]) ** 2).sum())
                if d2 < RCTT * RCTT:
                    zt[i] += 1; zt[j] += 1
    nexp = int((zt[1:n:2] < 6).sum())
    return dict(rmean=float(rr.mean()), rstd=float(rr.std()),
                zstd=zsp, nexp=nexp, ntail=max(n // 2, 1))

# ══════════════════════════════════════════════════════════════
# CERTIFICATION DUMP (mirror mode): static config -> forces
# ══════════════════════════════════════════════════════════════
def cert(mode='ring', nmono=64, out=None):
    if out is None:
        out = f'/tmp/printer_cert_{mode}'
    st = State(mode)
    st.print_all(nmono)
    E = compute_forces(st, KANC)
    with open(out + '_config.txt', 'w') as f:
        f.write(f"{st.namph} {st.ninc} {mode}\n")
        for b in range(st.nact):
            f.write(f"{st.pos[b,0]:.17e} {st.pos[b,1]:.17e} {st.pos[b,2]:.17e}\n")
        for i in range(st.ninc):
            f.write(f"{st.ipos[i,0]:.17e} {st.ipos[i,1]:.17e} {st.ipos[i,2]:.17e}\n")
    with open(out + '_forces.txt', 'w') as f:
        for b in range(st.nact):
            f.write(f"{st.f[b,0]:.17e} {st.f[b,1]:.17e} {st.f[b,2]:.17e}\n")
        for i in range(st.ninc):
            f.write(f"{st.ifc[i,0]:.17e} {st.ifc[i,1]:.17e} {st.ifc[i,2]:.17e}\n")
    print(f"cert ({mode}, nmono={nmono}): E={E}")
    print(f"  wrote {out}_config.txt / {out}_forces.txt")

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or args[0] == '--fd':
        fd_check('ring', 32)
        fd_check('patch', 40)
    elif args[0] == '--cert':
        mode = args[1] if len(args) > 1 else 'ring'
        nm = 64 if mode == 'ring' else 144
        cert(mode, nm)
    elif args[0] == '--run':
        mode = args[1] if len(args) > 1 else 'ring'
        nsteps = int(args[2]) if len(args) > 2 else (14000 if mode == 'stack' else (11000 if mode == 'shrink' else 2500))
        nm = 144 if mode == 'patch' else (128 if mode == 'stack' else 64)
        st, hist = run(mode, nm, nsteps)
        m = closure_metrics(st)
        print("closure:", m)
