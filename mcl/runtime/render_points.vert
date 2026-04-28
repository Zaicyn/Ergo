#version 450

/*
 * Point cloud vertex shader — direct SoA read.
 *
 * 4 storage buffers read with coalesced access per warp.
 * No pack/transpose — BLAS trick: same data, different indexing.
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
} pc;

void main() {
    int i = gl_VertexIndex;

    vec4 pos = vec4(px[i] * pc.world_scale,
                    py[i] * pc.world_scale,
                    pz[i] * pc.world_scale,
                    1.0);

    gl_Position = pc.viewProj * pos;
    gl_PointSize = 1.0;

    v_value = clamp((cv[i] - pc.val_min) / (pc.val_max - pc.val_min + 1e-10),
                    0.0, 1.0);
}
