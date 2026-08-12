# Nightly chunked 3D encoder run

Runs the 3D multiphase encoder case (`runs/encoder_3d_mp/`, 66k cells) in
overnight chunks so the M4 mini is free during the day. OpenFOAM checkpoints
natively — the solver writes complete time directories, and restart resumes from
the last one — so a multi-day job splits into nightly sessions with no lost work.

Three commands, all non-interactive and safe to drive from cron / Claude
schedule / cowork:

| command | when | what it does |
|---|---|---|
| `./run_tonight.sh` | at night | starts fresh, or resumes from the last checkpoint. Detached. Idempotent (no-op if already running). |
| `./stop_clean.sh` | in the morning | asks the solver to write a final checkpoint and exit (`stopAt writeNow`); falls back to `docker stop` after 5 min. Last checkpoint always intact. |
| `./morning_check.sh` | after stopping | reconstructs the night's checkpoints, extracts droplets, prints **core-vs-wall ± SE** and a verdict. Exit 0 = keep going, 10 = decisive, stop. |

## The loop

```
night 1:  ./run_tonight.sh                 # fresh: mesh, seed, decompose, solve
morning:  ./stop_clean.sh && ./morning_check.sh
night 2:  ./run_tonight.sh                 # resumes automatically
...repeat until morning_check.sh exits 10 (decisive)
```

`morning_check.sh` is the decision point: it stops the loop when the corner
bias is **clearly nonzero** (3D effect confirmed) *or* **bounded tightly around
zero** (no effect > ~2%), whichever comes first — so you never run longer than
the physics needs. A large effect resolves in a few nights; only a near-zero
result needs the full n ≈ 34 (~4 s sim, ~7 nights).

## Scheduling notes

- **Idempotency:** `run_tonight.sh` no-ops if the container is already up, so a
  cron overlap is harmless. `stop_clean.sh` no-ops if nothing is running.
- **One run at a time:** fixed container name `encoder3d`.
- **Decomposition:** 4 ranks on the 4 performance cores. Do *not* raise to 10 —
  the efficiency cores stall the MPI ranks and it runs slower and less reliably.
- **Rate (measured):** ~48,000 s wall per simulated second on 4 ranks; ~0.5 s
  sim per 8 h night.
- **Disk:** `purgeWrite 0` keeps every checkpoint (needed to analyse composition
  over time). ~7 MB per write × ~900 writes ≈ 6 GB for a full run. Fine on the
  mini, but don't run it on a full disk.
- **Persistence:** the run lives in `runs/encoder_3d_mp/` which is **gitignored**
  — it survives across sessions but is never committed. These scripts are
  tracked; the multi-GB run data is not.

## Where the run lives (Aug 2026)

The completed run (t=3.0 s, n=23 — **no significant corner bias**) was archived
to the **Samsung T7** at `/Volumes/T7/robolab_runs/encoder_3d_mp/` to free the
internal disk. `runs/encoder_3d_mp.MOVED.txt` is a local pointer.

To resume it (toward the formal n≈40 bound): **move it back to internal first** —
Docker cannot bind-mount `/Volumes/T7` unless it is added to Docker Desktop →
Settings → Resources → File Sharing (that mount attempt hung the daemon once).
Then raise `endTime` and `./run_tonight.sh` resumes from the checkpoint.

## What the run is measuring

The 2D null passed (core-vs-wall ≈ 0). 3D adds channel corners where oil
intrudes. The question: does core-preferential sampling at the corners bias the
droplet code? `core-vs-wall = c2 − (c1+c3)/2`, which must be ≈ 0 in 2D and is
the whole signal in 3D. See `results/encoder_dye_2026-08/` for the 2D story and
`runs/encoder_3d_mp/README.md` for the case itself.

## Config touched for restart

In `runs/encoder_3d_mp/system/controlDict`: `startFrom latestTime`,
`runTimeModifiable yes`, `purgeWrite 0`, `stopAt endTime`, `endTime 4.5`
(ceiling; the decision rule stops earlier). MPI needs
`OMPI_ALLOW_RUN_AS_ROOT=1` in the container — set by the scripts, not the case.
