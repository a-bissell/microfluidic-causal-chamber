#!/usr/bin/env python3
"""Protocol-driven time-series runs for the T-junction causal chamber.

The physical causal chambers collect data via SET/WAIT/MSR protocols: a
single long experiment whose actuators step through a schedule, not many
independent cold-start experiments. This script builds (and optionally
runs) the simulation analog: one interFoam case per "chain" whose inlet
pressures follow a piecewise-constant time table (`uniformTotalPressure`),
visiting many setpoints in one run. Compared to independent sweep cases it
pays the startup transient once, gets per-droplet variance for free, and —
the real point — produces actuator-labelled *time series* suitable for
changepoint detection and temporal causal discovery, matching the
`wt_walks`/`lt_walks` dataset shape from the causal-chamber ecosystem.

Each chain directory contains `protocol.json` describing every segment
(setpoint, settle window, measure window); analyze_protocol_run.py uses it
to tag droplets with the active setpoint and to skip transition windows.

Usage (6 chains, each a random-order tour of the 5x5 grid):
    python3 protocol_run.py \\
        --base-case ../tjunction_2d_serpentine \\
        --output-dir ~/sweeps/protocol_v1 \\
        --p-cont 10000 11500 13000 14500 16000 \\
        --p-disp 2400 2700 3000 3300 3600 \\
        --mode grid-walk --chains 6 --concurrency 6

Modes:
    grid-walk  every (p_cont, p_disp) combination once, order shuffled
               per chain (seeded)
    random     --n-points setpoints sampled uniformly from the bounding
               box of the given pressure lists
"""
import argparse
import itertools
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

STEP_RAMP = 1e-4   # actuator step ramp time (s); ~real controller response


def replace_boundary_block(text: str, patch: str, new_body: str) -> str:
    """Replace the body of one named boundaryField block (brace-aware)."""
    lines = text.split("\n")
    out, i, replaced = [], 0, False
    while i < len(lines):
        line = lines[i]
        if not replaced and re.match(rf"\s*{re.escape(patch)}\s*$", line):
            out.append(line)
            depth = 0
            j = i + 1
            body_start = None
            while j < len(lines):
                depth += lines[j].count("{") - lines[j].count("}")
                if body_start is None and "{" in lines[j]:
                    body_start = j
                    out.append(lines[j])          # the opening brace line
                if depth == 0 and "}" in lines[j]:
                    out.append(new_body)
                    out.append(lines[j])          # the closing brace line
                    replaced = True
                    break
                j += 1
            if not replaced:
                raise ValueError(f"unterminated block '{patch}'")
            i = j + 1
            continue
        out.append(line)
        i += 1
    if not replaced:
        raise ValueError(f"boundary block '{patch}' not found")
    return "\n".join(out)


def pressure_table(segments, key) -> str:
    """Piecewise-constant Function1 table (steps ramp over STEP_RAMP)."""
    pts = []
    for seg in segments:
        pts.append((seg["t0"], seg[key]))
        pts.append((seg["t1"] - STEP_RAMP, seg[key]))
    rows = "\n".join(f"            ({t:.6f} {p:g})" for t, p in pts)
    return f"        table\n        (\n{rows}\n        )"


def make_schedule(args, rng):
    if args.mode == "grid-walk":
        pts = list(itertools.product(args.p_cont, args.p_disp))
        rng.shuffle(pts)
    else:
        lo_c, hi_c = min(args.p_cont), max(args.p_cont)
        lo_d, hi_d = min(args.p_disp), max(args.p_disp)
        pts = [(rng.uniform(lo_c, hi_c), rng.uniform(lo_d, hi_d))
               for _ in range(args.n_points)]
    segments, t = [], 0.0
    for k, (pc, pd) in enumerate(pts):
        settle = args.startup if k == 0 else args.settle
        t1 = t + settle + args.measure
        segments.append({
            "segment": k, "P_cont": round(float(pc), 1), "P_disp": round(float(pd), 1),
            "t0": round(t, 6), "t_measure": round(t + settle, 6), "t1": round(t1, 6),
        })
        t = t1
    return segments


def build_chain(chain_idx, args, base_case: Path):
    rng = np.random.default_rng(args.seed + chain_idx)
    segments = make_schedule(args, rng)
    d = args.output_dir / f"chain_{chain_idx}"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    for sub in ("0", "constant", "system"):
        shutil.copytree(base_case / sub, d / sub)

    p_rgh = d / "0" / "p_rgh"
    text = p_rgh.read_text()
    for patch, key in (("oil_inlet", "P_cont"), ("water_inlet", "P_disp")):
        body = (f"        // schedule from protocol.json ({len(segments)} segments)\n"
                f"        type            uniformTotalPressure;\n"
                f"        p0\n{pressure_table(segments, key)};\n"
                f"        value           uniform {segments[0][key]:g};")
        text = replace_boundary_block(text, patch, body)
    p_rgh.write_text(text)

    end_time = segments[-1]["t1"]
    ctrl = d / "system" / "controlDict"
    text = ctrl.read_text()
    text = re.sub(r"endTime\s+\S+;", f"endTime         {end_time:g};", text, count=1)
    text = re.sub(r"writeInterval\s+\S+;", f"writeInterval   {args.write_interval:g};",
                  text, count=1)
    ctrl.write_text(text)

    (d / "protocol.json").write_text(json.dumps({
        "chain": chain_idx, "seed": args.seed + chain_idx, "mode": args.mode,
        "settle": args.settle, "measure": args.measure, "startup": args.startup,
        "end_time": end_time, "segments": segments,
    }, indent=1))
    return d, end_time


def run_chain(chain_idx, args):
    d = args.output_dir / f"chain_{chain_idx}"
    t0 = time.time()
    cmd = [
        "docker", "run", "--rm", "--name", f"protocol-chain{chain_idx}",
        "--entrypoint", "bash", "-v", f"{d.resolve()}:/case", "-w", "/case", args.image, "-c",
        "source /usr/lib/openfoam/openfoam2306/etc/bashrc && "
        "blockMesh > log.blockMesh 2>&1 && setFields > log.setFields 2>&1 && "
        "interFoam > log.interFoam 2>&1 && foamToVTK -legacy > log.foamToVTK 2>&1",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    log = d / "log.interFoam"
    ok = r.returncode == 0 and log.exists() and "End" in log.read_text()[-2000:]
    print(f"[chain_{chain_idx}] {'OK' if ok else 'FAILED'} in {time.time()-t0:.0f}s", flush=True)
    if not ok:
        tail = r.stderr[-400:] if r.returncode != 0 else (log.read_text()[-400:] if log.exists() else "")
        print(f"  -> {tail.strip()[-300:]}", file=sys.stderr, flush=True)
    return ok


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base-case", required=True, type=Path,
                   help="Pressure-driven template case (tjunction_2d_serpentine)")
    p.add_argument("--output-dir", required=True, type=Path)
    p.add_argument("--p-cont", type=float, nargs="+", required=True)
    p.add_argument("--p-disp", type=float, nargs="+", required=True)
    p.add_argument("--mode", choices=["grid-walk", "random"], default="grid-walk")
    p.add_argument("--n-points", type=int, default=25, help="setpoints per chain (random mode)")
    p.add_argument("--chains", type=int, default=6)
    p.add_argument("--startup", type=float, default=0.03,
                   help="settle before the first setpoint's measure window (s)")
    p.add_argument("--settle", type=float, default=0.02,
                   help="post-step settle before each measure window (s)")
    p.add_argument("--measure", type=float, default=0.06, help="measure window (s)")
    p.add_argument("--write-interval", type=float, default=0.001)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--concurrency", type=int, default=6)
    p.add_argument("--image", default="opencfd/openfoam-default:2306")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not (args.base_case / "system" / "blockMeshDict").exists():
        p.error(f"--base-case {args.base_case} has no system/blockMeshDict")
    if "totalPressure" not in (args.base_case / "0" / "p_rgh").read_text():
        p.error("--base-case must be a pressure-driven case (totalPressure inlets)")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for i in range(args.chains):
        _, end_time = build_chain(i, args, args.base_case)
        print(f"built chain_{i}: endTime = {end_time:g} s", flush=True)
    (args.output_dir / "chains.json").write_text(json.dumps(
        {"chains": args.chains, "seed": args.seed, "mode": args.mode}, indent=1))

    if args.dry_run:
        print("Dry run: chains built, not executed.")
        return
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        status = list(ex.map(lambda i: run_chain(i, args), range(args.chains)))
    print(f"DONE: {sum(status)}/{len(status)} chains succeeded")
    if not all(status):
        sys.exit(1)


if __name__ == "__main__":
    main()
