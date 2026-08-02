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

The second combination cannot be produced by leg asymmetry — which is what
makes it diagnostic rather than suggestive. And in 2D it must be ~0, because
there are no corners. **The difference between the matched 2D and 3D runs is
the result.**

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

### Dyes are phases, not passive scalars

The obvious implementation is `interFoam` plus three `scalarTransport`
function objects. **That was tried first and rejected on physics.** A passive
scalar gets no MULES compression, so it is neither conserved nor bounded, and
it leaks across the oil–water interface because `phi` is the *mixture* flux.

Uniform leakage would cancel in a composition ratio and be harmless.
Differential leakage between dyes does not cancel — and differential leakage
is exactly what you'd expect, since the three laminae sit at different
distances from the interface. It is therefore **confounded with the physical
effect being measured**, unrecoverably.

`multiphaseInterFoam` with four phases (`water1/2/3` + `oil`) removes the
confound at the source: every `alpha.water_i` is MULES-advected, conserved and
bounded, so `Σ alpha.water_i` is an identity the solver enforces rather than a
diagnostic to be checked. Cost is ~1.3–1.5× `interFoam` (the pressure solve
dominates and is unchanged), which is cheap for removing a confound.

The three water phases are byte-identical in properties and differ only in
provenance — so the encoder **cannot perturb its own hydrodynamics**. Writing
a different symbol changes nothing the momentum equation can see.

---

## Requirements

**An ESI OpenFOAM build** (v1912+ / v2306). OpenFOAM.org has no
`multiphaseInterFoam` equivalent under `foamRun`, so this case will not run
there — unlike the other cases in this directory, which support both.

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

`multiphaseInterFoam` needs a contact angle for **every phase pair**, so the
generator emits the 4-phase generalisation: 160° for each water–oil pair, 90°
for water–water (arbitrary — same fluid, no physical contact line — but the
entry must exist or BC construction fails at run time, after meshing has
already succeeded). Order matters: `theta0` is measured through the *first*
phase of each pair, so `( oil water1 ) 160` would specify water-wet walls and
reproduce the failure.

If a run produces a long attached jet instead of droplets, check this first.

---

## Run plan

Ordered by information per CPU-hour. **Run 1 and 2 are the experiment**; 3 and
4 defend it.

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

The extractor also reports **phase-closure error**. `multiphaseInterFoam`
enforces `Σ alpha = 1`; if the per-droplet closure exceeds ~1e-4, every
composition in the run is suspect and the analysis says so rather than
printing numbers that look fine.

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
| Mesh generation, 2D and 3D | ✅ verified, `checkMesh` clean, all 5 inlet patches correct |
| 4-phase setup, `setFields` seeding | ✅ verified — solver reports phase-sum `1 1 1` |
| `multiphaseInterFoam` runs the case | ✅ verified, OpenFOAM v1912 |
| Wall contact angle | ✅ corrected after a 2D run jetted instead of dripping (see pitfall above) |
| Droplet formation in 2D at these BCs | ❌ **not yet achieved — the gate on everything else.** See below. |
| 3D run | ⏳ not yet run |
| `extract_droplet_dye.py` / `analyze_encoder.py` on real droplets | ⏳ the extractor's droplet-finding and rejection logic has been exercised against a real VTK tree and behaved correctly (it correctly refused a slug still attached to the junction), but no run has yet produced a *detached* droplet for it to measure |

**The acceptance test for step 1** is not just "droplets appear". The 2D case
must reproduce the verified 800 µm 2D numbers from
[`results/scaleup_2026-07`](../results/scaleup_2026-07/) — **slug length
~1240 µm, period ~175 ms** — because that is simultaneously the check on the
new solver (`multiphaseInterFoam` vs `interFoam`), the timestep, and the merge
geometry.

### Open problem: no pinch-off yet

As of this commit the 2D case **has not produced a detached droplet**, and
this is the one thing that must be resolved before any 3D time is spent.

Fixing the contact angle changed the behaviour substantially and in the right
direction — the water went from a thin wall-riding jet (34% of channel height,
running unbroken to 4.9 mm) to a compact body filling 45–65% of the channel
and confined near the junction — but by t = 0.185 s the thread was still
attached, growing at ~27 mm/s, and 2.5 mm long against an expected slug length
of 1.24 mm.

Three candidate causes, in the order worth testing:

1. **OpenFOAM version.** Local verification here used the Ubuntu 24.04 package
   (ESI **v1912**); this project's verified results were produced on **v2306**.
   A control is running: the *unmodified, verified* `tjunction_3d_mill` case at
   `--w-main 800 --two-d` with `interFoam`. If that does not drip either, the
   discrepancy is the OpenFOAM build and not this case — in which case this
   case may well be correct as committed, and the v2306 rig is the place to
   find out.
2. **`multiphaseInterFoam` vs `interFoam`.** The surface-tension force *should*
   sum correctly across the three water–oil pairs — at a 1/3-1/3-1/3 interface
   each pair contributes 1/3 of the two-phase value, totalling the same 1/δ —
   and that was checked analytically, not just assumed. But it is untested in
   this geometry. The isolating run is this case's mesh with `interFoam` and a
   single water phase.
3. **Merge geometry.** Least likely: with velocity-pinned inlets the flux
   reaching the junction is identical to the reference by construction.

Do not start the 3D run until step 1 drips and reproduces ~1240 µm / ~175 ms.
The case, the scripts, and the analysis are ready; this is the remaining gate.
