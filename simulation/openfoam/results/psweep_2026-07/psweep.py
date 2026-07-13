#!/usr/bin/env python3
"""Pressure-actuated sweep on the serpentine T-junction case.

3x3 grid of (P_cont, P_disp) around the verified reference point
(13 kPa, 3 kPa). This is the causal-chamber actuation model: pressures
are the actuators, droplet metrics the observables.
"""
import json
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SCRATCH = Path("/private/tmp/claude-501/-Users-app13-Documents-GitHub-robolab-microfluidic-causal-chamber/35b24bfc-0a90-4db4-8b6a-b9ffd2b0a9df/scratchpad")
TEMPLATE = Path("/Users/app13/Documents/GitHub/robolab/microfluidic-causal-chamber/simulation/openfoam/tjunction_2d_serpentine")
SWEEP = SCRATCH / "psweep"
IMAGE = "opencfd/openfoam-default:2306"

P_CONT_VALS = [10000, 13000, 16000]
P_DISP_VALS = [2400, 3000, 3600]
END_TIME = 0.08   # >= 2 droplet periods even in the slow-water corner


def make_cases():
    return [{"name": f"pc{pc//1000}k_pd{pd}",
             "mode": "pressure", "P_cont": float(pc), "P_disp": float(pd),
             "endTime": END_TIME}
            for pc in P_CONT_VALS for pd in P_DISP_VALS]


def build_case(c):
    d = SWEEP / c["name"]
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    for sub in ("0", "constant", "system"):
        shutil.copytree(TEMPLATE / sub, d / sub)
    p = (d / "0" / "p_rgh").read_text()
    p, n1 = re.subn(r"p0              uniform 13000;", f"p0              uniform {c['P_cont']};", p)
    p, n2 = re.subn(r"value           uniform 13000;", f"value           uniform {c['P_cont']};", p)
    p, n3 = re.subn(r"p0              uniform 3000;", f"p0              uniform {c['P_disp']};", p)
    p, n4 = re.subn(r"value           uniform 3000;", f"value           uniform {c['P_disp']};", p)
    assert n1 == n2 == n3 == n4 == 1, f"BC substitution failed for {c['name']}"
    (d / "0" / "p_rgh").write_text(p)
    ctrl = d / "system" / "controlDict"
    ctrl.write_text(re.sub(r"endTime\s+\S+;", f"endTime         {c['endTime']};",
                           ctrl.read_text(), count=1))
    return d


def run_case(c):
    d = SWEEP / c["name"]
    t0 = time.time()
    cmd = ["docker", "run", "--rm", "--name", f"psweep-{c['name']}",
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
        print(f"built {c['name']}", flush=True)
    with ThreadPoolExecutor(max_workers=6) as ex:
        status = list(ex.map(run_case, cases))
    (SWEEP / "cases.json").write_text(json.dumps(cases, indent=1))
    print(f"DONE: {sum(status)}/{len(cases)} succeeded", flush=True)


if __name__ == "__main__":
    main()
