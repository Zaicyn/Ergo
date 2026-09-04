#version 450

/*
 * Point cloud vertex shader — direct SoA read.
 *
 * 4 storage buffers read with coalesced access per warp.
 * Hemisphere culling: when cull_mode > 0, discard particles
 * behind the camera plane (dot(pos - cam, cam_forward) < 0).
 */

layout(location = 0) out float v_value;

layout(set = 0, binding = 0) buffer BufX { float px[]; };
layout(set = 0, binding = 1) buffer BufY { float py[]; };
layout(set = 0, binding = 2) buffer BufZ { float pz[]; };
layout(set = 0, binding = 3) buffer BufC { float cv[]; };

layout(push_constant) uniform PC {
    mat4  viewProj;
    float point_size;
    float val_min;
    float val_max;
    float world_scale;
    float cam_x;
    float cam_y;
    float cam_z;
    float cull_mode;   // 0 = off, 1 = hemisphere cull
} pc;

void main() {
    int i = gl_VertexIndex;

    vec3 world_pos = vec3(px[i], py[i], pz[i]) * pc.world_scale;

    // Hemisphere cull: discard particles behind camera plane
    if (pc.cull_mode > 0.5) {
        vec3 cam = vec3(pc.cam_x, pc.cam_y, pc.cam_z);
        vec3 cam_fwd = normalize(-cam); // camera looks at origin
        float d = dot(world_pos - cam, cam_fwd);
        if (d < 0.0) {
            gl_Position = vec4(0.0, 0.0, -2.0, 1.0); // behind clip plane
            gl_PointSize = 0.0;
            v_value = 0.0;
            return;
        }
    }

    gl_Position = pc.viewProj * vec4(world_pos, 1.0);

    /* Depth-attenuated point size (2026-09-04): near points render
       bigger — the strongest monocular depth cue for point tracers.
       pc.point_size is the host's base size (previously ignored). */
    float depth = length(world_pos - vec3(pc.cam_x, pc.cam_y, pc.cam_z));
    gl_PointSize = clamp(pc.point_size * 1.2 / max(depth, 0.05), 1.0, 12.0);

    v_value = clamp((cv[i] - pc.val_min) / (pc.val_max - pc.val_min + 1e-10),
                    0.0, 1.0);
}
