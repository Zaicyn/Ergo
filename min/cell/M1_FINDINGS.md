# M1 FINDINGS — 3D vesicle self-assembly

Project CELL, milestone M1. Pre-registered sections (oracles, bands,
thresholds, parameter set) written 2026-08-30 BEFORE the production
runs; the results sections are filled in after. Any post-hoc
recalibration is marked as such — a moved threshold is a failed
oracle, not an edited one.

## Model (design choice, documented before running)

**Two-bead dumbbell amphiphile** (Noguchi-style, solvent-free): each
amphiphile is a HEAD bead + a TAIL bead on a harmonic bond. Chosen over
one-bead-with-dipole because (a) the proven 2D sheet
(`tests/waveform_membrane.ergo`) is built from explicit HEAD/TAIL
beads, (b) the dumbbell axis IS the local normal the bending term acts
on — no phantom orientation dynamics, and (c) the two leaflets are
literally measurable for the thickness oracle (head-bead shells).

Bead index convention: amph I has HEAD at bead 2I-1, TAIL at bead 2I
(affine indices — the bond/axis loops stay INJECTIVE).

### Force set (σ = 1, ε = 1, f64)

1. **Bond:** harmonic, E = K_B(r − r0)², K_B = 100, r0 = 0.5.
2. **Short-range pairs via the M0 cell list** (rebuilt every step,
   no skin, RC = 2.6 cell edge):
   - TAIL–TAIL: full LJ (attractive — the aggregation driver),
     force cutoff RC_TT = 2.6.
   - HEAD–HEAD: WCA (LJ repulsive branch only), σ_HH = 1.05,
     cutoff 2^(1/6)·σ_HH ≈ 1.179.
   - HEAD–TAIL: WCA, σ_HT = 0.95, cutoff 2^(1/6)·0.95 ≈ 1.067.
3. **Bending / orientation (local normals):** axis A_I =
   (r_head − r_tail)/|…| is the local normal. Amphiphile pairs with
   centers within R_B = 2.6 (second, amph-level cell list) carry
   E = −K_AL (A_I·A_J), K_AL = 1.5 → force on the axis
   F_d = K_AL/L_I [A_J − (A_I·A_J)A_I], applied +F_d to the head,
   −F_d to the tail. Aligning neighboring normals penalizes curvature
   → bending rigidity.
4. **Thermostat:** Langevin, damping γ = 0.5, deterministic uniform
   noise amplitude set by kT = 0.2 (RAND-seeded per step/bead).
5. **Equilibration protocol (added after the first smoke exploded —
   recorded honestly):** the dispersed gas has overlapping beads (pair
   forces ~1e5), which blew the first build apart (shell radius 2e11
   by step 100). Shipped protocol: pair-force magnitude capped at
   FCAP = 500 (mask form, in the force set and the mirror) and hot
   damping γ = 10 for the first 1500 steps, then γ = 0.5.
6. **Bonded-pair exclusion:** the head–tail WCA never acts within a
   dumbbell (NBR_BUILD skips the bonded partner: amph of bead b is
   (b+1)/2). Without it the WCA tore every bond (ebond ~ 6e3 — found
   in smoke, fixed, mirror updated, mirror still passes).

### Amendment 1 (pre-registered 2026-08-30, before any closing run)

**Gas-pocket start.** The box-wide dispersed gas (bead density 0.064)
nucleates clusters fast but they never coalesce: cluster–cluster
diffusion across L=36 at γ=0.5 needs ~1e5+ time units — not computable
at M1 scale (documented exploration: N=400/L=20 grid, 15k–30k steps:
KT=0.2/γ=0.5 aggregates but stays multi-cluster; KT=0.3/γ=0.2 and
KT=0.2/γ=0.2 both boil — the thermostat cannot remove collapse heat at
γ ≤ 0.2). Amended protocol, still a dispersed-gas start (no structure
is imposed): monomer centers uniform in a central cube of half-width
POCKET, sized for bead density ~0.3/σ³ (POCKET = 13.4 for N1 = 1500,
16.9 for N2 = 3000 — POCKET ∝ N^{1/3} so both O3 sizes see identical
gas density). This is the standard nucleation trick and changes no
force term. γ = 0.5, KT = 0.2 stay.

### Fixed run parameters

DT = 0.002, NSTEPS = 15000 (t = 30), dispersed-gas start (uniform
random centers, random axes, small random velocities).
N1 = 1500 amphs (3000 beads), L1 = 36; O3 second size N2 = 3000,
L2 = 36·2^(1/3) ≈ 45.36 (same gas density).

## Pre-registered oracle bands

### O1 closure (genus-0 ray cast)

162 Fibonacci-sphere directions from the bead centroid; each TAIL bead
assigned to its best-aligned direction and a radial bin (0.5σ). A
direction's radial profile must contain **exactly one contiguous
membrane band** (bins ≥ 25% of the per-direction peak count). PASS:
≥ 98% of directions single-band, AND shell-radius spread
R_std/R_mean < 15% (a hole shows as a zero-band or split-band
direction; a second cluster shows as two bands).

### O2 bilayer thickness band — derived from bead geometry

Head-shell radii R_out (outer leaflet head peak) and R_in (inner
leaflet head peak) from the radial HEAD-density profile; bilayer
thickness T = R_out − R_in.

Geometric estimate BEFORE running: per leaflet, head-center to
midplane ≈ bond projection r0 (0.5) + tail-bead effective radius
(0.5–1.0σ: LJ tail pack near 2^(1/6)σ ≈ 1.12 compresses toward the
midplane). So T ≈ 2×(0.5 + 0.5…1.0) = 2.0–3.0σ, plus head-bead
radius on each side already folded into the head-PEAK positions.

**Pre-registered band: T ∈ [2.0, 4.0] σ.** A monolayer/micelle gives
T ≈ 1.0–1.5 (fails low); an uncompressed globule gives T ≫ 4 (fails
high).

### O3 surface scaling

S = 4π R_shell², R_shell = (R_out + R_in)/2. PASS:
S(N2)/S(N1) ∈ (N2/N1)^(2/3) ± 12% = 2^(2/3) = 1.587 ± 0.19.
(Curvature and packing corrections make 5% unrealistic; 12% is the
pre-registered tolerance.)

### O4 edge energy → 0

Tail bead coordination z_i = number of TAIL neighbors within RC_TT.
Bulk bilayer tail: z ≈ 9–12; a free-edge tail: z ≤ 5. **Exposed = z < 6.**
Edge energy proxy E_edge = Σ_exposed (6 − z_i)·ε/2.
PASS: E_edge(final)/N < 0.05 ε AND E_edge(final) < 10% of its
nucleation-stage peak (a persistent free edge keeps it high).

### Negative control (pre-registered)

All beads TAIL-type (no heads, no bonds, no bending — pure LJ fluid):
must NOT form a bilayer. Falsifiable trip: the O2 head-peak analysis
finds no two-leaflet structure (T undefined / outside band) OR the O1
shell test fails (a droplet has T ~ R, directions still single-band —
so the deciding test is O2-class: no two head shells exist at all).
Control presence proof: build banner prints NHEAD=0, NTAIL=2N.
Prediction: a spherical DROPLET — O1 ray-cast may PASS (a droplet is
genus-0!) and that is NOT a failure of the control; the control's
bilayer-specific gate is the two-leaflet thickness measurement.

## Results

(to be filled after the runs — oracle table, mirror diff, closure
evidence, micelle-vs-vesicle notes)

## Reproduce

(to be filled)
