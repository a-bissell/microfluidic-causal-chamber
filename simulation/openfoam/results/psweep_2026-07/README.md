# Pressure-actuated sweep — 2026-07-13

First sweep in the **causal-chamber actuation mode**: pressures are the
actuators, droplet metrics the observables. Run on
[`tjunction_2d_serpentine`](../../tjunction_2d_serpentine/) (inlet
resistor channels), which is what makes a pressure grid feasible at all —
on the resistor-less geometry the operating window was single-point.

## Setup

- Grid: P_cont ∈ {10, 13, 16} kPa × P_disp ∈ {2.4, 3.0, 3.6} kPa
- endTime 0.08 s (≥ 2 droplet periods in every cell), interFoam v2306
  in Docker, serial, 6 concurrent (~65–80 min/case)
- Provenance: `psweep.py` (driver), `panalyze.py` (metrics/maps);
  paths hardcoded to the session scratchpad

## Results (`psweep_results.csv`, maps in `psweep_maps.png`)

- **All 9 cells produce periodic droplet trains** — the resistor design
  achieves a wide, sweepable operating window at controller-realistic
  pressures.
- **Slug length L/w**: monotonically increasing in P_disp and decreasing
  in P_cont in every row/column (1.05 → 1.90 across the grid) — the
  expected causal response through Q_disp/Q_cont.
- **Droplet speed**: monotonic in P_cont (21 → 37 mm/s), the direct
  P_cont → Q_total path.
- **Frequency**: rises toward high-P_disp corners (25 → 50 Hz). The
  12 Hz cell at (16 kPa, 3.0 kPa) is a known artifact of the
  crossing-count frequency metric at 2 ms output frames (undercounting
  at high rates), not a physical dip — recompute from VTK with finer
  write intervals before using frequency quantitatively.

## Relation to the causal graph

These maps are direct measurements of the ground-truth mechanism
P_cont, P_disp → Q_cont, Q_disp → (f, L, v) from the project plan
(`hardware/microfluidic/microfluidic_chamber_plan.md`). Next packaging
step: emit this grid (plus interventional labels) in the causal-chamber
dataset format under `datasets/mf_tjunction_*`.

## Caveats

2D, 7.5 µm mesh, single seed per cell, one endTime — indicative response
surfaces, not converged statistics. See `../sweep_2026-07/README.md` for
the shared caveats and the Garstecki validation backing the metrics.
