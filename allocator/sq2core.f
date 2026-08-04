C     SQUARAGON V2 CORE - F77 PORT
C     ==============================
C     Torus allocator + LUTs + gate operations.
C     All state in COMMON blocks. Zero dynamic allocation.
C
C     Torus geometry: 2 shells x 8 bins x 32 ring = 512 slots
C     Gate: 12 cuboctahedral vertices (3 floats each)
C
C     COMMON /SQ2CON/ - compile-time constants
C     COMMON /SQ2LUT/ - precomputed LUTs (zero trig hot path)
C     COMMON /SQ2TOR/ - torus state (the allocator)
C     COMMON /SQ2SED/ - seed vertices (unit cuboctahedron)
C
      BLOCK DATA SQ2BLK
      IMPLICIT NONE
C
C     --- Constants ---
      REAL PHI, SCLRAT, BIAS, ISQR2, HOPFQ, SEMSTR
      INTEGER NVTX, NEDGE, NFACE, NBINS, NSHEL, NRING
      INTEGER NUNIQ, NSLOT, THBIAS, THWORK, THMAX
      INTEGER NDMOD, SEMBIT
      COMMON /SQ2CON/ PHI, SCLRAT, BIAS, ISQR2, HOPFQ, SEMSTR,
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
C
C     --- Precomputed LUTs ---
C     BIN_GEO: Viviani geo encoding per bin (8 entries)
C     FLOWW:   flow w-component per ring position (32 entries)
C     FLOWM:   flow mode per ring position (32 entries, 0/1/2)
C     SOLTON:  soliton window mask (32 entries, 0/1)
C     SCATLUT: Viviani scatter LUT (32 entries)
      INTEGER BINGEO(8), FLOWM(32), SOLTON(32), SCATLT(32)
      REAL    FLOWW(32)
      COMMON /SQ2LUT/ BINGEO, FLOWW, FLOWM, SOLTON, SCATLT
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
      DATA SCATLT /
     &  6, 4, 6, 2, 7, 4, 3, 0, 2, 0, 3, 4, 7, 2, 6, 4,
     &  6, 4, 6, 2, 7, 4, 3, 0, 2, 0, 3, 4, 7, 2, 6, 4/
C
C     --- Seed vertices: unit cuboctahedron ---
C     SEED(3,12): xyz for each of 12 vertices
      REAL SEED(3,12)
      COMMON /SQ2SED/ SEED
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
C     TINVAR(32,8,2):      invariant per slot
C     TOCC(32,8,2):        occupied flag
C     TFROZ(32,8,2):       frozen (period-4) flag
C     TWHEAD(8,2):         write head per strand
C     TLEN(8,2):           occupied count per strand
C     TALLOC(8,2):         total alloc count per strand
C     TTOTAL:              total occupied across all strands
C     TPHASE:              cell cycle phase (0=G1,1=S,2=G2,3=M)
C     TGEN:                cell generation (division count)
      REAL    GATES(3,12,32,8,2)
      REAL    TINVAR(32,8,2)
      INTEGER TOCC(32,8,2), TFROZ(32,8,2)
      INTEGER TWHEAD(8,2), TLEN(8,2), TALLOC(8,2)
      INTEGER TTOTAL, TPHASE, TGEN
      COMMON /SQ2TOR/ GATES, TINVAR, TOCC, TFROZ,
     &                 TWHEAD, TLEN, TALLOC,
     &                 TTOTAL, TPHASE, TGEN
C
      END
C
C     ================================================================
C     SUBROUTINE SQ2INI - Initialize gate vertices at given scale
C     ================================================================
C     VTX(3,12) = output vertices
C     SCALE     = scale factor
C
      SUBROUTINE SQ2INI(VTX, SCALE)
      IMPLICIT NONE
      REAL VTX(3,12), SCALE
      REAL SEED(3,12)
      COMMON /SQ2SED/ SEED
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
C     SUBROUTINE SQ2SCL - Scale gate by 27/16 (coherent stack)
C     ================================================================
C
      SUBROUTINE SQ2SCL(VTX, SCALE)
      IMPLICIT NONE
      REAL VTX(3,12), SCALE
      SCALE = SCALE * 1.6875
      CALL SQ2INI(VTX, SCALE)
      RETURN
      END
C
C     ================================================================
C     SUBROUTINE SQ2SPH - Scale gate by phi (spillover hop)
C     ================================================================
C
      SUBROUTINE SQ2SPH(VTX, SCALE)
      IMPLICIT NONE
      REAL VTX(3,12), SCALE
      SCALE = SCALE * 1.6180339887498948
      CALL SQ2INI(VTX, SCALE)
      RETURN
      END
C
C     ================================================================
C     FUNCTION SQ2FLD - Gate XOR fold (vertex data, returns hash)
C     ================================================================
C     Computes a simple hash of the vertex data for invariant.
C     F77 has no uint64, so we use REAL*8 bit patterns via EQUIVALENCE.
C
      REAL*8 FUNCTION SQ2FLD(VTX)
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
C         XOR via integer overlay
          CALL SQ2XOR(FOLD, DBUF, FOLD)
   10   CONTINUE
   20 CONTINUE
      SQ2FLD = FOLD
      RETURN
      END
C
C     ================================================================
C     SUBROUTINE SQ2XOR - XOR two REAL*8 values via integer bits
C     ================================================================
C
      SUBROUTINE SQ2XOR(A, B, C)
      IMPLICIT NONE
      REAL*8 A, B, C
      REAL*8 LA, LB
      INTEGER*4 IA(2), IB(2), IC(2)
      EQUIVALENCE (IA, LA)
      EQUIVALENCE (IB, LB)
C     Copy dummy args to locals for EQUIVALENCE
      LA = A
      LB = B
      IC(1) = IEOR(IA(1), IB(1))
      IC(2) = IEOR(IA(2), IB(2))
C     Copy result
      CALL SQ2CP8(IC, C)
      RETURN
      END
C
C     ================================================================
C     SUBROUTINE SQ2CP8 - Copy 8 bytes (INTEGER*4 pair to REAL*8)
C     ================================================================
C
      SUBROUTINE SQ2CP8(ISRC, DDST)
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
C     SUBROUTINE SQ2TIN - Initialize torus (all slots empty)
C     ================================================================
C
      SUBROUTINE SQ2TIN
      IMPLICIT NONE
      REAL    GATES(3,12,32,8,2)
      REAL    TINVAR(32,8,2)
      INTEGER TOCC(32,8,2), TFROZ(32,8,2)
      INTEGER TWHEAD(8,2), TLEN(8,2), TALLOC(8,2)
      INTEGER TTOTAL, TPHASE, TGEN
      COMMON /SQ2TOR/ GATES, TINVAR, TOCC, TFROZ,
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
            TINVAR(I,J,K) = 0.0
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
C     FUNCTION SQ2SCT - Viviani scatter (LUT, O(1))
C     ================================================================
C     Returns bin index 1-8 for a given ID
C
      INTEGER FUNCTION SQ2SCT(ID)
      IMPLICIT NONE
      INTEGER ID
      INTEGER BINGEO(8), FLOWM(32), SOLTON(32), SCATLT(32)
      REAL    FLOWW(32)
      COMMON /SQ2LUT/ BINGEO, FLOWW, FLOWM, SOLTON, SCATLT
C
      SQ2SCT = SCATLT(MOD(ID-1, 32) + 1) + 1
      RETURN
      END
C
C     ================================================================
C     SUBROUTINE SQ2ALC - Allocate: scatter to bin, write codon
C     ================================================================
C     ID    = allocation ID (1-based)
C     TOTAL = total allocations expected
C     DSEED = data seed for perturbation
C     IERR  = 0 on success, -1 on full
C
      SUBROUTINE SQ2ALC(ID, TOTAL, DSEED, IERR)
      IMPLICIT NONE
      INTEGER ID, TOTAL, IERR
      REAL DSEED
C
      REAL    GATES(3,12,32,8,2)
      REAL    TINVAR(32,8,2)
      INTEGER TOCC(32,8,2), TFROZ(32,8,2)
      INTEGER TWHEAD(8,2), TLEN(8,2), TALLOC(8,2)
      INTEGER TTOTAL, TPHASE, TGEN
      COMMON /SQ2TOR/ GATES, TINVAR, TOCC, TFROZ,
     &                 TWHEAD, TLEN, TALLOC,
     &                 TTOTAL, TPHASE, TGEN
C
      REAL PHI, SCLRAT, BIASV, ISQR2, HOPFQ, SEMSTR
      INTEGER NVTX, NEDGE, NFACE, NBINS, NSHEL, NRING
      INTEGER NUNIQ, NSLOT, THBIAS, THWORK, THMAX
      INTEGER NDMOD, SEMBIT
      COMMON /SQ2CON/ PHI, SCLRAT, BIASV, ISQR2, HOPFQ, SEMSTR,
     &                 NVTX, NEDGE, NFACE, NBINS, NSHEL, NRING,
     &                 NUNIQ, NSLOT, THBIAS, THWORK, THMAX,
     &                 NDMOD, SEMBIT
C
      INTEGER SQ2SCT
      REAL*8  SQ2FLD
      INTEGER BIN, GEN, VIDX, SHELL
      REAL    SCALE, VTX(3,12)
      REAL*8  INV
C
      IERR = 0
      SHELL = 1
      BIN = SQ2SCT(ID)
      GEN = TWHEAD(BIN, SHELL)
C
      IF (GEN .GT. 32) THEN
        IERR = -1
        RETURN
      END IF
C
C     Initialize gate at shell scale
      SCALE = 1.0
      CALL SQ2INI(VTX, SCALE)
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
      CALL SQ2SGT(VTX, GEN, BIN, SHELL)
C
C     Compute invariant (simplified: fold only)
      INV = SQ2FLD(VTX)
      TINVAR(GEN, BIN, SHELL) = REAL(INV)
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
C     SUBROUTINE SQ2FAL - FAST allocate (LUT-only, no gate write)
C     ================================================================
C     Matches the C optimized path: scatter + LUT invariant + rotate.
C     No vertex init, no gate fold, no memcpy. Just index math.
C
C     ID    = allocation ID (1-based)
C     IERR  = 0 on success, -1 on full
C
      SUBROUTINE SQ2FAL(ID, IERR)
      IMPLICIT NONE
      INTEGER ID, IERR
C
      REAL    GATES(3,12,32,8,2)
      REAL    TINVAR(32,8,2)
      INTEGER TOCC(32,8,2), TFROZ(32,8,2)
      INTEGER TWHEAD(8,2), TLEN(8,2), TALLOC(8,2)
      INTEGER TTOTAL, TPHASE, TGEN
      COMMON /SQ2TOR/ GATES, TINVAR, TOCC, TFROZ,
     &                 TWHEAD, TLEN, TALLOC,
     &                 TTOTAL, TPHASE, TGEN
C
      INTEGER BINGEO(8), FLOWM(32), SOLTON(32), SCATLT(32)
      REAL    FLOWW(32)
      COMMON /SQ2LUT/ BINGEO, FLOWW, FLOWM, SOLTON, SCATLT
C
      INTEGER SQ2SCT
      INTEGER BIN, GEN, SHELL, POS
      INTEGER IGEO, IBIN, ISHEL
      INTEGER TBITS
      REAL    RINV
C
      IERR = 0
      SHELL = 1
      BIN = SQ2SCT(ID)
      GEN = TWHEAD(BIN, SHELL)
C
      IF (GEN .GT. 32) THEN
        IERR = -1
        RETURN
      END IF
C
C     Fast invariant: LUT geo + bin + shell encoding (no sinf)
C     Matches sq2_shadow_invariant_fast from C version
      POS = MOD(GEN-1, 32) + 1
      IGEO = BINGEO(BIN)
      IBIN = BIN - 1
      ISHEL = SHELL - 1
C     Pack: geo<<24 | bin<<16 | shell<<8 | gen
C     (Simplified 32-bit invariant for F77, same structure as C 64-bit)
      RINV = REAL(ISHFT(IGEO, 24) + ISHFT(IBIN, 16)
     &       + ISHFT(ISHEL, 8) + (GEN - 1))
C
C     Apply seam rotation: gen * 2 bits (single rotate, not loop)
      TBITS = MOD((GEN - 1) * 2, 32)
      IF (TBITS .GT. 0) THEN
C       Rotate the integer bits (approximation via float)
        RINV = RINV + REAL(TBITS) * 0.01
      END IF
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
C     SUBROUTINE SQ2SGT - Store gate vertices into torus
C     ================================================================
C
      SUBROUTINE SQ2SGT(VTX, GEN, BIN, SHELL)
      IMPLICIT NONE
      REAL VTX(3,12)
      INTEGER GEN, BIN, SHELL
      REAL    GATES(3,12,32,8,2)
      REAL    TINVAR(32,8,2)
      INTEGER TOCC(32,8,2), TFROZ(32,8,2)
      INTEGER TWHEAD(8,2), TLEN(8,2), TALLOC(8,2)
      INTEGER TTOTAL, TPHASE, TGEN
      COMMON /SQ2TOR/ GATES, TINVAR, TOCC, TFROZ,
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
C     SUBROUTINE SQ2REP - Replicate shell 1 to shell 2 (S phase)
C     ================================================================
C     NCOPY = number of codons copied (output)
C
      SUBROUTINE SQ2REP(NCOPY)
      IMPLICIT NONE
      INTEGER NCOPY
      REAL    GATES(3,12,32,8,2)
      REAL    TINVAR(32,8,2)
      INTEGER TOCC(32,8,2), TFROZ(32,8,2)
      INTEGER TWHEAD(8,2), TLEN(8,2), TALLOC(8,2)
      INTEGER TTOTAL, TPHASE, TGEN
      COMMON /SQ2TOR/ GATES, TINVAR, TOCC, TFROZ,
     &                 TWHEAD, TLEN, TALLOC,
     &                 TTOTAL, TPHASE, TGEN
      INTEGER I, J, K
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
C     SUBROUTINE SQ2VFY - Verify shell 1 vs shell 2 (G2 phase)
C     ================================================================
C     NMIS = number of mismatches found (output)
C
      SUBROUTINE SQ2VFY(NMIS)
      IMPLICIT NONE
      INTEGER NMIS
      REAL    GATES(3,12,32,8,2)
      REAL    TINVAR(32,8,2)
      INTEGER TOCC(32,8,2), TFROZ(32,8,2)
      INTEGER TWHEAD(8,2), TLEN(8,2), TALLOC(8,2)
      INTEGER TTOTAL, TPHASE, TGEN
      COMMON /SQ2TOR/ GATES, TINVAR, TOCC, TFROZ,
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
C         Compare vertex data
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
C     SUBROUTINE SQ2DIV - Divide cell (M phase)
C     ================================================================
C     Daughter state goes to shell 2, parent keeps shell 1.
C     After division, shell 2 is cleared for parent.
C     NOCC1 = parent occupied (output)
C     NOCC2 = daughter occupied (output)
C
      SUBROUTINE SQ2DIV(NOCC1, NOCC2)
      IMPLICIT NONE
      INTEGER NOCC1, NOCC2
      REAL    GATES(3,12,32,8,2)
      REAL    TINVAR(32,8,2)
      INTEGER TOCC(32,8,2), TFROZ(32,8,2)
      INTEGER TWHEAD(8,2), TLEN(8,2), TALLOC(8,2)
      INTEGER TTOTAL, TPHASE, TGEN
      COMMON /SQ2TOR/ GATES, TINVAR, TOCC, TFROZ,
     &                 TWHEAD, TLEN, TALLOC,
     &                 TTOTAL, TPHASE, TGEN
      INTEGER I, J
C
      TPHASE = 3
      NOCC1 = 0
      NOCC2 = 0
C
C     Count occupancy per shell
      DO 20 J = 1, 8
        DO 10 I = 1, 32
          IF (TOCC(I,J,1) .EQ. 1) NOCC1 = NOCC1 + 1
          IF (TOCC(I,J,2) .EQ. 1) NOCC2 = NOCC2 + 1
   10   CONTINUE
   20 CONTINUE
C
C     Clear shell 2 (daughter takes it externally)
      DO 40 J = 1, 8
        DO 30 I = 1, 32
          TOCC(I,J,2) = 0
          TFROZ(I,J,2) = 0
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
C     FUNCTION SQ2ZON - Return zone string index for occupancy
C     ================================================================
C     Returns: 1=COASTING, 2=ACTIVE, 3=OVERDRIVE, 4=DIVIDE
C
      INTEGER FUNCTION SQ2ZON(NOCC)
      IMPLICIT NONE
      INTEGER NOCC
      IF (NOCC .LT. 384) THEN
        SQ2ZON = 1
      ELSE IF (NOCC .LT. 432) THEN
        SQ2ZON = 2
      ELSE IF (NOCC .LT. 496) THEN
        SQ2ZON = 3
      ELSE
        SQ2ZON = 4
      END IF
      RETURN
      END
C
C     ================================================================
C     FUNCTION SQ2FLW - Flow w-component (LUT, O(1))
C     ================================================================
C
      REAL FUNCTION SQ2FLW(IGEN)
      IMPLICIT NONE
      INTEGER IGEN
      INTEGER BINGEO(8), FLOWM(32), SOLTON(32), SCATLT(32)
      REAL    FLOWW(32)
      COMMON /SQ2LUT/ BINGEO, FLOWW, FLOWM, SOLTON, SCATLT
C
      SQ2FLW = FLOWW(MOD(IGEN-1, 32) + 1)
      RETURN
      END
C
C     ================================================================
C     FUNCTION SQ2FLM - Flow mode (LUT, O(1))
C     ================================================================
C     Returns: 0=COAST, 1=ACTIVE, 2=FLOW
C
      INTEGER FUNCTION SQ2FLM(IGEN)
      IMPLICIT NONE
      INTEGER IGEN
      INTEGER BINGEO(8), FLOWM(32), SOLTON(32), SCATLT(32)
      REAL    FLOWW(32)
      COMMON /SQ2LUT/ BINGEO, FLOWW, FLOWM, SOLTON, SCATLT
C
      SQ2FLM = FLOWM(MOD(IGEN-1, 32) + 1)
      RETURN
      END
C
C     ================================================================
C     FUNCTION SQ2SOL - Soliton window check (LUT, O(1))
C     ================================================================
C
      INTEGER FUNCTION SQ2SOL(IGEN)
      IMPLICIT NONE
      INTEGER IGEN
      INTEGER BINGEO(8), FLOWM(32), SOLTON(32), SCATLT(32)
      REAL    FLOWW(32)
      COMMON /SQ2LUT/ BINGEO, FLOWW, FLOWM, SOLTON, SCATLT
C
      SQ2SOL = SOLTON(MOD(IGEN-1, 32) + 1)
      RETURN
      END
