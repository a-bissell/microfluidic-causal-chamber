#!/bin/bash
# Stop the run cleanly, leaving a complete checkpoint to resume from.
#
# Preferred path: set `stopAt writeNow` in controlDict. Because runTimeModifiable
# is on and the case is bind-mounted, the running solver reads the edit at its
# next timestep, writes a final checkpoint, and exits on its own — no lost data.
# If it hasn't stopped within the grace window (a single 3D timestep can be slow),
# fall back to `docker stop`, which at worst discards the in-progress step; the
# last written checkpoint is always intact.

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"

if ! is_running; then
  echo "[stop] '$CONTAINER' is not running. Latest checkpoint: t=$(latest_time || echo none)"
  exit 0
fi

echo "[stop] requesting clean stop at next write (t=$(latest_time))..."
sed -i.bak 's/^stopAt .*/stopAt          writeNow;/' "$CASE_DIR/system/controlDict"
rm -f "$CASE_DIR/system/controlDict.bak"

# Wait up to ~5 min for the solver to write and exit on its own.
for i in $(seq 1 60); do
  is_running || { echo "[stop] clean stop confirmed at t=$(latest_time)."; exit 0; }
  sleep 5
done

echo "[stop] grace window elapsed; forcing docker stop (last checkpoint stays intact)."
docker stop "$CONTAINER" >/dev/null 2>&1 || true
sleep 2
echo "[stop] stopped at t=$(latest_time)."
