# Literature Scoping for the Rotor-Chain Critical Phase Paper

**Date:** 2026-07-25
**Purpose:** Position the findings of `min/FINDINGS.md` against the
published literature *before* submission. Verdict first, then per-thread
detail with citations.

---

## Verdict (one paragraph)

The **universality class is canonical** (c=1 Luttinger liquids in 1D
rotor/XY-type chains are the textbook example), and the **model family is
well-studied** (quantum phase/rotor models, chiral/twisted XY chains with
commensurability, floating phases, Pokrovsky–Talapov and BKT transition
taxonomy). What appears **unclaimed**: (1) the *specific* model — a rotor
chain with a helical on-site field and a two-harmonic competition whose
first harmonic cancels at an exactly computable drive ratio (B = 0.25) —
and the full c=1 characterization *on that exact line*; (2) the
classical↔quantum balance-point coincidence as a phenomenological bridge;
(3) the DMRG false-discovery case study. Recommended framing:
**characterization of an exactly-pinned competition line in a known
universality class**, plus a methods note — *not* "a new phase of
matter." Venue: PRB or SciPost Physics. PRX is a stretch for one model;
the methods note may have the broader reach.

---

## Thread 1: The universality class — canonical, cite and move on

c=1 Luttinger liquids, gap ∝ 1/N, Calabrese–Cardy entanglement scaling —
all standard since the 2000s.

- T. Giamarchi, *Quantum Physics in One Dimension* (Oxford) — the
  standard text. His lecture notes already treat the commensurability
  cosine competition directly:
  [Giamarchi lucca_08 lecture notes](https://giamarchi.unige.ch/wp-content/php_code/people/thierry.giamarchi/pdf/lucca_08.pdf),
  [Harvard mini-lectures](https://giamarchi.unige.ch/wp-content/php_code/people/thierry.giamarchi/Harvard%20mini-lectures/slides_2012.pdf)
- P. Calabrese & J. Cardy, J. Stat. Mech. P06002 (2004) — the
  entanglement-scaling formula we fit. Canonical; no novelty claim.

**Implication for the paper:** the *detection methodology* (gap scaling +
CC fits) is standard practice. Present it as such — reviewers will
recognize it and it builds trust.

## Thread 2: The model family — well-studied landscape, new point in it

Our chain (rotors, p²/2I + cosine on-site terms + cosine bonds) is a
member of the **quantum phase model** family — the paradigmatic model for
superconductor–insulator transitions in Josephson junction arrays:

- [Review: dissipative phase transitions / quantum phase model as
  paradigmatic rotor model](https://inis.iaea.org/records/55bk9-6gt11/files/52119443.pdf?download=1)
- [QPT in JJ arrays, duality approach (arXiv:0706.0324)](https://arxiv.org/pdf/0706.0324)

The gauge-transformed form of our model (uniform on-site field + twisted
bonds with twist 2π/N) is a **chiral/twisted XY-type chain**, whose
literature includes *floating phases* — critical Luttinger-liquid regions
with incommensurate correlations bounded by Pokrovsky–Talapov and
Kosterlitz–Thouless transitions:

- V. L. Pokrovsky & A. L. Talapov, Phys. Rev. Lett. 42, 65 (1979) —
  the commensurate–incommensurate transition canon.
- [From Kosterlitz–Thouless to Pokrovsky–Talapov transitions
  (arXiv:2209.10390)](https://ar5iv.labs.arxiv.org/html/2209.10390) —
  LL stability, KT vs PT taxonomy.
- [Floating phase with incommensurate correlations
  (arXiv:2206.11754)](https://arxiv.org/pdf/2206.11754) — KT and PT
  boundaries of a critical LL region; close structural cousin of our
  phase diagram.
- [Commensurate–incommensurate Mott transition, nematic LL in XXZ chain
  (arXiv:2510.05988)](https://arxiv.org/html/2510.05988v2) — recent
  example of two PT transitions bounding an LL region.

**Implication:** the *landscape* (LL region between transition lines in a
twisted/commensurate chain) exists in the literature. Our model's
*specific* combination — helical on-site field + two-harmonic drive with
exact cancellation at B = K_PHASE/K_BIAS — did not surface in searches
("quantum rotor chain helical rotating onsite field" returns nothing
directly on point). **The exact algebraic pinning of the competition line
appears unclaimed** — but phrase it as "to our knowledge" after one more
targeted check (suggested: search "quantum Frenkel-Kontorova",
"commensurate subharmonic competition rotor", "two-frequency cosine
lattice rotor chain").

## Thread 3: The classical↔quantum bridge — thin literature, frame carefully

Searches for established correspondences between classical driven-
dissipative oscillator competition and quantum critical points returned
generic driven-dissipative literature, not this mapping. The bridge
(classical coherence crash ↔ quantum critical line at the *same algebraic
balance point*) appears unclaimed as an explicit correspondence.

**Critical caveat for framing:** the two systems are linked by algebra
(same harmonic-cancellation point) and phenomenology (competition,
w-accumulation, fluctuation collapse), *not* by any theorem. The
classical model is dissipative first-order dynamics; the quantum model is
a T=0 Hamiltonian ground state. Frame as **"a structural correspondence
with an exactly shared balance point"** — never as a mapping or a
classical limit. A referee will attack anything stronger.

Related established fields to cite for context (not as precedents of the
bridge): Kuramoto-model transitions; dissipative phase transitions in
Josephson chains ([review](https://inis.iaea.org/records/55bk9-6gt11/files/52119443.pdf?download=1)).

## Thread 4: DMRG convergence failures — known problem, fresh case study

DMRG local-minimum trapping is documented in the literature:

- White's mixer work and the one-site vs two-site comparison; subspace
  expansion as the modern fix:
  [A Strictly Single-Site DMRG Algorithm with Subspace Expansion
  (arXiv:1501.05504)](https://arxiv.org/pdf/1501.05504)
- Incomplete convergence producing wrong physics (Xiang example):
  [cond-mat/0110420](https://arxiv.org/pdf/cond-mat/0110420)

**So the methods paper cannot claim "we discovered DMRG can fail."** What
is genuinely new in our case study (`min/spin_swap/`):

1. A failure that produced a **published physical claim** with a
   structured, compelling false pattern (N mod 4 switching at machine
   precision) — the danger is not noise but *discovery-shaped* noise.
2. The specific mechanism: symmetry-sector attractor at J/h ≫ 1, with
   the entire observable carried by the missing 0.005% of the state
   (energy error 1.4e-5 relative; overlap 99.995%).
3. The falsifiable diagnosis: the h=0 control reproduces the signature
   exactly; the energy referee catches it.

Framing: "a documented failure mode with a worked false-discovery example
and the energy-referee protocol that detects it." Cite the mixer /
subspace-expansion literature as the known general problem; our
contribution is the case study and protocol.

---

## External confirmation (2026-07-25)

Two independent AI-assisted literature searches (Deepseek:
`min/deepseek_literature_search.md`; assistant:
`min/LITERATURE_SEARCH_RESULTS.md`) ran the FK-chain, two-frequency
cosine, and twisted-XY/floating-phase queries. Both returned null on the
exact two-harmonic competition with algebraic cancellation, converging
with this document's verdict. Additional useful citations from those
searches:

- Braun & Kivshar, Phys. Rep. 306, 1 (1998) — foundational FK review.
- arXiv:1405.2901, 1405.2902 — quantum FK with DMRG.
- arXiv:2606.16128 — c=1 LL with BKT boundaries in Rydberg chains.
- A 1984 PRB paper on harmonic expansions in incommensurate dielectric
  phase transitions shares the *harmonic-cancellation motif* (as a
  phenomenological expansion, not an exact cancellation in a quantum
  Hamiltonian). Recommended one-sentence acknowledgment in the intro:
  > "We note in passing that the harmonic cancellation motif has
  > appeared in the commensurate phase transition literature [1984 PRB],
  > but in that context it is a phenomenological expansion, not an exact
  > algebraic cancellation in a quantum rotor Hamiltonian."

**Residual due-diligence note:** all searches (ours and theirs) are
web-search based. Before submission, run one formal database pass
(Web of Science / Scopus / Google Scholar with citation chaining from
arXiv:2206.11754 and arXiv:2510.05988) — or leave it to the referees,
who will run it anyway. The claim is scoped to survive either outcome:
worst case, the paper becomes "clean characterization in a model with an
exactly-pinned competition line," which is still publishable.

---

## Remaining checks before submission

1. Targeted searches: "quantum Frenkel-Kontorova chain", "commensurate
   subharmonic potential rotor chain", "two-frequency cosine lattice",
   "twisted clock chain floating phase" — to close the "to our knowledge"
   claim on the exact competition line.
2. Verify the PT-vs-BKT boundary question against the floating-phase
   literature (arXiv:2206.11754): our boundary at J_c ≈ 1.0–1.1 is where
   the extrapolated gap vanishes; the floating-phase papers show how to
   distinguish PT (z=1, q-locking) from KT boundaries via correlation
   wave-vector measurements — a concrete next measurement if the paper
   needs it.
3. Decide framing per target venue:
   - **PRB/SciPost:** characterization of the exactly-pinned line + c=1
     phase; methods note as appendix.
   - **PRX (ambitious):** only if led by the DMRG false-discovery /
     referee-protocol result with the phase diagram as the worked example.
