# Wetting and interfacial tension: the two unmeasured assumptions — 2026-08

**Status: study A complete. Studies B, C and the 3D spot-check are running;
this file will grow.**

## Why

Every geometric and hydraulic claim in this repo has been measured. The two
numbers underneath them had not been:

| | Where | What it says | Provenance |
|---|---|---|---|
| `sigma` | `constant/transportProperties` | 0.03 N/m | comment reads *"with 2% Span 80 … typical value 0.02–0.04"*. No citation. 0.03–0.04 is roughly the **bare** water/silicone-oil value, an odd place to land for a 2 wt% surfactant load well above CMC. |
| `theta0` | `0/alpha.water` | 160° | the file's own comment records that 120° *"let water spread as a stable wall film"*. **The value was selected because it dripped.** |

That second one had hardened into a claim. `simulation/openfoam/README.md`
carries it as a general troubleshooting rule (*"walls must be strongly
oil-wet — theta0 ≥ 150"*), and the plan's risk register marks
droplet-formation risk down from Medium to **Low** on the grounds that
contact angle is *"now verified in OpenFOAM, not just from literature."*
The simulation verified that 160° drips. It did not verify that a
Span-80-flooded PMMA/468MP channel *is* at 160°. Those are different
statements, and only the first one was ever tested.

Why sigma is the larger risk. Combining the viscous pressure drop
ΔP ~ μUL/w² with the definition of the capillary number U = Ca·σ/μ, the
viscosity cancels:

    ΔP  ~  Ca · σ · L / w²

**Drive pressure — the column height a builder sets on the bench — is
directly proportional to interfacial tension.** The capillary entry
threshold 2σ/w scales identically. So a factor-of-5 error in σ is not a
correction to the operating point; it moves the operating point bodily,
or leaves Ca 5× off and the chip jetting instead of squeezing.

## Study A — contact angle, 120° to 170°

Six 2D cases on the 800 µm chip, σ = 30 mN/m, drive fixed at the designed
980/490 Pa (10.0/5.0 cm H₂O). Pressure-driven, so flow rate is free to
respond to wall friction. `A_theta_results.csv`, `A_theta.png`.

| θ₀ | regime | L/w | rate (Hz) | slug speed |
|---|---|---|---|---|
| 120° | plugs | 1.550 | 5.48 | 24.95 mm/s |
| 130° | plugs | 1.500 | 5.48 | 26.04 |
| 140° | plugs | 1.550 | 5.56 | 27.64 |
| 150° | plugs | 1.550 | 5.71 | 28.24 |
| 160° | plugs | 1.550 | 5.63 | 28.64 |
| 170° | plugs | 1.450 | 5.88 | 28.15 |

**All six form plugs.** The troubleshooting rule does not reproduce at
800 µm: 120° drips, and is indistinguishable from 160° in slug length.

Every measured `L_um` is an exact multiple of 40 µm — the cell size — so
the extractor quantises length to one cell and the apparent 3.4% spread in
L/w *is* that one cell. **L/w is flat to the resolution of the
measurement.** Do not read the 1.45 at 170° as a trend.

Speed is the real signal. It is a ratio of differences rather than a
quantised extent, and it climbs monotonically **+15% from 120° to 160°**
before flattening. Physically sensible: a less oil-wet wall drags on the
water more, and under a *pressure* boundary condition that drag is free to
reduce the flow rate. So θ is not inert — it just does not control whether
droplets form.

Regression check: the θ = 160° cell reproduces `scaleup_2026-07`'s 800 µm
reference (L/w 1.550, 28.46 mm/s, 5.71 Hz) to **1.1% on speed and exactly
on L/w**, through a rebuilt mesh and a rewritten extraction path.

### What this does not settle

**In 2D, `frontAndBack` is `empty`, so `theta0` acts on only two of the
four walls.** The floor and ceiling carry no contact-angle condition at
all. In the real chip those two surfaces are the milled PMMA floor and the
**3M 468MP adhesive ceiling** — a much more polar surface, and the one most
likely to be water-wet.

A 2D sweep is therefore structurally biased toward finding θ unimportant:
half the wetted perimeter is missing from the model. Study A bounds the
problem; it does not close it. The 3D spot-check (θ = 120 vs 160 on the
44,000-cell half-depth mesh, where floor and ceiling are real walls) is the
test that carries weight, and it is running.

Even that leaves one gap: the 3D case's symmetry plane forces the ceiling
to share the floor's contact angle, so it still cannot test an oil-wet PMMA
floor against a water-wet adhesive ceiling. That asymmetry needs a
full-depth mesh with split wall patches, and remains unbuilt.

## A bug worth knowing about, since it affects what you can trust

`tjunction_2d_mill/gen_blockmesh.py` accepted `--w-main` but never emitted
`system/setFieldsDict`; the checked-in dict was frozen at 400 µm literals.
At 800 µm its boxes would have seeded water **inside the main channel**,
and `setFields` would have exited 0. Fixed here — the dict is now generated
alongside the mesh, covering both the water leg and the 27 mm resistor
channel (which must start water-filled, or the run is spent pushing oil out
of it). Verified: `blockMeshDict` is byte-identical at the 400 µm default,
and 800 µm gives 6,440 cells, matching `scaleup_2026-07`.

Separately, `extract_mature_droplets.process()` returned a bare dict on the
empty case but a `(summary, tracks)` tuple otherwise. Callers unpack two
values, so the dict unpacked into its two *keys* as strings and died several
lines later pointing at the wrong thing. Never triggered before because
every case in every prior sweep formed droplets; a wetting sweep is built to
produce cases that do not.

## Running

| Study | Varies | Drive | Purpose |
|---|---|---|---|
| A2 | θ = 60/75/90/105° | fixed 980/490 Pa | study A found no boundary down to 120°; PMMA under water in air is ~70°, so the edge is being hunted below |
| B | σ = 5–40 mN/m | fixed 980/490 Pa | calibration curve: what you see on the bench, and what σ it implies |
| C | σ = 5–40 mN/m | scaled ∝ σ | does retuning the head to P ∝ σ recover the design point? |
| D | θ = 120 vs 160 | velocity-driven, 3D | the test that closes the 2D wall gap |

Note D is **velocity-driven** — the 3D case has no feed resistors, so a
pressure BC has nothing to drop across. That closes the flow-rate channel
by which θ acted in study A, so its speeds are *not* comparable with the
table above. L/w and whether droplets form are what transfer.

## Reproducing

    bash ../../scripts/run_wetting_studies.sh ~/sweeps/wetting 8
    bash ../../scripts/run_phase2.sh

    python3 ../../scripts/analyze_fluid_sweep.py ~/sweeps/wetting/A_theta \
        --mode theta --out-dir .

Raw output is off-repo (~12 GB). `maxDeltaT` is deliberately left at the
case's 5e-6 s for every case rather than rescaled per σ: the capillary
timestep limit goes as 1/√σ, so the cap only gets safer as σ falls, and
holding it fixed keeps the sweep free of a timestep confound and its
nominal cell directly comparable to `scaleup_2026-07`.

**Scheduling note.** The 3D case is MPI and synchronises every timestep, so
one descheduled rank stalls all of them. Measured **~24 h/case** sharing 10
cores with nine serial 2D solvers, against **~1.85 h** uncontended — a 12×
penalty that the embarrassingly-parallel 2D cases do not suffer at all.
Sequence MPI work; do not overlap it with a full sweep.
