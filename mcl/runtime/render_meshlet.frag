#version 450

/*
 * Meshlet shell fragment shader — per-cell atlas with equal-area projection.
 * Same equal_area_octa_uv as atlas_gen.comp — Collignon quincuncial.
 */

layout(location = 0) in vec3  v_world_pos;
layout(location = 1) in vec3  v_normal;
layout(location = 2) in flat float v_cell_idx;

layout(location = 0) out vec4 frag_color;

layout(set = 0, binding = 2) readonly buffer AtlasBuf { uint atlas_pixels[]; };

layout(set = 0, binding = 5) uniform RenderParams {
    mat4  viewProj;
    float cam_x, cam_y, cam_z;
    float cull_mode;
    float val_min, val_max;
    float world_scale;
    float pad;
} pc;

#define PI 3.14159265359
#define SQRT2 1.41421356237

/* Must match atlas_gen.comp exactly */
vec2 equal_area_octa_uv(vec3 dir) {
    dir = normalize(dir);

    float phi = asin(clamp(dir.y, -1.0, 1.0));
    float lambda = atan(dir.x, dir.z);

    int q = int(floor(2.0 * lambda / PI));
    if (lambda < 0.0) q -= 1;
    q = clamp(q, -2, 1);

    float lambda_0 = lambda - (PI / 2.0) * float(q) - PI / 4.0;

    float cos_phi = cos(abs(phi) / 2.0 + PI / 4.0);

    float x = -(2.0 * SQRT2 / PI) * lambda_0 * cos_phi;
    float y;
    if (phi < 0.0)
        y = 1.0 - cos_phi / SQRT2;
    else
        y = cos_phi / SQRT2;

    float xt, yt;
    if (q == 0)       { xt = x + y;  yt = x - y; }
    else if (q == 1)  { xt = -x - y; yt = x - y; }
    else if (q == -1) { xt = x + y;  yt = -x + y; }
    else              { xt = -x - y; yt = -x + y; }

    return clamp(vec2(xt, yt) * 0.5 + 0.5, vec2(0.0), vec2(1.0));
}

void main() {
    int cell = int(v_cell_idx + 0.5);

    vec3 dir = normalize(v_normal);
    vec2 uv = equal_area_octa_uv(dir);
    ivec2 local_px = clamp(ivec2(uv * 64.0), ivec2(0), ivec2(63));

    int tile_x = cell % 128;
    int tile_y = cell / 128;
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
