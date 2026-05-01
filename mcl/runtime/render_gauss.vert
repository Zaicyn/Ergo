#version 450

/*
 * Gaussian splat vertex shader — instanced quad expansion.
 *
 * Each particle (instance) expands to a screen-aligned quad (2 triangles, 6 verts).
 * gl_InstanceIndex = particle index into SoA buffers
 * gl_VertexIndex = quad corner (0-5)
 *
 * Hemisphere culling: when cull_mode > 0, discard particles
 * behind the camera plane.
 */

layout(location = 0) out vec2  v_uv;
layout(location = 1) out float v_value;

layout(set = 0, binding = 0) buffer BufX { float px[]; };
layout(set = 0, binding = 1) buffer BufY { float py[]; };
layout(set = 0, binding = 2) buffer BufZ { float pz[]; };
layout(set = 0, binding = 3) buffer BufC { float cv[]; };

layout(set = 0, binding = 5) uniform RenderParams {
    mat4  viewProj;
    float cam_x;
    float cam_y;
    float cam_z;
    float cull_mode;   // 0 = off, 1 = hemisphere cull
    float val_min;
    float val_max;
    float world_scale;
    float pad;
} pc;

void main() {
    int particle = gl_InstanceIndex;
    int corner   = gl_VertexIndex;

    const vec2 corners[6] = vec2[6](
        vec2(-1.0, -1.0),
        vec2( 1.0, -1.0),
        vec2(-1.0,  1.0),
        vec2(-1.0,  1.0),
        vec2( 1.0, -1.0),
        vec2( 1.0,  1.0)
    );

    vec2 offset = corners[corner];

    vec3 world_pos = vec3(px[particle], py[particle], pz[particle]) * pc.world_scale;

    // Hemisphere cull
    if (pc.cull_mode > 0.5) {
        vec3 cam = vec3(pc.cam_x, pc.cam_y, pc.cam_z);
        vec3 cam_fwd = normalize(-cam);
        float d = dot(world_pos - cam, cam_fwd);
        if (d < 0.0) {
            gl_Position = vec4(0.0, 0.0, -2.0, 1.0);
            v_uv = vec2(0.0);
            v_value = 0.0;
            return;
        }
    }

    vec4 clip_center = pc.viewProj * vec4(world_pos, 1.0);

    float raw_val = cv[particle];
    float t = clamp((raw_val - pc.val_min) / (pc.val_max - pc.val_min + 1e-10), 0.0, 1.0);

    float radius = 0.008 * (0.5 + t);  /* fixed splat size in clip space */

    gl_Position = clip_center;
    gl_Position.xy += offset * radius * clip_center.w;

    v_uv = offset;
    v_value = t;
}
