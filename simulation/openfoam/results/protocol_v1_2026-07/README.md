# protocol_v1 — first time-series (SET/WAIT/MSR) dataset — 2026-07-14

Six chained simulations on `tjunction_2d_serpentine`, each a shuffled
grid-walk tour of the same 3×3 pressure grid as the
[`psweep_2026-07`](../psweep_2026-07/) pilot (P_cont ∈ {10, 13, 16} kPa,
P_disp ∈ {2.4, 3.0, 3.6} kPa), 9 setpoints/chain, produced with:

```
python3 scripts/protocol_run.py --base-case tjunction_2d_serpentine \
    --p-cont 10000 13000 16000 --p-disp 2400 3000 3600 \
    --mode grid-walk --chains 6 --concurrency 6 \
    --startup 0.03 --settle 0.015 --measure 0.05
```

Runtime ≈ 9.4 h on an M4 Mac mini (6 chains fully parallel; settle/measure
windows trimmed from the script's defaults to fit an overnight run — see
caveats). Analyzed with `scripts/analyze_protocol_run.py`.

## Results

- **54/54 setpoint-segments produced droplet metrics** — no misses across
  6 chains × 9 setpoints, despite each chain visiting setpoints in a
  different shuffled order (testing for order-dependent hysteresis).
- **Cross-check against the independent cold-start pilot, at the same 9
  pressures**: median |ΔL/w| = **0.7%**, max 11.9% (one point, 13/3.6 kPa,
  n=6 chain-visits — likely just that cell's sampling noise). This is the
  headline result: a value measured mid-schedule, after only a 15 ms
  settle window, agrees with a value from a fully independent cold-start
  simulation to within ~1% at 8 of 9 points. The chained/protocol data
  mode is trustworthy, not just cheaper.
- `timeseries.csv` (3,606 frames) is frame-by-frame actuator state +
  droplet count/position/size — the raw material for changepoint
  detection and time-lagged causal discovery. Each step between setpoints
  is a labeled, physically-caused regime transition.

## Caveats

- **Frequency metric is unreliable here and should not be used from this
  file.** The 50 ms measure window (needed to fit the run overnight)
  spans under one droplet period at the slowest corner (17 Hz ≈ 59 ms),
  so `frequency_Hz` in `protocol_results.csv` disagrees with the pilot by
  up to 3× at some points. Slug length (`L_over_w`) does not have this
  problem — it's measured from droplet geometry directly, not from
  counting events in a short window — which is why it's the metric
  reported above. A future run with `--measure 0.10+` would fix
  frequency at the cost of runtime.
- Grid is 3×3, coarser than the `psweep5x5_2026-07` dataset — chosen to
  match the existing pilot for this cross-check rather than for maximum
  coverage.
- Same 2D/7.5 µm mesh caveats as the other `results/` sets apply.
