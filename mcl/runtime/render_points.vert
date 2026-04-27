#version 450
#extension GL_EXT_shader_explicit_arithmetic_types_float64 : enable

/*
 * Point cloud vertex shader for particle simulations.
 *
 * Each invocation = one particle. gl_VertexIndex = particle index.
 * Reads position from 3 separate f64 storage buffers (SoA layout).
 * Reads color value from a 4th f64 buffer.
 */

layout(location = 0) out float v_value; /* normalized color value */

layout(set = 0, binding = 0) buffer BufX { float64_t px[]; };
layout(set = 0, binding = 1) buffer BufY { float64_t py[]; };
layout(set = 0, binding = 2) buffer BufZ { float64_t pz[]; };
layout(set = 0, binding = 3) buffer BufC { float64_t cv[]; };

layout(push_constant) uniform PC {
    mat4  viewProj;
    float point_size;
    float val_min;
    float val_max;
    float world_scale; /* 1/world_radius: maps world coords to ~[-1,1] */
} pc;

void main() {
    int i = gl_VertexIndex;

    float x = float(px[i]) * pc.world_scale;
    float y = float(py[i]) * pc.world_scale;
    float z = float(pz[i]) * pc.world_scale;

    gl_Position = pc.viewProj * vec4(x, y, z, 1.0);
    gl_PointSize = pc.point_size;

    float val = float(cv[i]);
    v_value = clamp((val - pc.val_min) / (pc.val_max - pc.val_min + 1e-10),
                    0.0, 1.0);
}
