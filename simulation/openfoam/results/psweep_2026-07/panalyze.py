#!/usr/bin/env python3
"""Analyze the pressure sweep: droplet metrics per (P_cont, P_disp) cell."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SCRATCH = Path("/private/tmp/claude-501/-Users-app13-Documents-GitHub-robolab-microfluidic-causal-chamber/35b24bfc-0a90-4db4-8b6a-b9ffd2b0a9df/scratchpad")
SWEEP = SCRATCH / "psweep"
sys.path.insert(0, "/Users/app13/Documents/GitHub/robolab/microfluidic-causal-chamber/simulation/openfoam/scripts")
from extract_droplets import DropletExtractor  # noqa: E402

rows = []
for c in json.loads((SWEEP / "cases.json").read_text()):
    d = SWEEP / c["name"]
    row = dict(c)
    ex = DropletExtractor(d)
    df, summary = ex.process_case()
    row["frequency_Hz"] = summary["frequency_Hz"]
    if not df.empty:
        free = df[(df["centroid_y"] < 150) & (df["length"] < 500)
                  & (df["centroid_x"].between(700, 1450))]
        row["n_free"] = len(free)
        if len(free):
            row["L_um"] = free["length"].median()
            row["L_over_w"] = row["L_um"] / 150.0
        # droplet advection speed from leading-droplet displacement
        allfree = df[(df["centroid_y"] < 150) & (df["length"] < 500)].sort_values("time")
        speeds = []
        groups = list(allfree.groupby("time"))
        for (t0, g0), (t1, g1) in zip(groups[:-1], groups[1:]):
            dx = g1["centroid_x"].max() - g0["centroid_x"].max()
            if 0 < dx < 200:
                speeds.append(dx * 1e-6 / (t1 - t0))
        if speeds:
            row["v_drop_mm_s"] = np.median(speeds) * 1000
    rows.append(row)

res = pd.DataFrame(rows)
res.to_csv(SWEEP / "psweep_results.csv", index=False)
cols = ["name", "P_cont", "P_disp", "frequency_Hz", "n_free", "L_um", "L_over_w", "v_drop_mm_s"]
print(res[[c for c in cols if c in res.columns]].to_string(index=False))

# response maps
pcs = sorted(res["P_cont"].unique())
pds = sorted(res["P_disp"].unique())
def grid(col):
    g = np.full((len(pds), len(pcs)), np.nan)
    for _, r in res.iterrows():
        g[pds.index(r["P_disp"]), pcs.index(r["P_cont"])] = r.get(col, np.nan)
    return g

fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
for ax, col, title in zip(axes, ["frequency_Hz", "L_over_w", "v_drop_mm_s"],
                          ["Droplet frequency (Hz)", "Slug length L/w", "Droplet speed (mm/s)"]):
    g = grid(col)
    im = ax.imshow(g, origin="lower", cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(pcs)), [f"{p/1000:.0f}" for p in pcs])
    ax.set_yticks(range(len(pds)), [f"{p/1000:.1f}" for p in pds])
    ax.set_xlabel("P_cont (kPa)")
    ax.set_ylabel("P_disp (kPa)")
    ax.set_title(title, fontsize=10)
    for i in range(len(pds)):
        for j in range(len(pcs)):
            if np.isfinite(g[i, j]):
                ax.text(j, i, f"{g[i, j]:.2f}" if col == "L_over_w" else f"{g[i, j]:.0f}",
                        ha="center", va="center", color="white", fontsize=8)
    plt.colorbar(im, ax=ax)
plt.suptitle("Pressure-actuated response maps — serpentine T-junction (P_cont x P_disp)", fontsize=11)
plt.tight_layout()
plt.savefig(SWEEP / "psweep_maps.png", dpi=150)
print("plot:", SWEEP / "psweep_maps.png")
