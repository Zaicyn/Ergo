/*
 * ergo_net.h — Minimal UDP transport for oracle ↔ GPU communication
 *
 * Pure C. POSIX sockets. No dependencies beyond libc.
 * Loss-tolerant, latest-wins, idempotent spawn commands.
 *
 * GPU → Oracle:  census reduction (~100 bytes, adaptive interval)
 * Oracle → GPU:  spawn count + next interval + flags (~16 bytes)
 *
 * The transport mirrors the physics: sparse, event-driven, compact.
 * The GPU pulses, the oracle gates.
 */
#ifndef ERGO_NET_H
#define ERGO_NET_H

#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/in.h>

/* ip_mreq may be hidden behind _GNU_SOURCE in strict C99 mode */
#ifndef IP_ADD_MEMBERSHIP
#define IP_ADD_MEMBERSHIP 35
#endif
#if !defined(__GLIBC__) || !defined(_GNU_SOURCE)
struct ergo_ip_mreq {
    struct in_addr imr_multiaddr;
    struct in_addr imr_interface;
};
#define ERGO_IP_MREQ struct ergo_ip_mreq
#else
#define ERGO_IP_MREQ struct ip_mreq
#endif

#define ERGO_MAGIC   0x4552   /* 'ER' */
#define ERGO_VERSION 1
#define ERGO_PORT    4242
#define ERGO_MAX_GPUS 16
#define ERGO_MCAST_GROUP "239.42.0.1"  /* field broadcast multicast group */
#define ERGO_MCAST_PORT  4243          /* separate port for multicast field */

/* ========================================================================
 * PACKET TYPES
 * ======================================================================== */

enum {
    ERGO_CENSUS   = 1,   /* GPU → Oracle: population statistics */
    ERGO_SPAWN    = 2,   /* Oracle → GPU: spawn command + interval */
    ERGO_VERIFY   = 3,   /* GPU → Oracle: Lagrangian probe (12 particles) */
    ERGO_SEED      = 4,   /* Oracle → GPU: simulation seed (init params) */
    ERGO_REGISTER  = 5,   /* GPU → Oracle: client registration (handshake) */
    ERGO_PROBE_SET = 6,   /* Oracle → GPU: random probe indices for next VERIFY */
    ERGO_FIELD     = 7,   /* Bidirectional: chunked density grid (128KB) */
    ERGO_FIELD_ACK = 8    /* Acknowledgement: field transfer complete */
};

/* ========================================================================
 * FIELD TRANSFER — chunked 128KB grid over UDP
 *
 * 32³ × f32 = 131072 bytes. At 1360 bytes/chunk = 97 packets.
 * Each chunk is self-describing (offset + length). Loss-tolerant:
 * receiver tracks which chunks arrived; missing chunks use local data.
 * ======================================================================== */

#define ERGO_FIELD_CHUNK_SIZE  1360   /* payload per chunk (fits in MTU) */
#define ERGO_FIELD_GRID_SIZE   32
#define ERGO_FIELD_GRID_CELLS  (32*32*32)  /* 32768 */
#define ERGO_FIELD_GRID_BYTES  (ERGO_FIELD_GRID_CELLS * sizeof(float))  /* 131072 */
#define ERGO_FIELD_NCHUNKS     ((ERGO_FIELD_GRID_BYTES + ERGO_FIELD_CHUNK_SIZE - 1) / ERGO_FIELD_CHUNK_SIZE)  /* 97 */

#pragma pack(push, 1)
typedef struct {
    uint32_t field_id;        /* monotonic transfer ID */
    uint16_t chunk_idx;       /* which chunk (0..96) */
    uint16_t n_chunks;        /* total chunks in this transfer */
    uint32_t byte_offset;     /* offset into grid data */
    uint16_t chunk_len;       /* bytes in this chunk */
    uint16_t _pad;
} ergo_field_chunk_t;         /* 16 bytes, followed by chunk data */
#pragma pack(pop)

/* Field receive state — tracks partial grid reassembly */
typedef struct {
    float    grid[ERGO_FIELD_GRID_CELLS];  /* reassembly buffer */
    uint32_t field_id;         /* current transfer being assembled */
    uint8_t  received[ERGO_FIELD_NCHUNKS]; /* bitmap of arrived chunks */
    int      n_received;       /* count of arrived chunks */
    int      complete;         /* all chunks arrived */
} ergo_field_rx_t;

/* ========================================================================
 * PACKET HEADER — 16 bytes, all packets start with this
 * ======================================================================== */

#pragma pack(push, 1)
typedef struct {
    uint16_t magic;       /* ERGO_MAGIC (network byte order) */
    uint8_t  type;        /* ERGO_CENSUS | ERGO_SPAWN | ERGO_VERIFY */
    uint8_t  version;     /* ERGO_VERSION */
    uint32_t frame;       /* simulation frame (network byte order) */
    uint32_t seq_id;      /* monotonic per sender (network byte order) */
    uint8_t  gpu_id;      /* sender GPU index (0-15) */
    uint8_t  _pad;
    uint16_t payload_len; /* bytes after header (network byte order) */
} ergo_hdr_t;
#pragma pack(pop)

/* ========================================================================
 * CENSUS PAYLOAD — GPU → Oracle (~96 bytes)
 *
 * Pre-reduced statistics. The GPU computes the reduction, the oracle
 * receives the summary. 96 bytes instead of 600KB raw readback.
 * ======================================================================== */

typedef struct {
    /* Population counts */
    uint32_t alive;
    uint32_t nova;
    uint32_t crystal;
    uint32_t ejected;
    uint32_t other;

    /* Omega statistics */
    double   omega_mean;
    double   omega_max;

    /* Crystal field */
    double   cx, cy, cz;  /* centroid */
    double   spread;

    /* Frame metadata */
    uint32_t frame;
    uint32_t sample_count; /* how many particles were sampled */
    uint32_t capacity;     /* VRAM-based max particles (for normalization) */
} ergo_census_t;

/* ========================================================================
 * SPAWN PAYLOAD — Oracle → GPU (16 bytes)
 * ======================================================================== */

typedef struct {
    uint32_t spawn_count;    /* how many particles to add */
    uint32_t spawn_id;       /* monotonic command ID (idempotent apply) */
    uint32_t next_census;    /* frames until next census readback */
    uint32_t flags;          /* bit 0=pause spawn, 1=force readback,
                                2=diagnostic mode, 3=shutdown */
} ergo_spawn_t;

/* ========================================================================
 * VERIFY PAYLOAD — GPU → Oracle
 *
 * 12 fixed shell particles + up to 8 random probe particles = 20 max.
 * Each particle: 7 doubles (px,py,pz,vx,vy,vz,omega) = 56 bytes.
 * Max payload: 20 × 56 = 1120 bytes (fits in one UDP packet).
 * ======================================================================== */

#define ERGO_VERIFY_SHELL  12   /* fixed cuboctahedral shell (indices 0-11) */
#define ERGO_VERIFY_RANDOM 8    /* random probe particles (server-selected) */
#define ERGO_VERIFY_NPART  (ERGO_VERIFY_SHELL + ERGO_VERIFY_RANDOM)  /* 20 total */
#define ERGO_VERIFY_FIELDS 7
#define ERGO_VERIFY_SIZE (ERGO_VERIFY_NPART * ERGO_VERIFY_FIELDS * sizeof(double))

/* ========================================================================
 * PROBE SET — Oracle → GPU (32 bytes)
 *
 * Server sends 8 random particle indices for the client to include
 * in its next VERIFY packet. Indices rotate each cycle — client can't
 * predict which particles will be checked.
 * ======================================================================== */

typedef struct {
    uint32_t indices[ERGO_VERIFY_RANDOM]; /* particle indices to probe */
} ergo_probe_set_t;

/* ========================================================================
 * REGISTER PAYLOAD — GPU → Oracle (8 bytes)
 *
 * Client announces itself. Server captures sockaddr, responds with SEED.
 * ======================================================================== */

typedef struct {
    uint8_t  gpu_id;          /* requested GPU slot (0-15) */
    uint8_t  _pad[3];
    uint32_t protocol_version; /* client's ERGO_VERSION */
} ergo_register_t;

/* ========================================================================
 * SEED PAYLOAD — Oracle → GPU (32 bytes)
 *
 * Only runtime-variable values. Compiled-in constants (BH_MASS, ISCO_R,
 * TANGENT LUT, FLOW_MODE LUT) are identical on both sides — sending
 * them wastes bytes for no physics benefit.
 * ======================================================================== */

typedef struct {
    uint32_t n_initial;           /* initial particle count */
    uint32_t capacity;            /* max particles (VRAM-limited on client) */
    uint32_t rng_seed;            /* deterministic RNG seed */
    uint32_t reserved;            /* alignment padding */
    double   dt;                  /* timestep */
    double   omega_nova_thresh;   /* omega threshold for supernova */
    double   rho_nova_thresh;     /* density threshold for nova cascade */
} ergo_seed_t;

/* ========================================================================
 * CONNECTION STATE
 * ======================================================================== */

typedef struct {
    int sock;
    struct sockaddr_in peer;
    socklen_t peer_len;

    uint32_t tx_seq;           /* outbound sequence counter */
    uint32_t rx_seq_last[ERGO_MAX_GPUS]; /* per-GPU highest inbound seq */
    uint32_t last_spawn_id;    /* last applied spawn command (idempotency) */
    uint8_t  gpu_id;           /* this node's GPU index */

    /* Multicast: field broadcast (O(1) instead of O(N)) */
    int mcast_sock;            /* -1 if unused */
    struct sockaddr_in mcast_addr;
} ergo_net_t;

/* ========================================================================
 * INIT — call once
 *
 * For GPU side:  ergo_net_init(&net, "192.168.1.10", ERGO_PORT, 0, gpu_id)
 * For Oracle:    ergo_net_init(&net, NULL, ERGO_PORT, 1, 0)
 * ======================================================================== */

static inline int ergo_net_init(ergo_net_t* n, const char* host, int port,
                                int bind_local, uint8_t gpu_id) {
    memset(n, 0, sizeof(*n));
    n->gpu_id = gpu_id;
    n->mcast_sock = -1;

    n->sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (n->sock < 0) { perror("[ergo-net] socket"); return -1; }

    /* Enlarge receive buffer for bursty multi-GPU traffic */
    int rcvbuf = 1 << 20;  /* 1MB */
    setsockopt(n->sock, SOL_SOCKET, SO_RCVBUF, &rcvbuf, sizeof(rcvbuf));

    if (bind_local) {
        struct sockaddr_in addr;
        memset(&addr, 0, sizeof(addr));
        addr.sin_family = AF_INET;
        addr.sin_port = htons(port);
        addr.sin_addr.s_addr = INADDR_ANY;
        if (bind(n->sock, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
            perror("[ergo-net] bind");
            return -2;
        }
        printf("[ergo-net] listening on port %d\n", port);
    }

    if (host) {
        n->peer.sin_family = AF_INET;
        n->peer.sin_port = htons(port);
        if (inet_pton(AF_INET, host, &n->peer.sin_addr) <= 0) {
            fprintf(stderr, "[ergo-net] invalid host: %s\n", host);
            return -3;
        }
        n->peer_len = sizeof(n->peer);
        printf("[ergo-net] target %s:%d gpu_id=%d\n", host, port, gpu_id);
    }

    return 0;
}

/* ========================================================================
 * SEND — generic packet send
 * ======================================================================== */

static inline int ergo_net_send(ergo_net_t* n, uint8_t type, uint32_t frame,
                                const void* payload, uint16_t len) {
    uint8_t buf[2048];
    if (len + sizeof(ergo_hdr_t) > sizeof(buf)) return -1;

    ergo_hdr_t h;
    h.magic       = htons(ERGO_MAGIC);
    h.type        = type;
    h.version     = ERGO_VERSION;
    h.frame       = htonl(frame);
    h.seq_id      = htonl(++n->tx_seq);
    h.gpu_id      = n->gpu_id;
    h._pad        = 0;
    h.payload_len = htons(len);

    memcpy(buf, &h, sizeof(h));
    if (len > 0) memcpy(buf + sizeof(h), payload, len);

    return sendto(n->sock, buf, sizeof(h) + len, 0,
                  (struct sockaddr*)&n->peer, n->peer_len);
}

/* ========================================================================
 * TYPED SEND HELPERS
 * ======================================================================== */

static inline int ergo_net_send_census(ergo_net_t* n, uint32_t frame,
                                       const ergo_census_t* c) {
    return ergo_net_send(n, ERGO_CENSUS, frame, c, sizeof(*c));
}

static inline int ergo_net_send_spawn(ergo_net_t* n, uint32_t frame,
                                      const ergo_spawn_t* s) {
    return ergo_net_send(n, ERGO_SPAWN, frame, s, sizeof(*s));
}

static inline int ergo_net_send_verify(ergo_net_t* n, uint32_t frame,
                                       const void* data, uint16_t len) {
    return ergo_net_send(n, ERGO_VERIFY, frame, data, len);
}

static inline int ergo_net_send_seed(ergo_net_t* n, const ergo_seed_t* s) {
    return ergo_net_send(n, ERGO_SEED, 0, s, sizeof(*s));
}

static inline int ergo_net_send_probe_set(ergo_net_t* n, uint32_t frame,
                                          const ergo_probe_set_t* ps) {
    return ergo_net_send(n, ERGO_PROBE_SET, frame, ps, sizeof(*ps));
}

static inline int ergo_net_send_register(ergo_net_t* n, uint8_t gpu_id) {
    ergo_register_t r;
    memset(&r, 0, sizeof(r));
    r.gpu_id = gpu_id;
    r.protocol_version = ERGO_VERSION;
    return ergo_net_send(n, ERGO_REGISTER, 0, &r, sizeof(r));
}

/* ========================================================================
 * RECEIVE — non-blocking, latest-wins, idempotent
 *
 * Returns: packet type (ERGO_CENSUS/SPAWN/VERIFY), 0 if nothing, -1 error
 * Fills header + payload. Caller dispatches by type.
 * Stale/duplicate packets silently dropped.
 * ======================================================================== */

static inline int ergo_net_recv(ergo_net_t* n, ergo_hdr_t* hdr,
                                void* payload, uint16_t max_payload,
                                struct sockaddr_in* sender) {
    uint8_t buf[2048];
    socklen_t slen = sizeof(*sender);

    int r = recvfrom(n->sock, buf, sizeof(buf), MSG_DONTWAIT,
                     (struct sockaddr*)sender, &slen);
    if (r <= 0) return 0;
    if (r < (int)sizeof(ergo_hdr_t)) return 0;

    memcpy(hdr, buf, sizeof(*hdr));

    /* Validate */
    if (ntohs(hdr->magic) != ERGO_MAGIC) return 0;
    if (hdr->version != ERGO_VERSION) return 0;

    /* Decode network byte order */
    hdr->frame       = ntohl(hdr->frame);
    hdr->seq_id      = ntohl(hdr->seq_id);
    hdr->payload_len = ntohs(hdr->payload_len);
    hdr->magic       = ERGO_MAGIC;  /* restore after ntohs */

    /* Latest-wins: per-GPU sequence tracking.
     * FIELD packets bypass — they use field_id + chunk_idx for ordering. */
    uint8_t gid = hdr->gpu_id;
    if (gid >= ERGO_MAX_GPUS) return 0;
    if (hdr->type != ERGO_FIELD) {
        if (hdr->seq_id <= n->rx_seq_last[gid]) return 0;
        n->rx_seq_last[gid] = hdr->seq_id;
    }

    /* Copy payload */
    uint16_t plen = hdr->payload_len;
    if (plen > max_payload) plen = max_payload;
    if (plen > 0 && (int)(sizeof(ergo_hdr_t) + plen) <= r)
        memcpy(payload, buf + sizeof(ergo_hdr_t), plen);

    return hdr->type;
}

/* ========================================================================
 * CONVENIENCE: receive spawn with idempotency check
 * ======================================================================== */

static inline int ergo_net_recv_spawn(ergo_net_t* n, ergo_spawn_t* out) {
    ergo_hdr_t hdr;
    ergo_spawn_t sp;
    struct sockaddr_in sender;

    int type = ergo_net_recv(n, &hdr, &sp, sizeof(sp), &sender);
    if (type != ERGO_SPAWN) return 0;

    /* Idempotent: skip already-applied commands */
    if (sp.spawn_id <= n->last_spawn_id) return 0;
    n->last_spawn_id = sp.spawn_id;

    *out = sp;
    return 1;
}

/* ========================================================================
 * FIELD TRANSFER: chunked send/recv for 128KB density grid
 *
 * Send: breaks grid into 97 chunks, each with header + data.
 * Recv: reassembles chunks into ergo_field_rx_t buffer.
 * Loss-tolerant: partial grids are usable (missing cells keep local values).
 * ======================================================================== */

static inline void ergo_field_rx_reset(ergo_field_rx_t* rx) {
    rx->field_id = 0;
    memset(rx->received, 0, sizeof(rx->received));
    rx->n_received = 0;
    rx->complete = 0;
}

/* Send a complete density grid as chunked FIELD packets.
 * grid: pointer to 32³ floats (131072 bytes).
 * field_id: monotonic transfer ID (caller manages).
 * Returns number of chunks sent. */
static inline int ergo_net_send_field(ergo_net_t* n, uint32_t frame,
                                      const float* grid, uint32_t field_id) {
    uint8_t buf[sizeof(ergo_field_chunk_t) + ERGO_FIELD_CHUNK_SIZE];
    const uint8_t* src = (const uint8_t*)grid;
    uint32_t remaining = ERGO_FIELD_GRID_BYTES;
    uint32_t offset = 0;
    int sent = 0;

    for (uint16_t i = 0; i < ERGO_FIELD_NCHUNKS && remaining > 0; i++) {
        uint16_t chunk_len = remaining < ERGO_FIELD_CHUNK_SIZE
                           ? (uint16_t)remaining : ERGO_FIELD_CHUNK_SIZE;

        ergo_field_chunk_t ch;
        ch.field_id = field_id;
        ch.chunk_idx = i;
        ch.n_chunks = ERGO_FIELD_NCHUNKS;
        ch.byte_offset = offset;
        ch.chunk_len = chunk_len;
        ch._pad = 0;

        memcpy(buf, &ch, sizeof(ch));
        memcpy(buf + sizeof(ch), src + offset, chunk_len);

        ergo_net_send(n, ERGO_FIELD, frame, buf,
                      (uint16_t)(sizeof(ch) + chunk_len));
        offset += chunk_len;
        remaining -= chunk_len;
        sent++;
    }
    return sent;
}

/* Process one received FIELD chunk into the reassembly buffer.
 * Returns 1 if the transfer is now complete, 0 otherwise. */
static inline int ergo_field_rx_chunk(ergo_field_rx_t* rx,
                                      const void* payload, uint16_t len) {
    if (len < sizeof(ergo_field_chunk_t)) return 0;

    ergo_field_chunk_t ch;
    memcpy(&ch, payload, sizeof(ch));

    /* New transfer — reset state */
    if (ch.field_id != rx->field_id) {
        ergo_field_rx_reset(rx);
        rx->field_id = ch.field_id;
    }

    /* Bounds check */
    if (ch.chunk_idx >= ERGO_FIELD_NCHUNKS) return 0;
    if (ch.byte_offset + ch.chunk_len > ERGO_FIELD_GRID_BYTES) return 0;

    /* Copy chunk data into grid buffer */
    const uint8_t* data = (const uint8_t*)payload + sizeof(ch);
    uint16_t data_len = len - sizeof(ergo_field_chunk_t);
    if (data_len > ch.chunk_len) data_len = ch.chunk_len;
    memcpy((uint8_t*)rx->grid + ch.byte_offset, data, data_len);

    /* Mark received */
    if (!rx->received[ch.chunk_idx]) {
        rx->received[ch.chunk_idx] = 1;
        rx->n_received++;
    }

    rx->complete = (rx->n_received >= (int)ch.n_chunks);
    return rx->complete;
}

/* ========================================================================
 * MULTICAST — O(1) field broadcast
 *
 * Oracle calls ergo_net_mcast_init_sender() to set up multicast output.
 * Clients call ergo_net_mcast_init_recv() to join the multicast group.
 * ergo_net_send_field_mcast() sends one copy; all clients receive it.
 * ======================================================================== */

static inline int ergo_net_mcast_init_sender(ergo_net_t* n) {
    n->mcast_sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (n->mcast_sock < 0) {
        perror("[ergo-net] mcast socket");
        return -1;
    }
    uint8_t ttl = 1;
    setsockopt(n->mcast_sock, IPPROTO_IP, IP_MULTICAST_TTL, &ttl, sizeof(ttl));

    memset(&n->mcast_addr, 0, sizeof(n->mcast_addr));
    n->mcast_addr.sin_family = AF_INET;
    n->mcast_addr.sin_port = htons(ERGO_MCAST_PORT);
    inet_pton(AF_INET, ERGO_MCAST_GROUP, &n->mcast_addr.sin_addr);

    printf("[ergo-net] multicast sender → %s:%d\n",
           ERGO_MCAST_GROUP, ERGO_MCAST_PORT);
    return 0;
}

static inline int ergo_net_mcast_init_recv(ergo_net_t* n) {
    n->mcast_sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (n->mcast_sock < 0) {
        perror("[ergo-net] mcast socket");
        return -1;
    }

    int reuse = 1;
    setsockopt(n->mcast_sock, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));
#ifdef SO_REUSEPORT
    setsockopt(n->mcast_sock, SOL_SOCKET, SO_REUSEPORT, &reuse, sizeof(reuse));
#endif

    int rcvbuf = 1 << 20;
    setsockopt(n->mcast_sock, SOL_SOCKET, SO_RCVBUF, &rcvbuf, sizeof(rcvbuf));

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(ERGO_MCAST_PORT);
    addr.sin_addr.s_addr = INADDR_ANY;
    if (bind(n->mcast_sock, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("[ergo-net] mcast bind");
        return -2;
    }

    ERGO_IP_MREQ mreq;
    inet_pton(AF_INET, ERGO_MCAST_GROUP, &mreq.imr_multiaddr);
    mreq.imr_interface.s_addr = INADDR_ANY;
    if (setsockopt(n->mcast_sock, IPPROTO_IP, IP_ADD_MEMBERSHIP,
                   &mreq, sizeof(mreq)) < 0) {
        perror("[ergo-net] mcast join");
        return -3;
    }

    printf("[ergo-net] joined multicast group %s:%d\n",
           ERGO_MCAST_GROUP, ERGO_MCAST_PORT);
    return 0;
}

static inline int ergo_net_send_field_mcast(ergo_net_t* n, uint32_t frame,
                                            const float* grid,
                                            uint32_t field_id) {
    if (n->mcast_sock < 0) return -1;

    uint8_t buf[sizeof(ergo_hdr_t) + sizeof(ergo_field_chunk_t)
                + ERGO_FIELD_CHUNK_SIZE];
    const uint8_t* src = (const uint8_t*)grid;
    uint32_t remaining = ERGO_FIELD_GRID_BYTES;
    uint32_t offset = 0;
    int sent = 0;

    for (uint16_t i = 0; i < ERGO_FIELD_NCHUNKS && remaining > 0; i++) {
        uint16_t chunk_len = remaining < ERGO_FIELD_CHUNK_SIZE
                           ? (uint16_t)remaining : ERGO_FIELD_CHUNK_SIZE;

        ergo_hdr_t h;
        h.magic       = htons(ERGO_MAGIC);
        h.type        = ERGO_FIELD;
        h.version     = ERGO_VERSION;
        h.frame       = htonl(frame);
        h.seq_id      = htonl(++n->tx_seq);
        h.gpu_id      = n->gpu_id;
        h._pad        = 0;
        uint16_t plen = sizeof(ergo_field_chunk_t) + chunk_len;
        h.payload_len = htons(plen);

        ergo_field_chunk_t ch;
        ch.field_id = field_id;
        ch.chunk_idx = i;
        ch.n_chunks = ERGO_FIELD_NCHUNKS;
        ch.byte_offset = offset;
        ch.chunk_len = chunk_len;
        ch._pad = 0;

        memcpy(buf, &h, sizeof(h));
        memcpy(buf + sizeof(h), &ch, sizeof(ch));
        memcpy(buf + sizeof(h) + sizeof(ch), src + offset, chunk_len);

        sendto(n->mcast_sock, buf, sizeof(h) + plen, 0,
               (struct sockaddr*)&n->mcast_addr, sizeof(n->mcast_addr));
        offset += chunk_len;
        remaining -= chunk_len;
        sent++;
    }
    return sent;
}

static inline int ergo_net_recv_field_mcast(ergo_net_t* n,
                                            ergo_field_rx_t* rx) {
    if (n->mcast_sock < 0) return -1;

    uint8_t buf[2048];
    int r = recv(n->mcast_sock, buf, sizeof(buf), MSG_DONTWAIT);
    if (r <= 0) return 0;
    if (r < (int)(sizeof(ergo_hdr_t) + sizeof(ergo_field_chunk_t))) return 0;

    ergo_hdr_t hdr;
    memcpy(&hdr, buf, sizeof(hdr));
    if (ntohs(hdr.magic) != ERGO_MAGIC) return 0;
    if (hdr.type != ERGO_FIELD) return 0;

    uint16_t plen = ntohs(hdr.payload_len);
    if (plen < sizeof(ergo_field_chunk_t)) return 0;
    if ((int)(sizeof(ergo_hdr_t) + plen) > r) return 0;

    return ergo_field_rx_chunk(rx, buf + sizeof(ergo_hdr_t), plen);
}

/* ========================================================================
 * CLEANUP
 * ======================================================================== */

static inline void ergo_net_close(ergo_net_t* n) {
    if (n->sock >= 0) close(n->sock);
    if (n->mcast_sock >= 0) close(n->mcast_sock);
    n->sock = -1;
    n->mcast_sock = -1;
}

#endif /* ERGO_NET_H */
