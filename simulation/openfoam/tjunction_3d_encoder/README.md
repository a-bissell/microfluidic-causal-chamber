# tjunction_3d_encoder — does the T-junction write the code faithfully?

Digital twin of an **encoded-droplet** chip: three dye streams merge upstream
of the T-junction, and the composition of each droplet is a *symbol*. This
case exists to test one claim, in 3D, because 2D cannot answer it.

---

## The claim, and the hole in it

The encoder sets a droplet's code by flow ratio:

> A droplet's integrated dye content equals the commanded flow fraction,
> `c_i = Q_i / ΣQ`.

The argument is mass conservation. The slug consumes the full channel
cross-section, so it captures each stream in proportion to its flux —
**whether or not the streams have mixed**. That is what makes the scheme
cheap: no on-chip mixer is needed, and the bench version can be read as
integrated absorbance with a colour camera, since `∫ −log(I/I₀) dA = ε c V`
is independent of path length and droplet shape.

The hole is three-dimensional. If the continuous phase intrudes at the
**corners** of the water leg near the junction, the slug does *not* sample the
full cross-section — it preferentially samples the core. The three laminae do
not sit symmetrically in that cross-section, so core-preferential sampling
biases the code.

This is not hypothetical. [`results/mill3d800_2026-08`](../results/mill3d800_2026-08/)
found exactly this geometry: minimum cell-centre `alpha` of **0.75 across x and
0.83 across z** in the water leg, with the note that *"the interface that does
appear in the leg is corner intrusion near the junction."* That same run
measured a slug-bypass ratio of 1.307 in 3D against 1.118 in 2D (textbook
~1.33 for square channels) — the corners are load-bearing, and **a 2D mesh has
none**.

---

## Geometry: a cross-merge, and why

```
                       dye2  (axial → centre lamina)
                         │
                         ▼
     dye1 ──────────►  ──┼──  ◄────────── dye3
                         │
                         │  shared water leg (--l-leg, default 1200 µm)
                         ▼
     oil ═══════════[ T-junction ]═══════════►  coded droplets
```

`dye1` and `dye3` enter from opposite sides at the same station; `dye2` enters
axially. Downstream, the leg carries three laminae across its width with
`dye2` in the middle.

Two reasons for this shape rather than a Y or a comb:

1. **Orthogonal**, so blockMesh needs no angled blocks, and it mills in the
   same single-endmill workflow as the rest of the chip.
2. **`dye1` and `dye3` are mirror images** — same leg length, same resistance,
   same wall proximity. That is a free control, and it is what makes the
   experiment interpretable (below).

---

## The experimental design

Run at the symmetric point `c = (⅓, ⅓, ⅓)`. Then two independent signatures
separate artifact from physics:

| Observation | Meaning |
|---|---|
| `c1 ≠ c3` | **Artifact.** The legs are mirror images; geometry guarantees equality. Suspect mesh, decomposition, or BCs. Invalidates the run. |
| `c1 = c3` but `c2 > (c1+c3)/2` | **Real sampling bias.** The core lamina is over-sampled. This is the corner-gutter effect on the encoder. |

> ❗ **The first row is wrong — confirmed by measurement.** A 6.5 s multiphase
> 2D run (n = 34) gives `c1 − c3 = −0.035` at ~3σ, stationary across the run.
> The legs are mirror images in *plan*, but oil crosses the junction in one
> direction: `dye1` (upstream arm, facing the oncoming oil) is stripped more
> than `dye3` (downstream, in the slug's lee), so `dye1 < dye3` systematically
> (0.318 vs 0.354). `c1 = c3` is **not** geometrically guaranteed, so a nonzero
> `c1 − c3` does not invalidate a run — this row's diagnostic is retired.
>
> The second row survives intact: core-vs-wall averages c1 and c3, so it is
> immune to this asymmetry by construction, and it holds the 2D null at 0.9σ
> (−0.008). **The gate was unnecessary for the quantity it guarded.** See
> [`results/encoder_dye_2026-08`](../results/encoder_dye_2026-08/).

The second combination cannot be produced by leg asymmetry — which is what
makes it diagnostic rather than suggestive, and which the measurement now
*confirms* rather than assumes: the leg asymmetry is real (`c1 − c3 = −0.035`),
yet core-vs-wall stays at zero in 2D (−0.008, 0.9σ) because averaging c1 and c3
cancels it. In 2D core-vs-wall must be ~0, because there are no corners.
**The difference between the matched 2D and 3D runs is the result** — and it is
carried entirely by core-vs-wall, not by `c1 − c3`, which is now known to be a
2D property of the geometry rather than a run-quality signal.

This is why the case ships a `--two-d` flag rather than a separate 2D case:
one generator, one flag, so dimensionality is the only thing that differs.
Same discipline that
[`results/mill3d800_2026-08`](../results/mill3d800_2026-08/) had to impose
after its predecessor was found to have varied dimensionality *and* actuation
mode together.

### Actuation: velocity inlets, deliberately

The encoder has two distinct error mechanisms, and mixing them would waste the
3D compute:

- **Sampling fidelity** — does the junction chop the laminated stream without
  bias? Hydrodynamic, needs 3D, isolated by *pinning* the flow rates.
- **Hydraulic crosstalk** — under pressure actuation the three legs couple
  through the shared merge node, so commanding `P_i` does not deliver the
  intended `Q_i`.

This case uses velocity inlets, so `Q_i` are exogenous and crosstalk is **zero
by construction**. What remains is sampling fidelity alone. Crosstalk is a
separate, much cheaper experiment — see the bottom of this file.

### Dyes are passive scalars — after trying the better idea and measuring it fail

The physically nicer design is `multiphaseInterFoam` with four phases
(`water1/2/3` + `oil`). Each `alpha.water_i` is then MULES-advected, conserved
and bounded, so `Σ alpha.water_i` is an identity the solver *enforces* rather
than a diagnostic to be checked, and composition carries no numerical leakage
at all. That was built first, for exactly that reason.

**It does not form droplets** — ❌ **this was wrong, see the banner at the top
and [`results/encoder_dye_2026-08`](../results/encoder_dye_2026-08/).** The
three runs below were read as settling it:

| Geometry | Solver | Result |
|---|---|---|
| verified `tjunction_3d_mill` | `interFoam` | drips, L = 1400 µm |
| **this case** | `interFoam` | **drips, L = 1240 µm** |
| this case | `multiphaseInterFoam` | ~~no pinch-off~~ **drips, L = 1240 µm, T = 160 ms** |

The third row was measured again on the restored case, unmodified: pinch-off at
**205 ms**, then every 160 ms. The growth quoted below — thread past 2.5 mm at
~27 mm/s — is real and reproduces exactly (26.4 mm/s between t = 0.15 and 0.20),
but it is what the thread does *before* it necks, not evidence that it never
does. Everything in the rest of this section follows from a premise that no
longer holds.

The middle row is the important one: this exact mesh, these exact velocity BCs
and this exact contact angle reproduce the verified 800 µm 2D slug length of
**1240 µm** from [`results/scaleup_2026-07`](../results/scaleup_2026-07/) on
the nose. The merge geometry is sound and the operating point is right — the
solver is what differs. Under `multiphaseInterFoam` the thread stays attached
past 2.5 mm and keeps growing at ~27 mm/s instead of necking.

The surface-tension force does appear to sum correctly across the three
water–oil pairs (at a ⅓-⅓-⅓ interface each pair contributes a third of the
two-phase value, totalling the same `1/δ` — checked analytically, not
assumed). More likely causes are the per-pair curvature estimate, built from
an alpha field that only ever spans 0 to ⅓ and is correspondingly noisier, and
interface compression acting between water phases that have no physical
interface. Not chased further: **a working two-phase route is worth more than
a conservation guarantee on a solver that will not drip.**

> ❌ That trade was made against a solver that *does* drip, so it was never the
> trade it looked like. The conservation guarantee was available all along, and
> the two-phase route bought a ~20% measurement floor in exchange for nothing.
> The per-pair curvature suspicion in the paragraph above is also unnecessary
> to resolve — whatever its status, the slugs form on time and at the right
> length. The one defect that survives scrutiny is `cAlpha`: it is a single
> global value applied between *every* phase pair, including the three
> water–water pairs that have no physical interface. Real, but not blocking —
> `cAlpha 0` and `cAlpha 1` both drip.

**The cost of coming back.** A passive scalar gets no MULES compression, so it
is neither conserved nor bounded, and it leaks across the interface because
`phi` is the *mixture* flux. Uniform leakage cancels in a composition ratio
and is harmless; differential leakage between laminae at different distances
from the interface does not, and is confounded with the sampling bias this
case measures. Two things bound it, and both must be used:

1. `Σ dye_i == alpha.water` is an identity by construction but is *not*
   numerically enforced, so its violation is a free per-droplet error measure.
   `analyze_encoder.py` reports it and **refuses to interpret a bias smaller
   than the leakage**.
2. Numerical leakage scales with `dx`; a physical bias does not. **A bias seen
   at one resolution is not a result** — see the `--dx 20` run in the plan.

The three dye streams are the same fluid and differ only in provenance, so the
encoder **cannot perturb its own hydrodynamics**: writing a different symbol
changes nothing the momentum equation can see.

---

## Requirements

`interFoam` (ESI) or `foamRun` + `solver incompressibleVoF` (OpenFOAM.org
11+). `Allrun` detects which is present, so this case runs on both, like the
rest of this directory.

**One caveat on function objects — now resolved.** The three dye scalars are
`scalarTransport` function objects. The Ubuntu 24.04 OpenFOAM package
(`1912.200626-2build3`) aborts on *any* function object with
`error in IOstream "sha1"` — a GCC-13 rebuild bug in `OSHA1stream`, unrelated
to this case. **Under `opencfd/openfoam-default:2306` they load and advect
correctly**, with the `libs` lines exactly as written; `check_dye_transport.py`
passes all three tests. Use the ESI image and this is a non-issue. The two-phase droplet physics beneath
them **is** verified in this exact mesh (1240 µm slug, above). `Allrun` greps
`log.solver` for function-object errors and warns, because a run whose FOs
failed still completes and still makes droplets — it just silently carries no
code, and you would not find out until the extractor errors out much later.

---

## One pitfall, already hit

**Wall wetting is load-bearing.** The first version of this generator emitted
`zeroGradient` for `alpha` on walls — neutral wetting, 90°. The case meshed
cleanly, ran cleanly, conserved phase to machine precision, and **produced no
droplets at all**: water entered at the top of the channel and rode the wall as
a jet out to 2.9 mm without ever blocking the junction, so the oil never had to
squeeze it. Nothing looked wrong; the answer simply never appeared.

The two-phase cases here carry `theta0 = 160°` with a comment recording the
same lesson — *"160 deg keeps the water thread off the walls so it can neck
and pinch off (120 deg let water spread as a stable wall film)"*.

The generator now emits `constantAlphaContactAngle` with `theta0 160`,
byte-identical to those cases.

If a run produces a long attached jet instead of droplets, check this first.

---

## Run plan

Ordered by information per CPU-hour. **Run 1 and 2 are the experiment**; 3 and
4 defend it.

### 0. Dye-transport pre-flight — 2 minutes, do this first

The three dye scalars are `scalarTransport` function objects, and they have
never been run anywhere: the build used for local verification aborts on *any*
function object (see Requirements). Everything else about this case is
verified; this is the one open link, and it is cheap to close.

```bash
cd tjunction_3d_encoder
python3 gen_blockmesh.py --w-main 800 --two-d

# short run: 0.02 s is plenty, no droplets needed
sed -i.bak 's/^endTime         0.8;/endTime         0.02;/' system/controlDict
./Allrun 4
python3 ../scripts/check_dye_transport.py .
mv system/controlDict.bak system/controlDict     # restore
```

`check_dye_transport.py` tests three things, and the middle one is the reason
it exists:

1. the dye fields are present in the output;
2. **they have changed since t=0** — a field that is registered and written
   but never advected is the silent failure. The run completes, makes good
   droplets, and reports compositions exactly equal to the seeded values,
   which looks like a plausible result;
3. `Σ dye_i == alpha.water` over wet cells — the leakage number that later
   bounds how much of any measured bias could be numerical.

**If it fails with "Unknown function type scalarTransport" or a library load
error**, it is the `libs` entry in `system/controlDict`, not the case. The
`("libsolverFunctionObjects.so")` spelling is ESI. Try deleting the three
`libs` lines entirely first — most builds resolve the type without them. If
your build genuinely lacks the function object, an ESI image (v2306) is the
fallback, and everything else in this case is version-agnostic.

### 1. Matched 2D baseline — the null

```bash
cd tjunction_3d_encoder
python3 gen_blockmesh.py --w-main 800 --two-d
./Allrun 4
python3 ../scripts/extract_droplet_dye.py .
python3 ../scripts/analyze_encoder.py .
```

**Expect:** `c1 = c2 = c3 = ⅓` to within scatter, and core-vs-wall bias ~0.
2D has no corners, so a nonzero bias here means a bug — most likely in the
extractor's window or the seeding, not in the physics. **Do not proceed to the
3D run until this is clean**; it costs 40 minutes and it is the only thing
standing between you and misreading a 6-hour result.

### 2. The 3D run — the experiment

```bash
python3 gen_blockmesh.py --w-main 800
./Allrun 4        # raise to your core count; edit decomposeParDict to match
python3 ../scripts/extract_droplet_dye.py .
python3 ../scripts/analyze_encoder.py . --compare-with ../<2d-case-dir>
```

**Copy the 2D case directory aside before this step.** `gen_blockmesh.py`
writes to fixed paths, so generating the 3D mesh overwrites `0/`,
`system/blockMeshDict`, `system/setFieldsDict` *and `geometry.json`* — the 2D
run's manifest included. Pairing a 3D manifest with 2D output is a mistake
that costs hours, because the commanded composition and outlet window still
look sane and the analysis runs without complaint while reporting wrong
volumes under a wrong dimensionality label. `extract_droplet_dye.py` now
cross-checks the manifest's cell count against the VTK and refuses to run on a
mismatch (68,000 vs 6,800 at the defaults), but copying the directory is the
habit that avoids the situation entirely.

`--compare-with` then prints the dimensionality difference directly, which is
the headline number.

### 3. Mesh-convergence confirmation — *required before reporting a bias*

```bash
python3 gen_blockmesh.py --w-main 800 --dx 20
# tighten maxDeltaT to ~5e-6 in system/controlDict — the capillary limit
# goes as dx^1.5, and 1.5e-5 is unsafe at 20 µm
```

Any residual numerical leakage scales with `dx`; a physical sampling bias does
not. **A bias measured at one resolution is not a result.** This run is 8× the
cells and is the expensive one — only worth it if run 2 shows a nonzero bias.

### 4. Asymmetric code — linearity

```bash
python3 gen_blockmesh.py --w-main 800 --c 0.5 0.25 0.25
```

Tests whether the bias is a fixed offset or scales with composition. Determines
whether a bench calibration needs one number or a matrix.

### Cost

| Run | Cells | Wall time, 4 cores | Notes |
|---|---|---|---|
| 2D baseline | 6,800 | **~50 min** | measured 3,800 s per simulated second at `maxDeltaT 1e-5` |
| 3D | 68,000 | ~8 h (extrapolated ×10 on cells) | ~2–2.5 h at 16 ranks |
| 3D, `--dx 20` | 544,000 | ~2–3 days | only if run 2 shows a bias, and needs `maxDeltaT 5e-6` |

Cell-count scaling is the honest bound but slightly pessimistic — the pressure
solve does not scale quite linearly. Treat the 3D figure as an upper estimate.

### Yield — read this before choosing `endTime`

`endTime` is 0.8 s, longer than the other cases here, and that is not padding.
Water takes **~207 ms** to travel from the merge node to the junction at the
default leg length. Droplets formed before then carry the *seeded* composition
from `setFields`, not one the encoder wrote.

That cut is not squeamishness — it is necessary for a specific reason. The
seeded water is *uniformly mixed*, whereas inlet-derived water is *laminated*,
and uniformly-mixed water **cannot exhibit a lamination bias by construction**.
Including those droplets would not just be trivially favourable, it would
actively dilute the effect being measured.

Usable yield is therefore `(endTime − t_transit) / droplet_period`:

| | period | yield at `endTime` 0.8 s | at 1.2 s |
|---|---|---|---|
| 2D | 175 ms | **~3 droplets** | ~6 |
| 3D | 110 ms | **~5 droplets** | ~9 |

**This matters differently for the two headline numbers.** The core-vs-wall
bias is a statement about the *mean*, and ~5 droplets supports it adequately
provided within-droplet scatter is small. The channel-capacity figure is a
statement about the *between-droplet SD*, and ~5 droplets does not support it
— an SD from n=5 carries roughly a 35% standard error of its own.
`analyze_encoder.py` refuses to present the capacity as a result below n=8 and
says so explicitly.

So: **0.8 s is enough to measure the bias, not enough to measure the
capacity.** If you want both from one run, use `endTime 1.2` and accept ~9 h
on 4 cores.

Two cheaper ways to raise yield, in preference order:

1. **Shorten `--l-leg`.** Under velocity inlets this is nearly free — the leg
   length exists to decouple junction pressure from the merge node, and that
   coupling is already zero here because the flow rates are pinned. The leg
   only needs to be long enough for the laminae to establish, roughly one
   channel width. `--l-leg 800` cuts transit to ~138 ms and buys ~0.6
   droplets per 0.1 s of run. **Do not do this for the pressure-driven
   crosstalk variant**, where the leg length is hydraulically load-bearing.
2. Raise `endTime`. Linear in cost, no side effects.

---

## Reading the output

`analyze_encoder.py` prints four sections, and they are ordered so the run
validates itself before it makes a claim:

1. **Fidelity** — realized vs commanded composition, with between-droplet and
   within-droplet scatter reported separately. A droplet is seen in many
   frames, so within-droplet spread is *measurement* noise and between-droplet
   spread is *real per-symbol* noise. Only the second limits the channel;
   pooling them would understate the encoder.
2. **Symmetry control** — gates everything after it.
3. **Core-vs-wall bias** — the 3D signature.
4. **Channel estimate** — bits per droplet, flagged inline as a scaling
   argument (it ignores simplex boundaries, inter-dye noise correlation, and
   decoding).

The extractor also reports **dye-closure error**: per droplet, the sum of the
three dye integrals against the `alpha.water` integral. These are equal by
construction but not numerically enforced, so the mismatch *is* the passive
scalars' leakage. It is not decoration — it bounds how much of the measured
bias could be numerical, and `analyze_encoder.py` refuses to interpret a
core-vs-wall bias smaller than it.

---

## What this case cannot answer

- **Hydraulic crosstalk.** Zero here by construction (velocity inlets). Under
  pressure actuation the legs couple through the merge node, and a
  lumped-element model predicts a *dilation of the code simplex*: raising oil
  pressure pushes `c` away from the conductance-weighted barycentre
  `c*ᵢ = Gᵢ/ΣGⱼ`, with `dcᵢ/dP_J ∝ (cᵢ − c*ᵢ)`, so crosstalk is exactly zero at
  the simplex centre and grows toward the corners. That is a **2D experiment**
  — swap the inlet BCs to `totalPressure` and sweep. Cheap, and it does not
  need this case's 3D cost. Not yet built.
- **Wall wetting and adsorption.** Dye sticking to PMMA and 468MP is the
  dominant *bench* drift mechanism and has no analogue here — the walls are
  ideal.
- **Full-depth asymmetry.** Half-depth symmetry assumes floor and lid wet
  identically; the real chip is milled PMMA against adhesive. Same caveat as
  `mill3d800_2026-08`, unresolved by either.
- **Anything about the pressure-driven chamber's causal graph.** Velocity
  inlets sever the emergent-flow edges. See
  [`results/cyclicity_2026-07`](../results/cyclicity_2026-07/).

---

## Status

| | |
|---|---|
| Mesh generation, 2D and 3D | ✅ `checkMesh` clean, all 5 inlet patches correct (200 faces each in 3D) |
| Wall contact angle | ✅ corrected after a run jetted instead of dripping (pitfall above) |
| **Droplet formation in this geometry** | ✅ **verified against `scaleup_2026-07` on all four observables — see table below** |
| Solver choice | ❌ **reopened** — `multiphaseInterFoam` drips after all (1240 µm, 160 ms); the revert rested on a false negative |
| `analyze_encoder.py` statistics | ✅ validated against synthetic data with known injected bias and noise |
| Dye `scalarTransport` function objects | ✅ **verified working** on ESI 2306 — [`encoder_dye_2026-08`](../results/encoder_dye_2026-08/) |
| Startup cut and pinch-off extrapolation | ✅ fixed — the old cut was 2.5× too short |
| Composition integral | ✅ masked, halo-independent in both solvers |
| Passive-scalar dye field | ❌ **unusable** — ~20% floor, core-vs-wall changes sign with `dx` |
| **Composition readout, multiphase** | ✅ **2D null passes** — core-vs-wall +0.0065 (0.47σ), closure exact |
| Symmetry control (`c1 = c3`) | ❗ **retired** — real leg asymmetry −0.035 at 3σ (n=34); the gate was wrong, not the runs |
| Per-droplet noise, multiphase | ⚠️ ~10× the passive figure — 3D bias run needs n ≈ 34 |
| **3D run** | ✅ **done (n=23): core-vs-wall −0.007 ± 0.009, consistent with zero — no significant corner bias** |

The droplet physics, the geometry and the operating point are verified and
unaffected. The passive-scalar *readout* failed — the three dyes are advected
on the mixture flux with no coupling to `alpha`, so nothing enforces
`Σ dye_i == alpha.water`, about a fifth of the dye ends up in the oil, and the
measurement floor is ~20% against a ~2% effect. **`multiphaseInterFoam` fixes
this at the source** — each phase is MULES-conserved, closure is exact, and the
2D null passes (core-vs-wall +0.0065, 0.47σ). That is the correct route, and
it needs no method rewrite: the solver was wrongly ruled out (see the banner).
Routes that don't work — advecting on the water flux — and the one remaining
untested fallback (`dye_i/alpha`) are laid out in
[`results/encoder_dye_2026-08`](../results/encoder_dye_2026-08/).

### Verification against the chamber

A 0.40 s run of this exact mesh with `interFoam` (no dye transport — the
droplet physics alone), against the verified 800 µm 2D numbers in
[`results/scaleup_2026-07`](../results/scaleup_2026-07/):

| Observable | `scaleup_2026-07` | this geometry | Δ |
|---|---|---|---|
| Slug length | 1240 µm | 1265, 1283 µm | +2.7% |
| Period | 175 ms | 170 ms | −2.9% |
| Droplet rate | 5.71 Hz | 5.88 Hz | +3.0% |
| Advection speed | 28.46 mm/s | 30.7, 32.6 mm/s | +8% |

All inside the ±10% band this project uses elsewhere, and well inside the
3–19% spread the mesh-convergence study found. **The cross-merge does not
disturb the junction**: adding three inlets and a merge node 1.2 mm upstream
leaves the chamber's droplet behaviour intact, which is the premise the whole
encoder rests on.

Two caveats on those numbers. The period is a **single** interval between two
droplets, not a statistic — the run was sized to answer "does it drip", not to
average. And both droplets formed before the 207 ms transit, so they carry
seeded water; that is irrelevant here (this checks formation, not composition)
but it is why this run cannot double as a fidelity measurement.

**Acceptance test for step 1** is therefore now half-satisfied: the physics is
confirmed. What remains is that the dye fields are actually present in the VTK
output, with a dye-closure error small enough to interpret a bias against.
