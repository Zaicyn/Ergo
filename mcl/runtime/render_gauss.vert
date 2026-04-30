#version 450

/*
 * Gaussian splat vertex shader — instanced quad expansion.
 *
 * Each particle (instance) expands to a screen-aligned quad.
 * gl_InstanceIndex = particle index, gl_VertexIndex = quad corner (0-5).
 * Render params via UBO (binding 5).
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
    float cull_mode;
    float val_min;
    float val_max;
    float world_scale;
    float pad;
} rp;

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

    vec3 world_pos = vec3(px[particle], py[particle], pz[particle]) * rp.world_scale;

    // Hemisphere cull
    if (rp.cull_mode > 0.5) {
        vec3 cam = vec3(rp.cam_x, rp.cam_y, rp.cam_z);
        vec3 cam_fwd = normalize(-cam);
        float d = dot(world_pos - cam, cam_fwd);
        if (d < 0.0) {
            gl_Position = vec4(0.0, 0.0, -2.0, 1.0);
            v_uv = vec2(0.0);
            v_value = 0.0;
            return;
        }
    }

    vec4 clip_center = rp.viewProj * vec4(world_pos, 1.0);

    float raw_val = cv[particle];
    float t = clamp((raw_val - rp.val_min) / (rp.val_max - rp.val_min + 1e-10), 0.0, 1.0);

    // Splat size: 0.003 base, scaled by energy
    float radius = 0.003 * (0.5 + t);

    gl_Position = clip_center;
    gl_Position.xy += offset * radius * clip_center.w;

    v_uv = offset;
    v_value = t;
}
