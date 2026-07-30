# tjunction_2d_mill — digital twin of the millable 400 µm chip

Simulation twin of a T-junction chip fabricated with the workflow from
[The Makers Guide to Microfluidics](https://www.instructables.com/The-Makers-Guide-to-Microfluidics/):
CNC-milled PMMA (single 1/64" endmill, 0.4 mm deep), 3M 468MP bonding,
3D-printed luer surface-mount ports. Same droplet regime as the validated
[`tjunction_2d_serpentine`](../tjunction_2d_serpentine) case
(Ca = 0.032, Q_disp/Q_cont = 0.25), rescaled to shop-floor feature sizes.

## Chip spec (what to mill)

| Feature | Value | Note |
|---|---|---|
| All channels | 400 µm wide × 400 µm deep | one 1/64" endmill, two 0.2 mm passes |
| Oil feed | 46 mm serpentine → junction | modelled straight in sim; fold to fit blank |
| Water leg | ≥ 2 mm from port to junction | |
| Outlet | ≥ 4 mm past junction | observation window: expect 2–3 slugs in view |
| Water feed resistance | **~31 cm of 0.3 mm-ID microbore tubing** upstream of the water port | water is too thin for a millable on-chip resistor; sim models it as an 80 µm × 27 mm channel with identical ΔP |

## Operating point (sim reference values)

| | Value | Hydrostatic equivalent |
|---|---|---|
| P_cont | ~3.9 kPa | ~40 cm water column |
| P_disp | ~1.8 kPa | ~18 cm water column |
| Capillary entry threshold | ~150 Pa | (vs ~800 Pa at 150 µm — wide stable window) |

Expected observables: **~600 µm slugs (L/w 1.50) at ~11.4 Hz, ~28 mm/s** —
measured, `../results/mill_2026-07/`.

> An earlier revision of this section quoted ~620 µm at ~27 Hz and
> ~40 mm/s "corrected after the 3D fidelity check". Those factors are
> withdrawn: the 3D run was fed 79% more water than the 2D case it was
> compared against (q = 0.5 vs the 2D measured 0.28), so most of the ×2.4
> rhythm was extra water, not corner-gutter bypass. See the correction box
> in [`../results/mill3d_2026-07/`](../results/mill3d_2026-07/). The +3%
> slug-length agreement survives, so the length response maps remain the
> bench-tuning chart. Corner-gutter bypass is real but currently
> unquantified, and it acts to *raise* frequency — treat 11.4 Hz as a
> lower bound and **film at ≥120 fps** for headroom.

**This width is no longer the recommended design.** A 1/64" endmill is a
high bar for replication. 600 µm and 800 µm reproduce this chamber to
within 4% on every observable and are far more forgiving to machine — see
[`../results/scaleup_2026-07/`](../results/scaleup_2026-07/) and generate
the wider geometry with `python3 gen_blockmesh.py --w-main 600`.

Both pressures sit inside the guide's balloon rig range (~2–4 kPa), but for
causal-chamber use the actuators must be *measured and repeatable*:
motorized hydrostatic columns or a small pump + MPX5010-class I2C sensor
(0–10 kPa) + PID are the cheap options. Instrument gap ≈ $200–600 total.

## Fluids

As `constant/transportProperties`: 50 cSt silicone oil + 2% Span 80
(continuous), DI water + food coloring (dispersed). **Hardware risk to
check first**: the sim assumes strongly oil-wet walls (θ₀ = 160°). Test a
water droplet on Span-80-doped-oil-flooded PMMA and 468MP adhesive before
committing to a chip — if water wets either surface, droplets will wall-pin
exactly like the December sim did.

## Running the twin

`system/blockMeshDict` is generated — edit `gen_blockmesh.py` and re-run
it. Mesh: 10 blocks, 9,440 cells, 20 µm transverse. Same Docker workflow
as the other cases; endTime 0.3 s ≈ startup + 2 droplet periods
(~45–60 min serial). Sweep with `../scripts/sweep_pressure.py
--base-case tjunction_2d_mill` using pressures around the reference point.

## Status

- [x] Mesh generated and checkMesh-clean; setFields regions verified
- [x] Solver verification at the reference point — droplets confirmed,
      slug length/speed/frequency within 11–23% of the design math (see
      `../results/mill_2026-07/`)
- [x] Operating-window sweep → the map hardware data lands on: 25/25 cells
      form droplets, L/w and speed perfectly monotonic across the ±18%
      pressure window (see `../results/mill_2026-07/`)
