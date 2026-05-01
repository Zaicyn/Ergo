#version 450

/*
 * Grid gaussian vertex shader — O(cells) render from grid moments.
 *
 * Each grid cell (instance) expands to a screen-aligned quad.
 * gl_InstanceIndex = flattened cell index (0..GRID_SIZE^3 - 1).
 * gl_VertexIndex = quad corner (0-5, two triangles).
 *
 * Uses push constants (same layout as particle gauss shader).
 * point_size field repurposed as grid_size.
 */

layout(location = 0) out vec2  v_uv;
layout(location = 1) out float v_value;

/* Grid SSBOs — all float, flattened 3D (GRID_SIZE^3 elements) */
layout(set = 0, binding = 0) readonly buffer BufGradX   { float grad_x[];  };
layout(set = 0, binding = 1) readonly buffer BufGradY   { float grad_y[];  };
layout(set = 0, binding = 2) readonly buffer BufGradZ   { float grad_z[];  };
layout(set = 0, binding = 3) readonly buffer BufMGate   { float met_gate[]; };

layout(push_constant) uniform PC {
    mat4  viewProj;
    float grid_size;   /* repurposed from point_size */
    float val_min;
    float val_max;
    float world_scale;
};

void main() {
    int cell = gl_InstanceIndex;
    int corner = gl_VertexIndex;

    float gate = met_gate[cell];

    /* Skip cells with baseline gate (no particles contributed) */
    if (gate < 0.25) {
        gl_Position = vec4(0.0, 0.0, -2.0, 1.0);
        v_uv = vec2(0.0);
        v_value = 0.0;
        return;
    }

    const vec2 corners[6] = vec2[6](
        vec2(-1.0, -1.0),
        vec2( 1.0, -1.0),
        vec2(-1.0,  1.0),
        vec2(-1.0,  1.0),
        vec2( 1.0, -1.0),
        vec2( 1.0,  1.0)
    );
    vec2 offset = corners[corner];

    /* Decompose flattened index -> (i, j, k) */
    int gs = 32;
    int gs2 = 1024;
    int ck = cell / gs2;
    int rem = cell - ck * gs2;
    int cj = rem / gs;
    int ci = rem - cj * gs;

    /* Cell center in world coords */
    vec3 world_pos = vec3(
        (float(ci) - 16.0 + 0.5) * 75.0,
        (float(cj) - 16.0 + 0.5) * 75.0,
        (float(ck) - 16.0 + 0.5) * 75.0
    ) * world_scale;

    vec4 clip_center = viewProj * vec4(world_pos, 1.0);

    /* Color from metabolic gate */
    float t = clamp((gate - 0.2) / 1.3, 0.0, 1.0);

    /* Splat size — fixed for now */
    float radius = 0.03 * (0.3 + t);

    gl_Position = clip_center;
    gl_Position.xy += offset * radius * clip_center.w;

    v_uv = offset;
    v_value = t;
}
