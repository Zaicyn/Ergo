#!/bin/sh
# drive 12 hold-release runs, max 3 concurrent
D=/mnt/agents/output/actin_phasespace/phi4/runs18
rm -f /tmp/r18/status.txt
for F in 0.5 1.0 2.0 3.0 4.0 6.0; do
  for S in 77031 84950; do
    N=rel2_f${F}_s${S}
    sh /tmp/r18/runner3.sh $D/$N.ergo $N &
    while [ "$(jobs -p | wc -l)" -ge 3 ]; do sleep 10; done
  done
done
wait
echo "ALL_DONE" >> /tmp/r18/status.txt
