/* pktcc.h -- portable packet-codec core (extract of min/Fasm/Secure/pktcodec.c).
 * 8 x 512 B units + P (XOR) + Q (GF(2^8)-weighted) parity. Repairs 1-2
 * whole-unit erasures; single-byte errors via per-unit SEC against
 * triple4 refs. Plain C99, no libc beyond stdint/stddef. Single source
 * for the host tools (gcc) and the ESP-IDF build.
 */
#pragma once
#include <stdint.h>
#include <stddef.h>

#define PKTCC_NP 8
#define PKTCC_PL 512

/* Build GF tables. Call once before anything else. */
void pktcc_init(void);
/* P[i] = XOR over units; Q[i] = XOR over gfm(gexp[u], units[u][i]). */
void pktcc_parity(const uint8_t units[PKTCC_NP][PKTCC_PL],
                  uint8_t p[PKTCC_PL], uint8_t q[PKTCC_PL]);
/* Per-unit 4-word stamp (detection reference, NOT reconstruction data). */
void pktcc_ref(const uint8_t *unit, uint32_t ref[4]);
/* Returns 1 if unit is clean or single-byte-repaired in place, else 0. */
int pktcc_sec(uint8_t *unit, const uint32_t ref[4]);
/* Rebuild lost[] units (erased = zeroed) in place from P (+Q if 2 lost).
 * Verbatim semantics: no-op success if none lost; if >2 lost, rebuilds
 * the first two found (caller must not rely on the rest).
 * Returns 0 on success. */
int pktcc_repair_erase(uint8_t units[PKTCC_NP][PKTCC_PL],
                       const uint8_t p[PKTCC_PL], const uint8_t q[PKTCC_PL],
                       const int lost[PKTCC_NP]);
