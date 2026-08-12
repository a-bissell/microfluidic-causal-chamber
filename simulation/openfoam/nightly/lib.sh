#!/bin/bash
# Shared config for the nightly 3D encoder run. Sourced by the other scripts.
#
# The run is chunked: start it at night, stop it cleanly in the morning, repeat.
# OpenFOAM checkpoints natively (writes complete time directories); restart with
# `startFrom latestTime` resumes exactly where it left off. Nothing here is
# interactive, so it is safe to drive from cron / Claude schedule / cowork.

set -euo pipefail

# Resolve paths relative to this file, so the scripts work from anywhere.
NIGHTLY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OF_DIR="$(dirname "$NIGHTLY_DIR")"                       # simulation/openfoam
RUNROOT="$OF_DIR/runs"                                   # bind-mounted into Docker
CASE="encoder_3d_mp"
CASE_DIR="$RUNROOT/$CASE"
SCRIPTS_DIR="$OF_DIR/scripts"                            # extract/analyze live here

CONTAINER="encoder3d"                                    # fixed name → one run at a time
IMAGE="opencfd/openfoam-default:2306"
NP=4                                                     # 4 P-cores; see README on why not 10
VENV_PY="$HOME/sweeps/venv/bin/python3"                  # has vtk/pandas/scipy

# Run a command inside the OpenFOAM image with the runs tree mounted and the
# environment sourced. $1 = the shell body to run in the case dir.
of_exec() {
  local body="$1"; shift
  docker run --rm "$@" --entrypoint bash \
    -e OMPI_ALLOW_RUN_AS_ROOT=1 -e OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1 \
    -v "$RUNROOT:/w" -w "/w/$CASE" "$IMAGE" -c "
      for B in /usr/lib/openfoam/openfoam*/etc/bashrc /opt/openfoam*/etc/bashrc; do
        [ -f \"\$B\" ] && { . \"\$B\"; break; }
      done
      export FOAM_ETC=\"\${FOAM_ETC:-\$WM_PROJECT_DIR/etc}\"
      $body
    "
}

is_running() { docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; }

latest_time() {
  # highest reconstructed OR processor time, whichever exists
  ls -d "$CASE_DIR"/processor0/[0-9]* "$CASE_DIR"/[0-9]* 2>/dev/null \
    | sed 's#.*/##' | grep -E '^[0-9]' | sort -g | tail -1
}
