# Operating window at 600 µm — 2026-07-31

## The question

`scaleup_2026-07` established that 600 and 800 µm reproduce the 400 µm
chamber's physics, but left one thing open, and it was the one thing the
hardware guide actually needs:

> The ±18% window is a 400 µm measurement being extrapolated. Given that the
> capillary threshold is a larger fraction of drive pressure at 800 µm, the
> window may well be narrower there.

The worry is concrete. Capillary entry pressure is 2σ/w, so it *falls* with
width in absolute terms (150 → 100 → 75 Pa) but the drive pressure falls
faster (as 1/w²), so as a **fraction** of drive it grows: 8.3% at 400 µm,
12% at 600, 15.3% at 800. If that fraction is what bounds the window, a
wider chip is easier to machine but fussier to actuate — and the guide would
have to say so.

## Design

25 cases on the 600 µm chip, 5×5 in (P_cont, P_disp), **±30%** about the
reference point — deliberately wider than the ±18% used at 400 µm. Reason:
that sweep returned 25/25 dripping, so it never found its own edge either.
Repeating ±18% here would most likely have returned another 25/25 — parity,
but still no boundary. ±30% has a real chance of bracketing an edge, and if
it also comes back clean that is a strictly stronger result.

| | Pa | cm H₂O |
|---|---|---|
| P_cont | 1210 / 1470 / **1730** / 1990 / 2250 | 12.3 / 15.0 / **17.6** / 20.3 / 22.9 |
| P_disp | 580 / 705 / **830** / 955 / 1080 | 5.9 / 7.2 / **8.5** / 9.7 / 11.0 |

Column heights are given throughout because that is the quantity a builder
sets on the bench, not pascals.

endTime 0.45 s (≥ 2 droplet periods even at the slowest corner), write
interval 5 ms (≈27 frames per period), 6-way concurrency. 136,812 s of
solver time total, mean 5472 s/case, ~6.4 h wall. Raw data 6.2 GB, off-repo.

Extraction uses the track-based `extract_mature_droplets.py` via
`analyze_window_sweep.py` — the static length/position filter would count
still-growing attached threads as droplets, which matters most at exactly
the extreme cells this sweep exists to probe.

## Result: 25/25 drip. No edge, in any direction.

**The window at 600 µm is at least ±30% on both actuators** — 12.3–22.9 cm
of oil against 5.9–11.0 cm of water — and its edges lie outside this sweep.
**The motivating concern is not borne out.** In relative terms the 600 µm
window is at least as wide as the 400 µm one, despite the capillary
threshold being a larger fraction of drive pressure. At the lowest P_disp
tested, 580 Pa is still 5.8× the 100 Pa entry threshold; the threshold is
simply not what bounds this window.

### Slug length L/w — monotonic in 25/25 cells

| L/w | 580 Pa | 705 | 830 | 955 | 1080 |
|---|---|---|---|---|---|
| **1210 Pa** | 1.63 | 1.75 | 1.89 | 2.01 | 2.21 |
| **1470** | 1.45 | 1.55 | 1.68 | 1.80 | 1.95 |
| **1730** ★ | 1.35 | 1.45 | **1.55** | 1.65 | 1.75 |
| **1990** | 1.25 | 1.35 | 1.45 | 1.55 | 1.60 |
| **2250** | 1.15 | 1.25 | 1.35 | 1.43 | 1.50 |

Increasing in P_disp and decreasing in P_cont with no reversals anywhere.
The anti-diagonals are near iso-L/w: one step up in P_cont almost exactly
cancels one step up in P_disp.

Range 1.15–2.21, wider than the 400 µm sweep's 1.25–1.80.

### Validation against an independent run

The centre cell is the same operating point as the standalone 600 µm run in
`scaleup_2026-07`, launched separately by a different driver. It reproduces
it at **L = 932.3307 µm, L/w = 1.5539 — identical to seven significant
figures**. Period is 137.5 ms here vs 135 ms there, a 1.9% difference that
is the different write interval (5 vs 7.5 ms) quantizing formation times.

This is the check that caught the geometry-hardcoding bug in the 400 µm
sweep, where 150 µm assumptions inflated L/w by 2.67×. The grid passes it.

## Caveats

**L/w is resolution-limited.** Slug length is quantized to about one mesh
cell (30 µm, i.e. ΔL/w ≈ 0.05), and adjacent grid cells differ by only 1–2
quanta. The monotonic *ordering* is therefore real and the gradient
direction is trustworthy, but the surface cannot resolve structure finer
than ~0.1 in L/w. Do not read the exact per-cell values as converged.

**Two cells have unreliable frequencies.** Everything else follows a smooth
gradient (4.3 → 10.5 Hz, rising with both actuators); these two break it and
are visible as outliers in `window_map.png`:

- `pc1.21k_pd1.08k` reports 5.4 Hz where ~8 is expected. This is the
  longest-slug cell (L/w = 2.21 → a 1.32 mm slug in a 4 mm outlet), and 3 of
  its 6 tracks were incomplete. The fixed 4 mm outlet is the known
  truncation problem already flagged in `scaleup_2026-07`; this is where it
  bites. Its L/w is the number in the grid I would trust least.
- `pc2.25k_pd0.83k` reports 11.4 Hz where ~8 is expected, from a 87.5 ms
  formation gap that does not fit its neighbours.

Both are formation-gap estimates from few tracks at 5 ms quantization. Use
L/w, not frequency, for anything load-bearing — the same guidance the 400 µm
campaign arrived at.

**Single repeat per cell.** No actuation noise, so this measures the
response surface, not its repeatability. `psweep5x5_2026-07` did 3 noisy
repeats at 400 µm and found median CV 2.2%; that is assumed to carry over.

## For the hardware guide

The practical answer is that column height is a **usable continuous
actuator with generous tolerance**, not a knob that has to be hit exactly:

- Any water column between 5.9 and 11.0 cm and any oil column between 12.3
  and 22.9 cm produces droplets. There is no cliff inside that box.
- Sensitivity at the reference point: **0.079 in L/w per cm of water
  column**, 0.051 per cm of oil. So holding L/w to ±0.01 needs the water
  column set to about ±1.3 mm — trivial for a bottle on a printer Z-axis
  (0.1 mm resolution), and roughly a 100× margin.
- The reference point sits in the middle of the box, not near an edge, so
  drift in either direction degrades gracefully rather than stopping
  droplet formation.

## Files

- `window_results.csv` — one row per cell: pressures in Pa and cm H₂O,
  regime verdict, droplet count, L, L/w, period, frequency
- `window_map.png` — regime map, L/w surface, frequency surface

## Reproduce

```bash
python3 scripts/sweep_pressure.py --base-case <600um case> \
    --output-dir $CASES/psweep600 \
    --p-cont 1210 1470 1730 1990 2250 \
    --p-disp 580 705 830 955 1080 \
    --end-time 0.45 --write-interval 0.005 --concurrency 6

python3 scripts/analyze_window_sweep.py $CASES/psweep600 \
    --w-main-um 600 --write-interval 0.005 --out-dir .
```

## Not done

- **The window's actual edges.** Still unmeasured, now at ±30% rather than
  ±18%. Finding them needs a wider or 1-D scan; whether that is worth ~6 h
  of compute depends on whether anyone needs a number beyond "much wider
  than you will ever need on the bench".
- **800 µm.** The capillary-fraction argument predicts the window is
  narrowest there (15.3% vs 12%). This sweep weakens the premise but does
  not test that width.
- **3D.** Everything here is 2D. See the standing note in
  `scaleup_2026-07`.
