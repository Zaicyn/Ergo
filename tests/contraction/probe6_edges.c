#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
static uint64_t bits(double v){uint64_t u;memcpy(&u,&v,8);return u;}
static void p(const char*n, double v){printf("%-28s %016llx\n", n, (unsigned long long)bits(v));}
volatile double a = 0x1.049da838af05cp+3, b = 0x1.74cea82854b7ep+2,
                c = 0x1.56e4be93e9d1fp+0, d = 0x1.f529ef22f4506p+0;
volatile int cond = 1;
int main(void){
    /* mul-by-2.0 (strength reduction candidate) feeding add */
    p("a*2.0 + c", a * 2.0 + c);
    p("fma(a,2.0,c)", fma(a, 2.0, c));
    p("(a+a)+c", (a + a) + c);
    /* mul-by-0.5 feeding add */
    p("a*0.5 + c", a * 0.5 + c);
    p("fma(a,0.5,c)", fma(a, 0.5, c));
    /* cross-BB: mul in if-branch, add after */
    double t;
    if (cond) t = a * b; else t = c * d;
    p("if-mul then add", t + a);
    p("  fma(a,b,a)", fma(a, b, a));
    /* mul in loop-invariant position, add inside */
    double m = a * b, acc = 0;
    for (int i = 0; i < 3; i++) acc += m;   /* acc = acc + m: m is mul result */
    p("acc += (a*b) loop", acc);
    /* f32 check */
    float fa = 1.0000001f, fb = 1.0000002f, fc = -0.99999994f;
    float fr = fa + fb * fc;
    float ff = fmaf(fb, fc, fa);
    p("f32 a+b*c", fr); p("f32 fmaf", ff);
    /* div feeding mul feeding add */
    p("a + (b/c)*d", a + (b / c) * d);
    p("fma(b/c,d,a)", fma(b / c, d, a));
    /* mul feeding sub where SUB is first: c - a*b */
    p("c - a*b", c - a * b);
    p("fma(-a,b,c)", fma(-a, b, c));
    return 0;
}
