# Cyclicity test: actuation mode determines the causal graph — 2026-07

Tests a claim raised in project discussion: **how the chamber is driven
decides whether its causal graph contains a cycle**, on the same chip with
the same physics.

- **Pressure sources** (`totalPressure` inlets; hydrostatic columns or a
  regulator in hardware): flow rates are *emergent*. A forming droplet
  occludes the junction → continuous-phase resistance rises → junction
  pressure rises → both inlets are pushed back → pinch-off relieves it.
  Q_oil and Q_water are mutually determined through the shared junction
  node, and the equilibrium graph contains a cycle.
- **Flow sources** (`fixedValue` U inlets; syringe pumps in hardware): Q is
  imposed exogenously, incoming edges are severed, the graph is close to a
  DAG. A syringe pump acts as a physical do-operator.

We had already built both — pressure-driven (`tjunction_2d_serpentine`,
`tjunction_2d_mill`) and velocity-driven (`tjunction_2d`,
`tjunction_3d_mill`) cases — for hydraulic convenience, without noticing
they were two different causal structures. So the claim was testable on
existing data, with no new simulation.

## Result: confirmed, and the effect is large

Measured with `scripts/extract_inlet_flux.py` (per-face flux through the
inlet patches, Newell method).

| | pressure-driven | velocity-driven |
|---|---|---|
| Q_water fluctuation | **41% peak-to-peak** | 0.00% |
| Q_oil fluctuation | 6.4% peak-to-peak | 0.00% |
| flux cycle period | 22.3 ms (**44.8 Hz**) | — (flat) |
| droplet period (measured independently) | 22.0 ms (44.6 Hz) | — |
| corr(Q_oil, Q_water) | **+0.998 at zero lag** | undefined (both constant) |

The velocity-driven control is flat to six significant figures — flow
imposed, junction cannot push back. The pressure-driven case oscillates as
a relaxation cycle locked to droplet formation: the flux period and the
independently-measured droplet formation period agree to **1.4%**, so the
inlets are being clocked by the droplets.

**The zero-lag near-unity correlation is the causally interesting part.**
Q_oil and Q_water are not causing each other; they are driven simultaneously
by an unmeasured common cause (the junction pressure node). That is a
textbook confounded pair delivered by physics — a method seeing only the
two flow rates should infer a spurious direct edge, and the ground truth
says it is a fork.

Across five operating points spanning the sweep window (`flux_summary.csv`):
water-inlet modulation 21–83% peak-to-peak, oil 3.5–7.0% in all cases —
the effect is systematic, not a single lucky point. The zero-lag
correlation is *not* uniform, though: r ranges 0.27–1.00, weakening at the
low-P_disp corner where water sits near the capillary entry threshold and
its dynamics change character. That variation is itself a usable feature —
coupling strength is tunable by operating point — but it means "r ≈ 1" is a
property of part of the window, not all of it.

## An important qualification: cyclicity is timescale-relative

Unrolled in time this is still a DAG — Q(t) → P(t+δ) → Q(t+2δ). The cycle
is what remains after marginalising over the fast pressure-propagation
timescale (sub-millisecond) relative to the sampling interval. So what the
actuator toggles is whether the *equilibrium* (time-marginalised) graph has
a cycle, and the sampling rate decides whether an analyst can tell.

This strengthens rather than weakens the benchmark: the chamber can emit a
dataset where the correct causal answer *depends on the sampling rate*,
with physics stating which answer is right at which rate — directly
relevant to the causal-discovery-under-subsampling literature.

## Files

- `actuation_mode_comparison.png` — the two-panel figure.
- `flux_pressure_driven_pc13k_pd3k.csv` — flux time series, pressure-driven
  (serpentine chip, 13/3 kPa, 1 ms sampling).
- `flux_velocity_driven_mill3d.csv` — flux time series, velocity-driven
  control (3D mill chip at the reference point).
- `flux_summary.csv` — the five-operating-point survey.

## Caveats

- The velocity-driven control is 3D/mill and the pressure-driven case is
  2D/serpentine — different geometries. This does not affect the
  conclusion (the control's flatness is guaranteed by its boundary
  condition, and the pressure case's oscillation is established on its own
  terms), but a same-geometry A/B is the cleaner demonstration and is
  cheap to run if this becomes a published figure.
- Hardware will not reproduce the control's perfect flatness: real syringe
  pumps have compliance and tubing elasticity, so some coupling leaks back.
  That is a feature — a controllable *degree* of edge severance rather than
  a binary.
