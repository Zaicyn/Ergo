#version 450

/*
 * Meshlet shell fragment shader — per-cell atlas imposter.
 *
 * v_normal = icosphere template position = direction from cell center.
 * Use it directly as the octa lookup direction — no need to reconstruct
 * from world position.
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

vec2 dir_to_octa_uv(vec3 n) {
    n /= (abs(n.x) + abs(n.y) + abs(n.z));
    if (n.z < 0.0) {
        vec2 wrapped = (1.0 - abs(n.yx)) * vec2(
            n.x >= 0.0 ? 1.0 : -1.0,
            n.y >= 0.0 ? 1.0 : -1.0
        );
        n.x = wrapped.x;
        n.y = wrapped.y;
    }
    return n.xy * 0.5 + 0.5;
}

void main() {
    int cell = int(v_cell_idx + 0.5);

    /* Use normal directly as direction — it IS the icosphere template dir */
    vec3 dir = normalize(v_normal);
    vec2 uv = dir_to_octa_uv(dir);
    ivec2 local_px = clamp(ivec2(uv * 16.0), ivec2(0), ivec2(15));

    /* Atlas tile for this cell */
    int tile_x = cell % 128;
    int tile_y = cell / 128;
    ivec2 atlas_px = ivec2(tile_x * 16, tile_y * 16) + local_px;
    uint pixel_idx = uint(atlas_px.y) * 2048u + uint(atlas_px.x);

    uint packed = atlas_pixels[pixel_idx];

    /* Unpack RGBA8 */
    float r = float(packed & 0xFFu) / 255.0;
    float g = float((packed >> 8u) & 0xFFu) / 255.0;
    float b = float((packed >> 16u) & 0xFFu) / 255.0;

    /* Discard empty pixels */
    if (r + g + b < 0.01) discard;

    /* Lighting */
    vec3 light_dir = normalize(vec3(0.3, 0.7, 0.5));
    vec3 N = normalize(v_normal);
    float ndotl = abs(dot(N, light_dir));
    float lighting = 0.3 + 0.7 * ndotl;

    frag_color = vec4(vec3(r, g, b) * lighting, 1.0);
}
