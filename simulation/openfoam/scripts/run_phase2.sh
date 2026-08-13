#!/usr/bin/env bash
# Phase 2: the 3D contact-angle spot-check, then study C.
#
# Waits for the 2D studies (B, A2) to drain before starting. That wait is the
# whole point: interFoam under MPI synchronises every timestep, so on an
# oversubscribed box one descheduled rank stalls all of them at the barrier.
# The 3D case measured ~24 h/case sharing 10 cores with nine serial solvers,
# against ~1.85 h uncontended -- a 12x penalty that serial jobs simply do not
# suffer. Sequencing beats sharing here.
#
# 6 ranks, not 8: 44,000 cells over 8 ranks is 5,500 cells/rank, below where
# OpenFOAM scales well, and 6 is what results/mill3d800_2026-08 used -- so
# this run stays directly comparable to that reference rather than differing
# in decomposition as well as in theta.
set -u -o pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
PY="$HOME/sweeps/venv/bin/python3"
ROOT="$HOME/sweeps/wetting"
P_CONT=980
P_DISP=490

echo "=== phase 2 armed at $(date '+%H:%M') -- waiting for 2D studies to drain ==="
while [ "$(docker ps --format '{{.Names}}' 2>/dev/null | grep -c '^fluidsweep-')" -gt 0 ]; do
    sleep 60
done
echo "=== 2D studies drained at $(date '+%H:%M') ==="

echo; echo "--- 3D contact-angle spot-check: theta 120 vs 160, 6-way MPI ---"
$PY "$HERE/sweep_fluid_props.py" --base-case "$HERE/../tjunction_3d_mill" --w-main 800 \
    --output-dir "$ROOT/D_3d_theta" \
    --sigma 0.03 --theta 120 160 \
    --u-oil 0.019834 --u-water 0.005791 \
    --end-time 0.6 --write-interval 0.005 \
    --mpi-ranks 6 --concurrency 1
echo "3D exit=$?  at $(date '+%H:%M')"

echo; echo "--- STUDY C: sigma with drive retuned P ~ sigma (6 cases) ---"
$PY "$HERE/sweep_fluid_props.py" --base-case "$HERE/../tjunction_2d_mill" --w-main 800 \
    --output-dir "$ROOT/C_sigma_scaledP" \
    --sigma 0.005 0.008 0.012 0.02 0.03 0.04 --theta 160 \
    --p-cont $P_CONT --p-disp $P_DISP --pressure-mode scale-with-sigma \
    --sigma-ref 0.03 \
    --end-time 0.6 --write-interval 0.005 --concurrency 6
echo "STUDY C exit=$?  at $(date '+%H:%M')"

echo; echo "=== PHASE 2 FINISHED $(date '+%H:%M') ==="
du -sh "$ROOT"
