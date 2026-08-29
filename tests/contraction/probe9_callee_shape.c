#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
static void p(const char*n, double v){uint64_t u;memcpy(&u,&v,8);printf("%-40s %016llx\n",n,(unsigned long long)u);}
/* multi-return inline callee (like _ergo_cos's switch-return shape) */
static inline double multi_ret(double x) {
    if (x > 100.0) return x - x;
    switch ((int)(x > 0) + 2 * (int)(x > 50)) {
    case 0: return x * 1.1;
    case 1: return x * 1.2;
    default: return x * 1.3;
    }
}
/* single-return inline callee (like _ergo_sin's switch-break shape) */
static inline double single_ret(double x) {
    double v;
    if (x > 100.0) { v = x - x; }
    else switch ((int)(x > 0) + 2 * (int)(x > 50)) {
    case 0: v = x * 1.1; break;
    case 1: v = x * 1.2; break;
    default: v = x * 1.3; break;
    }
    return v;
}
__attribute__((noinline)) static double noret_multi(double x) {
    if (x > 100.0) return x - x;
    if (x > 0) return x * 1.1;
    return x * 1.3;
}
volatile double base = 0.37;
int main(void) {
    /* accumulate with mul by constant after each callee shape */
    double S1 = 0, S2 = 0, S3 = 0, S4 = 0;
    for (int i = 1; i <= 100; i++) {
        double X = i * 0.001;
        double a = multi_ret(X);
        double b = a * 0.73;
        S1 = S1 + b;
        double c = single_ret(X);
        double d = c * 0.73;
        S2 = S2 + d;
        double e2 = noret_multi(X);
        double f2 = e2 * 0.73;
        S3 = S3 + f2;
        S4 = S4 + X * 0.73;   /* no call — control */
    }
    p("S += multi_ret_inline(X)*k", S1);
    p("S += single_ret_inline(X)*k", S2);
    p("S += noinline_multi(X)*k", S3);
    p("S += X*k (control)", S4);
    return 0;
}
