#!/usr/bin/env python3
"""Measure droplet VOLUME, z-extent and wall contact directly from 3D VTK.

`extract_droplets.py` clusters on x and reports x- and y-extent. That is the
right tool for a 2D case and a systematically incomplete one for 3D: a droplet
can differ in depth, or in how much wall it touches, with identical length and
width. Two plausible explanations for the study D speed difference died here,
both because this script measured what the projection could not see:

  corner-gutter bypass  slug width is 0.95 w at BOTH theta = 120 and 160
  depth occupancy       z-extent is 720 um (0.90 w) at BOTH

and a third -- that ~20% of injected water was vanishing into a wall film,
inferred from droplet volume x rate falling short of the imposed flow rate --
died when the totals showed essentially all outlet water sitting in discrete
droplets. That shortfall was droplet-count granularity across a 4-to-5-droplet
run, not missing water.

What it does show: theta = 120 puts 4.4x more water in contact with the side
walls (26.2 nL vs 6.0 nL), which is the wetting effect the repo's old
"theta0 >= 150" rule was reaching for -- real, measurable, and nowhere near
the runaway film that rule implies.

Volumes are doubled throughout: tjunction_3d_mill models half the depth with a
symmetry plane at z = w/2.

Usage:
    python3 measure_3d_droplet_volume.py ~/sweeps/wetting/D_3d_theta/s30_t120 \\
        [--w-main-um 800] [--frames 25]
"""
import argparse
import contextlib
import io
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from extract_droplets import DropletExtractor  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("case_dir", type=Path)
    ap.add_argument("--w-main-um", type=float, default=800.0)
    ap.add_argument("--frames", type=int, default=25,
                    help="How many trailing frames to use (default: 25, i.e. the "
                         "fully-developed tail of a 0.6 s run)")
    ap.add_argument("--min-cells", type=int, default=200,
                    help="Smallest cluster counted as a droplet (default: 200)")
    args = ap.parse_args()

    w = args.w_main_um * 1e-6
    dx = w / 20.0                       # gen_blockmesh.py: DX = W_MAIN / 20
    cell_nl = (dx * 1e6) ** 3 / 1e6     # um^3 -> nL
    x_j = 2000e-6 + w

    ex = DropletExtractor(args.case_dir, w_main_m=w, x_junction_m=x_j)
    with contextlib.redirect_stdout(io.StringIO()):
        files = ex.find_vtk_files()

    vols, zs, ys, totals, walls = [], [], [], [], []
    for f in files[-args.frames:]:
        with contextlib.redirect_stdout(io.StringIO()):
            coords, alpha = ex.read_vtk(f)
        # Clear of the junction (still-forming water) and of the outlet plane
        # (slugs mid-exit, whose measured volume is meaningless).
        m = (coords[:, 0] > x_j + 0.5 * w) & (coords[:, 0] < x_j + 4000e-6 - 400e-6)
        c, a = coords[m], alpha[m]
        wat = c[a > 0.5]
        if len(wat) < 50:
            continue
        totals.append(len(wat) * cell_nl * 2)
        yv = wat[:, 1]
        walls.append(((yv < dx) | (yv > w - dx)).sum() * cell_nl * 2)

        xs = np.sort(np.unique(np.round(wat[:, 0], 9)))
        gaps = np.where(np.diff(xs) > 2 * dx)[0]
        starts = np.concatenate([[0], gaps + 1])
        ends = np.concatenate([gaps + 1, [len(xs)]])
        for s, e in zip(starts, ends):
            sel = wat[(wat[:, 0] >= xs[s]) & (wat[:, 0] <= xs[e - 1])]
            if len(sel) < args.min_cells:
                continue
            vols.append(len(sel) * cell_nl * 2)
            zs.append((sel[:, 2].max() - sel[:, 2].min()) * 1e6 * 2)
            ys.append((sel[:, 1].max() - sel[:, 1].min()) * 1e6)

    if not vols:
        print("no droplets found")
        return
    print(f"{args.case_dir.name}  ({len(vols)} droplet observations over "
          f"{len(totals)} frames)")
    print(f"  volume            {np.median(vols):7.1f} nL")
    print(f"  z-extent          {np.median(zs):7.0f} um  "
          f"({np.median(zs)/(w*1e6):.2f} w)")
    print(f"  y-extent          {np.median(ys):7.0f} um  "
          f"({np.median(ys)/(w*1e6):.2f} w)")
    print(f"  total in outlet   {np.median(totals):7.1f} nL")
    print(f"  touching y-walls  {np.median(walls):7.1f} nL  "
          f"({100*np.median(walls)/np.median(totals):.0f}% of total)")


if __name__ == "__main__":
    main()
