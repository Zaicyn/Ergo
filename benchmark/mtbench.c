/* mtbench.c -- multithreaded alloc scaling: glibc vs tcmalloc vs pools.
 * Build twice (glibc default, -ltcmalloc). Threads T in {1,2,4,6,8,12},
 * M ops/thread of 64 B, barrier start, wall time, best-of-3. Modes:
 *   churn   per-thread malloc/free (thread caches engage on their own)
 *   shard   per-thread PRIVATE pool: ring claim + invariant stamp write
 *           (SQ4-style claim path, C model: no locks, no sharing)
 *   shared  ONE pool + pthread_mutex around the same claim (lock cost)
 * Pool slot: 16 B (4 B invariant stamp + occupancy + pad); claim =
 * advance head, write stamp, set occupied; 4096-slot ring recycles.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <pthread.h>

#define MOPS 2000000L
#define ROUNDS 3
#define POOLN 4096

typedef struct {
    unsigned invar;
    unsigned char occ;
    unsigned char pad[11];
} slot_t; /* 16 B */

typedef struct {
    slot_t slots[POOLN];
    unsigned head;
    unsigned gen;
} pool_t;

static pool_t *shard_pools;
static pool_t shared_pool;
static pthread_mutex_t shared_mx = PTHREAD_MUTEX_INITIALIZER;
static pthread_barrier_t bar;
static int nthreads, mode;
static double *telapsed;
static long *opsdone;

static double now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1e9 + (double)ts.tv_nsec;
}
/* claim one slot: head advance + position stamp + occupy. Returns stamp. */
static inline unsigned pool_claim(pool_t *p, int tid) {
    unsigned h = p->head;
    unsigned stamp = (unsigned)(tid + 1) * 0x1000000u + p->gen * 4096u + h;
    p->slots[h].invar = stamp;
    p->slots[h].occ = 1;
    h++;
    if (h >= POOLN) {
        h = 0;
        p->gen++;
    }
    p->head = h;
    return stamp;
}
static void *worker(void *arg) {
    long tid = (long)arg;
    unsigned long acc = 0;
    pthread_barrier_wait(&bar);
    double t0 = now_ns();
    if (mode == 0) {
        for (long i = 0; i < MOPS; i++) {
            void *p = malloc(64);
            *(volatile unsigned long *)p = (unsigned long)i;
            free(p);
        }
        acc = MOPS;
    } else if (mode == 1) {
        pool_t *pp = &shard_pools[tid];
        for (long i = 0; i < MOPS; i++)
            acc += pool_claim(pp, (int)tid);
    } else {
        for (long i = 0; i < MOPS; i++) {
            pthread_mutex_lock(&shared_mx);
            acc += pool_claim(&shared_pool, (int)tid);
            pthread_mutex_unlock(&shared_mx);
        }
    }
    double dt = now_ns() - t0;
    telapsed[tid] = dt;
    opsdone[tid] = acc ? MOPS : 0;
    return NULL;
}
static double run(int t, int m) {
    double best = 0; /* max throughput */
    nthreads = t;
    mode = m;
    for (int r = 0; r < ROUNDS; r++) {
        if (m == 1) {
            for (int i = 0; i < t; i++) {
                memset(&shard_pools[i], 0, sizeof(pool_t));
            }
        } else if (m == 2) {
            memset(&shared_pool, 0, sizeof shared_pool);
        }
        pthread_barrier_init(&bar, NULL, t + 1);
        pthread_t *th = malloc(sizeof(pthread_t) * (size_t)t);
        for (int i = 0; i < t; i++)
            pthread_create(&th[i], NULL, worker, (void *)(long)i);
        pthread_barrier_wait(&bar);
        double t0 = now_ns();
        for (int i = 0; i < t; i++)
            pthread_join(th[i], NULL);
        double wall = now_ns() - t0;
        free(th);
        pthread_barrier_destroy(&bar);
        long tot = 0;
        for (int i = 0; i < t; i++)
            tot += opsdone[i];
        if (tot != (long)t * MOPS) {
            printf("MISMATCH t=%d mode=%d tot=%ld\n", t, m, tot);
            continue;
        }
        double ops = (double)t * MOPS / (wall / 1e9); /* ops/s */
        if (ops > best)
            best = ops;
    }
    return best / 1e6; /* Mops/s */
}
int main(void) {
    shard_pools = malloc(sizeof(pool_t) * 12);
    telapsed = malloc(sizeof(double) * 12);
    opsdone = malloc(sizeof(long) * 12);
    const int ts[] = { 1, 2, 4, 6, 8, 12 };
    const char *mn[] = { "churn", "shard", "shared" };
    printf("mode/threads: Mops/s (best-of-3), efficiency in ()\n");
    for (int m = 0; m < 3; m++) {
        double base = 0;
        printf("%-6s:", mn[m]);
        for (int i = 0; i < 6; i++) {
            double v = run(ts[i], m);
            if (!i)
                base = v;
            printf(" %7.1f(%4.2f)", v, v / base / ts[i] * ts[0]);
            fflush(stdout);
        }
        printf("\n");
    }
    return 0;
}
