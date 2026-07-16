# Mesh convergence check (5 µm vs 7.5 µm) — 2026-07

Answers the caveat carried by every serpentine-based dataset so far
("2D, coarse mesh: quantitatively indicative, not converged. Re-run the
repo-resolution (5 µm)..."). **Verdict: inconclusive on a rigorous
point-by-point basis — not because the solver disagrees, but because
measuring droplet length reliably from VTK output turned out to be
genuinely harder at 5 µm than the existing tooling was built for.** That
finding is itself worth having; see below for what's trustworthy and what
isn't.

## Setup

`gen_blockmesh.py --dx 5.0` on `tjunction_2d_serpentine` (2.29× more cells:
12,614 vs 5,500; checkMesh-clean), timestep recalibrated to the tighter
capillary limit. 9 cases at the same pressures already published in
`psweep_2026-07` and `protocol_v1_2026-07` — P_cont ∈ {10, 13, 16} kPa ×
P_disp ∈ {2.4, 3.0, 3.6} kPa, a literal subset of `psweep5x5_2026-07`'s
25-cell grid, giving three independent 7.5 µm reference points per pressure
combination to compare against. All 9 solver runs succeeded (~16–20k s
each, ~1.7–2× the 7.5 µm cost, less than the ~4.25× first-principles
estimate — likely because these specific points run somewhat faster flow
than the case used to calibrate that estimate).

## What's solid: solver-level behavior

**Droplets form at every one of the 9 pressure points at 5 µm, the same
qualitative regime as at 7.5 µm.** No case failed, no case went dry, no
case jumped to a different flow regime (jetting, stratified). That's the
question a mesh-convergence check most needs to rule out — a resolution-
dependent regime change — and it doesn't happen here.

## What's not solid: quantitative droplet-length comparison

The existing extraction pipeline (`extract_droplets.py` +
`analyze_pressure_sweep.py`'s static x/length window) was built around how
droplets looked in the cases it was validated on, and produced clearly
wrong numbers here on first pass: `L/w` up to 2.57 with non-monotonic
trends (see `results_default_filter_UNRELIABLE.csv` — kept for
transparency, not for use). Root cause, confirmed by direct inspection of
the raw per-frame VTK detections: a still-attached, still-growing water
thread (fed continuously from the inlet, length increasing every frame)
passes through the same x/length window a genuinely detached slug does,
and every growth-phase snapshot gets counted as an independent "droplet"
observation, contaminating the median.

Built [`extract_mature_droplets.py`](../../scripts/extract_mature_droplets.py)
to fix this: link raw detections into per-droplet tracks (frame-to-frame
position continuity), and only accept a frame as "mature" when the slug's
length is flat AND its position is advancing (an attached thread grows in
place; a detached slug translates rigidly). This is a real improvement —
it correctly and automatically recovers the hand-verified reference value
at `pc10k_pd3k` (275.7 µm, exactly matching manual inspection) — but it
has two remaining known false-positive modes, found by cross-checking its
output against manual reads (`mature_extractor_output.txt`):

1. **Growth-phase frame pairs that are locally flat by chance** — a mostly-
   monotonic growth curve can have a frame-to-frame delta small enough to
   pass the flatness threshold even while still attached, especially near
   the top of a long, slowing growth ramp.
2. **Boundary-exit trajectories** — a slug leaving the domain gets
   truncated at the outlet, so its measured length shrinks over several
   frames; if that shrinkage is gradual, some frame pairs pass the same
   flatness test while the position (still exiting) keeps advancing.

Both modes were visible in the 9-case output: some cases produced a single
clean, well-supported track (e.g. `pc16k_pd2.4k`, 49 matching frames);
others produced multiple tracks with implausible sub-3ms "formation gaps"
between them (a sign of a single detachment event being split) or a
lone 5-frame track at `L/w = 6.65` (`pc10k_pd3.6k` — obviously a boundary-
exit fragment, not a droplet). Distinguishing these algorithmically needs
either explicit domain-boundary handling or velocity-field-based advection
prediction instead of naive nearest-neighbor position matching — more
engineering than fits in this pass.

## The numbers that are trustworthy (manually cross-checked)

| Point | 5 µm L/w | 7.5 µm L/w (mean, psweep5x5) | Diff |
|---|---|---|---|
| pc10k_pd3k | 1.84 (hand-verified: clean 11-frame plateau at 275.7 µm) | 1.50 | +23% |
| pc16k_pd3k | 1.07–1.30 (two independent clean plateaus, 160.4 & 195.5 µm) | 1.14 | −6% to +14% |

Everything else in the grid has at least one plausible reading but isn't
independently confirmed by hand, so it isn't reported as a comparison
point here.

## Verdict and recommendation

No evidence of a mesh-resolution-driven regime change or solver
disagreement. The two hand-verified comparison points span from good
agreement (pc16k_pd3k) to a real ~23% difference (pc10k_pd3k) — not
alarming, but not a clean "converged" result either, and not enough points
to characterize a trend. **The honest state: this check increased
confidence that the published response surfaces aren't qualitatively
wrong, but it did not deliver the rigorous quantitative validation it set
out to.**

Highest-value follow-up, in order:
1. Re-run these same 9 points at 5 µm with a longer `endTime` (e.g. 0.12 s
   instead of 0.06 s) so 2–3+ full clean formation cycles occur per case —
   most of the ambiguity above comes from catching cases mid-cycle in a
   short window, and this would very likely resolve most of it without
   further tooling work.
2. If a fully general, trustworthy extractor matters going forward (e.g.
   for the eventual 3D run or external sharing), invest in proper
   velocity-field-based advection tracking and explicit boundary handling
   in `extract_mature_droplets.py` rather than the position-proximity
   heuristic used here.

## Files

- `results_default_filter_UNRELIABLE.csv` — first-pass output from the
  existing pipeline; kept for transparency, known wrong, do not use.
- `mature_extractor_output.txt` — `extract_mature_droplets.py`'s raw
  per-track output for all 9 cases, the basis for the table above.
- `cases.json` — case definitions (pressures, endTime, etc.)
