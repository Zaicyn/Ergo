# R6 adhesion engine — implementation notes (brush_adh.ergo)

Parent: brush_bfm.ergo (copied verbatim, then PADH channel added).
Spec: SPEC.md / plan_adhesion.md (registered 2026-09-02).

## Implementation map

- Parameters: PADH(=0 default), XADH=2.0, RADH=0.75, KADH=2.0, KONA=2.0,
  KOFFA=0.02, FBA=1.0, SMAXA=2.5 (PARAMETER block after formin channel).
- State: ADHM/ADHB/ADHBORN/ADHX/ADHY/ADHZ per filament slot (MAXF+2),
  zeroed in the main init loop.
- RNG: hash slots 4600+2*(F-1) attachment, 4601+2*(F-1) rupture, drawn
  once per active filament per step inside ADHKIN (called from KINETICS
  only when PADH=1). No draws exist when PADH=0.
- Attachment: pointed-end tail bead B=2*FILPNT(F), eligible if
  PX(B) <= XADH+RADH; target A=(XADH, PY(B), PZ(B)) frozen at attach.
  Bond tracks the monomer (ADHM) — shaft grip after pointed growth.
- Force: ADHESION_FORCE, called after WALLS (before PISTON) in both the
  dynamic loop and the MIRROR path, only when PADH=1. F=2*KADH*(A-R_B)
  on bead ADHB(F); substrate traction accumulated as -F per step.
- Rupture: hard release d>SMAXA (cause 2) else slip
  P=KOFFA*DT*EXP(|F|/FBA) (cause 1); monomer unbind at barbed/pointed
  end (cause 3, inline before release relocation); filament death in
  DISSOLVE (cause 4). All via ADH_REL (writes adhr, clears state).
- Birth/slot-reuse clearing: branch birth (F3), DIMKIN promotion (F2),
  DISSOLVE slot reset; init loop zeroes all slots.
- Records (WRITE-only, only when PADH=1): adha (attach), adhr (rupture,
  cause 1/2/3/4), adhs (NDIAG window: nadh, mean traction trx/try/trz,
  mean |F| over attached-bond samples, attach/rupture rates per step).
- MIRROR cert: INIT_CERT with PADH=1 constructs a loaded adhesion on
  filament 1 pointed tail bead (bead 2) with A=(XADH, y2, z2) post-jitter
  (purely x-directed d). CERT_ENERGY adds EP_ADH=KADH*d*d; DUMP_MIRROR
  adds additive ADHC + CERT_ADH records. Existing CERT record unchanged.

## Checks run (compile-level / short sanity only; no gates/smokes)

Toolchain: /mnt/agents/output/actin_swarm/toolchain/ergo_mcl (python3 -m core).

1. PADH=0 bit-identity vs parent, NSTEPS=3000 variants, 0 diffs:
   - default (PBR=1, FORMIN=0, DIMERS=1, PSTN=1)
   - gate arm 1: PBR=0, FORMIN=0, DIMERS=0
   - gate arm 2: PBR=1, FORMIN=1
2. MIRROR=1 PADH=0 dump bit-identical to parent MIRROR=1 dump.
3. MIRROR=1 PADH=1: CERT_ADH == KADH*d*d to 1e-15; FRC delta on bead 2
   == 2*KADH*(A-R) exactly; all other bead forces unchanged.
4. PADH=1 100k-step default-arm run: exit 0; 131 adha / 130 adhr
   (causes: 117 slip, 12 unbind, 1 death); adhs nadh == adha-adhr event
   reconstruction at all 200 censuses; nbound+nfree+2*ndim=400 at all
   censuses; FINAL records present; all adha targets x=2.0.

Caveat: hard-stretch (cause 2) did not occur in the 100k sanity (slip
dominates at SMAXA=2.5); path is compiled and shares ADH_REL. Test
variants and logs live in /tmp, not in the repo. The two `**` occurrences
are inherited parent code (compiles cleanly); all new code uses explicit
products.

## Amendment XSEED (registered in plan_adhesion.md §4.4, R6-b)

- `PARAMETER REAL :: XSEED = 6.0` added in the adhesion parameter block;
  default is exactly the parent dynamic seed center `LBOX/2` (LBOX=12.0).
- `INIT_DYN()` only: `CX0 := XSEED` replaces `CX0 := LBOX * 0.5`.
  INIT_CERT/MIRROR geometry, free-gas seeding slab, and all
  kinetic/force/RNG code are untouched (diff = 2 lines).

### Checks run for the amendment (short only; no gates/smokes)

Toolchain: /mnt/agents/output/actin_swarm/toolchain/ergo_mcl (python3 -m
core). All variants compiled cleanly, including the verbatim source.

1. PADH=0, XSEED=6.0 (default) vs parent brush_bfm.ergo, NSTEPS=3000,
   direct cmp = 0 diffs on both gate arms:
   - arm 1 (PBR=0, FORMIN=0, DIMERS=0): md5 5c44db5775412be7b6d5a06a6adf3a6c
   - arm 2 (PBR=1, FORMIN=1):           md5 ffb198c4b6efe5440b48aeeccb0160bf
2. MIRROR=1 PADH=0 dump byte-identical to parent MIRROR=1 dump:
   md5 ff405b7ee69d179acb3150c9f63cb8bd.
3. MIRROR=1 PADH=1 cert: CERT_ADH eadh=28.423286162412776 == KADH*d*d
   exactly (d=3.7698332962090495 from ADHC target and CFG bead 2); FRC
   delta on bead 2 == 2*KADH*(A-R) bitwise; all other bead forces and the
   full CFG byte-identical to the PADH=0 dump.
4. PADH=1 unit-geometry sanity, 20k steps, XSEED=3.5, PADH=1, PBR=0,
   FORMIN=0, DIMERS=0, PSTN=1, F_EXT=1.0, seed 77031:
   - initial pointed tail bead (bead 2) at x=2.650000 as designed
     (verified via /tmp-only diagnostic variant);
   - 33 adha / 32 adhr events; every adha target x=2.000000;
   - log completes (step 20000 DIAG, FINAL, FINAL_E present, exit 0);
   - nbound+nfree+2*ndim=400 at all 40 censuses; final adhs nadh=1
     equals net adha-adhr.

Caveat (unit sanity): the first adha is bead 34 (monomer 17), not the
initial bead 2. Root cause traced with the diagnostic variant: pointed
polymerization replaced the pointed tail monomer at step 185 before an
attachment draw fired; fired draws at steps 227 and 298 were correctly
rejected by the eligibility gate because the tail bead had drifted out of
the capture slab (x=2.770, 2.930 > XADH+RADH=2.75); first eligible fired
draw attaches at step 438. Geometry and gate behavior are as registered;
the outcome is the deterministic seed-77031 kinetics of the certified
parent pointed-growth channel, which the XSEED amendment must not change.
Diagnostic variants and logs live in /tmp, not in the repo.
