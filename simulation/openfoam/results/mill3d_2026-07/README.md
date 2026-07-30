# 3D fidelity check — millable chip twin — 2026-07-18

> ## ⚠️ SUPERSEDED — the speed and frequency numbers below are confounded
>
> This run was **not** at the 2D twin's operating point, contrary to what
> the paragraph below originally claimed. `0/U` set the water inlet to
> 0.01 m/s against an oil inlet of 0.02 m/s, i.e. Q_disp/Q_cont = 0.5. The
> 2D reference case's *measured* flux ratio is q = 0.28 (Q_oil 3.193,
> Q_water 0.895 µL/s at 3.9/1.8 kPa — see `../scaleup_2026-07/`). This run
> therefore fed **79% more water** than the case it was being compared to.
>
> Of the headline ×2.4 frequency ratio, roughly ×1.79 is just the extra
> water. The corner-gutter effect is real and the ×3% length agreement is
> unaffected (length is weakly dependent on q), but **the ×1.43 speed and
> ×2.4 frequency factors must not be quoted** as the 2D→3D correction.
>
> `tjunction_3d_mill/0/U` was corrected to 0.0056 m/s on 2026-07-18. The
> re-run at the corrected operating point was started and then killed when
> the project pivoted to the 600/800 µm scale-up, so **no corrected 3D
> measurement exists yet.** Everything below is kept for provenance.

First 3D simulation of the project: `tjunction_3d_mill` (84k cells,
half-depth symmetry domain), intended to sit at the velocity-driven
operating point the 2D mill twin was verified at (Ca = 0.032,
Q_disp/Q_cont = 0.25 as specified — 0.5 as actually run; see the
correction above, and note the 2D case's *measured* ratio is 0.28, so the
0.25 target was itself slightly off).
Solved in 8.25 h on the M4 mini at 6-way MPI (smoke-gated first: 2.4×
parallel speedup, both modes FATAL-free). This was meant to answer the
question every 2D dataset carried as a caveat: **what does the 2D shortcut
cost?** It does not yet answer it.

## Result as originally reported (confounded — see the box above)

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

## Consequences for hardware first light — WITHDRAWN

The three bullets that stood here told the guide to expect ~27 Hz and
~40 mm/s and to scale the 2D response maps by ×1.4 and ×2.4. Those came
from the confounded comparison and are withdrawn. What survives:

- **Slug length ~620 µm (L/w 1.55) still stands.** Length is only weakly
  dependent on q through Garstecki (L/w = 1 + αq), and 1.55 is what the
  2D scale-up measured independently at 600 and 800 µm. The 2D response
  maps' slug-length panel still transfers, and map-guided column tuning
  (which keys off slug length) is unaffected.
- **Corner-gutter bypass is real** — oil does route past the forming
  droplet through the four corners a rounded interface cannot seal — but
  its *magnitude* is unmeasured, because the measurement was taken against
  the wrong baseline.
- **Use the 2D numbers until a corrected 3D run exists**: ~11 Hz and
  ~28 mm/s at 400 µm, ~7.4 Hz and ~28 mm/s at 600 µm, ~5.7 Hz and
  ~28 mm/s at 800 µm (`../scaleup_2026-07/`). Treat these as *lower*
  bounds on frequency, since gutter bypass shortens the cycle in the
  direction the confounded run pointed, by an unknown factor.
- **Camera ≥120 fps still holds**, but now for headroom rather than from
  a 27 Hz measurement.

## Caveats

- Single operating point; the correction factors are measured at the
  reference conditions and assumed roughly regime-constant across the
  ±18% window — plausible (same regime everywhere per the 2D sweep) but
  unverified. A 3-point 3D mini-sweep would bound it if it matters.
- Half-depth symmetry assumed (standard for this regime); a full-depth
  spot check is the fallback if hardware shows z-asymmetric behavior.
- Startup track (first droplet, 660 µm) excluded from the steady-state
  numbers, consistent with all prior analyses.
