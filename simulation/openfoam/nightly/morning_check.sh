#!/bin/bash
# Reconstruct the night's new checkpoints, run the droplet analysis, and say
# whether the run is decisive yet. Read-only w.r.t. the running case: it only
# reconstructs and converts, so it is safe to call whether or not the solver is
# running (though normally you stop first).
#
# Prints, and also exits: 0 = keep running, 10 = decisive (you can stop for good).

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"

T=$(latest_time || echo 0)
echo "=============================================================="
echo " encoder_3d_mp — morning check   (latest checkpoint t = ${T} s)"
echo "=============================================================="

# 1. Reconstruct + convert, ECONOMICALLY. The extractor needs only the three
#    water-phase fields, and only the post-settle window -- so restrict to those.
#    Reconstructing all 6 fields over all times is what filled a near-full disk
#    at t=2.04 s. A disk guard aborts rather than repeating that.
FIELDS='(alpha.water1 alpha.water2 alpha.water3)'
SETTLE_FROM='0.35'                                  # just before the ~0.386 s cut
FREE_G=$(df -g "$CASE_DIR" | awk 'NR==2{print $4}')
echo "[check] ${FREE_G}G free. Reconstructing 3 fields, t>=${SETTLE_FROM}, + foamToVTK..."
if [ "${FREE_G:-0}" -lt 3 ]; then
  echo "[check] ABORT: <3 GB free — refusing to reconstruct and risk filling the disk."
  echo "        Free space (or move the run to external storage) and re-run."
  exit 2
fi
of_exec "reconstructPar -fields '$FIELDS' -time '${SETTLE_FROM}:' -newTimes > log.reconstruct 2>&1 || true
         foamToVTK -legacy -fields '$FIELDS' -time '${SETTLE_FROM}:' > log.foamToVTK 2>&1 || true"

# 2. Extract droplets (writes droplet_dye.csv). Tolerate "too early / none yet".
echo "[check] extracting droplets..."
if ! "$VENV_PY" "$SCRIPTS_DIR/extract_droplet_dye.py" "$CASE_DIR" > "$CASE_DIR/log.extract" 2>&1; then
  echo "[check] no mature droplets extractable yet (t=${T}s). Keep running."
  tail -2 "$CASE_DIR/log.extract" 2>/dev/null | sed 's/^/    /'
  exit 0
fi
grep -E "satellites below|droplet observations" "$CASE_DIR/log.extract" | tail -1 | sed 's/^/    /'

# 3. Analyse: core-vs-wall ± SE, symmetry, and the decisive-yet verdict.
"$VENV_PY" - "$CASE_DIR" "$SCRIPTS_DIR" <<'PY'
import sys, numpy as np
sys.path.insert(0, sys.argv[2])
from pathlib import Path
from analyze_encoder import load, track, per_droplet, flag_unstable
case = Path(sys.argv[1])
try:
    df, geom = load(case); d = track(df, geom)
    drops, ndrop, cut = per_droplet(d, geom); drops, uns = flag_unstable(drops)
except SystemExit as e:
    print(f"    analysis not ready: {e}"); sys.exit(0)

n = len(drops)
if n == 0:
    print(f"    settle cut is {cut['t_cut']*1e3:.0f} ms; no droplets past it yet. Keep running.")
    sys.exit(0)

core = (drops.c2 - 0.5*(drops.c1+drops.c3)).to_numpy()
a13  = (drops.c1 - drops.c3).to_numpy()
cse  = core.std(ddof=1)/np.sqrt(n) if n > 1 else float('nan')
period = cut['period']

print(f"    droplets past settle cut:  n = {n}   (period {period*1e3:.0f} ms)")
print(f"    core-vs-wall (3D signal):  {core.mean():+.4f} +/- {cse:.4f}"
      + (f"   ({abs(core.mean())/cse:.1f} sigma)" if n>1 and cse>0 else ""))
print(f"    leg asymmetry c1-c3:       {a13.mean():+.4f}   (expected real ~ -0.03)")
if len(uns):
    print(f"    ({len(uns)} unstable droplet(s) dropped as coalescence/mistrack)")

# Decision rule. The question: is the corner bias nonzero?
#  - clearly nonzero early  -> confirmed, stop.
#  - SE tight around ~0      -> bounded as 'no bias > 2% at 3 sigma', stop.
#  - otherwise               -> keep running.
NEED_SE = 0.0067          # 3-sigma resolution of a 2% effect
decisive = False; why = ""
if n >= 8 and cse > 0 and abs(core.mean()) > 3*cse and abs(core.mean()) > 0.015:
    decisive = True; why = "corner bias is clearly NONZERO -- the 3D effect is real."
elif n >= 8 and cse > 0 and cse <= NEED_SE:
    decisive = True; why = ("bias bounded tightly around zero -- no corner effect "
                            "larger than ~2%." if abs(core.mean()) < 0.015
                            else "bias resolved at target precision.")
if decisive:
    print(f"\n    >>> DECISIVE: {why}")
    print(f"    >>> You can stop for good. See results write-up next.")
    sys.exit(10)
else:
    need_n = int(np.ceil((core.std(ddof=1)/NEED_SE)**2)) if n > 1 else 34
    more_s = max(0.0, (need_n - n)) * period
    print(f"\n    keep running: need ~n={need_n} for a 3-sigma call "
          f"(~{more_s:.2f}s more sim, ~{more_s*47840/3600:.1f} h).")
    sys.exit(0)
PY
rc=$?

# Reclaim the reconstructed root time-dirs (regenerable from the processor
# checkpoints). Keeps the run dir small on a tight disk; VTK + CSV are kept for
# inspection, processor checkpoints are untouched so resume still works.
( cd "$CASE_DIR" && for d in [0-9]*; do [ "$d" != "0" ] && [ -d "$d" ] && rm -rf "$d"; done ) 2>/dev/null

echo "--------------------------------------------------------------"
echo "free after cleanup: $(df -g "$CASE_DIR" | awk 'NR==2{print $4}')G"
[ $rc -eq 10 ] && echo "verdict: DECISIVE — stop the run." || echo "verdict: keep running another night."
exit $rc
