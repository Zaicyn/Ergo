/* udp_proxy.c -- fixed-plan fault proxy for asm/C interop.
 * Binds PS, forwards 9 datagrams to PR with argv damage, then exits.
 * Plans: clean | drop=U[,..] | flip=U:OFF:DV[,..] (decimal, DV hex ok)
 * Example: udp_proxy drop=3 flip=2:100:0x5A
 * Prints: "X fwd=<n> drop=<d> flip=<f>"
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/select.h>

#define PS 41001
#define PR 41002

static int drops[8], ndrop;
static int flips[16][3], nflip;
static uint8_t buf[2048], out[2048];

static int waitfd(int fd, int ms) {
    fd_set rf;
    FD_ZERO(&rf);
    FD_SET(fd, &rf);
    struct timeval tv = { ms / 1000, (ms % 1000) * 1000 };
    return select(fd + 1, &rf, NULL, NULL, &tv);
}
int main(int argc, char **argv) {
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
    int si = socket(AF_INET, SOCK_DGRAM, 0);
    int so = socket(AF_INET, SOCK_DGRAM, 0);
    struct sockaddr_in ai, ao;
    memset(&ai, 0, sizeof ai);
    ai.sin_family = AF_INET;
    ai.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    ai.sin_port = htons(PS);
    bind(si, (struct sockaddr *)&ai, sizeof ai);
    memset(&ao, 0, sizeof ao);
    ao.sin_family = AF_INET;
    ao.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    ao.sin_port = htons(PR);
    int fwd = 0, fd = 0, ff = 0;
    for (int m = 0; m < 9; m++) {
        if (!waitfd(si, 1500))
            break;
        ssize_t n = recv(si, buf, sizeof buf, 0);
        if (n < 8)
            continue;
        uint8_t k = buf[2], ix = buf[3];
        if (k == 0) {
            int drop = 0;
            for (int d = 0; d < ndrop; d++)
                if (drops[d] == ix)
                    drop = 1;
            if (drop) {
                fd++;
                continue;
            }
            memcpy(out, buf, (size_t)n);
            for (int f = 0; f < nflip; f++)
                if (flips[f][0] == ix &&
                    flips[f][1] < (int)n - 8) {
                    out[8 + flips[f][1]] ^= (uint8_t)flips[f][2];
                    ff++;
                }
            sendto(so, out, (size_t)n, 0, (struct sockaddr *)&ao,
                   sizeof ao);
        } else {
            sendto(so, buf, (size_t)n, 0, (struct sockaddr *)&ao,
                   sizeof ao);
        }
        fwd++;
    }
    printf("X fwd=%d drop=%d flip=%d\n", fwd, fd, ff);
    return 0;
}
