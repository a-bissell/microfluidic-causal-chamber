# Mill-twin verification and operating-window sweep — 2026-07

First actual solve of [`tjunction_2d_mill`](../../tjunction_2d_mill/) — the
digital twin of the 400 µm chip millable with a single 1/64" endmill. Its
mesh had been checkMesh-clean since the case was created, but interFoam had
never been run on it until now; every number in the case's README was
back-of-envelope hydraulic design math, not a checked simulation.

## Reference-point verification

One run at the twin's documented operating point (P_cont = 3.9 kPa,
P_disp = 1.8 kPa, endTime 0.3 s ≈ startup + 2 droplet periods): 7,203 s
(2.0 h) wall time. Droplets form, detach, and exit cleanly — 3 distinct
formation events, 90 ms apart.

| Observable | Design prediction | Simulated | Diff |
|---|---|---|---|
| Slug length | ~540 µm | 600 µm | +11% |
| Advection speed | ~25 mm/s | 28.3 mm/s (hand-tracked) / 28.0 mm/s (script) | +12–13% |
| Frequency | ~9 Hz | 11.1 Hz (hand-counted from 3 formation events) | +23% |

The chip design is now simulation-confirmed, not just algebra.
`droplet_filmstrip.png` shows the run: water column descends (5 ms), the
tongue bends into the cross-flow and blocks the junction (50 ms), the
first ~600 µm slug detaches and transits (90–110 ms), and the cycle
settles into its steady ~90 ms rhythm (150–300 ms).

## Operating-window sweep

25 cases, 5×5 grid at ±18% around the reference point (P_cont ∈ {3200,
3550, 3900, 4250, 4600} Pa, P_disp ∈ {1500, 1650, 1800, 1950, 2100} Pa), no
repeats — this geometry's stability boundaries were unmapped going in, so
breadth was prioritized over statistics this round (same precedent as the
serpentine case's first 3×3 before its later 5×5×3). 25/25 succeeded,
~9,900 s/case average, ~7 h wall time at 6-way concurrency.

**All 25 cells form droplets. L/w and speed are perfectly monotonic**
across every row and column (L/w: 1.25–1.80, decreasing in P_cont,
increasing in P_disp; speed: 22–34 mm/s, increasing in P_cont) — see
`response_maps.png`. This is the bench-tuning map: if real droplets don't
land exactly on the predicted 600 µm/28 mm/s at 3.9/1.8 kPa, this grid says
which direction to move each water column.

The swept reference-point cell (P_cont=3900, P_disp=1800) independently
reproduces the standalone verification almost exactly — L/w = 1.500 (vs.
600/400 = 1.500) and speed 28.0 mm/s (vs. 28.3 mm/s hand-tracked) — two
separate runs of the same setup landing on the same answer.

## A bug found and fixed along the way

The first analysis pass on this sweep produced garbage (`L/w` inflated
2.67×, most cases showing zero droplets). Cause: `extract_droplets.py` and
`analyze_pressure_sweep.py` hardcoded the *original* 150 µm-channel
geometry (junction position, channel width, frequency reference line,
droplet length cap) — none of which apply to this 400 µm-channel, 46 mm
feed-serpentine geometry. Both scripts are now geometry-parameterized
(`--w-main-um`, `--x-junction-um`, `--x-ref-um`, `--outlet-x-min/max-um`,
`--free-length-max-um`); defaults reproduce the original case's numbers
exactly (regression-checked against the committed `psweep5x5_2026-07`
results). This run used:

```
python3 scripts/analyze_pressure_sweep.py --sweep-dir <dir> \
    --w-main-um 400 --x-junction-um 2400 --x-ref-um 4000 \
    --outlet-x-min-um 2400 --outlet-x-max-um 6400 --free-length-max-um 2000
```

## Caveats

- **Frequency is unreliable in this dataset** — the crossing-counter is
  badly quantized at only 0.3 s per case (≈2–3 droplet periods), producing
  a noisy, non-monotonic map (3.3–10 Hz) even though hand-tracking the
  same VTK output gives a clean, physically sensible 11.1 Hz at the
  reference point. Same known limitation documented in `psweep_2026-07`
  and `protocol_v1_2026-07`; use L/w or speed, or re-run with a longer
  `endTime`, for frequency work on this geometry.
- 2D, single seed per cell, no repeats — indicative response surfaces, not
  converged statistics (same caveat as every other `results/` set here).
- The oil-feed serpentine is modelled straight in the 2D mesh; the real
  chip's folded layout is hydraulically equivalent by design but untested.
