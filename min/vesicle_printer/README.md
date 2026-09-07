# Vesicle Printer

A deterministic genome-driven vesicle printer written in **ergo** (compiled by
the Python `mcl` toolchain). It reads codon tapes one codon at a time, decodes
each codon into a monomer (species-A amphiphile, species-B amphiphile, or
membrane-protein inclusion), and places it on a blueprint site under a stiff
anchor spring. An optional shrink phase then marches the anchor sites inward
so the printed structure closes into a 3D shell; anchors release and the
structure evolves free. Geometry self-aligns — no curvature (Helfrich)
machinery anywhere.

Everything is mirror-first verified: a pure-Python mirror
(`printer_mirror.py`) reproduces the engine's static state byte-for-byte, and
every force gradient is finite-difference certified.

## Contents

| file | what it is |
|---|---|
| `vesicle_printer.ergo` | main engine, all four print modes (set `PRINTMODE`) |
| `vesicle_printer_shrink.ergo` | ready-built variant: mode 3, 64 monomers, 12000 steps |
| `vesicle_printer_stack.ergo` | ready-built variant: mode 4, 128 monomers, 14000 steps |
| `vesicle_printer_cert_{ring,patch,stack}.ergo` | `MIRROR=1` static-certification variants |
| `printer_mirror.py` | pure-Python mirror: FD checks, cert-oracle generation, independent dynamics |
| `PRINTER_SPEC.md` | full design/verification log with results per milestone |
| `cert_oracles/` | reference config/force dumps for the three static certs |

## Quick start

Requires the `mcl` compiler (the `core` package; ergo sources compile with
`python3 -m core file.ergo -o binary`) and Python 3 with NumPy for the mirror.

```bash
# build & run the default ring print (PRINTMODE=1, 64 monomers, 8000 steps)
python3 -m core vesicle_printer.ergo -o /tmp/vprt
/tmp/vprt > ring_run.log

# closure variants
python3 -m core vesicle_printer_shrink.ergo -o /tmp/vshrink && /tmp/vshrink > shrink.log
python3 -m core vesicle_printer_stack.ergo  -o /tmp/vstack  && /tmp/vstack  > stack.log

# static certification: engine dump vs mirror oracle (byte-level)
python3 -m core vesicle_printer_cert_ring.ergo -o /tmp/vcert && /tmp/vcert > cert_out.txt
grep '^CFG' cert_out.txt | awk '{print $2, $3, $4}' > /tmp/cfg.txt
diff /tmp/cfg.txt <(tail -n +2 cert_oracles/printer_cert_ring_config.txt)   # ~1e-15
grep '^FRC' cert_out.txt | awk '{print $2, $3, $4}' > /tmp/frc.txt
diff /tmp/frc.txt cert_oracles/printer_cert_ring_forces.txt                  # ~1e-12

# mirror: FD validation of the force gradients, oracle regeneration, dynamics
python3 printer_mirror.py                 # finite-difference check (ring + patch)
python3 printer_mirror.py --cert ring     # regenerate a cert oracle (ring|patch)
python3 printer_mirror.py --run stack 14000   # independent dynamic confirmation
```

Expected cert agreement (this package, x86-64): ring config 3.6e-15 / forces
7.3e-12; patch byte-exact / 7.1e-14; stack 3.6e-15 / 1.7e-12 (max abs diffs).
CERT energy lines match the mirror to 13–15 significant digits.

Typical wall clock (single thread): ring 8000 steps ≈ 0.4 s, shrink 12000 ≈
1.2 s, stack 14000 ≈ 4 s. The Python mirror runs ~500× slower — use it for
certs and one-off confirmations, not sweeps.

## Print modes

| `PRINTMODE` | blueprint | `NMONO` | schedule |
|---|---|---|---|
| 1 | single ring at z = cz, radius `RING_R` | 64 | print only |
| 2 | flat 12×12 bilayer patch, spacing `PATCH_SP`, leaflet offset `PATCH_Z` | 144 | print only |
| 3 | ring + shrink-ring closure | 64 | print → shrink → release |
| 4 | two-ring stack at z = cz ± `RING_HZ` + closure + cargo | 128 | print → shrink → release+seat |

Phases (steps): `NPRINT = NMONO·K_EMIT` print → `N_SHRINK` shrink (modes 3/4)
→ `NDECAY` anchor release → free evolution to `NSTEPS`.

## The decoder

One byte = one codon. Byte bases map A=0, T=1, G=2, C=3, so codon value

$$c = 16\,b_1 + 4\,b_2 + b_3$$

decodes as

- **pole** $p = \lfloor c/32 \rfloor$ — selects the leaflet (0 outer, 1 inner);
- **ring position** $r = c \bmod 32$, azimuth $\theta_c = 2\pi r/32$;
- **wobble** (the siphon coordinate from `predict_organism --siphon`):

$$w(c) = \pm\tfrac{1}{3}\sin(5\,\theta_c),\quad + \text{for pole 0},\ - \text{for pole 1}$$

applied as an azimuthal jitter `WOB = WW·w(c)` with `WW = 0.02` rad. The
per-tape siphon sums are acpA −0.018, sepF +0.038, crr +0.016; weighted by the
emission program below the printed structure nets **+0.079** (pumps positive —
the uploads' viability criterion).

The emission program `PROG = [0,0,1,0,1,0,0,1,0,2]` cycles per decade:
5 codons from tape A (`acpA`, 73 codons, species A), 4 from tape B (`sepF`,
138, species B), 1 from tape T (`crr`, 154, inclusion). Tapes loop. Each
emission advances the print head one blueprint site regardless of monomer
type.

## Emission geometry

Ring/stack sites $k$ sit at azimuth $\Theta_k = 2\pi k/64 + \mathrm{WOB}$.
Species and pole set the bead radius and sign $s = \pm1$ (pole 0 → +1):

$$R_s = R_{ring} - p,\qquad r_{head} = c + (R_s + s\,h_0)\,\hat e_r,\qquad r_{tail} = c + (R_s - s\,h_0)\,\hat e_r$$

with $h_0 = R_0/2$ (half the bond rest length), $c = (L_{box}/2, L_{box}/2)$,
z at the ring plane (mode 4: $z = c_z \pm$ `RING_HZ`, emission alternating
between the two rings, $k \bmod 2$). Patch mode places sites on a square grid
with leaflet offset `PATCH_Z` in z instead.

Every bead records its **site bookkeeping** `(STH, SROFF, SZ0)` = azimuth,
radial offset from `RING_R`, plane z; inclusions record `(ISTH, ISROFF, ISZ0)`.
This is what the shrink march uses. Mode-4 inclusions print in an outward
docking pose at $z = c_z \pm(\texttt{RING\_HZ} + \texttt{ZI})$
(`ZI = 0.7`) — same-plane printing puts them inside the tail LJ core of the
belt (capped forces, FD-invalid) — but their march target `ISZ0` is the ring
plane, so the first march step slides them into the belt.

## Force field

Beads: odd index = head, even = tail. Unit masses, ε = 1, tail σ = 1.

**Pair forces** (directed neighbor list, cell-edge 2.769 ≥ RC; per-pair
weights exactly one of $w_{TT}, w_{HH}, w_{HT} \in \{0,1\}$ by parity).
Magnitude $f$ along $\Delta \mathbf r$, applied to bead $i$:

$$f = \frac{24\left(2 b_{TT}^{12} - b_{TT}^{6}\right) + 24\left(2 b_{H}^{12} - b_{H}^{6}\right)}{d^{2}}$$

- tail–tail: full Lennard-Jones, $b_{TT} = \sigma/d$, active for $d < R_{CTT} = 2.6$ → $U_{TT} = 4[(\sigma/d)^{12} - (\sigma/d)^6]$ (the hydrophobic attraction);
- head–head / head–tail: WCA, $b_H = \sigma_{ij}/d$ active for $d < 2^{1/6}\sigma_{ij}$, with the arithmetic comb $\sigma_{ij} = \tfrac12(\sigma_i + \sigma_j)$ and head–tail shifted down by `HTSHIFT = 0.10`; head σ is per-species (`HSA = 1.05`, `HSB = 0.95`).

Forces are capped: $|f|\,d \le$ `FCAP = 500`, and pairs with $d < 10^{-12}$
are skipped (guard band; certification counts TT iff $10^{-12} \le d < R_{CTT}$).

**Bond** (per amphiphile, head–tail axis $\mathbf a$, rest length `R0A = 0.5`
/ `R0B = 0.45`):

$$U_{bond} = K_B(d - R_0)^2,\qquad \mathbf F = -2 K_B (d - R_0)\,\hat{\mathbf a},\quad K_B = 100$$

**Bending / nematic alignment** (`BENDMODE = 1`): amphiphile centroids within
`RB = 2.6` of each other couple their axes. With $q = \mathbf a_i \cdot
\mathbf a_j$,

$$U_{bend} = -K_{AL}\, q^2,\qquad \mathbf S_i = \sum_j 2q\,(\mathbf a_j - q\,\mathbf a_i),\qquad \mathbf F_{head} \mathrel{+}= K_{AL}\,\mathbf S_i / L_i,\ \ \mathbf F_{tail} \mathrel{-}= K_{AL}\,\mathbf S_i / L_i$$

$K_{AL} = 1.5$, $L_i$ = bond length. This is the self-alignment term that
lets the geometry close without curvature machinery.

**Inclusions** (membrane proteins): inclusion–inclusion WCA (σ = 1.5),
inclusion–head WCA (σ = 1.3), inclusion–tail full LJ to `RCINC = 2.6`
(σ = 1.3) — the hydrophobic belt that seats cargo in the shell.

**Anchors**: harmonic springs to the print site,

$$U_{anch} = K_{AC}\,|\mathbf a_i - \mathbf r_i|^2,\qquad \mathbf F = 2K_{AC}(\mathbf a_i - \mathbf r_i),\quad K_{AC} = 50$$

beads gated by `HASA`, inclusions on the separate `IAC` schedule.

**Walls**: soft harmonic box, pen depth from face at `XWALL = 0.5`,
$U = K_W\,(\text{pen})^2$, $K_W = 100$.

**Integrator**: Langevin velocity-Verlet, Δt = 0.002, deterministic
hash-seeded noise (same seed ⇒ same trajectory, bit-for-bit):

$$\mathbf v \leftarrow \mathbf v\,(1 - \gamma\Delta t) + \mathbf F\,\Delta t + \eta,\qquad \mathbf r \leftarrow \mathbf r + \mathbf v\,\Delta t$$

with $\eta = \sqrt{12\,kT\left[1 - (1-\gamma\Delta t)^2\right]}\,(U - \tfrac12)$,
$kT = 0.2$, $\gamma = 10$ while the printer is active (step ≤ `NPRINT2`),
$\gamma = 0.5$ in free evolution.

## Schedules (closure machinery)

Anchor stiffness is piecewise linear. With $t_P =$ `NPRINT`, $t_S =$
`NPRINT + N_SHRINK`:

$$K_{AC}(t) = \begin{cases} 50 & t \le t_S \\ 50\left(1 - \dfrac{t - t_S}{N_{DECAY}}\right) & t_S < t \le t_S + N_{DECAY} \\ 0 & \text{after} \end{cases}$$

Inclusions use the same shape but release over `N_SEAT = 500` instead of
`NDECAY = 3000` (**dock-after-closure**: cargo rides the rail at full
strength through the shrink — releasing it early abandons it on the rail,
the rings march inward faster than the IT attraction can drag it).

During the shrink phase the site radius marches linearly,

$$R(t) = R_{ring} + \left(R_{end} - R_{ring}\right)\frac{t - t_P}{N_{shrink}},\qquad R_{end} = 3.0$$

and `MARCH_ANCHORS` recomputes each anchor from the bookkeeping:
$\mathbf a = c + (R(t) + \mathrm{SROFF})(\cos\mathrm{STH}, \sin\mathrm{STH})$,
$z = \mathrm{SZ0}$. Buckling into 3D is left to the physics — the z target
stays on the site's plane.

## Output lines

| prefix | meaning |
|---|---|
| `# VESICLE_PRINTER …` | run header (mode, NMONO, cadence, KANC, KT) |
| `PRT k inc j cod c pole p` | emission k placed inclusion j from codon c |
| `step … kt epair ebond ebend nexp eedge rshell nact ninc maxnb ovf nout fmax kanc` | DIAG every `NDIAG` steps. `nexp` = tails with coordination < 6 (shell-quality metric), `rshell` = mean tail radius rel centroid, `nout` = beads outside the box, `fmax` = max force magnitude |
| `MIRROR_DUMP / CFG / FRC / CERT` | static-cert dump (`MIRROR=1`): positions, forces, energy decomposition at full print |
| `FINAL / FINAL_E` | end-of-run morphology: `rmean/rstd/rmin/rmax`, `zstd` (tail z-spread — the 3D-closure metric), physical energies |
| `FPOS type idx x y z` | final positions (type 1 head, 0 tail, 2 inclusion) for radial-distribution analysis |

Convention note: DIAG's `epair/ebend` come from the directed neighbor list
and are **2× physical** (each ordered pair counted per endpoint); `CERT` and
`FINAL_E` single-count and are the physical energies.

## Verification workflow (mirror-first)

1. **FD check** — `python3 printer_mirror.py` perturbs each coordinate and
   compares analytic forces to central differences (max_rel ≈ 2e-6 on the
   stack blueprint after the ZI docking fix).
2. **Static cert** — build any `vesicle_printer_cert_*.ergo`, diff `CFG`/`FRC`
   rows against `cert_oracles/` (expect ≤1e-11) and check the `CERT` energy
   line matches 13–15 digits.
3. **Dynamic cross-check** — `python3 printer_mirror.py --run <mode> <steps>`
   and compare `closure:` metrics statistically against the engine's `FINAL`
   (trajectories diverge chaotically; compare distributions, not trajectories).
   Reference: engine stack `rmean 3.106 rstd 0.845 zstd 1.391 nexp 1`, mirror
   `rmean 2.957 rstd 0.725 zstd 1.332 nexp 0`.

## Known limits

Closed structures so far are caps trending spherical (zstd: patch 0.48,
1-ring 0.75, 2-ring stack 1.39), not full spheres — next rungs are taller
stacks or a latitude blueprint with the same machinery. `nexp` is
shell-calibrated (a bare ring reads all-exposed by design). See
`PRINTER_SPEC.md` §10 for the full list and §9 for the staged
decoder-enrichment hooks (promoter→cadence, class-fractions→PROG,
`predict_delta` fitness oracle).
