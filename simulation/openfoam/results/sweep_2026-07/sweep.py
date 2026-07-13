#!/usr/bin/env python3
"""Concurrent Docker-based parametric sweep for the T-junction case.

Grid over inlet velocities (U_oil x U_water) spanning Ca = 0.016-0.048 and
Q_disp/Q_cont = 0.083-0.75, plus one pressure-driven pilot (850/650 Pa).
Template: the verified coarse-mesh (7.5 um) scratch case.
"""
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SCRATCH = Path("/private/tmp/claude-501/-Users-app13-Documents-GitHub-robolab-microfluidic-causal-chamber/35b24bfc-0a90-4db4-8b6a-b9ffd2b0a9df/scratchpad")
REPO_CASE = Path("/Users/app13/Documents/GitHub/robolab/microfluidic-causal-chamber/simulation/openfoam/tjunction_2d")
TEMPLATE_SYSTEM = SCRATCH / "run2d" / "system"   # coarse mesh + relaxed solver
SWEEP = SCRATCH / "sweep"
IMAGE = "opencfd/openfoam-default:2306"

MU_OIL, SIGMA = 0.048, 0.03
W_MAIN, W_DISP = 150e-6, 75e-6

U_OIL_VALS = [0.01, 0.02, 0.03]
U_WATER_VALS = [0.005, 0.01, 0.015]


def make_cases():
    cases = []
    for uo in U_OIL_VALS:
        for uw in U_WATER_VALS:
            q_ratio = (uw * W_DISP) / (uo * W_MAIN)
            # ~3 droplet periods + startup; period ~ L_slug*w_main/(uw*w_disp)
            l_est = W_MAIN * (1 + q_ratio)
            period = l_est * W_MAIN / (uw * W_DISP)
            end_time = min(0.10, max(0.04, round(0.01 + 3 * period, 3)))
            cases.append({
                "name": f"uo{int(uo*1000)}_uw{int(uw*1000)}",
                "mode": "velocity", "U_oil": uo, "U_water": uw,
                "Ca": MU_OIL * uo / SIGMA, "q_ratio": q_ratio,
                "endTime": end_time,
            })
    cases.append({
        "name": "pilot_p850_650", "mode": "pressure",
        "P_cont": 850.0, "P_disp": 650.0,
        "Ca": None, "q_ratio": None, "endTime": 0.06,
    })
    return cases


def sed(path, pattern, repl):
    s = path.read_text()
    s2 = re.sub(pattern, repl, s)
    assert s2 != s or re.search(pattern, s), f"pattern missing in {path}: {pattern}"
    path.write_text(s2)


def build_case(c):
    d = SWEEP / c["name"]
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    shutil.copytree(REPO_CASE / "0", d / "0")          # pristine BCs
    shutil.copytree(REPO_CASE / "constant", d / "constant")
    shutil.copytree(TEMPLATE_SYSTEM, d / "system")     # coarse mesh, tuned dicts
    sed(d / "system" / "controlDict", r"endTime\s+\S+;", f"endTime         {c['endTime']};")

    if c["mode"] == "velocity":
        sed(d / "0" / "U", r"value           uniform \(0\.02 0 0\);",
            f"value           uniform ({c['U_oil']} 0 0);")
        sed(d / "0" / "U", r"value           uniform \(0 -0\.01 0\);",
            f"value           uniform (0 -{c['U_water']} 0);")
    else:
        # pressure-driven pilot: totalPressure inlets + pressure-derived velocity
        u = (d / "0" / "U").read_text()
        u = u.replace("""        type            fixedValue;
        value           uniform (0.02 0 0);""",
"""        type            pressureInletOutletVelocity;
        value           uniform (0 0 0);""")
        u = u.replace("""        type            fixedValue;
        value           uniform (0 -0.01 0);""",
"""        type            pressureInletOutletVelocity;
        value           uniform (0 0 0);""")
        (d / "0" / "U").write_text(u)
        p = (d / "0" / "p_rgh").read_text()
        for patch, val in (("oil_inlet", c["P_cont"]), ("water_inlet", c["P_disp"])):
            p = re.sub(
                patch + r"\n    \{\n(?:        //.*\n)*        type            fixedFluxPressure;\n        value           uniform 0;",
                patch + "\n    {\n        type            totalPressure;\n"
                f"        p0              uniform {val};\n"
                f"        value           uniform {val};", p)
        assert "totalPressure" in p, "pressure BC substitution failed"
        (d / "0" / "p_rgh").write_text(p)
    return d


def run_case(c):
    d = SWEEP / c["name"]
    t0 = time.time()
    cmd = ["docker", "run", "--rm", "--name", f"sweep-{c['name']}",
           "--entrypoint", "bash", "-v", f"{d}:/case", "-w", "/case", IMAGE, "-c",
           "source /usr/lib/openfoam/openfoam2306/etc/bashrc && "
           "blockMesh > log.blockMesh 2>&1 && setFields > log.setFields 2>&1 && "
           "interFoam > log.interFoam 2>&1 && foamToVTK -legacy > log.foamToVTK 2>&1"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    ok = r.returncode == 0 and "End" in (d / "log.interFoam").read_text()[-2000:]
    print(f"[{c['name']}] {'OK' if ok else 'FAILED'} in {time.time()-t0:.0f}s", flush=True)
    return ok


def main():
    cases = make_cases()
    SWEEP.mkdir(exist_ok=True)
    for c in cases:
        build_case(c)
        print(f"built {c['name']} (endTime={c['endTime']})", flush=True)
    with ThreadPoolExecutor(max_workers=6) as ex:
        status = list(ex.map(run_case, cases))
    import json
    (SWEEP / "cases.json").write_text(json.dumps(cases, indent=1))
    print(f"DONE: {sum(status)}/{len(cases)} succeeded", flush=True)


if __name__ == "__main__":
    main()
