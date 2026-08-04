C     SQUARAGON V4 CORE - F77 PORT
C     ==============================
C     Torus allocator + LUTs + gate operations.
C     All state in COMMON blocks. Zero dynamic allocation.
C
C     Torus geometry: 2 shells x 8 bins x 32 ring = 512 slots
C     Gate: 12 cuboctahedral vertices (3 floats each)
C
C     V4 CHANGES (from the tuning audit, allocator/TUNING_FINDINGS.md):
C     V4-1: SCATLT rebaked from sq2_viviani_scatter_full(id, 52) at
C           HOPFQ=1.97. The v2/v3 bake (total=32) used only bins
C           {0,2,3,4,6,7}; bins 1,5 were dead, capping occupancy at
C           384 = THRESHOLD_BIAS and leaving OVERDRIVE/DIVIDE
C           unreachable. The new LUT uses all 8 bins
C           (histogram 5,2,4,5,7,3,4,2 per 32 IDs). Tradeoff: worst-case
C           adjacent-ID torus separation 2.819 -> 1.688 (the generator
C           family's ceiling under 8-bin coverage); mean separation
C           improves 11.73 -> 12.63. See allocator/v4_check.py.
C     V4-2: TINVAR widened REAL -> INTEGER with the exact v3 bit-pack
C           (geo<<24 | bin<<16 | seam<<9 | shell<<8 | gen), replacing
C           the lossy REAL pack and the 0.01*TBITS float fudge. Bit-
C           exact cross-port with tests/sq4core.ergo. The slow path
C           (SQ4ALC) keeps its REAL*8 gate fold but stores it truncated
C           to INTEGER -- marked lossy; use SQ4FAL for exact invariants.
C     V4-3: SQ4RES added -- 3-axis corruption residual. The v2 triple-
C           XOR residual is exactly 3*|z-centroid|/scale: blind to any
C           in-plane (x/y) perturbation, which is 2/3 of the imprint
C           channel. SQ4RES applies the (I+R120+R240) symmetrization
C           about all three Cartesian axes and takes the max.
C           Detection floor: any single-vertex perturbation d gives
C           response >= sqrt(3)*|d|/scale (since max_a |d.a| >= |d|/sqrt3,
C           and per-axis response = 3*|d.a|/scale). Unperturbed gate
C           gives exactly 0 (vertices pair as exact +/-; fl sign
C           symmetry makes the paired sums cancel bit-exactly).
C     V4-4: SQ4REP writes the shell-2 TINVAR pack (v2 left it stale).
C
C     COMMON /SQ4CON/ - compile-time constants
C     COMMON /SQ4LUT/ - precomputed LUTs (zero trig hot path)
C     COMMON /SQ4TOR/ - torus state (the allocator)
C     COMMON /SQ4SED/ - seed vertices (unit cuboctahedron)
C
      BLOCK DATA SQ4BLK
      IMPLICIT NONE
C
C     --- Constants ---
      REAL PHI, SCLRAT, BIAS, ISQR2, HOPFQ, SEMSTR
      INTEGER NVTX, NEDGE, NFACE, NBINS, NSHEL, NRING
      INTEGER NUNIQ, NSLOT, THBIAS, THWORK, THMAX
      INTEGER NDMOD, SEMBIT
      COMMON /SQ4CON/ PHI, SCLRAT, BIAS, ISQR2, HOPFQ, SEMSTR,
     &                 NVTX, NEDGE, NFACE, NBINS, NSHEL, NRING,
     &                 NUNIQ, NSLOT, THBIAS, THWORK, THMAX,
     &                 NDMOD, SEMBIT
      DATA PHI   /1.6180339887498948/
      DATA SCLRAT/1.6875/
      DATA BIAS  /0.75/
      DATA ISQR2 /0.7071067811865475/
      DATA HOPFQ /1.97/
      DATA SEMSTR/0.03/
      DATA NVTX/12/, NEDGE/24/, NFACE/14/
      DATA NBINS/8/, NSHEL/2/, NRING/32/
      DATA NUNIQ/31/, NSLOT/512/
      DATA THBIAS/384/, THWORK/432/, THMAX/496/
      DATA NDMOD/8/, SEMBIT/2/
C     Audit verdicts (TUNING_FINDINGS.md): SCLRAT inert in the alloc
C     path (only SQ4SCL uses it, and nothing calls SQ4SCL); BIAS inert
C     (only multiplies the identically-zero residual); HOPFQ load-
C     bearing via SCATLT generation, measured worst-case optimum;
C     SEMSTR inert in the +-20% band (round(64*s)=2 throughout).
C
C     --- Precomputed LUTs ---
C     BIN_GEO: Viviani geo encoding per bin (8 entries)
C     FLOWW:   flow w-component per ring position (32 entries)
C     FLOWM:   flow mode per ring position (32 entries, 0/1/2)
C     SOLTON:  soliton window mask (32 entries, 0/1)
C     SCATLT:  Viviani scatter LUT (32 entries) -- V4-1, see header
      INTEGER BINGEO(8), FLOWM(32), SOLTON(32), SCATLT(32)
      REAL    FLOWW(32)
      COMMON /SQ4LUT/ BINGEO, FLOWW, FLOWM, SOLTON, SCATLT
C
      DATA BINGEO /228, 104, 0, 104, 228, 104, 0, 104/
C
      DATA FLOWW /
     &  0.000000,  0.263371,  0.231222,  0.227317,
     &  0.340459,  0.163085, -0.216041, -0.319410,
     & -0.259259, -0.319410, -0.216041,  0.163086,
     &  0.340459,  0.227318,  0.231222,  0.263371,
     & -0.000000, -0.263371, -0.231222, -0.227317,
     & -0.340459, -0.163085,  0.216041,  0.319410,
     &  0.259259,  0.319410,  0.216041, -0.163086,
     & -0.340459, -0.227317, -0.231222, -0.263371/
C
      DATA FLOWM /
     &  0, 1, 1, 1, 2, 0, 0, 2, 1, 2, 0, 0, 2, 1, 1, 1,
     &  0, 1, 1, 1, 2, 0, 0, 2, 1, 2, 0, 0, 2, 1, 1, 1/
C
      DATA SOLTON /
     &  0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0,
     &  0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0/
C
C     V4-1: 8-bin scatter LUT. sq2_viviani_scatter_full(id, 52),
C     HOPFQ=1.97, float32 bake. Best worst-case separation among
C     8-bin candidates (family ceiling 1.6875); most balanced of the
C     HOPFQ=1.97 ceiling candidates (histogram 5,2,4,5,7,3,4,2).
      DATA SCATLT /
     &  6, 5, 4, 0, 2, 3, 4, 7, 4, 6, 3, 0, 1, 2, 1, 0,
     &  3, 6, 4, 7, 4, 3, 2, 0, 4, 5, 6, 5, 4, 0, 2, 3/
C
C     --- Seed vertices: unit cuboctahedron ---
C     SEED(3,12): xyz for each of 12 vertices
      REAL SEED(3,12)
      COMMON /SQ4SED/ SEED
C     XY plane (z=0)
      DATA SEED(1,1) / 0.7071067811865475/
      DATA SEED(2,1) / 0.7071067811865475/
      DATA SEED(3,1) / 0.0/
      DATA SEED(1,2) / 0.7071067811865475/
      DATA SEED(2,2) /-0.7071067811865475/
      DATA SEED(3,2) / 0.0/
      DATA SEED(1,3) /-0.7071067811865475/
      DATA SEED(2,3) / 0.7071067811865475/
      DATA SEED(3,3) / 0.0/
      DATA SEED(1,4) /-0.7071067811865475/
      DATA SEED(2,4) /-0.7071067811865475/
      DATA SEED(3,4) / 0.0/
C     XZ plane (y=0)
      DATA SEED(1,5) / 0.7071067811865475/
      DATA SEED(2,5) / 0.0/
      DATA SEED(3,5) / 0.7071067811865475/
      DATA SEED(1,6) / 0.7071067811865475/
      DATA SEED(2,6) / 0.0/
      DATA SEED(3,6) /-0.7071067811865475/
      DATA SEED(1,7) /-0.7071067811865475/
      DATA SEED(2,7) / 0.0/
      DATA SEED(3,7) / 0.7071067811865475/
      DATA SEED(1,8) /-0.7071067811865475/
      DATA SEED(2,8) / 0.0/
      DATA SEED(3,8) /-0.7071067811865475/
C     YZ plane (x=0)
      DATA SEED(1,9)  / 0.0/
      DATA SEED(2,9)  / 0.7071067811865475/
      DATA SEED(3,9)  / 0.7071067811865475/
      DATA SEED(1,10) / 0.0/
      DATA SEED(2,10) / 0.7071067811865475/
      DATA SEED(3,10) /-0.7071067811865475/
      DATA SEED(1,11) / 0.0/
      DATA SEED(2,11) /-0.7071067811865475/
      DATA SEED(3,11) / 0.7071067811865475/
      DATA SEED(1,12) / 0.0/
      DATA SEED(2,12) /-0.7071067811865475/
      DATA SEED(3,12) /-0.7071067811865475/
C
C     --- Torus state ---
C     GATES(3,12,32,8,2): vertex data [xyz, vtx, gen, bin, shell]
C     TINVAR(32,8,2):      invariant per slot (V4-2: INTEGER bit-pack)
C     TOCC(32,8,2):        occupied flag
C     TFROZ(32,8,2):       frozen (period-4) flag
C     TWHEAD(8,2):         write head per strand
C     TLEN(8,2):           occupied count per strand
C     TALLOC(8,2):         total alloc count per strand
C     TTOTAL:              total occupied across all strands
C     TPHASE:              cell cycle phase (0=G1,1=S,2=G2,3=M)
C     TGEN:                cell generation (division count)
      REAL    GATES(3,12,32,8,2)
      INTEGER TINVAR(32,8,2)
      INTEGER TOCC(32,8,2), TFROZ(32,8,2)
      INTEGER TWHEAD(8,2), TLEN(8,2), TALLOC(8,2)
      INTEGER TTOTAL, TPHASE, TGEN
      COMMON /SQ4TOR/ GATES, TINVAR, TOCC, TFROZ,
     &                 TWHEAD, TLEN, TALLOC,
     &                 TTOTAL, TPHASE, TGEN
C
      END
C
C     ================================================================
C     SUBROUTINE SQ4INI - Initialize gate vertices at given scale
C     ================================================================
C
      SUBROUTINE SQ4INI(VTX, SCALE)
      IMPLICIT NONE
      REAL VTX(3,12), SCALE
      REAL SEED(3,12)
      COMMON /SQ4SED/ SEED
      INTEGER I
C
      DO 10 I = 1, 12
        VTX(1,I) = SEED(1,I) * SCALE
        VTX(2,I) = SEED(2,I) * SCALE
        VTX(3,I) = SEED(3,I) * SCALE
   10 CONTINUE
      RETURN
      END
C
C     ================================================================
C     SUBROUTINE SQ4SCL - Scale gate by 27/16 (coherent stack)
C     ================================================================
C
      SUBROUTINE SQ4SCL(VTX, SCALE)
      IMPLICIT NONE
      REAL VTX(3,12), SCALE
      SCALE = SCALE * 1.6875
      CALL SQ4INI(VTX, SCALE)
      RETURN
      END
C
C     ================================================================
C     SUBROUTINE SQ4SPH - Scale gate by phi (spillover hop)
C     ================================================================
C
      SUBROUTINE SQ4SPH(VTX, SCALE)
      IMPLICIT NONE
      REAL VTX(3,12), SCALE
      SCALE = SCALE * 1.6180339887498948
      CALL SQ4INI(VTX, SCALE)
      RETURN
      END
C
C     ================================================================
C     FUNCTION SQ4FLD - Gate XOR fold (vertex data, returns hash)
C     ================================================================
C
      REAL*8 FUNCTION SQ4FLD(VTX)
      IMPLICIT NONE
      REAL VTX(3,12)
      INTEGER I, J
      REAL*8 FOLD, CHUNK
      REAL FBUF(2)
      REAL*8 DBUF
      EQUIVALENCE (FBUF, DBUF)
C
      FOLD = 0.0D0
      DO 20 I = 1, 12
        DO 10 J = 1, 3, 2
          FBUF(1) = VTX(J,I)
          IF (J+1 .LE. 3) THEN
            FBUF(2) = VTX(J+1,I)
          ELSE
            FBUF(2) = 0.0
          END IF
          CALL SQ4XOR(FOLD, DBUF, FOLD)
   10   CONTINUE
   20 CONTINUE
      SQ4FLD = FOLD
      RETURN
      END
C
C     ================================================================
C     SUBROUTINE SQ4XOR - XOR two REAL*8 values via integer bits
C     ================================================================
C
      SUBROUTINE SQ4XOR(A, B, C)
      IMPLICIT NONE
      REAL*8 A, B, C
      REAL*8 LA, LB
      INTEGER*4 IA(2), IB(2), IC(2)
      EQUIVALENCE (IA, LA)
      EQUIVALENCE (IB, LB)
      LA = A
      LB = B
      IC(1) = IEOR(IA(1), IB(1))
      IC(2) = IEOR(IA(2), IB(2))
      CALL SQ4CP8(IC, C)
      RETURN
      END
C
C     ================================================================
C     SUBROUTINE SQ4CP8 - Copy 8 bytes (INTEGER*4 pair to REAL*8)
C     ================================================================
C
      SUBROUTINE SQ4CP8(ISRC, DDST)
      IMPLICIT NONE
      INTEGER*4 ISRC(2)
      REAL*8 DDST
      INTEGER*4 ITMP(2)
      REAL*8 DTMP
      EQUIVALENCE (ITMP, DTMP)
      ITMP(1) = ISRC(1)
      ITMP(2) = ISRC(2)
      DDST = DTMP
      RETURN
      END
C
C     ================================================================
C     SUBROUTINE SQ4TIN - Initialize torus (all slots empty)
C     ================================================================
C
      SUBROUTINE SQ4TIN
      IMPLICIT NONE
      REAL    GATES(3,12,32,8,2)
      INTEGER TINVAR(32,8,2)
      INTEGER TOCC(32,8,2), TFROZ(32,8,2)
      INTEGER TWHEAD(8,2), TLEN(8,2), TALLOC(8,2)
      INTEGER TTOTAL, TPHASE, TGEN
      COMMON /SQ4TOR/ GATES, TINVAR, TOCC, TFROZ,
     &                 TWHEAD, TLEN, TALLOC,
     &                 TTOTAL, TPHASE, TGEN
      INTEGER I, J, K
C
      DO 30 K = 1, 2
        DO 20 J = 1, 8
          TWHEAD(J,K) = 1
          TLEN(J,K) = 0
          TALLOC(J,K) = 0
          DO 10 I = 1, 32
            TOCC(I,J,K) = 0
            TFROZ(I,J,K) = 0
            TINVAR(I,J,K) = 0
   10     CONTINUE
   20   CONTINUE
   30 CONTINUE
      TTOTAL = 0
      TPHASE = 0
      TGEN = 0
      RETURN
      END
C
C     ================================================================
C     FUNCTION SQ4SCT - Viviani scatter (LUT, O(1))
C     ================================================================
C     Returns bin index 1-8 for a given ID
C
      INTEGER FUNCTION SQ4SCT(ID)
      IMPLICIT NONE
      INTEGER ID
      INTEGER BINGEO(8), FLOWM(32), SOLTON(32), SCATLT(32)
      REAL    FLOWW(32)
      COMMON /SQ4LUT/ BINGEO, FLOWW, FLOWM, SOLTON, SCATLT
C
      SQ4SCT = SCATLT(MOD(ID-1, 32) + 1) + 1
      RETURN
      END
C
C     ================================================================
C     SUBROUTINE SQ4ALC - Allocate: scatter to bin, write codon
C     ================================================================
C     ID    = allocation ID (1-based)
C     TOTAL = total allocations expected
C     DSEED = data seed for perturbation
C     IERR  = 0 on success, -1 on full
C
      SUBROUTINE SQ4ALC(ID, TOTAL, DSEED, IERR)
      IMPLICIT NONE
      INTEGER ID, TOTAL, IERR
      REAL DSEED
C
      REAL    GATES(3,12,32,8,2)
      INTEGER TINVAR(32,8,2)
      INTEGER TOCC(32,8,2), TFROZ(32,8,2)
      INTEGER TWHEAD(8,2), TLEN(8,2), TALLOC(8,2)
      INTEGER TTOTAL, TPHASE, TGEN
      COMMON /SQ4TOR/ GATES, TINVAR, TOCC, TFROZ,
     &                 TWHEAD, TLEN, TALLOC,
     &                 TTOTAL, TPHASE, TGEN
C
      REAL PHI, SCLRAT, BIASV, ISQR2, HOPFQ, SEMSTR
      INTEGER NVTX, NEDGE, NFACE, NBINS, NSHEL, NRING
      INTEGER NUNIQ, NSLOT, THBIAS, THWORK, THMAX
      INTEGER NDMOD, SEMBIT
      COMMON /SQ4CON/ PHI, SCLRAT, BIASV, ISQR2, HOPFQ, SEMSTR,
     &                 NVTX, NEDGE, NFACE, NBINS, NSHEL, NRING,
     &                 NUNIQ, NSLOT, THBIAS, THWORK, THMAX,
     &                 NDMOD, SEMBIT
C
      INTEGER SQ4SCT
      REAL*8  SQ4FLD
      INTEGER BIN, GEN, VIDX, SHELL
      REAL    SCALE, VTX(3,12)
      REAL*8  INV
C
      IERR = 0
      SHELL = 1
      BIN = SQ4SCT(ID)
      GEN = TWHEAD(BIN, SHELL)
C
      IF (GEN .GT. 32) THEN
        IERR = -1
        RETURN
      END IF
C
C     Initialize gate at shell scale
      SCALE = 1.0
      CALL SQ4INI(VTX, SCALE)
C
C     Imprint data: perturb vertices
      VIDX = MOD(GEN-1, 12) + 1
      VTX(1, VIDX) = VTX(1, VIDX) + 0.001 * DSEED
      VIDX = MOD(GEN+3, 12) + 1
      VTX(2, VIDX) = VTX(2, VIDX) + 0.0005 * DSEED * REAL(GEN)
      VIDX = MOD(GEN+7, 12) + 1
      VTX(3, VIDX) = VTX(3, VIDX) - 0.0003 * REAL(GEN)
C
C     Store gate vertices
      CALL SQ4SGT(VTX, GEN, BIN, SHELL)
C
C     Invariant (V4-2 note: REAL*8 fold truncated to INTEGER -- lossy,
C     kept for slow-path continuity; SQ4FAL stores the exact bit-pack)
      INV = SQ4FLD(VTX)
      TINVAR(GEN, BIN, SHELL) = INT(INV)
C
C     Mark occupied, check period-4
      TOCC(GEN, BIN, SHELL) = 1
      TALLOC(BIN, SHELL) = TALLOC(BIN, SHELL) + 1
      IF (MOD(TALLOC(BIN, SHELL), 4) .EQ. 0) THEN
        TFROZ(GEN, BIN, SHELL) = 1
      ELSE
        TFROZ(GEN, BIN, SHELL) = 0
      END IF
C
      TWHEAD(BIN, SHELL) = GEN + 1
      TLEN(BIN, SHELL) = TLEN(BIN, SHELL) + 1
      TTOTAL = TTOTAL + 1
C
      RETURN
      END
C
C     ================================================================
C     SUBROUTINE SQ4FAL - FAST allocate (LUT-only, no gate write)
C     ================================================================
C     V4-2: exact integer bit-pack invariant (same layout as v3 Ergo):
C       geo<<24 | bin<<16 | seam<<9 | shell<<8 | gen
C
      SUBROUTINE SQ4FAL(ID, IERR)
      IMPLICIT NONE
      INTEGER ID, IERR
C
      REAL    GATES(3,12,32,8,2)
      INTEGER TINVAR(32,8,2)
      INTEGER TOCC(32,8,2), TFROZ(32,8,2)
      INTEGER TWHEAD(8,2), TLEN(8,2), TALLOC(8,2)
      INTEGER TTOTAL, TPHASE, TGEN
      COMMON /SQ4TOR/ GATES, TINVAR, TOCC, TFROZ,
     &                 TWHEAD, TLEN, TALLOC,
     &                 TTOTAL, TPHASE, TGEN
C
      INTEGER BINGEO(8), FLOWM(32), SOLTON(32), SCATLT(32)
      REAL    FLOWW(32)
      COMMON /SQ4LUT/ BINGEO, FLOWW, FLOWM, SOLTON, SCATLT
C
      INTEGER SQ4SCT
      INTEGER BIN, GEN, SHELL, POS
      INTEGER IGEO, IBIN, ISHEL
      INTEGER TBITS
      INTEGER RINV
C
      IERR = 0
      SHELL = 1
      BIN = SQ4SCT(ID)
      GEN = TWHEAD(BIN, SHELL)
C
      IF (GEN .GT. 32) THEN
        IERR = -1
        RETURN
      END IF
C
      POS = MOD(GEN-1, 32) + 1
      IGEO = BINGEO(BIN)
      IBIN = BIN - 1
      ISHEL = SHELL - 1
      TBITS = IAND(ISHFT(GEN - 1, 1), 31)
C
      RINV = ISHFT(IGEO, 24) + ISHFT(IBIN, 16)
     &     + ISHFT(TBITS, 9) + ISHFT(ISHEL, 8) + (GEN - 1)
C
      TINVAR(GEN, BIN, SHELL) = RINV
C
C     Mark occupied, period-4
      TOCC(GEN, BIN, SHELL) = 1
      TALLOC(BIN, SHELL) = TALLOC(BIN, SHELL) + 1
      IF (MOD(TALLOC(BIN, SHELL), 4) .EQ. 0) THEN
        TFROZ(GEN, BIN, SHELL) = 1
      ELSE
        TFROZ(GEN, BIN, SHELL) = 0
      END IF
C
      TWHEAD(BIN, SHELL) = GEN + 1
      TLEN(BIN, SHELL) = TLEN(BIN, SHELL) + 1
      TTOTAL = TTOTAL + 1
C
      RETURN
      END
C
C     ================================================================
C     SUBROUTINE SQ4SGT - Store gate vertices into torus
C     ================================================================
C
      SUBROUTINE SQ4SGT(VTX, GEN, BIN, SHELL)
      IMPLICIT NONE
      REAL VTX(3,12)
      INTEGER GEN, BIN, SHELL
      REAL    GATES(3,12,32,8,2)
      INTEGER TINVAR(32,8,2)
      INTEGER TOCC(32,8,2), TFROZ(32,8,2)
      INTEGER TWHEAD(8,2), TLEN(8,2), TALLOC(8,2)
      INTEGER TTOTAL, TPHASE, TGEN
      COMMON /SQ4TOR/ GATES, TINVAR, TOCC, TFROZ,
     &                 TWHEAD, TLEN, TALLOC,
     &                 TTOTAL, TPHASE, TGEN
      INTEGER I, J
C
      DO 10 I = 1, 12
        GATES(1, I, GEN, BIN, SHELL) = VTX(1, I)
        GATES(2, I, GEN, BIN, SHELL) = VTX(2, I)
        GATES(3, I, GEN, BIN, SHELL) = VTX(3, I)
   10 CONTINUE
      RETURN
      END
C
C     ================================================================
C     SUBROUTINE SQ4REP - Replicate shell 1 to shell 2 (S phase)
C     ================================================================
C     V4-4: also writes the shell-2 TINVAR bit-pack (v2 left it stale).
C
      SUBROUTINE SQ4REP(NCOPY)
      IMPLICIT NONE
      INTEGER NCOPY
      REAL    GATES(3,12,32,8,2)
      INTEGER TINVAR(32,8,2)
      INTEGER TOCC(32,8,2), TFROZ(32,8,2)
      INTEGER TWHEAD(8,2), TLEN(8,2), TALLOC(8,2)
      INTEGER TTOTAL, TPHASE, TGEN
      COMMON /SQ4TOR/ GATES, TINVAR, TOCC, TFROZ,
     &                 TWHEAD, TLEN, TALLOC,
     &                 TTOTAL, TPHASE, TGEN
      INTEGER BINGEO(8), FLOWM(32), SOLTON(32), SCATLT(32)
      REAL    FLOWW(32)
      COMMON /SQ4LUT/ BINGEO, FLOWW, FLOWM, SOLTON, SCATLT
      INTEGER I, J, K
      INTEGER IGEO, IBIN, TBITS
C
      NCOPY = 0
      TPHASE = 1
C
      DO 30 J = 1, 8
        DO 20 I = 1, 32
          IF (TOCC(I, J, 1) .EQ. 0) GOTO 20
C         Copy gate data
          DO 10 K = 1, 12
            GATES(1, K, I, J, 2) = GATES(1, K, I, J, 1)
            GATES(2, K, I, J, 2) = GATES(2, K, I, J, 1)
            GATES(3, K, I, J, 2) = GATES(3, K, I, J, 1)
   10     CONTINUE
C         V4-4: shell-2 invariant bit-pack
          IGEO = BINGEO(J)
          IBIN = J - 1
          TBITS = IAND(ISHFT(I - 1, 1), 31)
          TINVAR(I, J, 2) = ISHFT(IGEO, 24) + ISHFT(IBIN, 16)
     &                    + ISHFT(TBITS, 9) + ISHFT(1, 8) + (I - 1)
          TOCC(I, J, 2) = 1
          TFROZ(I, J, 2) = 0
          TLEN(J, 2) = TLEN(J, 2) + 1
          TTOTAL = TTOTAL + 1
          NCOPY = NCOPY + 1
   20   CONTINUE
        TWHEAD(J, 2) = TWHEAD(J, 1)
   30 CONTINUE
C
      TPHASE = 2
      RETURN
      END
C
C     ================================================================
C     SUBROUTINE SQ4VFY - Verify shell 1 vs shell 2 (G2 phase)
C     ================================================================
C
      SUBROUTINE SQ4VFY(NMIS)
      IMPLICIT NONE
      INTEGER NMIS
      REAL    GATES(3,12,32,8,2)
      INTEGER TINVAR(32,8,2)
      INTEGER TOCC(32,8,2), TFROZ(32,8,2)
      INTEGER TWHEAD(8,2), TLEN(8,2), TALLOC(8,2)
      INTEGER TTOTAL, TPHASE, TGEN
      COMMON /SQ4TOR/ GATES, TINVAR, TOCC, TFROZ,
     &                 TWHEAD, TLEN, TALLOC,
     &                 TTOTAL, TPHASE, TGEN
      INTEGER I, J, K
      REAL DIFF
C
      NMIS = 0
      TPHASE = 2
C
      DO 30 J = 1, 8
        DO 20 I = 1, 32
          IF (TOCC(I,J,1).EQ.0 .OR. TOCC(I,J,2).EQ.0) GOTO 20
          DO 10 K = 1, 12
            DIFF = ABS(GATES(1,K,I,J,1) - GATES(1,K,I,J,2))
     &           + ABS(GATES(2,K,I,J,1) - GATES(2,K,I,J,2))
     &           + ABS(GATES(3,K,I,J,1) - GATES(3,K,I,J,2))
            IF (DIFF .GT. 1.0E-6) THEN
              NMIS = NMIS + 1
              GOTO 20
            END IF
   10     CONTINUE
   20   CONTINUE
   30 CONTINUE
C
      RETURN
      END
C
C     ================================================================
C     SUBROUTINE SQ4DIV - Divide cell (M phase)
C     ================================================================
C
      SUBROUTINE SQ4DIV(NOCC1, NOCC2)
      IMPLICIT NONE
      INTEGER NOCC1, NOCC2
      REAL    GATES(3,12,32,8,2)
      INTEGER TINVAR(32,8,2)
      INTEGER TOCC(32,8,2), TFROZ(32,8,2)
      INTEGER TWHEAD(8,2), TLEN(8,2), TALLOC(8,2)
      INTEGER TTOTAL, TPHASE, TGEN
      COMMON /SQ4TOR/ GATES, TINVAR, TOCC, TFROZ,
     &                 TWHEAD, TLEN, TALLOC,
     &                 TTOTAL, TPHASE, TGEN
      INTEGER I, J
C
      TPHASE = 3
      NOCC1 = 0
      NOCC2 = 0
C
      DO 20 J = 1, 8
        DO 10 I = 1, 32
          IF (TOCC(I,J,1) .EQ. 1) NOCC1 = NOCC1 + 1
          IF (TOCC(I,J,2) .EQ. 1) NOCC2 = NOCC2 + 1
   10   CONTINUE
   20 CONTINUE
C
      DO 40 J = 1, 8
        DO 30 I = 1, 32
          TOCC(I,J,2) = 0
          TFROZ(I,J,2) = 0
          TINVAR(I,J,2) = 0
   30   CONTINUE
        TWHEAD(J,2) = 1
        TLEN(J,2) = 0
        TALLOC(J,2) = 0
   40 CONTINUE
C
      TTOTAL = NOCC1
      TGEN = TGEN + 1
      TPHASE = 0
C
      RETURN
      END
C
C     ================================================================
C     FUNCTION SQ4ZON - Return zone index for occupancy
C     ================================================================
C     Returns: 1=COASTING, 2=ACTIVE, 3=OVERDRIVE, 4=DIVIDE
C
      INTEGER FUNCTION SQ4ZON(NOCC)
      IMPLICIT NONE
      INTEGER NOCC
      IF (NOCC .LT. 384) THEN
        SQ4ZON = 1
      ELSE IF (NOCC .LT. 432) THEN
        SQ4ZON = 2
      ELSE IF (NOCC .LT. 496) THEN
        SQ4ZON = 3
      ELSE
        SQ4ZON = 4
      END IF
      RETURN
      END
C
C     ================================================================
C     FUNCTION SQ4RES - 3-axis corruption residual (V4-3, NEW)
C     ================================================================
C     Applies (I + R120 + R240) about each Cartesian axis and returns
C     the max of the three per-axis residuals, normalized by SCALE.
C     Per-axis piece for a single-vertex perturbation d is
C     3*|d.axis|/scale, so the max is bounded below by
C     sqrt(3)*|d|/scale for ANY perturbation direction.
C     Unperturbed cuboctahedral gate: exactly 0 (verified, v4_check.py).
C     REAL*8 internally so F77 and Ergo (f64 REAL) agree bit-for-bit.
C
      REAL*8 FUNCTION SQ4RES(VTX, SCALE)
      IMPLICIT NONE
      REAL VTX(3,12), SCALE
      REAL*8 C120, S120
      PARAMETER (C120 = -0.5D0, S120 = 0.8660254037844386D0)
      REAL*8 X, Y, Z, X1, Y1, Z1, X2, Y2, Z2
      REAL*8 SX, SY, SZ, RA, RMAX
      INTEGER I, AX
C
      RMAX = 0.0D0
      DO 40 AX = 1, 3
        SX = 0.0D0
        SY = 0.0D0
        SZ = 0.0D0
        DO 30 I = 1, 12
          X = VTX(1,I)
          Y = VTX(2,I)
          Z = VTX(3,I)
          IF (AX .EQ. 1) THEN
C           rotation about X: (y,z) plane
            X1 = X
            Y1 = C120*Y - S120*Z
            Z1 = S120*Y + C120*Z
            X2 = X
            Y2 = C120*Y + S120*Z
            Z2 = -S120*Y + C120*Z
          ELSE IF (AX .EQ. 2) THEN
C           rotation about Y: (z,x) plane
            X1 = C120*X + S120*Z
            Y1 = Y
            Z1 = -S120*X + C120*Z
            X2 = C120*X - S120*Z
            Y2 = Y
            Z2 = S120*X + C120*Z
          ELSE
C           rotation about Z: (x,y) plane (the v2 triple-XOR frame)
            X1 = C120*X - S120*Y
            Y1 = S120*X + C120*Y
            Z1 = Z
            X2 = C120*X + S120*Y
            Y2 = -S120*X + C120*Y
            Z2 = Z
          END IF
          SX = SX + X + X1 + X2
          SY = SY + Y + Y1 + Y2
          SZ = SZ + Z + Z1 + Z2
   30   CONTINUE
        RA = SQRT(SX*SX + SY*SY + SZ*SZ) / SCALE
        IF (RA .GT. RMAX) RMAX = RA
   40 CONTINUE
      SQ4RES = RMAX
      RETURN
      END
C
C     ================================================================
C     FUNCTION SQ4FLW - Flow w-component (LUT, O(1))
C     ================================================================
C
      REAL FUNCTION SQ4FLW(IGEN)
      IMPLICIT NONE
      INTEGER IGEN
      INTEGER BINGEO(8), FLOWM(32), SOLTON(32), SCATLT(32)
      REAL    FLOWW(32)
      COMMON /SQ4LUT/ BINGEO, FLOWW, FLOWM, SOLTON, SCATLT
C
      SQ4FLW = FLOWW(MOD(IGEN-1, 32) + 1)
      RETURN
      END
C
C     ================================================================
C     FUNCTION SQ4FLM - Flow mode (LUT, O(1))
C     ================================================================
C     Returns: 0=COAST, 1=ACTIVE, 2=FLOW
C
      INTEGER FUNCTION SQ4FLM(IGEN)
      IMPLICIT NONE
      INTEGER IGEN
      INTEGER BINGEO(8), FLOWM(32), SOLTON(32), SCATLT(32)
      REAL    FLOWW(32)
      COMMON /SQ4LUT/ BINGEO, FLOWW, FLOWM, SOLTON, SCATLT
C
      SQ4FLM = FLOWM(MOD(IGEN-1, 32) + 1)
      RETURN
      END
C
C     ================================================================
C     FUNCTION SQ4SOL - Soliton window check (LUT, O(1))
C     ================================================================
C
      INTEGER FUNCTION SQ4SOL(IGEN)
      IMPLICIT NONE
      INTEGER IGEN
      INTEGER BINGEO(8), FLOWM(32), SOLTON(32), SCATLT(32)
      REAL    FLOWW(32)
      COMMON /SQ4LUT/ BINGEO, FLOWW, FLOWM, SOLTON, SCATLT
C
      SQ4SOL = SOLTON(MOD(IGEN-1, 32) + 1)
      RETURN
      END
