#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
static uint64_t bits(double v){uint64_t u;memcpy(&u,&v,8);return u;}
static void p(const char*n, double v){printf("%-24s %016llx\n", n, (unsigned long long)bits(v));}
volatile double a, b, c, d;
static void setv(void) {
    a = 0x1.049da838af05cp+3; b = 0x1.74cea82854b7ep+2;
    c = 0x1.56e4be93e9d1fp+0; d = 0x1.f529ef22f4506p+0;
}
int main(void){
    setv();
    p("a*b + c*d  (compiler)", a*b + c*d);
    p("fma(a,b,c*d)", fma(a,b,c*d));
    p("fma(c,d,a*b)", fma(c,d,a*b));
    /* and with statements split like generated code */
    double t1 = a * b;
    double t2 = c * d;
    double r = t1 + t2;
    p("stmt-split t1+t2", r);
    /* reversed source order: c*d + a*b */
    p("c*d + a*b  (compiler)", c*d + a*b);
    return 0;
}
