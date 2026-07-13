# T-junction with inlet resistor channels (pressure-driven)

The same T-junction as [`../tjunction_2d`](../tjunction_2d), plus a long
narrow **resistor channel upstream of each inlet** — the 2D hydraulic
equivalent of the serpentine feed channels on a real chip. This is the
case to use for **pressure-actuated** runs, i.e. the causal-chamber
actuation model (P_cont, P_disp as actuators).

```
                                    │ │  ← water inlet (top of 30 µm × 4 mm resistor)
                                    │ │
                                    ┌┴┐
oil ══════════════════════════╗     │ │  ← 75 µm water channel
    ← 75 µm × 3 mm resistor → ╚═════╧═══════════════ → outlet
                              ← 150 µm main channel →
```

## Why the resistors

On the resistor-less geometry the pressure operating window is razor-thin
(see `../results/sweep_2026-07`): P_disp = 650 Pa cannot breach the
~800 Pa capillary entry pressure at the junction, while 1500 Pa gushes.
The resistors carry most of the driving pressure drop, so:

| | without resistors | with resistors |
|---|---|---|
| P_cont at reference flow | ~850 Pa | **~13 kPa** (real controller range) |
| P_disp at reference flow | ~1.4 kPa (edge of window) | **~3 kPa** |
| water sensitivity | ~unbounded | ~0.8 mm/s per 100 Pa |
| capillary breach surge | unbounded (gushing) | ~6 mm/s |

Reference operating point (set in `0/p_rgh`): **P_cont = 13 kPa,
P_disp = 3 kPa** → U_oil ≈ 20 mm/s, U_water ≈ 10 mm/s at the junction
(Ca = 0.032, Q_disp/Q_cont = 0.25), matching the verified velocity-driven
case.

## Mesh

`system/blockMeshDict` is **generated** — edit and re-run
`gen_blockmesh.py` (geometry, cell size, and resistor dimensions are
parameters at the top). 20 conformal blocks, 5,500 cells: 7.5 µm cells in
the two-phase region, long streamwise cells in the single-phase resistors
(graded finer toward the junction).

## Running

Same workflow as `../tjunction_2d` (`./Allrun`, or the Docker commands in
the main README). Sweep P_cont/P_disp with
`../scripts/run_parametric.py`, whose defaults still target the
resistor-less case — pass values around the reference point above for
this geometry.
