#!/usr/bin/env python3
"""Size the off-chip flow resistors and bench heads for the chip AS DRAWN.

The OpenFOAM operating point (scaleup_2026-07) is a pair of inlet pressures
on a simulated network: a 46 mm oil-feed proxy, a 2 mm approach, a 4 mm
outlet and a narrow water-resistor proxy, all 2D. The bench is a different
network: round tubing, the milled chip's square channels, and an outlet
long enough to watch. This script makes the two agree element by element:

  1. Calibrate a lumped model of the SIMULATED network from its own geometry
     (2D slot flow, R = 12 mu L / (h^3 D)) and the measured fluxes. This
     gives the time-averaged junction pressure P_j the simulation ran at.
  2. Size each bench element to its simulated counterpart:
         oil tubing + delivery + chip approach   = sim oil feed + approach
         water tubing + delivery + chip water leg = sim water resistor + leg
     Square ducts are R = 28.4 mu L / w^4, tubes R = 128 mu L / (pi d^4).
  3. The outlet cannot match: 4 mm of 2D slot is the resistance of only
     ~1.7 mm of real square duct, and you need ~11 mm to see 2-3 slugs. The
     excess outlet resistance raises P_j by dR * Q_total at the design flow,
     equally for both phases, so both heads go up by that amount.
  4. Forward-solve the bench network at the stated heads and rounded tube
     lengths and compare the flows with the simulation.

sigma = 30 mN/m throughout. At fixed Ca every pressure here scales as sigma
(U = Ca sigma / mu, and every term is viscous), so the heads scale with it;
the tube LENGTHS do not depend on sigma.

Run:  python3 size_resistors.py
"""
import csv
import math
from pathlib import Path

HERE = Path(__file__).parent
SUMMARY = HERE / "../../simulation/openfoam/results/scaleup_2026-07/summary.csv"

MU_OIL, MU_WATER = 0.048, 0.001          # Pa.s (50 cSt silicone oil, water)
SIGMA = 0.030                            # N/m, uncited -- see wetting_2026-08
PA_PER_CM = 98.07                        # 1 cm H2O
RHO_OIL = 960.0                          # an oil column is 1000/960 taller

# ---- simulated network (simulation/openfoam/tjunction_2d_mill/gen_blockmesh.py)
SIM_OIL_FEED, SIM_APPROACH, SIM_OUTLET = 46e-3, 2e-3, 4e-3
SIM_WATER_RES_L, SIM_WATER_LEG = 27e-3, 2e-3
SIM_WATER_RES_W = lambda w: 80e-6 * w / 400e-6   # scales with w

# ---- bench, both widths: off-chip parts (metres) --------------------------
INCH = 25.4e-3
OIL_TUBE_ID = INCH / 16                  # 1/16" ID PTFE
WATER_TUBE_ID = 0.5e-3                   # 0.5 mm ID PTFE/PEEK
OIL_DELIVERY = (0.50, INCH / 4)          # bottle -> resistor, 50 cm of 1/4" ID
WATER_DELIVERY = (0.50, INCH / 16)       # 50 cm of 1/16" ID
OUTLET_LINE = (0.10, INCH / 8)           # chip -> waste, 10 cm of 1/8" ID


def slot2d(mu, L, h, D):
    """What the 2D solver computes: flow between plates h apart, depth D."""
    return 12 * mu * L / (h**3 * D)


def duct(mu, L, w):
    return 28.4 * mu * L / w**4


def tube(mu, L, d):
    return 128 * mu * L / (math.pi * d**4)


def sim_rows():
    with open(SUMMARY) as f:
        return {int(r["w_um"]): r for r in csv.DictReader(f)}


def chip_lengths(geom):
    oil, junc, water, out = geom
    return junc[0] - oil[0], water[1] - junc[1], out[0] - junc[0]


def drawing():
    from gen_guide_diagrams import JUNCTION, OIL_PORT, OUT_PORT, WATER_PORT
    return OIL_PORT, JUNCTION, WATER_PORT, OUT_PORT


V2_FIRST_DRAWN = ((15.0, 12.7), (35.0, 12.7), (35.0, 20.5), (60.0, 12.7))


def simulated(w_um):
    """Lumped model of the simulated network, calibrated on its fluxes."""
    r = sim_rows()[w_um]
    w = w_um * 1e-6
    Pc, Pd = float(r["P_cont_Pa"]), float(r["P_disp_Pa"])
    Qo, Qw = float(r["Q_oil_uL_s"]) * 1e-9, float(r["Q_water_uL_s"]) * 1e-9
    R_oil = slot2d(MU_OIL, SIM_OIL_FEED + SIM_APPROACH, w, w)
    R_wat = (slot2d(MU_WATER, SIM_WATER_RES_L, SIM_WATER_RES_W(w), w)
             + slot2d(MU_WATER, SIM_WATER_LEG, w, w))
    R_out = slot2d(MU_OIL, SIM_OUTLET, w, w)       # as if all oil; see README
    Pj = Pc - R_oil * Qo
    return dict(w=w, Pc=Pc, Pd=Pd, Qo=Qo, Qw=Qw, R_oil=R_oil, R_wat=R_wat,
                R_out=R_out, Pj=Pj,
                P_2phase=Pj - R_out * (Qo + Qw),   # slug drag + junction loss
                P_wres=Pd - Pj - R_wat * Qw,        # water-side residual
                spacing=float(r["speed_mm_s"]) * float(r["period_s"]))


def bench(w_um, geom, oil_tube_L=None, water_tube_L=None):
    """Bench network for a chip geometry. Tube lengths default to exact match."""
    s = simulated(w_um)
    w = s["w"]
    a, leg, c = (x * 1e-3 for x in chip_lengths(geom))
    R_app = duct(MU_OIL, a, w)
    R_leg = duct(MU_WATER, leg, w)
    R_odel = tube(MU_OIL, *OIL_DELIVERY)
    R_wdel = tube(MU_WATER, *WATER_DELIVERY)
    if oil_tube_L is None:
        oil_tube_L = (s["R_oil"] - R_app - R_odel) / tube(MU_OIL, 1, OIL_TUBE_ID)
    if water_tube_L is None:
        water_tube_L = (s["R_wat"] - R_leg - R_wdel) / tube(MU_WATER, 1, WATER_TUBE_ID)
    R_oil = tube(MU_OIL, oil_tube_L, OIL_TUBE_ID) + R_odel + R_app
    R_wat = tube(MU_WATER, water_tube_L, WATER_TUBE_ID) + R_wdel + R_leg
    R_chip_out = duct(MU_OIL, c, w)
    R_out = R_chip_out + tube(MU_OIL, *OUTLET_LINE)
    dPj = (R_out - s["R_out"]) * (s["Qo"] + s["Qw"])
    return dict(s=s, a=a, leg=leg, c=c, R_app=R_app, R_leg=R_leg, R_oil=R_oil,
                R_wat=R_wat, R_chip_out=R_chip_out, R_out=R_out, dPj=dPj,
                oil_tube_L=oil_tube_L, water_tube_L=water_tube_L,
                Pc=s["Pc"] + dPj, Pd=s["Pd"] + dPj)


def solve(R_oil, R_wat, R_out, Pc, Pd, P_2phase, P_wres):
    """Mean flows of the lumped network. P_j = R_out*(Qo+Qw) + P_2phase."""
    # Pc - Pj = R_oil Qo ; Pd - Pj - P_wres = R_wat Qw
    g = 1 + R_out / R_oil + R_out / R_wat
    Pj = (P_2phase + R_out * (Pc / R_oil + (Pd - P_wres) / R_wat)) / g
    return (Pc - Pj) / R_oil, (Pd - Pj - P_wres) / R_wat, Pj


def coupling(R_oil, R_wat, R_out):
    """dP_j per Pa of each head: how much one phase's head moves the other."""
    g = 1 + R_out / R_oil + R_out / R_wat
    return R_out / R_oil / g, R_out / R_wat / g


def cm(p):
    return p / PA_PER_CM


def report(w_um, geom, label, round_to=0.5e-2):
    b = bench(w_um, geom)
    s = b["s"]
    oL = round(b["oil_tube_L"] / round_to) * round_to
    wL = round(b["water_tube_L"] / round_to) * round_to
    r = bench(w_um, geom, oL, wL)
    Qo, Qw, Pj = solve(r["R_oil"], r["R_wat"], r["R_out"], r["Pc"], r["Pd"],
                       s["P_2phase"], s["P_wres"])
    print(f"\n=== {w_um} um, {label}: approach {r['a']*1e3:.1f} mm, "
          f"water leg {r['leg']*1e3:.1f} mm, outlet {r['c']*1e3:.1f} mm ===")
    print(f"simulated: Pc {s['Pc']:.0f} / Pd {s['Pd']:.0f} Pa,  "
          f"Qo {s['Qo']*1e9:.3f} / Qw {s['Qw']*1e9:.3f} uL/s,  "
          f"Pc/Qo {s['Pc']/s['Qo']:.3g}")
    print(f"  oil feed+approach {s['R_oil']:.3g}  water res+leg {s['R_wat']:.3g}  "
          f"outlet {s['R_out']:.3g} Pa.s/m3")
    print(f"  P_j {s['Pj']:.0f} Pa = outlet viscous {s['R_out']*(s['Qo']+s['Qw']):.0f}"
          f" + two-phase {s['P_2phase']:.0f};  water residual {s['P_wres']:+.0f} Pa")
    print(f"  Pd - Pj = {s['Pd']-s['Pj']:.0f} Pa vs 2s/w {2*SIGMA/s['w']:.0f}, "
          f"4s/w {4*SIGMA/s['w']:.0f}")
    print(f"bench: oil tube {b['oil_tube_L']*100:.1f} cm of {OIL_TUBE_ID*1e3:.2f} mm ID "
          f"(use {oL*100:.1f}),  water tube {b['water_tube_L']*100:.1f} cm of "
          f"{WATER_TUBE_ID*1e3:.2f} mm ID (use {wL*100:.1f})")
    print(f"  oil path {r['R_oil']:.3g} ({(r['R_oil']/s['R_oil']-1)*100:+.1f}% vs sim), "
          f"chip approach {r['R_app']/r['R_oil']*100:.0f}% of it")
    print(f"  water path {r['R_wat']:.3g} ({(r['R_wat']/s['R_wat']-1)*100:+.1f}% vs sim)")
    print(f"  outlet {r['R_out']:.3g} (chip {r['R_chip_out']:.3g}) vs sim "
          f"{s['R_out']:.3g} -> {r['R_out']/s['R_out']:.1f}x;  dP_j = +{r['dPj']:.0f} Pa")
    print(f"  heads: oil {r['Pc']:.0f} Pa = {cm(r['Pc']):.1f} cm H2O "
          f"({cm(r['Pc'])*1000/RHO_OIL:.1f} cm of oil),  water {r['Pd']:.0f} Pa = "
          f"{cm(r['Pd']):.1f} cm H2O")
    print(f"  forward solve: Qo {Qo*1e9:.3f} ({(Qo/s['Qo']-1)*100:+.1f}%), "
          f"Qw {Qw*1e9:.3f} ({(Qw/s['Qw']-1)*100:+.1f}%), P_j {Pj:.0f} Pa, "
          f"Pd - Pj {r['Pd']-Pj:.0f} Pa")
    print(f"  effective Pc/Qo {r['Pc']/s['Qo']:.3g} ({r['Pc']/s['Pc']:.2f}x sim)")
    k_sim = coupling(s["R_oil"], s["R_wat"], s["R_out"])
    k = coupling(r["R_oil"], r["R_wat"], r["R_out"])
    print(f"  coupling dPj/dPc, dPj/dPd: sim {k_sim[0]:.3f}, {k_sim[1]:.3f}; "
          f"bench {k[0]:.3f}, {k[1]:.3f}")
    print(f"  slug spacing 2D {s['spacing']:.2f} mm; visible outlet past an 8 mm pad "
          f"{r['c']*1e3-4:.1f} mm")
    return r


def to_bench(w_um, geom):
    """Bench heads that reproduce the flows of simulated heads (Pc, Pd).

    Same flows means the same Q_total, so the bench junction sits higher by
    dR_out * Q_total(Pc, Pd), and Q_total is linear in the simulated heads:
        P_bench = P_sim + k0 + kc*(Pc - Pc0) + kd*(Pd - Pd0)
    for both phases. Valid while water is flowing (inside the window).
    """
    s, r = simulated(w_um), bench(w_um, geom)
    dR = r["R_out"] - s["R_out"]

    def offset(Pc, Pd):
        Qo, Qw, _ = solve(s["R_oil"], s["R_wat"], s["R_out"], Pc, Pd,
                          s["P_2phase"], s["P_wres"])
        return dR * (Qo + Qw)
    k0 = offset(s["Pc"], s["Pd"])
    return k0, offset(s["Pc"] + 1, s["Pd"]) - k0, offset(s["Pc"], s["Pd"] + 1) - k0


def legacy(w_um, geom, oil_L, oil_d, wat_L, wat_d):
    """The BOM's original tubing on a given chip, at the simulated heads."""
    s = simulated(w_um)
    w = s["w"]
    a, leg, c = (x * 1e-3 for x in chip_lengths(geom))
    R_oil = tube(MU_OIL, oil_L, oil_d) + duct(MU_OIL, a, w)
    R_wat = tube(MU_WATER, wat_L, wat_d) + duct(MU_WATER, leg, w)
    R_out = duct(MU_OIL, c, w)
    Qo, Qw, Pj = solve(R_oil, R_wat, R_out, s["Pc"], s["Pd"], s["P_2phase"], s["P_wres"])
    print(f"  {w_um} um, outlet {c*1e3:.0f} mm: Qo {Qo/s['Qo']*100:.0f}% of design, "
          f"Qw {Qw/s['Qw']*100:.0f}%, P_j {Pj:.0f} Pa (sim {s['Pj']:.0f})")


if __name__ == "__main__":
    print(f"sigma = {SIGMA*1e3:.0f} mN/m; every pressure below scales with it.")
    print("\n--- the BOM's original tubing, at the simulated heads ---")
    for geom, lab in ((((0, 0), (2, 0), (2, 2), (6, 0)), "sim-length chip"),
                      (V2_FIRST_DRAWN, "v2 as first drawn")):
        print(lab)
        legacy(800, geom, 0.19, INCH / 16, 0.20, 0.5e-3)
        legacy(600, geom, 0.12, 1.0e-3, 0.23, 0.4e-3)
    for w in (800, 600):
        report(w, V2_FIRST_DRAWN, "option (a): keep the 20/25 mm layout")
        report(w, drawing(), "option (b): the drawing as it now stands")
        k0, kc, kd = to_bench(w, drawing())
        print(f"  sim -> bench: P_bench = P_sim + {k0:.0f} + {kc:.3f}*(Pc - Pc0)"
              f" + {kd:.3f}*(Pd - Pd0), both phases")
