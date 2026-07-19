# 3D fidelity check — millable chip twin — 2026-07-18

First 3D simulation of the project: `tjunction_3d_mill` (84k cells,
half-depth symmetry domain) at the exact velocity-driven operating point
the 2D mill twin was verified at (Ca = 0.032, Q_disp/Q_cont = 0.25).
Solved in 8.25 h on the M4 mini at 6-way MPI (smoke-gated first: 2.4×
parallel speedup, both modes FATAL-free). This answers the question every
2D dataset carried as a caveat: **what does the 2D shortcut cost?**

## Result: the 2D→3D correction, measured

7 complete droplet tracks, 6 of them at *identical* 620 µm length, on a
metronomic 37.5 ms beat (see `mature_tracks_3d.txt`, filmstrip in
`droplet_filmstrip_3d.png`):

| Observable | 2D twin | 3D twin | Correction |
|---|---|---|---|
| Slug length | 600 µm (L/w 1.50) | 620 µm (L/w 1.55) | **+3% — 2D length maps certified** |
| Droplet speed | 28 mm/s | 40.0 mm/s (IQR 40.0–40.1) | ×1.43 |
| Frequency | 11.1 Hz | 26.7 Hz | ×2.4 |

Self-consistency: slug volume from mass conservation (Q_water/f = 60 nL)
matches measured slug geometry (~62 nL), and droplet speed is 1.33× the
superficial velocity — the classic square-channel slug bypass ratio.

**Physical reading**: corner gutters (the four corners of a square channel
that a droplet's rounded interface can't seal) let oil bypass the forming
droplet. This barely changes how much water accumulates per droplet
(length ≈ unchanged) but breaks the neck far sooner (2.4× the rhythm) and
carries slugs faster (bypass flow adds drag on the caps).

## Consequences for hardware first light

- **Expect ~620 µm slugs at ~27 Hz moving ~40 mm/s** at the reference
  columns (40 cm oil / 18 cm water). The 2D-based expectation of ~11 Hz
  is superseded.
- **Camera: use ≥120 fps.** At 27 Hz, 60 fps gives only ~2.2 frames per
  droplet cycle — marginal for counting, useless for pinch-off detail.
- The 2D response maps' *slug-length* panel transfers essentially as-is
  (+3%); treat the speed and frequency panels as shape-correct but
  multiply by ~1.4× and ~2.4× respectively. Map-guided column tuning is
  unaffected (it keys off slug length).

## Caveats

- Single operating point; the correction factors are measured at the
  reference conditions and assumed roughly regime-constant across the
  ±18% window — plausible (same regime everywhere per the 2D sweep) but
  unverified. A 3-point 3D mini-sweep would bound it if it matters.
- Half-depth symmetry assumed (standard for this regime); a full-depth
  spot check is the fallback if hardware shows z-asymmetric behavior.
- Startup track (first droplet, 660 µm) excluded from the steady-state
  numbers, consistent with all prior analyses.
