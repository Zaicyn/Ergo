/* ══════════════════════════════════════════════════════════════════
 * ERGO_IO.H — file-unit runtime for Ergo (Spec/Ergo_Spec.md Part 10).
 *
 * Header-only (static inline). Unit namespace:
 *   * = stdout, 0 = stderr (preconnected, handled by codegen),
 *   1..63 = OPEN / ESF_OPEN file units (one namespace, one table).
 *
 * Determinism contract: writes are program-ordered; flush points are
 * exactly CLOSE / ESF_CLOSE / program end (_ergo_io_shutdown, called
 * from main's normal exit and from STOP). Failures are NAMED runtime
 * errors ("ERGO-IO: ...") with exit status 1 — never silent.
 * ══════════════════════════════════════════════════════════════════ */
#ifndef ERGO_IO_H
#define ERGO_IO_H

#include <stdio.h>
#include <stdlib.h>

#define ERGO_MAX_UNIT 64

/* kind: 0 = free, 1 = formatted/raw file (OPEN), 2 = .esf stream */
static FILE *_ergo_unit_fp[ERGO_MAX_UNIT];
static int   _ergo_unit_kind[ERGO_MAX_UNIT];

static void _ergo_io_fail(const char *what) {
    fprintf(stderr, "ERGO-IO: %s\n", what);
    exit(1);
}

/* Register `fp` on `unit` with kind `kind` (1=file, 2=esf).
 * Shared by _ergo_open (here) and esf_open (ergo_stream.h). */
static inline void _ergo_unit_claim(int unit, FILE *fp, int kind) {
    if (unit < 1 || unit >= ERGO_MAX_UNIT)
        _ergo_io_fail("OPEN: unit out of range (1..63)");
    if (_ergo_unit_kind[unit] != 0)
        _ergo_io_fail("OPEN: unit already open");
    _ergo_unit_fp[unit] = fp;
    _ergo_unit_kind[unit] = kind;
}

static inline void _ergo_open(int unit, const char *path,
                              const char *mode) {
    if (unit < 1 || unit >= ERGO_MAX_UNIT)
        _ergo_io_fail("OPEN: unit out of range (1..63)");
    if (_ergo_unit_kind[unit] != 0)
        _ergo_io_fail("OPEN: unit already open");
    FILE *fp = fopen(path, mode);
    if (!fp) {
        fprintf(stderr, "ERGO-IO: OPEN failed for path '%s'\n", path);
        exit(1);
    }
    _ergo_unit_claim(unit, fp, 1);
}

/* Unit lookup for WRITE(unit, ...): must be open for formatted/raw
 * file output (kind 1). .esf units reject plain WRITE. */
static inline FILE *_ergo_unit(int unit) {
    if (unit < 1 || unit >= ERGO_MAX_UNIT ||
            _ergo_unit_kind[unit] == 0)
        _ergo_io_fail("WRITE: unit is not open");
    if (_ergo_unit_kind[unit] != 1)
        _ergo_io_fail("WRITE: unit is an .esf stream "
                      "(use ESF_WRITE)");
    return _ergo_unit_fp[unit];
}

/* Raw-record write of A(lo:hi): bytes (hi-lo+1)*esz from base+(lo-1),
 * no record markers, native endianness (Part 10.4). */
static inline void _ergo_raw_write(FILE *fp, const void *base,
                                   long lo, long hi, long extent,
                                   size_t esz, const char *name) {
    if (lo < 1 || hi < lo || hi > extent) {
        fprintf(stderr,
                "ERGO-IO: raw WRITE section out of bounds: %s(%ld:%ld) "
                "vs extent %ld\n", name, lo, hi, extent);
        exit(1);
    }
    size_t n = (size_t)(hi - lo + 1);
    const char *p = (const char *)base + (size_t)(lo - 1) * esz;
    if (n > 0 && fwrite(p, esz, n, fp) != n)
        _ergo_io_fail("raw WRITE: short write (disk full?)");
}

static inline void _ergo_close(int unit) {
    if (unit < 1 || unit >= ERGO_MAX_UNIT ||
            _ergo_unit_kind[unit] == 0)
        _ergo_io_fail("CLOSE: unit is not open");
    if (_ergo_unit_kind[unit] != 1)
        _ergo_io_fail("CLOSE: unit is an .esf stream "
                      "(use ESF_CLOSE)");
    fflush(_ergo_unit_fp[unit]);
    fclose(_ergo_unit_fp[unit]);
    _ergo_unit_fp[unit] = NULL;
    _ergo_unit_kind[unit] = 0;
}

/* Program end: flush+close every open unit in increasing unit order.
 * .esf frames are written eagerly (one fwrite per ESF_WRITE), so
 * kind-2 units need nothing beyond flush+close either. */
static inline void _ergo_io_shutdown(void) {
    for (int u = 1; u < ERGO_MAX_UNIT; u++) {
        if (_ergo_unit_kind[u] != 0) {
            fflush(_ergo_unit_fp[u]);
            fclose(_ergo_unit_fp[u]);
            _ergo_unit_fp[u] = NULL;
            _ergo_unit_kind[u] = 0;
        }
    }
}

#endif /* ERGO_IO_H */
