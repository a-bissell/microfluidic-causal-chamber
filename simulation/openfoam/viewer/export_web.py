#!/usr/bin/env python3
"""
export_web.py — turn OpenFOAM output into self-contained data for the viewer.

Two products, both written as plain `.js` files that assign a global (so the
viewer loads them with a <script> tag and works even from file://, no server
and no fetch/CORS needed):

  1. 2D alpha.water field frames  ->  data/twod_frames.js   (window.MCC2D)
     Reads the legacy-VTK series a case emits (foamToVTK -legacy), resamples the
     unstructured alpha field onto a regular grid once (the mesh is static, so
     the grid->cell map is built a single time and reused per frame), quantises
     to uint8, and base64-packs each frame. Cells outside the channel are marked
     with a sentinel so the viewer can draw the T-junction walls.

  2. Droplet metrics from a sweep CSV  ->  data/metrics.js   (window.MCCMETRICS)

Usage:
  export_web.py twod    <case_dir>   [--nx 200] [--out data/twod_frames.js]
  export_web.py metrics <sweep.csv>  [--out data/metrics.js]

Run with the venv that has vtk + numpy + scipy (see the viewer README).
"""
import argparse, base64, csv, json, re, sys
from pathlib import Path

import numpy as np


# ---------------------------------------------------------------- 2D frames ---
def _read_vtk(path):
    """Return (time_value, centroids_xy Nx2, alpha N) for one legacy .vtk."""
    import vtk
    from vtk.util.numpy_support import vtk_to_numpy

    reader = vtk.vtkGenericDataObjectReader()
    reader.SetFileName(str(path))
    reader.ReadAllScalarsOn()
    reader.Update()
    grid = reader.GetOutput()

    cc = vtk.vtkCellCenters()
    cc.SetInputData(grid)
    cc.Update()
    cen = vtk_to_numpy(cc.GetOutput().GetPoints().GetData())[:, :2]

    cd = grid.GetCellData()
    arr = cd.GetArray("alpha.water") or cd.GetArray("alpha_water")
    if arr is None:
        raise SystemExit(f"{path.name}: no alpha.water cell field")
    alpha = vtk_to_numpy(arr).astype(np.float32)

    tv = grid.GetFieldData().GetArray("TimeValue")
    t = float(tv.GetTuple1(0)) if tv else float("nan")
    return t, cen, alpha


def _vtk_series(case_dir):
    """Sorted list of internal-mesh .vtk files (top level of VTK/, not patches)."""
    vtkdir = Path(case_dir) / "VTK"
    if not vtkdir.is_dir():
        raise SystemExit(f"no VTK/ dir in {case_dir} — run foamToVTK -legacy first")
    files = [p for p in vtkdir.glob("*.vtk") if p.is_file()]
    if not files:
        raise SystemExit(f"no .vtk files in {vtkdir}")

    def idx(p):
        m = re.search(r"_(\d+)\.vtk$", p.name)
        return int(m.group(1)) if m else 0

    return sorted(files, key=idx)


def export_twod(case_dir, out, nx=200):
    from scipy.spatial import cKDTree

    files = _vtk_series(case_dir)
    t0, cen, a0 = _read_vtk(files[0])

    x0, x1 = float(cen[:, 0].min()), float(cen[:, 0].max())
    y0, y1 = float(cen[:, 1].min()), float(cen[:, 1].max())
    dx = (x1 - x0) / nx
    ny = max(1, int(round((y1 - y0) / dx)))

    # regular grid of cell CENTRES spanning the field bounds
    gx = x0 + (np.arange(nx) + 0.5) * dx
    gy = y0 + (np.arange(ny) + 0.5) * dx
    GX, GY = np.meshgrid(gx, gy)                       # (ny, nx), row 0 = bottom
    pts = np.column_stack([GX.ravel(), GY.ravel()])

    tree = cKDTree(cen)
    dist, nn = tree.query(pts, k=1)

    # a grid point is "outside the channel" if the nearest cell centroid is
    # farther than one mesh cell away -> lets the viewer paint the walls
    cell_h = np.median(tree.query(cen, k=2)[0][:, 1])   # nearest-neighbour spacing
    outside = dist > 1.05 * cell_h

    def pack(alpha):
        v = np.clip(alpha[nn], 0.0, 1.0)
        q = np.rint(v * 250).astype(np.uint8)
        q[outside] = 255                                # sentinel: wall / no data
        return base64.b64encode(q.tobytes()).decode("ascii")

    frames, times_ms = [], []
    for f in files:
        t, _, alpha = _read_vtk(f)
        frames.append(pack(alpha))
        times_ms.append(round(t * 1e3, 4))

    meta = dict(
        nx=nx, ny=ny,
        x0_mm=round(x0 * 1e3, 4), x1_mm=round(x1 * 1e3, 4),
        y0_mm=round(y0 * 1e3, 4), y1_mm=round(y1 * 1e3, 4),
        dx_um=round(dx * 1e6, 3), ncells=int(cen.shape[0]),
        times_ms=times_ms, wall=255,
    )
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {"meta": meta, "frames": frames}
    out.write_text("window.MCC2D = " + json.dumps(payload) + ";\n")
    kb = out.stat().st_size / 1024
    print(f"[twod] {len(frames)} frames  grid {nx}x{ny}  "
          f"t={times_ms[0]}..{times_ms[-1]} ms  -> {out}  ({kb:.0f} KB)")


# -------------------------------------------------------------------- metrics ---
def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def export_metrics(csv_path, out):
    rows = []
    with open(csv_path, newline="") as fh:
        for r in csv.DictReader(fh):
            # keep the clean, completed velocity-driven droplet points
            if r.get("mode") != "velocity" or r.get("status") != "ok":
                continue
            Ca, q = _f(r.get("Ca")), _f(r.get("q_ratio"))
            Lw, freq = _f(r.get("L_over_w")), _f(r.get("frequency_Hz"))
            deq = _f(r.get("d_eq_um"))
            if None in (Ca, q, Lw, freq):
                continue
            rows.append(dict(name=r.get("name"), Ca=round(Ca, 4), q=round(q, 4),
                             L_over_w=round(Lw, 4), freq_Hz=round(freq, 3),
                             d_eq_um=round(deq, 2) if deq else None))
    rows.sort(key=lambda d: (d["Ca"], d["q"]))
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {"source": Path(csv_path).name, "sweep": rows}
    out.write_text("window.MCCMETRICS = " + json.dumps(payload) + ";\n")
    print(f"[metrics] {len(rows)} points from {csv_path} -> {out}")


# ------------------------------------------------------------------------ main ---
def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p2 = sub.add_parser("twod")
    p2.add_argument("case_dir")
    p2.add_argument("--nx", type=int, default=200)
    p2.add_argument("--out", default="data/twod_frames.js")
    pm = sub.add_parser("metrics")
    pm.add_argument("csv_path")
    pm.add_argument("--out", default="data/metrics.js")
    a = ap.parse_args()
    if a.cmd == "twod":
        export_twod(a.case_dir, a.out, a.nx)
    else:
        export_metrics(a.csv_path, a.out)


if __name__ == "__main__":
    main()
