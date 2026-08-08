#!/usr/bin/env python3
"""Encoder fidelity statistics from extract_droplet_dye.py output.

THE FOUR QUESTIONS THIS ANSWERS
-------------------------------
1. IS THE CODE WRITTEN FAITHFULLY?
   Mean realized composition against the commanded one. A systematic gap is a
   calibration matrix the bench could invert; what matters is whether it is
   stable, so the between-droplet spread is reported alongside it.

2. IS THE MEASUREMENT TRUSTWORTHY? (the symmetry control)
   The cross-merge puts dye1 and dye3 in mirror-image legs: same length, same
   resistance, same wall proximity. So c1 == c3 is guaranteed by geometry,
   independent of any physics. A measured c1 != c3 is therefore a pure
   artifact -- mesh asymmetry, decomposition, or a bug -- and it invalidates
   the run before any physical claim is made. This check runs FIRST.

3. IS THERE A REAL SAMPLING BIAS? (the 3D signature)
   dye2 enters axially and rides the channel core; dye1 and dye3 hug the side
   walls. If the continuous phase intrudes at the corners of the water leg,
   the slug preferentially samples the core, and the signature is

       c2 > (c1 + c3) / 2      with c1 == c3

   That combination cannot be produced by leg asymmetry, which is what makes
   it diagnostic. In 2D it must be absent: a 2D mesh has no corners. The
   whole point of the matched 2D/3D pair is that this number is the
   difference between them.

4. HOW MANY BITS IS THE CHANNEL WORTH?
   The between-droplet spread in composition is the encoder's per-symbol
   noise, and it sets how many codes are distinguishable. Reported as an
   order-of-magnitude estimate with its assumptions stated inline -- it is a
   scaling argument, not a measured capacity.

TWO NOISE SOURCES, SEPARATED
----------------------------
A droplet is seen in many consecutive frames as it advects down the outlet.
That is repeated measurement of one physical symbol, so:

    spread WITHIN a droplet's frames  -> measurement/numerical noise
    spread BETWEEN droplets           -> real per-symbol code noise

Only the second limits the channel. Conflating them (by pooling all rows)
would inflate the noise estimate and understate the encoder, so this script
tracks droplets across frames rather than pooling.

Usage:
    python3 analyze_encoder.py <case_dir> [--compare-with <other_case_dir>]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def load(case):
    csv = case / "droplet_dye.csv"
    if not csv.exists():
        sys.exit(f"{csv} not found. Run extract_droplet_dye.py first.")
    geom = json.loads((case / "geometry.json").read_text())
    return pd.read_csv(csv), geom


def track(df, geom):
    """Assign a persistent id to each physical droplet across frames.

    Greedy nearest-centroid matching in x. Slug flow in a straight outlet is
    strictly ordered and one-directional, so a droplet's centroid only ever
    increases in x and never overtakes another -- which makes this simple
    matching safe here in a way it would not be in general.

    Candidates are drawn ONLY from the immediately preceding frame. Carrying
    every id ever seen produces a specific and silent failure: a droplet that
    has already left the window keeps its last centroid as a live candidate,
    and when a later droplet advects to that same x it matches with distance
    zero -- beating the correct predecessor. Successive droplets then collapse
    into one id. On synthetic data with a known answer that turned 12 droplets
    into 4, and it does not look like an error: it produces a plausible,
    smaller droplet count with plausible compositions and a badly understated
    between-droplet spread, which is exactly the quantity the channel estimate
    depends on.

    A droplet missing for a single frame therefore starts a new id rather than
    resuming its old one. That over-counts slightly, which is the safe
    direction: it inflates the apparent per-symbol spread rather than hiding
    it, and singletons are dropped downstream.
    """
    df = df.sort_values(["time_s", "x_centroid_um"]).copy()
    df["droplet_id"] = -1
    next_id, prev = 0, {}          # droplet_id -> x_centroid in the PREVIOUS frame

    for _, frame in df.groupby("time_s", sort=True):
        used, current = set(), {}
        for idx, row in frame.iterrows():
            x = row.x_centroid_um
            best, best_d = None, np.inf
            for did, xprev in prev.items():
                if did in used:
                    continue
                d = x - xprev
                # Must have moved downstream, but less than its own length:
                # a bigger jump means this is a different droplet.
                if -0.25 * row.L_um <= d < row.L_um and abs(d) < best_d:
                    best, best_d = did, abs(d)
            if best is None:
                best = next_id
                next_id += 1
            used.add(best)
            df.loc[idx, "droplet_id"] = best
            current[best] = x
        prev = current             # expire anything not seen this frame
    return df


def settle_cut(df, geom):
    """Time before which a droplet cannot carry an encoder-written composition.

    Three things must finish before a droplet's composition is the one the
    inlets commanded, and `t_transit_s` covers only the first:

      1. the LEG flushes         l_leg / u_leg      <- this is t_transit_s
      2. the MERGE NODE flushes  w_main / u_leg     <- omitted
      3. a droplet then forms    one droplet period <- omitted

    setFieldsDict seeds uniform (1/3, 1/3, 1/3) water across the whole column
    above the junction -- the leg AND the square merge node above it -- so a
    cut at the leg transit alone passes droplets that are still part seeded
    water. In the 0.8 s 2D reference run it let two through: their
    core-vs-wall signature was -0.087 and -0.039 while the one clean droplet
    gave +0.002, and averaging the three produced a false ASYMMETRIC verdict.

    The period is measured from the run rather than assumed. Formation is very
    regular here (170.0 ms between each of four droplets in the reference run)
    and it is a hydrodynamic quantity, so the startup transient does not
    corrupt it even though the compositions are still settling.
    """
    t_flush = (geom["l_leg_um"] + geom["w_main_um"]) * 1e-6 / geom["u_leg_m_s"]

    first = df.groupby("droplet_id").time_s.min().sort_values()
    if len(first) >= 2:
        period = float(np.median(np.diff(first.to_numpy())))
        period_src = f"measured, {period*1e3:.0f} ms"
    else:
        period = 0.0
        period_src = "UNKNOWN -- fewer than 2 droplets, cut may be too early"
    return t_flush + period, t_flush, period, period_src


def _fit_to_station(d, x_ref_um):
    """Composition regressed onto x and evaluated at the pinch-off station.

    A droplet's composition is fixed the moment it detaches and cannot
    physically change afterwards: the three dyes are the same fluid, advected
    with D = 0, so nothing redistributes them between laminae.

    The MEASURED composition does change as the droplet travels, because the
    passive scalars get no MULES compression and bleed across the interface,
    and the bleed is differential between laminae at different distances from
    it. In the reference run the alpha volume was conserved to 0.2% over a
    2 mm window while the summed dye fell by up to 14%, and c1 - c3 drifted by
    -0.009 to -0.016 per mm of travel. Most of that run's alarming
    c1 - c3 = -0.066 was accumulated AFTER pinch-off; at the junction it was
    -0.004.

    So a mean over a droplet's frames answers "what was the composition
    wherever this droplet happened to be sampled", which is not the question.
    Regress on x and read the fit at the junction instead. The residual about
    that fit is the real within-droplet measurement noise -- the previous
    std() over frames was dominated by the drift and overstated it.

    Returns (composition, drift_per_mm, residual_sd, extrapolation_um).
    """
    x = d.x_centroid_um.to_numpy()
    c, drift, resid = {}, {}, {}
    if len(d) >= 3 and np.ptp(x) > 0:
        for k in (1, 2, 3):
            y = d[f"c{k}"].to_numpy()
            slope, intercept = np.polyfit(x, y, 1)
            c[k] = float(slope * x_ref_um + intercept)
            drift[k] = float(slope * 1000.0)          # per mm
            resid[k] = float(np.std(y - (slope * x + intercept), ddof=0))
    else:
        # Too few frames to separate drift from noise; fall back to the mean
        # and say so by leaving the drift undefined.
        for k in (1, 2, 3):
            c[k] = float(d[f"c{k}"].mean())
            drift[k] = np.nan
            resid[k] = float(d[f"c{k}"].std(ddof=0))
    return c, drift, resid, float(x.min() - x_ref_um)


def per_droplet(df, geom):
    """Collapse frames to one row per droplet, after the startup cut."""
    t_cut, t_flush, period, period_src = settle_cut(df, geom)

    # Cut on FORMATION time, per droplet -- not on frame time. A droplet that
    # formed before the cut is contaminated for its whole life; keeping its
    # later frames keeps the contamination and, worse, leaves only frames far
    # downstream, which lengthens the extrapolation back to the junction and
    # weakens the fit exactly where it is already weakest.
    t_first = df.groupby("droplet_id").time_s.transform("min")
    kept = df[t_first >= t_cut]
    n_dropped = df.droplet_id.nunique() - kept.droplet_id.nunique()
    if kept.empty:
        sys.exit(
            f"Every droplet formed before the settle cut at {t_cut*1e3:.0f} ms "
            f"({t_flush*1e3:.0f} ms to flush the leg and merge node, plus one "
            f"{period*1e3:.0f} ms formation period).\nThe run is too short to "
            f"say anything about the encoder; raise endTime or shorten "
            f"--l-leg.\nNote this cut is LATER than t_transit_s "
            f"({geom['t_transit_s']*1e3:.0f} ms), which counts the leg only.")

    # Composition is read at the downstream edge of the junction -- where the
    # droplet detaches, and therefore where its code is written.
    x_ref = float(geom["x_junction_um"][1])

    rows = []
    for did, d in kept.groupby("droplet_id"):
        if len(d) < 2:
            continue
        c, drift, resid, extrap = _fit_to_station(d, x_ref)
        # Within-droplet scatter of the core signal itself, straight from the
        # frames. A clean slug advects rigidly, so its composition is fixed and
        # this is only measurement noise (~0.003 here). A coalescence event or
        # a mistrack makes the frames disagree -- the -0.20 outlier in the
        # 6.5 s run had 0.043, 12x the norm. It is the honest "is this one
        # rigid droplet" number, and report() filters on it.
        core_frames = d.c2 - 0.5 * (d.c1 + d.c3)
        rec = {"droplet_id": did, "n_frames": len(d),
               "t_first_s": d.time_s.min(),
               "L_um": d.L_um.mean(), "V_nL": d.V_nL.mean(),
               "extrap_um": extrap,
               "core_within_sd": float(core_frames.std(ddof=0))}
        for k in (1, 2, 3):
            rec[f"c{k}"] = c[k]
            rec[f"c{k}_within_sd"] = resid[k]
            rec[f"c{k}_drift_per_mm"] = drift[k]
            rec[f"c{k}_rawmean"] = float(d[f"c{k}"].mean())
        if "dye_closure_err" in d:
            rec["dye_closure_err"] = d.dye_closure_err.max()
        if "dye_outside_frac" in d:
            rec["dye_outside_frac"] = d.dye_outside_frac.mean()
        # Same quantities at a stricter interface cut, to expose how much of
        # the answer rests on where the interface is sliced.
        for src, dst in (("core_bias_strict", "core_strict"),
                         ("asym_strict", "asym_strict")):
            if src in d:
                rec[dst] = d[src].mean()
        rows.append(rec)
    return (pd.DataFrame(rows), n_dropped,
            {"t_cut": t_cut, "t_flush": t_flush, "period": period,
             "period_src": period_src, "x_ref": x_ref})


def flag_unstable(drops):
    """Drop droplets whose composition is not internally consistent.

    A droplet's code is fixed at pinch-off and cannot change as it advects, so
    across its frames the core signal should hold to within measurement noise.
    A droplet that instead disagrees frame-to-frame is not one rigid slug: it
    is a coalescence event, a satellite catching its parent, or a tracking slip
    that stitched two bodies together. Its mean is not a symbol and must not
    enter the statistics.

    The threshold is self-calibrating -- a robust centre and spread of the
    population's own within-scatter (median + 4x scaled-MAD), floored so a run
    where every droplet is clean does not manufacture a cut from pure noise.
    On the 6.5 s multiphase run this removes exactly the one coalescence
    droplet (within-scatter 0.043) that levered the OLS trend to -0.035; the
    robust mean barely moves because it was never really there.

    This is NOT the |core| > 0.07 outlier test used in the write-up. That test
    peeks at the answer -- it removes droplets for having an extreme result,
    which biases the mean toward zero by construction. This one removes them
    for being self-inconsistent, a property of the measurement independent of
    what value it lands on, so an unstable droplet that happened to read ~0
    is dropped too.
    """
    if "core_within_sd" not in drops or len(drops) < 4:
        return drops, drops.iloc[:0]
    w = drops.core_within_sd.to_numpy()
    med = float(np.median(w))
    mad = float(np.median(np.abs(w - med))) * 1.4826
    thr = max(med + 4.0 * mad, 0.015)     # floor: 4-5x a clean droplet's noise
    keep = drops.core_within_sd <= thr
    return drops[keep].reset_index(drop=True), drops[~keep]


def report(case, label=""):
    df_raw, geom = load(case)
    df = track(df_raw, geom)
    drops, n_dropped, cut = per_droplet(df, geom)
    drops, unstable = flag_unstable(drops)
    c_cmd = np.array(geom["commanded_c"])
    dim = "2D" if geom["two_d"] else "3D"

    print(f"\n{'='*68}\n{label or case.name}   [{dim}, w = {geom['w_main_um']:.0f} um]\n{'='*68}")
    print(f"{len(drops)} droplets measured after the {cut['t_cut']*1e3:.0f} ms "
          f"settle cut ({n_dropped} startup droplets discarded)")
    if len(unstable):
        ids = ", ".join(f"#{int(r.droplet_id)}(sd={r.core_within_sd:.3f})"
                        for r in unstable.itertuples())
        print(f"  {len(unstable)} unstable droplet(s) dropped -- composition not "
              f"rigid frame-to-frame\n  (coalescence / mistrack): {ids}")
    print(f"  cut = {cut['t_flush']*1e3:.0f} ms to flush leg + merge node"
          f"  +  1 formation period ({cut['period_src']})")
    print(f"  composition read at x = {cut['x_ref']:.0f} um (pinch-off), "
          f"extrapolated from {drops.extrap_um.min():.0f}-"
          f"{drops.extrap_um.max():.0f} um downstream")

    if "dye_closure_err" in drops:
        worst = drops.dye_closure_err.max()
        verdict = "OK" if worst < 0.02 else "*** SUSPECT ***"
        print(f"dye closure error: {worst:.2%}   {verdict}")
        print("  (sum of dyes vs alpha.water per droplet -- the dyes are passive\n"
              "   scalars without MULES compression, so this is the numerical\n"
              "   leakage and it BOUNDS how much of any bias below is not real.)")
        if worst >= 0.02:
            print("  Leakage exceeds 2%. A core-vs-wall bias smaller than this\n"
                  "  cannot be distinguished from differential dye leakage.\n"
                  "  Refine the mesh (--dx 20) before reporting anything.")

    if "dye_outside_frac" in drops:
        out = float(drops.dye_outside_frac.mean())
        print(f"below the mask: {out:.2%} of the window's dye sits in cells with "
              f"water < 0.5.\n  Part interface shell, part escape -- not "
              f"comparable between solvers.")
    if "dye_dry_frac" in drops:
        dry = float(drops.dye_dry_frac.mean())
        verdict = "OK" if dry < 0.01 else "*** LEAKING ***"
        print(f"in essentially pure oil: {dry:.3%}   {verdict}")
        print("  Material in cells with water < 0.01. This is the real escape,\n"
              "  and it means the same thing for passive scalars and for\n"
              "  multiphase (where it is ~0 by construction). It is the number\n"
              "  that bounds how much of any bias below is the method leaking.")

    # Post-pinch-off drift. This is a pure artifact -- composition is fixed at
    # detachment -- so it is reported as a correction size, not a result. When
    # the correction is comparable to the bias being measured, the bias is
    # resting on an extrapolation rather than on data.
    drift_cols = ["c1_drift_per_mm", "c2_drift_per_mm", "c3_drift_per_mm"]
    if drift_cols[0] in drops and drops[drift_cols].notna().any().any():
        dr = drops[drift_cols].to_numpy()
        worst_drift = float(np.nanmax(np.abs(dr)))
        corr = worst_drift * abs(drops.extrap_um.mean()) / 1000.0
        print(f"\ndye-leakage drift: up to {worst_drift:+.4f} per mm of travel "
              f"(c1/c2/c3 = "
              f"{np.nanmean(dr[:, 0]):+.4f}/{np.nanmean(dr[:, 1]):+.4f}/"
              f"{np.nanmean(dr[:, 2]):+.4f})")
        print(f"  Composition cannot change after pinch-off, so this is the\n"
              f"  passive scalars bleeding differentially across the interface.\n"
              f"  Correcting for it moved the composition by ~{corr:.4f}.")
        if corr > 0.01:
            print("  This correction is LARGE. The reported bias depends on the\n"
                  "  linear extrapolation back to the junction being right.\n"
                  "  Write output more often, or measure nearer the junction.")

    c = drops[["c1", "c2", "c3"]].to_numpy()
    mean = c.mean(axis=0)
    # ddof=1 on a single droplet is a divide-by-zero, and the resulting nan
    # would quietly pass every comparison below it. n < 2 is reported as a
    # missing scatter estimate instead.
    sd = c.std(axis=0, ddof=1) if len(drops) > 1 else np.full(3, np.nan)
    within = drops[["c1_within_sd", "c2_within_sd", "c3_within_sd"]].mean().to_numpy()

    print(f"\n--- 1. Fidelity ---")
    print(f"{'':>6} {'commanded':>10} {'realized':>10} {'bias':>10} "
          f"{'between-sd':>11} {'within-sd':>10}")
    for k in range(3):
        print(f"  c{k+1}: {c_cmd[k]:>10.4f} {mean[k]:>10.4f} "
              f"{mean[k]-c_cmd[k]:>+10.4f} {sd[k]:>11.4f} {within[k]:>10.4f}")

    # The symmetry control gates everything downstream of it.
    print(f"\n--- 2. Symmetry control (c1 vs c3, equal by construction) ---")
    asym = mean[0] - mean[2]
    # Compare against the between-droplet scatter: an asymmetry smaller than
    # the noise on it is not evidence of anything.
    se = np.sqrt(sd[0]**2 + sd[2]**2) / max(np.sqrt(len(drops)), 1)
    print(f"  c1 - c3 = {asym:+.5f}   (standard error {se:.5f})")
    # The composition integral is masked at alpha > 0.5 and is therefore
    # independent of the integration window. It is NOT independent of where
    # the interface is cut. Showing the strict-cut value alongside keeps a
    # verdict that flips between the two from reading as a clean pass.
    if "asym_strict" in drops:
        a_s = float(drops.asym_strict.mean())
        print(f"  at a stricter interface cut (alpha > 0.9): {a_s:+.5f}")
        if np.sign(a_s) != np.sign(asym) or abs(a_s - asym) > max(abs(asym), 0.005):
            print("  *** CUT-DEPENDENT *** The two cuts disagree materially.\n"
                  "  This control is not resolving a real asymmetry; do not\n"
                  "  read either value as the answer.")
    if len(drops) < 2:
        # With one droplet there is no between-droplet scatter to test
        # against, and nan comparisons below would silently read as "passed".
        print("  n = 1: NO SCATTER ESTIMATE. This control cannot run, so\n"
              "  nothing below it is gated. Treat the run as inconclusive\n"
              "  rather than as a pass -- raise endTime.")
    elif abs(asym) > 3 * se and abs(asym) > 0.005:
        # NOTE: this was originally read as a run-quality gate -- a nonzero
        # c1-c3 was assumed to mean a broken mesh/decomposition/BC, because the
        # legs are mirror images in plan. results/encoder_dye_2026-08 showed
        # that assumption is wrong: the clean multiphase run gives a stationary
        # c1-c3 ~ -0.035 because oil crosses the junction in one direction, so
        # the upstream lamina (dye1) is stripped more than the downstream one
        # (dye3). It is a REAL in-plane leg asymmetry, not an artifact, and it
        # does NOT invalidate the core-vs-wall bias -- which averages c1 and c3
        # and so cancels it. Flagged, not fatal.
        print("  *** ASYMMETRIC *** c1 and c3 differ by more than scatter.\n"
              "  This is most likely the REAL leg asymmetry (oil crosses the\n"
              "  junction one way; dye1 is stripped more than dye3) -- see\n"
              "  results/encoder_dye_2026-08 -- NOT a broken run. It does not\n"
              "  invalidate the core-vs-wall bias below, which averages c1,c3.\n"
              "  Only suspect mesh/decomposition/BCs if |c1-c3| is far larger\n"
              "  than the ~0.035 measured there, or flips sign between meshes.")
    else:
        print("  Symmetric within scatter. The measurement is self-consistent,\n"
              "  so a c2 departure below can be read as physical.")

    print(f"\n--- 3. Core-vs-wall sampling bias (the 3D signature) ---")
    wall = 0.5 * (mean[0] + mean[2])
    bias = mean[1] - wall
    rel = bias / wall if wall else np.nan
    print(f"  c2 - (c1+c3)/2 = {bias:+.5f}   ({rel:+.2%} relative)")
    print(f"  In 2D this must be ~0 (no corners exist). A nonzero value in 3D,\n"
          f"  with the symmetry control passing, is corner intrusion in the\n"
          f"  water leg biasing the junction toward the core lamina.")

    # The bias and the capacity have very different sample-size needs, and
    # conflating them is the easiest way to overclaim from a short run. The
    # bias is a statement about the MEAN, which a handful of droplets supports
    # if the within-droplet noise is small. The capacity is a statement about
    # the between-droplet SD, which a handful of droplets does not support at
    # all -- an SD from n=4 has roughly a 40% standard error of its own.
    N_FOR_SD = 8
    print(f"\n--- 4. Channel estimate ---")
    if len(drops) < N_FOR_SD:
        print(f"  n = {len(drops)} droplets: TOO FEW for a spread-based claim.")
        print(f"  The bias above is still usable (it is a statement about the")
        print(f"  mean); the numbers below are indicative only. Yield is")
        print(f"  (endTime - {cut['t_cut']*1e3:.0f} ms) / {cut['period']*1e3:.0f} ms, "
              f"so reaching n = {N_FOR_SD} needs")
        need = cut["t_cut"] + N_FOR_SD * cut["period"]
        print(f"  endTime >= {need:.2f} s.")
    # Composition lives on the 2-simplex. Treat the per-symbol noise as
    # isotropic with scale sd_mean and require codes separated by 3 sigma to
    # be reliably distinguishable. This is a scaling argument: it ignores the
    # simplex boundary, any noise correlation between dyes, and all decoder
    # cleverness. Treat it as an order of magnitude.
    sd_mean = float(sd.mean())
    if sd_mean <= 0:
        print("  per-symbol sd is zero -- too few droplets, or every droplet\n"
              "  measured identically. No channel estimate possible.")
    else:
        levels = 1.0 / (3.0 * sd_mean)
        n_codes = max(0.5 * levels ** 2, 1.0)   # 2-simplex area in noise cells
        print(f"  per-symbol sd = {sd_mean:.4f} -> ~{levels:.1f} levels per axis")
        print(f"  ~{n_codes:.0f} distinguishable codes "
              f"(~{np.log2(n_codes):.1f} bits/droplet at 3-sigma spacing)")
        print(f"  Scaling argument only: ignores simplex boundaries, inter-dye\n"
              f"  noise correlation, and decoding. Order of magnitude.")
        ratio = within.mean() / sd_mean
        limited = ("measurement-limited, refine the mesh before believing the"
                   " spread" if ratio > 1 else "physics-limited, the spread is real")
        print(f"  measurement noise is {ratio:.2f}x the per-symbol noise "
              f"-- {limited}")

    return {"dim": dim, "mean": mean, "sd": sd, "asym": asym, "bias": bias,
            "n": len(drops), "cmd": c_cmd}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("case_dir", type=Path)
    ap.add_argument("--compare-with", type=Path, default=None,
                    help="Second case (the matched 2D or 3D twin). The "
                         "difference in core-vs-wall bias between them IS the "
                         "dimensionality result.")
    args = ap.parse_args()

    a = report(args.case_dir.resolve())
    if args.compare_with:
        b = report(args.compare_with.resolve())
        print(f"\n{'='*68}\nDIMENSIONALITY COMPARISON\n{'='*68}")
        print(f"  {a['dim']} core-vs-wall bias: {a['bias']:+.5f}")
        print(f"  {b['dim']} core-vs-wall bias: {b['bias']:+.5f}")
        print(f"  difference:            {a['bias']-b['bias']:+.5f}")
        print("\n  If the 2D case shows ~0 and the 3D case does not, the encoder\n"
              "  has a geometric sampling bias that only a 3D mesh can see --\n"
              "  and any bench calibration derived from 2D would be wrong by\n"
              "  that amount. If both are ~0, integrated readout is unbiased and\n"
              "  the mixing-insensitivity argument holds as stated.")


if __name__ == "__main__":
    main()
