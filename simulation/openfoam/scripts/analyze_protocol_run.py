#!/usr/bin/env python3
"""Analyze protocol_run.py output: setpoint-tagged metrics + time series.

For every chain directory under --run-dir, reads protocol.json and the VTK
output, tags each output frame with the active protocol segment, and writes:

  - <run-dir>/protocol_results.csv   one row per (chain, segment): droplet
                                      metrics computed from the segment's
                                      *measure* window only (settle and
                                      step-transition frames excluded)
  - <run-dir>/timeseries.csv         one row per output frame per chain:
                                      active setpoints, droplet count,
                                      leading-droplet position, median
                                      slug length — the raw material for
                                      changepoint / temporal-causal work
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from extract_droplets import DropletExtractor  # noqa: E402

X_REF_UM = 1000.0    # crossing-count reference line (mid-outlet)
W_MAIN_UM = 150.0


def active_segment(t, segments):
    for seg in segments:
        if seg["t0"] <= t < seg["t1"]:
            return seg
    return segments[-1] if t >= segments[-1]["t1"] else None


def analyze_chain(chain_dir: Path):
    proto = json.loads((chain_dir / "protocol.json").read_text())
    segments = proto["segments"]
    log = chain_dir / "log.interFoam"
    if not (log.exists() and "End" in log.read_text()[-2000:]):
        print(f"  {chain_dir.name}: solver did not finish; skipping", file=sys.stderr)
        return [], []

    ex = DropletExtractor(chain_dir)
    df, _ = ex.process_case()

    # Frame times come from the solver's output times, NOT from detections:
    # frames with zero droplets are data (n_droplets = 0), not gaps.
    frames = ex.resolve_times(ex.find_vtk_files())
    if df.empty:
        df = pd.DataFrame(columns=["time", "centroid_x", "centroid_y",
                                   "length", "d_equivalent"])
    detached = df[(df["centroid_y"] < 150) & (df["length"] < 500)]

    ts_rows = []
    for t in frames:
        seg = active_segment(t, segments)
        g = detached[detached["time"] == t]
        ts_rows.append({
            "chain": proto["chain"], "time": t,
            "segment": seg["segment"] if seg else -1,
            "P_cont": seg["P_cont"] if seg else np.nan,
            "P_disp": seg["P_disp"] if seg else np.nan,
            "phase": ("measure" if seg and t >= seg["t_measure"] else "settle") if seg else "n/a",
            "n_droplets": len(g),
            "n_beyond_ref": int((g["centroid_x"] > X_REF_UM).sum()),
            "lead_x_um": g["centroid_x"].max() if len(g) else np.nan,
            "median_L_um": g["length"].median() if len(g) else np.nan,
        })
    ts = pd.DataFrame(ts_rows)

    seg_rows = []
    for seg in segments:
        m = ts[(ts["segment"] == seg["segment"]) & (ts["phase"] == "measure")]
        row = {
            "chain": proto["chain"], **{k: seg[k] for k in
                                        ("segment", "P_cont", "P_disp", "t0", "t_measure", "t1")},
            "n_frames": len(m),
        }
        if len(m) >= 2:
            crossings = np.maximum(np.diff(m["n_beyond_ref"].values), 0).sum()
            duration = m["time"].iloc[-1] - m["time"].iloc[0]
            row["frequency_Hz"] = crossings / duration if duration > 0 else np.nan
            mid = detached[detached["time"].isin(m["time"])
                           & detached["centroid_x"].between(700, 1450)]
            if len(mid):
                row["L_um"] = mid["length"].median()
                row["L_over_w"] = row["L_um"] / W_MAIN_UM
                row["d_eq_um"] = mid["d_equivalent"].median()
                row["n_droplet_obs"] = len(mid)
        seg_rows.append(row)
    return seg_rows, ts_rows


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run-dir", required=True, type=Path,
                   help="protocol_run.py --output-dir (contains chain_*/)")
    args = p.parse_args()

    chains = sorted(args.run_dir.glob("chain_*"))
    if not chains:
        p.error(f"no chain_* directories in {args.run_dir}")

    all_segs, all_ts = [], []
    for c in chains:
        print(f"analyzing {c.name}...")
        segs, ts = analyze_chain(c)
        all_segs += segs
        all_ts += ts

    res = pd.DataFrame(all_segs)
    res.to_csv(args.run_dir / "protocol_results.csv", index=False)
    pd.DataFrame(all_ts).to_csv(args.run_dir / "timeseries.csv", index=False)
    print(f"\nwrote {args.run_dir / 'protocol_results.csv'} ({len(res)} segments)")
    print(f"wrote {args.run_dir / 'timeseries.csv'} ({len(all_ts)} frames)")
    if len(res) and "L_over_w" in res.columns:
        ok = res["L_over_w"].notna().sum()
        print(f"segments with droplet metrics: {ok}/{len(res)}")


if __name__ == "__main__":
    main()
