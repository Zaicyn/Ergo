#version 450

layout(location = 0) in vec3  v_world_pos;
layout(location = 1) in vec3  v_normal;
layout(location = 2) in flat float v_cell_idx;
layout(location = 0) out vec4 frag_color;
layout(set = 0, binding = 2) readonly buffer AtlasBuf { uint atlas_pixels[]; };
layout(set = 0, binding = 5) uniform RenderParams {
    mat4 viewProj; float cam_x, cam_y, cam_z; float cull_mode;
    float val_min, val_max; float world_scale; float pad;
} pc;

/* --- Petroff projection (identical to atlas_gen.comp) --- */
#define PI      3.14159265359
#define SQRT2   1.41421356237
#define SQRT3   1.73205080757
#define PHI_0   1.17809724510

vec2 petroff_uv(vec3 dir) {
    dir = normalize(dir);
    float phi = asin(clamp(dir.y, -1.0, 1.0));
    float lambda_ = atan(dir.x, dir.z) + PI;
    float cos_phi0 = cos(PHI_0); float sin_phi0 = sin(PHI_0);
    float psi0 = asin(1.0 / sqrt(2.0 - cos_phi0 * cos_phi0));
    float rho_v = asin(2.0 * sin_phi0 / sqrt(3.0 - cos(2.0 * PHI_0)));
    float hprime = (12.0 / PI) * (psi0 + rho_v - PI / 2.0);
    float xiprime = atan((PI * (hprime - 3.0) * (hprime - 3.0)) /
        (SQRT3 * (PI * (hprime * hprime - 2.0 * hprime + 45.0) - 96.0 * psi0 - 48.0 * rho_v)));
    float phi_c = abs(phi); float lambda_c = lambda_ - PI / 4.0;
    float quadrant = floor(2.0 * lambda_ / PI);
    float lambda0 = quadrant * PI / 2.0;
    float theta = abs(atan(cos(phi_c) * sin(lambda_c - lambda0),
        sin_phi0 * cos(phi_c) * cos(lambda_c - lambda0) - cos_phi0 * sin(phi_c)));
    float r = acos(clamp(sin_phi0 * sin(phi_c) + cos_phi0 * cos(phi_c) * cos(lambda_c - lambda0), -1.0, 1.0));
    float psi1 = PI - 2.0 * psi0;
    float beta; if (theta <= psi0) beta = psi0 - theta; else if (theta <= psi0 + psi1) beta = theta - psi0; else beta = PI - theta;
    float c; if (theta <= psi0 + psi1) c = acos(cos_phi0 / SQRT2); else c = PI / 2.0 - PHI_0;
    float G; if (theta <= psi0) G = psi0; else if (theta <= psi0 + psi1) G = psi1; else G = psi0;
    float psi0prime = atan(SQRT3 / hprime);
    float psi1prime = 7.0 * PI / 6.0 - psi0prime - xiprime;
    float psi2prime = xiprime - PI / 6.0;
    float Gprime; if (theta <= psi0) Gprime = psi0prime; else if (theta <= psi0 + psi1) Gprime = psi1prime; else Gprime = psi2prime;
    float F; if (theta <= psi0) F = rho_v; else if (theta <= psi0 + psi1) F = PI / 2.0 - rho_v; else F = PI / 4.0;
    float aprime; if (theta <= psi0) aprime = hprime; else aprime = sqrt(hprime * hprime + 3.0) * sin(PI / 3.0 - atan(hprime / SQRT3)) / sin(xiprime);
    float cprime; if (theta <= psi0 + psi1) cprime = sqrt(hprime * hprime + 3.0); else cprime = 3.0 - hprime;
    float x = acos(clamp(cos(r) * cos(c) + sin(r) * sin(c) * cos(beta), -1.0, 1.0));
    float gamma_v = 0.0; if (x > 1e-10) gamma_v = asin(clamp(sin(beta) * sin(r) / sin(x), -1.0, 1.0));
    float epsilon = acos(clamp(sin(G) * sin(gamma_v) * cos(c) - cos(G) * cos(gamma_v), -1.0, 1.0));
    float upupvp = (gamma_v + G + epsilon - PI) / (F + G - PI / 2.0);
    float s_e = max(sin(epsilon), 1e-10);
    float cos_xy = sqrt(max(1.0 - (sin(G) * sin(c) / s_e) * (sin(G) * sin(c) / s_e), 0.0));
    float xpxpyp = sqrt(max((1.0 - cos(x)) / max(1.0 - cos_xy, 1e-10), 0.0));
    float uprime = aprime * upupvp;
    float xpyp = sqrt(max(uprime * uprime + cprime * cprime - 2.0 * uprime * cprime * cos(Gprime), 0.0));
    float uGp = uprime * sin(Gprime) / max(xpyp, 1e-10);
    float cos_gp = sqrt(max(1.0 - uGp * uGp, 0.0));
    float xprime = xpyp * xpxpyp; float yprime = xpyp - xprime;
    float rprime = sqrt(max(xprime * xprime + cprime * cprime - 2.0 * xprime * cprime * cos_gp, 0.0));
    float alphaprime;
    if (uprime * rprime <= 1e-10) alphaprime = psi2prime;
    else { float ca = (yprime * yprime - uprime * uprime - rprime * rprime) / (-2.0 * uprime * rprime); alphaprime = acos(clamp(ca, -1.0, 1.0)); }
    float thetaprime;
    if (theta <= psi0) thetaprime = alphaprime;
    else if (theta <= psi0 + psi1) thetaprime = PI - psi2prime - alphaprime;
    else thetaprime = PI - psi2prime + alphaprime;
    float sign_lc = (lambda_c - lambda0 >= 0.0) ? 1.0 : -1.0;
    float x_c = sign_lc * rprime * sin(thetaprime);
    float y_c = hprime - rprime * cos(thetaprime);
    float y_h = y_c * sign(phi) - 3.0;
    float zeta = PI / 4.0 + quadrant * PI / 2.0;
    float scale = SQRT3 / (3.0 * SQRT2);
    float x_m = (x_c * cos(zeta) - y_h * sin(zeta) / SQRT3) * scale;
    float y_m = (x_c * sin(zeta) + y_h * cos(zeta) / SQRT3) * scale;
    return clamp(vec2(x_m, y_m) * 0.5 + 0.5, vec2(0.0), vec2(1.0));
}
/* --- end Petroff --- */

void main() {
    int cell = int(v_cell_idx + 0.5);
    vec3 dir = normalize(v_normal);
    vec2 uv = petroff_uv(dir);
    ivec2 local_px = clamp(ivec2(uv * 64.0), ivec2(0), ivec2(63));
    int tile_x = cell % 128; int tile_y = cell / 128;
    ivec2 atlas_px = ivec2(tile_x * 64, tile_y * 64) + local_px;
    uint pixel_idx = uint(atlas_px.y) * 8192u + uint(atlas_px.x);
    uint packed = atlas_pixels[pixel_idx];
    float r = float(packed & 0xFFu) / 255.0;
    float g = float((packed >> 8u) & 0xFFu) / 255.0;
    float b = float((packed >> 16u) & 0xFFu) / 255.0;
    if (r + g + b < 0.01) discard;
    vec3 light_dir = normalize(vec3(0.3, 0.7, 0.5));
    vec3 N = normalize(v_normal);
    float ndotl = abs(dot(N, light_dir));
    float lighting = 0.3 + 0.7 * ndotl;
    frag_color = vec4(vec3(r, g, b) * lighting, 1.0);
}
