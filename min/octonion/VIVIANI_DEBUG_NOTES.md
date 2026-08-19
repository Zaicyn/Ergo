# Viviani 4D ED — repair notes (viviani_4d_ed_fixed6.ergo)

Date: 2026-08-15. Repair performed in place on
`min/octonion/viviani_4d_ed_fixed6.ergo`; earlier versions untouched
(historical record). Reference: an independent numpy dense-ED of the
intended Hamiltonian (dim 4096, `eigvalsh`/`eigh`), which reproduced
all four mirror oracles to print precision before the Ergo file was
changed — the model identification below is therefore evidence-based,
not assumed.

## Mirror oracles vs repaired output

| quantity | mirror oracle | repaired Ergo | status |
|---|---|---|---|
| EA | −764.041145458466 | −764.041145458471 | ✓ (~5e-12) |
| MA | +2.57866371114e-2 | +2.57866371140e-2 | ✓ (~4e-15) |
| EB | −763.885720819343 | −763.885720819343 | ✓ (all printed digits) |
| MB | +3.469e-18 | −8.753e-18 | ✓ (< 1e-12, f64 floor) |

Determinism: two consecutive runs byte-identical (`cmp` clean).

## The bug chain (final, with evidence)

### B1 — ISHFT direction (root bug)
Ergo's ISHFT follows Fortran: positive shift = LEFT. Every site read
`IAND(ISHFT(S-1,I-1),1)` therefore tested bit 0 (site 1) for all I —
the field, bond, and diagnostic loops all saw the same bit. Fixed to
`IAND(ISHFT(S-1,1-I),1)` (right shift brings site I to bit 0). The
mask builds `ISHFT(1,I-1)` were already correct and are unchanged.
Sites: z-field loop, single-site loop, bond BI/BJ reads, case-B
diagnostic, M-observable loop.

### B2 — "single-site geometry-dressed coupling" ran at bond strength
The block is the transverse part of the *field* (the n·S coupling's
NX,NY pieces) but was coded with the bond strength `-JJ/2` per spin
flip — at J=200 that is ~−1840 of phantom binding across 12 sites:
this, and only this, produced the fixed6 numbers EA=−2601.87,
EB=−2589.49 — the "3.4× energies". **The "3.4× = lithium" hypothesis
was a bug rationalization: with the block at its correct field
strength (−HH/2, vanishing at h=0), the configuration gives the
expected XX-chain energy scale (−764), not a 3.4× anomaly.** The
transverse phase signs were also wrong vs the mirror convention
(amp = −h/2·(NX − i·NY) for an up spin, −h/2·(NX + i·NY) for down);
both corrected.

### B3 — case-A start vector was an exact eigenvector
s=0 (all spins down) is annihilated by every flip-flop bond and is
diagonal under the field — an exact eigenvector, so Lanczos broke down
at IT=1 (β=0) and printed degenerate output (EA≈0, MA=nan). Both
cases now start from the Néel state s=2730 (Sz=0 sector), which has
full bond support in both cases.

### B4 — cyclic Jacobi never formed the sine (the below-ground producer)
The sweep computed `t` and `C = 1/√(1+t²)` but rotated with `TT`
(= tan θ) where `sin θ = t·c` belongs: the "rotation" [[C,−t],[t,C]]
is not orthogonal (norm² = C²+t² ≠ 1), so the tridiagonal solve
returned non-similarity "eigenvalues" — with B1–B3 patched this
printed EA=−2805, EB=−3140, *below the true ground state*, which a
correct Lanczos+similarity chain can never do. Fixed: `SJ := TT*C`
used in all three update loops (A columns, A rows, V).

**Cleared suspect:** the fiber-twist block (`dq = qmul(q2,conj(q1))`,
`CHI = 2·ACOS(Q0)`) was suspected during the hunt (a BETA = J·√3
reading at IT=1 was misread as implying CC=±1 everywhere). It is
correct as written: uniform CC = −5/8, SS = √39/8, and a numpy
reference ED with exactly those values reproduces EB to all printed
digits. The misleading diagnostic was an artifact of B1 (all sites
read bit 0, so the *effective* model being measured was not the
intended one).

### B5 — the 0.02% case-A gap was the texture, not the z-field sign
The file built the first Hopf-map quaternion product as
R = (−Q1, Q0, Q2, Q3); the standard scalar-first qmul(q,i) is
(−Q1, Q0, Q3, −Q2). The wrong components gave a period-3 NZ texture
[−0.577, 0.788, −0.211]×4 vs the mirror's [−1, 0.5, 0.5]×4. At h=0
this is invisible (field off — EB matched even with the wrong
texture); at h=1 the second-order field shift is texture-sensitive,
which was the entire 0.02% gap. The up/down z-field sign convention
hypothesis was tested explicitly: both conventions are
spectral-identical for this model (global spin flip × translation
symmetry, Σ NZ = 0), so the convention question is moot for EA — the
Ergo file's z-sign choice matches the mirror and is kept. **The
mirror's case A also couples the field through the full n·S (z plus
transverse), not the z-component alone** — reflected in B2 and in the
M-observable, which now applies the full dot-product action (the
JJ=0, HH=1/N reuse with the existing negation is then exactly
⟨m·n⟩ = (1/N)Σ n_i·S_i).

## Verification protocol used

1. numpy dense ED of the intended model reproduced mirror EA/EB/MA/MB
   to print precision *before* any Ergo edits (model identification).
2. The identification sweep tested: twist conventions (file formula
   vs fiber-phase vs none — file formula exact), texture variants
   (standard qmul exact), field forms (z-only vs full n·S, ×1/2 — full
   n·S at h/2 exact).
3. Repaired Ergo program: oracle table above; two runs byte-identical.
