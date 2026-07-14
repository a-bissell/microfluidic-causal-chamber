# 5×5×3 pressure-actuated dataset — 2026-07-14 (overnight run)

The first full MCC dataset: 75 cases on `tjunction_2d_serpentine`
(P_cont ∈ {10, 11.5, 13, 14.5, 16} kPa × P_disp ∈ {2.4, 2.7, 3.0, 3.3,
3.6} kPa × 3 repeats with seeded ~2% actuation noise), run with
`scripts/sweep_pressure.py --write-interval 0.001` on an M4 Mac mini
(~15.5 h, 6 concurrent Docker containers). Raw case data (~13 GB) lives
off-repo; this folder is the curated summary.

## Results

- **75/75 completed; droplets in every case** — the whole window is
  robust to actuation noise.
- **Slug length L/w monotonic in both actuators across all 25 cells**
  (1.04 → 1.75); droplet speed likewise (21 → 37 mm/s). These are the
  ground-truth causal responses P → Q → droplet metrics as data.
- **Within-cell repeatability: median CV 2.2%** across the 3 noisy
  repeats per cell — real variance for statistical methods, small enough
  to leave the response surfaces crisp.
- Frequency spans 17–50 Hz; the finer 1 ms write interval fixed the
  crossing-counter undercount seen in the 3×3, though values remain
  quantized (integer crossings over a ~60 ms window). Use per-droplet
  intervals from the raw VTK for fine-grained frequency work.

## Files

- `results.csv` — one row per case: nominal + actually-applied pressures,
  droplet metrics.
- `causal_dataset.csv` — causal-chamber variable schema (P_*, P_*_meas,
  f/L/d/v observables, intervention flag). Candidate `mf_tjunction` seed.
- `response_maps.png` — frequency / L over w / speed over the actuator grid.
- `cases.json` — full case definitions including the per-repeat noise draws.
