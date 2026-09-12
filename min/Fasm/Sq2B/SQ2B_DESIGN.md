# SQ2B — biologically-revised Squaragon v2 cell

2026-08-27. Applies what the ribosome / transcription / cell campaigns
taught to the V22 DNA cell. Every biological mechanism is a concrete
structure with a measurable oracle; nothing is decorative.
Files: `squaragon_v2_bio.h` (the cell), `bench_sq2b.c` (comparison row),
`sq2b_cert.c` (certification driver).

## 1. Biology → mechanism mapping

| biology | V22 had | SQ2B has |
|---|---|---|
| duplex complementarity | two identical shells, compared wholesale | shell 1 stores the **base-complement** (2-bit pairing ⇒ byte ⊕ 0x55). Mismatch = per-byte localization with zero arithmetic |
| strand-directed mismatch repair (MutS/MutH) | shell 0 assumed golden | per-strand **self-syndrome**; on mismatch, the strand whose own syndrome fails is the damaged one — structural arbitration |
| excision repair (NER) | byte/gate patch copy | damaged codon **resynthesized wholesale** from the intact strand |
| kinetic proofreading (ribosome, Hopfield) | none — write and hope | two-stage commit: write duplex, **re-read and verify**, then mark occupied; one retry (GTP bill), else the alloc is refused |
| hemimethylation | none | shell 0 = methylated template, shell 1 = nascent; clean sweeps age the codon; both-pass conflicts resolve to the elder |
| apoptosis | none — corruption could only propagate | both strands damaged ⇒ `0xDEAD5EED` tombstone, loudly counted |
| transcription asymmetry | reads hit the archive | `sqb_transcribe` decodes a disposable RNA working copy; integrity burden stays on the duplex archive |

## 2. What this buys (measured, not claimed)

- **Multi-byte single-strand damage is fully repairable.** The
  complement strand arbitrates, so any damage confined to one strand of
  a codon — one byte or fifty — resynthesizes exactly. Under the 12
  events/round poisson tail, repair is **98.3%** vs SQ5's moment scheme
  at 89.5% on the same protocol. Detection stays 100% in both regimes.
- **Per-byte localization for free.** V22 could say "this gate is bad";
  SQ2B's duplex mask says *which bytes* disagree, before any syndrome
  is consulted.
- **Check-field corruption self-heals.** A syndrome-field hit makes one
  strand fail its own check; the sweep resynthesizes it from the clean
  strand — syndrome included. (O3/O4: 300/300.)
- **Failure is loud.** Double-strand hits tombstone; 48 apoptoses in
  the poisson phase, every one counted as a loss, none propagated
  (coh_fail equals tomb count exactly — no silent corruption anywhere).

## 3. Certification (pre-registered oracles, byte-deterministic runs)

```
SQ2BOR O1_payload_det   900/900  = 1.000000  counting [A]     PASS
SQ2BOR O2_payload_rep   900/900  = 1.000000  measurement [A]  PASS
SQ2BOR O3_syndrome_det  300/300  = 1.000000  counting [A]     PASS
SQ2BOR O4_syndrome_rep  300/300  = 1.000000  measurement [A]  PASS
SQ2BOR O5_closure       0 unresolved [A]                      PASS
SQ2BOR O6_apoptosis     0 [A] isolated                        PASS
SQ2BOR O7_blind_random  2000/2000 detected+tombstoned         PASS
SQ2BOR O8_blind_crafted 2000/2000 blind    documented-exclusion
SQ2BOR auxB_det         5647/5647 = 1.000000 poisson tail
SQ2BOR auxB_rep         5551/5647 = 0.983000 poisson tail
SQ2BOR auxB_tombs       48  auxB_coh_fail 48  auxB_slippage 0  auxB_unresolved 0
```

## 4. The blind spot, mapped (same discipline as the Wigner exclusions)

A coordinated hit on the **same byte of both strands with the same
mask** keeps the duplex consistent (s1⊕m = (v⊕m)⊕0x55) — but both
stored syndromes then disagree, so a *random* coordinated hit is always
detected and apoptosed, never silent (O7: 2000/2000). True blindness
requires additionally repairing both syndrome words to match the
corrupted content — a **6-target coordinated attack needing content
knowledge** (O8: constructively demonstrated 2000/2000 blind). That is
the documented exclusion boundary: SQ2B is robust to accidents, not to
an adversary who can read the codon. Same status as SQ5's moment
collisions, but the attack is strictly harder to stage (six consistent
targets vs four).

## 5. The energy bill (honest costs)

| mechanism | cost | measured |
|---|---|---|
| kinetic proofreading | one fused re-read pass per alloc | alloc **336 ns/item vs V22's 121** (~2.8×); proofread retries in the bench threat model: **0** — corruption arrives post-alloc, so the GTP bill buys nothing *here*. It earns its keep only if writes themselves can fail (cosmic-ray-on-write, marginal hardware). Honest negative. |
| duplex storage | 2× payload memory (same as V22's two shells — free vs status quo) | 168 B/codon vs V22's 152 B gate |
| G2 sweep | per-codon syndrome recompute, scalar | ~70 µs per full-cell sweep (256 codons); SIMD-able if it ever lands on a hot path |
| apoptosis | capacity loss under heavy damage | 48/256 codons tombstoned at 12 events/round — the price of never propagating |

## 6. What is NOT biological (yet)

- No recombination/crossover (V22 had `sq2_strand_recombine`; SQ2B
  dropped it — it never had an integrity function, and un-scored
  mechanisms are how canaries hide).
- No division cycle / threshold lifecycle (G1/S/G2/M exists as the
  alloc → inject → sweep phases of the harness, not as cell state).
- Mutation *rate* is not coupled to age (senescence); age is an
  informational methylation clock only.
- The 2-bit "base" is a byte-level fiction (⊕ 0x55); a true 4-symbol
  encoding would halve payload density for no integrity gain — rejected.

## 7. Verdict

SQ2B is the integrity-optimal design in the family: strongest
arbitration (per-byte, strand-directed), strongest multi-error repair
(short of cryptography), loud failure. It pays ~2.8× V22's alloc cost
for proofreading that this threat model never exercises, and ~70 µs
sweeps. If the workload is store-and-sweep (archive cells, checkpoints)
it is the right cell; if the workload is alloc-hot (SQ4's regime), SQ4's
3 ns metadata-only path remains the right one, and SQ5 stays the
middle point. The comparison table now shows all three regimes
explicitly.
