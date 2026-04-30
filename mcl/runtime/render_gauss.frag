#version 450

/*
 * Gaussian splat fragment shader — texture LUT falloff.
 *
 * Samples precomputed gaussian falloff from a 2D texture.
 * UV from vertex shader spans [-1, 1] within the splat quad.
 * Texture coordinates mapped to [0, 1] for lookup.
 *
 * Heat palette coloring (same as point renderer).
 * Alpha from gaussian falloff — smooth volumetric appearance.
 */

layout(location = 0) in vec2  v_uv;
layout(location = 1) in float v_value;

layout(location = 0) out vec4 frag_color;

layout(set = 0, binding = 4) uniform sampler2D gaussLUT;

void main() {
    // Map UV from [-1,1] to [0,1] for texture lookup
    vec2 tex_uv = v_uv * 0.5 + 0.5;

    // Gaussian weight from precomputed LUT
    float weight = texture(gaussLUT, tex_uv).r;

    // Discard fully transparent fragments (outside 2-sigma)
    if (weight < 0.01) discard;

    // Heat palette: blue -> cyan -> green -> yellow -> red
    float t = clamp(v_value, 0.0, 1.0);
    float r = clamp(t * 4.0 - 2.0, 0.0, 1.0);
    float g = clamp(1.0 - abs(t * 4.0 - 2.0), 0.0, 1.0) +
              clamp(t * 4.0 - 2.0, 0.0, 1.0) * step(0.5, t);
    float b = clamp(1.0 - t * 4.0, 0.0, 1.0);

    frag_color = vec4(r, clamp(g, 0.0, 1.0), b, weight);
}
