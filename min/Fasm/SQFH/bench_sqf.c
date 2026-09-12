/* SQF bench: hot-path cost of forward-batched initial writes, with
 * occasional incremental backprop infill.  SQF_EAGER=1 (journal
 * anchored at flush) vs SQF_EAGER=0 (anchor deferred to backprop).
 *
 * 4096-slot fill per epoch, 25 epochs (cell reset between epochs;
 * ids reused).  Backprop every SQF_BP_EVERY batches (incremental:
 * scans only slots written since last pass) + one final full pass.
 */
#include "sqf_core.h"
#include <stdio.h>
#include <time.h>

#ifndef SQF_BP_EVERY
#define SQF_BP_EVERY 32
#endif

#define SQFN SQF_CAPACITY
#define EPOCHS 25

static uint64_t rngs = 0x9E3779B97F4A7C15ULL;
static uint64_t rnd(void) {
    rngs ^= rngs << 13; rngs ^= rngs >> 7; rngs ^= rngs << 17; return rngs;
}
static double now_ns(void) {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1e9 + ts.tv_nsec;
}

int main(void) {
    static uint8_t stream[SQFN][SQM_PAY];
    for (int i = 0; i < SQFN; i++)
        for (int j = 0; j < SQM_PAY; j++)
            stream[i][j] = (uint8_t)(rnd() >> 32);

    double hot = 0.0, bp = 0.0;
    uint64_t hot_wr = 0, bp_rd = 0, bp_wr = 0, scans = 0;
    int coh_bad = 0;

    for (int e = 0; e < EPOCHS; e++) {
        sqf_t t; sqf_init(&t);
        double t0 = now_ns();
        for (int i = 0; i < SQFN; i++) sqf_write(&t, i, i, stream[i]);
        if (t.b_n) sqf_flush(&t);
        hot += now_ns() - t0;
        int nb = SQFN / SQF_BATCH, done = 0;
        t0 = now_ns();
        while (done < nb) {
            int chunk = SQF_BP_EVERY < nb - done ? SQF_BP_EVERY : nb - done;
            (void)chunk;
            sqf_backprop(&t, 0);
            done += SQF_BP_EVERY;
        }
        sqf_backprop(&t, 1);
        bp += now_ns() - t0;
        hot_wr += t.wr_bytes_hot; bp_rd += t.rd_bytes_bp;
        bp_wr += t.wr_bytes_bp; scans += t.bp_scans;
        if (e == EPOCHS - 1)
            for (int i = 0; i < SQFN; i++) {
                int s = sqf_slot_of_tab[i];
                if (s < 0 || memcmp(t.pay[s >> 8][s & 0xFF], stream[i], SQM_PAY))
                    coh_bad++;
            }
    }

    double n = (double)SQFN * EPOCHS;
    fprintf(stderr,
        "SQFT eager=%d bp_every=%d | hot=%.2f bp=%.2f total=%.2f ns/item"
        " | hot_wr=%.1f bp_rd=%.2f bp_wr=%.3f B/item | scans/item=%.2f\n",
        SQF_EAGER, SQF_BP_EVERY, hot / n, bp / n, (hot + bp) / n,
        hot_wr / n, bp_rd / n, bp_wr / n, scans / n);
    printf("SQF eager=%d items=%.0f hot=%.2f bp=%.2f total=%.2f ns/item coh_fail=%d/%d\n",
           SQF_EAGER, n, hot / n, bp / n, (hot + bp) / n, coh_bad, SQFN);
    return 0;
}
