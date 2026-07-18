# Mesh convergence check (5 µm vs 7.5 µm) — 2026-07

Answers the caveat carried by every serpentine-based dataset so far
("2D, coarse mesh: quantitatively indicative, not converged. Re-run the
repo-resolution (5 µm)..."). Two passes: an initial `endTime = 0.06 s` run
(too short — cases were caught mid-formation-cycle, giving 2 solid
comparison points and several ambiguous ones) and a follow-up at
`endTime = 0.12 s` on the same 9 cases, which resolved most of that
ambiguity. **Verdict (v2): 4 of 9 points now have clean, internally
self-consistent measurements agreeing with the 7.5 µm data to within
3–19% — reasonable agreement, improving at higher pressure. The other 5
hit a new, distinct issue at high droplet throughput (see below) that's a
genuine open question, not obviously an artifact.**

## Update — rerun at endTime = 0.12 s

Same 9 cases, same 5 µm mesh, `endTime` doubled (~33–38k s/case, ~9–11h
wall-clock spread across the run). All 9 solved cleanly again.

**4 points now have strong, repeatable evidence** — 3 independent
near-identical length readings per case, each spanning 40+ frames (a third
to half of the whole run), not just one lucky plateau:

| Point | 5 µm L/w (n independent tracks) | 7.5 µm mean (psweep5x5) | Diff |
|---|---|---|---|
| pc16k_pd3k | 1.175 (6 tracks, scattered 120–205) | 1.136 | +3.4% |
| pc16k_pd2.4k | 1.092 (3 tracks: 160, 165, 165) | 1.036 | +5.4% |
| pc13k_pd2.4k | 1.236 (3 tracks: 180, 185, 190) | 1.136 | +8.8% |
| pc10k_pd2.4k | 1.554 (3 tracks: 211, 236, 253) | 1.303 | +19.2% |

Agreement is best at high pressure and degrades toward the low-pressure
corner — physically sensible (higher Ca means faster, more decisive
pinch-off, less sensitive to small numerical differences near a marginal
regime boundary). None of these differences is alarming for a 2D,
first-refinement mesh study.

**5 points (all P_disp = 3.6 kPa, plus pc10k_pd3k) show a new pattern**:
repeated detections at exactly `length ≈ 997.4 µm` — essentially the
*entire* outlet channel length — appearing persistently in the back half
of the longer run. Two candidate explanations, not yet distinguished:

1. **Post-processing artifact**: these are the highest-total-flow cases,
   so more droplets form and queue up in the fixed ~1000 µm outlet within
   0.12 s; if their spacing shrinks below `2×dx`, the naive gap-based
   clustering in `detect_droplets_2d` would merge adjacent droplets into
   one apparent blob.
2. **Genuine physics**: `pc16k_pd3.6k` (the single highest-flow corner of
   the whole grid) shows a *different* signature — not the 997.4 µm
   plateau, but a sequence of tracks with steadily increasing length
   (230 → 338 → 449 → 524 → 531 → 581 µm across the run) — consistent with
   a real transition toward a longer-slug or jetting-adjacent regime as
   the transient clears, not a clustering bug. If real, that's a
   legitimate and interesting finding: the highest-flow corner of the
   sweep may not have reached steady state within the original
   `endTime = 0.06 s`, and the published `psweep5x5` value there could be
   a transient snapshot rather than the asymptotic behavior.

Distinguishing these needs either a longer outlet domain (removes the
queuing explanation) or direct visual inspection of the alpha field near
`length ≈ 997 µm` (confirms whether it's one continuous water body or
several close droplets) — out of scope for this pass.

## Update 2 — extended-outlet recheck (v3): 997 µm signature resolved

Reran the two most-affected cases (`pc10k_pd3.6k`, `pc16k_pd3.6k`) at 5 µm
with the outlet tripled to 3000 µm (`gen_blockmesh.py --l-outlet 3000`,
24,797 cells; ~24–27 h/case). Both solved cleanly.

**The 997 µm signature and the "climbing length" trend are both gone.**
No full-channel water bodies, no runaway slug growth. The earlier
pathology was droplets crowding and coalescing in the too-short outlet —
a measurement-domain artifact, not chamber physics. Specifically:

- `pc16k_pd3.6k`: three independent tracks all at **exactly 165.0 µm**
  (agreement to ±0.1 µm, each tracked 36–107 frames), steady 35.5 ms
  rhythm. The cleanest measurement of the whole campaign — a stable,
  monodisperse slug train. The "growing-slug regime" hypothesis is
  refuted at this corner.
- `pc10k_pd3.6k`: five tracks in a clear **alternating large/small
  pattern** — 478, 270, 550, 245, 532 µm in formation order (L/w
  alternating ≈ 3.4 / ≈ 1.7). This is classic period-doubled (doublet)
  emission, a real and well-documented droplet-generation phenomenon
  near regime boundaries. The high-water corner of the grid genuinely
  sits near an emission-instability boundary.

**An honest confound, discovered during analysis:** tripling the outlet
also triples the outlet channel's hydraulic resistance, raising the
junction pressure from ~0.66 kPa to ~1.9 kPa at reference flow. The
extended-outlet cases therefore run at a *shifted operating point* (lower
effective water drive at the same inlet pressures), so their L/w values
must NOT be quantitatively compared against the short-outlet published
numbers — e.g. the drop from 1.29 (published, 7.5 µm short) to 1.10
(this run, 5 µm long) at pc16k_pd3.6k mixes outlet de-crowding, mesh
refinement, and the operating-point shift inseparably. The qualitative
conclusions above (no artifact blob, no runaway growth, stable
monodisperse emission at 16k, period-doubled emission at 10k) are
internal to the extended-outlet configuration and unaffected. A future
apples-to-apples version would compensate the inlet pressures for the
added outlet resistance, or report against measured junction pressure.

**Final convergence verdict across the campaign:**
- 4 interior/low-water points: converged within 3–19% (best at high Ca).
- High-water corner (P_disp = 3.6 kPa): near a period-doubling emission
  boundary; single-valued "slug length" is not a well-posed summary
  there, and values are sensitive to mesh, endTime, and downstream
  resistance. The corresponding `psweep5x5_2026-07` cells should be
  treated as regime-boundary-adjacent rather than converged point
  measurements (noted in that dataset's README).

**Original (endTime = 0.06 s) findings below, unchanged, for reference.**

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
- `mature_extractor_output.txt` / `cases.json` — endTime=0.06s pass.
- `mature_extractor_output_v2_endtime0.12.txt` / `cases_v2_endtime0.12.json`
  — endTime=0.12s rerun, the basis for the updated table above.

## Recommendation (updated)

The 4 clean points give reasonable confidence the published response
surfaces aren't quantitatively wrong at low-to-moderate P_disp. The
high-P_disp corner needs one more targeted check before trusting it:
extend the outlet domain length in `gen_blockmesh.py` (a few hundred µm
is likely enough) and re-run just `pc10k_pd3.6k` and `pc16k_pd3.6k` — if
the 997.4 µm signature disappears, it was queuing/clustering; if
`pc16k_pd3.6k`'s length keeps climbing, the growing-slug trend is real and
the published `psweep5x5` value at that corner should be flagged as
possibly transient.
