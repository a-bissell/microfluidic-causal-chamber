#!/usr/bin/env python3
"""Generate system/blockMeshDict for the MILLABLE 400 um T-junction chip.

Digital twin of the chip fabricated per "The Makers Guide to Microfluidics"
(CNC-milled PMMA, 3M 468MP bonding): 400 um channels — one pass of a 1/64"
endmill at 0.4 mm depth — for both phases, so no tool changes and no
sub-250 um features.

Hydraulic design (Ca = 0.032, Q_disp/Q_cont = 0.25, same regime as the
validated tjunction_2d_serpentine case):

BOTH flow resistors are OFF-CHIP tubing in the current design (plan §2.1);
neither is milled into the blank. They appear here as in-domain channels
only because a pressure boundary condition needs the resistance to live
somewhere, and the solver has no lumped-resistance BC. What the junction
sees is a flow rate, so any upstream geometry of the right resistance does:

  - oil feed: modelled as a 46 mm x 400 um channel, standing in for the
    off-chip oil resistor -- ~19 cm of 1/16" (1.59 mm) ID at 800 um. That
    tubing plus the chip's own channels comes to 8.08e10 Pa.s/m^3 against
    this model's 7.72e10, i.e. 4.6% -- so the bench rig reproduces the
    simulated operating point. (An earlier revision described this as an
    on-chip serpentine to be folded into the blank. It is not; do not mill
    it.)
  - water feed: modelled as an 80 um x 27 mm channel, the 2D hydraulic
    equivalent of ~31 cm of 0.3 mm-ID microbore tubing upstream of the
    chip port (water is too thin for a millable on-chip resistor at any of
    these widths -- it would need sub-250 um features)
  - operating point: P_cont ~ 3.9 kPa, P_disp ~ 1.8 kPa — inside the
    range of balloons (~2-4 kPa) or hydrostatic columns (10 cm H2O
    = 0.98 kPa), so the guide's fluid-handling rig can actuate it
  - capillary entry threshold at 400 um: ~150 Pa (vs ~800 at 150 um),
    a much wider stable window relative to actuation noise
  - expected observables: ~9 Hz, ~540 um slugs, ~25 mm/s

Topology is simpler than the serpentine case: the oil feed is full channel
width, so the main row needs no y-strips; only the water inlet splits into
x-strips (160/80/160 um) to meet the narrow water-resistor channel.

Run:  python3 gen_blockmesh.py   (writes system/blockMeshDict)
"""
from pathlib import Path

# ---- geometry (micrometres) -------------------------------------------------
import argparse
_ap = argparse.ArgumentParser()
_ap.add_argument("--w-main", type=float, default=400.0,
                 help="Main channel width AND depth (um). 400 = 1/64\" endmill "
                      "(the original design); 600 or 800 are far more "
                      "replicable (tool stiffness ~ d^4, so a 0.6 mm tool is "
                      "5x and a 0.8 mm tool 16x stiffer than 1/64\"). All "
                      "width-like dimensions scale with this; channel LENGTHS "
                      "stay fixed, so drive pressures fall as 1/w^2 and the "
                      "regime (Ca = mu*U/sigma) is unchanged.")
W_MAIN = _ap.parse_args().w_main
_k = W_MAIN / 400.0                      # scale factor vs the original design

L_OIL_FEED = 46000.0    # in-domain stand-in for the off-chip oil resistor tubing
                        # -- a LENGTH, unscaled
L_APPROACH = 2000.0     # feed exit -> junction
L_OUTLET = 4000.0       # junction -> outlet
W_RES_WAT = 80.0 * _k   # water resistor (tubing proxy) -- a WIDTH, scales
L_RES_WAT = 27000.0
L_WAT_INLET = 2000.0    # water leg between resistor and junction
DEPTH = W_MAIN          # milled depth (z; 2D empty direction) -- square section

DX = W_MAIN / 20.0      # transverse cell size (20 cells across main channel)

x_j0 = L_APPROACH                        # junction left edge
x_j1 = x_j0 + W_MAIN                     # junction right edge
# junction sub-strips straddle the water leg; they are fractions of W_MAIN
XS = [-L_OIL_FEED, 0.0, x_j0, x_j0 + 0.4 * W_MAIN, x_j0 + 0.6 * W_MAIN, x_j1,
      x_j1 + L_OUTLET]
YS = [0.0, W_MAIN, W_MAIN + L_WAT_INLET, W_MAIN + L_WAT_INLET + L_RES_WAT]
ZS = [0.0, DEPTH]

def _n(length):                          # uniform-resolution cell count
    return max(1, round(length / DX))
# the graded oil-feed block keeps its hand-tuned count; the rest follow DX
NX = [100, _n(L_APPROACH), _n(0.4 * W_MAIN), _n(0.2 * W_MAIN), _n(0.4 * W_MAIN),
      _n(L_OUTLET)]
NY = [_n(W_MAIN), 40, 60]
GX = [0.1, 1, 1, 1, 1, 1]       # oil feed refines toward the chip
GY = [1, 6, 12]                 # water legs refine toward the junction

# (x-interval, y-interval) index pairs
BLOCKS = (
    [(i, 0) for i in range(6)]           # main channel row, full width
    + [(i, 1) for i in (2, 3, 4)]        # water inlet strips
    + [(3, 2)]                           # water resistor (tubing proxy)
)

# ---- mesh assembly (same machinery as tjunction_2d_serpentine) ---------------
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
    hexes.append((v, NX[ix], NY[iy], GX[ix], GY[iy]))
    faces = [
        ('x', x0, (v[0], v[4], v[7], v[3])),
        ('x', x1, (v[1], v[2], v[6], v[5])),
        ('y', y0, (v[0], v[1], v[5], v[4])),
        ('y', y1, (v[3], v[7], v[6], v[2])),
        ('z', ZS[0], (v[0], v[3], v[2], v[1])),
        ('z', ZS[1], (v[4], v[5], v[6], v[7])),
    ]
    for axis, coord, quad in faces:
        face_count.setdefault(tuple(sorted(quad)), []).append((axis, coord, quad))

for ix, iy in BLOCKS:
    add_block(ix, iy)

patches = {'oil_inlet': [], 'water_inlet': [], 'outlet': [], 'walls': [], 'frontAndBack': []}
for entries in face_count.values():
    if len(entries) != 1:
        continue
    axis, coord, quad = entries[0]
    if axis == 'z':
        patches['frontAndBack'].append(quad)
    elif axis == 'x' and coord == XS[0]:
        patches['oil_inlet'].append(quad)
    elif axis == 'x' and coord == XS[-1]:
        patches['outlet'].append(quad)
    elif axis == 'y' and coord == YS[-1]:
        patches['water_inlet'].append(quad)
    else:
        patches['walls'].append(quad)

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
for v, nx, ny, gx, gy in hexes:
    lines.append(f"    hex ({' '.join(map(str, v))}) ({nx} {ny} 1) "
                 f"simpleGrading ({gx} {gy} 1)")
lines.append(");\n\nedges\n(\n);\n\nboundary\n(")
TYPES = {'oil_inlet': 'patch', 'water_inlet': 'patch', 'outlet': 'patch',
         'walls': 'wall', 'frontAndBack': 'empty'}
for name, quads in patches.items():
    lines.append(f"    {name}\n    {{\n        type {TYPES[name]};\n        faces\n        (")
    for q in quads:
        lines.append(f"            ({' '.join(map(str, q))})")
    lines.append("        );\n    }")
lines.append(");\n\nmergePatchPairs\n(\n);\n\n// ************************************************************************* //")

out = Path(__file__).parent / "system" / "blockMeshDict"
out.parent.mkdir(exist_ok=True)
out.write_text("\n".join(lines) + "\n")
ncells = sum(nx * ny for _, nx, ny, _, _ in hexes)
print(f"wrote {out}: {len(verts)} vertices, {len(hexes)} blocks, {ncells} cells")

# ---- setFieldsDict ----------------------------------------------------------
# Emitted here rather than hand-maintained, for the same reason as in
# tjunction_3d_mill: every coordinate below scales with --w-main, so a dict
# left at the 400 um literals would seed water INSIDE the main channel on any
# wider chip. setFields would exit 0 and interFoam would run happily -- a
# silently wrong initial condition, not an error.
#
# Two regions, and both matter. The water LEG is the obvious one. The
# RESISTOR channel must be pre-filled too: it is 27 mm of narrow duct, and
# starting it full of oil would make the water spend most of the run pushing
# that column out before it ever reaches the junction.
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
    volScalarFieldValue alpha.water 0       // oil everywhere by default
);

regions
(
    // water inlet leg: junction width, from the top of the main channel up
    boxToCell
    {{
        box ({XS[2]*1e-6:.6g} {W_MAIN*1e-6:.6g} {ZS[0]*1e-6:.6g}) \
({XS[5]*1e-6:.6g} {YS[2]*1e-6:.6g} {ZS[1]*1e-6:.6g});
        fieldValues ( volScalarFieldValue alpha.water 1 );
    }}
    // water resistor ({W_RES_WAT:.0f} um x {L_RES_WAT/1000:.0f} mm tubing proxy)
    boxToCell
    {{
        box ({XS[3]*1e-6:.6g} {YS[2]*1e-6:.6g} {ZS[0]*1e-6:.6g}) \
({XS[4]*1e-6:.6g} {YS[3]*1e-6:.6g} {ZS[1]*1e-6:.6g});
        fieldValues ( volScalarFieldValue alpha.water 1 );
    }}
);

// ************************************************************************* //
""")
print(f"wrote {sf}: leg x {XS[2]:.0f}-{XS[5]:.0f} y {W_MAIN:.0f}-{YS[2]:.0f}, "
      f"resistor x {XS[3]:.0f}-{XS[4]:.0f} y {YS[2]:.0f}-{YS[3]:.0f} um")
