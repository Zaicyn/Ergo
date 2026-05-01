/*
 * Petroff 2021 equal-area quincuncial projection.
 * Forward mapping: sphere (latitude phi, longitude lambda) -> square (xm, ym) in [-1,1].
 * Equations 1-41 from the paper. phi_0 = 3*pi/8.
 */

#define PI      3.14159265359
#define SQRT2   1.41421356237
#define SQRT3   1.73205080757

/* Precomputed constants for phi_0 = 3*pi/8 */
#define PHI_0   1.17809724510  /* 3*pi/8 */

/* Eq 1: psi_0 = arcsin(1 / sqrt(2 - cos^2(phi_0))) */
float get_psi_0() {
    float cp0 = cos(PHI_0);
    return asin(1.0 / sqrt(2.0 - cp0 * cp0));
}

/* Eq 2: psi_1 = pi - 2*psi_0 */
float get_psi_1(float psi_0) { return PI - 2.0 * psi_0; }

/* Eq 3: rho = arcsin(2*sin(phi_0) / (sqrt(3) - cos(2*phi_0))) */
float get_rho() {
    return asin(2.0 * sin(PHI_0) / (SQRT3 - cos(2.0 * PHI_0)));
}

/* Eq 9: h' = (12/pi) * (psi_0 + rho - pi/2) */
float get_h_prime(float psi_0, float rho) {
    return (12.0 / PI) * (psi_0 + rho - PI / 2.0);
}

/* Eq 11: xi' = arctan(...) */
float get_xi_prime(float h_prime, float psi_0, float rho) {
    float num = PI * (h_prime - 3.0) * (h_prime - 3.0);
    float den = SQRT3 * (PI * (h_prime * h_prime - 2.0 * h_prime + 45.0) - 96.0 * psi_0 - 48.0 * rho);
    return atan(num / den);
}

vec2 petroff_forward(float phi, float lambda) {
    float psi_0 = get_psi_0();
    float psi_1 = get_psi_1(psi_0);
    float rho = get_rho();
    float h_prime = get_h_prime(psi_0, rho);
    float xi_prime = get_xi_prime(h_prime, psi_0, rho);

    /* Eq 4-7: Euclidean sub-triangle angles */
    float psi_0_prime = atan(SQRT3 / h_prime);
    float psi_1_prime = 7.0 * PI / 6.0 - psi_0_prime - xi_prime;
    float psi_2_prime = xi_prime - PI / 6.0;
    float rho_prime = atan(h_prime / SQRT3);

    /* Restrict to positive latitudes, centered longitudes */
    float phi_c = abs(phi);
    float lambda_c = lambda - PI / 4.0;

    /* Eq 12-13: octant index and dividing longitude */
    int q = int(floor(2.0 * lambda_c / PI));
    float lambda_0 = (PI / 2.0) * float(q);

    /* Eq 14: theta - angle around dividing point */
    float theta = abs(atan(
        cos(phi_c) * sin(lambda_c - lambda_0),
        sin(PHI_0) * cos(phi_c) * cos(lambda_c - lambda_0) - cos(PHI_0) * sin(phi_c)
    ));

    /* Eq 15: r - distance from dividing point */
    float r = acos(clamp(
        sin(PHI_0) * sin(phi_c) + cos(PHI_0) * cos(phi_c) * cos(lambda_c - lambda_0),
        -1.0, 1.0));

    /* Eq 16: beta */
    float beta;
    if (theta <= psi_0) beta = psi_0 - theta;
    else if (theta <= psi_0 + psi_1) beta = theta - psi_0;
    else beta = PI - theta;

    /* Eq 17: c - hypotenuse of sub-triangle */
    float c;
    if (theta <= psi_0 + psi_1) c = acos(cos(PHI_0) / SQRT2);
    else c = PI / 2.0 - PHI_0;

    /* Eq 18-19: G, G' */
    float G, G_prime;
    if (theta <= psi_0) { G = psi_0; G_prime = psi_0_prime; }
    else if (theta <= psi_0 + psi_1) { G = psi_1; G_prime = psi_1_prime; }
    else { G = psi_0; G_prime = psi_2_prime; }

    /* Eq 20: F */
    float F;
    if (theta <= psi_0) F = rho;
    else if (theta <= psi_0 + psi_1) F = PI / 2.0 - rho;
    else F = PI / 4.0;

    /* Eq 21: a' */
    float a_prime;
    if (theta <= psi_0) a_prime = h_prime;
    else a_prime = sqrt(h_prime * h_prime + 3.0) * sin(PI / 3.0 - rho_prime) / sin(xi_prime);

    /* Eq 22: c' */
    float c_prime;
    if (theta <= psi_0 + psi_1) c_prime = sqrt(h_prime * h_prime + 3.0);
    else c_prime = 3.0 - h_prime;

    /* Eq 23: x - distance from octant corner on sphere */
    float x = acos(clamp(cos(r) * cos(c) + sin(r) * sin(c) * cos(beta), -1.0, 1.0));

    /* Eq 24: gamma */
    float gamma = asin(clamp(sin(beta) * sin(r) / sin(x), -1.0, 1.0));

    /* Eq 25: epsilon */
    float epsilon = acos(clamp(sin(G) * sin(gamma) * cos(c) - cos(G) * cos(gamma), -1.0, 1.0));

    /* Eq 26: u'/(u'+v') ratio */
    float uv_ratio = (gamma + epsilon - PI) / (F + G - PI / 2.0);

    /* Eq 27-28: cos(x+y) and x'/(x'+y') */
    float sinGsinc = sin(G) * sin(c);
    float sineps = sin(epsilon);
    float cos_xpy = (sineps > 1e-10) ? sqrt(1.0 - (sinGsinc / sineps) * (sinGsinc / sineps)) : 1.0;
    float xy_ratio = (x > 1e-10) ? sqrt((1.0 - cos(x)) / (1.0 - cos_xpy)) : 0.0;

    /* Eq 29: u' */
    float u_prime = a_prime * uv_ratio;

    /* Eq 30: x'+y' */
    float xpy = sqrt(u_prime * u_prime + c_prime * c_prime - 2.0 * u_prime * c_prime * cos(G_prime));

    /* Eq 31-32: cos gamma', x' */
    float cos_gamma_prime = (xpy > 1e-10) ? sqrt(1.0 - (u_prime * sin(G_prime) / xpy) * (u_prime * sin(G_prime) / xpy)) : 1.0;
    float x_prime = xpy * xy_ratio;
    float y_prime = xpy - x_prime;

    /* Eq 34-35: r', alpha' in Euclidean polar coords */
    float r_prime = sqrt(x_prime * x_prime + c_prime * c_prime - 2.0 * x_prime * c_prime * cos_gamma_prime);
    float alpha_prime = (r_prime > 1e-10) ? acos(clamp((y_prime * y_prime - u_prime * u_prime - r_prime * r_prime) / (-2.0 * u_prime * r_prime), -1.0, 1.0)) : 0.0;

    /* Eq 36: theta' - angle on Euclidean triangle */
    float theta_prime;
    if (theta <= psi_0) theta_prime = alpha_prime;
    else if (theta <= psi_0 + psi_1) theta_prime = 7.0 * PI / 6.0 - xi_prime - alpha_prime;
    else theta_prime = 7.0 * PI / 6.0 - xi_prime + alpha_prime;

    /* Eq 37-38: Cartesian coords relative to equilateral triangle */
    float x_c = sign(lambda_c - lambda_0) * r_prime * sin(theta_prime);
    float y_c = h_prime - r_prime * cos(theta_prime);

    /* Eq 39: hemisphere separation */
    float y_h;
    if (phi >= 0.0) y_h = y_c;
    else y_h = -y_c - 6.0 + y_c;  /* y_c * sgn(phi) - 3 simplified for negative */

    /* Actually eq 39: y_h = y_c * sgn(phi) - 3 ... but only for south hemisphere */
    if (phi < 0.0) y_h = y_c - 3.0;  /* sgn = -1: y_h = y_c*(-1) ... wait */
    /* Re-reading: y_h = y_c sgn phi - 3. For phi>=0: y_h = y_c - 3?? No... */
    /* Eq 39 says y_h = y_c * sgn(phi) - 3. So:
     *   phi >= 0: y_h = y_c - 3
     *   phi <  0: y_h = -y_c - 3
     * But the paper says y_c >= -3 separates hemispheres (eq 50). */
    y_h = y_c * sign(phi) - 3.0;

    /* Eq 40-41: squish into quincuncial square */
    float zeta = PI / 4.0 + (PI / 2.0) * float(q);
    float scale = SQRT3 / (3.0 * SQRT2);
    float x_m = (x_c * cos(zeta) - y_h * sin(zeta) / SQRT3) * scale;
    float y_m = (x_c * sin(zeta) + y_h * cos(zeta) / SQRT3) * scale;

    return vec2(x_m, y_m);
}

/* Main entry: direction vector -> UV in [0,1]^2 */
vec2 petroff_uv(vec3 dir) {
    dir = normalize(dir);
    float phi = asin(clamp(dir.y, -1.0, 1.0));
    float lambda = atan(dir.x, dir.z) + PI;  /* [0, 2*pi] */

    vec2 xy = petroff_forward(phi, lambda);
    return clamp(xy * 0.5 + 0.5, vec2(0.0), vec2(1.0));
}
