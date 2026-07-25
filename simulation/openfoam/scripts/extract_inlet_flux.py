#!/usr/bin/env python3
"""Time series of volumetric flow rate through inlet patches.

Motivation — the cyclicity test. How the chamber is actuated determines
its causal graph:

  * Pressure sources (totalPressure inlets; hydrostatic columns or a
    regulator in hardware): the flow rates are EMERGENT. A forming droplet
    occludes the junction, raising continuous-phase resistance, raising
    junction pressure, which pushes back on BOTH inlets. Q_oil and Q_water
    are then mutually determined through the shared junction node, and the
    equilibrium causal graph contains a cycle.
  * Flow sources (fixedValue U inlets; syringe pumps in hardware): Q is
    imposed exogenously. The incoming edges are severed and the graph is
    close to a DAG — a syringe pump acts as a physical do-operator.

Same chip, same physics, two ground-truth graphs. This script measures the
observable signature: inlet flow rate that oscillates at the droplet
formation frequency (pressure-driven) versus flat by construction
(velocity-driven).

Flux per patch face is computed with the Newell method: the polygon's
normal vector has magnitude equal to its area, so the face contribution is
simply U · n_vec, no normalisation needed. Reported |Q| in µL/s
(2D cases are per the mesh's extruded depth).

Usage:
    python3 extract_inlet_flux.py <case_dir> [--patches oil_inlet water_inlet]
                                  [--output flux.csv]
"""
import argparse
import glob
import re
from pathlib import Path

import numpy as np
import pandas as pd
import vtk
from vtk.util import numpy_support


def resolve_times(case_dir: Path, n_files: int):
    """Physical times from the solver's time directories (VTK filenames are
    iteration indices, not seconds — the same trap fixed in
    extract_droplets.py)."""
    ts = []
    for d in case_dir.iterdir():
        if d.is_dir() and re.fullmatch(r"[0-9.eE+-]+", d.name):
            try:
                ts.append(float(d.name))
            except ValueError:
                pass
    ts.sort()
    if len(ts) == n_files:
        return ts
    print(f"  warning: {len(ts)} time dirs vs {n_files} VTK files; "
          "falling back to filename indices")
    return None


def patch_flux(path: str) -> float:
    """Volumetric flux through one patch snapshot, in m^3/s."""
    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(path)
    reader.Update()
    data = reader.GetOutput()
    if data.GetNumberOfCells() == 0:
        reader = vtk.vtkUnstructuredGridReader()
        reader.SetFileName(path)
        reader.Update()
        data = reader.GetOutput()

    cd = data.GetCellData()
    u_arr = None
    for i in range(cd.GetNumberOfArrays()):
        if cd.GetArrayName(i) == "U":
            u_arr = numpy_support.vtk_to_numpy(cd.GetArray(i))
    if u_arr is None:
        raise ValueError(f"no cell-centred U in {path}")

    total = 0.0
    for c in range(data.GetNumberOfCells()):
        cell = data.GetCell(c)
        pts = np.array([cell.GetPoints().GetPoint(i)
                        for i in range(cell.GetNumberOfPoints())])
        # Newell: |n_vec| == polygon area, so flux = U . n_vec
        n_vec = 0.5 * np.sum(np.cross(pts, np.roll(pts, -1, axis=0)), axis=0)
        total += float(np.dot(u_arr[c], n_vec))
    return total


def series(case_dir: Path, patch: str):
    files = sorted(glob.glob(str(case_dir / "VTK" / patch / "*.vtk")),
                   key=lambda f: float(re.findall(r"_(\d+)\.vtk$", f)[0]))
    if not files:
        raise FileNotFoundError(f"no VTK for patch '{patch}' in {case_dir}")
    return files, np.array([patch_flux(f) for f in files])


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("case_dir", type=Path)
    p.add_argument("--patches", nargs="+", default=["oil_inlet", "water_inlet"])
    p.add_argument("--output", type=Path, default=None)
    args = p.parse_args()

    cols = {}
    times = None
    for patch in args.patches:
        files, q = series(args.case_dir, patch)
        if times is None:
            times = resolve_times(args.case_dir, len(files))
            if times is None:
                times = [float(re.findall(r"_(\d+)\.vtk$", f)[0]) for f in files]
        cols[f"Q_{patch}_uL_s"] = np.abs(q) * 1e9   # m^3/s -> µL/s
    df = pd.DataFrame({"time": times, **cols})

    out = args.output or (args.case_dir / "inlet_flux.csv")
    df.to_csv(out, index=False)
    print(f"wrote {out}  ({len(df)} frames)")
    for c in cols:
        v = df[c].values
        # skip the startup transient for the summary statistics
        tail = v[len(v) // 3:]
        print(f"  {c}: mean {tail.mean():.3f}, CV {100*tail.std()/tail.mean():.2f}%, "
              f"range {tail.min():.3f}–{tail.max():.3f}")


if __name__ == "__main__":
    main()
