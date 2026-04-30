/*
 * ergo_oracle.c — Multi-client oracle server for Ergo galaxy simulation
 *
 * Receives: CENSUS (~96 bytes pre-reduced stats) + VERIFY (672 bytes probe)
 * Sends:    SPAWN commands (spawn count + next interval + flags)
 *
 * Supports up to 16 GPU clients simultaneously. Each client gets independent
 * regime classification and spawn control. The oracle also tracks aggregate
 * state across all clients for global decisions.
 *
 * Pure decision logic on reduced statistics. No physics, no particle arrays.
 * Runs on a Pi or any machine with UDP.
 *
 * Usage: ./ergo_oracle [port]    (default: 4242)
 *
 * Build: cc -O2 -o ergo_oracle ergo_oracle.c -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <math.h>
#include <time.h>

/* Pull in the transport layer */
#include "../mcl/runtime/ergo_net.h"

/* ========================================================================
 * REGIME CLASSIFICATION — per-client Eulerian aggregator
 * ======================================================================== */

#define CENSUS_INTERVAL_MIN     50
#define CENSUS_INTERVAL_MAX     2000
#define CENSUS_INTERVAL_DEFAULT 500

#define SPAWN_BASE_RATE  10     /* particles per spawn event */
#define SPAWN_MAX_RATE   100
#define POP_TARGET       50000  /* target alive population per client */

typedef struct {
    /* Previous census values for drift computation */
    double prev_omega_max;
    double prev_omega_mean;
    int    prev_crystal;
    int    prev_nova;
    double prev_spread;
    int    prev_frame;

    /* Regime state */
    const char* regime;
    int    interval;
    int    initialized;

    /* Verify state */
    int    last_verify_frame;

    /* Client identity */
    struct sockaddr_in addr;
    socklen_t addr_len;
    int    active;              /* has this slot received a packet? */
    uint32_t spawn_id;         /* per-client spawn command counter */

    /* Last census snapshot (for aggregate view) */
    ergo_census_t last_census;

    /* Field receive state */
    ergo_field_rx_t field_rx;
    int    field_ready;         /* this client's grid is complete for current round */

    /* Trust score: 0.0 = untrusted, 1.0 = fully trusted.
     * Affects weight in density grid consensus. Decays on deviation,
     * recovers slowly on consistent behavior. */
    float  trust;
} ClientState;

/* Aggregate state across all clients */
typedef struct {
    int    n_clients;
    int    total_alive;
    int    total_nova;
    int    total_crystal;
    double global_omega_max;
    double omega_mean;      /* mean of per-client omega_max */
    double omega_stddev;    /* stddev of per-client omega_max */
    double alive_mean;      /* mean alive count across clients */
    double alive_stddev;
    const char* global_regime;
} AggregateState;

static void client_init(ClientState* cs) {
    memset(cs, 0, sizeof(*cs));
    cs->regime = "COLD";
    cs->interval = CENSUS_INTERVAL_DEFAULT;
    cs->trust = 1.0f;
}

static void aggregate_compute(AggregateState* agg, ClientState clients[],
                              int max_clients) {
    memset(agg, 0, sizeof(*agg));
    agg->global_regime = "COLD";

    /* Pass 1: sums */
    double omega_sum = 0, alive_sum = 0;
    for (int i = 0; i < max_clients; i++) {
        if (!clients[i].active) continue;
        agg->n_clients++;
        agg->total_alive += (int)clients[i].last_census.alive;
        agg->total_nova += (int)clients[i].last_census.nova;
        agg->total_crystal += (int)clients[i].last_census.crystal;
        if (clients[i].last_census.omega_max > agg->global_omega_max)
            agg->global_omega_max = clients[i].last_census.omega_max;
        omega_sum += clients[i].last_census.omega_max;
        alive_sum += (double)clients[i].last_census.alive;
    }

    if (agg->n_clients > 0) {
        agg->omega_mean = omega_sum / agg->n_clients;
        agg->alive_mean = alive_sum / agg->n_clients;
    }

    /* Pass 2: variance */
    double omega_var = 0, alive_var = 0;
    for (int i = 0; i < max_clients; i++) {
        if (!clients[i].active) continue;
        double d = clients[i].last_census.omega_max - agg->omega_mean;
        omega_var += d * d;
        double da = (double)clients[i].last_census.alive - agg->alive_mean;
        alive_var += da * da;
    }
    if (agg->n_clients > 1) {
        agg->omega_stddev = sqrt(omega_var / (agg->n_clients - 1));
        agg->alive_stddev = sqrt(alive_var / (agg->n_clients - 1));
    }

    /* Global regime from worst-case omega */
    if (agg->global_omega_max > 0.3)
        agg->global_regime = "WARMING";
    else if (agg->global_omega_max > 0.1)
        agg->global_regime = "RISING";
    else if (agg->global_omega_max < 0.01)
        agg->global_regime = "COLD";
    else
        agg->global_regime = "STABLE";
}

/*
 * trust_update — adjust client trust based on census deviation
 *
 * Checks multiple signals against the aggregate. Each violation
 * decays trust; consistent behavior slowly recovers it.
 * Called after aggregate_compute, before oracle_decide.
 */
static void trust_update(ClientState* cs, const ergo_census_t* c,
                         const AggregateState* agg) {
    if (agg->n_clients < 2) return;  /* can't measure deviation with 1 client */

    float decay = 1.0f;

    /* Signal 1: omega_max deviation from group mean (3-sigma outlier) */
    if (agg->omega_stddev > 1e-6) {
        float dev = (float)fabs(c->omega_max - agg->omega_mean)
                  / (float)(agg->omega_stddev + 1e-6);
        if (dev > 3.0f) decay *= 0.9f;
    }

    /* Signal 2: alive count deviation from group mean (2-sigma) */
    if (agg->alive_stddev > 1.0) {
        float dev = (float)fabs((double)c->alive - agg->alive_mean)
                  / (float)(agg->alive_stddev + 1e-6);
        if (dev > 2.0f) decay *= 0.95f;
    }

    /* Signal 3: physics bounds — omega can't exceed OMEGA_MAX (2.0) */
    if (c->omega_max > 2.5) decay *= 0.8f;

    /* Signal 4: density grid mass vs reported alive count.
     * Each alive particle contributes 1.0 to total density.
     * If grid is complete, check consistency. */
    if (cs->field_ready) {
        float grid_mass = 0;
        for (int j = 0; j < ERGO_FIELD_GRID_CELLS; j++)
            grid_mass += cs->field_rx.grid[j];
        float expected = (float)c->alive;
        if (expected > 10.0f) {
            float mass_ratio = grid_mass / expected;
            /* Mass should be close to alive count (within 50%) */
            if (mass_ratio < 0.5f || mass_ratio > 1.5f) decay *= 0.85f;
        }
    }

    /* Signal 5: evolution consistency — crystal count can't decrease */
    if (cs->initialized && (int)c->crystal < cs->prev_crystal) {
        decay *= 0.95f;
    }

    /* Signal 6: rate-of-change bounds — omega can't jump more than 2.0/frame */
    if (cs->initialized && cs->prev_frame > 0) {
        int dt = (int)c->frame - cs->prev_frame;
        if (dt > 0) {
            double d_omega = fabs(c->omega_max - cs->prev_omega_max) / dt;
            if (d_omega > 2.0) decay *= 0.9f;
        }
    }

    /* Apply decay or recovery */
    if (decay < 1.0f) {
        cs->trust *= decay;
        if (cs->trust < 0.01f) cs->trust = 0.01f;  /* floor: never fully zero */
    } else {
        cs->trust *= 1.01f;  /* slow recovery: ~100 census rounds to full trust */
        if (cs->trust > 1.0f) cs->trust = 1.0f;
    }
}

/*
 * oracle_decide — per-client regime classification + spawn decision
 *
 * Same logic as single-client, but aware of aggregate state.
 * Global WARMING can pause spawn on all clients.
 */
static ergo_spawn_t oracle_decide(ClientState* cs, const ergo_census_t* c,
                                  uint32_t frame, const AggregateState* agg) {
    ergo_spawn_t sp = {0};
    int interval = CENSUS_INTERVAL_DEFAULT;

    if (cs->initialized) {
        int dt = (int)frame - cs->prev_frame;
        if (dt > 0) {
            double d_omega_max = (c->omega_max - cs->prev_omega_max) / dt;
            double d_crystal = (double)((int)c->crystal - cs->prev_crystal) / dt;

            /* Classify regime */
            if (c->omega_max > 0.3) {
                cs->regime = "WARMING";
                interval = CENSUS_INTERVAL_MIN;
            } else if (d_omega_max > 0.001) {
                cs->regime = "RISING";
                interval = CENSUS_INTERVAL_DEFAULT / 2;
            } else if (d_crystal > 0.1) {
                cs->regime = "CRYSTALLIZING";
                interval = CENSUS_INTERVAL_DEFAULT / 2;
            } else if (c->omega_max < 0.01 && d_omega_max <= 0.0) {
                cs->regime = "COLD";
                interval = CENSUS_INTERVAL_MAX;
            } else {
                cs->regime = "STABLE";
                interval = CENSUS_INTERVAL_DEFAULT;
            }

            /* Crystal spread convergence */
            if (cs->prev_spread > 0.0 && c->spread < cs->prev_spread - 5.0) {
                interval = CENSUS_INTERVAL_MIN;
            }
        }
    }

    /* Clamp interval */
    if (interval < CENSUS_INTERVAL_MIN) interval = CENSUS_INTERVAL_MIN;
    if (interval > CENSUS_INTERVAL_MAX) interval = CENSUS_INTERVAL_MAX;
    cs->interval = interval;

    /* Spawn decision: per-client target */
    int alive = (int)c->alive;
    if (alive < POP_TARGET) {
        int deficit = POP_TARGET - alive;
        sp.spawn_count = deficit / 100;
        if (sp.spawn_count < SPAWN_BASE_RATE) sp.spawn_count = SPAWN_BASE_RATE;
        if (sp.spawn_count > SPAWN_MAX_RATE) sp.spawn_count = SPAWN_MAX_RATE;
    } else {
        sp.spawn_count = 0;
    }

    /* Global WARMING: pause spawn across all clients */
    if (agg->global_omega_max > 0.4 || c->omega_max > 0.4) {
        sp.spawn_count = 0;
        sp.flags |= 1;  /* bit 0 = pause spawn */
    }

    sp.next_census = (uint32_t)interval;

    /* Update persistent state */
    cs->prev_omega_max = c->omega_max;
    cs->prev_omega_mean = c->omega_mean;
    cs->prev_crystal = (int)c->crystal;
    cs->prev_nova = (int)c->nova;
    cs->prev_spread = c->spread;
    cs->prev_frame = (int)frame;
    cs->initialized = 1;
    cs->last_census = *c;

    return sp;
}

/* ========================================================================
 * FIELD REDUCTION — sum density grids across clients, broadcast global
 *
 * Called when all active clients have submitted their density grids.
 * The density field is a linear accumulation (scatter += 1.0 per particle),
 * so partial fields sum directly to the correct global field.
 * ======================================================================== */

static float global_field[ERGO_FIELD_GRID_CELLS];
static uint32_t field_broadcast_id = 0;

static void field_reduce_and_broadcast(ergo_net_t* net, ClientState clients[],
                                       int max_clients, uint32_t frame) {
    /* Trust-weighted consensus: global[cell] = sum(trust[i] * grid[i][cell]) / sum(trust[i])
     * A client with trust=0.1 contributes 10% of what a trust=1.0 client does.
     * This dampens hardware faults, divergent clients, or malicious actors. */
    memset(global_field, 0, sizeof(global_field));
    float trust_sum = 0;
    int n_contrib = 0;
    for (int i = 0; i < max_clients; i++) {
        if (!clients[i].active || !clients[i].field_ready) continue;
        float t = clients[i].trust;
        const float* src = clients[i].field_rx.grid;
        for (int j = 0; j < ERGO_FIELD_GRID_CELLS; j++)
            global_field[j] += t * src[j];
        trust_sum += t;
        n_contrib++;
    }

    if (n_contrib == 0) return;

    /* Normalize by trust sum */
    if (trust_sum > 0) {
        float inv_trust = 1.0f / trust_sum;
        for (int j = 0; j < ERGO_FIELD_GRID_CELLS; j++)
            global_field[j] *= inv_trust;
    }

    /* Find max for diagnostics */
    float field_max = 0;
    for (int j = 0; j < ERGO_FIELD_GRID_CELLS; j++)
        if (global_field[j] > field_max) field_max = global_field[j];

    printf("[field] reduced %d grids → global (max=%.1f, trust_sum=%.2f, frame=%u)\n",
           n_contrib, field_max, trust_sum, frame);

    /* Broadcast global field — multicast + unicast.
     * Multicast for O(1) on real networks; unicast as reliable fallback
     * (works on loopback, handles clients that can't join multicast). */
    field_broadcast_id++;
    if (net->mcast_sock >= 0) {
        ergo_net_send_field_mcast(net, frame, global_field,
                                  field_broadcast_id);
    }
    /* Always unicast too — reliable fallback */
    for (int i = 0; i < max_clients; i++) {
        if (!clients[i].active) continue;
        net->peer = clients[i].addr;
        net->peer_len = clients[i].addr_len;
        ergo_net_send_field(net, frame, global_field,
                            field_broadcast_id);
    }
    printf("[field] broadcast id=%u (%d chunks, mcast=%s, %d clients)\n",
           field_broadcast_id, ERGO_FIELD_NCHUNKS,
           net->mcast_sock >= 0 ? "yes" : "no", n_contrib);
    for (int i = 0; i < max_clients; i++)
        clients[i].field_ready = 0;
}

/* Check if all active clients have submitted their field */
static int all_fields_ready(ClientState clients[], int max_clients) {
    int n_active = 0, n_ready = 0;
    for (int i = 0; i < max_clients; i++) {
        if (!clients[i].active) continue;
        n_active++;
        if (clients[i].field_ready) n_ready++;
    }
    return (n_active > 0 && n_ready == n_active);
}

/* ========================================================================
 * MAIN — recvfrom loop with per-client dispatch
 * ======================================================================== */

static volatile int running = 1;

static void sighandler(int sig) {
    (void)sig;
    running = 0;
}

int main(int argc, char** argv) {
    int port = (argc > 1) ? atoi(argv[1]) : ERGO_PORT;

    ergo_net_t net;
    if (ergo_net_init(&net, NULL, port, 1, 0) < 0) {
        fprintf(stderr, "Failed to init oracle on port %d\n", port);
        return 1;
    }

    signal(SIGINT, sighandler);
    signal(SIGTERM, sighandler);

    ClientState clients[ERGO_MAX_GPUS];
    for (int i = 0; i < ERGO_MAX_GPUS; i++)
        client_init(&clients[i]);

    AggregateState agg = {0};

    /* Set up multicast sender for O(1) field broadcast */
    if (ergo_net_mcast_init_sender(&net) < 0) {
        printf("[oracle] multicast unavailable, falling back to unicast\n");
    }

    printf("[oracle] listening on port %d (multi-client, max %d)\n",
           port, ERGO_MAX_GPUS);

    while (running) {
        ergo_hdr_t hdr;
        uint8_t payload[2048];
        struct sockaddr_in sender;

        int type = ergo_net_recv(&net, &hdr, payload, sizeof(payload), &sender);
        if (type == 0) {
            usleep(1000);
            continue;
        }

        int gid = hdr.gpu_id;
        if (gid >= ERGO_MAX_GPUS) {
            printf("[oracle] ignoring gpu_id=%d (max %d)\n", gid, ERGO_MAX_GPUS);
            continue;
        }

        ClientState* cs = &clients[gid];

        /* First packet from this client — register it */
        if (!cs->active) {
            cs->active = 1;
            cs->addr = sender;
            cs->addr_len = sizeof(sender);
            printf("[oracle] client gpu=%d registered from %s:%d\n",
                   gid, inet_ntoa(sender.sin_addr), ntohs(sender.sin_port));
        }

        switch (type) {
        case ERGO_CENSUS: {
            if (hdr.payload_len < sizeof(ergo_census_t)) break;
            ergo_census_t c;
            memcpy(&c, payload, sizeof(c));

            printf("[census] gpu=%d frame=%u alive=%u/%u nova=%u crystal=%u "
                   "omega=(%.4f,%.4f) spread=%.1f\n",
                   gid, hdr.frame, c.alive, c.capacity, c.nova, c.crystal,
                   c.omega_mean, c.omega_max, c.spread);

            /* Recompute aggregate before deciding */
            cs->last_census = c;
            aggregate_compute(&agg, clients, ERGO_MAX_GPUS);

            /* Update trust score based on deviation from consensus */
            float prev_trust = cs->trust;
            trust_update(cs, &c, &agg);

            /* Per-client decision with global awareness */
            ergo_spawn_t sp = oracle_decide(cs, &c, hdr.frame, &agg);
            sp.spawn_id = ++cs->spawn_id;

            /* Send response back to this client */
            net.peer = sender;
            net.peer_len = sizeof(sender);
            ergo_net_send_spawn(&net, hdr.frame, &sp);

            printf("[spawn] -> gpu=%d count=%u interval=%u flags=0x%x "
                   "trust=%.3f%s [%d clients, %d alive, %s]\n",
                   gid, sp.spawn_count, sp.next_census, sp.flags,
                   cs->trust,
                   (cs->trust < prev_trust) ? " ↓" :
                   (cs->trust > prev_trust) ? " ↑" : "",
                   agg.n_clients, agg.total_alive, agg.global_regime);
            break;
        }

        case ERGO_VERIFY: {
            int nfields = hdr.payload_len / sizeof(double);
            printf("[verify] gpu=%d frame=%u payload=%u bytes (%d doubles)\n",
                   gid, hdr.frame, hdr.payload_len, nfields);
            cs->last_verify_frame = (int)hdr.frame;
            break;
        }

        case ERGO_FIELD: {
            int complete = ergo_field_rx_chunk(&cs->field_rx,
                                              payload, hdr.payload_len);
            if (complete && !cs->field_ready) {
                cs->field_ready = 1;
                printf("[field] gpu=%d grid complete (id=%u, frame=%u)\n",
                       gid, cs->field_rx.field_id, hdr.frame);
                /* Check if all clients ready for reduction */
                if (all_fields_ready(clients, ERGO_MAX_GPUS)) {
                    field_reduce_and_broadcast(&net, clients,
                                              ERGO_MAX_GPUS, hdr.frame);
                }
            }
            break;
        }

        case ERGO_REGISTER: {
            printf("[oracle] explicit register from gpu=%d\n", gid);
            break;
        }

        default:
            printf("[oracle] unknown packet type=%d from gpu=%d\n", type, gid);
            break;
        }
    }

    printf("[oracle] shutting down (%d clients served)\n", agg.n_clients);
    ergo_net_close(&net);
    return 0;
}
