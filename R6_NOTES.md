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
