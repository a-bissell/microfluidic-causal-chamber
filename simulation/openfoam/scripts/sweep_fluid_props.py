#!/usr/bin/env python3
"""Sweep the two FLUID-PROPERTY assumptions the chamber rests on: sigma and theta0.

Every geometric and hydraulic claim in this repo has been measured. The two
numbers underneath them have not:

  sigma  = 0.03 N/m   constant/transportProperties, commented "with 2% Span 80
                      ... typical value 0.02-0.04". No citation. 0.03-0.04 is
                      roughly the BARE water/silicone-oil value, which is a
                      strange place to land for a 2 wt% surfactant load (well
                      above CMC). If the real interface is nearer 5-10 mN/m
                      this is off by 3-6x.

  theta0 = 160 deg    0/alpha.water, whose own comment records that 120 deg
                      "let water spread as a stable wall film". The value was
                      SELECTED because it dripped. That is a legitimate way to
                      find a sensitive parameter and an illegitimate way to
                      claim one has been verified.

Why sigma is the bigger risk of the two. Combining the viscous pressure drop
dP ~ mu*U*L/w^2 with the definition of the capillary number U = Ca*sigma/mu,
the viscosity cancels:

        dP  ~  Ca * sigma * L / w^2

The drive pressure -- i.e. the hydrostatic column height a builder sets on the
bench -- is DIRECTLY PROPORTIONAL to interfacial tension. It is not a second-
order correction to the operating point; it is the operating point. And the
capillary entry threshold 2*sigma/w scales identically, so both terms move
together. Get sigma wrong by 5x and either the head is wrong by 5x, or Ca is
wrong by 5x and the chip jets instead of squeezing.

Three studies, selected by --pressure-mode and what you pass to --sigma/--theta:

  A. theta boundary        --sigma 0.03 --theta 120 130 140 150 160 170
                           --pressure-mode fixed
     Where does dripping actually stop? The docs asserts 120 fails and 160
     works; nothing in between has ever been run.

  B. sigma, drive unchanged  --sigma 0.005 ... 0.04 --theta 160
                             --pressure-mode fixed
     What a builder actually sees if they set the designed 980/490 Pa and
     sigma is not 0.03. This is the calibration curve: observed droplet rate
     -> inferred sigma.

  C. sigma, drive retuned    --sigma 0.005 ... 0.04 --theta 160
                             --pressure-mode scale-with-sigma
     Does retuning the head to P ~ sigma recover the design point? If the
     observables collapse, the chamber is sigma-robust with a known one-line
     correction, and that correction is the deliverable.

In scale-with-sigma mode the TIME axis is rescaled too (endTime and
writeInterval by sigma_ref/sigma). That is not a fudge: if P ~ sigma then
U ~ sigma, so the droplet period goes as 1/sigma. Holding endTime fixed would
show fewer droplets at low sigma purely because the clock ran out, which would
read as a regime change rather than as slower physics.

maxDeltaT is deliberately NOT rescaled. The capillary timestep limit
sqrt(rho*dx^3/(2*pi*sigma)) goes as 1/sqrt(sigma), so the case's existing
5e-6 s cap only gets safer as sigma falls, and it is already ~3.6x
conservative at the 40 um cells of the 800 um chip. Leaving it fixed costs
some wall time on the slow cases and buys a sweep with no timestep confound,
whose nominal cell is directly comparable to results/scaleup_2026-07.

Usage (the three studies as run for results/wetting_2026-08):

    python3 sweep_fluid_props.py --base-case ../tjunction_2d_mill \\
        --w-main 800 --output-dir ~/sweeps/wetting/A_theta \\
        --sigma 0.03 --theta 120 130 140 150 160 170 \\
        --p-cont 980 --p-disp 490 --pressure-mode fixed \\
        --end-time 0.6 --write-interval 0.005 --concurrency 6
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

sys.path.insert(0, str(Path(__file__).parent))
from sweep_pressure import patch_boundary_value, warn_if_slow_fs  # noqa: E402


def patch_block_entry(text: str, block: str, key: str, value) -> str:
    """Replace `key <value>;` inside one named brace block (e.g. walls).

    Brace-counting rather than a bare regex for the same reason as
    sweep_pressure.patch_boundary_value: these blocks carry free-form
    comments containing numbers, and 0/alpha.water in particular has a
    comment mentioning "120 deg" three lines above the theta0 it documents.
    A global regex on theta0 would be fine today and would silently pick the
    wrong occurrence the day someone adds a second wall patch.
    """
    lines, out = text.split("\n"), []
    in_block, depth, found = False, 0, 0
    for line in lines:
        if not in_block and re.match(rf"\s*{re.escape(block)}\s*$", line):
            in_block = True
        if in_block:
            depth += line.count("{") - line.count("}")
            if re.match(rf"\s*{re.escape(key)}\s+[-0-9.eE+]+\s*;", line):
                indent = line[: len(line) - len(line.lstrip())]
                line = f"{indent}{key:<15} {value:g};"
                found += 1
            if depth == 0 and "}" in line:
                in_block = False
        out.append(line)
    if found != 1:
        raise ValueError(f"expected exactly 1 '{key}' in block '{block}', found {found}")
    return "\n".join(out)


def patch_block_vector(text: str, block: str, vec: str) -> str:
    """Replace `value uniform (a b c);` inside one named brace block.

    Separate from patch_block_entry because the velocity BC's payload is a
    parenthesised vector, not a scalar, and the scalar regex would not match
    it at all -- silently leaving the inlet at whatever it was.
    """
    lines, out = text.split("\n"), []
    in_block, depth, found = False, 0, 0
    for line in lines:
        if not in_block and re.match(rf"\s*{re.escape(block)}\s*$", line):
            in_block = True
        if in_block:
            depth += line.count("{") - line.count("}")
            if re.match(r"\s*value\s+uniform\s*\([^)]*\)\s*;", line):
                indent = line[: len(line) - len(line.lstrip())]
                line = f"{indent}{'value':<15} uniform {vec};"
                found += 1
            if depth == 0 and "}" in line:
                in_block = False
        out.append(line)
    if found != 1:
        raise ValueError(f"expected exactly 1 vector 'value' in block '{block}', found {found}")
    return "\n".join(out)


def patch_top_level(text: str, key: str, value) -> str:
    """Replace a top-level `key <value>;` entry (transportProperties sigma)."""
    new, n = re.subn(rf"^(\s*){re.escape(key)}\s+[-0-9.eE+]+\s*;",
                     rf"\g<1>{key:<15} {value:g};", text, count=1, flags=re.M)
    if n != 1:
        raise ValueError(f"expected exactly 1 top-level '{key}', found {n}")
    return new


def make_cases(args):
    cases = []
    for sigma in args.sigma:
        for theta in args.theta:
            if args.pressure_mode == "scale-with-sigma":
                k = sigma / args.sigma_ref
            else:
                k = 1.0
            if args.u_oil is not None:
                # Velocity-driven (the 3D mill case): U = Ca*sigma/mu, so the
                # drive scales with sigma exactly as pressure does.
                cases.append({
                    "name": f"s{sigma*1000:g}_t{theta:g}",
                    "sigma": sigma, "theta0": theta,
                    "U_oil": args.u_oil * k, "U_water": args.u_water * k,
                    "P_cont": None, "P_disp": None,
                    "end_time": round(args.end_time * (1.0 / k if k != 1.0 else 1.0), 6),
                    "write_interval": round(args.write_interval * (1.0 / k if k != 1.0 else 1.0), 8),
                    "pressure_mode": f"velocity:{args.pressure_mode}",
                    "w_main_um": args.w_main,
                })
                continue
            # Only the time axis follows sigma, and only when the drive does
            # too -- at fixed pressure the velocity is set by hydraulics, not
            # by sigma, so the clock should not move.
            t_scale = 1.0 / k if args.pressure_mode == "scale-with-sigma" else 1.0
            cases.append({
                "name": f"s{sigma*1000:g}_t{theta:g}",
                "sigma": sigma,
                "theta0": theta,
                "P_cont": round(args.p_cont * k, 2),
                "P_disp": round(args.p_disp * k, 2),
                "end_time": round(args.end_time * t_scale, 6),
                "write_interval": round(args.write_interval * t_scale, 8),
                "pressure_mode": args.pressure_mode,
                "w_main_um": args.w_main,
            })
    return cases


def build_case(c, base_case: Path, output_dir: Path):
    d = output_dir / c["name"]
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    for sub in ("0", "constant", "system"):
        shutil.copytree(base_case / sub, d / sub)

    # Regenerate the mesh AND setFieldsDict at the requested width, in the
    # case dir. gen_blockmesh.py writes relative to its own location, so
    # copying it in and running it there keeps the source tree untouched.
    gen = base_case / "gen_blockmesh.py"
    if not gen.exists():
        raise FileNotFoundError(f"{gen} not found; needed to build at w={c['w_main_um']} um")
    shutil.copy(gen, d / "gen_blockmesh.py")
    r = subprocess.run([sys.executable, "gen_blockmesh.py", "--w-main", str(c["w_main_um"])],
                       cwd=d, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"gen_blockmesh failed for {c['name']}: {r.stderr[-400:]}")

    tp = d / "constant" / "transportProperties"
    tp.write_text(patch_top_level(tp.read_text(), "sigma", c["sigma"]))

    aw = d / "0" / "alpha.water"
    aw.write_text(patch_block_entry(aw.read_text(), "walls", "theta0", c["theta0"]))

    if c.get("U_oil") is not None:
        # Velocity-driven: the 3D mill case has NO feed resistors (velocity
        # inlets pin the flow directly), so there is no geometry for a
        # pressure BC to drop across and p_rgh stays fixedFluxPressure.
        u = d / "0" / "U"
        text = u.read_text()
        text = patch_block_vector(text, "oil_inlet", f"({c['U_oil']:.6g} 0 0)")
        text = patch_block_vector(text, "water_inlet", f"(0 -{c['U_water']:.6g} 0)")
        u.write_text(text)
    else:
        p_rgh = d / "0" / "p_rgh"
        text = p_rgh.read_text()
        for patch, val in (("oil_inlet", c["P_cont"]), ("water_inlet", c["P_disp"])):
            text = patch_boundary_value(text, patch, "p0", val)
            text = patch_boundary_value(text, patch, "value", val)
        p_rgh.write_text(text)

    ctrl = d / "system" / "controlDict"
    text = ctrl.read_text()
    text = re.sub(r"endTime\s+\S+;", f"endTime         {c['end_time']:g};", text, count=1)
    text = re.sub(r"writeInterval\s+\S+;", f"writeInterval   {c['write_interval']:g};", text, count=1)
    ctrl.write_text(text)
    return d


def run_case(c, output_dir: Path, image: str, mpi_ranks: int = 1):
    d = output_dir / c["name"]
    t0 = time.time()
    container = f"fluidsweep-{c['name']}".replace(".", "p")
    if mpi_ranks > 1:
        # decomposeParDict ships with numberOfSubdomains 6; rewrite it so
        # --mpi-ranks is actually honoured rather than silently ignored (a
        # mismatch is a hard mpirun error, but only after the mesh is built).
        solve = (f"sed -i 's/^numberOfSubdomains.*/numberOfSubdomains  {mpi_ranks};/' "
                 "system/decomposeParDict && "
                 "decomposePar > log.decomposePar 2>&1 && "
                 f"mpirun -np {mpi_ranks} --allow-run-as-root interFoam -parallel "
                 "> log.interFoam 2>&1 && "
                 "reconstructPar > log.reconstructPar 2>&1 && "
                 # processor*/ duplicates every reconstructed time step. On the
                 # 44k-cell 3D mesh that is ~0.5 GB per case of pure redundancy,
                 # and a full disk mid-sweep costs a day.
                 "rm -rf processor* && ")
    else:
        solve = "interFoam > log.interFoam 2>&1 && "
    cmd = [
        "docker", "run", "--rm", "--name", container,
        "--entrypoint", "bash", "-v", f"{d.resolve()}:/case", "-w", "/case", image, "-c",
        "source /usr/lib/openfoam/openfoam2306/etc/bashrc && "
        "blockMesh > log.blockMesh 2>&1 && setFields > log.setFields 2>&1 && "
        + solve +
        # -legacy is not optional: v2306 defaults to .vtm/.vtu, and every
        # extractor in scripts/ globs VTK/*.vtk, so the default silently
        # yields zero frames and an empty analysis rather than an error.
        "foamToVTK -legacy > log.foamToVTK 2>&1",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    log = d / "log.interFoam"
    ok = r.returncode == 0 and log.exists() and "End" in log.read_text()[-2000:]
    drive = (f"U={c['U_oil']:.5g}/{c['U_water']:.5g} m/s" if c.get("U_oil") is not None
             else f"P={c['P_cont']:.0f}/{c['P_disp']:.0f} Pa")
    print(f"[{c['name']}] {'OK' if ok else 'FAILED'} in {time.time()-t0:.0f}s "
          f"(sigma={c['sigma']*1000:g} mN/m, theta0={c['theta0']:g} deg, "
          f"{drive}, endTime={c['end_time']:g} s)", flush=True)
    if not ok:
        tail = r.stderr[-500:] if r.returncode != 0 else (
            log.read_text()[-500:] if log.exists() else "(no log)")
        print(f"  -> {tail.strip()[-300:]}", file=sys.stderr, flush=True)
    return ok


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base-case", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    p.add_argument("--w-main", type=float, default=800.0,
                   help="Channel width/depth in um, passed to gen_blockmesh.py (default: 800)")
    p.add_argument("--sigma", type=float, nargs="+", required=True,
                   help="Interfacial tensions in N/m, e.g. 0.005 0.008 0.012 0.02 0.03 0.04")
    p.add_argument("--theta", type=float, nargs="+", required=True,
                   help="Wall contact angles in degrees, measured through water")
    p.add_argument("--p-cont", type=float, default=None, help="Reference oil drive (Pa)")
    p.add_argument("--p-disp", type=float, default=None, help="Reference water drive (Pa)")
    p.add_argument("--u-oil", type=float, default=None,
                   help="Velocity-driven instead of pressure-driven: oil inlet speed (m/s). "
                        "Required for tjunction_3d_mill, which has no feed resistors for a "
                        "pressure BC to drop across. Implies --u-water.")
    p.add_argument("--u-water", type=float, default=None,
                   help="Water inlet speed (m/s), applied as (0 -u 0)")
    p.add_argument("--mpi-ranks", type=int, default=1,
                   help="Run each case under mpirun with this many ranks (default: 1, serial). "
                        "The 44k-cell 3D mesh wants 4-6; the 6.4k-cell 2D meshes do not "
                        "benefit and should stay serial with more cases in flight instead.")
    p.add_argument("--pressure-mode", choices=("fixed", "scale-with-sigma"), default="fixed",
                   help="fixed: every case uses --p-cont/--p-disp as given (what a builder "
                        "who trusted the docs would set). scale-with-sigma: scale both by "
                        "sigma/--sigma-ref, testing whether dP ~ Ca*sigma recovers the "
                        "design point (default: fixed)")
    p.add_argument("--sigma-ref", type=float, default=0.03,
                   help="sigma the --p-cont/--p-disp reference point was designed for "
                        "(default: 0.03)")
    p.add_argument("--end-time", type=float, default=0.6,
                   help="endTime (s) at sigma-ref; scaled by sigma-ref/sigma in "
                        "scale-with-sigma mode (default: 0.6, ~3.4 periods at 800 um)")
    p.add_argument("--write-interval", type=float, default=0.005,
                   help="writeInterval (s) at sigma-ref, scaled the same way (default: 0.005)")
    p.add_argument("--concurrency", type=int, default=6)
    p.add_argument("--image", default="opencfd/openfoam-default:2306")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not (args.base_case / "gen_blockmesh.py").exists():
        p.error(f"--base-case {args.base_case} has no gen_blockmesh.py")
    if (args.u_oil is None) != (args.u_water is None):
        p.error("--u-oil and --u-water must be given together")
    if args.u_oil is None and (args.p_cont is None or args.p_disp is None):
        p.error("give either --p-cont/--p-disp (pressure-driven) or --u-oil/--u-water")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    warn_if_slow_fs(args.output_dir)

    cases = make_cases(args)
    print(f"Building {len(cases)} case(s) at w = {args.w_main:g} um "
          f"({len(args.sigma)} sigma x {len(args.theta)} theta, "
          f"pressure-mode={args.pressure_mode})...")
    for c in cases:
        build_case(c, args.base_case, args.output_dir)
        drive = (f"U={c['U_oil']:.5g}/{c['U_water']:.5g} m/s" if c.get("U_oil") is not None
                 else f"P={c['P_cont']:.0f}/{c['P_disp']:.0f} Pa")
        print(f"  built {c['name']}: sigma={c['sigma']*1000:g} mN/m theta0={c['theta0']:g} "
              f"{drive} endTime={c['end_time']:g}s", flush=True)
    (args.output_dir / "cases.json").write_text(json.dumps(cases, indent=1))

    if args.dry_run:
        print("Dry run: cases built, not executed.")
        return

    print(f"Running with concurrency={args.concurrency}...")
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        status = list(ex.map(
            lambda c: run_case(c, args.output_dir, args.image, args.mpi_ranks), cases))

    print(f"DONE: {sum(status)}/{len(cases)} succeeded")
    if not all(status):
        print("Failed: " + ", ".join(c["name"] for c, ok in zip(cases, status) if not ok),
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
