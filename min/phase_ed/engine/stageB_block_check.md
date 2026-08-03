# Stage B block: correct complex-state entanglement — validation report

Program: `stageB_block.ergo` (generator `gen_ergo_stageB_block.py`).
Method: entanglement entropy from the 2n×2n real-symmetric block
[[G, −K], [K, G]] with G = A_r A_rᵀ + A_i A_iᵀ (symmetric part of
ρ = A A^H) and K = A_i A_rᵀ − A_r A_iᵀ (antisymmetric part). The block's
spectrum is each eigenvalue of the complex Hermitian ρ, exactly doubled;
entropy uses half weight. Cyclic round-robin Jacobi on the block,
eigenvalues-only, insertion sort on the diagonal.

## (a) Doubled-spectrum verification (Python replica)

- n=5 random complex A: max |eig(block) − doubled eig(ρ)| = 7.1e-15.
- Ground-state cuts at (B=0.1, J=2.0), l = 1, 2, 3: max deviation
  7.8e-16, 4.4e-16, 4.4e-16. Sign convention K = A_i A_rᵀ − A_r A_iᵀ
  with B[:n,n:] = −K, B[n:,:n] = K confirmed correct.

## (b) Off-line validation, (B=0.1, J=2.0), cuts l=1..3

| l | Ergo block S | Python true S (SVD of A) | delta |
|---|---|---|---|
| 1 | 0.730050 | 0.730026 | 2.4e-5 |
| 2 | 0.944405 | 0.944375 | 3.0e-5 |
| 3 | 1.052326 | 1.052292 | 3.4e-5 |

**CC-fit c = 0.9639 — EXACTLY the Python 3-cut fit (0.9639)** and within
±0.05 of the 6-cut target 0.9537. PASS. (The 3-cut and 6-cut fits differ
by fit window, not physics; both quoted.)

## (c) On-line invariance, (B=0.25, J=1.0)

K = 0 for the real-up-to-phase line state → block spectrum = doubled G
spectrum, entropy unchanged: S(l) = [0.880772, 1.112147, 1.226433] —
EXACT match to Python `entropy_cc` at all three cuts. CC = 1.0347,
exactly Python's 3-cut fit at the line (1.0347); the full 6-cut value
1.0161 stands from the previous stage. PASS.

## Task 2 — rotation update audit (Deepseek's note)

The rotation in `stageB_block.ergo` (and `stageB_jacobi.ergo`) is
ALREADY the textbook 4-vector form — no matrix multiply anywhere. Per
rotation, two loops of length M2 each (columns P, Q), then two loops of
length M2 each (rows P, Q), at stageB_block.ergo lines 262–273 (columns)
and 274–279 (rows): 4 vector updates of length n per rotation, O(n). No
change needed. Per-sweep cost at 729×729 (from the earlier
stageB_jacobi run): the l=6 cut costs ~15–20 s for 12 sweeps ≈ 1.5 s
per sweep — consistent with M³ = 3.9e8 ops/sweep at ~0.4 GFLOP/s single
thread. The 81×81 numpy gate stands at 1.9e-11 relative (previous run);
the block program's line-point S values reproduce it end-to-end.

## Bug saga (worth recording)

The production run surfaced a three-layer bug chain, each found by
isolating a smaller repro:
1. **Insertion-sort corruption**: the early-exit branch (`ELSE: Q0 := 0`)
   destroyed the write position for no-swap cases, overwriting BMAT(1,1)
   and duplicating large eigenvalues (isolated with `sort_test.ergo`,
   reproduced exactly: input [0.1715,0.657,0.1715,0.1715,0.657,0.1715]
   → output [0.1715, 0.657×5]).
2. **Flag-version infinite loop**: the first fix (DONE flag) never
   decremented Q0 after the flag was set.
3. **POS pattern** (final): track insertion position POS explicitly;
   natural exit → POS = 1, flag exit → POS = Q0+1. Verified in
   isolation, then applied everywhere. The Jacobi itself (build,
   schedule, rotations) was correct from the start — the corruption was
   entirely in the post-processing sort.

## Files

`gen_ergo_stageB_block.py`, `stageB_block.ergo`, `stageB_block` (binary),
`stageB_block.out`, `sort_test.ergo` (sort repro), this file.
