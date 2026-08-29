/* dump.c — bit-exact dump harness for the owned math kernels.
 *
 * Reads lines "func hexbits [hexbits2]" on stdin:
 *   func: sin cos exp log atan2 pow (f64) or sinf cosf expf logf
 *         atan2f powf (f32)
 *   hexbits: input value as raw f64 (16 hex) or f32 (8 hex) bits
 * Writes "func in_bits [in2_bits] out_bits" — out as raw bits.
 * Pure bit plumbing: no float text parsing anywhere on the path.
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "ergo_math_kernels.h"

static double d64(uint64_t u) { double d; memcpy(&d, &u, 8); return d; }
static uint64_t b64(double d) { uint64_t u; memcpy(&u, &d, 8); return u; }
static float f32(uint32_t u) { float f; memcpy(&f, &u, 4); return f; }
static uint32_t b32(float f) { uint32_t u; memcpy(&u, &f, 4); return u; }

int main(void) {
    char fn[16];
    unsigned long long a, b;
    while (scanf("%15s", fn) == 1) {
        int two = (fn[0] == 'a' || fn[0] == 'p');   /* atan2/pow take 2 */
        if (scanf("%llx", &a) != 1) return 1;
        if (two && scanf("%llx", &b) != 1) return 1;
        if (fn[strlen(fn) - 1] == 'f') {
            uint32_t r = 0;
            float x = f32((uint32_t)a), y = two ? f32((uint32_t)b) : 0;
#ifdef ERGO_HAVE_F32
            if (!strcmp(fn, "sinf")) r = b32(_ergo_sinf(x));
            else if (!strcmp(fn, "cosf")) r = b32(_ergo_cosf(x));
            else if (!strcmp(fn, "expf")) r = b32(_ergo_expf(x));
            else if (!strcmp(fn, "logf")) r = b32(_ergo_logf(x));
#ifdef ERGO_HAVE_POWF
            else if (!strcmp(fn, "powf")) r = b32(_ergo_powf(x, y));
#endif
            else if (!strcmp(fn, "atan2f")) r = b32(_ergo_atan2f(x, y));
#else
            if (0) {}
#endif
            else return 1;
            printf("%s %08x", fn, (unsigned)a);
            if (two) printf(" %08x", (unsigned)b);
            printf(" %08x\n", r);
        } else {
            uint64_t r = 0;
            double x = d64(a), y = two ? d64(b) : 0;
            if (!strcmp(fn, "sin")) r = b64(_ergo_sin(x));
            else if (!strcmp(fn, "cos")) r = b64(_ergo_cos(x));
            else if (!strcmp(fn, "exp")) r = b64(_ergo_exp(x));
            else if (!strcmp(fn, "log")) r = b64(_ergo_log(x));
#ifdef ERGO_HAVE_POW
            else if (!strcmp(fn, "pow")) r = b64(_ergo_pow(x, y));
#endif
            else if (!strcmp(fn, "atan2")) r = b64(_ergo_atan2(x, y));
            else return 1;
            printf("%s %016llx", fn, a);
            if (two) printf(" %016llx", b);
            printf(" %016llx\n", (unsigned long long)r);
        }
    }
    return 0;
}
