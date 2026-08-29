#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
static void p(const char*n, double v){uint64_t u;memcpy(&u,&v,8);printf("%-30s %016llx\n",n,(unsigned long long)u);}
volatile double a = 0x1.049da838af05cp+3, b = 0x1.74cea82854b7ep+2,
                c = 0x1.56e4be93e9d1fp+0;
int main(void){
    p("-(a*b) + c", -(a*b) + c);
    p("fma(-a,b,c)", fma(-a,b,c));
    p("c - (-(a*b))", c - (-(a*b)));
    p("fma(a,b,c)", fma(a,b,c));
    /* sub with NEG-mul on right: x - (-(a*b)) where neg is separate */
    volatile double n1 = -(a*b);
    p("stmt c - n1(-ab)", c - n1);
    /* mul of neg: (-a)*b + c — factor sign is exact */
    p("(-a)*b + c", (-a)*b + c);
    p("fma(-a,b,c) #2", fma(-a,b,c));
    /* add where the SAME mul feeds twice: t=a*b; t+t */
    volatile double t = a*b;
    p("t+t", t + t);
    p("fma(a,b,t)", fma(a,b,t));
    return 0;
}
