/* Tiny oracle driver: fixed inputs -> printable outputs.
 * Build with gcc AND musl-gcc, diff the stdout. */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "v8_slice.c"

int main(void) {
    uint8_t buf[256];
    for (int i = 0; i < 256; i++) buf[i] = (uint8_t)(i * 2654435761u >> 16);

    printf("invariant=%.16llx\n",
           (unsigned long long)compute_invariant(buf, sizeof buf));

    for (int k = 0; k < 4; k++) {
        VivianNormal n = viviani_normal(0.5f * (float)k);
        uint32_t xb, yb, zb;
        memcpy(&xb, &n.x, 4); memcpy(&yb, &n.y, 4); memcpy(&zb, &n.z, 4);
        printf("normal[%d]=%08x %08x %08x\n", k, xb, yb, zb);
    }
    return 0;
}
