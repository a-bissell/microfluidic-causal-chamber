#!/usr/bin/env python3
"""Extract droplet metrics from a sweep_pressure.py output dir and summarize.

Reads <output-dir>/cases.json (written by sweep_pressure.py), runs
extract_droplets.py's DropletExtractor on every case, and writes:

  - <output-dir>/results.csv           per-case metrics
  - <output-dir>/causal_dataset.csv    causal-chamber variable-schema export
                                        (actuator/observable columns, one row
                                        per case; P_*_meas = the actually-
                                        applied noisy pressure when the sweep
                                        used --repeats > 1)
  - <output-dir>/response_maps.png     frequency / L-over-w / speed heatmaps
                                        (only when the grid has >1 unique
                                        P_cont and P_disp value)

Usage:
    python3 analyze_pressure_sweep.py --sweep-dir ./sweep_out

    # Non-default geometry (e.g. tjunction_2d_mill, 400 um channels with a
    # feed serpentine before the junction) MUST override the geometry
    # parameters below, or every downstream number is silently wrong:
    # channel height caps the free-droplet y filter, the outlet window and
    # frequency reference line are meaningless if they land upstream of the
    # junction, and a length cap tuned for ~200 um droplets truncates larger
    # slugs from a wider channel.
    python3 analyze_pressure_sweep.py --sweep-dir ./mill_sweep_out \\
        --w-main-um 400 --x-junction-um 2400 --x-ref-um 4000 \\
        --outlet-x-min-um 2400 --outlet-x-max-um 6400 --free-length-max-um 2000
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from extract_droplets import DropletExtractor  # noqa: E402


def analyze_case(c, sweep_dir: Path, geom):
    d = sweep_dir / c["name"]
    row = dict(c)
    log = d / "log.interFoam"
    ok = log.exists() and "End" in log.read_text()[-2000:]
    row["status"] = "ok" if ok else "failed"
    if not ok:
        return row

    ex = DropletExtractor(d, w_main_m=geom["w_main_um"] * 1e-6,
                          x_junction_m=geom["x_junction_um"] * 1e-6 if geom["x_junction_um"] is not None else None,
                          x_ref_m=geom["x_ref_um"] * 1e-6 if geom["x_ref_um"] is not None else None)
    df, summary = ex.process_case()
    row["frequency_Hz"] = summary["frequency_Hz"]
    row["n_detections"] = summary["n_droplets_total"]
    if df.empty:
        row["n_free"] = 0
        return row

    in_outlet = (df["centroid_y"] < geom["w_main_um"]) & (df["length"] < geom["free_length_max_um"])
    free = df[in_outlet & df["centroid_x"].between(geom["outlet_x_min_um"], geom["outlet_x_max_um"])]
    row["n_free"] = len(free)
    if len(free):
        row["L_um"] = free["length"].median()
        row["w_um"] = free["width"].median()
        row["d_eq_um"] = free["d_equivalent"].median()
        row["L_over_w"] = row["L_um"] / geom["w_main_um"]
        row["polydispersity"] = (free["d_equivalent"].std() / free["d_equivalent"].mean()
                                  if free["d_equivalent"].mean() > 0 else np.nan)

    allfree = df[in_outlet].sort_values("time")
    speeds = []
    groups = list(allfree.groupby("time"))
    for (t0, g0), (t1, g1) in zip(groups[:-1], groups[1:]):
        dx = g1["centroid_x"].max() - g0["centroid_x"].max()
        if 0 < dx < geom["speed_dx_max_um"]:
            speeds.append(dx * 1e-6 / (t1 - t0))
    if speeds:
        row["v_drop_mm_s"] = np.median(speeds) * 1000
    return row


def make_response_maps(res: pd.DataFrame, out_path: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    for col in ("frequency_Hz", "L_over_w", "v_drop_mm_s"):
        if col not in res.columns:
            res[col] = np.nan
    agg = res[res["status"] == "ok"].groupby(["P_cont_nominal", "P_disp_nominal"]).agg(
        frequency_Hz=("frequency_Hz", "mean"),
        L_over_w=("L_over_w", "mean"),
        v_drop_mm_s=("v_drop_mm_s", "mean"),
    ).reset_index()

    pcs = sorted(agg["P_cont_nominal"].unique())
    pds = sorted(agg["P_disp_nominal"].unique())
    if len(pcs) < 2 or len(pds) < 2:
        print("Grid has <2 unique values on an axis; skipping response maps.")
        return

    def grid(col):
        g = np.full((len(pds), len(pcs)), np.nan)
        for _, r in agg.iterrows():
            g[pds.index(r["P_disp_nominal"]), pcs.index(r["P_cont_nominal"])] = r.get(col, np.nan)
        return g

    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8 + 0.3 * max(0, len(pcs) - 3)))
    for ax, col, title in zip(axes, ["frequency_Hz", "L_over_w", "v_drop_mm_s"],
                               ["Droplet frequency (Hz)", "Slug length L/w", "Droplet speed (mm/s)"]):
        g = grid(col)
        im = ax.imshow(g, origin="lower", cmap="viridis", aspect="auto")
        ax.set_xticks(range(len(pcs)), [f"{p/1000:.1f}" for p in pcs])
        ax.set_yticks(range(len(pds)), [f"{p/1000:.1f}" for p in pds])
        ax.set_xlabel("P_cont (kPa)")
        ax.set_ylabel("P_disp (kPa)")
        ax.set_title(title, fontsize=10)
        for i in range(len(pds)):
            for j in range(len(pcs)):
                if np.isfinite(g[i, j]):
                    ax.text(j, i, f"{g[i, j]:.2f}" if col == "L_over_w" else f"{g[i, j]:.0f}",
                            ha="center", va="center", color="white", fontsize=7)
        plt.colorbar(im, ax=ax)
    plt.suptitle("Pressure-actuated response maps", fontsize=11)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    print(f"wrote {out_path}")


def make_causal_dataset(res: pd.DataFrame, out_path: Path):
    rows = []
    for i, r in res.iterrows():
        rows.append({
            "counter": i,
            "config": "pressure_driven",
            # Sweep rows are all observational: repeat-to-repeat actuation
            # noise is measurement/actuator variation, not a do-intervention.
            # Set 1 here only for rows generated by an explicit intervention
            # protocol (none exist in sweep_pressure.py output yet).
            "intervention": 0,
            "P_cont": r.get("P_cont_nominal", r["P_cont"]),
            "P_disp": r.get("P_disp_nominal", r["P_disp"]),
            "P_out": 0,
            "P_cont_meas": r["P_cont"],   # actually-applied pressure (may include repeat noise)
            "P_disp_meas": r["P_disp"],
            "P_out_meas": 0,
            "f_droplet": r.get("frequency_Hz", np.nan),
            "d_droplet": r.get("d_eq_um", np.nan),
            "L_droplet": r.get("L_um", np.nan),
            "w_droplet": r.get("w_um", np.nan),
            "n_droplets": r.get("n_free", 0),
            "polydispersity": r.get("polydispersity", np.nan),
            "v_droplet": r.get("v_drop_mm_s", np.nan),
            "regime": "dripping" if r.get("frequency_Hz", 0) and r["frequency_Hz"] > 0 else "unknown",
            "status": r["status"],
        })
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"wrote {out_path}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sweep-dir", required=True, type=Path)
    p.add_argument("--w-main-um", type=float, default=150.0,
                   help="Main channel width in um (default: the original 150 um case's)")
    p.add_argument("--x-junction-um", type=float, default=None,
                   help="X position (um) marking the end of the T-junction; "
                        "default reproduces the original case's derivation")
    p.add_argument("--x-ref-um", type=float, default=None,
                   help="Frequency-counter reference line (um); default is 1000 (the "
                        "original case's mid-outlet point)")
    p.add_argument("--outlet-x-min-um", type=float, default=700.0)
    p.add_argument("--outlet-x-max-um", type=float, default=1450.0)
    p.add_argument("--free-length-max-um", type=float, default=500.0,
                   help="Upper length cap distinguishing a real droplet from a "
                        "still-attached feed thread; scale up for wider channels")
    p.add_argument("--speed-dx-max-um", type=float, default=200.0,
                   help="Max plausible per-frame advection distance for tracking "
                        "the same droplet across frames")
    args = p.parse_args()
    geom = {"w_main_um": args.w_main_um, "x_junction_um": args.x_junction_um,
            "x_ref_um": args.x_ref_um, "outlet_x_min_um": args.outlet_x_min_um,
            "outlet_x_max_um": args.outlet_x_max_um,
            "free_length_max_um": args.free_length_max_um,
            "speed_dx_max_um": args.speed_dx_max_um}

    cases = json.loads((args.sweep_dir / "cases.json").read_text())
    rows = [analyze_case(c, args.sweep_dir, geom) for c in cases]
    res = pd.DataFrame(rows)
    res.to_csv(args.sweep_dir / "results.csv", index=False)

    n_ok = (res["status"] == "ok").sum()
    print(f"\n{n_ok}/{len(res)} cases ok")
    cols = ["name", "P_cont", "P_disp", "status", "frequency_Hz", "L_over_w", "v_drop_mm_s"]
    print(res[[c for c in cols if c in res.columns]].to_string(index=False))

    make_causal_dataset(res, args.sweep_dir / "causal_dataset.csv")
    if n_ok >= 4:
        make_response_maps(res, args.sweep_dir / "response_maps.png")


if __name__ == "__main__":
    main()
