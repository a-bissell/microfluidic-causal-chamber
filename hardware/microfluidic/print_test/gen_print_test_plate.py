#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = ["cadquery>=2.4", "matplotlib"]
# ///
"""Resin print test plate: can a monolithic printed chip replace the milled one?

Run:  uv run gen_print_test_plate.py        (no setup; uv fetches CadQuery)

Designed for the Formlabs Form Studio 1 (MSLA, 35 um XY pixel, 405 nm) in
Alpha Clear, printed FLAT and FLOOR-DOWN directly on the build platform -- the
orientation a planar chip would use. Every Z dimension is a multiple of
100 um, Alpha Clear's primary layer height, so no feature falls between
layers.

Each coupon answers one question the milled design never had to ask:

  W   channel WIDTH sweep    400-1200 um, nominally square, open both ends.
      Saw across at the side notches and measure the sections. XY is set by
      pixels (800 um is 22.9 px), so expect +-1 px (35 um) of quantisation.
  H   channel HEIGHT sweep   800 um wide, 800-1200 um tall. In bottom-up MSLA
      the layers that close a channel cure with the trapped liquid resin
      ABOVE the cure plane, and light that is not absorbed keeps going into
      it. Over-cure therefore grows down from the CEILING and eats channel
      height -- worst in a clear resin, which carries the least absorber.
      Whichever nominal height prints as 800 um is the Z compensation.
  T600  printed twin of the v2 milled chip, coordinates imported from
      ../gen_guide_diagrams.py, flat 1.5 mm port holes so your existing
      surface-mount Luers + 468MP donuts fit unchanged. 21 mm of enclosed
      main channel (6 mm approach + 15 mm outlet) and a 7.8 mm water leg.
  T800  same layout at 800 um with female Luer sockets printed in, testing
      whether the fittings can be part of the chip.
  LUER  three sockets identical to T800's, opening diameter -0.10 / 0 /
      +0.10 mm. Resin holes print undersize; find the offset that seats a
      syringe tip before trusting T800's.
  THF   9 x 9 x 2 mm flat coupon. Its top face was cured against the vat film,
      as is a channel FLOOR. Sized to lie in a standard 10 mm cuvette for a
      sessile drop under oil.
  THV   9 x 2 x 9 mm upright coupon. Its large faces are stacked layer edges,
      as are channel SIDE WALLS. Print standing; lay it on its side to test.
  OPT   step wedge 0.5 / 1.0 / 1.5 / 2.0 mm. Image a sharp edge through each
      under your backlight. 2.0 mm is the floor + ceiling path through a chip.

Nothing replicates the over-cured channel CEILING as a test surface -- it
cannot be exposed without cutting -- so judge it from the H sections.

Outputs (alongside this script):
  stl/<coupon>.stl          one per coupon: the print files (import all into
                            PreForm together; it lays them out)
  print_test_plate.step     assembly, for editing in Fusion / FreeCAD
  measurement_sheet.csv     every nominal dimension, with blanks to fill in
  preview.png               translucent render, channels opaque

The script also checks its own output and exits non-zero on failure: every
solid valid, NO sealed internal cavity (a sealed void in a resin print is
trapped liquid resin that never drains), and every bar channel sectioned
back to its nominal width and height.
"""
import csv
import sys
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
# Single source of truth for the chip layout: if the v2 drawing moves a port,
# the printed twin moves with it.
from gen_guide_diagrams import (BLANK_H, BLANK_W, HOLE_D, JUNCTION,  # noqa: E402
                                NOTCH, OIL_PORT, OUT_PORT, WATER_PORT, Y_MAIN)

# ---- process ----------------------------------------------------------------
LAYER = 0.1          # Alpha Clear primary layer height (mm)
PIXEL = 0.035        # Form Studio 1 XY pixel (mm)
FLOOR = 1.0          # under every channel
CEIL = 1.0           # over the tallest channel in a coupon
LABEL_H = 1.5        # text height
LABEL_D = 0.3        # deboss depth = 3 layers; leaves >= 0.7 mm over a channel
FONT = "Arial"

# ---- Luer: ISO 80369-7 / 594-1 female slip ---------------------------------
# Opening 4.270-4.315 mm, 6 % taper on diameter, >= 7.5 mm deep. A nominal
# male tip (3.925 mm) seats ~6.1 mm in, so 7.5 leaves it clear of the floor.
LUER_D_OPEN = 4.2925
LUER_TAPER = 0.06
LUER_DEPTH = 7.5
LUER_WALL = 1.6
LUER_BOSS_H = LUER_DEPTH + 1.0     # 1 mm socket floor before the port bore
LUER_OFFSETS = (-0.10, 0.0, 0.10)

# ---- bars -------------------------------------------------------------------
BAR_LEN, BAR_PITCH, BAR_MARGIN = 12.0, 3.0, 3.0
W_SPECS = [(w, w) for w in (0.4, 0.6, 0.8, 1.0, 1.2)]        # (width, height)
H_SPECS = [(0.8, h) for h in (0.8, 0.9, 1.0, 1.1, 1.2)]


# ---- helpers ----------------------------------------------------------------
def box(x0, y0, z0, dx, dy, dz):
    return cq.Solid.makeBox(dx, dy, dz, cq.Vector(x0, y0, z0))


def cyl(x, y, z0, d, h):
    return cq.Solid.makeCylinder(d / 2, h, cq.Vector(x, y, z0))


def deboss(body, text, x, y, z_top, size=LABEL_H, rot=0):
    t = (cq.Workplane("XY").workplane(offset=z_top)
         .transformed(offset=(x, y, 0), rotate=(0, 0, rot))
         .text(text, size, -LABEL_D, combine=False, font=FONT, kind="bold",
               halign="center", valign="center"))
    return body.cut(t.val())


def luer_socket(x, y, z_top, d_open):
    """Tapered female socket opening at z_top, plus the bore below it."""
    d_bot = d_open - LUER_TAPER * LUER_DEPTH
    # Overshoot the boss top by 0.05 mm on the same taper: a cone ending flush
    # with the face it cuts leaves OCC a coplanar boolean, which can close the
    # mouth with a zero-thickness skin -- and a skinned-over socket is a sealed
    # resin trap that the cavity check would (rightly) fail.
    over = 0.05
    return cq.Solid.makeCone(d_bot / 2, (d_open + LUER_TAPER * over) / 2,
                             LUER_DEPTH + over, cq.Vector(x, y, z_top - LUER_DEPTH))


# ---- coupons ----------------------------------------------------------------
# Each builder returns (body, voids). `voids` are the channel/port negatives,
# kept only so the preview can draw them opaque inside a translucent body.

def channel_bar(tag, specs):
    n = len(specs)
    hmax = max(h for _, h in specs)
    W = 2 * BAR_MARGIN + (n - 1) * BAR_PITCH
    T = FLOOR + hmax + CEIL
    body, voids = box(0, 0, 0, BAR_LEN, W, T), []
    for i, (w, h) in enumerate(specs):
        yc = BAR_MARGIN + i * BAR_PITCH
        # through-channel, overshooting both ends so the opening is clean
        v = box(-1, yc - w / 2, FLOOR, BAR_LEN + 2, w, h)
        body, voids = body.cut(v), voids + [v.intersect(box(0, 0, 0, BAR_LEN, W, T))]
        val = w if tag == "W" else h
        body = deboss(body, f"{val * 10:g}", 1.6, yc, T, size=1.3)
    # saw-line notches on both long faces at mid-length
    for y0 in (-0.2, W - 0.2):
        body = body.cut(box(BAR_LEN / 2 - 0.2, y0, 0, 0.4, 0.4, T))
    body = deboss(body, tag, BAR_LEN - 2.2, BAR_MARGIN / 2 - 0.3, T, size=1.4)
    return body, voids, T


def t_chip(w, ports):
    T = FLOOR + w + CEIL
    body = box(0, 0, 0, BLANK_W, BLANK_H, T)
    # orientation notch, top-left as on the milled blank
    notch = (cq.Workplane("XY").polyline([(0, BLANK_H - NOTCH), (0, BLANK_H),
                                          (NOTCH, BLANK_H)]).close().extrude(T))
    body = body.cut(notch.val())
    ch = [box(OIL_PORT[0], Y_MAIN - w / 2, FLOOR, OUT_PORT[0] - OIL_PORT[0], w, w),
          box(JUNCTION[0] - w / 2, Y_MAIN, FLOOR, w, WATER_PORT[1] - Y_MAIN, w)]
    voids = list(ch)
    for v in ch:
        body = body.cut(v)
    top = T
    if ports == "luer":
        boss_d = LUER_D_OPEN + 2 * LUER_WALL
        for (x, y) in (OIL_PORT, WATER_PORT, OUT_PORT):
            body = body.fuse(cyl(x, y, T, boss_d, LUER_BOSS_H))
        top = T + LUER_BOSS_H
        for (x, y) in (OIL_PORT, WATER_PORT, OUT_PORT):
            s = luer_socket(x, y, top, LUER_D_OPEN)
            body, voids = body.cut(s), voids + [s]
    for (x, y) in (OIL_PORT, WATER_PORT, OUT_PORT):
        b = cyl(x, y, FLOOR, HOLE_D, top - FLOOR + 0.01)
        body = body.cut(b)
        voids.append(cyl(x, y, FLOOR, HOLE_D, top - FLOOR - (LUER_DEPTH if ports == "luer" else 0)))
    body = deboss(body, "OIL", OIL_PORT[0], Y_MAIN - 6.0, T)
    body = deboss(body, "OUT", OUT_PORT[0], Y_MAIN - 6.0, T)
    body = deboss(body, "H2O", WATER_PORT[0] + 7.5, WATER_PORT[1], T)
    body = deboss(body, f"T{w * 1000:.0f} {'LUER' if ports == 'luer' else 'PAD'}",
                  BLANK_W - 12.0, 4.0, T)
    return body, voids, T


def luer_gauge():
    T = FLOOR + 0.8 + CEIL           # same base as T800, so the fit transfers
    pitch, L, Wd, y = 9.0, 29.0, 13.0, 6.5
    body, voids = box(0, 0, 0, L, Wd, T), []
    boss_d = LUER_D_OPEN + 2 * LUER_WALL
    xs = [L / 2 + (i - 1) * pitch for i in range(3)]
    for x in xs:
        body = body.fuse(cyl(x, y, T, boss_d, LUER_BOSS_H))
    top = T + LUER_BOSS_H
    for x, off in zip(xs, LUER_OFFSETS):
        s = luer_socket(x, y, top, LUER_D_OPEN + off)
        b = cyl(x, y, -0.01, HOLE_D, top)          # through, so resin drains
        body = body.cut(s).cut(b)
        voids += [s]
        body = deboss(body, f"{off * 100:+.0f}" if off else "0", x, 1.2, T, size=1.3)
    return body, voids, T


def theta_flat():
    return box(0, 0, 0, 9.0, 9.0, 2.0), [], 2.0


def theta_upright():
    return box(0, 0, 0, 9.0, 2.0, 9.0), [], 9.0


def optical_wedge():
    steps, L = (0.5, 1.0, 1.5, 2.0), 8.0
    body = box(0, 0, 0, L, 10.0, steps[0])
    for i, t in enumerate(steps[1:], 1):
        body = body.fuse(box(i * L, 0, 0, L, 10.0, t))
    return body.clean(), [], steps[-1]


# ---- plate ------------------------------------------------------------------
COUPONS = [
    # name,         builder,                         plate (x, y)
    ("T600_pad",    lambda: t_chip(0.6, "pad"),      (0.0, 0.0)),
    ("T800_luer",   lambda: t_chip(0.8, "luer"),     (0.0, 31.0)),
    ("W_width",     lambda: channel_bar("W", W_SPECS), (0.0, 62.0)),
    ("H_height",    lambda: channel_bar("H", H_SPECS), (17.0, 62.0)),
    ("LUER_gauge",  luer_gauge,                      (34.0, 62.0)),
    ("OPT_wedge",   optical_wedge,                   (68.0, 62.0)),
    ("THF_flat",    theta_flat,                      (68.0, 77.0)),
    ("THV_upright", theta_upright,                   (82.0, 77.0)),
]


def sealed_cavities(body):
    """Count voids NOT connected to the outside. Must be zero for resin."""
    bb = body.BoundingBox()
    shell = box(bb.xmin - 1, bb.ymin - 1, bb.zmin - 1,
                bb.xlen + 2, bb.ylen + 2, bb.zlen + 2)
    return len(shell.cut(body).Solids()) - 1


def section_bar(body, specs, T):
    """Recover each channel's width/height from a mid-length section."""
    # Exactly the bar's own y/z extent: any wider and the outside air comes back
    # as one more "channel". Taken from the design dimensions, NOT from
    # BoundingBox(): OCC pads bounding boxes by its tolerance, and a slab built
    # from one stood 5.8 um proud of the bar and returned an 18 mm x 5.8 um
    # skin of air as the first "channel" -- shifting every row by one.
    # x sits 1 mm past the saw notch and clear of the labels.
    W = 2 * BAR_MARGIN + (len(specs) - 1) * BAR_PITCH
    slab = box(BAR_LEN / 2 + 1.0, 0.0, 0.0, 0.05, W, T)
    air = slab.cut(body)
    found = sorted((s.BoundingBox() for s in air.Solids()), key=lambda b: b.ymin)
    out = []
    for (w, h), b in zip(specs, found):
        out.append((w, h, round(b.ylen, 4), round(b.zlen, 4), round(b.zmin, 4)))
    return out, len(found)


def main():
    (HERE / "stl").mkdir(exist_ok=True)
    assy, built, ok = cq.Assembly(name="print_test_plate"), {}, True
    for name, build, (px, py) in COUPONS:
        body, voids, T = build()
        valid = body.isValid()
        sealed = sealed_cavities(body)
        bb = body.BoundingBox()
        print(f"{name:12s} {bb.xlen:6.1f} x {bb.ylen:5.1f} x {bb.zlen:5.2f} mm  "
              f"vol {body.Volume() / 1000:5.2f} mL  valid={valid}  sealed_cavities={sealed}")
        ok &= valid and sealed == 0
        cq.exporters.export(body, str(HERE / "stl" / f"{name}.stl"),
                            tolerance=0.005, angularTolerance=0.1)
        placed = body.moved(cq.Location(cq.Vector(px, py, 0)))
        assy.add(placed, name=name)
        built[name] = (placed, [v.moved(cq.Location(cq.Vector(px, py, 0))) for v in voids])

        if name in ("W_width", "H_height"):
            specs = W_SPECS if name == "W_width" else H_SPECS
            rows, n = section_bar(body, specs, T)
            ok &= n == len(specs)
            for w, h, mw, mh, z0 in rows:
                good = abs(mw - w) < 1e-3 and abs(mh - h) < 1e-3 and abs(z0 - FLOOR) < 1e-3
                ok &= good
                print(f"    section: nominal {w*1000:4.0f} x {h*1000:4.0f} um -> CAD "
                      f"{mw*1000:6.1f} x {mh*1000:6.1f} um, floor z={z0:.2f}  "
                      f"{'ok' if good else 'MISMATCH'}")

    assy.export(str(HERE / "print_test_plate.step"))
    write_sheet()
    render_preview(built)
    print("\nALL CHECKS PASSED" if ok else "\nCHECKS FAILED")
    sys.exit(0 if ok else 1)


def write_sheet():
    rows = [["coupon", "feature", "nominal_w_um", "nominal_h_um", "nominal_w_px",
             "nominal_h_layers", "measured_w_um", "measured_h_um", "notes"]]
    for tag, specs in (("W", W_SPECS), ("H", H_SPECS)):
        for w, h in specs:
            rows.append([tag, f"{w*1000:.0f}x{h*1000:.0f}", f"{w*1000:.0f}", f"{h*1000:.0f}",
                         f"{w / PIXEL:.1f}", f"{h / LAYER:.0f}", "", "", ""])
    for off in LUER_OFFSETS:
        rows.append(["LUER", f"socket {off:+.2f} mm", f"{(LUER_D_OPEN + off)*1000:.0f}",
                     "", "", "", "", "", "seats? leaks under syringe push?"])
    rows.append(["THF", "theta, flat (layer face, ~channel floor)", "", "", "", "", "", "",
                 "theta_deg through water, under doped oil"])
    rows.append(["THV", "theta, upright (layer edges, ~side wall)", "", "", "", "", "", "",
                 "theta_deg through water, under doped oil"])
    for t in (0.5, 1.0, 1.5, 2.0):
        rows.append(["OPT", f"window {t:.1f} mm", "", f"{t*1000:.0f}", "", f"{t / LAYER:.0f}",
                     "", "", "edge sharp under strobe? (px blur)"])
    for chip in ("T600_pad", "T800_luer"):
        rows.append([chip, "drains with IPA flush?", "", "", "", "", "", "", ""])
        rows.append([chip, "leak-free at operating head?", "", "", "", "", "", "", ""])
    with open(HERE / "measurement_sheet.csv", "w", newline="") as f:
        csv.writer(f).writerows(rows)


def render_preview(built):
    import vtk
    ren = vtk.vtkRenderer()
    ren.SetBackground(1, 1, 1)
    bodies, voids = vtk.vtkAppendPolyData(), vtk.vtkAppendPolyData()
    for placed, vs in built.values():
        bodies.AddInputData(placed.toVtkPolyData(0.02, 0.2))
        for v in vs:
            voids.AddInputData(v.toVtkPolyData(0.02, 0.2))
    for src, rgb, alpha in ((voids, (0.13, 0.42, 0.78), 1.0), (bodies, (0.62, 0.70, 0.76), 0.28)):
        src.Update()
        m = vtk.vtkPolyDataMapper()
        m.SetInputData(src.GetOutput())
        a = vtk.vtkActor()
        a.SetMapper(m)
        a.GetProperty().SetColor(*rgb)
        a.GetProperty().SetOpacity(alpha)
        ren.AddActor(a)
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.AddRenderer(ren)
    win.SetSize(1800, 1150)
    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(48, 45, 0)
    cam.SetPosition(48 - 70, 45 - 150, 150)
    cam.SetViewUp(0, 0, 1)
    ren.ResetCamera()
    cam.Zoom(1.12)
    win.Render()
    grab = vtk.vtkWindowToImageFilter()
    grab.SetInput(win)
    grab.Update()
    w = vtk.vtkPNGWriter()
    w.SetFileName(str(HERE / "preview.png"))
    w.SetInputConnection(grab.GetOutputPort())
    w.Write()


if __name__ == "__main__":
    main()
