# Parametric sweep — 2026-07-13

First working parametric sweep of the corrected T-junction case
(see the July 2026 boundary-condition fix documented in
`../../tjunction_2d/0/U` and the main OpenFOAM README).

## Setup

- **Solver**: interFoam, `opencfd/openfoam-default:2306` Docker image (arm64),
  serial, one container per case, 6 concurrent.
- **Mesh**: 2D, 7.5 µm cells (1.5× coarser than the repo case, chosen for
  laptop runtime; ~9–27 min/case).
- **Grid**: U_oil ∈ {10, 20, 30} mm/s × U_water ∈ {5, 10, 15} mm/s
  → Ca ∈ {0.016, 0.032, 0.048}, Q_disp/Q_cont ∈ {0.083 … 0.75},
  plus pressure-driven pilots (see below).
- **Driver / analysis**: `sweep.py`, `aggregate.py` (paths hardcoded to the
  session scratchpad — kept here as provenance for `sweep_results.csv`).

## Results

- **All 9 velocity-driven cases produced periodic droplet trains** (10–43 Hz).
- **Garstecki scaling recovered**: L/w = 0.80 + 1.24 · (Q_disp/Q_cont),
  R² = 0.94. Slope α = 1.24 sits in the literature range (α ≈ 1–3).
  The intercept below 1 and the Ca-stratification of the residuals are
  expected: the law is exact only in the squeezing limit (Ca → 0), and the
  Ca = 0.048 cases sit visibly below the pooled fit (shear-assisted breakup
  shortens slugs).
- **Slug metrics** are medians over detached droplets in the mid-outlet
  (700–1450 µm), from `scripts/extract_droplets.py`.

## Pressure-driven pilots

- `pilot_p850_650` (P_cont = 850 Pa, P_disp = 650 Pa): oil flows at
  14.8 mm/s (Ca ≈ 0.024) but **water never enters** — the capillary entry
  pressure at this scale (σ/(w/2) ≈ 800 Pa) exceeds the ~95 Pa of
  overpressure the water inlet has over the junction. A real chip avoids
  this because tubing/serpentine resistance lets the controller sit far
  above the junction pressure.
- `pilot_p850_1500` raises P_disp above the capillary entry threshold and
  **forms droplets**: 16.7 Hz, L/w = 1.80 (long slugs — 1500 Pa drives a
  high water flow ratio, ~0.8 by the Garstecki fit), oil at 9.2 mm/s
  (Ca = 0.015). Pressure actuation therefore works end-to-end; its
  operating window on this short domain is roughly
  P_disp ∈ (junction pressure + ~800 Pa capillary entry, jetting onset),
  i.e. narrow — adding upstream channel resistance to the geometry would
  widen it and make pressure sweeps practical for datasets.

## Caveats

- 2D, coarse mesh: quantitatively indicative, not converged. Re-run the
  repo-resolution (5 µm) or 3D case before publishing numbers.
- The frequency metric counts reference-line crossings between output
  frames; at high rates with 2 ms frames it can undercount (the
  uo30_uw15 case reads 12 Hz against a ~45 Hz trend).
- endTime 0.085–0.1 s ≈ 2–4 droplet periods per case; longer runs would
  tighten the medians.
