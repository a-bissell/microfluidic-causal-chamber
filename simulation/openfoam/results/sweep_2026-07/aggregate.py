#!/usr/bin/env python3
"""Aggregate sweep results, fit the Garstecki scaling law, make plots."""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SCRATCH = Path("/private/tmp/claude-501/-Users-app13-Documents-GitHub-robolab-microfluidic-causal-chamber/35b24bfc-0a90-4db4-8b6a-b9ffd2b0a9df/scratchpad")
SWEEP = SCRATCH / "sweep"
sys.path.insert(0, "/Users/app13/Documents/GitHub/robolab/microfluidic-causal-chamber/simulation/openfoam/scripts")
from extract_droplets import DropletExtractor  # noqa: E402

W_MAIN_UM = 150.0


def patch_mean_velocity(case_dir, patch, comp):
    """Mean |U_comp| on a patch from the last written time directory."""
    tdirs = sorted((float(d.name), d) for d in case_dir.iterdir()
                   if d.is_dir() and re.fullmatch(r"[0-9.e-]+", d.name)
                   and d.name != "0")
    if not tdirs:
        return np.nan
    txt = (tdirs[-1][1] / "U").read_text()
    m = re.search(patch + r"\s*\{[^}]*?value\s+nonuniform List<vector>\s*\n\d+\s*\(\n(.*?)\n\)",
                  txt, re.S)
    if not m:
        m2 = re.search(patch + r"\s*\{[^}]*?value\s+uniform \(([-0-9.e ]+)\)", txt, re.S)
        return abs(float(m2.group(1).split()[comp])) if m2 else np.nan
    vecs = re.findall(r"\(([-0-9.e]+) ([-0-9.e]+) ([-0-9.e]+)\)", m.group(1))
    vals = np.array([[float(a), float(b), float(c)] for a, b, c in vecs])
    return abs(vals[:, comp].mean())


def analyze_case(c):
    d = SWEEP / c["name"]
    row = dict(c)
    ok = (d / "log.interFoam").exists() and "End" in (d / "log.interFoam").read_text()[-2000:]
    row["status"] = "ok" if ok else "failed"
    if not ok:
        return row
    ex = DropletExtractor(d)
    df, summary = ex.process_case()
    row["frequency_Hz"] = summary["frequency_Hz"]
    row["n_detections"] = summary["n_droplets_total"]
    if df.empty:
        row["n_free_frames"] = 0
        row["U_oil_meas"] = patch_mean_velocity(d, "oil_inlet", 0)
        row["U_water_meas"] = patch_mean_velocity(d, "water_inlet", 1)
        return row
    # detached, fully-formed droplets in mid-outlet only
    free = df[(df["centroid_y"] < 150) & (df["length"] < 500)
              & (df["centroid_x"].between(700, 1450))]
    row["n_free_frames"] = len(free)
    if len(free):
        row["L_um"] = free["length"].median()
        row["w_um"] = free["width"].median()
        row["d_eq_um"] = free["d_equivalent"].median()
        row["L_over_w"] = row["L_um"] / W_MAIN_UM
    # realized inlet velocities (from solved fields; = imposed for velocity BCs)
    row["U_oil_meas"] = patch_mean_velocity(d, "oil_inlet", 0)
    row["U_water_meas"] = patch_mean_velocity(d, "water_inlet", 1)
    if c["mode"] == "pressure" and np.isfinite(row["U_oil_meas"]):
        row["Ca"] = 0.048 * row["U_oil_meas"] / 0.03
        if np.isfinite(row["U_water_meas"]) and row["U_oil_meas"] > 0:
            row["q_ratio"] = (row["U_water_meas"] * 75) / (row["U_oil_meas"] * 150)
    return row


def main():
    cases = json.loads((SWEEP / "cases.json").read_text())
    rows = [analyze_case(c) for c in cases]
    res = pd.DataFrame(rows)
    res.to_csv(SWEEP / "sweep_results.csv", index=False)
    print(res.drop(columns=["endTime"], errors="ignore").to_string(index=False))

    fit = res[(res["status"] == "ok") & res.get("L_over_w", pd.Series(dtype=float)).notna()
              & res["q_ratio"].notna()]
    if len(fit) >= 3:
        q, low = fit["q_ratio"].values, fit["L_over_w"].values
        alpha, intercept = np.polyfit(q, low, 1)
        pred = intercept + alpha * q
        ss_res = ((low - pred) ** 2).sum()
        ss_tot = ((low - low.mean()) ** 2).sum()
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
        print(f"\nGarstecki fit: L/w = {intercept:.2f} + {alpha:.2f} * (Q_disp/Q_cont)"
              f"   [expected: L/w = 1 + alpha*q, alpha ~ 1-3]   R^2 = {r2:.3f}")

        fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
        ax = axes[0]
        for uo, g in fit.groupby("U_oil"):
            ax.scatter(g["q_ratio"], g["L_over_w"], s=45,
                       label=f"U_oil = {uo*1000:.0f} mm/s (Ca = {0.048*uo/0.03:.3f})")
        qq = np.linspace(0, fit["q_ratio"].max() * 1.1, 50)
        ax.plot(qq, intercept + alpha * qq, "k--",
                label=f"fit: {intercept:.2f} + {alpha:.2f} q  (R2={r2:.2f})")
        ax.set_xlabel("Q_disp / Q_cont")
        ax.set_ylabel("L / w")
        ax.set_title("Slug length vs flow ratio (Garstecki scaling)")
        ax.legend(fontsize=8)

        ax = axes[1]
        okv = res[(res["status"] == "ok") & (res["mode"] == "velocity")]
        sc = ax.scatter(okv["Ca"], okv["q_ratio"], c=okv["frequency_Hz"],
                        s=80, cmap="viridis")
        for _, r in okv.iterrows():
            ax.annotate(f"{r['frequency_Hz']:.0f} Hz", (r["Ca"], r["q_ratio"]),
                        textcoords="offset points", xytext=(6, 4), fontsize=7)
        plt.colorbar(sc, ax=ax, label="droplet frequency (Hz)")
        ax.set_xlabel("Ca")
        ax.set_ylabel("Q_disp / Q_cont")
        ax.set_title("Formation frequency across the sweep")
        plt.tight_layout()
        plt.savefig(SWEEP / "sweep_summary.png", dpi=150)
        print(f"plot: {SWEEP / 'sweep_summary.png'}")


if __name__ == "__main__":
    main()
