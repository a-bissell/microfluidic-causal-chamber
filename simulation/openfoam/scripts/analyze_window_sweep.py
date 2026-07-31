#!/usr/bin/env python3
"""Operating-window analysis for a pressure sweep: where does the chip still drip?

`analyze_pressure_sweep.py` answers "what are the droplet metrics across the
grid" using a static length/position filter. This script answers the narrower
question the hardware guide actually needs -- **over what range of column
heights does the chamber still form droplets** -- and it uses the track-based
extractor (`extract_mature_droplets.py`), which is the only one that reliably
distinguishes a detached slug from an attached, still-growing thread.

A cell is classified as:

  drips     >= 2 complete droplet tracks with a measurable formation gap.
            This is the working regime.
  marginal  1 complete track, or tracks whose lengths disagree by more than
            --spread-tol. Something forms, but the run is too short or the
            rhythm too irregular to call it periodic. Do NOT design an
            operating point here.
  no-drip   no complete tracks: water either never enters (drive below the
            capillary entry threshold 2*sigma/w) or never detaches
            (co-flowing / jetting rather than squeezing).

Geometry defaults follow the millable-chip family, where channel LENGTHS are
fixed and WIDTHS scale, so the junction ends at 2000 + w and the track-linking
distance must scale with (droplet speed x writeInterval) rather than with w.

Usage:
    python3 analyze_window_sweep.py /path/to/psweep600 --w-main-um 600 \
        --write-interval 0.005 --out-dir ../results/window600_2026-07
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap, BoundaryNorm

sys.path.insert(0, str(Path(__file__).parent))
from extract_mature_droplets import process  # noqa: E402

PA_PER_CM_H2O = 1000.0 * 9.81 / 100.0        # 98.1 Pa per cm of water column
SIGMA = 0.03                                  # N/m, as constant/transportProperties

CLASSES = ["no-drip", "marginal", "drips"]


def classify(summary, tracks, spread_tol):
    if summary.get("n_complete", 0) == 0:
        return "no-drip"
    if summary.get("n_complete", 0) < 2 or "formation_gap_ms" not in summary:
        return "marginal"
    L = np.asarray(tracks.L_um, dtype=float)
    if L.size >= 2 and (L.max() - L.min()) / np.median(L) > spread_tol:
        return "marginal"
    return "drips"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sweep_dir", type=Path)
    ap.add_argument("--w-main-um", type=float, required=True)
    ap.add_argument("--write-interval", type=float, required=True,
                    help="controlDict writeInterval (s); sets the track-linking distance")
    ap.add_argument("--speed-ceiling-mm-s", type=float, default=45.0,
                    help="Upper bound on plausible slug speed, for track linking")
    ap.add_argument("--spread-tol", type=float, default=0.15,
                    help="Max (max-min)/median slug length before a cell is 'marginal'")
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()

    w = args.w_main_um
    # A slug advances speed*writeInterval between frames. Linking on w would
    # be wrong in both directions: too permissive at fine write intervals
    # (chains separate droplets together) and too strict at coarse ones.
    max_advance = args.speed_ceiling_mm_s * 1e3 * args.write_interval
    x_junction = 2000.0 + w

    cases = json.loads((args.sweep_dir / "cases.json").read_text())
    rows = []
    for c in cases:
        d = args.sweep_dir / c["name"]
        log = d / "log.interFoam"
        if not log.exists() or "End" not in log.read_text()[-2000:]:
            print(f"  {c['name']}: not finished, skipped", flush=True)
            continue
        summary, tracks = process(d, w, x_junction,
                                  growth_threshold_um=0.05 * w,
                                  min_track_frames=3,
                                  max_advance_um=max_advance,
                                  min_length_um=0.2 * w)
        verdict = classify(summary, tracks, args.spread_tol)
        gap = summary.get("formation_gap_ms", np.nan)
        rows.append({
            "name": c["name"],
            "P_cont_Pa": c["P_cont"], "P_disp_Pa": c["P_disp"],
            "P_cont_cmH2O": round(c["P_cont"] / PA_PER_CM_H2O, 2),
            "P_disp_cmH2O": round(c["P_disp"] / PA_PER_CM_H2O, 2),
            "verdict": verdict,
            "n_droplets": summary.get("n_complete", 0),
            "L_um": summary.get("L_um_median", np.nan),
            "L_over_w": summary.get("L_over_w", np.nan),
            "period_ms": gap,
            "f_Hz": 1000.0 / gap if gap == gap and gap else np.nan,
        })
        print(f"  {c['name']}: {verdict}  n={rows[-1]['n_droplets']} "
              f"L/w={rows[-1]['L_over_w']:.3f}" if rows[-1]["L_over_w"] == rows[-1]["L_over_w"]
              else f"  {c['name']}: {verdict}", flush=True)

    df = pd.DataFrame(rows)
    if df.empty:
        print("no finished cases")
        return

    out_dir = args.out_dir or args.sweep_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "window_results.csv", index=False)

    n = len(df)
    counts = df.verdict.value_counts().to_dict()
    print(f"\n{n} finished cases: " +
          ", ".join(f"{counts.get(k, 0)} {k}" for k in reversed(CLASSES)))
    # Only a COMPLETE grid licenses a window claim. On partial data the
    # finished cases are whichever ones the scheduler happened to reach
    # first, which is not a rectangle -- reporting its bounding box as "the
    # window" would overstate what has been measured.
    if counts.get("drips", 0) == n and n == len(cases):
        pcs, pds = sorted(df.P_cont_cmH2O.unique()), sorted(df.P_disp_cmH2O.unique())
        print(f"Whole grid drips -- window is at least "
              f"{pcs[0]}-{pcs[-1]} cm oil x {pds[0]}-{pds[-1]} cm water; "
              f"its edges are OUTSIDE this sweep and remain unmeasured.")
    elif n < len(cases):
        print(f"PARTIAL: {n}/{len(cases)} cases finished -- no window claim yet.")

    # ---- figure: verdict map + the two response surfaces -------------------
    pc = np.array(sorted(df.P_cont_Pa.unique()))
    pd_ = np.array(sorted(df.P_disp_Pa.unique()))
    def grid(col):
        g = np.full((len(pd_), len(pc)), np.nan)
        for _, r in df.iterrows():
            g[np.where(pd_ == r.P_disp_Pa)[0][0], np.where(pc == r.P_cont_Pa)[0][0]] = r[col]
        return g

    vmap = np.full((len(pd_), len(pc)), np.nan)
    for _, r in df.iterrows():
        vmap[np.where(pd_ == r.P_disp_Pa)[0][0],
             np.where(pc == r.P_cont_Pa)[0][0]] = CLASSES.index(r.verdict)

    fig, axes = plt.subplots(1, 3, figsize=(16.5, 4.8))
    ext = [-0.5, len(pc) - 0.5, -0.5, len(pd_) - 0.5]
    panels = [
        ("Regime", vmap, ListedColormap(["#b2182b", "#f0c419", "#2166ac"]), None),
        ("Slug length L/w", grid("L_over_w"), "viridis", "{:.2f}"),
        ("Droplet rate (Hz)", grid("f_Hz"), "magma", "{:.1f}"),
    ]
    for ax, (title, g, cmap, fmt) in zip(axes, panels):
        kw = dict(norm=BoundaryNorm([-0.5, 0.5, 1.5, 2.5], 3)) if fmt is None else {}
        im = ax.imshow(g, origin="lower", extent=ext, aspect="auto", cmap=cmap, **kw)
        ax.set_xticks(range(len(pc)))
        ax.set_yticks(range(len(pd_)))
        ax.set_xticklabels([f"{v:.0f}\n{v/PA_PER_CM_H2O:.1f} cm" for v in pc], fontsize=8)
        ax.set_yticklabels([f"{v:.0f}\n{v/PA_PER_CM_H2O:.1f} cm" for v in pd_], fontsize=8)
        ax.set_xlabel("P_cont (Pa / cm H₂O)")
        ax.set_ylabel("P_disp (Pa / cm H₂O)")
        ax.set_title(title)
        for i in range(len(pd_)):
            for j in range(len(pc)):
                v = g[i, j]
                if v != v:
                    continue
                txt = CLASSES[int(v)] if fmt is None else fmt.format(v)
                ax.text(j, i, txt, ha="center", va="center", fontsize=8,
                        color="white" if fmt is None else "w",
                        bbox=None)
        if fmt is not None:
            fig.colorbar(im, ax=ax, fraction=0.045)
    # mark the reference point (grid centre)
    for ax in axes:
        ax.plot(len(pc) // 2, len(pd_) // 2, marker="*", ms=16, mfc="none",
                mec="white", mew=1.8)

    cap = (2 * SIGMA / (w * 1e-6))
    fig.suptitle(f"{w:.0f} µm chip — operating window "
                 f"(★ = reference point; capillary entry threshold {cap:.0f} Pa "
                 f"= {cap/PA_PER_CM_H2O:.1f} cm H₂O)", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(out_dir / "window_map.png", dpi=140)
    print(f"wrote {out_dir}/window_results.csv and window_map.png")


if __name__ == "__main__":
    main()
