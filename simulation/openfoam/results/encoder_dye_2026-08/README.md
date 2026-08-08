# Encoder dye transport: the passive-scalar method does not measure composition — 2026-08

## What this directory concludes

The encoder twin ([`tjunction_3d_encoder`](../../tjunction_3d_encoder/)) reads a
droplet's code by integrating three `scalarTransport` dye fields over the
droplet. **That measurement has a floor of roughly 20%, against an effect of
roughly 2%.** About a fifth of the dye leaves the droplet and sits in the oil,
the loss is strongly differential between the three laminae, and the resulting
composition does not converge under mesh refinement — the core-vs-wall
signature *changes sign* between 40 µm and 60 µm cells.

The planned 3D run is therefore **not interpretable** and should not be
launched against this method. Mesh refinement will not rescue it: measured
leakage scales as `dx^0.49`, so reaching 2% would need sub-micron cells.

This is a negative result about the *instrument*, not about the encoder. The
droplet physics in this geometry remains verified (see the case README's
cross-merge table). What is not verified — and cannot be, this way — is the
composition readout built on top of it.

**The replacement is already known to work.** `multiphaseInterFoam` — abandoned
in [`f10ae84`](#the-revert-was-a-false-negative) because it "does not drip" —
does drip, with the config exactly as it was abandoned. It produces 1240 µm
slugs on a 160 ms period, matching `interFoam` in this geometry, and its
composition fields are MULES-conserved and bounded, which deletes this entire
failure mode rather than mitigating it. See **The revert was a false negative**
below. Fidelity on multiphase is being measured now; formation and
conservation are confirmed.

## The one piece of good news

The `scalarTransport` function objects **work**. They were the case's single
`⚠️ unverified` item, blocked locally by the Ubuntu 24.04 OpenFOAM package
(`1912.200626-2build3`) aborting on *any* function object with
`error in IOstream "sha1"`.

Running under `opencfd/openfoam-default:2306` (Docker, arm64) they load and
advect with no error, with the `libs ("libsolverFunctionObjects.so")` spelling
exactly as written. `check_dye_transport.py` passes all three tests. That
blocker is closed; use the ESI image.

## Runs

All 2D, `--w-main 800`, velocity inlets, `c = (⅓, ⅓, ⅓)`, serial in the ESI
2306 image. `writeInterval` 0.0025 s.

| run | dx | cells | endTime | maxDeltaT | wall time |
|---|---|---|---|---|---|
| pre-flight | 40 µm | 6,800 | 0.02 s | 1e-5 | 2 min |
| reference | 40 µm | 6,800 | 0.8 s | 1e-5 | 50 min |
| **main** | 40 µm | 6,800 | **2.0 s** | 1e-5 | **2.1 h** |
| **coarse** | 60 µm | 2,964 | **2.0 s** | 1e-5 | **45 min** |
| refine | 20 µm | 27,200 | 1.6 s | 3.5e-6 | **abandoned, see below** |

`maxDeltaT` was deliberately held at 1e-5 between 40 and 60 µm so that `dx` is
the only variable. It could not be held for the 20 µm run — the capillary
limit goes as `dx^1.5` — which is one reason that run was a weaker test than
it looked.

Droplet physics is preserved across the two resolutions that completed, so
`dx` is cleanly isolated: slug length 1303 → 1232 µm (−5.4%), period 170 →
157 ms (−7.6%), advection speed 32.8 → 32.7 mm/s (−0.3%). All inside the ±10%
band used elsewhere in this project.

## The measurement bug, and why it hid the problem

`extract_droplet_dye.py` integrated `dye_i` over the droplet's x-window **plus
a 3-cell halo**, with no alpha mask — the halo existed to capture the diffuse
interface shell rather than clip it at `alpha = 0.5`.

`dye_i` is a volume fraction of water-of-type-i. Integrating it over cells
that contain no water counts dye that has **leaked into the oil** as though it
were still droplet content. Because dye1 and dye3 sit at the rear and front
caps of the slug, that leakage is asymmetric, and the measured composition
became a function of how much oil the window happened to enclose:

| halo (cells) | `c1−c3` | core-vs-wall |
|---|---|---|
| 0 | −0.043 | −0.022 |
| 3 *(the default)* | −0.016 | −0.021 |
| 8 | +0.008 | −0.024 |
| 15 | +0.033 | −0.029 |
| 25 | +0.054 | −0.031 |
| 40 | +0.069 | −0.035 |
| 55 | +0.076 | −0.037 |

Neither column converges. Worse, **the default halo of 3 sat near `c1−c3`'s
zero crossing**, so the symmetry control — the gate gating every claim this
case makes — read as a clean pass (`+0.0016`, SE 0.0017) on what was an
artifact of the window size.

**The fix**: mask the integral to cells that actually contain water
(`water > threshold`). The droplet then defines the integral instead of the
window, and the result is halo-independent *by construction* — verified
identical to five decimals from halo 0 to halo 40.

## Results under the corrected measurement

| | dx = 40 µm | dx = 60 µm |
|---|---|---|
| c1 / c2 / c3 | 0.2890 / 0.3241 / 0.3868 | 0.2527 / 0.3437 / 0.4036 |
| **dye outside the droplet** | **17.78%** | **21.65%** |
| closure error over wet cells | 17.55% | 23.87% |
| `c1−c3` | −0.098 | −0.151 |
| `c1−c3`, strict cut (α>0.9) | −0.088 | −0.165 |
| core-vs-wall | −0.014 | **+0.016** |
| core-vs-wall, saturated (last 4) | −0.019 | **+0.012** |

Three things kill the method:

1. **~20% of the dye is not in the droplet.** This is the honest leakage
   figure. It was previously invisible because the unmasked integral counted
   the leaked dye as content, which partially cancelled the error.
2. **The loss is differential.** `c1−c3` is −0.098 where geometry guarantees
   zero, and it grows to −0.151 when the mesh is coarsened. dye1 (rear cap)
   loses more than dye3 (front cap).
3. **The core signature does not converge — it changes sign.** −0.019 at
   40 µm, +0.012 at 60 µm. There is no value to extrapolate.

## Why refinement cannot fix it

Leakage went 17.78% → 21.65% for `dx` 40 → 60 µm, i.e. `dx^0.49`. Extrapolating
and, for safety, repeating the calculation under stronger assumed scalings:

| assumed scaling | leakage at dx = 20 | dx needed for < 2% |
|---|---|---|
| `dx^0.49` (measured) | 12.7% | 0.5 µm |
| `dx^1` | 8.9% | 4.4 µm |
| `dx^2` | 4.4% | 13 µm |

Every case leaves dx = 20 µm at more than double the effect size, and the mesh
required to get under it is infeasible in 2D — let alone 3D, where it would be
cubed.

The 20 µm run was launched and killed after measuring its rate: **120,500 s per
simulated second**, i.e. 53.5 h for 1.6 s, against a 19 h estimate that assumed
cost scales as cells × steps (the pressure solve needs more iterations per step
on the finer mesh, costing 2.8× beyond the naive scaling). It was stopped
because it would have spent two days confirming a number the table above
already predicts, without changing any decision.

## Root cause

`alpha.water` is advected by MULES with interface compression. The dyes are
`scalarTransport` function objects on the **mixture flux** `phi`, with no
compression and no coupling to `alpha`. Nothing ties `Σ dye_i` to
`alpha.water`; the identity is true by construction and enforced by nothing.
So dye diffuses out of the sharp alpha interface into cells where `alpha ≈ 0`
and stays there.

`div(phi,dye)` is already `limitedLinear01` — a bounded scheme, correctly
chosen. This is not a scheme mistake; clipping each dye to [0,1] individually
does not constrain their sum against `alpha` in interface cells. The problem
is structural.

This is precisely the cost the case README anticipated when it moved off
`multiphaseInterFoam` — *"a passive scalar gets no MULES compression, so it is
neither conserved nor bounded"*. That trade was made because
`multiphaseInterFoam` would not form droplets. **This directory is the
measurement of what the trade cost: too much.**

## The revert was a false negative

`f10ae84` moved this case off `multiphaseInterFoam` on the finding that it
"does not form droplets" — *"the thread stays attached past 2.5 mm and keeps
growing at ~27 mm/s instead of necking."* The case was restored from
`f10ae84^` and re-run unmodified, 2D, `--w-main 800`, ESI 2306:

| t (s) | attached thread | detached droplets |
|---|---|---|
| 0.15 | 1320 µm | |
| 0.20 | 2640 µm | |
| **0.21** | 240 µm | **1240 µm @ 4500** |
| 0.26 | 280 µm | 800 µm @ 5980 |
| 0.36 | 2480 µm | |
| **0.37** | 600 µm | **1560 µm @ 4020** |
| 0.40 | 0 µm | 1200 µm @ 5220 |

It drips. Slug length **1240 µm**, period **160 ms**, advection **29.6 mm/s** —
against `interFoam` in this same geometry at 1240 µm, 170 ms, ~30 mm/s.

The original observation was *correct*: between t = 0.15 and 0.20 the thread
runs 1320 → 2640 µm, i.e. **26.4 mm/s past 2.5 mm**, matching the commit's
"~27 mm/s" to the digit. **The first pinch-off is at 205 ms, just past where
that observation stopped.** The measurement was right; the conclusion was one
frame early.

No water is seeded below `y = 800 µm` (every `setFields` box starts at the
channel roof), so anything in the outlet channel arrived through the junction.
These are droplets, not initial condition being flushed.

### `cAlpha` was a real defect but not the blocker

`multiphaseMixture.C` reads a **single global** `cAlpha` —
`phic = min(cAlpha*phic, max(phic))` — and applies it inside a nested loop over
every phase pair, so `water1–water2`, `water1–water3` and `water2–water3` are
all told to sharpen into distinct interfaces. Three artificial interfaces
inside what is physically one body of water. There is no per-pair knob.

That is a genuine formulation defect and it is the second suspect the revert
commit named. It was **not** blocking pinch-off: runs at `cAlpha 1` and
`cAlpha 0` both drip. Keep `cAlpha 1` and its sharp interface.

## What to do instead

Not more compute, and not a scheme change. Three routes were considered; one is
tested and dead, one is untested, one works.

**❌ Advect the dyes on the water flux.** Tested. `alphaPhi0.water` is
registered and written by `interFoam`, and `scalarTransport` accepts
`phi alphaPhi0.water;` with no error — the plumbing exists. But it does not
fix the leak. A/B in a single run, two identical dye fields differing only in
that line, measuring the fraction of each in essentially-pure-oil cells:

| t (s) | mixture flux | water flux |
|---|---|---|
| 0.03 | 0.068% | **0.000%** |
| 0.06 | 0.313% | **0.011%** |
| 0.09 | 0.796% | 0.765% |
| 0.12 | 1.164% | **1.833%** |
| 0.15 | 1.760% | **2.634%** |

~30× better early, ~50% worse by 0.15 s, and accelerating. Swapping the flux
gives `∂dye/∂t + ∇·(alphaPhi·dye) = 0`, which is not conservative — the water
flux is not divergence-free, `∇·alphaPhi = −∂alpha/∂t` — and it treats `dye` as
a concentration when it is defined as a content. Where water is still, dye
cannot move, which is why it looks so good early. Where `alpha` is changing —
necking, pinch-off, exactly where the code is written — the inconsistency
generates error faster than the leak it prevents.

**◻ Solve for `dye_i/alpha`.** The correct passive-scalar formulation:
`∂(alpha·c)/∂t + ∇·(alphaPhi·c) = 0`, bounded in [0,1] independently of
interface smearing. Needs both changes together and cannot be expressed in
`scalarTransport` at all — a coded function object or a modified solver,
compiled. Untested. This is the fallback if multiphase disappoints on fidelity.

**✅ Return to `multiphaseInterFoam`.** It drips (above), and each phase is
MULES-advected: phase-sum holds at 1.000000 to machine precision, undershoot
~5e−6, and material in essentially-pure-oil cells is **0.028%** against the
passive scalars' 1.76% at matched time — ~100×, and *flat* rather than growing,
because MULES bounds it.

Acceptance test, on this directory's data: **material in pure-oil cells below
~2%, and a core-vs-wall signature that does not change sign between 40 µm and
60 µm.** Multiphase clears the first by two orders of magnitude.

## The fidelity run: multiphase passes the 2D null

A 2.0 s multiphase run, same mesh, same `endTime`, same `writeInterval` as the
passive-scalar `null2d_long` — solver the only difference:

| | passive scalars | multiphase |
|---|---|---|
| droplets after the 515 ms cut | 8 | 8 |
| period | 170 ms | **170 ms** |
| slug length | 1303 ± 14 µm | 1293 ± 166 µm |
| closure error | 17.55% | **0.00% (identity)** |
| material in pure-oil cells | ~18% | **~0%** |
| **core-vs-wall (the null)** | **−0.019 (6.6σ)** | **+0.0065 ± 0.0139 (0.47σ)** |
| `c1−c3` | −0.098 | −0.034 ± 0.015 (2.3σ) |
| `c1−c3`, strict cut | −0.088 | −0.035 |

**The core-vs-wall null passes** — consistent with zero at 0.47σ, where 2D
demands zero. Under passive scalars the same quantity sat at 6.6σ and flipped
sign with mesh spacing. This is the first time the experiment's own null has
held. Composition fidelity under multiphase is confirmed; the readout works.

Two caveats it also surfaced, both real:

**Multiphase is ~10× noisier per droplet.** Between-droplet SD is 0.039 vs
0.004, and slug length varies ±166 µm vs ±14 µm. The satellite shedding
(below) is the likely sink — mass leaving the slug irregularly. Consequence
for 3D: resolving a 2% corner bias at 3σ needs SE ≤ 0.0067, i.e. **n ≈ 34**,
not the 8–9 the run plan assumed. That is `endTime` ≈ 6.5 s in 2D (~11 h) and
days-scale serial in 3D. A longer 2D run (6.5 s) is under way to pin `c1−c3`.

**`c1−c3` = −0.034 at 2.3σ, cut-independent (−0.034 vs −0.035).** Under the 3σ
gate so the analyzer passes it, but it is not clean and it is not a windowing
artifact. **The 6.5 s run below confirms it is real.**

## The 6.5 s run: the leg asymmetry is real, the signal survives it

34 droplets (the n the noise demands for a 3σ statement), 2D, multiphase:

| quantity | value | over the run | verdict |
|---|---|---|---|
| `c1 − c3` (the validity gate) | **−0.035**, 2.9–3.6σ | −0.031 → −0.040, stable | **real leg asymmetry** |
| core-vs-wall (the 3D signal) | **−0.008**, 0.9σ | +0.007 → −0.022 | **null holds** |

`c1 − c3` did not wash out with more droplets — it is stationary across both
halves. The mechanism is in the sign: `dye1` (upstream arm, facing the oncoming
oil) reads 0.318; `dye3` (downstream arm, in the slug's lee) reads 0.354. Oil
crosses the junction in +x, so the upstream-facing lamina is stripped slightly
more as each slug forms. This is an in-plane hydrodynamic asymmetry with nothing
to do with 3D corners.

**The design's validity gate is therefore wrong.** `c1 ≠ c3 ⇒ invalid run`
assumed the legs are equivalent; they are not, so the gate would reject every
run, good ones included. But the quantity it was protecting does not need it:
core-vs-wall averages c1 and c3, so it cancels this asymmetry by construction,
and it holds at 0.9σ. **Remove the gate; keep the signal.**

The loose thread — a core-vs-wall drift +0.007 → −0.022 across the run — was
run down and **is not real.** Lag-1 autocorrelation of the per-droplet core is
0.15 (essentially white noise; a genuine slow settling would be autocorrelated),
and the −0.035 OLS slope collapses to −0.007 when four flagged droplets are
removed. One droplet does most of it: a coalescence event at t≈3.96 s (core
−0.20, c3=0.53) whose composition scatters ±0.043 frame-to-frame — 12× the
0.0035 of a clean slug — i.e. not one rigid droplet at all.

That motivated a **within-droplet-scatter filter** (`flag_unstable` in
`analyze_encoder.py`): a slug's code is fixed at pinch-off, so frames that
disagree flag a coalescence or a tracking slip, not a symbol. The threshold is
self-calibrating (median + 4·MAD of the population's own within-scatter,
floored at 0.015 so a clean run invents no cut). It is deliberately *not* the
|core|>0.07 test used in this write-up — that one peeks at the answer and biases
the mean toward zero; the scatter filter removes droplets for being
self-inconsistent, independent of what value they land on. On the 6.5 s run it
drops exactly the one coalescence droplet and the null tightens to **−0.0018**
(from −0.0076); on the 2.0 s run it drops none. Passive-scalar runs are
untouched (their within-scatter ~0.001 is far below the floor).

### A second extractor bug, found here

The first multiphase analysis was wrong: it reported a **62 ms** period against
the 160 ms measured directly off the filmstrip. Cause: the speck filter was
`e - s < 5`, counting **cells, not x-stations**. In 2D a body one column wide
still carries ~20 cells stacked across the channel, so it passed. interFoam
produces no satellites here, so it never mattered; multiphase sheds many —
**651 satellite observations against 212 real slugs** in the 2.0 s run.
Counting them as droplets pulled the period to 62 ms and made every downstream
statistic meaningless.

Fixed with a physical filter: a slug spanning the channel cannot be shorter
than one channel width (`--min-length-um`, default `w_main`). The satellite
count is now reported. Whether the satellites are physical or an artifact of
the global `cAlpha` sharpening the three water phases against one another is
open — if the latter, suppressing them would cut the per-droplet noise and
shorten every run after.

## Fixes made to the analysis chain

These are independent of the dye problem and worth keeping.

**1. The startup cut was ~2.5× too short** (`analyze_encoder.py:settle_cut`).
It used `t_transit_s` = `l_leg / u_leg` = 207 ms, the leg alone. But
`setFieldsDict` seeds uniform ⅓ water across the whole column above the
junction — leg *and* the square merge node on top of it (+138 ms) — and a
droplet then needs one formation period (+170 ms). Correct cut: **515 ms**.
The 0.8 s reference run passed two still-settling droplets, whose core
signature was −0.087 and −0.039 against the one clean droplet's +0.002;
averaging the three produced a false ASYMMETRIC verdict.

The cut now acts on **formation time per droplet**, not frame time. Filtering
frames kept a contaminated droplet alive on its later frames and left only
far-downstream ones, lengthening the extrapolation below exactly where it is
weakest.

**2. Composition is now read at pinch-off** (`analyze_encoder.py:_fit_to_station`).
A droplet's composition is fixed when it detaches — the dyes are the same
fluid, advected with `D = 0`. But the *measured* composition drifts as the
droplet travels (−0.009 to −0.016 per mm in `c1−c3`), because the leak is
differential. Each `c_k` is now regressed on x and evaluated at
`x_junction`. Side benefit: `within_sd` is now the residual about that fit,
which is real measurement noise — it was previously dominated by the drift and
overstated ~3×.

**3. `n = 1` no longer reads as a pass.** With one droplet `ddof=1` gives
`nan`, and every downstream comparison against `nan` evaluates false, printing
"Symmetric within scatter" on no evidence. It now reports the run inconclusive.

**4. New diagnostics**: composition at a stricter interface cut, so a verdict
that flips between cuts is visible rather than hidden, and two separate leakage
numbers — see below, because conflating them is easy and misleading.

**5. Two leakage metrics, because one is not comparable between solvers.**
`dye_outside_frac` is material below the 0.5 mask. For passive scalars that is
part interface shell and part genuine escape; for multiphase it is interface
shell *only*, since a water phase cannot exist where there is no water.
Multiphase reads **higher** on it (27.7% vs 17.8%) purely because its interface
is more diffuse. `dye_dry_frac` — material in cells with `water < 0.01` — means
the same thing in both and is the one to compare on.

**6. The extractor reads both formulations.** `multiphaseInterFoam` has no
`alpha.water`; the three water phases *are* the water and the total is their
sum. `resolve_fields()` detects which naming the output uses, so one extractor
serves both solvers and nothing else in the measurement chain differs when
comparing them.

**7. Satellite filter is physical, not a cell count.** The old speck filter
`e - s < 5` counted cells; a one-column body carries ~20 cells in 2D and
passed. Replaced with a length floor of one channel width (`--min-length-um`).
Only surfaced under multiphase, which sheds satellites where interFoam did not.

The masked integral is correct for multiphase too, which was not obvious —
there is no leak to exclude, so the mask might have been discarding real
signal. Measured: masked is halo-stable to five decimals from halo 0 to 20,
unmasked drifts ~10% over the same range. The mask stays. (Beyond halo ~40 the
window reaches the neighbouring droplet — 1600 µm of halo against a ~3560 µm
gap — which is a window too large, not a method failure.)

## Corrections to readings made during this work

Recorded because each was stated with apparent support before more data
arrived, and the sequence is instructive:

- *"The compositions converge to zero as the transient washes out."* From
  n = 3 (−0.087, −0.039, +0.002). They saturate at **−0.021**, passing through
  zero at exactly the droplet the 0.8 s run happened to contain.
- *"The core bias is robust to the halo, so it is likely real 2D physics."*
  The halo sweep only covered 0–8 cells. Extended to droplet spacing it moves
  −0.022 → −0.037, and under the corrected mask it flips sign with resolution.
- *"`c1−c3` = +0.0016, the symmetry control passes."* An artifact of
  `halo_cells = 3` sitting on the zero crossing. Correctly measured it is
  −0.098.
- *"Passive scalars leak 17.8%, multiphase 0.028% — 600× better."* Two
  different measurements set side by side: the first per-droplet below the
  0.5 mask, the second domain-wide in pure-oil cells. On the same metric
  multiphase reads **higher** (27.7%), because its interface is more diffuse.
  The like-for-like comparison is 1.76% vs 0.018% at matched time. The
  conclusion held; the numbers quoted for it did not. This is what
  `dye_dry_frac` exists to prevent.
- *"`cAlpha` between the water phases is the likely cause of the no-drip."*
  A real defect — it is global and does apply between water pairs — but not
  the cause of anything, because there was no no-drip to explain.
- *"The masked integral is robust, so the multiphase null can be trusted as
  first reported."* The first multiphase analysis was not trustworthy at all:
  a satellite-counting bug put the period at 62 ms and the core bias at
  −0.093. Only after the length filter did the real numbers appear (170 ms,
  +0.0065). The lesson repeats the session's theme — a derived quantity
  (here the period) that disagrees with a directly measured one (160 ms off
  the filmstrip) is the tell that something upstream is miscounting.

## Files

| | |
|---|---|
| `droplet_dye_dx40.csv` | passive scalars, 2.0 s, 40 µm — 8 droplets after the 515 ms cut |
| `droplet_dye_dx60.csv` | passive scalars, 2.0 s, 60 µm — 9 droplets |
| `droplet_dye_multiphase_2s.csv` | **multiphase**, 2.0 s, 40 µm — 8 droplets, the null that passes |
| `droplet_dye_multiphase_6p5s.csv` | **multiphase**, 6.5 s, 40 µm — 34 droplets, settles `c1−c3` and the noise |

All written by the corrected `extract_droplet_dye.py` (masked integral,
satellite filter), so `V_nL` and the `c_i` are wet-cell quantities and are
**not** comparable to CSVs produced before this date. The multiphase CSV has no
`alpha.water` column upstream — its `c_i` come from the three water phases
directly.

## Status of the encoder case after this work

| | |
|---|---|
| `scalarTransport` function objects | ✅ verified working on ESI 2306 |
| Droplet physics in this geometry | ✅ unchanged, still verified |
| Startup cut / pinch-off extrapolation | ✅ fixed |
| Composition integral | ✅ fixed (masked), halo-independent in both solvers |
| **Passive-scalar dye field** | ❌ **unusable** — ~20% floor, no convergence |
| Symmetry control, passive scalars | ❌ fails at −0.098 once measured correctly |
| Core-vs-wall, passive scalars | ❌ does not converge; changes sign with `dx` |
| Dyes on the water flux | ❌ tested — accepted by the FO, but worse |
| **`multiphaseInterFoam` formation** | ✅ **drips** — 1240 µm, 160 ms, matches `interFoam` |
| **`multiphaseInterFoam` conservation** | ✅ phase-sum 1.000000; 0.028% in pure oil |
| **`multiphaseInterFoam` fidelity** | ✅ **2D null passes** — core-vs-wall +0.0065 (0.47σ) |
| Per-droplet noise, multiphase | ⚠️ ~10× the passive-scalar figure — 3D needs n ≈ 34 |
| **`c1−c3` asymmetry** | ❗ **real** — −0.035 at 3σ over n=34, stationary. The validity gate is wrong, not the run |
| Core-vs-wall vs the asymmetry | ✅ immune by construction (averages c1,c3) — null holds at 0.9σ |
| Satellite droplets | ⚠️ filtered (`--min-length-um`); physical-vs-`cAlpha` artifact open |
| Core-vs-wall slow drift | ✅ **not real** — white noise + one coalescence droplet; within-scatter filter added |
| **3D run** | ⚠️ unblocked in principle (readout works); gate must be removed first, and 3D needs n≈34 |
