/* sockbench.c -- the protocol on real sockets.
 *
 * Loopback is reliable, so damage is applied by a fault-injecting
 * proxy between sender and receiver (standard practice: the socket
 * paths are genuine -- serialization, send/recv, reassembly, fetch
 * round trip -- only the corruption itself is injected).
 *
 * Topology (all 127.0.0.1, one process, sequential):
 *   sender --(units+meta)--> proxy --(damaged)--> receiver
 *   receiver --(fetch req)--> sender(fetch sock); sender --(P+Q)-->
 *   receiver. Datagram: [seq u16][kind u8][idx u8][len u16] + payload.
 * kinds: 0=unit(512B) 1=meta(256B) 2=parP 3=parQ 4=fetch-req.
 * TCP mode: same messages over streams with u16 length prefix; the
 * proxy is message-aware (parses, damages payloads, forwards).
 * Damage plan per trial uses the packetbench models (spread / burst /
 * drop / mixed) applied at the proxy. NTR=50/cell; 30 ms receiver
 * timeout separates loss from delay.
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <time.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>

#define NP 8
#define PL 512
#define FR (NP * PL)
#define META 256
#define NTR 50
#define PS 41001 /* sender -> proxy */
#define PR 41002 /* proxy -> receiver */
#define PF 41003 /* fetch: receiver -> sender, replies back */

static uint8_t bku[NP][PL], snd[NP][PL], rcv[NP][PL];
static uint8_t parP[PL], parQ[PL], meta[META];
static uint32_t refs[NP][4];
static uint8_t gexp[512], glog[256];
static uint64_t bondK;
static int use_tcp;

static uint64_t trng = 0xC0FFEE123456789ull;
static uint64_t trand(void) {
    trng ^= trng << 13;
    trng ^= trng >> 7;
    trng ^= trng << 17;
    return trng;
}
static uint64_t sm64(uint64_t *s) {
    uint64_t z = (*s += 0x9E3779B97F4A7C15ull);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ull;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBull;
    return z ^ (z >> 31);
}
static uint8_t gfm(uint8_t a, uint8_t b) {
    uint8_t r = 0;
    while (b) {
        if (b & 1)
            r ^= a;
        uint8_t hi = a & 0x80;
        a <<= 1;
        if (hi)
            a ^= 0x1B;
        b >>= 1;
    }
    return r;
}
static void gf_init(void) {
    uint8_t v = 1;
    for (int i = 0; i < 511; i++) {
        gexp[i] = v;
        if (i < 255)
            glog[v] = (uint8_t)i;
        v = gfm(v, 3);
    }
    gexp[511] = 1;
}
static uint8_t gf_div(uint8_t a, uint8_t b) {
    if (!a)
        return 0;
    int l = (int)glog[a] - (int)glog[b];
    if (l < 0)
        l += 255;
    return gexp[l];
}
static void triple4(const uint8_t *p, uint32_t *s) {
    uint32_t a = 0, b = 0, c = 0, d = 0;
    for (int i = 0; i < PL; i++) {
        uint32_t v = p[i], k = (uint32_t)i + 1;
        a += v;
        b += v * k;
        c += v * k * k;
        d += v * k * k * k;
    }
    s[0] = a;
    s[1] = b;
    s[2] = c;
    s[3] = d;
}
static int sec_pkt(uint8_t *p, const uint32_t *ref) {
    uint32_t s[4];
    triple4(p, s);
    uint32_t e0 = s[0] - ref[0], e1 = s[1] - ref[1];
    uint32_t e2 = s[2] - ref[2], e3 = s[3] - ref[3];
    if (!(e0 | e1 | e2 | e3))
        return 1;
    int32_t d = (int32_t)e0;
    if (!((d >= 1 && d <= 255) || (d >= -255 && d <= -1)))
        return 0;
    int32_t e1s = (int32_t)e1;
    if (e1s % d != 0)
        return 0;
    int32_t q = e1s / d;
    if (q < 1 || q > PL)
        return 0;
    if ((int64_t)d * q * q != (int32_t)e2)
        return 0;
    if ((uint32_t)((int64_t)d * q * q * q) != e3)
        return 0;
    p[q - 1] = (uint8_t)(p[q - 1] - (uint8_t)d);
    triple4(p, s);
    return !((s[0] - ref[0]) | (s[1] - ref[1]) | (s[2] - ref[2]) |
             (s[3] - ref[3]));
}
static uint64_t ktag(uint64_t K, const uint8_t *m, size_t n,
                     uint64_t dom) {
    uint64_t h = K ^ dom;
    for (size_t i = 0; i < n; i++) {
        h ^= m[i] + 0x9E3779B97F4A7C15ull + (h << 6) + (h >> 2) + i;
        if ((i & 63) == 63) {
            uint64_t s = h;
            h = sm64(&s);
        }
    }
    uint64_t s = h ^ (uint64_t)n;
    return sm64(&s);
}
/* sockets: ssnd sender->proxy, sprx proxy in, sfwd proxy->receiver,
 * srcv receiver in, sfs sender fetch端, sfr receiver fetch端. */
static int ssnd, sprx, sfwd, srcv, sfs, sfr;
static struct sockaddr_in a_proxy, a_recv, a_fetch;
static double now_us(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1e6 + (double)ts.tv_nsec / 1e3;
}
static void addr(struct sockaddr_in *a, int port) {
    memset(a, 0, sizeof *a);
    a->sin_family = AF_INET;
    a->sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    a->sin_port = htons((uint16_t)port);
}
static void sk_init(void) {
    int t = use_tcp ? SOCK_STREAM : SOCK_DGRAM;
    struct timeval tvr = { 0, 30000 };
    int reuse = 1;
    addr(&a_proxy, PS);
    addr(&a_recv, PR);
    addr(&a_fetch, PF);
    if (use_tcp) {
        int l1 = socket(AF_INET, t, 0), l2 = socket(AF_INET, t, 0),
            l3 = socket(AF_INET, t, 0);
        setsockopt(l1, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof reuse);
        setsockopt(l2, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof reuse);
        setsockopt(l3, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof reuse);
        struct sockaddr_in b1, b2, b3;
        addr(&b1, PS);
        addr(&b2, PR);
        addr(&b3, PF);
        bind(l1, (struct sockaddr *)&b1, sizeof b1);
        bind(l2, (struct sockaddr *)&b2, sizeof b2);
        bind(l3, (struct sockaddr *)&b3, sizeof b3);
        listen(l1, 4);
        listen(l2, 4);
        listen(l3, 4);
        ssnd = socket(AF_INET, t, 0);
        sfwd = socket(AF_INET, t, 0);
        sfr = socket(AF_INET, t, 0);
        setsockopt(ssnd, SOL_SOCKET, SO_REUSEADDR, &reuse,
                   sizeof reuse);
        setsockopt(sfwd, SOL_SOCKET, SO_REUSEADDR, &reuse,
                   sizeof reuse);
        setsockopt(sfr, SOL_SOCKET, SO_REUSEADDR, &reuse,
                   sizeof reuse);
        connect(ssnd, (struct sockaddr *)&b1, sizeof b1);
        connect(sfwd, (struct sockaddr *)&b2, sizeof b2);
        connect(sfr, (struct sockaddr *)&b3, sizeof b3);
        sprx = accept(l1, NULL, NULL);
        srcv = accept(l2, NULL, NULL);
        sfs = accept(l3, NULL, NULL);
        close(l1);
        close(l2);
        close(l3);
        setsockopt(srcv, SOL_SOCKET, SO_RCVTIMEO, &tvr, sizeof tvr);
        setsockopt(sfr, SOL_SOCKET, SO_RCVTIMEO, &tvr, sizeof tvr);
        setsockopt(sfs, SOL_SOCKET, SO_RCVTIMEO, &tvr, sizeof tvr);
        int nd = 1;
        setsockopt(ssnd, IPPROTO_TCP, TCP_NODELAY, &nd, sizeof nd);
        setsockopt(sfwd, IPPROTO_TCP, TCP_NODELAY, &nd, sizeof nd);
        setsockopt(sfr, IPPROTO_TCP, TCP_NODELAY, &nd, sizeof nd);
        setsockopt(sprx, IPPROTO_TCP, TCP_NODELAY, &nd, sizeof nd);
        setsockopt(srcv, IPPROTO_TCP, TCP_NODELAY, &nd, sizeof nd);
        setsockopt(sfs, IPPROTO_TCP, TCP_NODELAY, &nd, sizeof nd);
    } else {
        ssnd = socket(AF_INET, t, 0);
        sprx = socket(AF_INET, t, 0);
        sfwd = socket(AF_INET, t, 0);
        srcv = socket(AF_INET, t, 0);
        sfs = socket(AF_INET, t, 0);
        sfr = socket(AF_INET, t, 0);
        setsockopt(sprx, SOL_SOCKET, SO_REUSEADDR, &reuse,
                   sizeof reuse);
        setsockopt(srcv, SOL_SOCKET, SO_REUSEADDR, &reuse,
                   sizeof reuse);
        setsockopt(sfs, SOL_SOCKET, SO_REUSEADDR, &reuse,
                   sizeof reuse);
        bind(sprx, (struct sockaddr *)&a_proxy, sizeof a_proxy);
        bind(srcv, (struct sockaddr *)&a_recv, sizeof a_recv);
        bind(sfs, (struct sockaddr *)&a_fetch, sizeof a_fetch);
        connect(ssnd, (struct sockaddr *)&a_proxy, sizeof a_proxy);
        connect(sfwd, (struct sockaddr *)&a_recv, sizeof a_recv);
        connect(sfr, (struct sockaddr *)&a_fetch, sizeof a_fetch);
        setsockopt(srcv, SOL_SOCKET, SO_RCVTIMEO, &tvr, sizeof tvr);
        setsockopt(sfr, SOL_SOCKET, SO_RCVTIMEO, &tvr, sizeof tvr);
    }
}
static uint8_t mbuf[2048];
static void tx(int fd, uint16_t seq, uint8_t kind, uint8_t idx,
               const uint8_t *pl, uint16_t len) {
    mbuf[0] = (uint8_t)(seq & 255);
    mbuf[1] = (uint8_t)(seq >> 8);
    mbuf[2] = kind;
    mbuf[3] = idx;
    mbuf[4] = (uint8_t)(len & 255);
    mbuf[5] = (uint8_t)(len >> 8);
    mbuf[6] = 0;
    mbuf[7] = 0;
    memcpy(mbuf + 8, pl, len);
    if (use_tcp) {
        uint8_t lp[2] = { (uint8_t)((len + 8) & 255),
                          (uint8_t)((len + 8) >> 8) };
        send(fd, lp, 2, 0);
        send(fd, mbuf, len + 8, 0);
    } else {
        send(fd, mbuf, len + 8, 0);
    }
}
static int rx(int fd, uint8_t *kind, uint8_t *idx, uint8_t *pl,
              uint16_t *len) {
    ssize_t n;
    if (use_tcp) {
        uint8_t lp[2];
        size_t got = 0;
        while (got < 2) {
            n = recv(fd, lp + got, 2 - got, 0);
            if (n <= 0)
                return 0;
            got += (size_t)n;
        }
        uint16_t ml = (uint16_t)(lp[0] | (lp[1] << 8));
        if (ml > sizeof mbuf)
            return 0;
        got = 0;
        while (got < ml) {
            n = recv(fd, mbuf + got, ml - got, 0);
            if (n <= 0)
                return 0;
            got += (size_t)n;
        }
    } else {
        n = recv(fd, mbuf, sizeof mbuf, 0);
        if (n < 8)
            return 0;
    }
    *kind = mbuf[2];
    *idx = mbuf[3];
    *len = (uint16_t)(mbuf[4] | (mbuf[5] << 8));
    if (*len > 2040)
        return 0;
    memcpy(pl, mbuf + 8, *len);
    return 1;
}
/* damage plan (packetbench models) */
static int flips[64][3], nflip, dropu[NP];
static void plan(int kind) {
    nflip = 0;
    memset(dropu, 0, sizeof dropu);
    if (kind == 1 || kind == 2) {
        int n = kind == 1 ? 1 : 4;
        for (int j = 0; j < n; j++) {
            int pos = (int)(trand() % FR), dv;
            do {
                dv = (int)((trand() & 255) + 1) & 255;
            } while (!dv);
            flips[nflip][0] = pos % 8;
            flips[nflip][1] = pos / 8;
            flips[nflip][2] = dv;
            nflip++;
        }
    } else if (kind == 3 || kind == 4) {
        int len = kind == 3 ? 8 : 64;
        int st = (int)(trand() % (FR - len));
        for (int j = 0; j < len && nflip < 64; j++) {
            int pos = st + j, dv;
            do {
                dv = (int)((trand() & 255) + 1) & 255;
            } while (!dv);
            flips[nflip][0] = pos % 8;
            flips[nflip][1] = pos / 8;
            flips[nflip][2] = dv;
            nflip++;
        }
    } else if (kind == 5 || kind == 6) {
        int d = kind - 4, n = 0;
        while (n < d) {
            int p = (int)(trand() % NP);
            if (!dropu[p]) {
                dropu[p] = 1;
                n++;
            }
        }
    } else if (kind == 7) {
        int n = 0;
        while (n < 1) {
            int p = (int)(trand() % NP);
            if (!dropu[p]) {
                dropu[p] = 1;
                n++;
            }
        }
        for (int j = 0; j < 2; j++) {
            int pos = (int)(trand() % FR), dv;
            int u = pos % 8;
            if (dropu[u])
                continue;
            do {
                dv = (int)((trand() & 255) + 1) & 255;
            } while (!dv);
            flips[nflip][0] = u;
            flips[nflip][1] = pos / 8;
            flips[nflip][2] = dv;
            nflip++;
        }
    }
}
static uint8_t rpl[META];
static int bytes_ok(void) {
    int n = 0;
    for (int u = 0; u < NP; u++)
        for (int i = 0; i < PL; i++)
            n += (rcv[u][i] == bku[u][i]);
    return n;
}
/* sender fetch responder: drain pending reqs (nonblocking), reply P+Q */
/* NOTE: SO_RCVTIMEO {0,0} means BLOCK (not poll) on Linux, so the
 * drain below uses select() with a zero timeout, which is a true
 * nonblocking poll. */
#include <sys/select.h>
static int poll_in(int fd) {
    fd_set rf;
    FD_ZERO(&rf);
    FD_SET(fd, &rf);
    struct timeval tv = { 0, 0 };
    return select(fd + 1, &rf, NULL, NULL, &tv);
}
static void serve_fetch(void) {
    socklen_t al;
    struct sockaddr_in peer;
    if (use_tcp) {
        uint8_t k, ix, pl[64];
        uint16_t ln;
        struct timeval tv0 = { 0, 0 }, tv1 = { 0, 100000 };
        setsockopt(sfs, SOL_SOCKET, SO_RCVTIMEO, &tv0, sizeof tv0);
        for (;;) {
            if (!poll_in(sfs))
                break;
            if (!rx(sfs, &k, &ix, pl, &ln))
                break;
            if (k == 4) {
                tx(sfs, 0, 2, 0, parP, PL);
                tx(sfs, 0, 3, 0, parQ, PL);
            }
        }
        setsockopt(sfs, SOL_SOCKET, SO_RCVTIMEO, &tv1, sizeof tv1);
    } else {
        for (;;) {
            if (!poll_in(sfs))
                break;
            al = sizeof peer;
            ssize_t n = recvfrom(sfs, mbuf, sizeof mbuf, 0,
                                 (struct sockaddr *)&peer, &al);
            if (n < 8)
                break;
            if (mbuf[2] == 4) {
                /* NOTE: length header must be set explicitly here;
                 * stale req len (1) once shipped 1-byte "parities". */
                mbuf[2] = 2;
                mbuf[4] = 0;
                mbuf[5] = 2;
                memcpy(mbuf + 8, parP, PL);
                sendto(sfs, mbuf, PL + 8, 0,
                       (struct sockaddr *)&peer, al);
                mbuf[2] = 3;
                mbuf[4] = 0;
                mbuf[5] = 2;
                memcpy(mbuf + 8, parQ, PL);
                sendto(sfs, mbuf, PL + 8, 0,
                       (struct sockaddr *)&peer, al);
            }
        }
    }
}
static void build_meta(void) {
    for (int u = 0; u < NP; u++)
        for (int w = 0; w < 4; w++) {
            meta[u * 16 + w * 4 + 0] = (uint8_t)refs[u][w];
            meta[u * 16 + w * 4 + 1] = (uint8_t)(refs[u][w] >> 8);
            meta[u * 16 + w * 4 + 2] = (uint8_t)(refs[u][w] >> 16);
            meta[u * 16 + w * 4 + 3] = (uint8_t)(refs[u][w] >> 24);
        }
    static uint8_t cat[2 * PL];
    memcpy(cat, parP, PL);
    memcpy(cat + PL, parQ, PL);
    uint64_t pc = ktag(bondK, cat, 2 * PL, 0x50524F4D495345ull);
    memcpy(meta + 128, &pc, 8);
    uint64_t sa = ktag(bondK, meta, 136, 0x53545245414D4155ull);
    memcpy(meta + 136, &sa, 8);
    memset(meta + 144, 0, META - 144);
}
static void build_all(void) {
    gf_init();
    for (int u = 0; u < NP; u++)
        for (int k = 0; k < PL; k++) {
            int j = 8 * k + u;
            uint8_t v = (uint8_t)(((j * 67 + 41) ^ 0x3C ^ (j >> 3)) & 0xFF);
            bku[u][k] = v;
            snd[u][k] = v;
        }
    bku[0][0] = 0x45;
    bku[1][0] = 0x53;
    bku[2][0] = 0x46;
    bku[3][0] = 0x32;
    memcpy(snd, bku, sizeof bku);
    for (int u = 0; u < NP; u++)
        triple4(bku[u], refs[u]);
    memset(parP, 0, PL);
    memset(parQ, 0, PL);
    for (int u = 0; u < NP; u++) {
        uint8_t c = gexp[u];
        for (int i = 0; i < PL; i++) {
            parP[i] ^= bku[u][i];
            parQ[i] ^= gfm(c, bku[u][i]);
        }
    }
    bondK = 18050561372206496278ull;
    build_meta();
}
static const char *kn[8] = { "clean", "SP1", "SP4", "BUI8",
                             "BUI64", "LO1", "LO2", "MX" };
int main(int argc, char **argv) {
    use_tcp = argc > 1 && !strcmp(argv[1], "tcp");
    build_all();
    sk_init();
    printf("mode=%s sockets=127.0.0.1:%d/%d/%d NTR=%d\n",
           use_tcp ? "TCP" : "UDP", PS, PR, PF, NTR);
    const int cells[] = { 0, 1, 2, 3, 4, 5, 6, 7 };
    for (int ci = 0; ci < 8; ci++) {
        int kind = cells[ci], full = 0, fetches = 0;
        double tmus = 0, trtt = 0;
        for (int t = 0; t < NTR; t++) {
            for (int u = 0; u < NP; u++)
                tx(ssnd, (uint16_t)t, 0, (uint8_t)u, snd[u], PL);
            tx(ssnd, (uint16_t)t, 1, 0, meta, META);
            plan(kind);
            uint8_t k, ix, pl[2048];
            uint16_t ln;
            for (int m = 0; m < 9; m++) {
                if (!rx(sprx, &k, &ix, pl, &ln))
                    break;
                if (k == 0 && ix < NP && dropu[ix])
                    continue;
                if (k == 0 && ix < NP)
                    for (int f = 0; f < nflip; f++)
                        if (flips[f][0] == ix)
                            pl[flips[f][1]] ^=
                                (uint8_t)flips[f][2];
                tx(sfwd, (uint16_t)t, k, ix, pl, ln);
            }
            int haveu[NP], havem = 0, have = 0;
            memset(haveu, 0, sizeof haveu);
            memset(rcv, 0, sizeof rcv);
            while (have < 9) {
                if (!rx(srcv, &k, &ix, pl, &ln))
                    break;
                if (k == 0 && ix < NP && !haveu[ix]) {
                    memcpy(rcv[ix], pl, PL);
                    haveu[ix] = 1;
                    have++;
                } else if (k == 1 && !havem) {
                    memcpy(rpl, pl, META);
                    havem = 1;
                    have++;
                }
            }
            double t0 = now_us();
            int lost[NP], nl = 0;
            for (int u = 0; u < NP; u++) {
                lost[u] = !haveu[u];
                nl += lost[u];
            }
            for (int p = 0; p < NP; p++) {
                if (lost[p])
                    continue;
                sec_pkt(rcv[p], refs[p]);
            }
            int f = bytes_ok() == FR;
            double frtt = 0;
            /* Parity solves erasures only: fetch iff 1-2 units are
             * actually missing. Pure-error damage (nl==0) or beyond
             * P+Q (nl>2) cannot use fetched parity; a real stack
             * would resend-fallback here instead. */
            if (!f && havem && nl >= 1 && nl <= 2) {
                uint8_t rq[1] = { 0 };
                tx(sfr, (uint16_t)t, 4, 0, rq, 1);
                serve_fetch();
                double f0 = now_us();
                uint8_t fk, fi, fpl[2048];
                uint16_t fl;
                uint8_t gotP = 0, gotQ = 0;
                uint8_t fP[PL], fQ[PL];
                for (int m = 0; m < 2; m++) {
                    if (!rx(sfr, &fk, &fi, fpl, &fl))
                        break;
                    if (fk == 2) {
                        memcpy(fP, fpl, PL);
                        gotP = 1;
                    }
                    if (fk == 3) {
                        memcpy(fQ, fpl, PL);
                        gotQ = 1;
                    }
                }
                frtt = now_us() - f0;
                fetches++;
                if (gotP && gotQ) {
                    static uint8_t cat[2 * PL];
                    memcpy(cat, fP, PL);
                    memcpy(cat + PL, fQ, PL);
                    uint64_t pc = 0;
                    memcpy(&pc, rpl + 128, 8);
                    if (ktag(bondK, cat, 2 * PL,
                             0x50524F4D495345ull) == pc && nl >= 1 &&
                        nl <= 2) {
                        int L[2], c = 0;
                        for (int p = 0; p < NP && c < 2; p++)
                            if (lost[p])
                                L[c++] = p;
                        if (c == 1) {
                            for (int i = 0; i < PL; i++) {
                                uint8_t v = fP[i];
                                for (int p = 0; p < NP; p++)
                                    if (p != L[0])
                                        v ^= rcv[p][i];
                                rcv[L[0]][i] = v;
                            }
                        } else if (c == 2) {
                            uint8_t ca = gexp[L[0]], cb = gexp[L[1]],
                                    den = ca ^ cb;
                            for (int i = 0; i < PL; i++) {
                                uint8_t pp = fP[i], qq = fQ[i];
                                for (int p = 0; p < NP; p++)
                                    if (p != L[0] && p != L[1]) {
                                        pp ^= rcv[p][i];
                                        qq ^=
                                            gfm(gexp[p], rcv[p][i]);
                                    }
                                uint8_t ua =
                                    gf_div(qq ^ gfm(cb, pp), den);
                                rcv[L[0]][i] = ua;
                                rcv[L[1]][i] = pp ^ ua;
                            }
                        }
                        for (int p = 0; p < NP; p++)
                            if (lost[p])
                                sec_pkt(rcv[p], refs[p]);
                        f = bytes_ok() == FR;
                    }
                }
            }
            full += f;
            tmus += now_us() - t0 - frtt;
            trtt += frtt;
        }
        printf("%s %s: full=%d/%d fetches=%d compute=%.0fus fetch-rtt=%.0fus\n",
               use_tcp ? "TCP" : "UDP", kn[kind], full, NTR, fetches,
               tmus / NTR, fetches ? trtt / fetches : 0);
    }
    return 0;
}
