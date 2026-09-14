/* tcp_proxy.c -- fixed-plan fault proxy for TCP interop. Listens PS,
 * accepts sender; connects PR; forwards 9 framed messages with argv
 * damage; prints "X fwd=<n> drop=<d> flip=<f>".
 * Plans: clean | drop=U[,..] | flip=U:OFF:DV[,..]
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <sys/select.h>
#include <signal.h>

#define PS 41001
#define PR 41002

static int drops[8], ndrop;
static int flips[16][3], nflip;
static uint8_t msg[528];

static void addr(struct sockaddr_in *a, int port) {
    memset(a, 0, sizeof *a);
    a->sin_family = AF_INET;
    a->sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    a->sin_port = htons((uint16_t)port);
}
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
/* read one framed message into msg; returns paylen or 0 */
static int rdmsg(int fd) {
    uint8_t lp[2];
    size_t got = 0;
    while (got < 2) {
        if (!waitfd(fd, 1500))
            return 0;
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
        if (!waitfd(fd, 1500))
            return 0;
        ssize_t n = recv(fd, msg + got, ml - got, 0);
        if (n <= 0)
            return 0;
        got += (size_t)n;
    }
    return ml - 8;
}
static void fwmsg(int fd) {
    uint16_t ml = (uint16_t)(msg[4] | (msg[5] << 8)) + 8;
    uint8_t lp[2] = { (uint8_t)(ml & 255), (uint8_t)(ml >> 8) };
    sendall(fd, lp, 2);
    sendall(fd, msg, ml);
}
int main(int argc, char **argv) {
    signal(SIGPIPE, SIG_IGN);
    for (int i = 1; i < argc; i++) {
        if (!strncmp(argv[i], "drop=", 5)) {
            char *s = argv[i] + 5, *tok = strtok(s, ",");
            while (tok && ndrop < 8) {
                drops[ndrop++] = atoi(tok);
                tok = strtok(NULL, ",");
            }
        } else if (!strncmp(argv[i], "flip=", 5)) {
            char *s = argv[i] + 5, *tok = strtok(s, ",");
            while (tok && nflip < 16) {
                int u, o;
                unsigned dv;
                if (sscanf(tok, "%d:%d:%x", &u, &o, &dv) == 3) {
                    flips[nflip][0] = u;
                    flips[nflip][1] = o;
                    flips[nflip][2] = (int)(dv & 255);
                    nflip++;
                }
                tok = strtok(NULL, ",");
            }
        }
    }
    int ll = socket(AF_INET, SOCK_STREAM, 0), reuse = 1, nd = 1;
    setsockopt(ll, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof reuse);
    struct sockaddr_in a1;
    addr(&a1, PS);
    bind(ll, (struct sockaddr *)&a1, sizeof a1);
    listen(ll, 4);
    int si = -1;
    if (waitfd(ll, 8000))
        si = accept(ll, NULL, NULL);
    if (si < 0) {
        printf("X fwd=0 drop=0 flip=0\n");
        return 1;
    }
    setsockopt(si, IPPROTO_TCP, TCP_NODELAY, &nd, sizeof nd);
    int so = socket(AF_INET, SOCK_STREAM, 0);
    setsockopt(so, IPPROTO_TCP, TCP_NODELAY, &nd, sizeof nd);
    struct sockaddr_in a2;
    addr(&a2, PR);
    if (connect(so, (struct sockaddr *)&a2, sizeof a2)) {
        printf("X fwd=0 drop=0 flip=0\n");
        return 1;
    }
    int fwd = 0, fd = 0, ff = 0;
    for (int m = 0; m < 9; m++) {
        int pl = rdmsg(si);
        if (!pl)
            break;
        uint8_t k = msg[2], ix = msg[3];
        if (k == 0) {
            int drop = 0;
            for (int d = 0; d < ndrop; d++)
                if (drops[d] == ix)
                    drop = 1;
            if (drop) {
                fd++;
                continue;
            }
            for (int f = 0; f < nflip; f++)
                if (flips[f][0] == ix && flips[f][1] < pl) {
                    msg[8 + flips[f][1]] ^= (uint8_t)flips[f][2];
                    ff++;
                }
        }
        fwmsg(so);
        fwd++;
    }
    printf("X fwd=%d drop=%d flip=%d\n", fwd, fd, ff);
    close(si);
    close(so);
    close(ll);
    return 0;
}
