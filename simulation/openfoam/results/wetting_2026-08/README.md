# Wetting and interfacial tension: the two unmeasured assumptions — 2026-08

**Status: studies A, A2, B and the 3D spot-check (D) complete. Study C is
running; this file will grow.**

**Headline, in one line each.** The wall must be oil-wet by **105–120°**,
not the ≥150° the docs demand — but *neutral* wetting (90°) fails, so the
requirement is real, just 45° lower than advertised. And the chip needs
**σ ≳ 20 mN/m** to make the plugs it was specced for; below ~8 mN/m
nothing detaches at all.

The θ finding is **confirmed in 3D** (study D): at θ = 120° the chip still
forms plugs with all four walls wetting, so it is not a 2D artifact. The σ
numbers are 2D only. Neither can yet test the real asymmetry — an oil-wet
PMMA floor against a possibly water-wet 468MP ceiling — which needs a
full-depth mesh with split wall patches and remains unbuilt.

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
test that carries weight — **see study D below, which ran it and found
θ = 120° still forms plugs.** The 2D result survived.

Even that leaves one gap: the 3D case's symmetry plane forces the ceiling
to share the floor's contact angle, so it still cannot test an oil-wet PMMA
floor against a water-wet adhesive ceiling. That asymmetry needs a
full-depth mesh with split wall patches, and remains unbuilt.

## Study A2 — where the wetting cliff actually is

Study A found no boundary down to 120°, so four more cases went below it:
θ = 60, 75, 90, 105°, same σ and drive. `A2_theta_low_results.csv`.

| θ₀ | 60 | 75 | 90 | 105 | 120 | 130 | 140 | 150 | 160 | 170 |
|---|---|---|---|---|---|---|---|---|---|---|
| | thread | thread | thread | thread | **plugs** | plugs | plugs | plugs | plugs | plugs |

**The cliff is between 105° and 120°.** Every case at or below 105° is a
continuous thread — water enters and never pinches off, the detection
spanning 3960 µm of the 4000 µm outlet in all four.

So the original claim was not imaginary; it was mislocated by about 45°.
The rule in `simulation/openfoam/README.md` — *"walls must be strongly
oil-wet, theta0 ≥ 150"* — asks for roughly 45° more than the physics needs.
But the requirement is real and it is not merely "don't be water-wet":
**neutral wetting (90°) fails too.** The wall has to be meaningfully
oil-wet, just not extremely so.

That matters for the hardware, because plausible PMMA-under-Span-80-oil
values sit in the 120–150° range — *above* the cliff, but not by a wide
margin. 120° works and is also about where the cliff is. This is a
"probably fine, worth measuring" result, not a "stop worrying" one.

## Study B — σ with the drive left at the designed 980/490 Pa

What a builder actually sees if they set the specified 10.0/5.0 cm of water
and σ is not 0.03. `B_sigma_fixedP_results.csv`.

| σ (mN/m) | regime | L/w | speed (mm/s) | rate (Hz) | entry 2σ/w |
|---|---|---|---|---|---|
| 5 | **thread** | — | — | — | 12.5 Pa |
| 8 | marginal | 1.088 | 24.95 | 12.50 | 20 Pa |
| 12 | marginal | 1.075 | 32.22 | 11.11 | 30 Pa |
| 20 | plugs | 1.400 | 29.85 | 7.14 | 50 Pa |
| 30 | plugs | 1.550 | 28.64 | 5.63 | 75 Pa |
| 40 | marginal | 1.550 | 21.19 | 5.00 | 100 Pa |

Three regimes:

- **σ ≥ 20** — proper plugs, L/w 1.4–1.55, regular trains.
- **σ = 8–12** — droplets form and detach, but at L/w ≈ 1.08 they are
  barely plugs at all, sitting on the squeezing/dripping boundary, and
  forming irregularly enough to score `marginal`. Garstecki's
  L/w = 1 + αq, which the design math uses, stops applying here.
- **σ ≤ 5** — nothing detaches.

**Droplet rate is the calibration variable.** It is monotonic across the
whole working range, 12.5 → 5.0 Hz for σ = 8 → 40, a 2.5× span. L/w also
responds but saturates above 20 mN/m. **Speed does not work** — it is
non-monotonic, peaking at σ = 12 — which is most likely noisy speed
estimates in the irregular marginal cases rather than physics.

Two things are unresolved. σ = 40 scores `marginal` at the *top* end on
length spread with only 3 droplets in 0.6 s; that smells like run length
rather than physics, but it has not been shown. And the measured period is
quantised to the 5 ms write interval, so rate resolution is ±5.5% at 11 Hz
and ±2.8% at 5.6 Hz.

**The consequence for the bench.** If 2% Span 80 puts the real interface
anywhere near 5–10 mN/m, this chip at its designed head does not produce
the plugs the repo is calibrated on. The fix is to *lower* the columns in
proportion to σ (ΔP ~ Ca·σ·L/w², so ~2 cm rather than 10 at σ = 6 mN/m) —
which study C is testing. It is emphatically **not** to push harder: a
thread is stabilised, not broken, by more water pressure.

## Study D — the 3D spot-check, θ = 120 vs 160

The test that closes the 2D wall gap: the 44,000-cell half-depth mesh, where
the floor is a real wall and the ceiling its mirror, so `theta0` acts on the
full wetted perimeter. Velocity-driven (this geometry has no feed resistors),
6-way MPI, 5.1 h and 4.9 h respectively. `D_3d_theta_results.csv`.

**Validity check first.** The θ = 160° case reproduces
`mill3d800_2026-08` essentially exactly — L/w 1.350 vs 1.350, slug width
0.950 w vs 0.950 w, 9.0909 Hz vs 9.091 Hz, 33.37 vs 33.50 mm/s (0.4%).
Configuration has not drifted, so θ = 120 vs 160 is a controlled comparison.

| | θ = 120° | θ = 160° | how much to trust it |
|---|---|---|---|
| regime | **plugs** | **plugs** | high — detach 2910 / 2871 µm |
| L / w | 1.30 | 1.35 | one 40 µm cell apart; indistinguishable |
| droplet volume | 422 nL | 407 nL | 4%, near resolution |
| slug speed | 27.00 mm/s | 33.37 mm/s | 19% — many frames, real |
| water touching y-walls | 26.2 nL (6%) | 6.0 nL (1%) | **4.4×** — real |
| droplet rate | 6.90 Hz | 9.09 Hz | only 3–4 gaps — weak |

**θ = 120° forms plugs in 3D.** The 2D result survives the test designed to
break it, so `theta0 ≥ 150` is not merely a 2D artifact — it is wrong.

θ is not inert, though. It wets **4.4× more wall**, which is the mechanism
the original claim was reaching for: present, measurable, and nowhere near
runaway. Enough to add drag and slow the slugs 19%; nothing like a film.

### Two mechanisms proposed and killed by measurement

Worth recording, because both were plausible and both were wrong:

1. **Depth occupancy.** The tracking extractor sees only x and y, so a
   droplet could be deeper at θ = 120 and hold more water per unit length.
   Killed by measuring z directly with `measure_3d_droplet_volume.py`:
   **720 µm (0.90 w) in both.** Depth is not the variable.
2. **Corner-gutter bypass.** A square channel leaves oil-filled corners the
   slug slides past, and θ should govern how much cross-section the water
   claims. *Not* cleanly killed, but the sign is wrong for the simple
   argument. Restricted to fully-formed mid-channel droplets, θ = 120 is
   **narrower** — 680 µm (0.85 w) against 760 µm (0.95 w) — so it leaves
   *more* room in the gutters, yet it travels **slower**. More bypass area
   with less bypass speed is the opposite of what the mechanism predicts.

   Note this disagrees with the tracking extractor, which reports 0.95 w for
   both. That figure includes still-forming droplets at the junction, which
   span the full width and wash out the difference; the windowed direct
   measurement is the one to trust. The gap is 2 cells, so it is resolvable
   but not comfortably.

**No mechanism is claimed for the speed difference.** Three candidate
explanations have now been proposed and measured; two are dead and the third
points the wrong way.

A third reading — that 20% of the injected water was vanishing into a film,
inferred from V × f falling short of the imposed Q — also did not survive.
Essentially all water in the outlet is in discrete droplets (441.9 of
441.9 nL at θ = 120). The shortfall was droplet-count granularity across a
4-to-5-droplet run, not missing water.

**What would settle the rate difference:** a longer run. At 0.6 s this case
yields 4–5 droplets and therefore 3–4 inter-droplet gaps, which is too few
to separate a real 24% frequency shift from sampling. The speed and
wall-contact numbers do not depend on that and stand on their own.

## Classifier: a thread can masquerade as a plug

The first pass of `analyze_fluid_sweep.py` tested for `thread` only when a
case produced **zero** complete droplet tracks. That is not sufficient. A
continuous thread satisfies every maturity test the extractor applies — its
length plateaus, because it is pinned at the channel length, and its
centroid advances — so it arrives at the classifier looking like a very
long, very regular plug.

It reported σ = 5 mN/m as `plugs`, L/w = 4.95, at a suspiciously exact
20.000 Hz, with the median "slug" measuring 3960 µm of a 4000 µm outlet.
θ = 105° likewise came back as L/w = 2.61 plugs.

The fix tests whether a slug ever **separates from the junction**: track the
upstream edge (centroid − length/2) across mature frames and ask how far
past the junction it ever gets. A detached slug marches downstream; a thread
stays welded. The separation is not subtle —

| | detach distance |
|---|---|
| σ = 5 mN/m (thread) | 152 µm |
| θ = 105° (thread) | 49 µm |
| σ = 30 mN/m (plugs) | 2686 µm |

— roughly 17–55×, against a threshold of one channel width. Both false
plugs are now correctly `thread`, and the nominal σ = 30 case still
reproduces the reference exactly (L/w 1.550, 28.64 mm/s, 5.63 Hz).

Had this gone unnoticed it would have corrupted study B specifically, since
study B *is* the calibration curve: a fit through "L/w = 4.95 at 20 Hz for
σ = 5" would have been precise, confident and entirely wrong.

**Caveat on study A.** Its raw VTK was purged for disk before this fix
existed, so its six cases were classified by the older logic and cannot be
re-run through the new one without recomputing (~18 h). Its θ = 160° cell is
independently confirmed by study B's σ = 30 case — identical configuration,
reproduces exactly — and all six had L/w ≈ 1.55 with normal speeds, so they
are near-certainly genuine plugs. But that is inference, not a re-check.

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

| Study | Varies | Drive | Status |
|---|---|---|---|
| A | θ = 120–170° | fixed 980/490 Pa | ✅ all plugs, no boundary found |
| A2 | θ = 60–105° | fixed 980/490 Pa | ✅ all thread — cliff bracketed to 105–120° |
| B | σ = 5–40 mN/m | fixed 980/490 Pa | ✅ calibration curve; cliff between 5 and 8 mN/m |
| C | σ = 5–40 mN/m | scaled ∝ σ | running — does retuning the head to P ∝ σ recover the design point? |
| D | θ = 120 vs 160 | velocity-driven, 3D | ✅ both form plugs — the 2D finding holds with all four walls wetting |

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
