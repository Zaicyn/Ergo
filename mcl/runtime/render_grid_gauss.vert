#version 450

/*
 * Grid point vertex shader — one point per cell, direct projection.
 */

layout(location = 0) out float v_value;

layout(set = 0, binding = 0) readonly buffer BufGradX   { float grad_x[];  };
layout(set = 0, binding = 1) readonly buffer BufGradY   { float grad_y[];  };
layout(set = 0, binding = 2) readonly buffer BufGradZ   { float grad_z[];  };
layout(set = 0, binding = 3) readonly buffer BufMGate   { float met_gate[]; };

layout(push_constant) uniform PC {
    mat4  viewProj;
    float grid_size;
    float val_min;
    float val_max;
    float world_scale;
};

void main() {
    int cell = gl_VertexIndex;

    float gate = met_gate[cell];

    int gs = 32;
    int gs2 = 1024;
    int ck = cell / gs2;
    int rem = cell - ck * gs2;
    int cj = rem / gs;
    int ci = rem - cj * gs;

    vec3 world_pos = vec3(
        (float(ci) - 16.0 + 0.5) * 75.0,
        (float(cj) - 16.0 + 0.5) * 75.0,
        (float(ck) - 16.0 + 0.5) * 75.0
    ) * world_scale;

    gl_Position = viewProj * vec4(world_pos, 1.0);
    gl_PointSize = 20.0;

    /* DEBUG: force bright red */
    v_value = 1.0;
}
