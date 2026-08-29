#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
static void p64(const char*n, double v){uint64_t u;memcpy(&u,&v,8);printf("%-30s %016llx\n",n,(unsigned long long)u);}
static void p32(const char*n, float v){uint32_t u;memcpy(&u,&v,4);printf("%-30s %08x\n",n,u);}
volatile double a = 1.0000000000000002, b = 1.0000000000000004, c = -1.0000000000000001;
volatile float fa = 1.0000001f, fb = 1.0000002f, fc = -0.99999994f;
int main(void){
    /* f64: discriminating add-mul (from probe5 values) */
    volatile double A = 0x1.049da838af05cp+3, B = 0x1.74cea82854b7ep+2,
                    C = 0x1.56e4be93e9d1fp+0, D = 0x1.f529ef22f4506p+0;
    volatile double m1 = A*B;          /* barrier: unfused product */
    volatile double m2 = C*D;
    p64("f64 unfused m1+m2", m1 + m2);
    p64("f64 compiler A*B+C*D", A*B + C*D);
    p64("f64 fma(A,B,m2)", fma(A,B,m2));
    p64("f64 fma(C,D,m1)", fma(C,D,m1));
    /* f64 simple a + b*c with cancellation */
    volatile double mb = b*c;
    p64("f64 unfused a+mb", a + mb);
    p64("f64 compiler a+b*c", a + b*c);
    p64("f64 fma(b,c,a)", fma(b,c,a));
    /* f32 same shapes */
    volatile float fmb = fb*fc;
    p32("f32 unfused fa+fmb", fa + fmb);
    p32("f32 compiler fa+fb*fc", fa + fb*fc);
    p32("f32 fmaf(fb,fc,fa)", fmaf(fb,fc,fa));
    /* f32 discriminating (non-cancelling) */
    volatile float ga = 1.25f, gb = 1.0000002f, gc = 1.0000004f;
    volatile float gmb = gb*gc;
    p32("f32 unfused ga+gmb", ga + gmb);
    p32("f32 compiler ga+gb*gc", ga + gb*gc);
    p32("f32 fmaf(gb,gc,ga)", fmaf(gb,gc,ga));
    return 0;
}
