#!/bin/sh
# verify-before-delete ensemble runner (runs18 hold-release grid)
# usage: runner3.sh <ergo_file> <name>
ERGO=$1
NAME=$2
TC=/mnt/agents/output/actin_swarm/toolchain/ergo_mcl
OUT=/mnt/agents/output/actin_phasespace/phi4/runs18
RAW=/tmp/r18/raw
BIN=/tmp/r18/bin
mkdir -p $RAW $OUT $BIN

cd $TC && python3 -m core $ERGO -o $BIN/$NAME || { echo "$NAME BUILD_FAIL" >> /tmp/r18/status.txt; exit 1; }

$BIN/$NAME > $RAW/$NAME.log 2>&1
rc=$?
nul=$(LC_ALL=C tr -cd '\000' < $RAW/$NAME.log | wc -c)
if [ $rc -ne 0 ] || [ "$nul" != "0" ]; then
  echo "$NAME RUN_FAIL rc=$rc nul=$nul" >> /tmp/r18/status.txt
  exit 1
fi
cp $RAW/$NAME.log $OUT/$NAME.log
nul2=$(LC_ALL=C tr -cd '\000' < $OUT/$NAME.log | wc -c)
if [ "$nul2" != "0" ]; then
  echo "$NAME COPY_FAIL nul2=$nul2 (raw kept)" >> /tmp/r18/status.txt
  exit 1
fi
rm -f $RAW/$NAME.log
echo "$NAME OK steps=$(grep -ac '^xpt' $OUT/$NAME.log)" >> /tmp/r18/status.txt
exit 0
