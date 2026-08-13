#!/usr/bin/env python3
"""Analyse a sigma/theta sweep from sweep_fluid_props.py: regime map + calibration.

`analyze_window_sweep.py` classifies a PRESSURE sweep into drips/marginal/
no-drip. That vocabulary is too coarse here, because this sweep is built to
produce failures and the failure MODES are opposites with opposite fixes:

  no-entry   Water never crosses into the main channel. The drive is below the
             capillary entry threshold 2*sigma/w. Fix: raise the water column.
  thread     Water enters and never pinches off -- a continuous stream or a
             wall film. Either the walls are too water-wet (low theta0) or Ca
             is too high (low sigma at unchanged drive). Fix: the opposite of
             the above. Raising the water column makes it WORSE.

A drips/no-drip classifier collapses these two into one cell and would send a
builder in exactly the wrong direction half the time. They are told apart on
the final frame: an unbroken thread produces a single detection spanning most
of the outlet channel, while no-entry leaves the outlet essentially dry.

Cases that do form droplets are further split by L/w, because that is the
squeezing/dripping boundary and it changes what the chip is FOR: plugs
(L/w >= 1) span the channel and are what every observable in this repo is
calibrated on; drops (L/w < 1) are smaller than the channel, travel faster,
and break the Garstecki scaling the design math uses.

Usage:
    python3 analyze_fluid_sweep.py ~/sweeps/wetting/A_theta --mode theta \\
        --out-dir ../results/wetting_2026-08
    python3 analyze_fluid_sweep.py ~/sweeps/wetting/B_sigma_fixedP --mode sigma-fixed \\
        --out-dir ../results/wetting_2026-08
    python3 analyze_fluid_sweep.py ~/sweeps/wetting/C_sigma_scaledP --mode sigma-scaled \\
        --out-dir ../results/wetting_2026-08
"""
import argparse
import contextlib
import io
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from extract_droplets import DropletExtractor  # noqa: E402
from extract_mature_droplets import link_tracks, mature_length  # noqa: E402

PA_PER_CM_H2O = 1000.0 * 9.81 / 100.0
L_OUTLET_UM = 4000.0          # gen_blockmesh.py L_OUTLET -- a LENGTH, unscaled
MU_OIL = 0.048                # Pa.s, from constant/transportProperties

REGIMES = ["no-entry", "thread", "marginal", "drops", "plugs"]
REGIME_COLOURS = ["#b2182b", "#e08214", "#f0c419", "#7fbc41", "#2166ac"]


def _finished(case_dir: Path) -> bool:
    """Did interFoam reach `End`? Accepts a gzipped log.

    A completed solver log is ~180 MB per case (~1 GB for a long
    scale-with-sigma run), so they get compressed once a study is done. If
    this only looked for the uncompressed name, every archived case would
    silently read as 'not finished' and drop out of the analysis.
    """
    log, logz = case_dir / "log.interFoam", case_dir / "log.interFoam.gz"
    if log.exists():
        return "End" in log.read_text(errors="replace")[-2000:]
    if logz.exists():
        import gzip
        with gzip.open(logz, "rt", errors="replace") as fh:
            return "End" in fh.read()[-2000:]
    return False


def measure(case_dir: Path, w_um: float, max_advance_um: float):
    """Full per-case measurement: tracks, plateau lengths, speeds, outlet state."""
    ex = DropletExtractor(case_dir, w_main_m=w_um * 1e-6,
                          x_junction_m=(2000.0 + w_um) * 1e-6)
    # The extractor narrates every frame; that is 120 lines per case here.
    with contextlib.redirect_stdout(io.StringIO()):
        df, _ = ex.process_case()

    out = {"n_tracks": 0, "n_complete": 0, "outlet_frac": 0.0, "max_detection_um": 0.0}
    if df.empty:
        return out, pd.DataFrame()

    # Outlet occupancy on the LAST frame, used only to tell no-entry from an
    # unbroken thread. Both give zero complete tracks; nothing in the track
    # data distinguishes them.
    out["max_detection_um"] = float(df.length.max())
    last = df[df.time == df.time.max()]
    out["outlet_frac"] = float(last.length.sum() / L_OUTLET_UM) if len(last) else 0.0

    df = df[df.centroid_y < w_um]
    tracks = [t for t in link_tracks(df, max_advance_um) if len(t) >= 3]
    out["n_tracks"] = len(tracks)

    rows = []
    for tr in tracks:
        L, W, complete = mature_length(tr, growth_threshold_um=0.05 * w_um,
                                       min_length_um=0.2 * w_um)
        if not complete:
            continue
        t = np.array([p[0] for p in tr])
        x = np.array([p[1] for p in tr])
        Ls = np.array([p[2] for p in tr])
        # Mature frames only: flat length AND translating. A track's tail is
        # the slug leaving the domain, its length collapsing as it exits.
        idx = np.where((np.abs(np.diff(Ls)) < 0.05 * w_um) & (np.diff(x) > 0))[0] + 1
        speed = (np.median(np.diff(x[idx]) / np.diff(t[idx])) * 1e-3
                 if len(idx) >= 2 else np.nan)
        rows.append({"first_t": tr[0][0], "L_um": L, "w_um": W, "speed_mm_s": speed})

    res = pd.DataFrame(rows)
    out["n_complete"] = len(res)
    if len(res):
        out["L_um"] = float(res.L_um.median())
        out["L_over_w"] = out["L_um"] / w_um
        out["speed_mm_s"] = float(np.nanmedian(res.speed_mm_s))
        starts = sorted(res.first_t)
        if len(starts) >= 2:
            gap = float(np.median(np.diff(starts)))
            out["period_ms"] = gap * 1000.0
            out["f_Hz"] = 1.0 / gap if gap else np.nan
    return out, res


def classify(m, spread_tol, res):
    n = m.get("n_complete", 0)
    if n == 0:
        # A thread spans the outlet; no-entry leaves it dry. The threshold is
        # deliberately high (0.8 of the outlet) so a single large-but-finite
        # slug caught mid-exit is not mistaken for a continuous stream.
        if m.get("max_detection_um", 0.0) > 0.8 * L_OUTLET_UM:
            return "thread"
        if m.get("outlet_frac", 0.0) < 0.01:
            return "no-entry"
        return "marginal"
    if n < 2 or "f_Hz" not in m:
        return "marginal"
    L = np.asarray(res.L_um, dtype=float)
    if L.size >= 2 and (L.max() - L.min()) / np.median(L) > spread_tol:
        return "marginal"
    return "plugs" if m["L_over_w"] >= 1.0 else "drops"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sweep_dir", type=Path)
    ap.add_argument("--mode", required=True,
                    choices=("theta", "sigma-fixed", "sigma-scaled"))
    ap.add_argument("--speed-ceiling-mm-s", type=float, default=60.0)
    ap.add_argument("--spread-tol", type=float, default=0.15)
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()

    cases = json.loads((args.sweep_dir / "cases.json").read_text())
    rows = []
    for c in cases:
        d = args.sweep_dir / c["name"]
        if not _finished(d):
            print(f"  {c['name']}: not finished, skipped", flush=True)
            continue
        w = c["w_main_um"]
        # A slug advances speed*writeInterval between frames. writeInterval
        # varies across a scale-with-sigma study, so this must be per case.
        max_adv = args.speed_ceiling_mm_s * 1e3 * c["write_interval"]
        m, res = measure(d, w, max_adv)
        verdict = classify(m, args.spread_tol, res)
        speed = m.get("speed_mm_s", np.nan)
        rows.append({
            "name": c["name"], "sigma_N_m": c["sigma"], "theta0_deg": c["theta0"],
            "P_cont_Pa": c["P_cont"], "P_disp_Pa": c["P_disp"],
            "P_cont_cmH2O": round(c["P_cont"] / PA_PER_CM_H2O, 2),
            "P_disp_cmH2O": round(c["P_disp"] / PA_PER_CM_H2O, 2),
            "end_time_s": c["end_time"],
            "regime": verdict,
            "n_droplets": m.get("n_complete", 0),
            "L_um": m.get("L_um", np.nan), "L_over_w": m.get("L_over_w", np.nan),
            "speed_mm_s": speed, "f_Hz": m.get("f_Hz", np.nan),
            "period_ms": m.get("period_ms", np.nan),
            # Ca on the MEASURED slug speed, not the design velocity -- that is
            # the number that says which regime the chip is actually in.
            "Ca_measured": (MU_OIL * speed * 1e-3 / c["sigma"]
                            if speed == speed else np.nan),
            "entry_pressure_Pa": round(2 * c["sigma"] / (w * 1e-6), 1),
            "max_detection_um": round(m.get("max_detection_um", 0.0), 1),
        })
        print(f"  {c['name']}: {verdict:9s} n={rows[-1]['n_droplets']} "
              f"L/w={rows[-1]['L_over_w']:.3f} f={rows[-1]['f_Hz']:.2f} Hz"
              if rows[-1]["n_droplets"] else f"  {c['name']}: {verdict}", flush=True)

    if not rows:
        print("no finished cases")
        return
    df = pd.DataFrame(rows)
    out_dir = args.out_dir or args.sweep_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = {"theta": "A_theta", "sigma-fixed": "B_sigma_fixedP",
           "sigma-scaled": "C_sigma_scaledP"}[args.mode]
    df.to_csv(out_dir / f"{tag}_results.csv", index=False)

    counts = df.regime.value_counts().to_dict()
    print("\n" + ", ".join(f"{counts.get(k, 0)} {k}" for k in REGIMES if counts.get(k)))
    if args.mode == "theta":
        ok = df[df.regime.isin(("plugs", "drops"))]
        if len(ok) and len(ok) < len(df):
            print(f"Dripping boundary is bracketed: fails at "
                  f"{sorted(set(df[~df.regime.isin(('plugs','drops'))].theta0_deg))} deg, "
                  f"works at {sorted(set(ok.theta0_deg))} deg.")
        elif len(ok) == len(df):
            print("Every theta in this sweep drips -- the boundary is BELOW "
                  f"{df.theta0_deg.min():.0f} deg and remains unmeasured.")

    _figure(df, args.mode, out_dir / f"{tag}.png")
    print(f"wrote {out_dir}/{tag}_results.csv and {tag}.png")


def _regime_band(ax, xvals, regimes):
    """Shade the x-axis by regime so failures read as regions, not gaps.

    Takes the PLOTTED x values rather than a column name: the sigma panels
    plot mN/m while the dataframe stores N/m, so keying off the column would
    put every band at x ~ 0.005 under data drawn at x = 5 -- invisible, and
    silently so.
    """
    for x, regime in zip(np.asarray(xvals, dtype=float), regimes):
        ax.axvspan(x * 0.97, x * 1.03, alpha=0.18, lw=0,
                   color=REGIME_COLOURS[REGIMES.index(regime)])


def _figure(df, mode, path):
    if mode == "theta":
        df = df.sort_values("theta0_deg")
        fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
        x = df.theta0_deg
        for ax, (col, label) in zip(axes, [("L_over_w", "Slug length L/w"),
                                           ("f_Hz", "Droplet rate (Hz)"),
                                           ("speed_mm_s", "Advection speed (mm/s)")]):
            _regime_band(ax, x, df.regime)
            ax.plot(x, df[col], "o-", color="#1f77b4", ms=7)
            ax.set_xlabel("wall contact angle θ₀ (deg, through water)")
            ax.set_title(label)
            ax.grid(alpha=0.25)
        handles = [plt.Line2D([], [], marker="s", ls="", ms=10, alpha=0.5,
                              color=REGIME_COLOURS[i], label=r)
                   for i, r in enumerate(REGIMES) if (df.regime == r).any()]
        axes[0].legend(handles=handles, fontsize=8, loc="best")
        fig.suptitle("Study A — contact-angle sensitivity at σ = 30 mN/m, "
                     "drive fixed at 980/490 Pa\n"
                     "θ₀ = 160° was chosen because it dripped; this is where "
                     "the boundary actually lies", fontsize=12)
    else:
        df = df.sort_values("sigma_N_m")
        s = df.sigma_N_m * 1000
        scaled = mode == "sigma-scaled"
        # Under P ~ sigma the flow is geometrically similar: L/w flat, and
        # both speed and rate proportional to sigma. Under fixed P nothing is
        # predicted -- that panel is the calibration curve, not a test.
        preds = ([("L_over_w", "Slug length L/w", "flat"),
                  ("speed_mm_s", "Advection speed (mm/s)", "∝ σ"),
                  ("f_Hz", "Droplet rate (Hz)", "∝ σ"),
                  ("Ca_measured", "Capillary number Ca", "flat")] if scaled else
                 [("L_over_w", "Slug length L/w", None),
                  ("speed_mm_s", "Advection speed (mm/s)", None),
                  ("f_Hz", "Droplet rate (Hz)", None),
                  ("Ca_measured", "Capillary number Ca", "∝ 1/σ")])
        fig, axes = plt.subplots(1, 4, figsize=(18, 4.2))
        ref = df[np.isclose(df.sigma_N_m, 0.03)]
        for ax, (col, label, pred) in zip(axes, preds):
            _regime_band(ax, s, df.regime)
            good = np.isfinite(df[col])
            if pred and len(ref) and np.isfinite(ref[col]).all():
                s0, v0 = 30.0, float(ref[col].iloc[0])
                sf = np.linspace(s.min() * 0.9, s.max() * 1.1, 50)
                curve = {"flat": np.full_like(sf, v0), "∝ σ": v0 * sf / s0,
                         "∝ 1/σ": v0 * s0 / sf}[pred]
                ax.fill_between(sf, curve * 0.9, curve * 1.1, color="0.85", zorder=0,
                                label="±10% of prediction")
                ax.plot(sf, curve, "--", color="0.55", lw=1.4, label=pred)
            ax.plot(s[good], df[col][good], "o-", color="#1f77b4", ms=7, label="simulated")
            ax.set_xlabel("interfacial tension σ (mN/m)")
            ax.set_title(label)
            ax.grid(alpha=0.25)
            ax.legend(fontsize=7, loc="best", framealpha=0.85, edgecolor="none")
        handles = [plt.Line2D([], [], marker="s", ls="", ms=10, alpha=0.5,
                              color=REGIME_COLOURS[i], label=r)
                   for i, r in enumerate(REGIMES) if (df.regime == r).any()]
        axes[-1].legend(handles=handles, fontsize=8, loc="best")
        fig.suptitle(
            ("Study C — σ with the drive retuned as P ∝ σ. If these collapse onto "
             "the dashed lines, the chamber is σ-robust and the correction is one line."
             if scaled else
             "Study B — σ with the drive left at the designed 980/490 Pa. "
             "This is the calibration curve: what you see on the bench, and what σ it implies."),
            fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.88])
    fig.savefig(path, dpi=140)


if __name__ == "__main__":
    main()
