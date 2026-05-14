#!/bin/bash
# Assemble signature-collection variant
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-galaxy_sig.ergo}"

cat "$DIR/constants.ergo" \
    "$DIR/fluid_state.ergo" \
    "$DIR/waveguide_state.ergo" \
    "$DIR/fluid_subs.ergo" \
    "$DIR/waveguide_subs.ergo" \
    "$DIR/census.ergo" \
    "$DIR/sig_dump.ergo" \
    "$DIR/main_sig.ergo" \
    > "$OUT"

echo "[sig] Assembled → $OUT ($(wc -l < "$OUT") lines)"
