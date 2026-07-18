#!/usr/bin/env python3
"""Fabrication layout for the MCC mill chip v1 on a 1x3" (25.4 x 76.2 mm) blank.

Emits mill_chip_v1.svg (CAM-ready, mm units, one SVG group per operation
layer) and mill_chip_v1_preview.png (dimensioned shop drawing) from the
same coordinates, so the preview always matches the cut file.

Design source: simulation/openfoam/tjunction_2d_mill (sim-verified at
P_cont = 3.9 kPa / P_disp = 1.8 kPa; see results/mill_2026-07). Key facts:

  - All channels 400 um wide x 400 um deep: one 1/64" endmill, two 0.2 mm
    passes (the Makers-Guide recipe).
  - Oil feed: the sim's "46 mm serpentine + 2 mm approach" unfolds into a
    single STRAIGHT 48 mm run on a 3" blank - no folding, no corner
    artifacts, one continuous pass.
  - Water feed resistance is OFF-chip (~31 cm of 0.3 mm-ID tubing on the
    water port); the on-chip water leg is 7.3 mm here vs 2 mm in the sim,
    adding only ~11 Pa (negligible: water is 48x less viscous than oil).
  - Outlet run is 6 mm (sim: 4.4 mm); the extra 1.6 mm adds ~115 Pa
    (~3% of P_cont) of downstream resistance - within the response map's
    cell spacing, but if being fussy, run the oil column ~1 cm lower...
    or just trust the map: it's the knob you'll tune anyway.
  - Port holes 1.5 mm through; 8 mm pads drawn as reference for the
    3D-printed luer surface mounts + 468MP donuts (match to your STL).

SVG layers (groups): "outline" (cut through), "channels" (0.4 mm deep),
"ports" (through-holes), "reference" (pads + text - don't cut).
"""
from pathlib import Path

# ---- layout (millimetres) ----------------------------------------------------
BLANK_W, BLANK_H = 76.2, 25.4
CH_W = 0.4                       # channel width = 1/64" endmill
Y_MAIN = 10.0                    # main channel centerline
OIL_PORT = (12.0, Y_MAIN)        # oil inlet port (hole center)
JUNCTION = (60.0, Y_MAIN)        # T-junction center
OUT_PORT = (66.0, Y_MAIN)        # outlet port
WATER_PORT = (60.0, 17.5)        # water inlet port (above junction)
HOLE_D = 1.5                     # port through-hole diameter
PAD_D = 8.0                      # luer mount pad (reference only)
NOTCH = 3.0                      # top-left orientation chamfer

OIL_PATH_MM = JUNCTION[0] - OIL_PORT[0]          # 48.0 -> ~3.46 kPa at ref flow
OUTLET_MM = OUT_PORT[0] - JUNCTION[0]            # 6.0
WATER_LEG_MM = WATER_PORT[1] - Y_MAIN            # 7.5 (hole center to channel CL)

def svg():
    p = []
    p.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{BLANK_W}mm" '
             f'height="{BLANK_H}mm" viewBox="0 0 {BLANK_W} {BLANK_H}">')
    # outline with orientation notch (top-left, SVG y-down: top = y0)
    p.append('<g id="outline" fill="none" stroke="#0044cc" stroke-width="0.1">')
    p.append(f'<path d="M {NOTCH} 0 L {BLANK_W} 0 L {BLANK_W} {BLANK_H} '
             f'L 0 {BLANK_H} L 0 {NOTCH} Z"/>')
    p.append('</g>')

    def y(v):   # flip: layout is y-up, SVG is y-down
        return BLANK_H - v

    p.append(f'<g id="channels" fill="none" stroke="#000000" '
             f'stroke-width="{CH_W}" stroke-linecap="round">')
    p.append(f'<line x1="{OIL_PORT[0]}" y1="{y(Y_MAIN)}" '
             f'x2="{OUT_PORT[0]}" y2="{y(Y_MAIN)}"/>')
    p.append(f'<line x1="{WATER_PORT[0]}" y1="{y(WATER_PORT[1])}" '
             f'x2="{JUNCTION[0]}" y2="{y(Y_MAIN)}"/>')
    p.append('</g>')

    p.append('<g id="ports" fill="none" stroke="#cc0000" stroke-width="0.1">')
    for cx, cy in (OIL_PORT, WATER_PORT, OUT_PORT):
        p.append(f'<circle cx="{cx}" cy="{y(cy)}" r="{HOLE_D/2}"/>')
    p.append('</g>')

    p.append('<g id="reference" fill="none" stroke="#999999" '
             'stroke-width="0.1" stroke-dasharray="0.8 0.5">')
    for cx, cy in (OIL_PORT, WATER_PORT, OUT_PORT):
        p.append(f'<circle cx="{cx}" cy="{y(cy)}" r="{PAD_D/2}"/>')
    p.append('</g>')
    p.append('<g id="labels" fill="#999999" font-size="1.8" '
             'font-family="sans-serif">')
    p.append(f'<text x="{OIL_PORT[0]-3}" y="{y(Y_MAIN-5.5)}">OIL</text>')
    p.append(f'<text x="{WATER_PORT[0]-4.5}" y="{y(WATER_PORT[1]+5)}">WATER</text>')
    p.append(f'<text x="{OUT_PORT[0]-2.5}" y="{y(Y_MAIN-5.5)}">OUT</text>')
    p.append('</g>')
    p.append('</svg>')
    return "\n".join(p)


def preview(out_png):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    fig, ax = plt.subplots(figsize=(11, 4.4))
    ax.plot([NOTCH, BLANK_W, BLANK_W, 0, 0, NOTCH],
            [BLANK_H, BLANK_H, 0, 0, BLANK_H - NOTCH, BLANK_H],
            color="#0044cc", lw=1.2)
    ax.plot([OIL_PORT[0], OUT_PORT[0]], [Y_MAIN, Y_MAIN], color="k", lw=3,
            solid_capstyle="round")
    ax.plot([WATER_PORT[0], JUNCTION[0]], [WATER_PORT[1], Y_MAIN], color="k", lw=3,
            solid_capstyle="round")
    for cx, cy in (OIL_PORT, WATER_PORT, OUT_PORT):
        ax.add_patch(Circle((cx, cy), HOLE_D / 2, fill=False, color="#cc0000", lw=1.2))
        ax.add_patch(Circle((cx, cy), PAD_D / 2, fill=False, color="#999999",
                            lw=0.9, linestyle=(0, (3, 2))))
    ann = dict(fontsize=8, color="#333333", ha="center")
    ax.annotate("", xy=(OIL_PORT[0], 5.5), xytext=(JUNCTION[0], 5.5),
                arrowprops=dict(arrowstyle="<->", color="#333333", lw=0.8))
    ax.text((OIL_PORT[0] + JUNCTION[0]) / 2, 4.2,
            f"oil feed {OIL_PATH_MM:.0f} mm (straight — no serpentine needed on 3\")",
            **ann)
    ax.annotate("", xy=(JUNCTION[0], 6.8), xytext=(OUT_PORT[0], 6.8),
                arrowprops=dict(arrowstyle="<->", color="#333333", lw=0.8))
    ax.text(63.0, 5.6, f"{OUTLET_MM:.0f} mm", **ann)
    ax.annotate("", xy=(56.4, Y_MAIN), xytext=(56.4, WATER_PORT[1]),
                arrowprops=dict(arrowstyle="<->", color="#333333", lw=0.8))
    ax.text(54.2, 13.6, f"{WATER_LEG_MM:.1f} mm", **ann)
    ax.text(38, 26.4, 'MCC mill chip v1 — 1×3" blank, channels 0.4 mm wide × 0.4 mm deep '
            '(1/64" endmill, two 0.2 mm passes)', fontsize=9, ha="center")
    ax.text(38, 1.2, "port holes ⌀1.5 thru (red) · pads ⌀8 reference for luer mounts "
            "+ 468MP donuts (grey) · water resistance off-chip: 31 cm of 0.3 mm-ID tubing",
            fontsize=7.5, color="#555555", ha="center")
    ax.text(OIL_PORT[0], Y_MAIN - 5.6, "OIL", **ann)
    ax.text(WATER_PORT[0], WATER_PORT[1] + 4.7, "WATER", **ann)
    ax.text(OUT_PORT[0] + 1.5, Y_MAIN - 5.6, "OUT", **ann)
    ax.set_xlim(-2, 78.2)
    ax.set_ylim(-1, 28.2)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(out_png, dpi=170, bbox_inches="tight")
    print("saved", out_png)


if __name__ == "__main__":
    here = Path(__file__).parent
    (here / "mill_chip_v1.svg").write_text(svg())
    print("saved", here / "mill_chip_v1.svg")
    print(f"oil path {OIL_PATH_MM} mm -> ~{OIL_PATH_MM*72:.0f} Pa at reference flow "
          f"(sim serpentine+approach: 48 mm -> ~3456 Pa; match)")
    preview(here / "mill_chip_v1_preview.png")
