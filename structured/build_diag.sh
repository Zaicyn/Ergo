#!/bin/bash
# Assemble diagnostic variant: same module order as build.sh, plus diag,
# and main_diag instead of main.
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-galaxy_diag.ergo}"

cat "$DIR/constants.ergo" \
    "$DIR/fluid_state.ergo" \
    "$DIR/waveguide_state.ergo" \
    "$DIR/fluid_subs.ergo" \
    "$DIR/waveguide_subs.ergo" \
    "$DIR/census.ergo" \
    "$DIR/diag.ergo" \
    "$DIR/main_diag.ergo" \
    > "$OUT"

echo "[diag] Assembled → $OUT ($(wc -l < "$OUT") lines)"
