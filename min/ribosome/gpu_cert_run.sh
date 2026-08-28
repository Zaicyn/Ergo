#!/bin/sh
# gpu_cert_run.sh — tRNA 76-bead GPU-vs-CPU certification cross-check.
# Run from the mcl repo root (where `python -m core` works).
# Variants: trna_gpu_<s>.ergo = certified rung-2 recipe in the new
# unified slot form (data blocks diff-identical to the certified old
# build; only the pair-force loop structure changed).
#
# 6 builds, 6 runs:
#   CPU: default C target, f64 — tests the slot-form restructure itself
#        against the old-form certified results (4.45/4.87/6.24).
#   GPU: --target spirv --precision f32 — the full GPU path.
#
# Usage: sh gpu_cert_run.sh <outdir>
set -e
OUT=${1:-/tmp/gpucert}
mkdir -p "$OUT"
DIR=$(dirname "$0")

for S in 0 1 2; do
  V="$DIR/trna_gpu_$S.ergo"

  # CPU f64
  if [ ! -s "$OUT/trna_cpu_$S.csv" ]; then
    python -m core "$V" -o "/tmp/trna_cpu_$S"
    "/tmp/trna_cpu_$S" > "$OUT/trna_cpu_$S.csv"
    echo "cpu $S done"
  fi

  # GPU f32 spirv
  if [ ! -s "$OUT/trna_gpu_$S.csv" ]; then
    python -m core "$V" --target spirv --precision f32 -o "/tmp/trna_gpu_$S"
    "/tmp/trna_gpu_$S" > "$OUT/trna_gpu_$S.csv"
    echo "gpu $S done"
  fi
done

python3 "$DIR/gpu_cert_analysis.py" "$OUT"
