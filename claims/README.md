# claims/ — the chamber's claims layer (lakatos engine port, phase 1)

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
| `battery.py` | the 12-claim registry + expected-disposition acceptance ledger |

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
