# PRINTER_SPEC — Project CELL, Milestone M2: the Codon-Driven 3-Type Printer

2026-08-14. Status: **engine-certified against the mirror, both blueprints; M3 cheap closure (shrink-ring) working and stable; decoder enrichment hooks identified from the preprocessor/fitness uploads.**

This document specifies the vesicle printer: a scripted print head that reads real
Syn3 gene tapes codon-by-codon and emits monomers onto a blueprint, bridging the
ribosome side of Project CELL (codons in) to the vesicle side (bilayer out).

---

## 1. What the printer is

A deterministic ergo engine (`vesicle_printer.ergo`, M1-optimized force field
generalized to three monomer types) plus an FD-validated Python mirror
(`printer_mirror.py`). The print head advances one blueprint site per codon.
Each codon does double duty:

1. **Which tape is being read** (the emission program `PROG`) selects the
   **material channel** — which monomer type is printed.
2. **The codon's own bits** (pole = c/32, ring = c mod 32, shadow w(c)) modulate
   the **placement geometry** — leaflet choice and azimuthal wobble.

Printed monomers are frozen by anchor springs to their blueprint sites; after the
last emission the anchors release linearly over `NDECAY` steps — the rail
schedule made concrete: **print → gated release → free dynamics**.

## 2. The 3-type monomer library (rich decoder)

Grounded in the 4DWCM paper (Thornburg et al. 2026, *Cell* — the project-inspiring
PDF): a minimal cell's membrane grows by **insertion** of lipids and membrane
proteins, and **two lipid species suffice** for a viable Syn3A membrane. Hence:

| type | monomer | tape (real Syn3 gene) | gene class | codons |
|---|---|---|---|---|
| species A amphiphile | dumbbell, head σ=1.05, bond r₀=0.50 | `acpA` | Lipid | 73 |
| species B amphiphile | dumbbell, head σ=0.95, bond r₀=0.45 | `sepF` | Membrane | 138 |
| inclusion bead | PtsG-like transmembrane protein | `crr` | Transport | 154 |

Species A is **identical** to the validated M1 baseline (σ 1.05/0.95/1.0
convention via a −0.10 HT shift), so all prior vesicle certification carries over.

Emission program: `PROG = [0,0,1,0,1,0,0,1,0,2]` — emission k reads tape
`PROG[k mod 10]`, i.e. **5 A : 4 B : 1 inclusion per decade**. Each tape is read
with its own cursor, wrapping modulo its length. Tapes were extracted
boundary-aware from the Syn3 genome (gene-frame codons expanded to bases, exact
nucleotide slice, reverse-complement on the minus strand, stop codon dropped;
table-4 convention TGA=Trp).

## 3. The decoder (codon → geometry)

For codon c emitted at site k:

- **pole** `p = c / 32` selects the **leaflet**: pole 0 → outer (ring) / upper
  (patch), pole 1 → inner / lower.
- **ring** `r = c mod 32` sets the **azimuthal wobble**:
  `w(c) = ±(1/3)·sin(5·2πr/32)` (sign + for pole 0, − for pole 1),
  applied as `θ = 2πk/64 + WW·w(c)` with `WW = 0.02` rad (ring),
  or as a z-jitter `z = z₀ + WW·w(c)` (patch).

This is the minimal honest decoder: the gene's functional class chooses the
material, the codon sequence perturbs placement. Nothing in the 4DWCM paper or
the classifier prototypes provides a real codon→geometry mapping — this grammar
is ours, and it is deliberately small until the physics says it should grow.

## 4. Blueprints

- **Ring** (`PRINTMODE=1`, `NMONO=64`): sites on a circle of radius
  `RING_R=12.0`, `RING_N=64` sites. Pole 0 heads point radially out at R+½r₀,
  pole 1 heads radially in at (R−1)−½r₀; inclusions sit mid-ring at R−0.5.
  Prints a closed bilayer ring (cross-section of a tubule).
- **Patch** (`PRINTMODE=2`, `NMONO=144`): 12×12 grid, spacing 1.15, leaflets at
  z = ∓0.55 about the midplane, heads pointing away from it. Prints a flat
  bilayer patch — the curvature-free control.

Both blueprints were tuned so no two printed beads sit inside each other's
force cores at the print site (nearest same-leaflet chord 1.178σ, nearest
cross-leaflet tail-tail 1.28σ) — required for FD validity and a cap-free start.

## 5. Force field (M1, generalized)

- tail–tail: LJ σ=1, cutoff 2.6 (unshifted); head–head: WCA σ=combined;
  head–tail: WCA σ=combined−0.10. Combining is Lorentz over per-bead σ.
- bonds: harmonic K=100, per-species r₀.
- bending: **nematic** E=−KAL·q² (KAL=1.5, centroid cutoff 2.6) — accepts the
  antiparallel leaflets a printed bilayer has. `BENDMODE=0` restores polar.
- inclusions: WCA σ=1.5 among themselves, WCA σ=1.3 to heads, **LJ σ=1.3 to
  tails** (the hydrophobic belt that seats the protein).
- anchors: `f = 2·KAC·(site−pos)`, KAC = KANC = 50 during print, linear ramp to
  0 over NDECAY=3000 after the last emission.
- soft walls (XWALL=0.5, KWALL=100), vector force cap FCAP=500, discrete-exact
  Langevin (DT=0.002, KT=0.2, γ=10 hot during print+release, 0.5 after).

## 6. Verification (all passed)

**Mirror FD validation** (analytic forces vs finite differences of total energy):
ring max_rel = 1.36e-6, patch 8.85e-7 — both at the FD noise floor.

**Static certification** (`MIRROR=1`, engine vs mirror cert dumps):

| oracle | ring | patch |
|---|---|---|
| config positions | max_abs 3.6e-15 | **byte-exact** |
| forces | max_abs 7.3e-12 | max_abs 7.1e-14 |
| EP_BEND | −152.27164588060143 (mirror …145) | **−1189.5 exactly** (793 pairs at \|q\|=1) |
| EP_PAIR | −50.589767111093373 (mirror …931) | −253.48275216492149 (mirror …215) |
| EP_INC | 115.62093145744750 (mirror …446) | 153.76180064179312 (mirror …793) |

Cert procedure: set `MIRROR=1` (and `NMONO=144` for patch), compile, run, collect
the `CFG`/`FRC`/`CERT` stdout rows, diff against `printer_cert_<mode>_*.txt`.

**Dynamic stability** (delivered defaults, NSTEPS=8000):

- Ring: prints 58 amphs + 6 inclusions over 1600 steps (rshell tracks blueprint
  2.6→11.5, kT 0.17–0.23); after release rshell holds 11.14–11.17, kT≈0.2,
  fmax ~20, zero wall escapes, zero list overflows. FINAL: rmean 11.1575,
  rstd 0.62 — a coherent free ring.
- Patch: 130 amphs + 14 inclusions; nexp 1–4 exposed tails of 130 throughout and
  after release; post-release compaction 5.29→4.85 with no exposure growth —
  the patch tightens, it does not disintegrate.

Note: DIAG's epair/ebend follow the parent vesicle_asm convention of summing the
directed neighbor list (2× physical energy); CERT_ENERGY/FINAL_E are physical
(single-counted) and match the mirror.

## 7. Run commands

```bash
# engine (delivered defaults: ring, 64 monomers, 8000 steps)
python -m core vesicle_printer.ergo -o /tmp/vprt && /tmp/vprt

# patch variant: set PRINTMODE=2, NMONO=144
# M3 closure: set PRINTMODE=3, NSTEPS=12000  (print 1600 -> shrink 4000
#             -> release 3000 -> ~3400 free)
# static certification: additionally set MIRROR=1 and diff CFG/FRC rows
#   against printer_cert_<mode>_{config,forces}.txt

# mirror
python3 printer_mirror.py --fd            # FD validation, both blueprints
python3 printer_mirror.py --cert ring     # write cert dumps
python3 printer_mirror.py --cert patch
python3 printer_mirror.py --run ring 2500 # dynamic smoke
python3 printer_mirror.py --run shrink    # M3 closure (11000 steps)
python3 printer_mirror.py --run stack     # M3b two-ring stack (14000 steps)
```

## 8. M3 cheap closure (PRINTMODE=3) — DONE 2026-08-14

User's call: cheap version first, no Helfrich machinery — "the geometry should
self align if we get the structures right."

Design: ring print exactly as mode 1; then the anchor sites march inward
`R(t) = RING_R + (SHRINK_R_END − RING_R)·(t−NPRINT)/N_SHRINK` at full KANC
(anchor z stays on the midplane — buckling is the physics' job, not the
schedule's); then the usual NDECAY release; then free. Per-bead blueprint
azimuth and radial offset are recorded at emission (`STH`/`SROFF`).

Engine result (NMONO=64, RING_R 12→3 over 4000 steps, NSTEPS=12000):
rshell 11.5 → 2.7 at end of shrink; **nexp = 0 from step 4500 onward**
(every tail coordinated, eedge 0); kT spike 0.68 during the march, settling
to 0.2; after full release the closed structure holds at rmean 2.60,
rstd 0.66 for 3400 free steps, no escapes, no overflows. The free ring
(control, mode 1) stays open at rmean 11.16. Closure is real, self-aligned,
and stable without anchors.

The same schedule in the mirror (`--run shrink`) confirms the phenomenon in
an independent implementation (trajectories diverge chaotically; statistics
are the cross-check).

## 8b. M3b two-ring stack (PRINTMODE=4) — DONE 2026-08-14

Design: two 64-site bilayer rings printed at z = cz ± RING_HZ (RING_HZ=1.25;
gap 2.5 sits just inside the tail LJ range so the seam welds). Emission k
alternates rings (k mod 2), site index k/2. Same shrink schedule as M3.

Blueprint hazard found and fixed (mirror-first discipline): same-plane
inclusions in the stack sit ~1.0 from the nearest belt tails — inside the
IT LJ core, capped forces, FD-invalid (max_rel 0.54). Fix: inclusions ride
ZI=0.7 outward of their ring plane (docking pose, d_min→1.20, FD max_rel
2.0e-6). Ring/patch certs untouched (stack-only change).

Cargo schedule — dock-after-closure (IAC, separate from KAC): inclusions
hold at FULL anchor strength through print AND shrink, with their march
z-target set to the ring plane (ISZ0 = cz ± RING_HZ), not the print pose —
the first march step slides them into the belt and they ride the rail
inward with the rings. Only AFTER closure do they release, linearly over
N_SEAT=500 steps. Negative result that forced this design: releasing
inclusions right after the print loses them entirely (final r = 10.99±2.18
vs body rmax 5.15) — the rings march inward faster than the IT attraction
can drag a free inclusion, so the cargo gets abandoned on the rail. Hold-
through-shrink is mandatory.

Static cert (MIRROR=1, NMONO=128): config max_abs 3.6e-15, forces max_abs
1.7e-12, energies match the mirror to 13–15 digits (epair
−104.2655497388683, ebend −348.0350830956970, einc −12.8138080409380).
Re-diffed clean after the cargo-schedule edits (ring 3.6e-15/7.3e-12,
patch byte-exact/7.1e-14, stack 3.6e-15/1.7e-12).

Engine closure run (NMONO=128, NSTEPS=14000: print 3200 → shrink 4000 →
release 3000+500 seat → 3800 free): rshell 11.5 → 3.11; kT spike 0.65
during the march, settling to ~0.25 free; **stable through 3800 free steps
with no anchors, no escapes (nout 0)**. FINAL: namph 116 ninc 12 nexp 1
rmean 3.1063 rstd 0.8445 rmin 1.0812 rmax 5.2623 **zstd 1.3909** — vs 0.75
for the 1-ring shrink and 0.48 for the flat patch: two caps closing toward
each other, best 3D coverage yet. Still oblate (zstd/rmean ≈ 0.45), not
yet spherical — the route to a full shell is more rings / taller stacks,
same machinery. Cargo: all 12 inclusions embedded in the finished shell at
r = 3.79±1.26 rel centroid (11 at r 3.1–5.8 in the belt, 1 at r 0.39 near
the core) — carried in, seated, retained.

Mirror independent run (`printer_mirror.py --run stack 14000`, same dock-
after-closure schedule): rmean 2.957±0.725, **zstd 1.332, nexp 0/116**,
stable through the full 3800 free steps at kT ≈ 0.22 — reproduces the
engine (rmean 3.106, zstd 1.391, nexp 1) within statistical divergence;
the two-cap closure is mirror-confirmed, not an engine artifact.

## 9. Decoder enrichment hooks (from the 2026-08-14 uploads)

The preprocessors + `predict_organism(1).py` + `MCLtranslation.md` close the
"richer details" gap:

1. **The wobble IS the siphon.** `predict_organism --siphon` defines the
   axis-2 escape dimension w(c) = ±⅓sin(5θ) over the same 32 ring positions
   with the same pole sign convention the printer uses — the printer's WW·w(c)
   wobble is exactly this coordinate. Per-tape siphon: acpA −0.018,
   sepF +0.038, crr +0.016; the PROG-weighted program (5A:4B:1INC) nets
   **+0.079 — the printed structure pumps positive**, matching the uploads'
   viability doctrine (all viable organisms pump positive).
2. **Promoter strengths** (per-gene, 0.1–1.0, upstream AT-content + class
   boost, table-4-aware) → per-tape emission cadence (K_EMIT per tape
   instead of one global cadence). Staged, not yet wired.
3. **Class fractions → PROG.** `derive_rates` maps class fractions to
   MREFF/SYEFF/ADECAY; the same fractions can generate the emission program
   instead of the hand-set 5:4:1, making the print mixture organism-specific.
4. **Fitness oracle.** `predict_delta` (M*, M_cliff, Δ, failure mode) is the
   viability scoring function for any genome-driven print program; the
   MCLtranslation membrane electrochemistry (mesh↔leak↔PSI↔ATP loop,
   7-operation tick, PSI≈−246 mV / ATP≈0.88 steady state) is the natural
   next layer to couple to the printer's output structure.

## 10. Known limits / next steps

1. **nexp is shell-calibrated**: a thin ring is all edge (all 58 tails read
   "exposed" in mode 1). The shrink run shows the metric working as intended
   once the structure compacts (58 → 0).
2. The decoder grammar is deliberately minimal (pole→leaflet, ring→wobble).
   Hooks in §9 are staged, not yet physics.
3. Closed structures so far are caps (1-ring: zstd 0.75; 2-ring stack:
   zstd 1.39), not spheres. Next rungs: taller stacks (3-4 rings), then a
   latitude-blueprint sphere. The shrink schedule + nematic self-alignment
   carry over unchanged.
4. Gene→class assignment currently uses the classifier's clean-ORF picks
   (acpA/sepF/crr). Swapping tapes is a DATA-block edit; keep
   LENA/LENB/LENT in sync.
