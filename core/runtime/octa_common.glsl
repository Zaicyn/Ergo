/*
 * Shared octahedral mapping with gnomonic correction.
 *
 * Standard octa mapping = equidistant (fisheye): r = f * θ
 * Gnomonic (rectilinear): r = f * tan(θ)
 *
 * The correction remaps the UV radial distance from center
 * using tan(θ)/θ to undo the fisheye compression at the edges.
 * This makes a flat grid projected onto a sphere appear flat.
 */

vec2 dir_to_octa_uv(vec3 n) {
    n = normalize(n);

    /* Standard octahedral projection */
    float l1 = abs(n.x) + abs(n.y) + abs(n.z);
    vec3 o = n / l1;

    if (o.z < 0.0) {
        vec2 wrapped = (1.0 - abs(o.yx)) * vec2(
            o.x >= 0.0 ? 1.0 : -1.0,
            o.y >= 0.0 ? 1.0 : -1.0
        );
        o.x = wrapped.x;
        o.y = wrapped.y;
    }

    vec2 uv = o.xy * 0.5 + 0.5;

    /* Gnomonic correction: remap radial distance from center.
     * θ = angle from nearest axis = acos(max component of |n|)
     * equidistant: r_eq = θ / (π/2) (normalized to [0,1])
     * gnomonic:    r_gn = tan(θ) / tan(π/2) ... but tan(π/2) = inf
     *
     * Simpler approach: the UV offset from (0.5, 0.5) represents
     * the octa-projected position. Scale it by tan(θ)/θ where
     * θ = angle from the z-axis of the dominant octahedron face. */
    vec2 offset = uv - 0.5;
    float r = length(offset);
    if (r > 0.001) {
        /* θ from the angle the direction makes with its dominant axis */
        float max_comp = max(abs(n.x), max(abs(n.y), abs(n.z)));
        float theta = acos(clamp(max_comp, 0.0, 1.0));

        /* Gnomonic: tan(θ), but scale relative to equidistant θ */
        float correction = 1.0;
        if (theta > 0.001) {
            correction = tan(theta) / theta;
        }

        /* Apply correction — expand edges, keep center */
        offset *= correction;
        uv = 0.5 + offset;
    }

    return clamp(uv, vec2(0.0), vec2(1.0));
}
