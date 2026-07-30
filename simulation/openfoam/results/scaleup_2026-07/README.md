# Scale-up: 400 → 600 → 800 µm, same regime — 2026-07

## Why

The 400 µm chip is one pass of a 1/64" endmill. That tool works, but it is
not a *replicable* requirement: a 0.4 mm endmill in a hobby CNC needs
careful workholding, low runout, and an operator who has broken enough of
them to have opinions. Endmill stiffness goes as d⁴, so a 0.6 mm tool is
5× stiffer and a 0.8 mm tool 16× stiffer than 1/64". If the chamber works
at 600 or 800 µm, the fabrication bar drops from "experienced machinist"
to "anyone with a $500 mill".

The physics argument for why it *should* work: the droplet regime is set by
the capillary number Ca = µU/σ, which contains no length. Hold Ca fixed —
which means holding the mean **velocity** fixed, not the flow rate — and
the flow should be similar at any width. `gen_blockmesh.py --w-main`
therefore scales every width-like dimension with w while leaving channel
*lengths* alone, so drive pressures fall as 1/w² (R ∝ 1/w⁴ for a square
duct, Q ∝ w²) and the bigger chip is also the easier chip to actuate.

That is the prediction. This directory is the measurement.

## Runs

Three 2D pressure-driven cases, identical apart from width. Drive pressures
were chosen to hold the **capillary-corrected** drive ratio constant:
(P_disp − 2σ/w)/P_cont = 0.4231, 0.4220, 0.4235 — the same to ±0.2%.

| w | P_cont | P_disp | dx | cells | endTime | wall time |
|---|---|---|---|---|---|---|
| 400 µm | 3900 Pa | 1800 Pa | 20 µm | 9440 | 0.30 s | 2.7 h |
| 600 µm | 1730 Pa | 830 Pa | 30 µm | 7440 | 0.45 s | 1.2 h |
| 800 µm | 980 Pa | 490 Pa | 40 µm | 6440 | 0.60 s | 0.85 h |

The 400 µm row is the previously verified reference (`mill_2026-07`, sweep
cell `pc3.9k_pd1.8k`), re-extracted here with the same script so all three
numbers come from one code path. dx = w/20 in every case, so mesh
resolution *relative to the channel* is identical.

## Result — similarity holds to within 4%

All three widths form clean, periodic droplet trains. Three complete
droplets measured at each scale.

| Observable | 400 µm | 600 µm | 800 µm | prediction | worst error |
|---|---|---|---|---|---|
| Slug length L | 600 µm | 932 µm | 1240 µm | ∝ w | +3.6% |
| **L / w** | **1.500** | **1.554** | **1.550** | flat | +3.6% |
| Advection speed | 28.09 mm/s | 28.04 mm/s | 28.46 mm/s | flat | +1.3% |
| Period | 87.5 ms | 135 ms | 175 ms | ∝ w | −2.8% |
| Droplet rate | 11.43 Hz | 7.41 Hz | 5.71 Hz | ∝ 1/w | −2.8% |
| Q_oil | 3.193 µL/s | 7.121 µL/s | 12.694 µL/s | ∝ w² | −0.8% |
| Q_water | 0.895 µL/s | 2.020 µL/s | 3.706 µL/s | ∝ w² | +3.5% |
| Droplet volume | 78 nL | 273 nL | 649 nL | ∝ w³ | +3.6% |

Predictions are anchored on the 400 µm point — the width that was verified
first — so 600 and 800 are genuine out-of-sample predictions, not a fit.

`scale_comparison.png` shows this two ways: a filmstrip of all three chips
drawn on one common physical scale (the 800 µm channel really is twice as
thick on the page), and the four observables against w with their predicted
scalings and a ±10% band.

**The scale-up is viable.** 600 µm and 800 µm reproduce the 400 µm chamber's
behaviour, and neither is anywhere near a physical limit — Bond number is
0.0084 at 800 µm (buoyancy under 1% of capillarity; Bo = 1 only at w =
8.7 mm) and Reynolds number is 0.45 (entrance length ~18 µm, so the fixed
2 mm approach is ample even at 2.5 channel widths).

## The one systematic deviation

L/w rises 3.5% from 400 to 600 and then stays flat to 800. It is not drift
with w — 600 and 800 agree with each other to 0.3% — so it looks like a
step between the reference case and the scaled ones rather than a scaling
failure.

Measured q = Q_disp/Q_cont drifts the same direction: 0.280 → 0.284 →
0.292. Through Garstecki (L/w = 1 + αq, so α ≈ 1.79 here), that +4.3% in q
accounts for roughly +1.4% of the +3.5% in L/w. **The remaining ~2% is
unexplained.** Candidates, none tested:

- The outlet is a fixed 4000 µm, so it is 10 channel widths at 400 µm but
  only 5 at 800 µm. Outlet crowding has already produced one artifact in
  this project (the spurious 997 µm "full channel" signature in
  `mesh_convergence_2026-07`), so it is the leading suspect — but if it
  were the cause, the deviation should worsen from 600 to 800, and it does
  not.
- Interface resolution: dx/w is constant, but absolute dx grows, and the
  thin oil film between slug and wall is a fixed *physical* thickness set
  by Ca, not a fixed number of cells. At 40 µm cells that film is
  under-resolved.

2% is well inside the ±10% band and below the 3–19% spread the mesh
convergence study found, so it does not change the conclusion. It is
recorded here rather than smoothed over.

## Secondary findings

**Scale-up is cheaper to simulate.** Per simulated second: 32,000 s of wall
time at 400 µm, 9,700 at 600, 5,100 at 800 — a 6× saving, because the
Brackbill capillary timestep limit goes as √(dx³). Per droplet the saving
is ~3× (2800 → 1300 → 890 s), since bigger chips also run slower clocks.

**Sample throughput improves a lot.** At 800 µm the chip consumes water at
3.7 µL/s, so 1 L of sample takes 75 hours versus 310 hours at 400 µm.

**The pressure-driven cyclicity signature survives.** Inlet flow rates
still oscillate at the droplet frequency at every scale (Q_water CV 3.8% →
6.9% → 7.4%, Q_oil 2.2% → 2.0% → 3.7%), so the emergent-flow behaviour the
cyclicity test relies on is not an artifact of the small geometry. The
rising water CV is consistent with the shrinking outlet-length-in-widths
noted above and should not be read as a chip property.

**Actuation gets tighter, not looser.** This is the one thing scale-up
makes worse. Capillary entry pressure is 2σ/w, so as a fraction of drive
pressure it goes 8.3% → 12% → 15.3%. Combined with the ±18% droplet-forming
window from the 5×5 sweep, the water column must be set to about ±0.9 cm
H₂O at 800 µm versus ±3.3 cm at 400 µm. A bottle on a printer Z-axis
resolves 0.1 mm, so this is comfortable in practice — but it is why the
scale-up cannot continue indefinitely even though Bo says it could.

## Instrumentation consequence

Because U is held fixed by the Ca-preserving design, **scaling up does not
slow the interface down** — it stays at ~28 mm/s at every width. Camera
exposure is therefore set by scale-independent physics: 28 µm of travel per
millisecond means ≤300 µs exposure to keep motion blur under 1% of slug
length. What scale-up *does* relax is frame rate, since f ∝ 1/w: 120 fps is
comfortable at 600 µm and 90 fps at 800 µm, against 170 fps at 400 µm.

## Files

- `scale_comparison.png` — filmstrip on a common physical scale + the four
  scaling laws with ±10% bands
- `summary.csv` — every number in the results table
- `flux_400um.csv`, `flux_600um.csv`, `flux_800um.csv` — inlet flow-rate
  time series (the cyclicity observable)

## Reproduce

```bash
# geometry
python3 gen_blockmesh.py --w-main 600      # in tjunction_2d_mill/

# extraction and figure (all three, one code path)
python3 scripts/plot_scale_comparison.py \
    400:$CASES/mill_sweep/pc3.9k_pd1.8k \
    600:$CASES/mill2d_600um \
    800:$CASES/mill2d_800um \
    --out scale_comparison.png
```

Note `foamToVTK` must be run with `-legacy`; the extractor reads legacy
`.vtk` files, not the `.vtm`/`.vtu` tree that v2306 writes by default.

## Not done

- **3D at 600/800 µm.** Everything here is 2D, which has no corner gutters
  and therefore overstates junction blockage. The 3D fidelity check at
  400 µm was killed and restarted at a corrected operating point and has
  not been re-measured; `mill3d_2026-07`'s numbers remain not-for-quoting.
  Whichever width becomes the reference design needs a 3D pass.
- **Operating-window sweep at the new scale.** The ±18% window is a 400 µm
  measurement being extrapolated. Given that the capillary threshold is a
  larger fraction of drive pressure at 800 µm, the window may well be
  narrower there, which is exactly the number the hardware guide needs.
