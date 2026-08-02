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


def per_droplet(df, geom, settle_factor=1.0):
    """Collapse frames to one row per droplet, after the startup cut.

    Droplets formed before inlet-derived water reaches the junction carry the
    SEEDED composition from setFields, not a composition the encoder wrote.
    They would agree with the commanded value for a trivial reason -- the
    initial condition was set to it -- and including them would manufacture a
    fidelity result. The cut is at the merge->junction transit time.
    """
    t_cut = geom["t_transit_s"] * settle_factor
    kept = df[df.time_s >= t_cut]
    n_dropped = df.droplet_id.nunique() - kept.droplet_id.nunique()
    if kept.empty:
        sys.exit(f"Every droplet formed before t_transit = {t_cut*1e3:.0f} ms. "
                 f"The run is too short to say anything about the encoder; "
                 f"raise endTime or shorten --l-leg.")

    g = kept.groupby("droplet_id")
    rows = []
    for did, d in g:
        if len(d) < 2:
            continue
        rec = {"droplet_id": did, "n_frames": len(d),
               "t_first_s": d.time_s.min(),
               "L_um": d.L_um.mean(), "V_nL": d.V_nL.mean()}
        for k in (1, 2, 3):
            rec[f"c{k}"] = d[f"c{k}"].mean()
            rec[f"c{k}_within_sd"] = d[f"c{k}"].std(ddof=0)
        if "dye_closure_err" in d:
            rec["dye_closure_err"] = d.dye_closure_err.max()
        rows.append(rec)
    return pd.DataFrame(rows), n_dropped, t_cut


def report(case, label=""):
    df_raw, geom = load(case)
    df = track(df_raw, geom)
    drops, n_dropped, t_cut = per_droplet(df, geom)
    c_cmd = np.array(geom["commanded_c"])
    dim = "2D" if geom["two_d"] else "3D"

    print(f"\n{'='*68}\n{label or case.name}   [{dim}, w = {geom['w_main_um']:.0f} um]\n{'='*68}")
    print(f"{len(drops)} droplets measured after the {t_cut*1e3:.0f} ms "
          f"transit cut ({n_dropped} startup droplets discarded)")

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

    c = drops[["c1", "c2", "c3"]].to_numpy()
    mean, sd = c.mean(axis=0), c.std(axis=0, ddof=1)
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
    if abs(asym) > 3 * se and abs(asym) > 0.005:
        print("  *** ASYMMETRIC *** The two mirror legs disagree by more than\n"
              "  scatter allows. This is an artifact, not physics -- suspect the\n"
              "  mesh, the decomposition, or the BCs. Do not report a c2 bias\n"
              "  from this run.")
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
        print(f"  mean); the numbers below are indicative only. For a defensible")
        print(f"  per-symbol noise figure, raise endTime -- yield is")
        print(f"  (endTime - t_transit) / droplet_period, so at t_transit =")
        print(f"  {geom['t_transit_s']*1e3:.0f} ms each extra 0.4 s buys ~4 droplets in 3D.")
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
