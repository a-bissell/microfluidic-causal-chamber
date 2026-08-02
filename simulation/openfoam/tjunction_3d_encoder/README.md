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

Keep the 2D case directory (copy it aside) — `--compare-with` prints the
dimensionality difference directly, which is the headline number.

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
| 2D baseline | 6,800 | **~37 min** (measured) | 2,750 s per simulated second |
| 3D | 68,000 | ~6 h (extrapolated ×10) | ~1.5–2 h at 16 ranks |
| 3D, dx=20 µm | 544,000 | ~2–3 days | only if run 2 shows a bias |

`endTime` is 0.8 s, longer than the other cases here, and that is not
padding: water takes **~207 ms** to travel from the merge node to the junction
at the default leg length. Droplets formed before then carry the *seeded*
composition from `setFields`, not one the encoder wrote — they would agree with
the commanded value for a trivial reason. `analyze_encoder.py` discards them,
which leaves ~5 measurable droplets from a 0.8 s run. Shortening `endTime`
without shortening `--l-leg` will leave you with nothing to measure.

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
| `multiphaseInterFoam` runs the case | ✅ verified (short solve, OpenFOAM v1912) |
| Full 0.8 s 2D reference run | ⏳ see run plan step 1 |
| 3D run | ⏳ not yet run |
| `extract_droplet_dye.py` / `analyze_encoder.py` on real droplet data | ⏳ not yet exercised end-to-end |

The scripts are written against the field names and geometry manifest this
case emits, but until step 1 completes they have not been run on a VTK tree
containing actual droplets. Expect to fix something small on first use.
