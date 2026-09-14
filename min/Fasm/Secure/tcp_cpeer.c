/* tcp_cpeer.c -- C sender/receiver for asm TCP interop. Role via argv.
 * Framing (must match tcp_node.asm): [len16 LE][seq16][kind][idx]
 * [paylen16][00][payload]. Verdict lines identical to UDP peers.
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <sys/select.h>
#include <signal.h>

#define NP 8
#define PL 512
#define FR (NP * PL)
#define META 256
#define PS 41001
#define PR 41002
#define PF 41003
#define SEQ 7
#define BONDK 18050561372206496278ull

static uint8_t bku[NP][PL], rcv[NP][PL], parP[PL], parQ[PL];
static uint32_t refs[NP][4];
static uint8_t gexp[512], glog[256];
static uint8_t meta[META];

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
static void addr(struct sockaddr_in *a, int port) {
    memset(a, 0, sizeof *a);
    a->sin_family = AF_INET;
    a->sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    a->sin_port = htons((uint16_t)port);
}
static int tcpsock(void) {
    int f = socket(AF_INET, SOCK_STREAM, 0);
    int nd = 1;
    setsockopt(f, IPPROTO_TCP, TCP_NODELAY, &nd, sizeof nd);
    return f;
}
static void build(void) {
    gf_init();
    for (int u = 0; u < NP; u++)
        for (int k = 0; k < PL; k++) {
            int j = 8 * k + u;
            bku[u][k] =
                (uint8_t)(((j * 67 + 41) ^ 0x3C ^ (j >> 3)) & 0xFF);
        }
    bku[0][0] = 0x45;
    bku[1][0] = 0x53;
    bku[2][0] = 0x46;
    bku[3][0] = 0x32;
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
    uint64_t pc = ktag(BONDK, cat, 2 * PL, 0x50524F4D495345ull);
    memcpy(meta + 128, &pc, 8);
    uint64_t sa = ktag(BONDK, meta, 136, 0x53545245414D4155ull);
    memcpy(meta + 136, &sa, 8);
    memset(meta + 144, 0, META - 144);
}
static uint8_t sbuf[530], rbuf[2048];
static int waitfd(int fd, int ms) {
    fd_set rf;
    FD_ZERO(&rf);
    FD_SET(fd, &rf);
    struct timeval tv = { ms / 1000, (ms % 1000) * 1000 };
    return select(fd + 1, &rf, NULL, NULL, &tv);
}
static void sendall(int fd, const uint8_t *b, size_t n) {
    size_t o = 0;
    while (o < n) {
        ssize_t w = send(fd, b + o, n - o, 0);
        if (w <= 0)
            break;
        o += (size_t)w;
    }
}
static void txmsg(int fd, const uint8_t *pl, uint16_t len, uint8_t kind,
                  uint8_t idx) {
    uint16_t ml = len + 8;
    sbuf[0] = (uint8_t)(ml & 255);
    sbuf[1] = (uint8_t)(ml >> 8);
    sbuf[2] = SEQ & 255;
    sbuf[3] = SEQ >> 8;
    sbuf[4] = kind;
    sbuf[5] = idx;
    sbuf[6] = (uint8_t)(len & 255);
    sbuf[7] = (uint8_t)(len >> 8);
    sbuf[8] = sbuf[9] = 0;
    memcpy(sbuf + 10, pl, len);
    sendall(fd, sbuf, ml + 2);
}
/* rxmsg: whole message into rbuf, returns paylen or 0 */
static int rxmsg(int fd, int ms) {
    if (!waitfd(fd, ms))
        return 0;
    uint8_t lp[2];
    size_t got = 0;
    while (got < 2) {
        ssize_t n = recv(fd, lp + got, 2 - got, 0);
        if (n <= 0)
            return 0;
        got += (size_t)n;
    }
    uint16_t ml = (uint16_t)(lp[0] | (lp[1] << 8));
    if (ml < 8 || ml > 520)
        return 0;
    got = 0;
    while (got < ml) {
        if (!waitfd(fd, ms))
            return 0;
        ssize_t n = recv(fd, rbuf + got, ml - got, 0);
        if (n <= 0)
            return 0;
        got += (size_t)n;
    }
    return ml - 8;
}
static int bytes_ok(void) {
    int n = 0;
    for (int u = 0; u < NP; u++)
        for (int i = 0; i < PL; i++)
            n += (rcv[u][i] == bku[u][i]);
    return n;
}
int do_send(void) {
    build();
    int ss = tcpsock();
    struct sockaddr_in ap;
    addr(&ap, PS);
    if (connect(ss, (struct sockaddr *)&ap, sizeof ap)) {
        printf("S sent=0 served=0\n");
        return 1;
    }
    for (int u = 0; u < NP; u++)
        txmsg(ss, bku[u], PL, 0, (uint8_t)u);
    txmsg(ss, meta, META, 1, 0);
    int ls = tcpsock(), reuse = 1;
    setsockopt(ls, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof reuse);
    struct sockaddr_in af;
    addr(&af, PF);
    bind(ls, (struct sockaddr *)&af, sizeof af);
    listen(ls, 4);
    int served = 0, sfs = -1;
    if (waitfd(ls, 2000))
        sfs = accept(ls, NULL, NULL);
    if (sfs >= 0) {
        int nd = 1;
        setsockopt(sfs, IPPROTO_TCP, TCP_NODELAY, &nd, sizeof nd);
        for (;;) {
            int pl = rxmsg(sfs, 1000);
            if (!pl || served >= 8)
                break;
            if (rbuf[2] != 4)
                continue;
            txmsg(sfs, parP, PL, 2, 0);
            txmsg(sfs, parQ, PL, 3, 0);
            served++;
        }
        close(sfs);
    }
    printf("S sent=9 served=%d\n", served);
    close(ss);
    close(ls);
    return 0;
}
int do_recv(void) {
    build(); /* known-answer oracle only; repair never reads bku */
    int ll = tcpsock(), reuse = 1;
    setsockopt(ll, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof reuse);
    struct sockaddr_in ar;
    addr(&ar, PR);
    bind(ll, (struct sockaddr *)&ar, sizeof ar);
    listen(ll, 4);
    int haveu[NP] = { 0 }, havem = 0, got = 0, it = 0;
    uint8_t rpl[META];
    memset(rcv, 0, sizeof rcv);
    int cn = -1;
    if (waitfd(ll, 5000))
        cn = accept(ll, NULL, NULL);
    if (cn >= 0) {
        int nd = 1;
        setsockopt(cn, IPPROTO_TCP, TCP_NODELAY, &nd, sizeof nd);
        while (got < 9 && it++ < 40) {
            int pl = rxmsg(cn, 500);
            if (!pl)
                break;
            uint8_t k = rbuf[2], ix = rbuf[3];
            uint16_t ln = (uint16_t)(rbuf[4] | (rbuf[5] << 8));
            if (k == 0 && ix < NP && !haveu[ix] && ln == PL) {
                memcpy(rcv[ix], rbuf + 8, PL);
                haveu[ix] = 1;
                got++;
            } else if (k == 1 && !havem && ln == META) {
                memcpy(rpl, rbuf + 8, META);
                havem = 1;
                got++;
            }
        }
    }
    int lost[NP], nl = 0;
    for (int u = 0; u < NP; u++) {
        lost[u] = !haveu[u];
        nl += lost[u];
    }
    static uint32_t rref[NP][4];
    if (havem)
        memcpy(rref, rpl, 128);
    for (int p = 0; p < NP; p++) {
        if (lost[p])
            continue;
        sec_pkt(rcv[p], rref[p]);
    }
    int full = bytes_ok() == FR, fetch = 0;
    if (!full && havem && nl >= 1 && nl <= 2) {
        fetch = 1;
        int sf = tcpsock();
        struct sockaddr_in af;
        addr(&af, PF);
        if (!connect(sf, (struct sockaddr *)&af, sizeof af)) {
            uint8_t rq[1] = { 0 };
            txmsg(sf, rq, 1, 4, 0);
            uint8_t fP[PL], fQ[PL];
            int gotP = 0, gotQ = 0;
            for (int m = 0; m < 2; m++) {
                int pl = rxmsg(sf, 500);
                if (!pl)
                    break;
                if (rbuf[2] == 2) {
                    memcpy(fP, rbuf + 8, PL);
                    gotP = 1;
                }
                if (rbuf[2] == 3) {
                    memcpy(fQ, rbuf + 8, PL);
                    gotQ = 1;
                }
            }
            if (gotP && gotQ) {
                static uint8_t cat[2 * PL];
                memcpy(cat, fP, PL);
                memcpy(cat + PL, fQ, PL);
                uint64_t pc = 0;
                memcpy(&pc, rpl + 128, 8);
                if (ktag(BONDK, cat, 2 * PL, 0x50524F4D495345ull) ==
                    pc) {
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
                                    qq ^= gfm(gexp[p], rcv[p][i]);
                                }
                            uint8_t ua =
                                gf_div(qq ^ gfm(cb, pp), den);
                            rcv[L[0]][i] = ua;
                            rcv[L[1]][i] = pp ^ ua;
                        }
                    }
                    for (int p = 0; p < NP; p++)
                        if (lost[p])
                            sec_pkt(rcv[p], rref[p]);
                    full = bytes_ok() == FR;
                }
            }
        }
        close(sf);
    }
    printf("V got=%d lost=%d fetch=%d full=%d\n", got, nl, fetch,
           full);
    if (cn >= 0)
        close(cn);
    close(ll);
    return 0;
}
int main(int argc, char **argv) {
    signal(SIGPIPE, SIG_IGN);
    if (argc < 2) {
        printf("usage: tcp_cpeer send|recv\n");
        return 1;
    }
    if (!strcmp(argv[1], "send"))
        return do_send();
    if (!strcmp(argv[1], "recv"))
        return do_recv();
    printf("usage: tcp_cpeer send|recv\n");
    return 1;
}
