# Autonomous research station — sim → mill → test → gap

> Status: **design exploration.** No hardware committed, no code written yet.
> This document exists to decide what to build and in what order.

The idea: a bench cell that takes a chip geometry, simulates it, mills it,
plumbs it, runs a real experiment on it, and reports how far the simulation
was wrong — unattended, on a loop.

The thing worth building is not the robot. It is **a measured, repeatable
sim-to-real gap on a system whose causal ground truth we already know.** The
robot exists so that number can be collected hundreds of times instead of
five times, and so the station survives a clogged chip at 3 a.m. Keeping that
straight decides most of the architecture below.

---

## 1. What already exists

The simulation half of this loop is largely built and verified.

| Piece | Where | State |
|---|---|---|
| Verified droplet-regime solver | [`tjunction_2d_mill`](../simulation/openfoam/tjunction_2d_mill) | 25/25 sweep cells form droplets, monotonic response maps |
| 3D fidelity twin | [`tjunction_3d_mill`](../simulation/openfoam/tjunction_3d_mill) | length transfers 2D→3D within +3%; frequency **2.4× faster** in 3D |
| Batch sweep driver | [`sweep_pressure.py`](../simulation/openfoam/scripts/sweep_pressure.py) | Docker, concurrent, CLI-parameterised |
| Protocol time-series driver | [`protocol_run.py`](../simulation/openfoam/scripts/protocol_run.py) | SET/WAIT/MSR analog, actuator-labelled series |
| Droplet measurement | [`extract_mature_droplets.py`](../simulation/openfoam/scripts/extract_mature_droplets.py) | track-linking + growth-plateau detection |
| Causal-chamber schema | [`variables.csv`](../datasets/mf_tjunction_test_v1/variables.csv), [`causal_dataset.csv`](../simulation/openfoam/results/mill_2026-07/causal_dataset.csv) | 48 columns, ecosystem-compatible |
| Fabrication layout | [`gen_chip_layout.py`](../hardware/microfluidic/gen_chip_layout.py) | parametric, layered SVG, derived from the sim geometry |
| Causal structure result | [`cyclicity_2026-07`](../simulation/openfoam/results/cyclicity_2026-07) | actuation mode determines whether the graph has a cycle |

What does **not** exist: CAM, any actuator control, any camera pipeline, any
robot code (`hardware/control`, `hardware/arduino` are empty).

---

## 2. Three loops, not one

The pitch describes a single loop. It is actually three, with wildly
different periods and costs, and conflating them is the main way this project
could waste a year.

| Loop | Trigger | Period | Needs a new chip? | Needs a robot? |
|---|---|---|---|---|
| **Inner** — pressure setpoints | every measurement | seconds–minutes | no | no |
| **Outer** — geometry change | optimizer proposes a design | hours | yes | no (batch) |
| **Recovery** — clog, leak, fouling | failure detected | unpredictable | yes | **yes** |

Almost all of the science lives in the inner loop: the causal graph, the
response maps, the intervention experiments, the cyclicity result. None of it
needs a mill or an arm. The outer loop needs a mill but only in batches. The
robot's real job is the recovery loop — which is exactly the job that makes
unattended multi-day operation possible.

**Consequence:** build inner → outer → robot, not the reverse. And the outer
loop should be **batched**, not one-in-one-out (see §4).

---

## 3. Design rules that make this tractable

Four decisions do most of the work. Each one converts a hard robotics problem
into a fixture problem.

### R1. The robot only handles dry, rigid parts. Fluid connections are permanent.

The hardest manipulation task in the naive pitch is not chip handling — it is
plumbing. Inserting tubing, purging bubbles, and sealing luer ports
autonomously is a contact-rich, deformable-object, one-shot task with no
recovery, and it is well past what an SO-101-class arm does reliably.

So: the arm never touches a fluid connection. A **reusable clamped manifold**
carries the luer ports, tubing, and gaskets permanently. The milled chip is a
dry insert. Priming becomes a valve-and-pressure sequence, not a manipulation
task.

This also kills the 3M 468MP lamination step from the autonomous path —
peel-align-roller to 100 µm with no rework is not a job for these arms.

**Risk, stated plainly:** a dry clamped PMMA seal at 4 kPa is *plausible* but
unproven here. In its favour, channels are cut into the top face, so the
sealing land is virgin cast surface, not a milled one — flatness is good. The
specific failure mode is the **raised burr at the channel edge** holding the
lid off and letting oil wick along the interface. The adhesive layer's
compliance is precisely what swallows those burrs today.

**Graceful degradation:** if clamping fails, a human laminates a magazine of
finished chips every N runs and the robot only inserts them into the manifold.
The architecture does not hinge on this — clamping only decides *how far
upstream* the automation reaches. Prototype it early (§5, M0) on a hand-milled
chip; keep 468MP as the fallback.

### R2. Jig-dominant, arm-light.

These arms have roughly millimetre repeatability and a few hundred grams of
payload. Therefore: every placement gets a lead-in chamfer or funnel, every
clamp is servo- or pneumatically actuated (never arm-torqued), and placement
is closed-loop off a wrist camera and fiducials rather than open-loop off
kinematics. Nothing in the cell should require the arm to be accurate; the
jigs supply the accuracy.

### R3. Sim and real must share one measurement code path.

This is the single most important software change in the project, and it has
nothing to do with robots.

Today, `extract_mature_droplets.py` measures droplets from a VTK `alpha.water`
field. The bench will measure them from camera frames. If those are two
separate implementations, then the "sim-to-real gap" we publish is
contaminated by analysis-methodology drift and the number means nothing.

Refactor `DropletExtractor` into:

- **a frame source** — VTK alpha field *or* thresholded camera frame, both
  yielding a binary water mask on a known µm-per-pixel grid;
- **a measurement core** — connected components, track linking, growth-plateau
  detection, L/w/v/f extraction. Untouched, shared, identical.

Dyed water backlit against silicone oil in PMMA is a high-contrast target, so
the mask is genuinely comparable to a thresholded `alpha` field. Do this
refactor before any bench data is collected, so the first real number is
already trustworthy.

### R4. Measure fabrication variance before claiming model error.

Mill 3–5 nominally identical chips and run all of them. Chip-to-chip spread is
a term in the gap, and if it is not separated first, every "the model was 12%
off" claim is unfounded. Milling is cheap (§4) — replicates cost minutes.

The gap then decomposes cleanly into three terms we can each report:
**2D→3D model error** (already measured: +3% length, ×2.4 frequency),
**3D→real error**, and **chip-to-chip fabrication variance**.

---

## 4. The fab side is cheaper than expected

Worth doing the arithmetic before designing around it. Total channel length on
mill chip v1 is ~62 mm (48 mm oil feed + 7.5 mm water leg + 6 mm outlet), cut
in two 0.2 mm passes → ~124 mm of cutting. At a ~250 mm/min feed that is about
**30 seconds of cutting**; call it 2–5 minutes per chip with port drilling and
the outline.

So: **milling is fast and cheap; simulation is the expensive step** (45–60 min
per 2D case, serial). The loop is sim-bound, not fab-bound. That inverts the
obvious architecture:

- Run the optimizer asynchronously on a many-core box.
- **Batch-mill** 8 candidate geometries in ~30 minutes, then test them in
  sequence. A magazine, not a conveyor.
- Mill replicates for free (R4).

Two practical concerns on the Nomad:

- **Spindle ceiling.** The 883 Pro tops out around 10k RPM, which is low for a
  0.4 mm (1/64") cutter — PMMA gums and melts at low surface speed. At 9,600
  RPM and 250 mm/min with a 2-flute, chip load is ~13 µm/tooth, which is
  workable but tight. Use a **single-flute O-flute plastic cutter**, climb
  mill, and air-blast for chip evacuation. Feeds and speeds need bench
  verification, not spreadsheet confidence.
- **Blank fixturing.** Do not fixture individual 1×3" blanks. Mill from an
  8×8" sheet held permanently on the bed, leaving each chip on an onion-skin
  with small tabs; the arm snaps chips out. One manual sheet reload per ~8
  chips, and per-chip fixturing disappears entirely. Watch for onion-skin
  thickness consistency and part shift on the severing pass.

**Debris is the failure mode that matters.** Stringy PMMA swarf in a 400 µm
channel ruins a run. The cell needs an IPA dunk/ultrasonic station and a
post-mill optical channel inspection (same camera, before the chip is ever
plumbed) as a hard gate.

Also worth knowing before designing for unattended operation: at the
reference point (~28 mm/s in a 400×400 µm channel) total throughput is
**~16 mL/hr** — roughly 13 mL/hr oil, 3 mL/hr water. A 500 mL oil reservoir
is ~38 hours; a 500 mL waste vial fills in ~31 hours and is the binding
constraint. Size waste at 1 L for multi-day runs.

---

## 5. Milestones

Each one is chosen so it produces a result even if the next never happens.

### M0 — First sim-to-real number. No robots.
Human mills one chip from the existing SVG, clamps it, and runs a pressure
sweep against the response maps in
[`results/mill_2026-07`](../simulation/openfoam/results/mill_2026-07).

Needs: the R3 refactor, a camera at **≥120 fps** (the 3D check says ~27 Hz
droplets — 60 fps is not enough), backlight, and two *measured, repeatable*
pressure actuators. Instrument gap is ~$200–600, already scoped.

Also here: the R1 clamp prototype, and the wetting check the mill-chip README
flags — put a water droplet on Span-80-doped-oil-flooded PMMA before
committing to a chip. If water wets the surface, droplets wall-pin exactly as
the December 2025 sim did.

**Proves:** the gap is measurable at all. This is the paper's core number.

### M1 — Automate the inner loop.
Pressure setpoints under program control + camera + shared measurement →
unattended overnight protocol runs. The physical analog of `protocol_run.py`,
emitting the same schema.

**Proves:** it is a causal chamber. Enables the interesting experiment (§6).

### M2 — Automate fab handling.
Arm 1 (dirty side): sheet → snap out → clean → inspect → tray.
Arm 2 (clean side): tray → manifold → clamp → run → eject → waste.
Handoff via a passive tray so swarf never reaches the wet rig.

**Proves:** unattended multi-day operation, including clog recovery.

### M3 — Close the outer loop.
Optimizer proposes geometry → `gen_chip_layout.py` → CAM → mill → test →
update surrogate. Run in 2D with the measured 3D correction as a calibrated
surrogate; reserve full 3D for final fidelity checks.

Design vector: channel widths, depth, junction geometry, feed-resistance
length, outlet length. Objective: e.g. "500 µm slugs at 30 Hz, minimum
polydispersity."

**Proves:** the full pitch.

---

## 6. The experiment that makes this more than an engineering demo

The [cyclicity result](../simulation/openfoam/results/cyclicity_2026-07) says
actuation mode determines the causal graph: pressure sources give an emergent,
cyclic structure; flow sources act as a physical do-operator and give
something close to a DAG.

That is testable on the bench, and it is a much better question than "our slug
lengths were 12% off." Does the *causal structure* transfer sim→real — not
just the numbers? Run the real chip under hydrostatic columns, then under
syringe pumps, and check whether the predicted cycle appears and disappears.

Ground truth is known, the intervention is physical, and the station can
collect the statistics. That is the result worth automating for.

---

## 7. Risks, ranked honestly

1. **Autonomous plumbing.** Mitigated to near zero by R1, but only if the
   permanent-manifold design actually seals. Highest-leverage early test.
2. **Debris and clogging.** The dominant real-world failure mode for milled
   chips. Needs a hard inspection gate, not optimism.
3. **Measurement drift between sim and bench.** Silently poisons the headline
   number. R3 is the fix and it must land before M0 data.
4. **Fabrication variance swamping model error.** R4 is the fix; cheap.
5. **Nomad automation surface.** Door actuation, tool-length checks, and
   whether the controller can be driven programmatically (rather than through
   Carbide Motion by hand) all need verification. **Unknown to me — check the
   actual machine before designing around it.**
6. **Tool breakage.** A 0.4 mm carbide cutter snapping mid-job destroys a chip
   silently. Optical inspection catches the result; spindle-load or
   tool-length probing would catch the cause.
7. **Arm capability.** Lowest risk, given R1 and R2. If the arms turn out to be
   the limiting factor, the fixtures were designed wrong.

---

## 8. Why LeRobot, and what it gets back

Scripted motion would be enough for M2. The reason to build this in LeRobot is
the data: every cycle produces a robot episode paired with a fab record and a
physics measurement — which means **automatic, physically-grounded success
labels.** "Did this chip produce in-spec droplets" is a reward signal with no
human annotation in it.

A manipulation benchmark whose reward is a measured physical outcome rather
than a labelled demonstration is a genuinely unusual thing to have, and it
falls out of this station for free.

---

## 9. Open questions

- Does a dry clamped PMMA seal hold at 4 kPa, or is 468MP lamination
  unavoidable? (Decides how far upstream automation reaches — R1.)
- Can the Nomad 883 Pro be driven programmatically, and what is actually
  involved in automating the door? (Blocks M2 design.)
- Which pressure actuator: motorized hydrostatic columns, or pump + MPX5010 +
  PID? Columns are more repeatable and slower; pumps are faster and noisier.
- Camera and optics selection at ≥120 fps with enough field of view to hold
  2–3 slugs — the observation window is ~6 mm.
- One arm or two? Two buys dirty/clean separation cheaply, given a dozen are
  already on hand.
