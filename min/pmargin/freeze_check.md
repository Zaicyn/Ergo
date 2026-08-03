# Freeze-then-dock — post-fold rigidification for placement

Programs: `min/pmargin/gen_freeze.py` → `freeze_sim_x{3,5,10}.ergo`
(+binaries/.out). Base: `dock_sim.ergo` (deployable fold-then-dock,
sim folds; ×1 gate = `dock_sim.out`, reproduces: best 9.34 / mean 12.46).
Design (documented in the generator): RES_ANGK, RES_TORSK, BACKBONE_D
multiplied × M at program start (= docking-phase start — the run IS the
docking phase; no stabilization trigger needed); angle/torsion
multipliers skip the ±3 interface windows (linkers live);
interface/cross-domain terms (contacts, tether, interface registers)
unchanged.

Hypothesis under test (orient_check.md mechanism): the field satisfies
interface restraints by BENDING compliant domains instead of ROTATING
them; rigidification removes the bending channel so interface forces
must express as net translation/rotation.

## Multiplier-response curve (8 blocks, mean)

| M | best full | mean full | internal | placement |
|---|---|---|---|---|
| ×1 (gate) | 9.34 | 12.46 | 2.97 | 12.08 |
| ×3 | 8.95 | 11.90 | 2.81 | 11.55 |
| ×5 | 8.82 | 11.83 | 2.73 | 11.49 |
| ×10 | **8.69** | **11.75** | **2.65** | **11.43** |

Per-domain COM error / rotation (best block): ×3: 7.2/30°, 11.3/37°,
3.4/26°, 7.4/29° — ×10: 6.4/34°, 11.1/33°, 3.3/32°, 7.4/28° (vs ×1
baseline 7.9/33°, 11.8/31°, 3.5/25°, 7.3/27° from orient_errmode).
Domain integrity (best block, per-domain RMSD): B1 3.51→2.10→2.03
(×3→×10), B2 1.52→1.38→1.18 — **rigidification preserves the folds
~30–40% better** (the field-vs-crystal mismatch is locked less
deformed), the one clear benefit.

## Verdict

**(a) Does placement collapse? NO.** A monotone but small, saturating
gain: placement 12.08 → 11.43 (−5%) from ×1 to ×10; best full 9.34 →
8.69. Nowhere near < 3.

**(b) Failure mode: ENGAGED-BUT-INEFFECTIVE — the bending-absorption
mechanism was real but minor.** Rigidification demonstrably engages
(domains hold their folds better at every multiplier — internal RMSD
2.97→2.65, B1 3.51→2.03) yet rigid domains still dock wrong (A3 COM
error ~11 and rotation ~35° at ×10, essentially unchanged). The
diagnosed compliance channel absorbs only ~5% of the placement error;
the remaining ~95% is set independently of domain softness. Combined
with the earlier findings (cold ≡ hot → deformation is force-driven;
crystal relaxes 0→2.5–3.5 with zero heat), the consistent picture is:
**the field's own assembly minimum is wrong** — interface forces DO
express as translation/rotation when bending is removed, and they still
drive to the same wrong arrangement, because that arrangement is what
the field prefers. The next step this maps to is **field rebalancing**
(the frustration between the field's domain terms and its assembly
preference), not rigid-frame projection — projection cannot help when
the projected target itself is the wrong assembly.

Secondary result worth keeping: ×3–5 rigidification is a defensible
protocol addition for fold QUALITY (preserves input folds ~30–40%
better at no cost to anything else), even though it does not fix
placement. ×10 gives no meaningful extra rigidity benefit over ×5.

## Arc status (deterministic options exhausted)

contacts → short dihedrals → long dihedrals → cold schedule → early
activation → rigidification: all tie or move ≤5%. The placement error
is the force-field ceiling expressed at assembly level. Remaining
levers: (a) field rebalancing (the frustration itself); (b) rigid-body
Monte-Carlo domain moves (user's last resort — all deterministic
alternatives are now eliminated); (c) accept fold-then-dock (+freeze
for fold quality) as the current protocol ceiling: best ~8.7–9.1 vs
all-at-once 13.2.

Files: `gen_freeze.py`, `freeze_sim_x{3,5,10}.ergo` (+binaries, `.out`s),
this report.
