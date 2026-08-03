#version 450

/*
 * 3D surface fragment shader.
 *
 * Receives interpolated value and normal from vertex shader.
 * Applies heat palette coloring + simple directional diffuse lighting.
 */

layout(location = 0) in float v_value;
layout(location = 1) in vec3  v_normal;

layout(location = 0) out vec4 frag_color;

layout(push_constant) uniform PC {
    mat4  viewProj;
    int   grid_w;
    int   grid_h;
    float val_min;
    float val_max;
    float height_scale;
} pc;

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
    vec3 base_color = heat(v_value);

    /* Directional light from upper-right-front */
    vec3 light_dir = normalize(vec3(0.4, 0.8, 0.3));
    vec3 N = normalize(v_normal);

    /* Two-sided lighting: abs(dot) so backfaces aren't black */
    float diffuse = abs(dot(N, light_dir));

    /* Ambient + diffuse */
    float ambient = 0.25;
    float lit = ambient + (1.0 - ambient) * diffuse;

    frag_color = vec4(base_color * lit, 1.0);
}
