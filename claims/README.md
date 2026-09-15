# claims/ — the chamber's claims layer (lakatos engine port, phases 1–3)

The prose claims scattered across `results/*/README.md` — monotonicity,
similarity, mass balance, the 2D→3D correction, conditional independence —
re-expressed as machine-checked conjectures and pushed through the
[lakatos discovery engine](https://github.com/a-bissell/Lakatos): derived
attack schedules, graded verdicts (`ROBUST_CONJECTURE` / `REFUTED` /
`DOWNGRADED`), explicit envelopes, and a witness on every kill.

```
python3 -m claims.battery      # from the repo root
```

Needs the `lakatos` package: `pip install -e ../card_stuff`, or keep the
Lakatos repo checked out as a sibling directory (path fallback built in).

| file | role |
|---|---|
| `frozen.py` | Tier-1 decider: exhaustive instance tests over the frozen, committed CSVs (~2.4k rows re-checked per run) |
| `battery.py` | the 12-claim battery + expected-disposition acceptance ledger |
| `audit.py` | mechanical audit of [`CLAIMS.md`](../CLAIMS.md) (phase 2): controlled statuses, resolvable links, battery cross-check both ways, sources exist, no depending on refuted/withdrawn entries — plus the dependency query |
| `refit.py` | phase 3, fitter side: no-hints machine refit of the sweep scaling law (exact rational minimax over support pairs; the exact fitter's refusal on noise demonstrated first) |
| `refit_acceptance.py` | phase 3, checker side: knows the published Garstecki answer, judges the blind refit (R1 no-hints guard, R2 refusal, R3 recovery bands, R4 residual, R5 Ca-stratification) |

```
python3 -m claims.audit                                  # audit the registry
python3 -m claims.audit --dependents sigma-30-assumed    # what breaks if sigma != 30?
```

## The registry (phase 2)

[`CLAIMS.md`](../CLAIMS.md) at the repo root holds every load-bearing claim
— the 12 battery claims plus assumptions (σ = 30 mN/m, uncalibrated θ),
prose-verified results (Garstecki recovery, cyclicity, the design point,
the wetting cliff, the σ-head calibration), open anomalies (the 997 µm
mesh question, the 3.6 kPa column), and the withdrawn encoder null
control. `depends:` edges make blocking-assumption analysis a query: σ
currently implicates the two open-window claims, the design point, and
the wetting cliff. The `prose-verified` count is the mechanization
backlog.

## The refit acceptance (phase 3 — the port's t25)

`python3 -m claims.refit_acceptance`: the domain-free lakatos fitter,
pointed blind at the frozen velocity sweep, must re-derive the published
Garstecki fit unaided. Result (2026-08-30): the exact fitter first
REFUSED the raw noisy rows (honest — no exact law fits noise); the
minimax support-pair refit then proposed L/w = 0.852 + 1.203·q — slope
within 3% and intercept within 6.5% of the published 0.80 + 1.24 — and,
offered Ca as a second atom, rediscovered the README's stratification
note blind (residual 3.0× tighter, negative Ca coefficient =
shear-assisted breakup shortens slugs). A no-hints guard scans the whole
fit path's source for the law's name, its published coefficients, and any
least-squares vocabulary; the machine law is claim #13 in the battery.

## What the first run established (2026-08-30)

* **8 claims ROBUST within their frozen envelopes** — both monotonicity
  grids, both open-window claims, the noise-independence CI from plan §7.1,
  scale-up similarity at 4%, the volume mass balance, and median cross-run
  reproducibility at 3%.
* **The superseded mill3d claim is now refuted mechanically**, not just in
  a README warning box: the originally-reported ×2.4 frequency / ×1.43
  speed correction dies against the corrected `mill3d800` pair (measured
  ×1.59 / ×1.17, length ×0.87).
* **The corrected factors grade DOWNGRADED, not robust**: one matched
  pair, and the parameter signature says so (`validity-limited at 1`).
  Promoting them requires new solves (phase 4), not prose.
* **Two independent kills localize the same anomaly**: droplet speed
  breaks monotonicity at (P_cont 10 kPa, P_disp 3.3→3.6 kPa), and the
  protocol-vs-psweep disagreement peaks (6.8%) at (13 kPa, 3.6 kPa) —
  both in the P_disp = 3.6 kPa column the psweep5x5 README flagged as
  regime-boundary-adjacent (suspected period-doubling).

Honesty scope: these checks are exhaustive over the **frozen grids only**.
`ROBUST_CONJECTURE` here means *unrefuted over every committed case within
the stated envelope*; attacking beyond the frozen data means new OpenFOAM
solves (phase 4 wires the scheduler to the solver).
