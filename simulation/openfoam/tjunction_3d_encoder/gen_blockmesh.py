#!/usr/bin/env python3
"""Generate the encoder twin: a 3-dye cross-merge feeding a T-junction.

WHAT THIS CASE IS FOR
---------------------
The encoder writes a *code* into each droplet: three dye streams merge into
one water leg at flow rates (Q1, Q2, Q3), the T-junction chops that leg into
droplets, and the droplet's composition c_i = Q_i / sum(Q) is the symbol.

The whole scheme rests on one claim:

    A droplet's integrated dye content equals the commanded flow fraction.

The argument for it is mass conservation -- the slug consumes the full
channel cross-section, so it captures each stream in proportion to its flux,
whether or not the streams have diffusively mixed. Integrated readout is
therefore mixing-insensitive, which is why no on-chip mixer is needed and why
the bench version can be read with a colour camera in absorbance.

That argument has a hole, and the hole is three-dimensional. If the
continuous phase intrudes at the corners of the water leg near the junction
-- which is exactly what results/mill3d800_2026-08 found, reporting minimum
cell-centre alpha of 0.75 across x and 0.83 across z in the leg -- then the
slug does *not* sample the full cross-section. It preferentially samples the
core. The three laminae do not sit symmetrically in that cross-section, so
preferential core sampling biases the code.

A 2D mesh cannot show this. It has no corners.

THE GEOMETRY, AND WHY IT IS SHAPED THIS WAY
-------------------------------------------
The merge is a cross, not a Y:

                          dye2  (axial, centre lamina)
                            |
                            v
        dye1 --> +----------+----------+ <-- dye3
                            |
                            |  shared water leg
                            v
        oil ====== [ T-junction ] ======> droplets

dye1 and dye3 enter from opposite sides at the same station; dye2 enters
axially. Downstream of the merge the water leg carries three laminae across
its width, with dye2 in the middle and dye1/dye3 against the side walls.

Two reasons for this arrangement rather than a Y or a comb:

  1. It is orthogonal, so blockMesh handles it with no angled blocks, and it
     is millable in the same single-endmill workflow as the rest of the chip.

  2. It makes dye1 and dye3 geometrically equivalent -- same leg length, same
     resistance, same wall proximity, mirror images about the leg axis. That
     is a *built-in control*. At the symmetric operating point c = (1/3,
     1/3, 1/3):

         measured c1 != measured c3   =>  numerical or meshing artifact
         measured c1 == c3 != 1/3     =>  real geometric sampling bias

     The second signature is the corner-gutter effect on the encoder, and it
     is measurable without needing any absolute accuracy claim -- it is a
     departure from a symmetry that the geometry guarantees.

ACTUATION: VELOCITY INLETS, DELIBERATELY
----------------------------------------
The encoder has two distinct error mechanisms and they need separating:

  - Sampling fidelity: does the junction chop the laminated stream without
    bias? Hydrodynamic, needs 3D, isolated by *pinning* the flow rates.
  - Hydraulic crosstalk: under pressure actuation the three legs are coupled
    through the shared merge node, so commanding P_i does not deliver the
    intended Q_i. Lumped-circuit, 2D captures it fine, and it vanishes
    entirely under flow-rate actuation.

This case uses velocity inlets, so Q_i are exogenous and crosstalk is zero by
construction. What remains is sampling fidelity alone. Do not read these runs
as a statement about the pressure-driven chamber -- see README.md, "Crosstalk
is a separate experiment".

This also follows the correction in results/mill3d800_2026-08: that run found
its predecessor had varied dimensionality and actuation mode *together*, and
fixed it by driving both 2D and 3D from the same velocity BCs. --two-d here
emits the identical domain one cell thick for the same reason.

Run:
    python3 gen_blockmesh.py --w-main 800                 # 3D, ~68k cells
    python3 gen_blockmesh.py --w-main 800 --two-d         # matched 2D baseline
    python3 gen_blockmesh.py --w-main 800 --c 0.5 0.25 0.25   # asymmetric code
"""
import argparse
from pathlib import Path

# ---- geometry (micrometres) -------------------------------------------------
# Lengths are fixed while widths scale with --w-main, matching tjunction_2d_mill
# and tjunction_3d_mill: holding Ca fixed means holding velocity fixed, so a
# wider chip runs the same regime at lower drive pressure.
L_APPROACH = 2000.0     # oil inlet -> junction
L_OUTLET = 4000.0       # junction -> outlet

_p = argparse.ArgumentParser()
_p.add_argument("--w-main", type=float, default=800.0,
                help="Channel width (y) AND full depth (z), um. 800 is the "
                     "replicable milling scale (endmill stiffness ~ d^4).")
_p.add_argument("--dx", type=float, default=None,
                help="Cell size (um), uniform. Default w/20, matching every "
                     "other case here so relative resolution is fixed.")
_p.add_argument("--two-d", action="store_true",
                help="Emit the SAME domain as a single-cell-thick 2D mesh. The "
                     "controlled baseline: one generator, one flag, so "
                     "dimensionality is the only difference.")
_p.add_argument("--l-leg", type=float, default=1200.0,
                help="Merge node -> junction distance (um). THE key tradeoff: "
                     "this is the encoder's transport delay, so short means "
                     "inlet-derived (genuinely laminated) water reaches the "
                     "junction early in the run, but couples junction pressure "
                     "fluctuation back into the merge. At the default 1200 um "
                     "and U_leg ~ 5.8 mm/s the transit is ~0.21 s, about two "
                     "droplet periods -- so budget endTime >= 0.8 s to get "
                     "~5 measurable inlet-derived droplets.")
_p.add_argument("--l-dye", type=float, default=1600.0,
                help="Length of each of the three dye legs (um).")
_p.add_argument("--c", type=float, nargs=3, default=[1/3, 1/3, 1/3],
                metavar=("C1", "C2", "C3"),
                help="Commanded composition (dye1 dye2 dye3). Normalised "
                     "internally. Default is the symmetric point, which is the "
                     "highest-information run: it turns the c1==c3 symmetry "
                     "into a free artifact detector.")
_p.add_argument("--q-water", type=float, default=3.706,
                help="Total water flux, uL/s. Default is the MEASURED 2D flux "
                     "at 800 um from results/scaleup_2026-07, so this case "
                     "sits at the verified chamber operating point.")
_p.add_argument("--q-oil", type=float, default=12.694,
                help="Oil flux, uL/s. Default as above (gives q = 0.292, "
                     "Ca = 0.0317).")
a = _p.parse_args()

W = a.w_main
DEPTH = W
DX = a.dx if a.dx is not None else W / 20.0
TWO_D = a.two_d
L_LEG, L_DYE = a.l_leg, a.l_dye

csum = sum(a.c)
C = [ci / csum for ci in a.c]

# ---- station grid -----------------------------------------------------------
# x: oil inlet | dye1 leg | junction | dye3 leg | outlet
#    The dye legs live at merge-band y, so they share x-stations with the main
#    channel without overlapping it.
x_j0, x_j1 = L_APPROACH, L_APPROACH + W
XS = [0.0, x_j0 - L_DYE, x_j0, x_j1, x_j1 + L_DYE, x_j1 + L_OUTLET]
# y: main channel | water leg | merge band | dye2 leg
YS = [0.0, W, W + L_LEG, W + L_LEG + W, W + L_LEG + W + L_DYE]
ZS = [0.0, DEPTH] if TWO_D else [0.0, DEPTH / 2.0]

if XS[1] <= XS[0]:
    raise SystemExit(f"dye legs ({L_DYE} um) overrun the oil approach "
                     f"({L_APPROACH} um); shorten --l-dye")
if XS[4] >= XS[5]:
    raise SystemExit(f"dye legs ({L_DYE} um) overrun the outlet "
                     f"({L_OUTLET} um); shorten --l-dye")


def _n(length):
    return max(1, round(length / DX))


NX = [_n(XS[i + 1] - XS[i]) for i in range(5)]
NY = [_n(YS[i + 1] - YS[i]) for i in range(4)]
NZ = 1 if TWO_D else _n(ZS[1])

# (x-interval, y-interval) index pairs for every fluid block
BLOCKS = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0),   # main channel
          (2, 1),                                    # shared water leg
          (1, 2), (2, 2), (3, 2),                    # dye1 | merge | dye3
          (2, 3)]                                    # dye2 leg

# ---- mesh assembly ----------------------------------------------------------
verts: dict[tuple, int] = {}


def vid(x, y, z):
    key = (round(x, 3), round(y, 3), round(z, 3))
    if key not in verts:
        verts[key] = len(verts)
    return verts[key]


hexes = []
face_count: dict[tuple, list] = {}


def add_block(ix, iy):
    x0, x1 = XS[ix], XS[ix + 1]
    y0, y1 = YS[iy], YS[iy + 1]
    v = [vid(x0, y0, ZS[0]), vid(x1, y0, ZS[0]), vid(x1, y1, ZS[0]), vid(x0, y1, ZS[0]),
         vid(x0, y0, ZS[1]), vid(x1, y0, ZS[1]), vid(x1, y1, ZS[1]), vid(x0, y1, ZS[1])]
    hexes.append((v, NX[ix], NY[iy], NZ))
    for axis, coord, quad in [
        ('x', x0, (v[0], v[4], v[7], v[3])),
        ('x', x1, (v[1], v[2], v[6], v[5])),
        ('y', y0, (v[0], v[1], v[5], v[4])),
        ('y', y1, (v[3], v[7], v[6], v[2])),
        ('z', ZS[0], (v[0], v[3], v[2], v[1])),
        ('z', ZS[1], (v[4], v[5], v[6], v[7])),
    ]:
        face_count.setdefault(tuple(sorted(quad)), []).append((axis, coord, quad))


for ix, iy in BLOCKS:
    add_block(ix, iy)

patches = {'oil_inlet': [], 'dye1_inlet': [], 'dye2_inlet': [], 'dye3_inlet': [],
           'outlet': [], 'symmetryPlane': [], 'frontAndBack': [], 'walls': []}

# Only faces appearing once are boundaries; shared faces are internal. The dye
# inlets are the outer x-faces of the two side legs, which are unambiguous
# because no block exists beyond them at merge-band y.
for entries in face_count.values():
    if len(entries) != 1:
        continue
    axis, coord, quad = entries[0]
    if axis == 'x' and coord == XS[0]:
        patches['oil_inlet'].append(quad)
    elif axis == 'x' and coord == XS[5]:
        patches['outlet'].append(quad)
    elif axis == 'x' and coord == XS[1]:
        patches['dye1_inlet'].append(quad)
    elif axis == 'x' and coord == XS[4]:
        patches['dye3_inlet'].append(quad)
    elif axis == 'y' and coord == YS[4]:
        patches['dye2_inlet'].append(quad)
    elif axis == 'z' and TWO_D:
        patches['frontAndBack'].append(quad)
    elif axis == 'z' and coord == ZS[1]:
        patches['symmetryPlane'].append(quad)
    else:
        patches['walls'].append(quad)

for name in ('oil_inlet', 'dye1_inlet', 'dye2_inlet', 'dye3_inlet', 'outlet'):
    if not patches[name]:
        raise SystemExit(f"BUG: patch {name} came out empty -- station grid is wrong")

HERE = Path(__file__).parent
(HERE / "system").mkdir(exist_ok=True)
(HERE / "0").mkdir(exist_ok=True)

HDR = """/*--------------------------------*- C++ -*----------------------------------*\\
| Generated by gen_blockmesh.py — edit that script, not this file.            |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       {cls};
    object      {obj};
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
"""

# ---- blockMeshDict ----------------------------------------------------------
lines = [HDR.format(cls="dictionary", obj="blockMeshDict"),
         "\nscale 1e-6;   // coordinates below are micrometres\n\nvertices\n("]
for (x, y, z), i in sorted(verts.items(), key=lambda kv: kv[1]):
    lines.append(f"    ({x} {y} {z})   // {i}")
lines.append(");\n\nblocks\n(")
for v, nx, ny, nz in hexes:
    lines.append(f"    hex ({' '.join(map(str, v))}) ({nx} {ny} {nz}) simpleGrading (1 1 1)")
lines.append(");\n\nedges\n(\n);\n\nboundary\n(")
TYPES = {'oil_inlet': 'patch', 'dye1_inlet': 'patch', 'dye2_inlet': 'patch',
         'dye3_inlet': 'patch', 'outlet': 'patch', 'symmetryPlane': 'symmetry',
         'frontAndBack': 'empty', 'walls': 'wall'}
for name, quads in patches.items():
    if not quads:
        continue
    lines.append(f"    {name}\n    {{\n        type {TYPES[name]};\n        faces\n        (")
    for q in quads:
        lines.append(f"            ({' '.join(map(str, q))})")
    lines.append("        );\n    }")
lines.append(");\n\nmergePatchPairs\n(\n);\n\n// ***************************** //")
(HERE / "system" / "blockMeshDict").write_text("\n".join(lines) + "\n")
ncells = sum(nx * ny * nz for _, nx, ny, nz in hexes)
print(f"blockMeshDict: {len(verts)} vertices, {len(hexes)} blocks, {ncells} cells "
      f"({'2D' if TWO_D else '3D half-depth'}, w={W:.0f} um, dx={DX:.1f} um)")

# ---- velocities -------------------------------------------------------------
# Every inlet is a full w x w square, so U = Q / w^2 for each. In the 3D
# half-depth domain the patch area halves too, so the VELOCITY is unchanged and
# only the volumetric flux halves -- consistent between 2D and 3D, which is
# what makes the two comparable. Composition is a ratio and cancels entirely.
A = (W * 1e-6) ** 2                       # m^2, full-depth inlet area
U_oil = a.q_oil * 1e-9 / A                # m/s
U_dye = [ci * a.q_water * 1e-9 / A for ci in C]
U_leg = a.q_water * 1e-9 / A
t_transit = (L_LEG * 1e-6) / U_leg
# setFields seeds uniform (1/3,1/3,1/3) water across the whole column above
# the junction -- the leg AND the square merge node on top of it -- so the
# seeded water that must clear is L_LEG + W_MAIN, not L_LEG. A droplet then
# needs one more formation period before it is written entirely from
# inlet-derived fluid. analyze_encoder.py cuts at this settle time, not at
# t_transit; the 0.8 s reference run cut at t_transit and passed two
# still-settling droplets, which faked an asymmetry.
t_flush = ((L_LEG + a.w_main) * 1e-6) / U_leg

print(f"U_oil = {U_oil:.6f} m/s, U_leg = {U_leg:.6f} m/s")
print(f"U_dye = [{U_dye[0]:.6f}, {U_dye[1]:.6f}, {U_dye[2]:.6f}] m/s  "
      f"for c = [{C[0]:.4f}, {C[1]:.4f}, {C[2]:.4f}]")
print(f"merge->junction transit = {t_transit*1e3:.1f} ms (leg only)")
print(f"leg + merge node flush   = {t_flush*1e3:.1f} ms, plus one droplet "
      f"period before a clean droplet forms.")
print(f"  n droplets needs endTime ~ {t_flush*1e3:.0f} ms + (n+1) x period; "
      f"at ~170 ms that is ~{t_flush + 9*0.170:.1f} s for n = 8.")

DYE_PATCH = {'dye1_inlet': 0, 'dye2_inlet': 1, 'dye3_inlet': 2}
VEC = {'dye1_inlet': lambda u: f"({u:.8f} 0 0)",      # +x, from the left
       'dye3_inlet': lambda u: f"({-u:.8f} 0 0)",     # -x, from the right
       'dye2_inlet': lambda u: f"(0 {-u:.8f} 0)"}     # -y, axial

u_lines = [HDR.format(cls="volVectorField", obj="U"),
           "\ndimensions      [0 1 -1 0 0 0 0];\n\ninternalField   uniform (0 0 0);\n",
           "boundaryField\n{",
           f"    oil_inlet\n    {{\n        type            fixedValue;\n"
           f"        value           uniform ({U_oil:.8f} 0 0);\n    }}\n"]
for patch, idx in DYE_PATCH.items():
    u_lines.append(f"    {patch}\n    {{\n        type            fixedValue;\n"
                   f"        value           uniform {VEC[patch](U_dye[idx])};"
                   f"   // c{idx+1} = {C[idx]:.4f}\n    }}\n")
u_lines.append("    outlet\n    {\n        type            pressureInletOutletVelocity;\n"
               "        value           uniform (0 0 0);\n    }\n")
u_lines.append("    walls\n    {\n        type            noSlip;\n    }\n")
u_lines.append("    frontAndBack\n    {\n        type            empty;\n    }\n"
               if TWO_D else
               "    symmetryPlane\n    {\n        type            symmetry;\n    }\n")
u_lines.append("}\n\n// ***************************** //")
(HERE / "0" / "U").write_text("\n".join(u_lines) + "\n")

# ---- alpha.water, p_rgh, and the three dye scalars -------------------------
# WHY PASSIVE SCALARS AND NOT PHASES -- a negative result, recorded so it is
# not repeated.
#
# The physically nicer design is multiphaseInterFoam with four phases
# (water1/2/3 + oil). Every alpha.water_i is then MULES-advected, conserved
# and bounded, so sum_i alpha.water_i == total water is an identity the solver
# enforces rather than a diagnostic to be checked, and composition carries no
# numerical leakage at all. That was built first, for exactly that reason.
#
# IT DOES NOT FORM DROPLETS. Three runs settled it:
#
#   verified tjunction_3d_mill geometry + interFoam        -> drips, L = 1400 um
#   THIS geometry               + interFoam                -> drips, L = 1240 um
#   THIS geometry               + multiphaseInterFoam      -> no pinch-off
#
# The middle row is the important one: this exact mesh, these exact velocity
# BCs and this exact contact angle reproduce the verified 800 um 2D slug
# length of 1240 um from results/scaleup_2026-07 on the nose. So the merge
# geometry is sound and the operating point is right; the solver is what
# differs. With multiphaseInterFoam the thread stays attached past 2.5 mm and
# keeps growing at ~27 mm/s instead of necking.
#
# The surface-tension force does appear to sum correctly across the three
# water-oil pairs -- at a 1/3-1/3-1/3 interface each pair contributes a third
# of the two-phase value, totalling the same 1/delta -- so the cause is more
# likely the per-pair curvature estimate, which is built from an alpha field
# that only ever spans 0 to 1/3 and is correspondingly noisier, and/or the
# interface compression acting between water phases that have no physical
# interface. Not chased further: the two-phase route works and is verified in
# this geometry, which is worth more than the conservation guarantee.
#
# THE COST OF COMING BACK. A passive scalar gets no MULES compression, so it
# is neither conserved nor bounded, and it leaks across the interface because
# phi is the MIXTURE flux and differs from the water velocity where
# 0 < alpha < 1. Uniform leakage cancels in a composition RATIO and is
# harmless; differential leakage between laminae at different distances from
# the interface does not cancel, and is confounded with the physical sampling
# bias this case measures.
#
# Two things bound that confound, and both must be used:
#   1. sum_i dye_i == alpha.water is an identity by construction but is NOT
#      numerically enforced here, so its violation is a free pointwise error
#      measure. extract_droplet_dye.py integrates it per droplet.
#   2. Numerical leakage scales with dx; a physical sampling bias does not.
#      A bias seen at one resolution is not a result -- see the --dx 20
#      confirmation run in README.md.
PHASES = ["water", "oil"]


def bc_block(entries, two_d):
    out = ["boundaryField\n{"]
    for patch, body in entries:
        out.append(f"    {patch}\n    {{\n{body}    }}\n")
    out.append("    frontAndBack\n    {\n        type            empty;\n    }\n"
               if two_d else
               "    symmetryPlane\n    {\n        type            symmetry;\n    }\n")
    out.append("}\n\n// ***************************** //")
    return "\n".join(out)


FIXED = "        type            fixedValue;\n        value           uniform {v};\n"
ZG = "        type            zeroGradient;\n"
INOUT = ("        type            inletOutlet;\n"
         "        inletValue      uniform {v};\n        value           uniform {v};\n")

# WALL WETTING IS LOAD-BEARING, NOT A DETAIL.
#
# theta0 = 160 deg measured through the water phase: strongly oil-wet walls,
# carried over from tjunction_2d_mill and tjunction_3d_mill, whose own comment
# records what happens otherwise -- "160 deg keeps the water thread off the
# walls so it can neck and pinch off (120 deg let water spread as a stable
# wall film)".
#
# This was learned here the expensive way. The first version of this generator
# emitted zeroGradient on walls, which is NEUTRAL wetting (90 deg). The case
# meshed cleanly, ran cleanly, conserved phase perfectly, and produced no
# droplets at all: the water entered at the top of the channel and rode along
# the wall as a jet out to 2.9 mm without ever blocking the junction, so the
# oil never had to squeeze it. Nothing about the run looked wrong except that
# the answer never appeared. Do not "simplify" this back to zeroGradient.
#
# multiphaseInterFoam needs a contact angle for EVERY phase pair, not one
# value per field, so the table below is the 4-phase generalisation of the
# single theta0 the two-phase cases carry. Water-water pairs get 90 deg: they
# are the same fluid and there is no physical contact line between them, so
# the value is arbitrary -- but the entry must exist or the BC construction
# fails at run time, after meshing has already succeeded.
THETA_WATER_OIL = 160.0

# Strongly oil-wet walls, byte-identical to tjunction_2d_mill and
# tjunction_3d_mill, whose comment records what happens otherwise: "160 deg
# keeps the water thread off the walls so it can neck and pinch off (120 deg
# let water spread as a stable wall film)".
#
# Learned here the expensive way. The first version of this generator emitted
# zeroGradient, which is NEUTRAL wetting (90 deg). The case meshed cleanly,
# ran cleanly, and produced no droplets at all: water entered at the top of
# the channel and rode the wall as a jet out to 2.9 mm without ever blocking
# the junction, so the oil never had to squeeze it. Nothing looked wrong; the
# answer simply never appeared. Do not "simplify" this back to zeroGradient.
CONTACT_ANGLE = (
    "        // ESI (v1912+) name: constantAlphaContactAngle\n"
    "        // Foundation (11+) name: contactAngle\n"
    "        // theta0 measured through the water phase; 160 deg = oil-wet.\n"
    "        type            constantAlphaContactAngle;\n"
    f"        theta0          {THETA_WATER_OIL:g};\n"
    "        limit           gradient;\n"
    "        value           uniform 0;\n")

alpha = [HDR.format(cls="volScalarField", obj="alpha.water"),
         "\ndimensions      [0 0 0 0 0 0 0];\n\ninternalField   uniform 0;\n",
         bc_block([("oil_inlet", FIXED.format(v=0)),
                   ("dye1_inlet", FIXED.format(v=1)),
                   ("dye2_inlet", FIXED.format(v=1)),
                   ("dye3_inlet", FIXED.format(v=1)),
                   ("outlet", INOUT.format(v=0)),
                   ("walls", CONTACT_ANGLE)], TWO_D)]
(HERE / "0" / "alpha.water").write_text("\n".join(alpha) + "\n")

# The three dye scalars. dye_i is the volume fraction of water-of-type-i, so
# sum_i dye_i == alpha.water by construction -- see the block above for why
# that identity is a diagnostic here rather than a guarantee.
DYE_PATCH_IDX = {"dye1_inlet": 0, "dye2_inlet": 1, "dye3_inlet": 2}
for i in range(3):
    entries = [("oil_inlet", FIXED.format(v=0))]
    for patch, idx in sorted(DYE_PATCH_IDX.items()):
        entries.append((patch, FIXED.format(v=1 if idx == i else 0)))
    entries += [("outlet", INOUT.format(v=0)), ("walls", ZG)]
    fld = [HDR.format(cls="volScalarField", obj=f"dye{i+1}"),
           "\ndimensions      [0 0 0 0 0 0 0];\n\ninternalField   uniform 0;\n",
           bc_block(entries, TWO_D)]
    (HERE / "0" / f"dye{i+1}").write_text("\n".join(fld) + "\n")

prgh = [HDR.format(cls="volScalarField", obj="p_rgh"),
        "\ndimensions      [1 -1 -2 0 0 0 0];\n\ninternalField   uniform 0;\n",
        bc_block([("oil_inlet", ZG), ("dye1_inlet", ZG), ("dye2_inlet", ZG),
                  ("dye3_inlet", ZG),
                  ("outlet", "        type            fixedValue;\n"
                             "        value           uniform 0;\n"),
                  ("walls", ZG)], TWO_D)]
(HERE / "0" / "p_rgh").write_text("\n".join(prgh) + "\n")

# transportProperties is NOT generated -- it is the two-phase file shared with
# tjunction_2d_mill and tjunction_3d_mill (50 cSt silicone oil + 2% Span 80
# against DI water, sigma = 0.03). Generating a copy here would let the two
# drift apart silently, and the whole point of this case is that its junction
# physics is the same chamber as theirs.

# ---- setFieldsDict ----------------------------------------------------------
# Prime the whole water side (three dye legs + merge node + shared leg) so the
# run does not spend its first tenth of a second filling plumbing. Each dye leg
# gets its own dye at 1; the merge node and shared leg get the COMMANDED
# composition, so the initial condition agrees with the boundary condition and
# no startup step is written into the code.
#
# Note this seeded water is uniformly mixed, not laminated. Genuinely laminated
# inlet-derived water only reaches the junction after ~t_transit, which is why
# the analysis discards droplets formed before then -- they cannot answer the
# question this case exists to ask.
def box(x0, x1, y0, y1, field, val):
    return (f"    boxToCell\n    {{\n        box ({x0*1e-6:.8g} {y0*1e-6:.8g} "
            f"{ZS[0]*1e-6:.8g}) ({x1*1e-6:.8g} {y1*1e-6:.8g} {ZS[1]*1e-6:.8g});\n"
            f"        fieldValues ( volScalarFieldValue {field} {val} );\n    }}")


regions = []
DYE_LEGS = [((XS[1], XS[2], YS[2], YS[3]), 1),    # dye1 leg, from the left
            ((XS[3], XS[4], YS[2], YS[3]), 3),    # dye3 leg, from the right
            ((XS[2], XS[3], YS[3], YS[4]), 2)]    # dye2 leg, axial
SHARED = (XS[2], XS[3], YS[1], YS[3])             # merge node + shared leg

for (x0, x1, y0, y1), dye in DYE_LEGS:
    regions.append(box(x0, x1, y0, y1, "alpha.water", 1))
    regions.append(box(x0, x1, y0, y1, f"dye{dye}", 1))
regions.append(box(*SHARED, "alpha.water", 1))
for i, ci in enumerate(C):
    regions.append(box(*SHARED, f"dye{i+1}", f"{ci:.6f}"))

sf = [HDR.format(cls="dictionary", obj="setFieldsDict"),
      "\ndefaultFieldValues\n(\n    volScalarFieldValue alpha.water 0\n"
      "    volScalarFieldValue dye1 0\n    volScalarFieldValue dye2 0\n"
      "    volScalarFieldValue dye3 0\n);\n\nregions\n(",
      "\n".join(regions), ");\n\n// ***************************** //"]
(HERE / "system" / "setFieldsDict").write_text("\n".join(sf) + "\n")

# ---- geometry manifest ------------------------------------------------------
# Written so the extractor never has to be told the geometry by hand -- the
# 400 um sweep in results/mill_2026-07 produced a directory of garbage because
# extract_droplets.py had the previous chip's dimensions hardcoded.
manifest = HERE / "geometry.json"
manifest.write_text(
    "{\n"
    f'  "w_main_um": {W},\n'
    f'  "dx_um": {DX},\n'
    f'  "two_d": {"true" if TWO_D else "false"},\n'
    f'  "depth_modelled_um": {ZS[1]},\n'
    f'  "x_junction_um": [{XS[2]}, {XS[3]}],\n'
    f'  "x_outlet_um": [{XS[3]}, {XS[5]}],\n'
    f'  "y_channel_um": [{YS[0]}, {YS[1]}],\n'
    f'  "l_leg_um": {L_LEG},\n'
    f'  "commanded_c": [{C[0]:.8f}, {C[1]:.8f}, {C[2]:.8f}],\n'
    f'  "q_water_uL_s": {a.q_water},\n'
    f'  "q_oil_uL_s": {a.q_oil},\n'
    f'  "u_leg_m_s": {U_leg:.8f},\n'
    f'  "t_transit_s": {t_transit:.8f},\n'
    f'  "n_cells": {ncells}\n'
    "}\n")
print(f"geometry.json: junction x {XS[2]:.0f}-{XS[3]:.0f} um, "
      f"outlet to {XS[5]:.0f} um, transit {t_transit*1e3:.1f} ms")
