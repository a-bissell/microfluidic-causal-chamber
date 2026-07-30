#!/usr/bin/env python3
"""Compare the millable-chip twin across channel widths (400 / 600 / 800 um).

The replicability argument for scaling the chip up is that the droplet
REGIME is set by the capillary number Ca = mu*U/sigma, which contains no
length. Hold Ca fixed -- which means holding the mean velocity U fixed, not
the flow rate -- and the physics should be geometrically similar at any
width: L/w constant, U constant, Q ~ w^2, f ~ 1/w. Drive pressures fall as
1/w^2 (R ~ 1/w^4 for a square duct, Q ~ w^2), so a wider chip is also an
EASIER chip to actuate.

That is the prediction. This script plots the measurement.

Panel A is a filmstrip: each scale's alpha.water field over one droplet
period, drawn on a common PHYSICAL scale (a 600 um chip is literally 1.5x
the size of the 400 um one on the page). If the similarity argument holds,
the three rows differ only by that magnification.

Panel B plots the four observables against w with their predicted scalings
overlaid, so a departure from similarity shows up as a point off the line
rather than as a number in a table.

Usage:
    python3 plot_scale_comparison.py \
        400:/path/to/mill_run 600:/path/to/mill2d_600um 800:/path/to/mill2d_800um \
        --out scale_comparison.png
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from scipy.interpolate import griddata

sys.path.insert(0, str(Path(__file__).parent))
from extract_droplets import DropletExtractor  # noqa: E402
from extract_mature_droplets import link_tracks  # noqa: E402

# Every mill case puts the junction's LEFT edge at x = L_APPROACH = 2000 um
# (gen_blockmesh.py keeps channel lengths fixed while widths scale), so the
# junction spans 2000 .. 2000 + w. The extractor's x_junction is the
# downstream edge -- the line past which a detection is a free slug rather
# than the tongue still being fed -- so it must scale with w, not sit at a
# fixed 2400 um borrowed from the 400 um design.
X_APPROACH_UM = 2000.0


def x_junction_um(w_um):
    return X_APPROACH_UM + w_um


# One FIXED physical window for every row. If each row auto-fit its own
# geometry the rows would be drawn at different magnifications, which is
# exactly the thing the figure is claiming not to do. Same micrometre
# extents + aspect="equal" == genuinely common scale, so the 800 um channel
# really is drawn twice as thick as the 400 um one.
WINDOW = (1400.0, 7000.0, -350.0, 1150.0)   # x0, x1, y0, y1 in um


def load_frame(vtk_file, extractor, nx=560, ny=150):
    """Resample one frame's alpha field onto the common window for imshow.

    The mesh is graded (fine at the junction, coarse in the feed), so a
    scatter plot of cell centres would misrepresent area. griddata onto a
    uniform grid gives an honest picture at the cost of a little smoothing.
    Cells outside the fluid domain come back NaN and draw as blank page.
    """
    coords, alpha = extractor.read_vtk(vtk_file)
    xy = coords[:, :2] * 1e6                       # -> um
    x0, x1, y0, y1 = WINDOW
    gx, gy = np.meshgrid(np.linspace(x0, x1, nx), np.linspace(y0, y1, ny))
    grid = griddata(xy, alpha, (gx, gy), method="linear")
    return grid, WINDOW


def measure(case_dir, w_um, max_advance_um, growth_um):
    """Return (metrics dict, list of complete tracks) for one case."""
    ex = DropletExtractor(case_dir, w_main_m=w_um * 1e-6,
                          x_junction_m=x_junction_um(w_um) * 1e-6)
    df, _ = ex.process_case()
    df = df[df.centroid_y < w_um]
    tracks = [t for t in link_tracks(df, max_advance_um) if len(t) >= 3]

    lengths, speeds, starts = [], [], []
    for tr in tracks:
        t = np.array([p[0] for p in tr])
        x = np.array([p[1] for p in tr])
        L = np.array([p[2] for p in tr])
        # A mature frame: length flat AND the slug translating. The tail of
        # every track is the slug leaving the domain (length collapsing as
        # it exits), which must not be averaged in.
        dl = np.abs(np.diff(L))
        dx = np.diff(x)
        mature = np.where((dl < growth_um) & (dx > 0))[0] + 1
        if len(mature) < 2:
            continue
        lengths.append(np.median(L[mature]))
        speeds.append(np.median(np.diff(x[mature]) / np.diff(t[mature])) * 1e-3)
        starts.append(t[0])

    gaps = np.diff(sorted(starts))
    return {
        "w_um": w_um,
        "n_droplets": len(lengths),
        "L_um": float(np.median(lengths)) if lengths else np.nan,
        "L_over_w": float(np.median(lengths)) / w_um if lengths else np.nan,
        "speed_mm_s": float(np.median(speeds)) if speeds else np.nan,
        "period_s": float(np.median(gaps)) if len(gaps) else np.nan,
        "f_Hz": 1.0 / float(np.median(gaps)) if len(gaps) else np.nan,
    }, tracks, ex


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="+", metavar="W:DIR",
                    help="channel width (um) and case dir, e.g. 600:/data/mill600")
    ap.add_argument("--out", default="scale_comparison.png")
    ap.add_argument("--n-frames", type=int, default=4,
                    help="filmstrip columns (frames spanning one period)")
    args = ap.parse_args()

    parsed = []
    for spec in args.cases:
        w_s, d = spec.split(":", 1)
        parsed.append((float(w_s), Path(d)))
    parsed.sort()

    rows = []
    for w_um, case in parsed:
        m, tracks, ex = measure(case, w_um, max_advance_um=1.5 * w_um,
                                growth_um=0.05 * w_um)
        rows.append((w_um, case, m, tracks, ex))
        print(f"{w_um:.0f} um: {m}")

    n_cols = args.n_frames
    # WINDOW is 5600 x 1500 um; at aspect="equal" each tile is ~3.7:1, so
    # size the rows to that rather than leaving vertical slack.
    x0, x1, y0, y1 = WINDOW
    tile_w = 3.0
    tile_h = tile_w * (y1 - y0) / (x1 - x0)
    fig = plt.figure(figsize=(tile_w * n_cols, tile_h * len(rows) + 4.6))
    gs = fig.add_gridspec(len(rows) + 1, n_cols,
                          height_ratios=[tile_h] * len(rows) + [4.0],
                          hspace=0.5, wspace=0.06)

    for r, (w_um, case, m, tracks, ex) in enumerate(rows):
        files = ex.find_vtk_files()
        times = ex.resolve_times(files)
        # Centre the strip on the last complete droplet's formation, then
        # step through one period.
        period = m["period_s"] if np.isfinite(m["period_s"]) else (times[-1] - times[0]) / 3
        t_end = times[-1]
        t_start = max(times[0], t_end - period)
        picks = np.linspace(t_start, t_end, n_cols)
        for c, tp in enumerate(picks):
            i = int(np.argmin(np.abs(np.array(times) - tp)))
            grid, extent = load_frame(files[i], ex)
            ax = fig.add_subplot(gs[r, c])
            ax.imshow(grid, origin="lower", extent=extent, aspect="equal",
                      cmap="Blues", vmin=0, vmax=1, interpolation="bilinear")
            ax.set_xlim(extent[0], extent[1])
            ax.set_ylim(extent[2], extent[3])
            ax.set_xticks([])
            ax.set_yticks([])
            for s in ax.spines.values():
                s.set_visible(False)
            ax.set_title(f"t = {times[i]*1e3:.0f} ms", fontsize=8, pad=2)
            if c == 0:
                ax.set_ylabel(f"{w_um:.0f} µm", fontsize=11, fontweight="bold")
            # 1 mm bar in the margin BELOW the channel, identical length on
            # the page in every row -- that is the whole point of WINDOW.
            if c == n_cols - 1:
                bx = extent[1] - 1250
                ax.add_patch(Rectangle((bx, -300), 1000, 55,
                                       color="0.25", zorder=5))
                ax.text(bx + 500, -230, "1 mm", ha="center", fontsize=7,
                        color="0.25")

    w = np.array([r[0] for r in rows])
    # Each prediction is anchored on the SMALLEST measured width -- the
    # 400 um design, which is the one that was verified first -- so the
    # dashed line passes exactly through that point and the wider chips are
    # genuine out-of-sample predictions. (Anchoring on the plotting grid's
    # first element instead silently offsets every curve.)
    obs = [
        ("L / w", np.array([r[2]["L_over_w"] for r in rows]), "flat (Ca-similar)",
         lambda ww, ref, w0: np.full_like(ww, ref, dtype=float)),
        ("Slug length (µm)", np.array([r[2]["L_um"] for r in rows]), "∝ w",
         lambda ww, ref, w0: ref * ww / w0),
        ("Advection speed (mm/s)", np.array([r[2]["speed_mm_s"] for r in rows]),
         "flat (U fixed by Ca)", lambda ww, ref, w0: np.full_like(ww, ref, dtype=float)),
        ("Droplet rate (Hz)", np.array([r[2]["f_Hz"] for r in rows]), "∝ 1/w",
         lambda ww, ref, w0: ref * w0 / ww),
    ]
    for k, (label, vals, pred_label, pred) in enumerate(obs):
        ax = fig.add_subplot(gs[len(rows), k])
        good = np.isfinite(vals)
        ref, w_ref = vals[good][0], w[good][0]
        wf = np.linspace(w.min() * 0.92, w.max() * 1.08, 50)
        curve = pred(wf, ref, w_ref)
        ax.fill_between(wf, curve * 0.9, curve * 1.1, color="0.85", zorder=0,
                        label="±10% of prediction")
        ax.plot(wf, curve, "--", color="0.55", lw=1.4, label=pred_label)
        ax.plot(w[good], vals[good], "o-", color="#1f77b4", ms=7, lw=1.6,
                label="simulated")
        # Default autoscaling turns a 3% deviation from a flat prediction
        # into a full-height climb. Pin the view to the ±10% band so the
        # eye reads agreement as agreement.
        lo = min(curve.min() * 0.88, np.nanmin(vals[good]))
        hi = max(curve.max() * 1.12, np.nanmax(vals[good]))
        ax.set_ylim(lo, hi)
        ax.set_xlabel("channel width w (µm)", fontsize=9)
        ax.set_title(label, fontsize=10)
        ax.set_xticks(w)
        ax.legend(fontsize=7, loc="best", framealpha=0.85, edgecolor="none")
        ax.grid(alpha=0.25)
        ax.tick_params(labelsize=8)

    fig.suptitle("Millable-chip twin: geometric similarity across channel width\n"
                 "same Ca, same L/w, same speed — only the clock and the scale change",
                 fontsize=13, y=0.995)
    fig.savefig(args.out, dpi=140, bbox_inches="tight")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
