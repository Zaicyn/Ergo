#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
static void p(const char *n, double v) { uint64_t u; memcpy(&u,&v,8); printf("%-26s %016llx\n", n, (unsigned long long)u); }
/* values chosen so fma(a,b,cd) and fma(c,d,ab) differ */
volatile double a = 1.0000000000000002, b = 1.0000000000000004,
                c = 1.0000000000000007, d = 1.0000000000000011;
int main(void) {
    double mab = a * b, mcd = c * d;
    double r = a * b + c * d;
    p("a*b + c*d (compiler)", r);
    p("fma(a,b, c*d)", fma(a, b, mcd));
    p("fma(c,d, a*b)", fma(c, d, mab));
    double r2 = a * b - c * d;
    p("a*b - c*d (compiler)", r2);
    p("fma(a,b, -(c*d))", fma(a, b, -mcd));
    p("-(fma(c,d, -a*b))", -(fma(c, d, -mab)));
    p("fma(-c,d, a*b)", fma(-c, d, mab));
    /* triple: (a*b + c*d) + b*c */
    volatile double e = 0.9999999999999991;
    double r3 = a * b + c * d + e * b;   /* left assoc: ((ab)+(cd))+(eb) */
    p("(ab+cd)+eb compiler", r3);
    /* fusing options: inner: fma(c,d,ab) or fma(a,b,cd); outer: fma(e,b, inner) */
    double i1 = fma(c, d, mab), i2 = fma(a, b, mcd);
    p("fma(e,b, i1=fma(c,d,ab))", fma(e, b, i1));
    p("fma(e,b, i2=fma(a,b,cd))", fma(e, b, i2));
    /* does a mul feeding TWO adds both fuse? */
    double m = a * b;
    double r4 = m + c, r5 = e - m;
    p("m+c", r4); p("e-m", r5);
    p("fma(a,b,c)", fma(a,b,c)); p("fma(-a,b,e)", fma(-a,b,e));
    return 0;
}
