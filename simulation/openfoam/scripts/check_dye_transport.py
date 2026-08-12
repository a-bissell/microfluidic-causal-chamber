#!/usr/bin/env python3
"""Pre-flight check: did the three dye scalars actually get transported?

WHY THIS EXISTS
---------------
The dye fields come from three scalarTransport function objects. If those fail
to load, OpenFOAM's behaviour depends on the build: some versions abort, others
print a warning and carry on. The second case is the dangerous one -- the run
completes, makes perfectly good droplets, writes dye fields that are still
sitting at their initial values, and looks entirely successful. Nothing
surfaces until the analysis produces compositions that are exactly the seeded
values, which is a result that looks plausible.

That failure was not hypothetical when this was written: the local
verification build (Ubuntu 24.04, OpenFOAM 1912.200626-2build3) aborts on ANY
function object with 'error in IOstream "sha1"', a GCC-13 rebuild bug in
OSHA1stream. So the function objects in this case have never been run
anywhere. This script is how you find out in two minutes instead of eight
hours.

WHAT IT CHECKS
--------------
1. The three dye fields exist in the output at all.
2. They have CHANGED since t=0. This is the real test -- fields that are
   present but frozen mean the solver registered them and never advected them.
3. sum_i dye_i == alpha.water, cell by cell. Equal by construction; the
   mismatch is the passive scalars' leakage and is the number that later
   bounds how much of any measured bias could be numerical.

Usage:
    python3 check_dye_transport.py <case_dir>

Intended for a deliberately short run (endTime ~0.02 s). It does not need
droplets -- only evidence that the scalars are moving and staying consistent.
"""
import re
import sys
from pathlib import Path

import numpy as np

try:
    import vtk
    from vtk.util import numpy_support
except ImportError:
    sys.exit("VTK not found. pip install vtk")

DYES = ["dye1", "dye2", "dye3"]
WATER = "alpha.water"


def read(vtk_file):
    r = vtk.vtkUnstructuredGridReader()
    r.SetFileName(str(vtk_file))
    r.ReadAllScalarsOn()
    r.Update()
    cd = r.GetOutput().GetCellData()
    names = {cd.GetArrayName(i) for i in range(cd.GetNumberOfArrays())}
    got = {}
    for n in DYES + [WATER]:
        if n in names:
            got[n] = numpy_support.vtk_to_numpy(cd.GetArray(n))
    return got, names


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    case = Path(sys.argv[1]).resolve()
    vtk_dir = case / "VTK"
    if not vtk_dir.is_dir():
        sys.exit(f"No VTK/ in {case}. Run: foamToVTK -legacy")

    files = sorted(
        ((int(m.group(1)), f) for f in vtk_dir.glob("*.vtk")
         if (m := re.search(r"_(\d+)\.vtk$", f.name))),
        key=lambda p: p[0])
    if len(files) < 2:
        sys.exit(f"Need at least two time outputs in {vtk_dir}; found "
                 f"{len(files)}. Let the run write more than one step.")

    first, last = read(files[0][1])[0], read(files[-1][1])
    last, names = last[0], last[1]

    print(f"case: {case.name}")
    print(f"first output: {files[0][1].name}   last: {files[-1][1].name}\n")

    ok = True

    # --- 1. present at all --------------------------------------------------
    missing = [d for d in DYES if d not in last]
    if missing:
        print(f"FAIL  dye fields missing from output: {missing}")
        print(f"      arrays found: {sorted(names)}")
        print(f"      The scalarTransport function objects did not run. Check")
        print(f"      log.solver for 'Unknown function', a libs load error, or")
        print(f"      the 'sha1' IOstream abort.")
        sys.exit(1)
    print("PASS  all three dye fields present in the output")

    # --- 2. actually moving -------------------------------------------------
    # A frozen field is the silent failure: registered, written, never advected.
    for d in DYES:
        if d not in first:
            continue
        delta = float(np.abs(last[d] - first[d]).max())
        if delta < 1e-12:
            print(f"FAIL  {d} is byte-identical to its initial condition "
                  f"(max change {delta:.1e})")
            print(f"      The field is registered but not being transported --")
            print(f"      the exact silent failure this check exists for.")
            ok = False
        else:
            print(f"PASS  {d} has evolved since t=0 (max change {delta:.3f})")

    # --- 3. consistency with alpha.water ------------------------------------
    if WATER not in last:
        print(f"FAIL  {WATER} missing; cannot check closure")
        sys.exit(1)
    s = sum(last[d] for d in DYES)
    w = last[WATER]
    # Compare only where there is water to speak of; the oil bulk is 0 == 0
    # and would dilute the error into meaninglessness.
    m = w > 0.01
    if not m.any():
        print("WARN  no water in the domain at the last output; closure "
              "not meaningful yet")
    else:
        rel = float(np.abs(s[m] - w[m]).sum() / w[m].sum())
        worst = float(np.abs(s[m] - w[m]).max())
        verdict = "PASS" if rel < 0.02 else "WARN"
        print(f"\n{verdict}  dye closure: sum(dye) vs alpha.water over wet cells")
        print(f"      integrated relative error {rel:.3%}, worst cell {worst:.4f}")
        print(f"      This is the passive scalars' leakage. It BOUNDS how much")
        print(f"      of any composition bias measured later could be numerical")
        print(f"      rather than physical -- a core-vs-wall bias smaller than")
        print(f"      this cannot be claimed.")
        if rel >= 0.02:
            print(f"      Above 2% this early is a lot. Consider --dx 20.")

    print("\n" + ("READY: dye transport works. Proceed to the full 2D run."
                  if ok else
                  "NOT READY: fix the above before spending run time."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
