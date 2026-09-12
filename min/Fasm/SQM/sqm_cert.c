/* sqm_cert.c — SQM certification driver.
 *
 * Pre-registered oracles:
 *   O1 skip exactness: identical rewrites skip, content stays exact.
 *   O2 diff-write correctness: 1/2-byte mutations -> stored == incoming
 *      exactly AND journal == recompute (closure), 100%.
 *   O3 amplification: measured bytes read/written per write class.
 *   O4 sweep det/rep after payload/journal corruption (counting/meas).
 *   O5 blindness retreat: 4-point quads (blind to SQ5) are now CAUGHT
 *      by s3; 5-point (1,-4,6,-4,1) patterns are the mapped blind class.
 *   O6 hot-path window (documented): stored-payload corruption + a
 *      pure-skip write is invisible until sweep — measured, accepted.
 *   O7 byte determinism.
 *
 * Build: gcc -O2 -o sqm_cert sqm_cert.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "common.h"
#include "sqm_core.h"

#define CN 256

static void build(sqm_cell_t *t, uint8_t contents[][SQM_PAY]) {
    sqm_init(t);
    for (int i = 0; i < CN; i++) {
        sqm_fill(contents[i], i);
        sqm_write(t, i, i, contents[i]);
    }
}

int main(int argc, char **argv) {
    int rounds = (argc > 1) ? atoi(argv[1]) : 1000;
    uint64_t rng[4];
    cmp_seed(rng, 0xCE27U);

    static sqm_cell_t cell;
    static uint8_t contents[CN][SQM_PAY];
    build(&cell, contents);

    /* ---- O1: pure-skip rewrites ---- */
    long long o1_ok = 0;
    for (int i = 0; i < CN; i++) {
        long long b4r = cell.bytes_read, b4w = cell.bytes_written;
        sqm_write(&cell, i, i, contents[i]);
        o1_ok += (cell.bytes_read == b4r && cell.bytes_written == b4w &&
                  memcmp(cell.pay[sqm_slot_of[i] >> 8][sqm_slot_of[i] & 0xFF],
                         contents[i], SQM_PAY) == 0);
    }

    /* ---- O2/O3: 1-byte and 2-byte diff writes ---- */
    long long o2_ok = 0, o2_n = 0;
    long long rd1 = 0, wr1 = 0, n1 = 0, rd2 = 0, wr2 = 0, n2 = 0;
    for (int r = 0; r < rounds; r++) {
        int i = (int)(cmp_rand_u32(rng) % CN);
        int nmut = (r & 1) ? 2 : 1;
        long long b4r = cell.bytes_read, b4w = cell.bytes_written;
        for (int k = 0; k < nmut; k++) {
            int pos = (int)(cmp_rand_u32(rng) % SQM_PAY);
            contents[i][pos] ^= (uint8_t)(1 + (cmp_rand_u32(rng) % 255));
        }
        sqm_write(&cell, i, i, contents[i]);
        int b = sqm_slot_of[i] >> 8, g = sqm_slot_of[i] & 0xFF;
        int ok = (memcmp(cell.pay[b][g], contents[i], SQM_PAY) == 0);
        sqm_mom_t chk;
        sqm_mom(cell.pay[b][g], 0, SQM_PAY, &chk);
        ok = ok && sqm_mom_eq(&chk, &cell.root[b][g]);
        o2_ok += ok; o2_n++;
        if (nmut == 1) { rd1 += cell.bytes_read - b4r; wr1 += cell.bytes_written - b4w; n1++; }
        else           { rd2 += cell.bytes_read - b4r; wr2 += cell.bytes_written - b4w; n2++; }
    }

    /* ---- O4: corruption + sweep ---- */
    long long o4_det = 0, o4_rep = 0, o4_n = 0, o4_unres = 0;
    static sqm_cell_t snap;
    static uint8_t csnap[CN][SQM_PAY];
    memcpy(&snap, &cell, sizeof(sqm_cell_t));
    memcpy(csnap, contents, sizeof(csnap));
    static int slot_snap[SQM_CAPACITY * 4];
    memcpy(slot_snap, sqm_slot_of, sizeof(slot_snap));
    for (int r = 0; r < rounds; r++) {
        memcpy(&cell, &snap, sizeof(sqm_cell_t));
        memcpy(contents, csnap, sizeof(csnap));
        memcpy(sqm_slot_of, slot_snap, sizeof(slot_snap));
        /* one payload byte in a random occupied slot */
        int b = (int)(cmp_rand_u32(rng) % SQM_NB);
        int g = (int)(cmp_rand_u32(rng) % SQM_NR);
        int pos = (int)(cmp_rand_u32(rng) % SQM_PAY);
        uint8_t m = (uint8_t)(1 + (cmp_rand_u32(rng) % 255));
        cell.pay[b][g][pos] ^= m;
        static uint8_t action[SQM_NB * SQM_NR];
        long long un = sqm_sweep(&cell, action);
        o4_unres += un;
        o4_det += (action[b * SQM_NR + g] != 0);
        /* repaired = stored content back to the snapshot truth */
        int item = sqm_item_at[b][g];
        o4_rep += (memcmp(cell.pay[b][g], csnap[item], SQM_PAY) == 0);
        o4_n++;
    }
    memcpy(&cell, &snap, sizeof(sqm_cell_t));
    memcpy(contents, csnap, sizeof(csnap));
    memcpy(sqm_slot_of, slot_snap, sizeof(slot_snap));

    /* ---- O5: blindness retreat ----
     * 4-point (1,-3,3,-1): blind to 3 moments, must now be CAUGHT by s3.
     * 5-point (1,-4,6,-4,1): preserves s0..s3 — the mapped blind class. */
    long long quad_caught = 0, quad_n = 0, pent_blind = 0, pent_n = 0;
    for (int b = 0; b < SQM_NB; b++)
        for (int g = 0; g < SQM_NR; g++) {
            uint8_t *pay = cell.pay[b][g];
            for (int o = 0; o + 4 < SQM_PAY; o++) {
                /* quad: positions o..o+3 */
                if (quad_n < 2000 &&
                    (int)pay[o] + 1 <= 255 && (int)pay[o + 1] >= 3 &&
                    (int)pay[o + 2] + 3 <= 255 && (int)pay[o + 3] >= 1) {
                    sqm_mom_t before, after, D;
                    sqm_mom(pay, 0, SQM_PAY, &before);
                    pay[o] += 1; pay[o + 1] -= 3; pay[o + 2] += 3; pay[o + 3] -= 1;
                    sqm_mom(pay, 0, SQM_PAY, &after);
                    for (int k = 0; k < 4; k++) D.s[k] = after.s[k] - before.s[k];
                    quad_caught += !sqm_mom_eq(&D, &(sqm_mom_t){0});
                    quad_n++;
                    pay[o] -= 1; pay[o + 1] += 3; pay[o + 2] -= 3; pay[o + 3] += 1;
                }
                /* pent: positions o..o+4 */
                if (pent_n < 2000 &&
                    (int)pay[o] + 1 <= 255 && (int)pay[o + 1] >= 4 &&
                    (int)pay[o + 2] + 6 <= 255 && (int)pay[o + 3] >= 4 &&
                    (int)pay[o + 4] + 1 <= 255) {
                    sqm_mom_t before, after;
                    sqm_mom(pay, 0, SQM_PAY, &before);
                    pay[o] += 1; pay[o + 1] -= 4; pay[o + 2] += 6;
                    pay[o + 3] -= 4; pay[o + 4] += 1;
                    sqm_mom(pay, 0, SQM_PAY, &after);
                    pent_blind += sqm_mom_eq(&before, &after);
                    pent_n++;
                    pay[o] -= 1; pay[o + 1] += 4; pay[o + 2] -= 6;
                    pay[o + 3] += 4; pay[o + 4] -= 1;
                }
            }
        }

    /* ---- O6: hot-path window — corrupted stored payload + pure skip ---- */
    long long o6_blind = 0, o6_n = 0;
    memcpy(&snap, &cell, sizeof(sqm_cell_t));
    for (int r = 0; r < 200; r++) {
        memcpy(&cell, &snap, sizeof(sqm_cell_t));
        int i = (int)(cmp_rand_u32(rng) % CN);
        int b = sqm_slot_of[i] >> 8, g = sqm_slot_of[i] & 0xFF;
        int pos = (int)(cmp_rand_u32(rng) % SQM_PAY);
        cell.pay[b][g][pos] ^= (uint8_t)(1 + (cmp_rand_u32(rng) % 255));
        /* caller rewrites the SAME (correct) content -> journal matches
         * -> skip -> stale corrupted bytes persist unseen until sweep */
        sqm_write(&cell, i, i, contents[i]);
        o6_blind += (memcmp(cell.pay[b][g], contents[i], SQM_PAY) != 0);
        o6_n++;
    }
    memcpy(&cell, &snap, sizeof(sqm_cell_t));

    printf("SQMOR O1_skip_exact    %lld/%d = %.6f  expect=1.000000 (0 rd 0 wr)\n",
           o1_ok, CN, (double)o1_ok / CN);
    printf("SQMOR O2_diff_correct  %lld/%lld = %.6f  expect=1.000000 (content+journal closure)\n",
           o2_ok, o2_n, o2_n ? (double)o2_ok / o2_n : 0.0);
    printf("SQMOR O3_amplification 1-byte: %.2f rd %.2f wr | 2-byte: %.2f rd %.2f wr (bytes/write)\n",
           n1 ? (double)rd1 / n1 : 0.0, n1 ? (double)wr1 / n1 : 0.0,
           n2 ? (double)rd2 / n2 : 0.0, n2 ? (double)wr2 / n2 : 0.0);
    printf("SQMOR O4_sweep_det     %lld/%lld = %.6f  expect=1.000000 counting\n",
           o4_det, o4_n, o4_n ? (double)o4_det / o4_n : 0.0);
    printf("SQMOR O4_sweep_rep     %lld/%lld = %.6f  expect>=0.990 measurement\n",
           o4_rep, o4_n, o4_n ? (double)o4_rep / o4_n : 0.0);
    printf("SQMOR O4_unresolved    %lld  expect=0\n", o4_unres);
    printf("SQMOR O5_quad_caught   %lld/%lld = %.6f  expect=1.000000 (blind to SQ5, caught by s3)\n",
           quad_caught, quad_n, quad_n ? (double)quad_caught / quad_n : 0.0);
    printf("SQMOR O5_pent_blind    %lld/%lld = %.6f  expect=1.000000 documented-exclusion\n",
           pent_blind, pent_n, pent_n ? (double)pent_blind / pent_n : 0.0);
    printf("SQMOR O6_skip_window   %lld/%lld stale-after-skip  expect=all-stale documented-window (sweep closes it)\n",
           o6_blind, o6_n);
    return 0;
}
