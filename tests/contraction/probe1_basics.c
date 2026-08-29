/* contraction behavior probes: each function prints bits of result */
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdint.h>
static void p(const char *n, double v) { uint64_t u; memcpy(&u,&v,8); printf("%-22s %016llx\n", n, (unsigned long long)u); }
volatile double a = 1.0000000000000002, b = 1.0000000000000004,
                c = -1.0000000000000001, d = 0.33333333333333331;
int main(void) {
    /* 1: within-expression a + b*c */
    double r1 = a + b * c;                       p("expr a+b*c", r1);
    /* 2: cross-statement single-use temp */
    double t2 = b * c; double r2 = a + t2;       p("stmt a+t(b*c)", r2);
    /* 3: cross-statement MULTI-use temp (used twice) */
    double t3 = b * c; double r3 = a + t3; double u3 = t3 * 2.0; p("multiuse a+t(b*c)", r3); p("  (keep alive)", u3);
    /* 4: a*b + c*d — which mul fuses? */
    double r4 = a * b + c * d;                   p("expr a*b+c*d", r4);
    double mab = a * b, mcd = c * d;
    p("  fma(a,b,cd)", fma(a, b, mcd));
    p("  fma(c,d,ab)", fma(c, d, mab));
    /* 5: subtraction forms */
    double r5 = a - b * c;                       p("expr a-b*c", r5);
    p("  fma(-b,c,a)", fma(-b, c, a));
    double r6 = b * c - a;                       p("expr b*c-a", r6);
    p("  fma(b,c,-a)", fma(b, c, -a));
    /* 6: negated product -(b*c) + a */
    double r7 = -(b * c) + a;                    p("expr -(b*c)+a", r7);
    p("  fma(-b,c,a)=", fma(-b, c, a));
    /* 7: chained: (a*b+c)*d + ... nesting */
    double r8 = (a * b + c) * d;                 p("expr (a*b+c)*d", r8);
    p("  fma(a,b,c)*d", fma(a, b, c) * d);
    /* 8: add then mul: (a+b)*c — NOT fusible */
    double r9 = (a + b) * c;                     p("expr (a+b)*c", r9);
    /* 9: accumulation loop pattern across statements */
    double acc = 0.0;
    for (int i = 0; i < 4; i++) acc = acc + a * b;
    p("loop acc=acc+a*b", acc);
    double acc2 = 0.0;
    for (int i = 0; i < 4; i++) acc2 = fma(a, b, acc2);
    p("loop fma(a,b,acc)", acc2);
    /* 10: division present: a + (b/c)*d — can (b/c)*d fuse with +? no (div not mul) but *d with + */
    double r10 = a + (b / c) * d;                p("expr a+(b/c)*d", r10);
    p("  fma(b/c,d,a)", fma(b / c, d, a));
    return 0;
}
