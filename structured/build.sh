#!/bin/bash
# Assemble structured Ergo modules into a single compilable file.
# Order: constants → fluid_state → waveguide_state → fluid_subs → waveguide_subs → census → main

DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-galaxy_structured.ergo}"

cat "$DIR/constants.ergo" \
    "$DIR/fluid_state.ergo" \
    "$DIR/waveguide_state.ergo" \
    "$DIR/fluid_subs.ergo" \
    "$DIR/waveguide_subs.ergo" \
    "$DIR/census.ergo" \
    "$DIR/main.ergo" \
    > "$OUT"

echo "[structured] Assembled → $OUT ($(wc -l < "$OUT") lines)"
