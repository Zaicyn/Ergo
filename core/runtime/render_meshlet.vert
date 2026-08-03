#version 450

/*
 * Meshlet shell vertex shader — per-cell atlas imposter.
 *
 * Passes world position, surface normal, and cell index
 * for per-cell octahedral atlas tile lookup in fragment shader.
 */

layout(location = 0) out vec3  v_world_pos;
layout(location = 1) out vec3  v_normal;
layout(location = 2) out flat float v_cell_idx;

layout(set = 0, binding = 0) readonly buffer BufPos { vec4 pos[]; };
layout(set = 0, binding = 1) readonly buffer BufNV  { vec4 nv[];  };

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
} pc;

void main() {
    int i = gl_VertexIndex;
    vec4 p = pos[i];
    vec4 nval = nv[i];

    gl_Position = pc.viewProj * p;
    v_world_pos = p.xyz;
    v_normal = nval.xyz;        /* unit sphere normal */
    v_cell_idx = nval.w;        /* cell index for atlas tile */
}
