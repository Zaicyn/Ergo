#!/bin/bash
# Assemble SQ4 retest variants (originals untouched).
#   $1 = "scatter" (default) | "flat" ; $2 = output path
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
VARIANT="${1:-scatter}"

if [ "$VARIANT" = "flat" ]; then
  OUT="${2:-galaxy_sq4flat.ergo}"
  cat "$DIR/constants.ergo" \
      "$DIR/fluid_state.ergo" \
      "$DIR/waveguide_state.ergo" \
      "$DIR/fluid_subs.ergo" \
      "$DIR/waveguide_subs.ergo" \
      "$DIR/census.ergo" \
      "$DIR/main_sq4flat.ergo" \
      > "$OUT"
else
  OUT="${2:-galaxy_structured_sq4.ergo}"
  cat "$DIR/constants.ergo" \
      "$DIR/fluid_state.ergo" \
      "$DIR/waveguide_state.ergo" \
      "$DIR/fluid_subs_sq4.ergo" \
      "$DIR/waveguide_subs.ergo" \
      "$DIR/census_sq4.ergo" \
      "$DIR/main_sq4.ergo" \
      > "$OUT"
fi

echo "[sq4] Assembled $VARIANT → $OUT ($(wc -l < "$OUT") lines)"
