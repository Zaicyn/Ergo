/* V8 CPU slice — extracted verbatim from Testing/V8/aizawa.cuh
 * (compute_invariant @ ~L243, viviani_normal @ ~L144).
 * Only the CUDA decoration (VIVIANI_HOST_DEVICE) is stubbed out;
 * logic and constants are untouched. No CUDA headers needed. */

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <math.h>

#define VIVIANI_HOST_DEVICE static inline
#define VIVIANI_HOPF_Q 1.97f

typedef struct { float x, y, z; } VivianNormal;

VIVIANI_HOST_DEVICE VivianNormal viviani_normal(float theta) {
    float sin_t  = sinf(theta),       cos_t  = cosf(theta);
    float sin_3t = sinf(3.0f * theta), cos_3t = cosf(3.0f * theta);

    float x = sin_t  - 0.5f * sin_3t;
    float y = -cos_t + 0.5f * cos_3t;
    float z = cos_t  * cos_3t;

    float norm = sqrtf(x*x + y*y + z*z);
    if (norm < 1e-6f) norm = 1.0f;

    return (VivianNormal){ x/norm, y/norm, z/norm };
}

typedef struct {
    uint64_t primary;
    uint64_t shadow;
} ShadowPair;

VIVIANI_HOST_DEVICE uint64_t compute_invariant(const uint8_t* data, size_t size) {
    uint64_t inv = 0;
    const uint64_t* ptr = (const uint64_t*)data;
    size_t words = size / sizeof(uint64_t);
    for (size_t i = 0; i < words; i++) inv ^= ptr[i];
    inv ^= (inv >> 32);
    inv ^= (inv >> 16);
    inv ^= (inv >> 8);
    return inv;
}
