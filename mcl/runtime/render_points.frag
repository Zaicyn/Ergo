#version 450

/*
 * Point cloud fragment shader.
 *
 * Receives interpolated value, applies heat palette.
 * Discards fragments outside a circular point (smooth dots).
 */

layout(location = 0) in float v_value;
layout(location = 0) out vec4 frag_color;

/* Heat palette: blue -> cyan -> green -> yellow -> red */
vec3 heat(float t) {
    t = clamp(t, 0.0, 1.0);
    vec3 c;
    if (t < 0.25) {
        c = mix(vec3(0.0, 0.0, 0.5), vec3(0.0, 0.5, 1.0), t * 4.0);
    } else if (t < 0.5) {
        c = mix(vec3(0.0, 0.5, 1.0), vec3(0.0, 1.0, 0.0), (t - 0.25) * 4.0);
    } else if (t < 0.75) {
        c = mix(vec3(0.0, 1.0, 0.0), vec3(1.0, 1.0, 0.0), (t - 0.5) * 4.0);
    } else {
        c = mix(vec3(1.0, 1.0, 0.0), vec3(1.0, 0.0, 0.0), (t - 0.75) * 4.0);
    }
    return c;
}

void main() {
    /* Circular point: discard outside radius 0.5 from center */
    vec2 pc = gl_PointCoord - vec2(0.5);
    float r2 = dot(pc, pc);
    if (r2 > 0.25) discard;

    /* Soft edge falloff */
    float alpha = 1.0 - smoothstep(0.15, 0.25, r2);

    vec3 color = heat(v_value);
    frag_color = vec4(color, alpha);
}
