#!/usr/bin/env python3
"""Generate system/blockMeshDict for the 3D millable-chip T-junction twin.

The 2D cases model a mid-depth slice; a real 400x400 um square channel has
corner gutters -- the four corners a droplet's rounded interface can never
seal -- through which oil bypasses the forming droplet. 2D therefore
overstates junction blockage, biasing pinch-off timing and slug length.
This case quantifies that: the tjunction_2d_mill junction geometry, in 3D,
at the identical operating point (velocity inlets, Ca = 0.032, q = 0.25).

Design choices:
  - Junction region only (2 mm approach + junction + 4 mm outlet + 2 mm
    water leg). No feed serpentine/resistor: velocity inlets pin the flow
    rates directly, so upstream hydraulics are unnecessary for a fidelity
    check. x coordinates match tjunction_2d_mill's junction/outlet frame
    (junction at x = 2000-2400 um) so the droplet extractor's geometry
    parameters are identical.
  - Half-depth domain: wall at z = 0, symmetry plane at z = 200 um
    (mid-depth). Valid while the flow stays z-symmetric, which is expected
    at these capillary numbers; a full-depth spot check is the fallback if
    results look odd.

Run:  python3 gen_blockmesh.py             (DX = 20 um, ~84k cells)
      python3 gen_blockmesh.py --dx 13.3   (finer, for a later convergence pass)
"""
import argparse
from pathlib import Path

# ---- geometry (micrometres) -------------------------------------------------
# Channel LENGTHS are fixed while WIDTHS scale, matching tjunction_2d_mill:
# holding Ca fixed means holding velocity fixed, so a wider chip runs the
# same regime on lower drive pressures (see results/scaleup_2026-07).
L_APPROACH = 2000.0     # oil inlet -> junction left edge
L_OUTLET = 4000.0       # junction right edge -> outlet
L_WAT_LEG = 2000.0      # water inlet leg above the junction

BASE_DX = 20.0          # tuned for the 400 um chip: w/20 across the channel
_args = argparse.ArgumentParser()
_args.add_argument("--w-main", type=float, default=400.0,
                    help="Channel width (y) AND full depth (z), in um. 400 is "
                         "the original 1/64\" design; 800 is the replicable "
                         "one (endmill stiffness ~ d^4). --dx defaults to "
                         "w/20 so relative resolution is width-independent.")
_args.add_argument("--dx", type=float, default=None,
                    help="Cell size (um), uniform in x/y/z. Default w/20, "
                         "which reproduces the BASE_DX=20 tuning at 400 um.")
_args.add_argument("--two-d", action="store_true",
                    help="Emit the SAME domain as a single-cell-thick 2D mesh "
                         "(frontAndBack empty, no symmetry plane). This is the "
                         "controlled baseline for the 2D->3D fidelity "
                         "comparison: one generator, one geometry, one flag, "
                         "so dimensionality is the only thing that differs.")
_args.add_argument("--profile", choices=["square", "trapezoid"], default="square",
                    help="Channel cross-section. 'square' = milled (default, "
                         "half-depth domain with a mid-plane symmetry). "
                         "'trapezoid' = laser-cut V-groove with a flat root: "
                         "wide at the bonded lid, narrow at the root, FULL "
                         "depth (a V-groove is not symmetric top-to-bottom, "
                         "so the symmetry plane is unavailable).")
_args.add_argument("--w-root", type=float, default=200.0,
                    help="Trapezoid width (um) at the root; lid width is W_MAIN.")
_parsed = _args.parse_args()
W_MAIN = _parsed.w_main          # channel width (y) and full depth (z)
DEPTH = W_MAIN                   # square section; 3D models half the depth
DX = _parsed.dx if _parsed.dx is not None else W_MAIN / 20.0
PROFILE = _parsed.profile
TWO_D = _parsed.two_d
W_ROOT = _parsed.w_root * (W_MAIN / 400.0)   # a WIDTH, so it scales

x_j0, x_j1 = L_APPROACH, L_APPROACH + W_MAIN
XS = [0.0, x_j0, x_j1, x_j1 + L_OUTLET]
YS = [0.0, W_MAIN, W_MAIN + L_WAT_LEG]
# square: model half the depth and mirror at mid-plane. trapezoid: the
# cross-section is asymmetric in z (wide at lid, narrow at root), so the
# full depth must be meshed.
# 3D square: model half the depth, mirror at the mid-plane. Trapezoid is
# asymmetric in z so it needs full depth. 2D: full depth as the empty-
# direction thickness, matching tjunction_2d_mill, so volumetric fluxes are
# directly comparable to the pressure-driven 2D runs.
ZS = [0.0, DEPTH / 2.0] if (PROFILE == "square" and not TWO_D) else [0.0, DEPTH]

# Counts follow from the actual geometry rather than from scaling the 400 um
# tuning, so they stay correct when width and dx move together.
def _n(length):
    return max(1, round(length / DX))
NX = [_n(L_APPROACH), _n(W_MAIN), _n(L_OUTLET)]
NY = [_n(W_MAIN), _n(L_WAT_LEG)] if PROFILE == "square" else \
     [max(1, round(0.8 * W_MAIN / DX)), _n(L_WAT_LEG)]
NZ = 1 if TWO_D else _n(ZS[1])

# fluid blocks as (x-interval, y-interval) index pairs
BLOCKS = [(0, 0), (1, 0), (2, 0),   # main channel: approach, junction, outlet
          (1, 1)]                   # water leg above the junction

# ---- mesh assembly ----------------------------------------------------------
verts: dict[tuple, int] = {}
def vid(x, y, z):
    key = (round(x, 3), round(y, 3), round(z, 3))
    if key not in verts:
        verts[key] = len(verts)
    return verts[key]

hexes = []
face_count: dict[tuple, list] = {}

def chan_y(iy, z):
    """y bounds of interval `iy` at height z.

    Square: constant. Trapezoid: the main channel (iy=0) narrows linearly
    from W_MAIN at the lid (z=DEPTH) to W_ROOT at the root (z=0), centred on
    the channel axis; the water leg (iy=1) sits on top of it, so its lower
    bound follows the main channel's upper wall (a slanted but conformal
    shared face) while its outer bound stays flat.
    """
    if PROFILE == "square":
        return YS[iy], YS[iy + 1]
    w = W_ROOT + (W_MAIN - W_ROOT) * (z / DEPTH)
    lo, hi = 0.5 * (W_MAIN - w), 0.5 * (W_MAIN + w)
    return (lo, hi) if iy == 0 else (hi, YS[2])


def add_block(ix, iy):
    x0, x1 = XS[ix], XS[ix + 1]
    y0b, y1b = chan_y(iy, ZS[0])       # bounds at the lower z level
    y0t, y1t = chan_y(iy, ZS[1])       # bounds at the upper z level
    v = [vid(x0, y0b, ZS[0]), vid(x1, y0b, ZS[0]), vid(x1, y1b, ZS[0]), vid(x0, y1b, ZS[0]),
         vid(x0, y0t, ZS[1]), vid(x1, y0t, ZS[1]), vid(x1, y1t, ZS[1]), vid(x0, y1t, ZS[1])]
    hexes.append((v, NX[ix], NY[iy], NZ))
    faces = [
        ('x', x0, (v[0], v[4], v[7], v[3])),
        ('x', x1, (v[1], v[2], v[6], v[5])),
        # representative y for classification: only YS[-1] (the flat top of
        # the water leg) needs to match exactly; the trapezoid's side walls
        # are slanted and fall through to 'walls'.
        ('y', y0b, (v[0], v[1], v[5], v[4])),
        ('y', y1t, (v[3], v[7], v[6], v[2])),
        ('z', ZS[0], (v[0], v[3], v[2], v[1])),
        ('z', ZS[1], (v[4], v[5], v[6], v[7])),
    ]
    for axis, coord, quad in faces:
        face_count.setdefault(tuple(sorted(quad)), []).append((axis, coord, quad))

for ix, iy in BLOCKS:
    add_block(ix, iy)

patches = {'oil_inlet': [], 'water_inlet': [], 'outlet': [],
           'symmetryPlane': [], 'frontAndBack': [], 'walls': []}
for entries in face_count.values():
    if len(entries) != 1:
        continue
    axis, coord, quad = entries[0]
    if axis == 'x' and coord == XS[0]:
        patches['oil_inlet'].append(quad)
    elif axis == 'x' and coord == XS[-1]:
        patches['outlet'].append(quad)
    elif axis == 'y' and coord == YS[-1]:
        patches['water_inlet'].append(quad)
    elif axis == 'z' and TWO_D:
        patches['frontAndBack'].append(quad)
    elif axis == 'z' and coord == ZS[1] and PROFILE == "square":
        patches['symmetryPlane'].append(quad)
    else:
        patches['walls'].append(quad)

# ---- emit -------------------------------------------------------------------
lines = ["""/*--------------------------------*- C++ -*----------------------------------*\\
| Generated by gen_blockmesh.py — edit that script, not this file.            |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

scale 1e-6;   // coordinates below are micrometres

vertices
("""]
for (x, y, z), i in sorted(verts.items(), key=lambda kv: kv[1]):
    lines.append(f"    ({x} {y} {z})   // {i}")
lines.append(");\n\nblocks\n(")
for v, nx, ny, nz in hexes:
    lines.append(f"    hex ({' '.join(map(str, v))}) ({nx} {ny} {nz}) "
                 f"simpleGrading (1 1 1)")
lines.append(");\n\nedges\n(\n);\n\nboundary\n(")
TYPES = {'oil_inlet': 'patch', 'water_inlet': 'patch', 'outlet': 'patch',
         'symmetryPlane': 'symmetry', 'frontAndBack': 'empty', 'walls': 'wall'}
for name, quads in patches.items():
    if not quads:          # e.g. no symmetry plane in trapezoid mode
        continue
    lines.append(f"    {name}\n    {{\n        type {TYPES[name]};\n        faces\n        (")
    for q in quads:
        lines.append(f"            ({' '.join(map(str, q))})")
    lines.append("        );\n    }")
lines.append(");\n\nmergePatchPairs\n(\n);\n\n// ************************************************************************* //")

out = Path(__file__).parent / "system" / "blockMeshDict"
out.parent.mkdir(exist_ok=True)
out.write_text("\n".join(lines) + "\n")
ncells = sum(nx * ny * nz for _, nx, ny, nz in hexes)
print(f"wrote {out}: {len(verts)} vertices, {len(hexes)} blocks, {ncells} cells")

# ---- setFieldsDict ----------------------------------------------------------
# Emitted here, not hand-maintained: the initial water column spans the water
# leg only (y from W_MAIN up), and a box left at the 400 um values would seed
# water INSIDE the main channel on any wider chip -- a silent, wrong initial
# condition rather than an error.
sf = Path(__file__).parent / "system" / "setFieldsDict"
sf.write_text(f"""/*--------------------------------*- C++ -*----------------------------------*\\
| Generated by gen_blockmesh.py — edit that script, not this file.            |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      setFieldsDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

defaultFieldValues
(
    volScalarFieldValue alpha.water 0
);

regions
(
    // water leg above the junction, from the top of the main channel up
    boxToCell
    {{
        box ({XS[1]*1e-6:.6g} {W_MAIN*1e-6:.6g} {ZS[0]*1e-6:.6g}) \
({XS[2]*1e-6:.6g} {YS[2]*1e-6:.6g} {ZS[1]*1e-6:.6g});
        fieldValues ( volScalarFieldValue alpha.water 1 );
    }}
);

// ************************************************************************* //
""")
print(f"wrote {sf}: water leg x {XS[1]:.0f}-{XS[2]:.0f}, y {W_MAIN:.0f}-{YS[2]:.0f}, "
      f"z {ZS[0]:.0f}-{ZS[1]:.0f} um")
