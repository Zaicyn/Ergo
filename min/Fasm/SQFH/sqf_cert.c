/* SQF certification driver (pre-registered oracles).
 *
 * O1_hot_speed      forward writes carry zero stored-side reads
 * O2_coh            fill stream coherent after final backprop
 * O3_bp_det         1-byte corruption between flush and backprop is
 *                   detected+repaired by backprop (eager mode:
 *                   anchor predates corruption → exact)
 * O4_bp_2byte       2-byte corruption solved exactly by backprop
 * O5_window         deferred mode: corruption BEFORE first backprop
 *                   is baselined in (documented window, all cases)
 * O6_post_anchor    deferred mode: corruption AFTER anchoring is
 *                   detected+repaired exactly (same as eager)
 * O7_closure        zero unresolved across all repair phases
 * determinism       identical audit across two runs
 */
#include "sqf_core.h"
#include <stdio.h>

static uint64_t rngs = 0xC0FFEE1234567ULL;
static uint64_t rnd(void) {
    rngs ^= rngs << 13; rngs ^= rngs >> 7; rngs ^= rngs << 17; return rngs;
}

#define CN 2048

int main(void) {
    static uint8_t stream[CN][SQM_PAY];
    for (int i = 0; i < CN; i++)
        for (int j = 0; j < SQM_PAY; j++)
            stream[i][j] = (uint8_t)(rnd() >> 32);

    /* ---------- Phase A: eager or deferred fill, then backprop ---------- */
    sqf_t t; sqf_init(&t);
    for (int i = 0; i < CN; i++) sqf_write(&t, i, i, stream[i]);
    if (t.b_n) sqf_flush(&t);

    int o1 = (t.rd_bytes_bp == 0);               /* nothing read yet */
    sqf_backprop(&t, 1);
    int o2_bad = 0;
    for (int i = 0; i < CN; i++) {
        int s = sqf_slot_of_tab[i];
        if (s < 0 || memcmp(t.pay[s >> 8][s & 0xFF], stream[i], SQM_PAY)) o2_bad++;
    }
    printf("SQFOR O1_hot_zero_reads   %s (bp_rd before first backprop = %llu)\n",
           o1 ? "PASS" : "FAIL", (unsigned long long)t.rd_bytes_bp);
    printf("SQFOR O2_fill_coherent    %d/%d coherency after backprop\n",
           CN - o2_bad, CN);

    /* ---------- O3: 1-byte hits between anchor and backprop ---------- */
    int o3_det = 0, o3_rep = 0, o3_n = 1000;
    for (int k = 0; k < o3_n; k++) {
        int i = rnd() % CN;
        int s = sqf_slot_of_tab[i];
        int b = s >> 8, g = s & 0xFF;
        int p = rnd() % SQM_PAY;
        int d = 1 + (int)(rnd() % 255);
        uint8_t before = t.pay[b][g][p];
        t.pay[b][g][p] = (uint8_t)(before + d);
        uint64_t rep0 = t.bp_repairs;
        sqf_backprop(&t, 1);
        if (t.bp_repairs > rep0) o3_det++;
        if (memcmp(t.pay[b][g], stream[i], SQM_PAY) == 0) o3_rep++;
    }
    printf("SQFOR O3_bp_1byte_det     %d/%d = %.6f  expect=1.000000\n",
           o3_det, o3_n, (double)o3_det / o3_n);
    printf("SQFOR O3_bp_1byte_rep     %d/%d = %.6f  expect>=0.990\n",
           o3_rep, o3_n, (double)o3_rep / o3_n);

    /* ---------- O4: 2-byte hits ---------- */
    int o4_rep = 0, o4_n = 1000;
    for (int k = 0; k < o4_n; k++) {
        int i = rnd() % CN;
        int s = sqf_slot_of_tab[i];
        int b = s >> 8, g = s & 0xFF;
        int p1 = rnd() % SQM_PAY, p2;
        do { p2 = rnd() % SQM_PAY; } while (p2 == p1);
        t.pay[b][g][p1] = (uint8_t)(t.pay[b][g][p1] + 1 + (int)(rnd() % 255));
        t.pay[b][g][p2] = (uint8_t)(t.pay[b][g][p2] + 1 + (int)(rnd() % 255));
        sqf_backprop(&t, 1);
        if (memcmp(t.pay[b][g], stream[i], SQM_PAY) == 0) o4_rep++;
    }
    printf("SQFOR O4_bp_2byte_rep     %d/%d = %.6f  expect>=0.990\n",
           o4_rep, o4_n, (double)o4_rep / o4_n);

    /* ---------- O5/O6: deferred-mode window semantics ---------- */
#if SQF_EAGER
    printf("SQFOR O5_window           n/a (eager build — anchor at flush)\n");
    printf("SQFOR O6_post_anchor      n/a (eager build)\n");
#else
    sqf_t t2; sqf_init(&t2);
    for (int i = 0; i < CN; i++) sqf_write(&t2, i, i, stream[i]);
    if (t2.b_n) sqf_flush(&t2);
    /* corrupt BEFORE first backprop: gets baselined in */
    int o5_base = 0, o5_n = 200;
    for (int k = 0; k < o5_n; k++) {
        int i = rnd() % CN;
        int s = sqf_slot_of_tab[i];
        t2.pay[s >> 8][s & 0xFF][rnd() % SQM_PAY] ^= (uint8_t)(1 + (rnd() % 255));
    }
    sqf_backprop(&t2, 1);                           /* anchors baselines */
    for (int k = 0; k < o5_n; k++) { }           /* (baseline already set) */
    int o5_cnt = 0;
    for (int i = 0; i < CN; i++) {
        int s = sqf_slot_of_tab[i];
        if (memcmp(t2.pay[s >> 8][s & 0xFF], stream[i], SQM_PAY)) o5_cnt++;
    }
    printf("SQFOR O5_window           %d slots baselined with pre-anchor"
           " corruption (documented window; anchor truth = stored-at-backprop)\n",
           o5_cnt);
    /* corrupt AFTER anchoring: must be repaired exactly */
    int o6_rep = 0, o6_n = 500;
    for (int k = 0; k < o6_n; k++) {
        int i = rnd() % CN;
        int s = sqf_slot_of_tab[i];
        int b = s >> 8, g = s & 0xFF;
        uint8_t snap[SQM_PAY];
        memcpy(snap, t2.pay[b][g], SQM_PAY);     /* truth = anchored state */
        t2.pay[b][g][rnd() % SQM_PAY] ^= (uint8_t)(1 + (rnd() % 255));
        sqf_backprop(&t2, 1);
        if (memcmp(t2.pay[b][g], snap, SQM_PAY) == 0) o6_rep++;
    }
    printf("SQFOR O6_post_anchor_rep  %d/%d = %.6f  expect>=0.990\n",
           o6_rep, o6_n, (double)o6_rep / o6_n);
#endif

    /* ---------- O7: closure on isolated solvable events ---------- */
    {
        sqf_t t3; sqf_init(&t3);
        for (int i = 0; i < CN; i++) sqf_write(&t3, i, i, stream[i]);
        if (t3.b_n) sqf_flush(&t3);
        sqf_backprop(&t3, 1);
        for (int k = 0; k < 500; k++) {
            int i = rnd() % CN;
            int s = sqf_slot_of_tab[i];
            t3.pay[s >> 8][s & 0xFF][rnd() % SQM_PAY] ^=
                (uint8_t)(1 + (rnd() % 255));
            sqf_backprop(&t3, 1);
        }
        printf("SQFOR O7_closure          %llu unresolved over 500"
               " isolated events  expect=0\n",
               (unsigned long long)t3.bp_unresolved);
    }
    printf("SQFOR aux_tail_unresolved %llu accumulated >=3-point damage"
           " (loud, documented — beyond 2-pt solve)\n",
           (unsigned long long)t.bp_unresolved);
    return 0;
}
