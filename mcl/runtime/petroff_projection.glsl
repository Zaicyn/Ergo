/*
 * Petroff 2021 equal-area quincuncial projection — GLSL port.
 * Ported from reference/petroff_supplement/new_projection.py (public domain).
 *
 * Forward: (lambda, phi) -> (x_m, y_m) in [-1, 1]
 * Input: direction vector
 * Output: UV in [0, 1]^2
 */

#define PI      3.14159265359
#define SQRT2   1.41421356237
#define SQRT3   1.73205080757
#define PHI_0   1.17809724510  /* 3*pi/8 */

vec2 petroff_uv(vec3 dir) {
    dir = normalize(dir);
    float phi = asin(clamp(dir.y, -1.0, 1.0));
    float lambda_ = atan(dir.x, dir.z) + PI;  /* [0, 2*pi] */

    /* Precomputed constants */
    float cos_phi0 = cos(PHI_0);
    float sin_phi0 = sin(PHI_0);
    float psi0 = asin(1.0 / sqrt(2.0 - cos_phi0 * cos_phi0));
    float rho = asin(2.0 * sin_phi0 / sqrt(3.0 - cos(2.0 * PHI_0)));
    float hprime = (12.0 / PI) * (psi0 + rho - PI / 2.0);
    float xiprime = atan(
        (PI * (hprime - 3.0) * (hprime - 3.0)) /
        (SQRT3 * (PI * (hprime * hprime - 2.0 * hprime + 45.0)
                  - 96.0 * psi0 - 48.0 * rho))
    );

    float phi_c = abs(phi);
    float lambda_c = lambda_ - PI / 4.0;

    float quadrant = floor(2.0 * lambda_ / PI);
    float lambda0 = quadrant * PI / 2.0;

    float theta = abs(atan(
        cos(phi_c) * sin(lambda_c - lambda0),
        sin_phi0 * cos(phi_c) * cos(lambda_c - lambda0) - cos_phi0 * sin(phi_c)
    ));
    float r = acos(clamp(
        sin_phi0 * sin(phi_c) + cos_phi0 * cos(phi_c) * cos(lambda_c - lambda0),
        -1.0, 1.0));

    float psi1 = PI - 2.0 * psi0;

    /* beta (eq 16) */
    float beta;
    if (theta <= psi0) beta = psi0 - theta;
    else if (theta <= psi0 + psi1) beta = theta - psi0;
    else beta = PI - theta;

    /* c (eq 17) */
    float c;
    if (theta <= psi0 + psi1) c = acos(cos_phi0 / SQRT2);
    else c = PI / 2.0 - PHI_0;

    /* G (eq 18) */
    float G;
    if (theta <= psi0) G = psi0;
    else if (theta <= psi0 + psi1) G = psi1;
    else G = psi0;

    /* G', psi primes (eq 4-6, 19) */
    float psi0prime = atan(SQRT3 / hprime);
    float psi1prime = 7.0 * PI / 6.0 - psi0prime - xiprime;
    float psi2prime = xiprime - PI / 6.0;

    float Gprime;
    if (theta <= psi0) Gprime = psi0prime;
    else if (theta <= psi0 + psi1) Gprime = psi1prime;
    else Gprime = psi2prime;

    /* F (eq 20) */
    float F;
    if (theta <= psi0) F = rho;
    else if (theta <= psi0 + psi1) F = PI / 2.0 - rho;
    else F = PI / 4.0;

    /* a' (eq 21) */
    float aprime;
    if (theta <= psi0) aprime = hprime;
    else aprime = sqrt(hprime * hprime + 3.0) *
                  sin(PI / 3.0 - atan(hprime / SQRT3)) / sin(xiprime);

    /* c' (eq 22) */
    float cprime;
    if (theta <= psi0 + psi1) cprime = sqrt(hprime * hprime + 3.0);
    else cprime = 3.0 - hprime;

    /* x (eq 23) */
    float x = acos(clamp(cos(r) * cos(c) + sin(r) * sin(c) * cos(beta), -1.0, 1.0));

    /* gamma (eq 24) */
    float gamma = 0.0;
    if (x > 1e-10)
        gamma = asin(clamp(sin(beta) * sin(r) / sin(x), -1.0, 1.0));

    /* epsilon (eq 25) */
    float epsilon = acos(clamp(
        sin(G) * sin(gamma) * cos(c) - cos(G) * cos(gamma), -1.0, 1.0));

    /* u'/(u'+v') (eq 26) */
    float upupvp = (gamma + G + epsilon - PI) / (F + G - PI / 2.0);

    /* cos(x+y), x'/(x'+y') (eq 27-28) */
    float sinGsinc_over_sineps = sin(G) * sin(c) / max(sin(epsilon), 1e-10);
    float cos_xy = sqrt(max(1.0 - sinGsinc_over_sineps * sinGsinc_over_sineps, 0.0));
    float xpxpyp = sqrt(max((1.0 - cos(x)) / max(1.0 - cos_xy, 1e-10), 0.0));

    /* u' (eq 29) */
    float uprime = aprime * upupvp;

    /* x'+y' (eq 30) */
    float xpyp = sqrt(max(uprime * uprime + cprime * cprime
                          - 2.0 * uprime * cprime * cos(Gprime), 0.0));

    /* cos gamma' (eq 31) */
    float uGp_over_xpyp = uprime * sin(Gprime) / max(xpyp, 1e-10);
    float cos_gammaprime = sqrt(max(1.0 - uGp_over_xpyp * uGp_over_xpyp, 0.0));

    /* x', y' (eq 32-33) */
    float xprime = xpyp * xpxpyp;
    float yprime = xpyp - xprime;

    /* r', alpha' (eq 34-35) */
    float rprime = sqrt(max(xprime * xprime + cprime * cprime
                            - 2.0 * xprime * cprime * cos_gammaprime, 0.0));

    float alphaprime;
    if (uprime * rprime <= 1e-10) {
        alphaprime = xiprime - PI / 6.0;
    } else {
        float cos_alpha = (yprime * yprime - uprime * uprime - rprime * rprime)
                          / (-2.0 * uprime * rprime);
        alphaprime = acos(clamp(cos_alpha, -1.0, 1.0));
    }

    /* theta' (eq 36) */
    float thetaprime;
    if (theta <= psi0)
        thetaprime = alphaprime;
    else if (theta <= psi0 + psi1)
        thetaprime = PI - psi2prime - alphaprime;
    else
        thetaprime = PI - psi2prime + alphaprime;

    /* x_c, y_c (eq 37-38) */
    float sign_lc = (lambda_c - lambda0 >= 0.0) ? 1.0 : -1.0;
    float x_c = sign_lc * rprime * sin(thetaprime);
    float y_c = hprime - rprime * cos(thetaprime);

    /* y_h (eq 39) */
    float y_h = y_c * sign(phi) - 3.0;

    /* Squish to square (eq 40-41) */
    float zeta = PI / 4.0 + quadrant * PI / 2.0;
    float scale = SQRT3 / (3.0 * SQRT2);
    float x_m = (x_c * cos(zeta) - y_h * sin(zeta) / SQRT3) * scale;
    float y_m = (x_c * sin(zeta) + y_h * cos(zeta) / SQRT3) * scale;

    /* Map [-1,1] to [0,1] */
    return clamp(vec2(x_m, y_m) * 0.5 + 0.5, vec2(0.0), vec2(1.0));
}
