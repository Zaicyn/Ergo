#!/bin/bash
# Assemble structured MCL modules into a single compilable file.
# Order: constants → fluid_state → waveguide_state → fluid_subs → waveguide_subs → census → main

DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-galaxy_structured.mcl}"

cat "$DIR/constants.mcl" \
    "$DIR/fluid_state.mcl" \
    "$DIR/waveguide_state.mcl" \
    "$DIR/fluid_subs.mcl" \
    "$DIR/waveguide_subs.mcl" \
    "$DIR/census.mcl" \
    "$DIR/main.mcl" \
    > "$OUT"

echo "[structured] Assembled → $OUT ($(wc -l < "$OUT") lines)"
