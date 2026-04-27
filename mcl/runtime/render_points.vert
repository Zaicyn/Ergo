#version 450

/*
 * Point cloud vertex shader for particle simulations.
 *
 * Each invocation = one particle. gl_VertexIndex = particle index.
 * Reads position from 3 separate storage buffers (SoA layout).
 * Reads color value from a 4th buffer.
 * Supports f32 (--precision f32) via float buffers.
 */

layout(location = 0) out float v_value; /* normalized color value */

layout(set = 0, binding = 0) buffer BufX { float px[]; };
layout(set = 0, binding = 1) buffer BufY { float py[]; };
layout(set = 0, binding = 2) buffer BufZ { float pz[]; };
layout(set = 0, binding = 3) buffer BufC { float cv[]; };

layout(push_constant) uniform PC {
    mat4  viewProj;
    float point_size;
    float val_min;
    float val_max;
    float world_scale; /* 1/world_radius: maps world coords to ~[-1,1] */
} pc;

void main() {
    int i = gl_VertexIndex;

    float x = px[i] * pc.world_scale;
    float y = py[i] * pc.world_scale;
    float z = pz[i] * pc.world_scale;

    gl_Position = pc.viewProj * vec4(x, y, z, 1.0);
    gl_PointSize = pc.point_size;

    float val = cv[i];
    v_value = clamp((val - pc.val_min) / (pc.val_max - pc.val_min + 1e-10),
                    0.0, 1.0);
}
