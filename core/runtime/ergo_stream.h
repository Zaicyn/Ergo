/* ══════════════════════════════════════════════════════════════════
 * ERGO_STREAM.H — .esf framed stream writer
 * (Spec/Ergo_Stream_Format.md; language surface: Spec Part 10).
 *
 * Fixed 4096-byte frames; up to 8 logical channels multiplexed by the
 * Viviani scatter schedule (the v4 allocator bake); per-frame
 * integrity as three WEIGHTED SYNDROMES (ESF2): S0 = Σb, S1 = Σb·idx,
 * S2 = Σb·idx² over the fixed region [4,16) ∪ [28,4096) with idx
 * 1-based — detection floor |d| ≥ 1 plus exact single-byte repair
 * (see the spec §3 for the uniqueness proof and the consistency
 * gate). One ESF_WRITE = one frame = one eager fwrite — no hidden
 * buffering; flush points are ESF_CLOSE / program end.
 *
 *   esf_open(unit, "path", nch)     nch in 1..8
 *   ch = esf_next(unit)             scheduled channel of next frame
 *   esf_write(unit, ch, buf, nbytes)
 *   esf_close(unit)
 *
 * All failures are NAMED runtime errors ("ERGO-ESF: ..."), exit 1.
 * ══════════════════════════════════════════════════════════════════ */
#ifndef ERGO_STREAM_H
#define ERGO_STREAM_H

#include <stdint.h>
#include <string.h>

#include "ergo_io.h"

/* Scatter LUT: sq2_viviani_scatter_full(id, 52), HOPFQ=1.97, f32 —
 * the v4 bake (allocator/TUNING_FINDINGS.md Fix 1; cross-port
 * certified F77/Ergo/C/Python). All 8 bins visited per 32-period. */
static const uint8_t ESF_SCATLT[32] = {
    6, 5, 4, 0, 2, 3, 4, 7, 4, 6, 3, 0, 1, 2, 1, 0,
    3, 6, 4, 7, 4, 3, 2, 0, 4, 5, 6, 5, 4, 0, 2, 3
};

#define ESF_FRAME   4096
#define ESF_MAXPAY  4068
#define ESF_MAXCH   8

static uint32_t _esf_nch[ERGO_MAX_UNIT];
static uint32_t _esf_k[ERGO_MAX_UNIT];          /* next frame index */
static uint32_t _esf_cseq[ERGO_MAX_UNIT][ESF_MAXCH];

static void _esf_fail(const char *what) {
    fprintf(stderr, "ERGO-ESF: %s\n", what);
    exit(1);
}

static void _esf_put32(uint8_t *p, uint32_t v) {
    p[0] = (uint8_t)(v & 0xff);
    p[1] = (uint8_t)((v >> 8) & 0xff);
    p[2] = (uint8_t)((v >> 16) & 0xff);
    p[3] = (uint8_t)((v >> 24) & 0xff);
}

static void _esf_put16(uint8_t *p, uint32_t v) {
    p[0] = (uint8_t)(v & 0xff);
    p[1] = (uint8_t)((v >> 8) & 0xff);
}

static FILE *_esf_unit(int unit) {
    if (unit < 1 || unit >= ERGO_MAX_UNIT ||
            _ergo_unit_kind[unit] != 2)
        _esf_fail("unit is not an open .esf stream");
    return _ergo_unit_fp[unit];
}

static inline void esf_open(int unit, const char *path, int nch) {
    if (nch < 1 || nch > ESF_MAXCH)
        _esf_fail("ESF_OPEN: channel count out of range (1..8)");
    if (unit < 1 || unit >= ERGO_MAX_UNIT)
        _esf_fail("ESF_OPEN: unit out of range (1..63)");
    if (_ergo_unit_kind[unit] != 0)
        _esf_fail("ESF_OPEN: unit already open");
    FILE *fp = fopen(path, "wb");
    if (!fp) {
        fprintf(stderr, "ERGO-ESF: ESF_OPEN failed for path '%s'\n",
                path);
        exit(1);
    }
    _ergo_unit_claim(unit, fp, 2);
    _esf_nch[unit] = (uint32_t)nch;
    _esf_k[unit] = 0;
    for (int c = 0; c < ESF_MAXCH; c++)
        _esf_cseq[unit][c] = 0;
}

/* Scheduled channel of the next frame — direct addressing, computed
 * from the frame index, never searched. */
static inline int esf_next(int unit) {
    _esf_unit(unit);
    return (int)(ESF_SCATLT[_esf_k[unit] & 31u] % _esf_nch[unit]);
}

static inline void esf_write(int unit, int ch, const void *payload,
                             int nbytes) {
    FILE *fp = _esf_unit(unit);
    uint32_t k = _esf_k[unit];
    uint32_t sched = ESF_SCATLT[k & 31u] % _esf_nch[unit];
    if ((uint32_t)ch != sched)
        _esf_fail("ESF_WRITE: channel out of schedule "
                  "(post the channel ESF_NEXT returns)");
    if (nbytes < 0 || nbytes > ESF_MAXPAY)
        _esf_fail("ESF_WRITE: payload length out of range (0..4068)");
    static uint8_t frame[ESF_FRAME];
    memset(frame, 0, sizeof(frame));
    memcpy(frame, "ESF2", 4);
    _esf_put32(frame + 4, k);
    _esf_put16(frame + 8, (uint32_t)ch);
    _esf_put16(frame + 10, (uint32_t)nbytes);
    _esf_put32(frame + 12, _esf_cseq[unit][ch]);
    if (nbytes > 0)
        memcpy(frame + 28, payload, (size_t)nbytes);
    /* Weighted syndromes over the fixed region [4,16) ∪ [28,4096):
     * idx = o-3 (header, 1..12), idx = o-15 (payload, 13..4080);
     * S0 = Σb, S1 = Σb·idx, S2 = Σb·idx² (mod 2^32). Bytes past
     * nbytes are zero (memset) and contribute nothing. */
    uint32_t s0 = 0, s1 = 0, s2 = 0;
    for (uint32_t o = 4; o < 16; o++) {
        uint32_t b = frame[o], idx = o - 3;
        s0 += b;
        s1 += b * idx;
        s2 += (uint32_t)((uint64_t)b * idx * idx);
    }
    for (uint32_t o = 28; o < ESF_FRAME; o++) {
        uint32_t b = frame[o], idx = o - 15;
        s0 += b;
        s1 += b * idx;
        s2 += (uint32_t)((uint64_t)b * idx * idx);
    }
    _esf_put32(frame + 16, s0);
    _esf_put32(frame + 20, s1);
    _esf_put32(frame + 24, s2);
    if (fwrite(frame, 1, ESF_FRAME, fp) != ESF_FRAME)
        _esf_fail("ESF_WRITE: short write (disk full?)");
    _esf_cseq[unit][ch]++;
    _esf_k[unit] = k + 1;
}

static inline void esf_close(int unit) {
    FILE *fp = _esf_unit(unit);
    fflush(fp);
    fclose(fp);
    _ergo_unit_fp[unit] = NULL;
    _ergo_unit_kind[unit] = 0;
}

#endif /* ERGO_STREAM_H */
