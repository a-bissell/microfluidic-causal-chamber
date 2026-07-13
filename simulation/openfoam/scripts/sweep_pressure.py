#!/usr/bin/env python3
"""Concurrent Docker-based pressure sweep for the T-junction causal chamber.

Portable version of the ad-hoc script used for the 2026-07 sweeps (see
results/psweep_2026-07/psweep.py) — paths, grid, concurrency, and image are
all CLI flags instead of hardcoded, so this runs unchanged on a laptop or a
many-core Linux/WSL2 box.

Requires only Docker (no local OpenFOAM install): each case builds and runs
in its own `opencfd/openfoam-default` container. Cases are embarrassingly
parallel (independent single-threaded solvers on a small mesh), so wall time
scales close to linearly with concurrency up to your physical core count —
see the concurrency guidance below.

Usage:
    python3 sweep_pressure.py \\
        --base-case ../tjunction_2d_serpentine \\
        --output-dir ./sweep_out \\
        --p-cont 10000 11500 13000 14500 16000 \\
        --p-disp 2400 2700 3000 3300 3600 \\
        --concurrency 12

    # Repeated runs with small actuation noise (for a causal-chamber
    # dataset's P_*_meas columns; deterministic given --seed):
    python3 sweep_pressure.py --base-case ... --output-dir ... \\
        --p-cont 10000 13000 16000 --p-disp 2400 3000 3600 \\
        --repeats 3 --noise-frac 0.02

Concurrency guidance: interFoam here is single-threaded and the mesh
(~5,500 cells) is far too small for multi-core solves to help a single
case, so set --concurrency to your physical (not logical/SMT) core count,
minus 1-2 for the OS. A Ryzen 9 7900X (12 cores) -> ~12; this M4 Mac Mini
(4 performance + 6 efficiency cores, run through Docker Desktop's VM) is
why the default is conservative.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    import numpy as np
except ImportError:
    print("numpy not found. Install with: pip install numpy", file=sys.stderr)
    sys.exit(1)


def warn_if_slow_fs(path: Path) -> None:
    resolved = str(path.resolve())
    if resolved.lower().startswith("/mnt/"):
        print(
            f"WARNING: {path} resolves to {resolved}, which looks like a "
            "Windows drive mounted into WSL2 (/mnt/c/...). OpenFOAM writes "
            "thousands of small per-timestep files per case; the 9p bridge "
            "to NTFS is dramatically slower than WSL2's own ext4 filesystem "
            "for this access pattern. Use a path under your WSL2 home "
            "(e.g. ~/sweeps/...) instead.",
            file=sys.stderr,
        )


def patch_boundary_value(text: str, patch: str, field: str, new_value: float) -> str:
    """Replace `p0`/`value` numeric literals inside one named boundaryField block.

    Brace-counting rather than a single regex: the boundary blocks contain
    free-form comments (including numbers, e.g. "3 mm x 75 um resistor")
    that a naive regex could also match.
    """
    lines = text.split("\n")
    out = []
    in_block = False
    depth = 0
    found = 0
    for line in lines:
        if not in_block and re.match(rf"\s*{re.escape(patch)}\s*$", line):
            in_block = True
        if in_block:
            depth += line.count("{") - line.count("}")
            if re.match(r"\s*(p0|value)\s+uniform\s+[-0-9.eE]+\s*;", line):
                key = "p0" if line.strip().startswith("p0") else "value"
                indent = line[: len(line) - len(line.lstrip())]
                line = f"{indent}{key:<15} uniform {new_value:g};"
                found += 1
            if depth == 0 and "}" in line:
                in_block = False
        out.append(line)
    if found == 0:
        raise ValueError(f"boundary block '{patch}' (field {field}) not found or has no p0/value")
    return "\n".join(out)


def make_cases(args):
    rng = np.random.default_rng(args.seed)
    cases = []
    for pc in args.p_cont:
        for pd in args.p_disp:
            for rep in range(args.repeats):
                pc_actual, pd_actual = pc, pd
                if args.repeats > 1:
                    pc_actual = pc * (1 + rng.normal(0, args.noise_frac))
                    pd_actual = pd * (1 + rng.normal(0, args.noise_frac))
                name = f"pc{pc/1000:g}k_pd{pd/1000:g}k"
                if args.repeats > 1:
                    name += f"_r{rep}"
                cases.append({
                    "name": name, "P_cont_nominal": pc, "P_disp_nominal": pd,
                    "P_cont": round(pc_actual, 1), "P_disp": round(pd_actual, 1),
                    "repeat": rep,
                })
    return cases


def build_case(c, base_case: Path, output_dir: Path, end_time, write_interval):
    d = output_dir / c["name"]
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    for sub in ("0", "constant", "system"):
        shutil.copytree(base_case / sub, d / sub)

    p_rgh = d / "0" / "p_rgh"
    text = p_rgh.read_text()
    text = patch_boundary_value(text, "oil_inlet", "p0", c["P_cont"])
    text = patch_boundary_value(text, "oil_inlet", "value", c["P_cont"])
    text = patch_boundary_value(text, "water_inlet", "p0", c["P_disp"])
    text = patch_boundary_value(text, "water_inlet", "value", c["P_disp"])
    p_rgh.write_text(text)

    ctrl = d / "system" / "controlDict"
    text = ctrl.read_text()
    if end_time is not None:
        text = re.sub(r"endTime\s+\S+;", f"endTime         {end_time};", text, count=1)
    if write_interval is not None:
        text = re.sub(r"writeInterval\s+\S+;", f"writeInterval   {write_interval};", text, count=1)
    ctrl.write_text(text)
    return d


def run_case(c, output_dir: Path, image: str):
    d = output_dir / c["name"]
    t0 = time.time()
    container = f"sweep-{c['name']}".replace(".", "p")
    cmd = [
        "docker", "run", "--rm", "--name", container,
        "--entrypoint", "bash", "-v", f"{d.resolve()}:/case", "-w", "/case", image, "-c",
        "source /usr/lib/openfoam/openfoam2306/etc/bashrc && "
        "blockMesh > log.blockMesh 2>&1 && setFields > log.setFields 2>&1 && "
        "interFoam > log.interFoam 2>&1 && foamToVTK -legacy > log.foamToVTK 2>&1",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    log = d / "log.interFoam"
    ok = r.returncode == 0 and log.exists() and "End" in log.read_text()[-2000:]
    elapsed = time.time() - t0
    print(f"[{c['name']}] {'OK' if ok else 'FAILED'} in {elapsed:.0f}s "
          f"(P_cont={c['P_cont']:.0f} Pa, P_disp={c['P_disp']:.0f} Pa)", flush=True)
    if not ok:
        tail = r.stderr[-500:] if r.returncode != 0 else (log.read_text()[-500:] if log.exists() else "(no log)")
        print(f"  -> {tail.strip()[-300:]}", file=sys.stderr, flush=True)
    return ok


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base-case", required=True, type=Path,
                   help="Template case dir (0/, constant/, system/) — typically tjunction_2d_serpentine")
    p.add_argument("--output-dir", required=True, type=Path)
    p.add_argument("--p-cont", type=float, nargs="+", required=True, help="Continuous-phase pressures (Pa)")
    p.add_argument("--p-disp", type=float, nargs="+", required=True, help="Dispersed-phase pressures (Pa)")
    p.add_argument("--repeats", type=int, default=1,
                   help="Repeats per (P_cont, P_disp) cell; >1 adds actuation noise (default: 1)")
    p.add_argument("--noise-frac", type=float, default=0.02,
                   help="Fractional stdev of per-repeat actuation noise (default: 0.02)")
    p.add_argument("--seed", type=int, default=0, help="RNG seed for repeat noise (default: 0)")
    p.add_argument("--end-time", type=float, default=None, help="Override controlDict endTime (s)")
    p.add_argument("--write-interval", type=float, default=None,
                   help="Override controlDict writeInterval (s); tighten to reduce droplet-frequency "
                        "undercount from extract_droplets.py's crossing counter")
    p.add_argument("--concurrency", type=int, default=6,
                   help="Concurrent Docker containers — set to physical core count minus 1-2 (default: 6)")
    p.add_argument("--image", default="opencfd/openfoam-default:2306")
    p.add_argument("--dry-run", action="store_true", help="Build cases without running them")
    args = p.parse_args()

    if not (args.base_case / "system" / "blockMeshDict").exists():
        p.error(f"--base-case {args.base_case} doesn't look like an OpenFOAM case (no system/blockMeshDict)")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    warn_if_slow_fs(args.output_dir)

    cases = make_cases(args)
    print(f"Building {len(cases)} case(s) "
          f"({len(args.p_cont)} x {len(args.p_disp)} grid, {args.repeats} repeat(s))...")
    for c in cases:
        build_case(c, args.base_case, args.output_dir, args.end_time, args.write_interval)
        print(f"  built {c['name']}", flush=True)
    (args.output_dir / "cases.json").write_text(json.dumps(cases, indent=1))

    if args.dry_run:
        print("Dry run: cases built, not executed.")
        return

    print(f"Running with concurrency={args.concurrency}...")
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        status = list(ex.map(lambda c: run_case(c, args.output_dir, args.image), cases))

    print(f"DONE: {sum(status)}/{len(cases)} succeeded")
    if not all(status):
        failed = [c["name"] for c, ok in zip(cases, status) if not ok]
        print(f"Failed: {', '.join(failed)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
