#!/bin/sh
CH=$1
I=0
for f in runs7/ge_*.log; do
  Q=$((I % 3)); I=$((I+1))
  if [ $Q -ne $CH ]; then continue; fi
  S=$(basename $f .log | sed 's/ge_//')
  TORC_N=48 python3 run_oracle_batch.py $f oracle48_$S.json 24
  echo "oracle48 done $S"
done
