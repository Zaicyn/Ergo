#version 450

/*
 * Point cloud vertex shader — direct SoA read.
 *
 * 4 storage buffers read with coalesced access per warp.
 * Render params via UBO (binding 5) — no push constants.
 * Hemisphere culling: when cull_mode > 0, discard particles
 * behind the camera plane.
 */

layout(location = 0) out float v_value;

layout(set = 0, binding = 0) buffer BufX { float px[]; };
layout(set = 0, binding = 1) buffer BufY { float py[]; };
layout(set = 0, binding = 2) buffer BufZ { float pz[]; };
layout(set = 0, binding = 3) buffer BufC { float cv[]; };

layout(set = 0, binding = 5) uniform RenderParams {
    mat4  viewProj;
    float cam_x;
    float cam_y;
    float cam_z;
    float cull_mode;
    float val_min;
    float val_max;
    float world_scale;
    float pad;
} rp;

void main() {
    int i = gl_VertexIndex;

    vec3 world_pos = vec3(px[i], py[i], pz[i]) * rp.world_scale;

    // Hemisphere cull: discard particles behind camera plane
    if (rp.cull_mode > 0.5) {
        vec3 cam = vec3(rp.cam_x, rp.cam_y, rp.cam_z);
        vec3 cam_fwd = normalize(-cam);
        float d = dot(world_pos - cam, cam_fwd);
        if (d < 0.0) {
            gl_Position = vec4(0.0, 0.0, -2.0, 1.0);
            gl_PointSize = 0.0;
            v_value = 0.0;
            return;
        }
    }

    gl_Position = rp.viewProj * vec4(world_pos, 1.0);
    gl_PointSize = 1.0;

    v_value = clamp((cv[i] - rp.val_min) / (rp.val_max - rp.val_min + 1e-10),
                    0.0, 1.0);
}
