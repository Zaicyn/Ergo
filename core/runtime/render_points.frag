#version 450

/*
 * Point cloud fragment shader.
 *
 * Receives interpolated value, applies heat palette.
 * Discards fragments outside a circular point (smooth dots).
 */

layout(location = 0) in float v_value;
layout(location = 0) out vec4 frag_color;

void main() {
    float t = clamp(v_value, 0.0, 1.0);
    /* Branchless heat: blue → cyan → green → yellow → red */
    float r = clamp(t * 4.0 - 2.0, 0.0, 1.0);
    float g = clamp(1.0 - abs(t * 4.0 - 2.0), 0.0, 1.0) +
              clamp(t * 4.0 - 2.0, 0.0, 1.0) * step(0.5, t);
    float b = clamp(1.0 - t * 4.0, 0.0, 1.0);
    frag_color = vec4(r, clamp(g, 0.0, 1.0), b, 1.0);
}
