# CLAIMS.md — the chamber's claims registry

Every load-bearing claim the project makes, one entry each, with a
controlled status, a source, and explicit dependencies — so that "what
breaks if σ ≠ 30 mN/m?" is a query (`python3 -m claims.audit --dependents
sigma-30-assumed`), not an afternoon of re-reading READMEs. The registry is
mechanically audited by `claims/audit.py`; the audit fails the tree when an
entry violates the rules below.

**Statuses** (controlled vocabulary):

| status | meaning | audit requirement |
|---|---|---|
| `robust-frozen` | unrefuted over every committed case within the stated envelope | `verified:` names a battery candidate the battery expects `SURVIVOR` |
| `refuted-frozen` | killed by the battery, witness recorded | battery expects `REFUTED`; witness in body |
| `downgraded-frozen` | holds where seen; the signature admits no attack beyond | battery expects `DOWNGRADED` |
| `prose-verified` | verified in a results write-up, not yet mechanized | `source:` must exist; counts toward the mechanization backlog |
| `assumption` | an uncalibrated input the project currently trusts | no `verified:` field allowed |
| `open` | undecided; two explanations live | body names a **Distinguishing experiment:** |
| `withdrawn` | retired claim, kept for provenance | `superseded-by:` an existing entry, or a **Withdrawn:** line |

**Dependency semantics**: `depends:` means *this entry's claim about the
chamber stops being supported if the dependency falls*. Claims that are
pure statements about the frozen data (orderings, internal ratios,
identities) carry no assumption dependencies; claims whose absolute
operating points, regime boundaries, or bench transfer ride on an
assumption declare it. `[[links]]` elsewhere in an entry are
cross-references, not dependencies. No entry may depend on a
`refuted-frozen` or `withdrawn` entry.

---

## Assumptions

### sigma-30-assumed
- status: assumption
- kind: calibration-input
- source: hardware/microfluidic/microfluidic_chamber_plan.md

Interfacial tension is taken as σ = 30 mN/m everywhere in the simulation
campaign — uncited and unmeasured on the bench. ΔP ∝ σ, so this number
sets the entire operating point. Flagged as blocking in plan §12. The
remedy exists: [[sigma-head-calibration]] converts a measured σ directly
into head heights.

### theta-contact-angle-unmeasured
- status: assumption
- kind: calibration-input
- source: hardware/microfluidic/microfluidic_chamber_plan.md

The bench contact angle θ₀ is unknown; simulations bracket behavior
(see [[wetting-cliff-105-120]]) but the chip's actual wetting state is
unmeasured, and asymmetric wetting (PMMA floor vs adhesive ceiling) is
untestable with the current symmetry-plane meshes.

## Frozen-data claims (battery-checked)

### lw-monotone-psweep5x5
- status: robust-frozen
- kind: monotonicity
- source: simulation/openfoam/results/psweep5x5_2026-07/README.md
- verified: battery "psweep5x5: L/w monotone in both actuators" (2026-08-30, envelope nc=5 nd=5, 462 cases)

Cell-mean L/w strictly increases with P_disp and strictly decreases with
P_cont over the committed 5×5 grid. A pure ordering over frozen data — no
assumption dependencies.

### window-open-psweep5x5
- status: robust-frozen
- kind: operating-window
- source: simulation/openfoam/results/psweep5x5_2026-07/README.md
- verified: battery "psweep5x5: droplets in every cell (window open)" (2026-08-30, envelope nc=5 nd=5, 462 cases)
- depends: [[sigma-30-assumed]], [[theta-contact-angle-unmeasured]]

All 75 committed runs completed with droplets. As a statement about the
*chamber's* actuator window in Pa, it rides on σ (ΔP ∝ σ shifts the whole
window) and on wetting.

### lw-monotone-window600
- status: robust-frozen
- kind: monotonicity
- source: simulation/openfoam/results/window600_2026-07/README.md
- verified: battery "window600: L/w monotone in both actuators" (2026-08-30, envelope nc=5 nd=5, 154 cases)

Same double ordering at 600 µm over the ±30% window, 25/25 cells.

### window-open-window600
- status: robust-frozen
- kind: operating-window
- source: simulation/openfoam/results/window600_2026-07/README.md
- verified: battery "window600: drips in every cell (window at least +/-30%)" (2026-08-30, envelope nc=5 nd=5, 154 cases)
- depends: [[sigma-30-assumed]], [[theta-contact-angle-unmeasured]]

Every cell of the ±30% window at 600 µm drips — the window is at least as
wide as the 400 µm one. Same transfer caveat as
[[window-open-psweep5x5]].

### speed-monotone-both-actuators
- status: refuted-frozen
- kind: monotonicity
- source: claims/battery.py (posed by the battery; plausible by symmetry with L/w)
- verified: battery "psweep5x5: droplet speed monotone in both actuators" (2026-08-30, killed at (1,5))

Killed. Witness: at P_cont = 10 kPa, cell-mean speed drops 25.61 →
21.88 mm/s across P_disp 3300 → 3600 Pa. One of two independent kills
landing in the same column — see [[pdisp-3p6kpa-anomaly]].

### measurement-noise-independence
- status: robust-frozen
- kind: conditional-independence
- source: hardware/microfluidic/microfluidic_chamber_plan.md
- verified: battery "psweep5x5: actuator measurement noises independent" (2026-08-30, envelope k=25, r=0.078 vs 0.346)

Plan §7.1's P_cont_meas ⊥ P_disp_meas | (P_cont, P_disp) on the frozen
interventional grid: residual correlation |r| ≤ 3/√n at every prefix
attacked.

### scaleup-similarity-4pct
- status: robust-frozen
- kind: similarity
- source: simulation/openfoam/results/scaleup_2026-07/README.md
- verified: battery "scaleup: similarity within 4% (400 um anchor predicts 600/800)" (2026-08-30, envelope nw=3)

L ∝ w, L/w and speed flat, period ∝ w, f ∝ 1/w, Q ∝ w², V ∝ w³ — eight
observables within 4% of the 400 µm anchor's out-of-sample prediction.
Ratio-anchored, so internally σ-invariant.

### drop-volume-mass-balance
- status: robust-frozen
- kind: conservation
- source: simulation/openfoam/results/scaleup_2026-07/README.md
- verified: battery "scaleup: V_drop = Q_water x period within 1%" (2026-08-30, envelope nw=3)

Measured droplet volume equals dispersed flux × period at every committed
width — the pipeline's mass-balance self-check, now a permanent fixture.

### mill3d-correction-original
- status: refuted-frozen
- kind: dimensionality-correction
- source: simulation/openfoam/results/mill3d_2026-07/README.md
- verified: battery "mill3d: 2D->3D correction as FIRST reported (superseded)" (2026-08-30, dies at inspiring)
- superseded-by: mill3d-2d3d-correction-800um

The originally-reported 2D→3D factors (+3% length, ×1.43 speed, ×2.4
frequency) were confounded by a 79% water-flux excess. Witness against
the corrected matched pair: length ratio measured ×0.871 vs claimed
×1.03. The README warning box is now a failing test.

### mill3d-2d3d-correction-800um
- status: downgraded-frozen
- kind: dimensionality-correction
- source: simulation/openfoam/results/mill3d800_2026-08/README.md
- verified: battery "mill3d800: corrected 2D->3D factors (x0.87 L, x1.17 v, x1.59 f)" (2026-08-30, validity-limited at 1 pair)

The corrected factors hold — on exactly one matched pair, and the
parameter signature says so. A single-point calibration until phase 4
buys more matched solves; do not quote as a general correction.

### cross-repro-pointwise-5pct
- status: refuted-frozen
- kind: reproducibility
- source: claims/battery.py (posed by the battery)
- verified: battery "protocol vs psweep: L/w agrees within 5% at EVERY shared setting" (2026-08-30, killed at k=6)

Killed. Witness: the protocol run and the cold-start grid disagree by
6.8% on L/w at (13000, 3600) Pa — the second independent kill in the
3.6 kPa column, see [[pdisp-3p6kpa-anomaly]].

### cross-repro-median-3pct
- status: robust-frozen
- kind: reproducibility
- source: claims/battery.py (posed by the battery)
- verified: battery "protocol vs psweep: median L/w disagreement within 3%" (2026-08-30, envelope k=9)

The scoped survivor: median relative L/w disagreement across the nine
shared settings stays within 3% at every prefix attacked (1.6% at full
overlap). Cross-run reproducibility holds *in the median*; the pointwise
version dies on one setting.

## Prose-verified claims (mechanization backlog)

### garstecki-scaling-recovered
- status: robust-frozen
- kind: literature-recovery
- source: simulation/openfoam/results/sweep_2026-07/README.md
- verified: battery "sweep: L/w affine in flow-rate ratio (machine-refit law)" (2026-08-30, envelope k=9, tol 0.11)

L/w = 0.80 + 1.24·(Q_disp/Q_cont) recovered from the velocity-driven
sweep (Garstecki's squeezing-regime form). Mechanized in phase 3: the
no-hints-guarded minimax refit (claims/refit.py, exact rational, no least
squares) re-derived L/w = 0.852 + 1.203·q unaided — slope within 3%,
intercept within 6.5% of the published fit (refit_acceptance.py R1–R5) —
after the exact fitter first honestly REFUSED the raw noisy rows. The
machine also rediscovered the README's Ca-stratification blind: adding Ca
tightens the minimax residual 3.0× with a negative coefficient
(shear-assisted breakup shortens slugs).

### cyclicity-actuation-selects-graph
- status: prose-verified
- kind: causal-structure
- source: simulation/openfoam/results/cyclicity_2026-07/README.md

Pressure actuation makes flows emergent and the equilibrium causal graph
cyclic (latent junction-pressure node); imposed-flow actuation severs
those edges — a syringe pump is a physical do-operator. The result is
timescale-relative (equilibrium vs within-cycle), per the source's own
qualification. The flagship phase-5/6 target: formalize over a bounded
graph class where enumeration is a true exhaustive decider.

### design-point-hydrostatic-head
- status: prose-verified
- kind: operating-point
- source: simulation/openfoam/results/wetting_2026-08/README.md
- depends: [[sigma-30-assumed]], [[theta-contact-angle-unmeasured]]

The 800 µm chip's hydrostatic design point (oil/water column heights).
Study C shows retuning the head as P ∝ σ recovers the design point
exactly — so the *shape* survives a wrong σ, but the *numbers* in the BOM
ride on σ = 30 until the bench measures it.

### wetting-cliff-105-120
- status: prose-verified
- kind: regime-boundary
- source: simulation/openfoam/results/wetting_2026-08/README.md
- depends: [[sigma-30-assumed]]

Contact angle does not gate droplet formation at 800 µm until a cliff
bracketed between θ = 105° and 120°; θ = 120° forms plugs with all four
walls wetting (3D spot-check). Swept at σ = 30 mN/m.

### sigma-head-calibration
- status: prose-verified
- kind: calibration-procedure
- source: simulation/openfoam/results/wetting_2026-08/README.md

The remedy for [[sigma-30-assumed]]: pressures scale as P ∝ σ, so a
measured σ converts directly to head heights (oil column in cm ≈ σ in
mN/m ÷ 3). Turns the σ assumption from a threat into one bench
measurement.

## Open anomalies

### mesh-997um-anomaly
- status: open
- kind: anomaly
- source: simulation/openfoam/results/mesh_convergence_2026-07/README.md

5 of 9 mesh-convergence points report droplet length ≈ 997.4 µm — the
entire outlet. Two live explanations: a post-processing clustering
artifact, or a genuine regime transition at the highest-flow corner.
**Distinguishing experiment:** the source README proposes the decisive
run; not yet executed (phase-4 candidate).

### pdisp-3p6kpa-anomaly
- status: open
- kind: anomaly
- source: simulation/openfoam/results/psweep5x5_2026-07/README.md

The P_disp = 3.6 kPa column. The psweep5x5 README flagged it as
regime-boundary-adjacent (suspected period-doubling at 3.6 kPa); the
claims battery then landed two independent kills in the same column with
named coordinates — speed monotonicity breaks at (10 kPa, 3.3→3.6 kPa)
([[speed-monotone-both-actuators]]) and cross-run disagreement peaks at
6.8% at (13 kPa, 3.6 kPa) ([[cross-repro-pointwise-5pct]]).
**Distinguishing experiment:** targeted solves along the 3.6 kPa column
(finer P_disp steps, longer averaging windows, per-droplet frequency) —
first target when phase 4 wires the scheduler to the solver.

## Withdrawn

### encoder-null-control
- status: withdrawn
- kind: instrument
- source: simulation/openfoam/tjunction_3d_encoder/README.md

The encoder's symmetry null control assumed c1 == c3 was geometrically
guaranteed; measurement found c1 − c3 = −0.035 (3σ) because oil crosses
the junction directionally. **Withdrawn:** the diagnostic is retired in
place in the source README; the asymmetry is real signal, not a rig
error, and any future null control must be built on a measured baseline.
