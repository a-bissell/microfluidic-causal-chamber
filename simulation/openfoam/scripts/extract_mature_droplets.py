#!/usr/bin/env python3
"""Track-based droplet extraction: measure only fully-formed (detached) slugs.

analyze_pressure_sweep.py's free-droplet filter is a static length/position
window; it works when droplets pinch off quickly relative to the output
frame rate, but a still-growing, still-attached water thread mid-formation
(length increasing every frame as it's fed from the inlet) can pass through
that window too, and gets counted as an independent "droplet" observation at
whatever length it happened to be at that instant. Averaging those snapshots
in with genuinely detached slugs inflates and destabilizes the median. (This
surfaced clearly on a finer 5 um mesh where growth-phase frames dominated
the window; the coarser 7.5 um datasets happen not to show it badly at their
endTime, but the underlying static-window approach doesn't distinguish
"small droplet" from "large droplet, early in formation" anywhere.)

This script instead links raw detections into per-droplet tracks (frame-to-
frame position continuity) and finds each track's length PLATEAU: the
region after growth has stopped (frame-to-frame length change below
--growth-threshold-um), which is the actual, finished slug. Tracks that
are still growing when they exit the frame or the run ends are incomplete
and excluded rather than counted at a mid-growth length. Frequency is the
count of complete tracks per unit time (droplets actually observed to
finish forming) rather than a reference-line crossing count.

Usage:
    python3 extract_mature_droplets.py <case_dir> [--w-main-um 150]
        [--x-junction-um None] [--growth-threshold-um 20] [--min-track-frames 3]
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from extract_droplets import DropletExtractor  # noqa: E402


def link_tracks(df, max_advance_um):
    """Chain frame-to-frame nearest-neighbor detections into tracks."""
    tracks = []
    active = []  # list of (x, track_id)
    for t in sorted(df.time.unique()):
        rows = df[df.time == t].sort_values("centroid_x")
        used = set()
        new_active = []
        for _, row in rows.iterrows():
            x = row.centroid_x
            cand = [(i, ax) for i, (ax, tid) in enumerate(active)
                    if i not in used and 0 <= x - ax < max_advance_um]
            if cand:
                i, ax = min(cand, key=lambda c: x - c[1])
                used.add(i)
                tid = active[i][1]
            else:
                tid = len(tracks)
                tracks.append([])
            tracks[tid].append((t, x, row.length, row.width))
            new_active.append((x, tid))
        active = new_active
    return tracks


def mature_length(track, growth_threshold_um, min_length_um):
    """Return (mature_length, mature_width, complete) for one track.

    A still-attached, still-growing water thread stays roughly anchored in
    x (fed from the inlet) while its length extends -- length changing but
    position not. A genuinely detached slug translates rigidly: position
    advancing frame to frame while length stays flat. Require BOTH a flat
    length AND positive x-advancement to call a frame "mature"; length
    alone false-positives on the stationary-growing case. min_length_um
    excludes small numerical fragments/satellite noise -- not real slugs.
    """
    if len(track) < 3:
        return None, None, False
    mature_frames = []
    for i in range(1, len(track)):
        dl = abs(track[i][2] - track[i - 1][2])
        dx = track[i][1] - track[i - 1][1]
        if dl < growth_threshold_um and dx > 0 and track[i][2] >= min_length_um:
            mature_frames.append(track[i])
    if len(mature_frames) < 2:
        return None, None, False
    return (np.median([p[2] for p in mature_frames]),
            np.median([p[3] for p in mature_frames]), True)


def process(case_dir, w_main_um, x_junction_um, growth_threshold_um, min_track_frames,
            max_advance_um, min_length_um):
    ex = DropletExtractor(case_dir, w_main_m=w_main_um * 1e-6,
                          x_junction_m=(x_junction_um * 1e-6) if x_junction_um is not None else None)
    df, _ = ex.process_case()
    if df.empty:
        return {"n_tracks": 0, "n_complete": 0}

    df = df[df.centroid_y < w_main_um]
    tracks = link_tracks(df, max_advance_um)
    tracks = [t for t in tracks if len(t) >= min_track_frames]

    results = []
    for tr in tracks:
        L, W, complete = mature_length(tr, growth_threshold_um, min_length_um)
        if complete:
            results.append({"first_t": tr[0][0], "last_t": tr[-1][0], "L_um": L, "w_um": W,
                            "n_frames": len(tr)})
    res = pd.DataFrame(results)
    out = {"n_tracks": len(tracks), "n_complete": len(res)}
    if len(res):
        out["L_um_median"] = res.L_um.median()
        out["w_um_median"] = res.w_um.median()
        out["L_over_w"] = out["L_um_median"] / w_main_um
        starts = sorted(res.first_t)
        duration = df.time.max() - df.time.min()
        out["frequency_Hz"] = len(starts) / duration if duration > 0 else np.nan
        if len(starts) >= 2:
            out["formation_gap_ms"] = float(np.median(np.diff(starts))) * 1000
    return out, res


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("case_dir", type=Path)
    p.add_argument("--w-main-um", type=float, default=150.0)
    p.add_argument("--x-junction-um", type=float, default=None)
    p.add_argument("--growth-threshold-um", type=float, default=20.0)
    p.add_argument("--min-track-frames", type=int, default=3)
    p.add_argument("--max-advance-um", type=float, default=60.0,
                   help="Max plausible per-frame advection distance for track linking; "
                        "default assumes ~writeInterval-scale motion, not a whole channel width")
    p.add_argument("--min-length-um", type=float, default=80.0,
                   help="Exclude sub-noise-floor fragments from being counted as slugs")
    args = p.parse_args()

    summary, tracks_df = process(args.case_dir, args.w_main_um, args.x_junction_um,
                                 args.growth_threshold_um, args.min_track_frames,
                                 args.max_advance_um, args.min_length_um)
    print(f"{args.case_dir}: {summary}")
    if len(tracks_df):
        print(tracks_df.to_string(index=False))


if __name__ == "__main__":
    main()
