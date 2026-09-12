/* cache_perf.h — lightweight Linux perf_event_open wrapper for cache metrics.
 *
 * Measures:
 *   - L1 data cache load accesses / misses
 *   - Last-level cache (LLC) references / misses
 *   - CPU cycles and instructions retired
 *
 * These counters are read around a benchmark phase so we can report hit
 * rates and memory locality characteristics of each allocator/streaming
 * system.  Requires Linux and either root or kernel.perf_event_paranoid <= 1.
 */

#ifndef CACHE_PERF_H
#define CACHE_PERF_H

#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <linux/perf_event.h>
#include <linux/hw_breakpoint.h>

#define CP_NCOUNTERS 5

typedef enum {
    CP_L1D_LOADS = 0,
    CP_L1D_MISSES,
    CP_LLC_REFS,
    CP_LLC_MISSES,
    CP_INSTRS
} cp_counter_t;

typedef struct {
    int fds[CP_NCOUNTERS];
    uint64_t after[CP_NCOUNTERS];
    int available;
} cp_ctx_t;

static inline long perf_event_open(struct perf_event_attr *hw,
                                    pid_t pid, int cpu, int group_fd,
                                    unsigned long flags) {
    return syscall(__NR_perf_event_open, hw, pid, cpu, group_fd, flags);
}

static inline int cp_open(cp_ctx_t *ctx) {
    memset(ctx, 0, sizeof(*ctx));
    ctx->available = 1;

    struct perf_event_attr attrs[CP_NCOUNTERS];
    memset(attrs, 0, sizeof(attrs));

    /* L1 data cache read accesses */
    attrs[CP_L1D_LOADS].type = PERF_TYPE_HW_CACHE;
    attrs[CP_L1D_LOADS].size = sizeof(struct perf_event_attr);
    attrs[CP_L1D_LOADS].config =
        (PERF_COUNT_HW_CACHE_L1D) |
        (PERF_COUNT_HW_CACHE_OP_READ << 8) |
        (PERF_COUNT_HW_CACHE_RESULT_ACCESS << 16);
    attrs[CP_L1D_LOADS].disabled = 1;
    attrs[CP_L1D_LOADS].exclude_kernel = 1;
    attrs[CP_L1D_LOADS].exclude_hv = 1;

    /* L1 data cache read misses */
    attrs[CP_L1D_MISSES].type = PERF_TYPE_HW_CACHE;
    attrs[CP_L1D_MISSES].size = sizeof(struct perf_event_attr);
    attrs[CP_L1D_MISSES].config =
        (PERF_COUNT_HW_CACHE_L1D) |
        (PERF_COUNT_HW_CACHE_OP_READ << 8) |
        (PERF_COUNT_HW_CACHE_RESULT_MISS << 16);
    attrs[CP_L1D_MISSES].disabled = 1;
    attrs[CP_L1D_MISSES].exclude_kernel = 1;
    attrs[CP_L1D_MISSES].exclude_hv = 1;

    /* LLC references / misses */
    attrs[CP_LLC_REFS].type = PERF_TYPE_HARDWARE;
    attrs[CP_LLC_REFS].size = sizeof(struct perf_event_attr);
    attrs[CP_LLC_REFS].config = PERF_COUNT_HW_CACHE_REFERENCES;
    attrs[CP_LLC_REFS].disabled = 1;
    attrs[CP_LLC_REFS].exclude_kernel = 1;
    attrs[CP_LLC_REFS].exclude_hv = 1;

    attrs[CP_LLC_MISSES].type = PERF_TYPE_HARDWARE;
    attrs[CP_LLC_MISSES].size = sizeof(struct perf_event_attr);
    attrs[CP_LLC_MISSES].config = PERF_COUNT_HW_CACHE_MISSES;
    attrs[CP_LLC_MISSES].disabled = 1;
    attrs[CP_LLC_MISSES].exclude_kernel = 1;
    attrs[CP_LLC_MISSES].exclude_hv = 1;

    /* instructions retired */
    attrs[CP_INSTRS].type = PERF_TYPE_HARDWARE;
    attrs[CP_INSTRS].size = sizeof(struct perf_event_attr);
    attrs[CP_INSTRS].config = PERF_COUNT_HW_INSTRUCTIONS;
    attrs[CP_INSTRS].disabled = 1;
    attrs[CP_INSTRS].exclude_kernel = 1;
    attrs[CP_INSTRS].exclude_hv = 1;

    /* Open all events independently; AMD Zen2 can count them simultaneously. */
    for (int i = 0; i < CP_NCOUNTERS; i++) {
        ctx->fds[i] = perf_event_open(&attrs[i], 0, -1, -1, 0);
        if (ctx->fds[i] < 0) {
            ctx->available = 0;
            for (int j = 0; j < i; j++) {
                if (ctx->fds[j] >= 0) close(ctx->fds[j]);
            }
            return -1;
        }
    }
    return 0;
}

static inline void cp_start(cp_ctx_t *ctx) {
    if (!ctx->available) return;
    for (int i = 0; i < CP_NCOUNTERS; i++) {
        ioctl(ctx->fds[i], PERF_EVENT_IOC_RESET, 0);
        ioctl(ctx->fds[i], PERF_EVENT_IOC_ENABLE, 0);
    }
}

static inline void cp_stop(cp_ctx_t *ctx) {
    if (!ctx->available) return;
    for (int i = 0; i < CP_NCOUNTERS; i++) {
        ioctl(ctx->fds[i], PERF_EVENT_IOC_DISABLE, 0);
        if (read(ctx->fds[i], &ctx->after[i], sizeof(uint64_t)) != sizeof(uint64_t)) {
            ctx->after[i] = 0;
        }
    }
}

static inline void cp_close(cp_ctx_t *ctx) {
    if (!ctx->available) return;
    for (int i = 0; i < CP_NCOUNTERS; i++) {
        if (ctx->fds[i] >= 0) close(ctx->fds[i]);
    }
}

#endif /* CACHE_PERF_H */
