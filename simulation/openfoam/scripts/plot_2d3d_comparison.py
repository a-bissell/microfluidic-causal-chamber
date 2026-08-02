#!/usr/bin/env python3
"""2D vs 3D fidelity comparison for the millable-chip junction.

A 2D case models a mid-depth slice. A real square channel has four corners
that a droplet's rounded interface can never seal, so the continuous phase
bypasses the forming droplet through those corner gutters. 2D has no
corners, so it must route the bypass flow through side films instead --
which forces the droplet narrow and lets it grow longer before the neck
breaks. This script measures the difference.

Three filmstrip rows, each spanning ONE droplet period of its own case so
shapes are compared at matched phase, all on a common physical scale:

  2D                  the mid-depth slice, as modelled
  3D mid-plane        the same slice, in 3D (z = depth/2, the symmetry plane)
  3D near-wall        z ~ 0, where the corner gutters live

The near-wall row is the point of the figure: the difference between it and
the mid-plane row IS the corner-gutter effect, and 2D cannot represent it.

Usage:
    python3 plot_2d3d_comparison.py --case-2d DIR --case-3d DIR \
        --w-main-um 800 --period-2d 0.175 --period-3d 0.110 --out cmp.png
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from scipy.interpolate import griddata

sys.path.insert(0, str(Path(__file__).parent))
from extract_droplets import DropletExtractor  # noqa: E402

X_APPROACH_UM = 2000.0


def slice_frame(vtk_file, ex, w_um, z_target, nx=520, ny=150):
    """Resample alpha onto a regular (x, y) grid at ONE cell-centre z-plane.

    z_target is a depth in um, or None for a genuinely 2D mesh. The plane is
    snapped to the nearest layer of cell centres and exactly that layer is
    taken. Selecting a z *band* instead would hand griddata several cells
    sharing each (x, y) with different alpha; the triangulation then
    degenerates and the slice renders as speckle rather than as an
    interface.
    """
    coords, alpha = ex.read_vtk(vtk_file)
    xyz = coords * 1e6
    if z_target is not None:
        planes = np.unique(np.round(xyz[:, 2], 6))
        z = planes[np.argmin(np.abs(planes - z_target))]
        m = np.isclose(xyz[:, 2], z, atol=1e-6)
        xyz, alpha = xyz[m], alpha[m]
    x0, x1 = X_APPROACH_UM - 1.0 * w_um, X_APPROACH_UM + w_um + 4000.0
    y0, y1 = -0.35 * w_um, 1.30 * w_um
    gx, gy = np.meshgrid(np.linspace(x0, x1, nx), np.linspace(y0, y1, ny))
    grid = griddata(xyz[:, :2], alpha, (gx, gy), method="linear")
    return grid, (x0, x1, y0, y1)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--case-2d", type=Path, required=True)
    ap.add_argument("--case-3d", type=Path, required=True)
    ap.add_argument("--w-main-um", type=float, required=True)
    ap.add_argument("--period-2d", type=float, required=True, help="seconds")
    ap.add_argument("--period-3d", type=float, required=True, help="seconds")
    ap.add_argument("--n-frames", type=int, default=4)
    ap.add_argument("--out", default="cmp_2d3d.png")
    args = ap.parse_args()

    w = args.w_main_um
    ex2 = DropletExtractor(args.case_2d, w_main_m=w * 1e-6,
                           x_junction_m=(2000.0 + w) * 1e-6)
    ex3 = DropletExtractor(args.case_3d, w_main_m=w * 1e-6,
                           x_junction_m=(2000.0 + w) * 1e-6)
    f2, t2 = ex2.find_vtk_files(), ex2.resolve_times(ex2.find_vtk_files())
    f3, t3 = ex3.find_vtk_files(), ex3.resolve_times(ex3.find_vtk_files())

    # Half-depth domain: z = 0 is the milled floor, z = w/2 the mid-plane
    # symmetry. Both targets snap to the nearest cell-centre layer.
    rows = [
        ("2D\n(as modelled)", ex2, f2, np.asarray(t2), args.period_2d, None, "#1f77b4"),
        ("3D\nmid-plane", ex3, f3, np.asarray(t3), args.period_3d,
         w / 2, "#2166ac"),
        ("3D\nnear-wall", ex3, f3, np.asarray(t3), args.period_3d,
         0.0, "#b2182b"),
    ]

    n = args.n_frames
    fig = plt.figure(figsize=(3.2 * n, 2.15 * len(rows) + 4.4))
    gs = fig.add_gridspec(len(rows) + 1, n,
                          height_ratios=[1] * len(rows) + [2.1],
                          hspace=0.42, wspace=0.06)

    for r, (label, ex, files, times, period, ztarget, colour) in enumerate(rows):
        t_end = times[-1]
        picks = np.linspace(t_end - period, t_end, n)
        for c, tp in enumerate(picks):
            i = int(np.argmin(np.abs(times - tp)))
            grid, extent = slice_frame(files[i], ex, w, ztarget)
            ax = fig.add_subplot(gs[r, c])
            ax.imshow(grid, origin="lower", extent=extent, aspect="equal",
                      cmap="Blues", vmin=0, vmax=1, interpolation="bilinear")
            ax.set_xticks([]); ax.set_yticks([])
            for s in ax.spines.values():
                s.set_visible(False)
            ax.set_title(f"{(tp - picks[0]) * 1e3:.0f} ms into cycle",
                         fontsize=8, pad=2)
            if c == 0:
                ax.set_ylabel(label, fontsize=10, fontweight="bold",
                              color=colour)
            if c == n - 1:
                bx = extent[1] - 1250
                ax.add_patch(Rectangle((bx, -0.30 * w), 1000, 0.055 * w,
                                       color="0.25", zorder=5))
                ax.text(bx + 500, -0.22 * w, "1 mm", ha="center", fontsize=7,
                        color="0.25")

    # ---- correction bars ----------------------------------------------------
    # Everything normalised to the 2D baseline, with the withdrawn 400 um
    # figures alongside so the size of that error is visible rather than
    # merely asserted.
    labels = ["Slug\nlength", "Slug\nwidth", "Droplet\nrate", "Slug\nspeed",
              "Droplet\nvolume"]
    corrected = [0.871, 1.118, 1.591, 1.169, 0.629]
    withdrawn = [1.03, np.nan, 2.4, 1.43, np.nan]

    ax = fig.add_subplot(gs[len(rows), :])
    xs = np.arange(len(labels))
    ax.axhline(1.0, color="0.35", lw=1.3, ls="--", zorder=1)
    ax.bar(xs - 0.19, corrected, 0.36, color="#2166ac",
           label="corrected 800 µm (this run, matched operating point)")
    ax.bar(xs + 0.19, withdrawn, 0.36, color="#d6a0a0", hatch="//",
           edgecolor="#b2182b",
           label="withdrawn 400 µm (q = 0.50 vs reference 0.28)")
    for x, v in zip(xs, corrected):
        ax.text(x - 0.19, v + 0.04, f"×{v:.2f}", ha="center", fontsize=9,
                fontweight="bold", color="#2166ac")
    for x, v in zip(xs, withdrawn):
        if v == v:
            ax.text(x + 0.19, v + 0.04, f"×{v:.2f}", ha="center", fontsize=9,
                    color="#b2182b")
    ax.set_xticks(xs); ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("3D ÷ 2D", fontsize=10)
    ax.set_ylim(0, 2.75)
    ax.text(-0.45, 1.03, "2D baseline", fontsize=8, color="0.35")
    ax.legend(fontsize=8.5, frameon=False, loc="upper left")
    ax.grid(axis="y", alpha=0.25)
    ax.set_title("2D → 3D correction at a matched operating point "
                 "(q = 0.29, Ca = 0.032)", fontsize=11)

    fig.suptitle(f"{w:.0f} µm milled chip — what the 2D shortcut costs\n"
                 "corner gutters let oil bypass the forming droplet: shorter, "
                 "wider, faster, more frequent", fontsize=13, y=0.995)
    fig.savefig(args.out, dpi=140, bbox_inches="tight")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
