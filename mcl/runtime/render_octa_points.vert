#version 450

/*
 * Octahedral imposter point shader.
 *
 * Renders the point cloud into an octahedral 2D map.
 * Each point's world-space direction is mapped to octahedral UV,
 * depth is preserved for correct occlusion.
 *
 * Reads the same SoA particle buffers as the normal point renderer.
 */

layout(location = 0) out float v_value;

layout(set = 0, binding = 0) buffer BufX { float px[]; };
layout(set = 0, binding = 1) buffer BufY { float py[]; };
layout(set = 0, binding = 2) buffer BufZ { float pz[]; };
layout(set = 0, binding = 3) buffer BufC { float cv[]; };

layout(set = 0, binding = 5) uniform RenderParams {
    mat4  viewProj;    /* unused for octa — we project manually */
    float cam_x;
    float cam_y;
    float cam_z;
    float cull_mode;
    float val_min;
    float val_max;
    float world_scale;
    float pad;
} pc;

/* Direction to octahedral UV in [0,1]² */
vec2 dir_to_octa_uv(vec3 n) {
    /* Project onto octahedron: L1 normalize */
    n /= (abs(n.x) + abs(n.y) + abs(n.z));

    /* Fold lower hemisphere */
    if (n.z < 0.0) {
        vec2 wrapped = (1.0 - abs(n.yx)) * vec2(
            n.x >= 0.0 ? 1.0 : -1.0,
            n.y >= 0.0 ? 1.0 : -1.0
        );
        n.x = wrapped.x;
        n.y = wrapped.y;
    }

    /* Map from [-1,1] to [0,1] */
    return n.xy * 0.5 + 0.5;
}

void main() {
    int i = gl_VertexIndex;

    vec3 world_pos = vec3(px[i], py[i], pz[i]) * pc.world_scale;
    float dist = length(world_pos);

    if (dist < 1e-8) {
        gl_Position = vec4(0.0, 0.0, -2.0, 1.0);
        gl_PointSize = 0.0;
        v_value = 0.0;
        return;
    }

    vec3 dir = world_pos / dist;
    vec2 uv = dir_to_octa_uv(dir);

    /* Map UV [0,1] to clip space [-1,1] */
    gl_Position = vec4(uv * 2.0 - 1.0, dist * 0.01, 1.0);  /* depth from distance */
    gl_PointSize = 1.0;

    v_value = clamp((cv[i] - pc.val_min) / (pc.val_max - pc.val_min + 1e-10),
                    0.0, 1.0);
}
