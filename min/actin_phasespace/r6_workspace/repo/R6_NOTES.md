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

## Amendment PADHF (registered in plan_adhesion.md §4.4, §5 per-step force records)

- `PARAMETER INTEGER :: PADHF = 0` added at the end of the R6 adhesion
  parameter block; default 0 is inert.
- `ADHESION_FORCE()`: after the spring force of an attached bond is
  computed, emits the WRITE-only record
  `adhf STEP F M force_x force_y force_z` (M=ADHM(F), %.6f, same
  precision as adha/adhr) when `PADHF=1 .AND. MIRROR=0`. The record draws
  no RNG and changes no state or force (ADHM(F) is read directly in the
  WRITE; AFX/AFY/AFZ are already-computed scratch). No dynamics,
  kinetics, RNG slots, adha/adhr/adhs records, or MIRROR/PADH=0 paths are
  touched (diff = 1 parameter line + 3 force-routine lines + comment).
- Rupture-step force stays in `adhr` only: ADHKIN runs before force
  assembly each step, so a bond ruptured at step S has no adhf at S;
  a bond attached at step S has its first adhf at S with fy=fz=0 (the
  target yz is frozen at the current bead position in the same step).

### Checks run for the amendment (short only; no gates/smokes)

Toolchain: /mnt/agents/output/actin_swarm/toolchain/ergo_mcl (python3 -m
core). All variants compiled cleanly. Test variants and logs in /tmp/adhf.

1. PADH=0 vs parent brush_bfm.ergo, NSTEPS=3000, direct cmp = 0 diffs on
   both gate arms; md5s identical to the XSEED-amendment certificates:
   - arm 1 (PBR=0, FORMIN=0, DIMERS=0): md5 5c44db5775412be7b6d5a06a6adf3a6c
   - arm 2 (PBR=1, FORMIN=1):           md5 ffb198c4b6efe5440b48aeeccb0160bf
2. PADH=1, PADHF=0, 20k-step unit geometry (XSEED=3.5, PBR=0, FORMIN=0,
   DIMERS=0, PSTN=1, F_EXT=1.0, seed 77031) vs the pre-amendment engine
   (/mnt/agents/output/actin_phasespace/phi4/brush_adh.ergo, same
   variant transform): cmp = 0 diffs, md5 2eeff360d2a5a2b0ca62cd5cef68467f.
3. PADH=1, PADHF=1, same 20k unit geometry: exit 0, FINAL/FINAL_E
   present; 33 adha / 32 adhr / 12908 adhf / 40 adhs. Parsed checks:
   - every adhf record has an open attached bond: exact 1:1 match with
     the adha/adhr step-resolved reconstruction (0 missing, 0 extra, no
     duplicates); one bond (F=1, M=260) open at FINAL;
   - no adhf at any rupture step (rupture force is in adhr, as designed);
   - all force components finite, max |component| = 5.314234
     (consistent with 2*KADH*d, d <= SMAXA=2.5);
   - all 33 attach-step records have fy=fz=0 exactly (A frozen at the
     bead yz in the same step), the component of 2*KADH*(A-R) checkable
     without per-step positions;
   - all 40 adhs traction windows satisfy
     |trx - sum(-adhf_fx)/NDIAG| <= 4.98e-07 (and likewise try, trz),
     i.e. exact to the %.6f output rounding of both records;
   - final adhs nadh=1 equals net adha-adhr.
4. MIRROR=1 PADH=0 dump byte-identical to parent MIRROR=1 dump:
   md5 ff405b7ee69d179acb3150c9f63cb8bd.
5. MIRROR=1 PADH=1 cert unchanged and analytically exact with the
   amendment: CERT_ADH eadh=28.423286162412776 == KADH*d*d bitwise
   (d=3.7698332962090495); FRC delta on bead 2 == 2*KADH*(A-R) bitwise;
   all other bead forces and the legacy CERT record unchanged.
6. MIRROR=1 PADH=1 PADHF=1 dump byte-identical to the PADHF=0 MIRROR
   dump: PADHF adds no adhf records (or any other change) in MIRROR mode.

Caveat: the 2*KADH*(A-R) identity per adhf record cannot be checked
component-wise without per-step bead positions; the checks above cover
the checkable components (attach-step yz = 0, magnitudes within the
spring range, exact window-sum closure against adhs). Short checks only;
the registered O-A1 300k gates and R6 smokes/ensembles are unchanged and
still to be run by their stages.
