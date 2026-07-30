#!/usr/bin/env python3
"""Replication diagrams for the MCC v2 chip (600 um channels, off-chip resistors).

Emits three figures plus a CAM-ready SVG:

  mill_chip_v2.svg / _layout.png  chip fabrication drawing
  mcc_plumbing.png                system schematic (columns -> resistors -> chip)
  mcc_cross_section.png           channel stack detail + corner-gutter note

Design changes from v1 (400 um, on-chip 48 mm oil serpentine):

  - 600 um channels. The droplet regime is set by the capillary number
    Ca = mu*U/sigma, which contains no length, so widening the channel at
    fixed velocity keeps the same physics. What it buys is fabrication
    margin: endmill deflection and breakage scale as d^4, so a 0.6 mm tool
    is ~5x stiffer than the 1/64" (0.397 mm) the v1 design needed.
  - BOTH flow resistors moved off-chip into tubing. Nothing on the chip
    now does hydraulic work, so channel-length precision stops mattering
    and the milled part is just a tee plus an observation run.
  - Drive pressures fall as 1/w^2: 1.7 kPa oil / 0.83 kPa water, i.e.
    18 cm and 8 cm water columns (v1 needed 40 cm and 18 cm).

Run:  python3 gen_guide_diagrams.py
"""
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle, Polygon

HERE = Path(__file__).parent

# ---- chip layout (millimetres) ----------------------------------------------
BLANK_W, BLANK_H = 76.2, 25.4          # 1 x 3 inch blank
CH_W = 0.6                              # channel width AND depth (0.6 mm endmill)
Y_MAIN = 12.7                           # main channel centreline
OIL_PORT = (15.0, Y_MAIN)
JUNCTION = (35.0, Y_MAIN)
WATER_PORT = (35.0, 20.5)
OUT_PORT = (60.0, Y_MAIN)
HOLE_D, PAD_D, NOTCH = 1.5, 8.0, 3.0

INK, BLUE, AMBER, GREY = "#1B2733", "#2E7DB8", "#B8821F", "#8A97A3"


def chip_svg():
    def y(v):
        return BLANK_H - v
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{BLANK_W}mm" '
         f'height="{BLANK_H}mm" viewBox="0 0 {BLANK_W} {BLANK_H}">']
    p.append('<g id="outline" fill="none" stroke="#0044cc" stroke-width="0.1">')
    p.append(f'<path d="M {NOTCH} 0 L {BLANK_W} 0 L {BLANK_W} {BLANK_H} '
             f'L 0 {BLANK_H} L 0 {NOTCH} Z"/></g>')
    p.append(f'<g id="channels" fill="none" stroke="#000" stroke-width="{CH_W}" '
             f'stroke-linecap="round">')
    p.append(f'<line x1="{OIL_PORT[0]}" y1="{y(Y_MAIN)}" x2="{OUT_PORT[0]}" y2="{y(Y_MAIN)}"/>')
    p.append(f'<line x1="{WATER_PORT[0]}" y1="{y(WATER_PORT[1])}" '
             f'x2="{JUNCTION[0]}" y2="{y(Y_MAIN)}"/></g>')
    p.append('<g id="ports" fill="none" stroke="#c00" stroke-width="0.1">')
    for cx, cy in (OIL_PORT, WATER_PORT, OUT_PORT):
        p.append(f'<circle cx="{cx}" cy="{y(cy)}" r="{HOLE_D/2}"/>')
    p.append('</g>')
    p.append('<g id="reference" fill="none" stroke="#999" stroke-width="0.1" '
             'stroke-dasharray="0.8 0.5">')
    for cx, cy in (OIL_PORT, WATER_PORT, OUT_PORT):
        p.append(f'<circle cx="{cx}" cy="{y(cy)}" r="{PAD_D/2}"/>')
    p.append('</g></svg>')
    (HERE / "mill_chip_v2.svg").write_text("\n".join(p))
    print("wrote", HERE / "mill_chip_v2.svg")


def chip_layout_png():
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.plot([NOTCH, BLANK_W, BLANK_W, 0, 0, NOTCH],
            [BLANK_H, BLANK_H, 0, 0, BLANK_H - NOTCH, BLANK_H], color="#0044cc", lw=1.3)
    ax.plot([OIL_PORT[0], OUT_PORT[0]], [Y_MAIN, Y_MAIN], color="k", lw=4.5,
            solid_capstyle="round")
    ax.plot([WATER_PORT[0], JUNCTION[0]], [WATER_PORT[1], Y_MAIN], color="k", lw=4.5,
            solid_capstyle="round")
    for (cx, cy), lab in ((OIL_PORT, "OIL"), (WATER_PORT, "WATER"), (OUT_PORT, "OUT")):
        ax.add_patch(Circle((cx, cy), HOLE_D/2, fill=False, color="#c00", lw=1.3))
        ax.add_patch(Circle((cx, cy), PAD_D/2, fill=False, color=GREY, lw=0.9,
                            linestyle=(0, (3, 2))))
        ax.text(cx, cy - 5.6, lab, fontsize=8.5, ha="center", color=INK)
    ax.annotate("", xy=(JUNCTION[0], 6.0), xytext=(OUT_PORT[0], 6.0),
                arrowprops=dict(arrowstyle="<->", color="#444", lw=0.8))
    ax.text((JUNCTION[0]+OUT_PORT[0])/2, 4.6,
            "25 mm observation run\n(~25 droplets in view)", fontsize=8, ha="center", color="#444")
    ax.annotate("", xy=(OIL_PORT[0], 8.6), xytext=(JUNCTION[0], 8.6),
                arrowprops=dict(arrowstyle="<->", color="#444", lw=0.8))
    ax.text((OIL_PORT[0]+JUNCTION[0])/2, 7.3, "20 mm approach", fontsize=8,
            ha="center", color="#444")
    ax.text(BLANK_W/2, 27.6,
            'MCC chip v2 — 1×3" PMMA blank · all channels 0.6 mm wide × 0.6 mm deep '
            '(single 0.6 mm endmill)', fontsize=9.5, ha="center")
    ax.text(BLANK_W/2, 1.4,
            "no serpentine, no resistors on the chip — every channel here is just a conduit; "
            "all hydraulic resistance is set by tubing (see plumbing diagram)",
            fontsize=8, ha="center", color="#555")
    ax.text(1.0, 23.0, "notch = orientation mark", fontsize=7, color=GREY)
    ax.set_xlim(-3, 79); ax.set_ylim(-1, 29); ax.set_aspect("equal"); ax.axis("off")
    plt.tight_layout(); plt.savefig(HERE / "mill_chip_v2_layout.png", dpi=170, bbox_inches="tight")
    print("wrote", HERE / "mill_chip_v2_layout.png")


def plumbing_png():
    """Grid x 0-23.5, y 0-10.5. Chip centreline (datum) y=2.6; both bottles sit
    above it so drawn height == real head. Oil runs high (y 7.2) and drops at
    x 12.8; water runs low (y 0.8) and rises into the tee from below, so no
    two lines cross."""
    fig, ax = plt.subplots(figsize=(12.5, 6.6))
    DATUM = 2.6

    def bottle(y0, y1, col, name, sub):
        ax.add_patch(FancyBboxPatch((2.4, y0), 2.4, y1 - y0, boxstyle="round,pad=0.04",
                                    fc="white", ec=col, lw=1.8))
        ax.add_patch(Rectangle((2.5, y0 + 0.08), 2.2, (y1 - y0) * 0.46, fc=col,
                               alpha=0.28, ec="none"))
        ax.plot([3.2, 3.2], [y0 + 0.3, y1 + 0.42], color=INK, lw=1.3)
        ax.text(4.95, y1 + 0.30, "Mariotte\nair tube", fontsize=6.8, ha="left",
                va="center", color=INK)
        ax.text(3.6, y1 - 0.33, name, fontsize=10, ha="center", color=col, weight="bold")
        ax.text(3.6, y1 - 0.72, sub, fontsize=7, ha="center", color="#555")

    bottle(6.8, 8.4, AMBER, "OIL", "50 cSt + 2% Span 80")
    bottle(4.0, 5.6, BLUE, "WATER", "DI water + dye")

    ax.plot([1.3, 1.3], [DATUM, 7.5], color=GREY, lw=1.1)
    for yy, lab, col in ((DATUM, "0  (chip)", GREY), (4.4, "8 cm  → water", BLUE),
                         (7.2, "18 cm → oil", AMBER)):
        ax.plot([1.15, 1.45], [yy, yy], color=col, lw=1.5)
        ax.text(1.02, yy, lab, fontsize=8, ha="right", va="center", color=col)

    def coil(x0, x1, y, col):
        n = 26
        xs = [x0 + i * (x1 - x0) / n for i in range(n + 1)]
        ys = [y + 0.34 * (1 if i % 2 else -1) for i in range(n + 1)]
        ax.plot(xs, ys, color=col, lw=1.9)

    # oil: high route, drops into the chip inlet
    ax.plot([4.8, 6.4], [7.2, 7.2], color=AMBER, lw=1.9)
    coil(6.4, 11.4, 7.2, AMBER)
    ax.plot([11.4, 12.8], [7.2, 7.2], color=AMBER, lw=1.9)
    ax.plot([12.8, 12.8], [7.2, DATUM], color=AMBER, lw=1.9)
    ax.plot([12.8, 14.4], [DATUM, DATUM], color=AMBER, lw=1.9)
    ax.text(8.9, 6.25, "OIL RESISTOR   12 cm × 1.0 mm ID   (or 77 cm × 1/16″)",
            fontsize=8.5, ha="center", color=AMBER)

    # water: low route, rises into the tee from below
    ax.plot([4.8, 4.8], [4.4, 0.8], color=BLUE, lw=1.9)
    ax.plot([4.8, 6.4], [0.8, 0.8], color=BLUE, lw=1.9)
    coil(6.4, 11.4, 0.8, BLUE)
    ax.plot([11.4, 16.4], [0.8, 0.8], color=BLUE, lw=1.9)
    ax.plot([16.4, 16.4], [0.8, 1.4], color=BLUE, lw=1.9)
    ax.text(8.9, 0.02, "WATER RESISTOR   23 cm × 0.4 mm ID   (or 55 cm × 0.5 mm)",
            fontsize=8.5, ha="center", color=BLUE)

    # chip: main channel across, water stub rising to meet it -> clean tee
    ax.add_patch(FancyBboxPatch((14.4, 1.4), 4.4, 2.3, boxstyle="round,pad=0.06",
                                fc="#F3F6F9", ec=INK, lw=1.6))
    ax.plot([14.4, 18.8], [DATUM, DATUM], color=INK, lw=2.8, solid_capstyle="round")
    ax.plot([16.4, 16.4], [1.4, DATUM], color=INK, lw=2.8, solid_capstyle="round")
    ax.text(16.6, 3.32, "CHIP", fontsize=10, ha="center", color=INK, weight="bold")
    ax.text(16.6, 1.05, "a tee + a 25 mm observation run", fontsize=7.5,
            ha="center", color="#555")

    ax.plot([18.8, 20.6], [DATUM, DATUM], color="#5A6B7A", lw=1.9)
    ax.add_patch(Rectangle((20.6, 1.95), 1.5, 1.35, fc="none", ec=GREY, lw=1.4))
    ax.text(21.35, 1.6, "waste (open to air)", fontsize=7.5, ha="center", color=GREY)

    ax.add_patch(Circle((16.6, 4.7), 0.42, fc="none", ec=INK, lw=1.5))
    ax.plot([16.6, 16.6], [4.25, 3.8], color=GREY, lw=1.0, ls=":")
    ax.text(17.4, 4.7, "camera ≥120 fps", fontsize=8.5, va="center", color=INK)

    ax.text(0.2, 10.0, "MCC v2 plumbing — 600 µm chip, hydrostatic actuation",
            fontsize=12.5, weight="bold", color=INK)
    ax.text(0.2, 9.35, "Bottle height sets the pressure (1 cm water ≈ 98 Pa); tubing sets the "
            "resistance. The chip does neither — so its dimensions need not be precise.",
            fontsize=9, color="#444", va="center")
    ax.text(0.2, -0.75, "The Mariotte air tube fixes pressure at the tube mouth, so the drive does "
            "not sag as the bottle drains.  Mount both bottles on one motorised\nvertical axis and "
            "the two column heights become the chamber's two actuators.", fontsize=8, color="#555",
            va="top")
    ax.set_xlim(0, 23.5); ax.set_ylim(-1.6, 10.5); ax.axis("off")
    plt.tight_layout(); plt.savefig(HERE / "mcc_plumbing.png", dpi=170, bbox_inches="tight")
    print("wrote", HERE / "mcc_plumbing.png")


def cross_section_png():
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.0), gridspec_kw={"width_ratios": [1.15, 1]})

    ax = axes[0]
    ax.add_patch(Rectangle((0, 0), 10, 2.2, fc="#E8EDF1", ec=INK, lw=1.2))
    ax.add_patch(Rectangle((3.5, 0.9), 3.0, 1.31, fc="white", ec=INK, lw=1.2))
    ax.add_patch(Rectangle((0, 2.2), 10, 0.22, fc="#D9B44A", ec="none"))
    ax.add_patch(Rectangle((0, 2.42), 10, 1.1, fc="#E8EDF1", ec=INK, lw=1.2))
    ax.text(5.0, 1.5, "channel\n0.6 × 0.6 mm", fontsize=8.5, ha="center", color=INK)
    ax.text(10.4, 1.0, "1.5 mm PMMA\n(flow layer)", fontsize=8, va="center", color="#444")
    ax.text(10.4, 2.31, "3M 468MP adhesive", fontsize=8, va="center", color="#8A6D1D")
    ax.text(10.4, 2.97, "1 mm PMMA (cover)", fontsize=8, va="center", color="#444")
    for xx in (3.5, 6.5):
        ax.plot([xx], [2.2], marker="o", ms=7, mfc="none", mec="#C0392B", mew=1.6)
    ax.text(5.0, 3.75, "the two upper corners are where oil bypasses the droplet",
            fontsize=8, ha="center", color="#C0392B")
    ax.set_xlim(-0.6, 16.5); ax.set_ylim(-0.5, 4.2); ax.set_aspect("equal"); ax.axis("off")
    ax.text(-0.4, 4.05, "Bonded stack (milled)", fontsize=10.5, color=INK, weight="bold")

    ax = axes[1]
    ax.add_patch(Rectangle((0.4, 1.0), 3.4, 2.0, fc="white", ec=INK, lw=1.5))
    ax.text(2.1, 3.35, "MILLED  90°", fontsize=9, ha="center", color=INK)
    ax.text(2.1, 0.55, "gutters small\nsqueezing clean", fontsize=8, ha="center", color="#3E8E5C")
    ax.add_patch(Polygon([(5.2, 1.0), (8.6, 1.0), (9.4, 3.0), (4.4, 3.0)],
                         closed=True, fc="white", ec=INK, lw=1.5))
    ax.text(6.9, 3.35, "LASER  ~76°", fontsize=9, ha="center", color=INK)
    ax.text(6.9, 0.55, "bigger gutters\nsqueezing leaks", fontsize=8, ha="center", color="#C0392B")
    for xx in (4.4, 9.4):
        ax.plot([xx], [3.0], marker="o", ms=7, mfc="none", mec="#C0392B", mew=1.6)
    ax.set_xlim(0, 10.5); ax.set_ylim(0, 4.2); ax.set_aspect("equal"); ax.axis("off")
    ax.text(0.0, 4.05, "Why the mill is preferred", fontsize=10.5, color=INK, weight="bold")
    plt.tight_layout(); plt.savefig(HERE / "mcc_cross_section.png", dpi=170, bbox_inches="tight")
    print("wrote", HERE / "mcc_cross_section.png")


if __name__ == "__main__":
    chip_svg(); chip_layout_png(); plumbing_png(); cross_section_png()
