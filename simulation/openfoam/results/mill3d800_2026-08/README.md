# 3D fidelity check, done properly — 800 µm chip — 2026-08

Replaces [`mill3d_2026-07`](../mill3d_2026-07/), whose speed and frequency
corrections were withdrawn after the run was found to have been fed 79%
more water than the case it was compared against.

## What was wrong, and what is different here

The 2026-07 run had **two** confounds, not one:

1. **Operating point.** `0/U` set 0.02 / 0.01 m/s, i.e. q = Q_disp/Q_cont =
   0.50, against a 2D reference whose *measured* ratio was q = 0.28. This
   was the one already identified.
2. **Actuation mode.** A velocity-driven 3D case was compared against a
   *pressure*-driven 2D case. Since the cyclicity work established those
   are different causal structures, dimensionality and actuation were
   varied together.

Both are removed here.

The operating point is now **derived from the measured 2D fluxes** rather
than assumed, and the derivation lives in the BC file itself:

```
2D 800 µm measured:  Q_oil = 12.694 µL/s,  Q_water = 3.706 µL/s
both inlets are w × w  ->  U = Q / w²
    U_oil   = 0.019834 m/s
    U_water = 0.005791 m/s
    q  = 0.2919   (2D measured 0.292)
    Ca = 0.0317   (design 0.032)
```

The actuation confound is removed by running a **2D baseline through the
same generator**: `gen_blockmesh.py --w-main 800 --two-d` emits the identical
domain as a single-cell-thick mesh. Same 2 mm approach, same junction, same
4 mm outlet, same 40 µm cells, same velocity BCs. **Dimensionality is the
only thing that differs.**

| | cells | endTime | wall time |
|---|---|---|---|
| 2D baseline | 4,400 | 0.6 s | 33 min, serial |
| 3D (half-depth) | 44,000 | 0.6 s | 1.85 h, 6-way MPI |

## Result: the corrected 2D → 3D correction

Five complete droplets in 3D, three in 2D, both trains metronomic (3D gaps
110/110/110/110 ms; 2D 175/175 ms).

| Observable | 2D | 3D | correction |
|---|---|---|---|
| Slug length | 1240 µm | 1080 µm | **×0.87** (−12.9%) |
| L / w | 1.550 | 1.350 | ×0.87 |
| Slug width | 680 µm (0.85 w) | 760 µm (0.95 w) | ×1.12 |
| Period | 175.0 ms | 110.0 ms | ×0.63 |
| **Droplet rate** | 5.71 Hz | **9.09 Hz** | **×1.59** |
| Slug speed | 28.65 mm/s | 33.50 mm/s | ×1.17 |
| Droplet volume | 649 nL | 408 nL | ×0.63 |

**Physical reading.** In 2D the continuous phase can only bypass a forming
droplet through side films, which forces the droplet narrow (0.85 w) and
lets it grow long before the neck breaks. In 3D it escapes through the four
corners a rounded interface cannot seal, so the droplet widens to nearly the
full channel (0.95 w) *and* pinches off sooner. Net: shorter, wider, 37%
smaller in volume, 59% more of them.

`cmp_2d3d_800um.png` shows this directly. The third filmstrip row is a
near-wall slice (z ≈ 20 µm off the milled floor) where the water is a small
compact core surrounded by oil, against the mid-plane row where the slug is
a full-width body. That difference is the corner gutter, and 2D has no way
to represent it.

### Three independent checks

- **Mass conservation is exact.** Droplet volume ratio 0.6286 equals the
  inverse frequency ratio (110/175 = 0.6286). Same imposed water flux,
  smaller droplets, proportionally more of them.
- **The 3D case reproduces a textbook result the 2D case cannot.** Slug
  speed ÷ superficial velocity is **1.307** in 3D, against the classic
  square-channel slug bypass ratio of ~1.33. 2D gives 1.118 — it has no
  corners to bypass through.
- **The 2D baseline reproduces the pressure-driven 2D run exactly**:
  1240.0 µm and 175 ms in both, across two different domains (4,400 vs
  6,440 cells, with and without the 46 mm feed serpentine) and two
  actuation modes. So actuation mode does not affect mean droplet metrics
  at a matched operating point — it only governs whether inlet flow rates
  oscillate, which is the cyclicity result, not a geometry result.

That last check also settles what the 2026-07 confound cost: the actuation
half of it was **benign**. The whole error was the operating point.

## Against the withdrawn numbers

| | withdrawn (400 µm, q = 0.50) | corrected (800 µm, q = 0.29) |
|---|---|---|
| Slug length | +3% | −12.9% |
| Slug speed | ×1.43 | ×1.17 |
| Droplet rate | ×2.4 | ×1.59 |

Every one differs, and the length correction changes sign. That sign change
explains why the bad result looked convincing: a real ~−13% 3D shortening
plus a large positive bias from 79% excess water nets out near zero, which
was reported as "2D length maps certified".

**These are not decomposable.** The withdrawn figures were taken at 400 µm
and these at 800 µm, so the gap between the columns mixes the operating-point
error with any genuine width dependence. Corner gutters scale with the
channel, so at fixed Ca the correction *should* be width-independent — but
that is an argument, not a measurement. A corrected 400 µm run would settle
it; nothing here does.

## Consequences

**Hardware first light at 800 µm**: expect **~1080 µm slugs at ~9.1 Hz
moving ~33.5 mm/s, ~408 nL each** — not the 2D-based 1240 µm / 5.7 Hz /
28.5 mm/s. Water throughput is unchanged (3.7 µL/s is imposed), so the "1 L
of sample in ~75 h" figure still stands; you just get more, smaller drops.

**Camera specs tighten.** Earlier guidance derived from the 2D numbers
(≥90 fps, ≤360 µs exposure at 800 µm) is superseded:

| | from 2D | corrected |
|---|---|---|
| Interface speed | 28.5 mm/s | 33.5 mm/s |
| Exposure for ≤1% of L blur | ≤360 µs | **≤320 µs** |
| Exposure for ≤5 µm blur | ≤180 µs | **≤150 µs** |
| Frame rate, 15 frames/period | ≥87 fps | **≥140 fps** |

The practical change is the frame rate: 120 fps is now marginal rather than
comfortable, so target 140–200 fps. The strobed-backlight approach matters
more, not less, since 150 µs is a demanding exposure.

**Slug-length response maps still transfer, with a scale factor.** L/w is
1.35 in 3D against 1.55 in 2D — a uniform ×0.87, not a reshaping. The
operating-window map in `../window600_2026-07/` keys off L/w and its
*ordering* is unaffected; multiply the values by ~0.87 for 3D expectations.

## Files

- `cmp_2d3d_800um.png` — filmstrips (2D, 3D mid-plane, 3D near-wall) on a
  common physical scale, plus the correction bars against the withdrawn
  figures
- `metrics.csv` — the numbers in the results table

## Reproduce

```bash
# 3D case and its matched 2D baseline, one generator
python3 gen_blockmesh.py --w-main 800            # 44,000 cells
python3 gen_blockmesh.py --w-main 800 --two-d    #  4,400 cells

python3 scripts/plot_2d3d_comparison.py \
    --case-2d $CASES/m800_2d --case-3d $CASES/m800_3d \
    --w-main-um 800 --period-2d 0.175 --period-3d 0.110 \
    --out cmp_2d3d_800um.png
```

## Caveats

- **Half-depth symmetry.** The domain models z = 0 to w/2 with a mid-plane
  symmetry, which assumes the floor and lid wet identically. A real chip is
  milled PMMA on the bottom and 3M 468MP adhesive on top — a genuine
  asymmetry the model does not carry. This is a first-light question, not
  something this run can answer. A full-depth spot check is the fallback if
  the bench shows z-asymmetric behaviour.
- **Single operating point.** The correction factors are measured at the
  reference conditions only and assumed roughly regime-constant across the
  window. Unverified, as at 400 µm.
- **One mesh resolution.** 40 µm cells, i.e. w/20 — the same relative
  resolution as every 2D case here, but no 3D convergence study was run.
  The thin oil film between slug and wall is a fixed physical thickness set
  by Ca and is under-resolved at this cell size.
