#!/bin/bash
# Start or resume the 3D encoder run for one session, detached.
#
# Idempotent and safe to call unattended:
#   - if already running, it does nothing and exits 0;
#   - on the first call it meshes, seeds, and decomposes, then solves;
#   - on every later call it resumes from the last checkpoint (startFrom
#     latestTime), so it NEVER re-meshes or resets the clock.
#
# Pair with stop_clean.sh in the morning. Progress goes to log.solver.

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"

if is_running; then
  echo "[run] '$CONTAINER' is already running (t=$(latest_time)). Nothing to do."
  exit 0
fi

# A previous stop_clean set stopAt=writeNow; flip it back so the solver runs to
# endTime rather than stopping on the first step.
sed -i.bak 's/^stopAt .*/stopAt          endTime;/' "$CASE_DIR/system/controlDict"
rm -f "$CASE_DIR/system/controlDict.bak"

echo "[run] launching '$CONTAINER' (detached, $NP ranks). Resume time: $(latest_time || echo 0)"

docker run -d --rm --name "$CONTAINER" --entrypoint bash \
  -e OMPI_ALLOW_RUN_AS_ROOT=1 -e OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1 \
  -v "$RUNROOT:/w" -w "/w/$CASE" "$IMAGE" -c '
    for B in /usr/lib/openfoam/openfoam*/etc/bashrc /opt/openfoam*/etc/bashrc; do
      [ -f "$B" ] && { . "$B"; break; }
    done
    export FOAM_ETC="${FOAM_ETC:-$WM_PROJECT_DIR/etc}"

    if [ ! -d processor0 ]; then
      echo "=== fresh start $(date -u) ===" >> log.solver
      rm -rf [1-9]* 0.[0-9]* VTK postProcessing 2>/dev/null
      [ -d 0.orig ] || cp -r 0 0.orig
      rm -rf 0 && cp -r 0.orig 0
      blockMesh              > log.blockMesh   2>&1 || { echo BLOCKMESH_FAIL >> log.solver; exit 1; }
      checkMesh              > log.checkMesh   2>&1
      setFields             > log.setFields   2>&1 || { echo SETFIELDS_FAIL >> log.solver; exit 1; }
      decomposePar          > log.decomposePar 2>&1 || { echo DECOMPOSE_FAIL >> log.solver; exit 1; }
    else
      echo "=== resume $(date -u) from t='"$(latest_time || echo 0)"' ===" >> log.solver
    fi

    mpirun --allow-run-as-root -np '"$NP"' multiphaseInterFoam -parallel >> log.solver 2>&1
    echo "=== solver exited $(date -u) ===" >> log.solver
  '

sleep 3
if is_running; then
  echo "[run] started. Watch:  tail -f $CASE_DIR/log.solver"
else
  echo "[run] WARNING: container exited immediately — check $CASE_DIR/log.solver"
  tail -5 "$CASE_DIR/log.solver" 2>/dev/null
  exit 1
fi
