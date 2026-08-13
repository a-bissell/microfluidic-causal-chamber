#!/usr/bin/env bash
# Drive the three (sigma, theta) studies for results/wetting_2026-08.
#
# Runs them SEQUENTIALLY: each study saturates --concurrency on its own, and
# overlapping them would just add contention without finishing anything sooner.
# Ordered cheapest-and-most-informative first, so partial results are useful
# if the run is interrupted.
#
# Usage: bash run_wetting_studies.sh [output_root] [concurrency]
set -u -o pipefail

ROOT="${1:-$HOME/sweeps/wetting}"
CONC="${2:-8}"
PY="$HOME/sweeps/venv/bin/python3"
HERE="$(cd "$(dirname "$0")" && pwd)"
BASE="$HERE/../tjunction_2d_mill"

# The 800 um design point, measured in results/scaleup_2026-07.
P_CONT=980
P_DISP=490
SIGMAS="0.005 0.008 0.012 0.02 0.03 0.04"
THETAS="120 130 140 150 160 170"

echo "=== wetting studies: root=$ROOT concurrency=$CONC ==="
date

# ---------------------------------------------------------------------------
# A. theta boundary at the nominal sigma and the designed drive.
#    Where does dripping actually stop? Docs assert 120 fails / 160 works and
#    nothing between has been run.
# ---------------------------------------------------------------------------
echo; echo "--- STUDY A: theta boundary (6 cases) ---"
$PY "$HERE/sweep_fluid_props.py" --base-case "$BASE" --w-main 800 \
    --output-dir "$ROOT/A_theta" \
    --sigma 0.03 --theta $THETAS \
    --p-cont $P_CONT --p-disp $P_DISP --pressure-mode fixed \
    --end-time 0.6 --write-interval 0.005 --concurrency "$CONC"
echo "STUDY A exit=$?"

# ---------------------------------------------------------------------------
# B. sigma with the drive left at the designed 980/490 Pa -- what a builder
#    who trusted the docs actually sees. This is the calibration curve:
#    observed droplet rate -> inferred sigma.
# ---------------------------------------------------------------------------
echo; echo "--- STUDY B: sigma at fixed drive (6 cases) ---"
$PY "$HERE/sweep_fluid_props.py" --base-case "$BASE" --w-main 800 \
    --output-dir "$ROOT/B_sigma_fixedP" \
    --sigma $SIGMAS --theta 160 \
    --p-cont $P_CONT --p-disp $P_DISP --pressure-mode fixed \
    --end-time 0.6 --write-interval 0.005 --concurrency "$CONC"
echo "STUDY B exit=$?"

# ---------------------------------------------------------------------------
# C. sigma with the drive retuned as P ~ sigma. If the observables collapse,
#    the chamber is sigma-robust with a one-line correction to column height.
#    Longest study: endTime scales as 1/sigma, so the 5 mN/m case is 3.6 s.
# ---------------------------------------------------------------------------
echo; echo "--- STUDY C: sigma with drive retuned P ~ sigma (6 cases) ---"
$PY "$HERE/sweep_fluid_props.py" --base-case "$BASE" --w-main 800 \
    --output-dir "$ROOT/C_sigma_scaledP" \
    --sigma $SIGMAS --theta 160 \
    --p-cont $P_CONT --p-disp $P_DISP --pressure-mode scale-with-sigma \
    --sigma-ref 0.03 \
    --end-time 0.6 --write-interval 0.005 --concurrency "$CONC"
echo "STUDY C exit=$?"

echo; echo "=== ALL STUDIES FINISHED ==="
date
du -sh "$ROOT"
