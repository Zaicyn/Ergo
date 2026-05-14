#!/bin/bash
# Assemble probe variant: same module order as build.sh, plus probe,
# and main_probe instead of main.
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-galaxy_probe.ergo}"

cat "$DIR/constants.ergo" \
    "$DIR/fluid_state.ergo" \
    "$DIR/waveguide_state.ergo" \
    "$DIR/fluid_subs.ergo" \
    "$DIR/waveguide_subs.ergo" \
    "$DIR/census.ergo" \
    "$DIR/probe.ergo" \
    "$DIR/main_probe.ergo" \
    > "$OUT"

echo "[probe] Assembled → $OUT ($(wc -l < "$OUT") lines)"
