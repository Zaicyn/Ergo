/* esf_syndrome.h — shared ESF2 weighted-syndrome computation.
 *
 * Used by bench_esf_v2.c and bench_esf_v2_batch_repair.c.
 * Computes S0 = sum(b), S1 = sum(b*idx), S2 = sum(b*idx^2) over the fixed
 * region [4,16) U [28,4096) with 1-based idx.
 */

#ifndef ESF_SYNDROME_H
#define ESF_SYNDROME_H

#include <stdint.h>
#include <string.h>

#define ESF_FRAME   4096
#define ESF_MAXPAY  4068

static uint32_t esf_idx_table[ESF_MAXPAY];
static uint32_t esf_idx2_table[ESF_MAXPAY];
static int esf_v2_tables_ready = 0;

static inline void esf_v2_init_tables(void) {
    if (esf_v2_tables_ready) return;
    for (int i = 0; i < ESF_MAXPAY; i++) {
        uint32_t o = 28 + (uint32_t)i;
        uint32_t idx = o - 15;
        esf_idx_table[i] = idx;
        esf_idx2_table[i] = idx * idx;
    }
    esf_v2_tables_ready = 1;
}

static inline void esf_scalar_syndromes(const uint8_t *frame,
                                         uint32_t *s0, uint32_t *s1, uint32_t *s2) {
    uint32_t a = 0, b = 0, c = 0;
    for (uint32_t o = 4; o < 16; o++) {
        uint32_t v = frame[o], idx = o - 3;
        a += v;
        b += v * idx;
        c += (uint32_t)((uint64_t)v * idx * idx);
    }
    for (int i = 0; i < ESF_MAXPAY; i++) {
        uint32_t v = frame[28 + i], idx = esf_idx_table[i];
        a += v;
        b += v * idx;
        c += v * esf_idx2_table[i];
    }
    *s0 = a; *s1 = b; *s2 = c;
}

#if defined(__SSE4_1__)
#include <smmintrin.h>

static inline uint32_t esf_hsum_epi32(__m128i v) {
    __m128i hi = _mm_unpackhi_epi64(v, v);
    __m128i sum = _mm_add_epi32(v, hi);
    __m128i hi32 = _mm_shuffle_epi32(sum, _MM_SHUFFLE(2,3,0,1));
    sum = _mm_add_epi32(sum, hi32);
    return (uint32_t)_mm_cvtsi128_si32(sum);
}

static inline void esf_sse41_syndromes(const uint8_t *frame,
                                        uint32_t *s0, uint32_t *s1, uint32_t *s2) {
    uint32_t a = 0, b = 0, c = 0;
    for (uint32_t o = 4; o < 16; o++) {
        uint32_t v = frame[o], idx = o - 3;
        a += v;
        b += v * idx;
        c += (uint32_t)((uint64_t)v * idx * idx);
    }

    __m128i vs0 = _mm_setzero_si128();
    __m128i vs1 = _mm_setzero_si128();
    __m128i vs2 = _mm_setzero_si128();

    int i = 0;
    for (; i + 16 <= ESF_MAXPAY; i += 16) {
        __m128i bytes = _mm_loadu_si128((const __m128i*)(frame + 28 + i));
        __m128i v0 = _mm_cvtepu8_epi32(bytes);
        __m128i v1 = _mm_cvtepu8_epi32(_mm_srli_si128(bytes, 4));
        __m128i v2 = _mm_cvtepu8_epi32(_mm_srli_si128(bytes, 8));
        __m128i v3 = _mm_cvtepu8_epi32(_mm_srli_si128(bytes, 12));

        __m128i idx0 = _mm_loadu_si128((const __m128i*)(esf_idx_table + i));
        __m128i idx1 = _mm_loadu_si128((const __m128i*)(esf_idx_table + i + 4));
        __m128i idx2 = _mm_loadu_si128((const __m128i*)(esf_idx_table + i + 8));
        __m128i idx3 = _mm_loadu_si128((const __m128i*)(esf_idx_table + i + 12));

        vs0 = _mm_add_epi32(vs0, _mm_add_epi32(_mm_add_epi32(v0, v1), _mm_add_epi32(v2, v3)));
        vs1 = _mm_add_epi32(vs1, _mm_add_epi32(
            _mm_add_epi32(_mm_mullo_epi32(v0, idx0), _mm_mullo_epi32(v1, idx1)),
            _mm_add_epi32(_mm_mullo_epi32(v2, idx2), _mm_mullo_epi32(v3, idx3))));
        vs2 = _mm_add_epi32(vs2, _mm_add_epi32(
            _mm_add_epi32(_mm_mullo_epi32(v0, _mm_loadu_si128((const __m128i*)(esf_idx2_table + i))),
                          _mm_mullo_epi32(v1, _mm_loadu_si128((const __m128i*)(esf_idx2_table + i + 4)))),
            _mm_add_epi32(_mm_mullo_epi32(v2, _mm_loadu_si128((const __m128i*)(esf_idx2_table + i + 8))),
                          _mm_mullo_epi32(v3, _mm_loadu_si128((const __m128i*)(esf_idx2_table + i + 12))))));
    }

    a += esf_hsum_epi32(vs0);
    b += esf_hsum_epi32(vs1);
    c += esf_hsum_epi32(vs2);

    for (; i < ESF_MAXPAY; i++) {
        uint32_t v = frame[28 + i], idx = esf_idx_table[i];
        a += v;
        b += v * idx;
        c += v * esf_idx2_table[i];
    }

    *s0 = a; *s1 = b; *s2 = c;
}
#endif

#if defined(__AVX2__)
#include <immintrin.h>

static inline uint32_t esf_hsum_epi32_avx2(__m256i v) {
    __m128i lo = _mm256_castsi256_si128(v);
    __m128i hi = _mm256_extracti128_si256(v, 1);
    lo = _mm_add_epi32(lo, hi);
    __m128i hi64 = _mm_unpackhi_epi64(lo, lo);
    lo = _mm_add_epi32(lo, hi64);
    __m128i hi32 = _mm_shuffle_epi32(lo, _MM_SHUFFLE(2,3,0,1));
    lo = _mm_add_epi32(lo, hi32);
    return (uint32_t)_mm_cvtsi128_si32(lo);
}

static inline void esf_avx2_syndromes(const uint8_t *frame,
                                       uint32_t *s0, uint32_t *s1, uint32_t *s2) {
    uint32_t a = 0, b = 0, c = 0;
    for (uint32_t o = 4; o < 16; o++) {
        uint32_t v = frame[o], idx = o - 3;
        a += v;
        b += v * idx;
        c += (uint32_t)((uint64_t)v * idx * idx);
    }

    __m256i vs0 = _mm256_setzero_si256();
    __m256i vs1 = _mm256_setzero_si256();
    __m256i vs2 = _mm256_setzero_si256();

    int i = 0;
    for (; i + 32 <= ESF_MAXPAY; i += 32) {
        __m256i bytes = _mm256_loadu_si256((const __m256i*)(frame + 28 + i));
        __m128i lo = _mm256_castsi256_si128(bytes);
        __m128i hi = _mm256_extracti128_si256(bytes, 1);

        __m256i v0 = _mm256_cvtepu8_epi32(lo);
        __m256i v1 = _mm256_cvtepu8_epi32(_mm_srli_si128(lo, 8));
        __m256i v2 = _mm256_cvtepu8_epi32(hi);
        __m256i v3 = _mm256_cvtepu8_epi32(_mm_srli_si128(hi, 8));

        __m256i idx0 = _mm256_loadu_si256((const __m256i*)(esf_idx_table + i));
        __m256i idx1 = _mm256_loadu_si256((const __m256i*)(esf_idx_table + i + 8));
        __m256i idx2 = _mm256_loadu_si256((const __m256i*)(esf_idx_table + i + 16));
        __m256i idx3 = _mm256_loadu_si256((const __m256i*)(esf_idx_table + i + 24));

        __m256i i2_0 = _mm256_loadu_si256((const __m256i*)(esf_idx2_table + i));
        __m256i i2_1 = _mm256_loadu_si256((const __m256i*)(esf_idx2_table + i + 8));
        __m256i i2_2 = _mm256_loadu_si256((const __m256i*)(esf_idx2_table + i + 16));
        __m256i i2_3 = _mm256_loadu_si256((const __m256i*)(esf_idx2_table + i + 24));

        vs0 = _mm256_add_epi32(vs0, _mm256_add_epi32(_mm256_add_epi32(v0, v1), _mm256_add_epi32(v2, v3)));

        vs1 = _mm256_add_epi32(vs1, _mm256_add_epi32(
            _mm256_add_epi32(_mm256_mullo_epi32(v0, idx0), _mm256_mullo_epi32(v1, idx1)),
            _mm256_add_epi32(_mm256_mullo_epi32(v2, idx2), _mm256_mullo_epi32(v3, idx3))));

        vs2 = _mm256_add_epi32(vs2, _mm256_add_epi32(
            _mm256_add_epi32(_mm256_mullo_epi32(v0, i2_0), _mm256_mullo_epi32(v1, i2_1)),
            _mm256_add_epi32(_mm256_mullo_epi32(v2, i2_2), _mm256_mullo_epi32(v3, i2_3))));
    }

    a += esf_hsum_epi32_avx2(vs0);
    b += esf_hsum_epi32_avx2(vs1);
    c += esf_hsum_epi32_avx2(vs2);

    for (; i < ESF_MAXPAY; i++) {
        uint32_t v = frame[28 + i], idx = esf_idx_table[i];
        a += v;
        b += v * idx;
        c += v * esf_idx2_table[i];
    }

    *s0 = a; *s1 = b; *s2 = c;
}
#endif

static inline void esf_compute_syndromes_v2(const uint8_t *frame,
                                             uint32_t *s0, uint32_t *s1, uint32_t *s2) {
#if defined(__AVX2__)
    esf_avx2_syndromes(frame, s0, s1, s2);
#elif defined(__SSE4_1__)
    esf_sse41_syndromes(frame, s0, s1, s2);
#else
    esf_scalar_syndromes(frame, s0, s1, s2);
#endif
}

#endif /* ESF_SYNDROME_H */
