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
| corr(Q_oil, Q_water) | +0.998 *(case-specific — see correction below)* | undefined (both constant) |

The velocity-driven control is flat to six significant figures — flow
imposed, junction cannot push back. The pressure-driven case oscillates as
a relaxation cycle locked to droplet formation: the flux period and the
independently-measured droplet formation period agree to **1.4%**, so the
inlets are being clocked by the droplets.

**Both inlets are driven by an unmeasured common cause** — the junction
pressure node. Neither causes the other; a method seeing only the two flow
rates should infer a spurious direct edge where the ground truth is a fork.
(The strength of that signature is *not* a robust number — see the
correction below.)

Across five operating points spanning the sweep window (`flux_summary.csv`):
water-inlet modulation 21–83% peak-to-peak, oil 3.5–7.0% in all cases —
the effect is systematic, not a single lucky point. The zero-lag
correlation is *not* uniform, though: r ranges 0.27–1.00, weakening at the
low-P_disp corner where water sits near the capillary entry threshold and
its dynamics change character. That variation is itself a usable feature —
coupling strength is tunable by operating point — but it means "r ≈ 1" is a
property of part of the window, not all of it.

## Same-geometry A/B (2026-07-18) — and a correction

The first pass compared a pressure-driven 2D serpentine run against a
velocity-driven 3D mill run: different geometries. This is the controlled
version — **identical mesh, identical endTime, identical 1 ms sampling,
`diff` confirming only `0/U` and `0/p_rgh` differ.** The velocity arm's
inlet speeds (39.67 / 34.17 mm/s) were set from the *measured* mean flux
of the pressure arm on the same mesh, so both arms sit at the same
operating point.

**The headline result is stronger than the first pass.** The two arms
produce essentially the same droplets:

| | pressure arm | velocity arm |
|---|---|---|
| slug length | 188 µm | 180 µm (−4%) |
| formation gap | 21.0 ms | 21.0 ms (identical) |
| droplet frequency | 45.0 Hz | 44.6 Hz (−0.9%) |
| **Q_water fluctuation** | **9.9% CV** | **0.00%** |
| **Q_oil fluctuation** | **2.2% CV** | **0.00%** |

An observer measuring only the droplets cannot tell the arms apart. An
observer with flow sensors distinguishes them instantly. Two different
causal structures, the same observable output distribution — which is
precisely why instrumenting the mediators is not optional, and is a clean
physical illustration of why observational equivalence is a real hazard.

Flux period locks to the droplet clock exactly: autocorrelation gives
21 ms against a 21.0 ms measured formation gap.

### Correction: the r ≈ 1 claim was not robust

The first pass reported `corr(Q_oil, Q_water) = +0.998 at zero lag` as a
headline "confounded pair" signature. **That number is case- and
mesh-specific and should not be quoted as a property of the chamber.** The
same nominal conditions (13/3 kPa) on the 7.5 µm mesh give **r = +0.31**,
and the earlier five-point survey already spanned 0.27–1.00.

The reason is visible in the phase-averaged cycle
(`ab_same_geometry.png`, right panel): **the coupling is impulsive, not
sinusoidal.** For ~12 ms of each 21 ms cycle the system is quiescent —
water ramps up smoothly while oil sits flat to ±1%, because the oil
resistor isolates it. Then pinch-off fires: water collapses ~22%, oil
jumps ~5%, and both recover over ~8 ms. A linear correlation coefficient
is simply the wrong summary statistic for that shape; computed over the
transient alone it is even *negative* (−0.53), since the two move
oppositely during the collapse.

What is robust across every pressure-driven case measured:

1. flux oscillates at **exactly** the droplet formation period,
2. the modulation is large (Q_water ~10% CV, up to 40% peak-to-peak),
3. the velocity-driven control is flat to six significant figures,
4. droplet output is nearly unchanged between arms.

The corrected picture is arguably the more interesting one for causal ML:
a **nonlinear, impulsive, state-dependent** coupling is a harder and more
realistic target than a linear confounded pair, and linear-Gaussian
methods will under-detect it precisely because the dependence is
concentrated in ~30% of the duty cycle.

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

## Sampling-rate pathologies (demonstrated, not argued)

The cyclicity result above says the *equilibrium* graph depends on the
actuator. This section shows the companion effect: what an analyst
concludes depends on the **sampling rate**, demonstrated by decimating the
1 ms flux record rather than by argument. See
`sampling_rate_pathologies.png` and `sampling_rate_sweep.csv`.

The true cycle is 44.8 Hz, so Nyquist requires sampling faster than
11.2 ms. Two decimation modes were compared, because they correspond to
two real measurement modalities:

- **Subsampling** (a strobe, or a camera with short exposure at low frame
  rate): the variance survives but is *relocated*. Apparent frequency goes
  44.8 → 38.5 → 17.7 → **5.2 Hz** as the interval goes 8 → 12 → 16 → 20 ms.
  At 20 ms the 45 Hz droplet cycle masquerades as a slow 5 Hz mode — an
  oscillation the chamber does not have.
- **Aggregation** (an integrating sensor, a long-exposure frame, an RC-
  filtered pressure line): the cycle is *hidden* instead. Water-inlet CV
  collapses monotonically 9.9% → 2.2%, and the chamber increasingly looks
  like a steady input-output map with no dynamics at all.

Same underlying data, two opposite errors: invent structure, or erase it.

**The unexpected result: the confounding survives everything.**
`corr(Q_oil, Q_water)` stays in 0.996–0.999 at *every* sampling interval,
in *both* decimation modes. The instantaneous fork through the junction
pressure node is robust; only the temporal structure is fragile. That
splits methods cleanly:

- Contemporaneous/instantaneous discovery (LiNGAM-style) should return a
  consistent answer at every rate — the fork is always visible.
- Lag-based discovery (Granger, VAR, PCMCI) should be *confidently wrong*
  below Nyquist, reporting a 5 Hz mechanism that does not exist.

That is a sharp, falsifiable prediction about method behaviour, on a
system where the right answer is known at every rate — and it is the
concrete form of the "the correct answer depends on your sampling rate"
claim.

### Hardware consequence

Camera frame rate and sensor sampling rate are **experimental variables,
not instrument specs**. Record as fast as affordable and decimate in post,
so one physical experiment yields the whole family of datasets; a slow
recording can never be un-slowed. This revises the earlier ">=120 fps"
guidance (which was the floor for merely *counting* droplets at 27 Hz):
for sampling-rate studies, target 500-1000 fps and kHz-rate pressure
logging.

### Caveats

- The record is 86 samples at 1 ms (0.085 s). At 20 ms decimation that is
  5 points, so the coarse-rate CV values are noisy; the apparent
  frequencies are the analytic alias predictions, visually corroborated by
  the figure rather than fitted. A longer run (0.5-1 s) would make the
  aliased peaks statistically solid.
- Most subsampling theory assumes stochastic processes; this cycle is
  near-deterministic. Arguably more interesting — deterministic dynamics
  that look like noise to any i.i.d.-assuming method — but a different
  regime than the theory was built for.

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
