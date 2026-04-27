#version 450
#extension GL_EXT_shader_explicit_arithmetic_types_float64 : enable

/*
 * 3D grid-mesh vertex shader.
 *
 * No vertex buffer. gl_VertexIndex encodes grid cell + triangle vertex.
 * Each grid cell (i, j) emits 6 vertices (2 triangles):
 *
 *   (i,j)-----(i+1,j)
 *     |  \  1  |
 *     | 0  \   |
 *   (i,j+1)--(i+1,j+1)
 *
 * Triangle 0: (i,j), (i,j+1), (i+1,j+1)
 * Triangle 1: (i,j), (i+1,j+1), (i+1,j)
 *
 * Y coordinate = simulation value (heightfield).
 * Reads from storage buffer of f64 values.
 */

layout(location = 0) out float v_value;  /* normalized value for coloring */
layout(location = 1) out vec3  v_normal; /* surface normal for lighting  */

layout(set = 0, binding = 0) buffer SimData {
    float64_t data[];
} sim;

layout(push_constant) uniform PC {
    mat4  viewProj;
    int   grid_w;
    int   grid_h;
    float val_min;
    float val_max;
    float height_scale;
} pc;

/* Read simulation value at grid (ix, iy), clamped */
float read_val(int ix, int iy) {
    ix = clamp(ix, 0, pc.grid_w - 1);
    iy = clamp(iy, 0, pc.grid_h - 1);
    return float(sim.data[iy * pc.grid_w + ix]);
}

/* Normalize value to [0,1] for coloring */
float norm_val(float v) {
    return clamp((v - pc.val_min) / (pc.val_max - pc.val_min + 1e-10), 0.0, 1.0);
}

void main() {
    /* Decode gl_VertexIndex:
       cell = gl_VertexIndex / 6
       tri  = (gl_VertexIndex % 6)
       Grid has (grid_w - 1) * (grid_h - 1) cells. */
    int cell = gl_VertexIndex / 6;
    int vert = gl_VertexIndex % 6;

    int cells_x = pc.grid_w - 1;
    int ci = cell % cells_x;    /* cell column */
    int cj = cell / cells_x;    /* cell row    */

    /* Triangle vertex offsets within the cell */
    int di, dj;
    switch (vert) {
        case 0: di = 0; dj = 0; break;  /* tri 0, v0 */
        case 1: di = 0; dj = 1; break;  /* tri 0, v1 */
        case 2: di = 1; dj = 1; break;  /* tri 0, v2 */
        case 3: di = 0; dj = 0; break;  /* tri 1, v0 */
        case 4: di = 1; dj = 1; break;  /* tri 1, v1 */
        default: di = 1; dj = 0; break; /* tri 1, v2 */
    }

    int ix = ci + di;
    int iy = cj + dj;

    /* Read height from simulation buffer */
    float val = read_val(ix, iy);

    /* 3D position: X and Z from grid, Y from simulation value.
       Center the grid at origin. */
    float fx = float(ix) / float(pc.grid_w - 1) - 0.5;  /* [-0.5, 0.5] */
    float fz = float(iy) / float(pc.grid_h - 1) - 0.5;  /* [-0.5, 0.5] */
    float fy = norm_val(val) * pc.height_scale;

    gl_Position = pc.viewProj * vec4(fx, fy, fz, 1.0);

    /* Pass normalized value to fragment shader for coloring */
    v_value = norm_val(val);

    /* Compute surface normal via central differences */
    float hL = read_val(ix - 1, iy) * pc.height_scale;
    float hR = read_val(ix + 1, iy) * pc.height_scale;
    float hD = read_val(ix, iy - 1) * pc.height_scale;
    float hU = read_val(ix, iy + 1) * pc.height_scale;

    /* Grid spacing in world coords */
    float sx = 1.0 / float(pc.grid_w - 1);
    float sz = 1.0 / float(pc.grid_h - 1);

    /* Normal from height gradient (unnormalized) */
    float range = pc.val_max - pc.val_min + 1e-10;
    float nL = (read_val(ix - 1, iy) - pc.val_min) / range * pc.height_scale;
    float nR = (read_val(ix + 1, iy) - pc.val_min) / range * pc.height_scale;
    float nD = (read_val(ix, iy - 1) - pc.val_min) / range * pc.height_scale;
    float nU = (read_val(ix, iy + 1) - pc.val_min) / range * pc.height_scale;

    vec3 normal = normalize(vec3(
        (nL - nR) / (2.0 * sx),
        1.0,
        (nD - nU) / (2.0 * sz)
    ));
    v_normal = normal;
}
