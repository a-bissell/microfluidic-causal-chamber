#!/usr/bin/env python3
"""Per-droplet composition for the encoder twin (tjunction_3d_encoder).

WHAT IT MEASURES
----------------
The encoder writes a code into each droplet by merging three dye streams at
flow rates (Q1, Q2, Q3) upstream of the T-junction. The symbol carried by a
droplet is its composition

    c_i = V_i / (V_1 + V_2 + V_3)

where V_i is the volume of water-of-type-i inside that droplet. The claim
under test is c_i == Q_i / sum(Q): that the junction chops the laminated
stream in proportion to what arrives, so the code is written faithfully.

WHY THIS IS NOT extract_droplets.py WITH EXTRA COLUMNS
------------------------------------------------------
Three differences, each of which would corrupt the composition if ignored:

1. VOLUME-WEIGHTED, NOT CELL-COUNTED. extract_droplets.py estimates area as
   n_cells * dx^2, which is fine for a length or an aspect ratio. A
   composition is a ratio of integrals of a field, so it needs
   sum(alpha_i * V_cell), with real cell volumes.

2. INTERFACE CELLS ARE INCLUDED. Thresholding at alpha > 0.5 to *find* a
   droplet is correct; integrating only over alpha > 0.5 is not. The
   interface shell holds real dye, and it is the part of the droplet nearest
   the wall -- which is exactly where a sampling bias would live. Discarding
   it would suppress the effect being measured. So the threshold locates the
   droplet, and the integral then runs over every cell in its x-window.

3. TRUNCATED DROPLETS ARE REJECTED, NOT MEASURED. A droplet straddling the
   outlet boundary has part of its volume outside the domain. Its length is
   merely wrong; its composition is wrong in a way that correlates with
   position, because the laminae are not uniformly distributed along the
   slug. Any droplet touching either end of the measurement window is
   dropped, and the count of rejections is reported.

WHAT THE OUTPUT IS FOR
----------------------
One row per (time, droplet). analyze_encoder.py consumes this and does the
statistics; this script deliberately does no averaging, so that the rejection
of startup droplets (those formed before inlet-derived water reaches the
junction) is a visible, auditable step rather than a hidden default.

Usage:
    python3 extract_droplet_dye.py <case_dir> [--output dye.csv]

Geometry is read from the case's geometry.json, written by gen_blockmesh.py.
Nothing is hardcoded: the 400 um sweep in results/mill_2026-07 produced a
directory of garbage because extract_droplets.py carried the previous chip's
dimensions as defaults, and that failure mode is designed out here -- if
geometry.json is missing, this exits rather than guessing.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import vtk
    from vtk.util import numpy_support
except ImportError:
    sys.exit("VTK not found. pip install vtk")


DYES = ["dye1", "dye2", "dye3"]
WATER = "alpha.water"


def load_geometry(case_dir):
    """Read the generator's manifest. No fallback -- see module docstring."""
    for candidate in (case_dir / "geometry.json",
                      case_dir.parent / "geometry.json"):
        if candidate.exists():
            return json.loads(candidate.read_text())
    sys.exit(f"geometry.json not found next to {case_dir}. Re-run "
             f"gen_blockmesh.py in the case directory; this script will not "
             f"guess the geometry.")


def find_vtk_files(case_dir):
    """Time-ordered legacy .vtk files. foamToVTK must have been run -legacy."""
    vtk_dir = case_dir / "VTK"
    if not vtk_dir.is_dir():
        sys.exit(f"No VTK/ directory in {case_dir}. Run: foamToVTK -legacy")

    files = []
    for f in vtk_dir.glob("*.vtk"):
        m = re.search(r"_(\d+)\.vtk$", f.name)
        if m:
            files.append((int(m.group(1)), f))
    if not files:
        sys.exit(f"No indexed .vtk files in {vtk_dir}. ESI foamToVTK defaults "
                 f"to the .vtm/.vtu tree; it needs -legacy.")
    files.sort()
    return files


def read_fields(vtk_file):
    """Cell centres, cell volumes, and each water phase fraction."""
    reader = vtk.vtkUnstructuredGridReader()
    reader.SetFileName(str(vtk_file))
    reader.ReadAllScalarsOn()
    reader.Update()
    data = reader.GetOutput()

    centres = vtk.vtkCellCenters()
    centres.SetInputData(data)
    centres.Update()
    pts = centres.GetOutput().GetPoints()
    coords = numpy_support.vtk_to_numpy(pts.GetData())

    # Real cell volumes rather than dx^3: the composition is a ratio of
    # volume integrals, and assuming uniformity here would silently break any
    # future graded mesh.
    sizes = vtk.vtkCellSizeFilter()
    sizes.SetInputData(data)
    sizes.ComputeVolumeOn()
    sizes.ComputeAreaOff()
    sizes.ComputeLengthOff()
    sizes.ComputeVertexCountOff()
    sizes.Update()
    vol_arr = sizes.GetOutput().GetCellData().GetArray("Volume")
    if vol_arr is None:
        sys.exit(f"vtkCellSizeFilter produced no Volume array for {vtk_file}")
    vols = numpy_support.vtk_to_numpy(vol_arr)

    cd = data.GetCellData()
    available = {cd.GetArrayName(i) for i in range(cd.GetNumberOfArrays())}
    alphas = {}
    for name in DYES:
        if name not in available:
            sys.exit(f"{name} missing from {vtk_file.name}. Found: "
                     f"{sorted(available)}. The dye fields come from the three "
                     f"scalarTransport function objects in system/controlDict; "
                     f"if only alpha.water is present the solver ran without "
                     f"them (check log.solver for function-object errors).")
        alphas[name] = numpy_support.vtk_to_numpy(cd.GetArray(name))

    if WATER not in available:
        sys.exit(f"{WATER} missing from {vtk_file.name}.")
    water = numpy_support.vtk_to_numpy(cd.GetArray(WATER))
    return coords, vols, alphas, water


def detect(coords, vols, alphas, water, geom, threshold=0.5, halo_cells=3):
    """Locate detached droplets in the outlet and integrate each phase.

    Droplets are separated by gaps along x -- valid here because this is slug
    flow in a straight outlet, so droplets are strictly ordered and never
    side by side. That assumption breaks if the regime ever goes to jetting
    or parallel flow; check the filmstrip before trusting these numbers on a
    new operating point.
    """
    dx = geom["dx_um"] * 1e-6
    x_lo = geom["x_outlet_um"][0] * 1e-6      # junction downstream edge
    x_hi = geom["x_outlet_um"][1] * 1e-6      # domain outlet

    # Restrict to the outlet channel: the water leg and merge node upstream
    # are full of water that is not a droplet.
    in_outlet = (coords[:, 0] > x_lo) & (coords[:, 1] < geom["y_channel_um"][1] * 1e-6)
    core = in_outlet & (water > threshold)
    if not core.any():
        return [], 0

    xs = np.sort(coords[core, 0])
    # A gap wider than 2 cells separates two droplets.
    splits = np.where(np.diff(xs) > 2.0 * dx)[0]
    starts = np.concatenate([[0], splits + 1])
    ends = np.concatenate([splits + 1, [len(xs)]])

    droplets, rejected = [], 0
    for s, e in zip(starts, ends):
        if e - s < 5:                       # numerical speck, not a droplet
            continue
        x0, x1 = xs[s], xs[e - 1]

        # Reject anything touching either end of the measurement window; its
        # integral is truncated and its composition would be biased.
        if x0 <= x_lo + dx or x1 >= x_hi - dx:
            rejected += 1
            continue

        # Integrate over the droplet's x-window PLUS a halo, so the diffuse
        # interface shell is captured rather than clipped at alpha = 0.5.
        win = in_outlet & (coords[:, 0] >= x0 - halo_cells * dx) \
                        & (coords[:, 0] <= x1 + halo_cells * dx)

        v_i = np.array([float(np.sum(alphas[dye][win] * vols[win])) for dye in DYES])
        v_tot = float(v_i.sum())
        if v_tot <= 0:
            continue

        ys = coords[win & (water > threshold), 1]
        rec = {
            "x_min_um": x0 * 1e6, "x_max_um": x1 * 1e6,
            "x_centroid_um": float(np.average(coords[win, 0],
                                              weights=water[win] * vols[win])) * 1e6,
            "L_um": (x1 - x0) * 1e6,
            "w_um": (ys.max() - ys.min()) * 1e6 if len(ys) else np.nan,
            "V_nL": v_tot * 1e12,
            "n_cells": int(win.sum()),
        }
        for k in range(3):
            rec[f"V{k+1}_nL"] = v_i[k] * 1e12
            rec[f"c{k+1}"] = v_i[k] / v_tot

        # THE ERROR BAR. sum_i dye_i == alpha.water by construction, but
        # scalarTransport gives the dyes no MULES compression, so the identity
        # is not numerically enforced -- the dyes leak across the oil-water
        # interface on the mixture flux. The relative mismatch between the
        # dye-summed water volume and the alpha-integrated water volume is
        # therefore a direct measure of how much this method has lost, and it
        # bounds how much of any composition bias could be numerical rather
        # than physical. Recorded per droplet, never assumed small.
        v_water = float(np.sum(water[win] * vols[win]))
        rec["dye_closure_err"] = (abs(v_tot - v_water) / v_water
                                  if v_water > 0 else np.nan)
        droplets.append(rec)

    return droplets, rejected


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("case_dir", type=Path)
    ap.add_argument("--output", type=Path, default=None)
    ap.add_argument("--threshold", type=float, default=0.5,
                    help="Water fraction defining the droplet core (location "
                         "only; the integral always spans the full window).")
    ap.add_argument("--halo-cells", type=int, default=3,
                    help="Cells of margin added each side of a droplet before "
                         "integrating, to capture the interface shell.")
    args = ap.parse_args()

    case = args.case_dir.resolve()
    geom = load_geometry(case)
    files = find_vtk_files(case)
    print(f"{len(files)} VTK files; w = {geom['w_main_um']} um, "
          f"{'2D' if geom['two_d'] else '3D'}, commanded c = "
          f"{[round(v, 4) for v in geom['commanded_c']]}")

    # geometry.json is written by gen_blockmesh.py and is overwritten every
    # time it runs -- including by the OTHER variant, since the 2D baseline and
    # the 3D case share one generator and one output path. Pairing a 3D
    # manifest with a 2D run (or vice versa) is a mistake that costs hours: the
    # commanded composition and outlet window still look sane, so the run
    # analyses without complaint and produces wrong volumes and a wrong
    # dimensionality label. Cell count catches it immediately -- the two
    # variants differ by the depth cell count, 68000 vs 6800 at the defaults.
    probe = vtk.vtkUnstructuredGridReader()
    probe.SetFileName(str(files[0][1]))
    probe.Update()
    n_vtk = probe.GetOutput().GetNumberOfCells()
    if n_vtk != geom["n_cells"]:
        sys.exit(f"geometry.json says {geom['n_cells']} cells "
                 f"({'2D' if geom['two_d'] else '3D'}) but the VTK output has "
                 f"{n_vtk}. The manifest does not belong to this run -- it was "
                 f"most likely overwritten by a later gen_blockmesh.py call for "
                 f"the other variant. Copy the manifest that was generated "
                 f"alongside this case's mesh, or re-run the generator with the "
                 f"arguments this case was built with.")

    # foamToVTK indexes files by write number, not by time. Reconstruct the
    # physical time from the case's time directories so the transit-time cut
    # in analyze_encoder.py operates on seconds, not indices.
    times = sorted(float(d.name) for d in case.iterdir()
                   if re.fullmatch(r"\d+\.?\d*(e-?\d+)?", d.name) and d.is_dir())

    rows, total_rejected = [], 0
    for idx, (n, f) in enumerate(files):
        coords, vols, alphas, water = read_fields(f)
        drops, rejected = detect(coords, vols, alphas, water, geom,
                                 args.threshold, args.halo_cells)
        total_rejected += rejected
        t = times[idx] if idx < len(times) else np.nan
        for j, d in enumerate(drops):
            rows.append({"time_s": t, "vtk_index": n, "droplet_in_frame": j, **d})

    if not rows:
        sys.exit("No droplets detected. Check the run reached droplet "
                 "formation, and that the outlet window in geometry.json is "
                 "correct.")

    df = pd.DataFrame(rows)
    out = args.output or (case / "droplet_dye.csv")
    df.to_csv(out, index=False)

    print(f"\n{len(df)} droplet observations across {df.time_s.nunique()} frames "
          f"({total_rejected} rejected as truncated at a window edge)")
    print(f"written: {out}")
    if "dye_closure_err" in df:
        print(f"max dye-closure error: {df.dye_closure_err.max():.2%} "
              f"(sum of dyes vs alpha.water per droplet; this bounds how much\n"
              f" of any composition bias could be numerical)")
    print("\nNOT yet filtered for startup transient -- run analyze_encoder.py.")


if __name__ == "__main__":
    main()
