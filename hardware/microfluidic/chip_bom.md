# Bill of Materials: T-Junction Microfluidic Causal Chamber

Components needed to build the T-junction microfluidic Causal Chamber. Costs
are estimates and subject to change.

**Design targets** — 800 µm square channels (600 µm also verified), driven
hydrostatically. Two numbers set most of this list:

| | | |
|---|---|---|
| Tool | **1/32" (0.794 mm)** endmill | stiffness goes as d⁴, so this is **16× stiffer** than the 1/64" a 400 µm chip needs — the chip does not require a precision CNC |
| Drive | **980 / 490 Pa** = **10.0 / 5.0 cm** of water | pressure scales as 1/w², so the operating point is a bottle 10 cm above the chip — no compressor, no regulators |

Both measured, not designed:
[`scaleup_2026-07`](../../simulation/openfoam/results/scaleup_2026-07/) and
[`mill3d800_2026-08`](../../simulation/openfoam/results/mill3d800_2026-08/).

---

**1. Microfluidic Chip Fabrication**

Target: **800 µm wide × 800 µm deep** square channels (600 µm also verified).
Depth-to-diameter is 1.0 at every scale, so it is two passes at 0.5×D —
the same technique as at 400 µm, just with a tool that does not snap.

| Item | Quantity | Low Cost Option | Medium Cost Option | High Cost Option | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Acrylic Sheet (PMMA) | 1-2 | ~$10-20 (12"x12", 3 mm) | ~$10-20 (same) | ~$10-20 (same) | Cast, not extruded — extruded has thickness variation that fights a flat bond. |
| Milling Machine | 1 | **~$300-800 (hobby CNC, 3018-class + rigidity upgrades)** | ~$500-1200 (benchtop: Genmitsu PROVerXL, Shapeoko) | ~$1500-5000 (Nomad, Bantam Tools) | At 800 µm the tool is forgiving enough that a hobby CNC is genuinely sufficient. Rigidity and low runout still help, but this is not a precision-micromilling job. |
| End Mills | Set | ~$15-30 (**1/32" / 0.8 mm**, 2-flute, carbide) | ~$30-80 (better coating, spares) | $150+ (precision micro end mills) | **1/32" (0.794 mm) is the part to buy** — stock size, cheap, 16× the stiffness of 1/64". Buy 3; you will still break one learning feeds and speeds. A 0.6 mm tool (5× stiffness) if building the 600 µm variant. |
| Interface layer | 1 pack | ~$15-20 (3M 468MP adhesive sheet) | ~$30-50 (pre-made PDMS sheet) | ~$50-100 (better PDMS) | For bonding chip layers. 468MP is the Makers-Guide route and works. |
| 3D Printer | 1 | ~$150-300 (FDM) | ~$200-500 (resin: Elegoo Mars, Photon) | $1k+ | Luer ports. Resin preferred for detail/sealing. **A retired FDM printer is also the donor for the Z axes in §2** — do not scrap it. |
| 3D Printer Material | 1 spool/bottle | ~$20-30 (PLA/PETG) | ~$30-50 (standard resin) | $50+ (engineering resin) | For Luer ports. |

---

**2. Fluid Handling / Actuation (hydrostatic, motorised)**

Replaces the compressor + electronic-regulator rig entirely. The operating
point is a bottle 10 cm above the chip; see §2.2 of the plan for why, and
for the Mariotte drift numbers that make the air tube non-optional.

| Item | Quantity | Low Cost Option | Medium Cost Option | High Cost Option | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Mariotte reservoirs | 2 | ~$10-20 (0.5 L HDPE bottles, drilled caps, rigid air tube) | ~$30-60 (lab media bottles + GL45 port caps) | ~$100+ (commercial microfluidic reservoirs) | **Mariotte, not just a raised bottle.** A vented air tube to a fixed depth holds the head constant as the bottle drains. Without it the head falls **14.7 mm/hr (oil) and 4.3 mm/hr (water)** — out of the operating window in 2-4 h, mid-protocol. These need to vent, not seal. |
| Motorised vertical axis | 2 | **~$0-50 (salvaged 3D printer Z axis)** | ~$30-50 each (NEMA17 + T8 leadscrew linear rail) | ~$200+ each (motorised lab jack / linear stage) | This is the actuator **and** the sensor — 0.1 mm ≈ 0.98 Pa, ~250× better than a cheap transducer, with no calibration drift. 200 mm travel covers the whole window several times. Two independent axes: one per phase. |
| Stepper drivers | 2 | ~$2-5 each (A4988 / DRV8825) | ~$10-20 (TMC silent drivers) | — | Or reuse the donor printer's controller board and drive it over serial/G-code. |
| **Flow-resistor tubing** | 2 lengths | ~$10-25 (PTFE, cut to length) | ~$25-50 (PEEK for the water side) | $50+ | **A functional component, not plumbing.** Sized for the 800 µm chip: **oil ≈ 19 cm of 1/16" (1.59 mm) ID**, **water ≈ 20 cm of 0.5 mm ID**. Analytic first cuts — trim on the bench to match measured flow. (600 µm: ~12 cm of 1.0 mm ID oil, ~23 cm of 0.4 mm ID water.) |
| Delivery tubing | ~2-3 m | ~$10-20 (silicone/Tygon) | ~$20-40 (Tygon) | $50+ (PTFE) | Reservoirs to chip. Low compliance matters less than it did under gas pressure, but avoid soft-walled tube on the resistor runs. |
| Fittings/Connectors | Set | ~$10-30 (plastic Luer, barbs, tees) | ~$30-70 (Luer locks) | $70+ (Upchurch-class) | Connects tubing to ports and reservoirs. |

*Not required:* air compressor / N₂ cylinder, electronic pressure controllers,
pressurised reservoirs. Hydrostatic actuation removes all three.

---

**3. Sensing / Observation**

Specs follow the measured 800 µm 3D result
([`mill3d800_2026-08`](../../simulation/openfoam/results/mill3d800_2026-08/)):
**1080 µm slugs at 9.1 Hz moving 33.5 mm/s**.

| Item | Quantity | Low Cost Option | Medium Cost Option | High Cost Option | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Camera | 1 | ~$50 (Raspberry Pi Global Shutter cam, readout cropped to the channel strip) | **~$150-300 (IMX273-class mono USB3, ~226 fps)** | $1k+ (high-speed camera) | **≥140 fps** (15 frames per 110 ms period); 120 fps is marginal. **Mono, not colour** — Bayer costs 3× the light and softens the edges you are measuring. Avoid frame rates that are small-integer multiples of the droplet rate; they sample the same phase each cycle and hide jitter. |
| Lens / Optics | 1 | ~$20-50 (C-mount + extension) | ~$50-150 (C-mount fixed focal) | $200+ (telecentric) | **~0.5×, i.e. de*magnification*** — a 10 × 6 mm field at 5-10 µm/px. The slug is 1080 µm, so this is a macro problem, not a microscopy one. Stop to **f/8-f/11** so depth of field exceeds the 800 µm channel depth. Telecentric optics are the usual metrology reflex but unnecessary here: the chip is planar at fixed working distance. |
| Illumination | 1 | ~$10-30 (LED panel + diffuser, transmitted) | **~$30-80 (LED + MOSFET strobe driver)** | $100+ (controlled backlight) | **Backlit, and strobed if you can.** Exposure must be ≤150-320 µs (the interface moves 33.5 µm per ms). Pulsing the LED 50-100 µs per frame in a dark box makes the flash the shutter — blur is set by pulse width, peak flux can be 20-50× continuous rating (which pays for f/11), and a rolling-shutter sensor becomes usable. |
| Pressure sensors | 0-1 | ~$0 (axis position **is** the measurement) | ~$20-60 (one low-range differential, e.g. 0-2 kPa) | $150+ | At this scale a pressure transducer is the *worse* instrument: an MPX5010 (±2.5% FS) is ±250 Pa — half the water-side operating pressure, against 0.98 Pa for a 0.1 mm axis step. One low-range differential across the chip is useful for confirming the junction behaves; it is not how SET variables get logged. |
| Mounting / Stage | 1 | ~$20-50 (lab stand + clamps, or printed) | ~$50-150 (manual XY stage) | $150+ (damped microscope stage) | Holds chip under the camera; allows focusing. |

---

**4. Control & Data Acquisition**

| Item | Quantity | Low Cost Option | Medium Cost Option | High Cost Option | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Computer | 1 | ~$50-150 (Raspberry Pi 4/5) | **Existing laptop/desktop** | Workstation | Control, logging, video. A Pi can saturate on video throughput — 1440×1080 mono at 200 fps is ~300 MB/s, so crop the ROI or record in bursts during MSR windows. |
| Microcontroller | 1 | ~$5-20 (Pico, ESP32, Arduino) | ~$20-50 (Teensy) | $50+ | Drives the two Z axes, so it is on the critical path for SET commands — not optional. A spare 3D-printer control board doing G-code over serial also works. |
| Interfacing Hardware | Set | ~$20-40 (breadboard, jumpers, PSU) | ~$40-80 (proto board, connectors) | $100+ (custom PCB) | Steppers, endstops, optional sensor, LED strobe gate. |
| Software | - | Free (Python, OpenCV, etc.) | Free | Free | CAD/CAM may have costs unless using free tiers (Fusion 360 Personal). |

---

**5. Consumables & Miscellaneous**

| Item | Quantity | Low Cost Option | Medium Cost Option | High Cost Option | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Water (dispersed) | As needed | ~$1 (distilled + dye) | ~$5 (DI + dye) | ~$5 | Food colouring for visualisation. |
| Oil (continuous) | ~500 mL - 1 L | ~$15-25 | **~$25-45 (50 cSt silicone oil)** | $40+ (fluorinated) | **50 cSt specifically** — that is what every simulation in this repo assumes (µ = 0.048 Pa·s, ρ = 960). A different viscosity moves Ca and therefore the whole operating point. Budget generously: the chip draws ~12.7 µL/s, so a litre is about 22 hours of running. |
| Surfactant | ~5-10 mL | **~$10-20 (Span 80)** | ~$20-40 (higher purity) | $50+ | Crucial for stable droplets. ~2% in the oil. |
| Waste container | 1 | ~$1 (bottle) | ~$5 | ~$5 | Collects outlet fluid. At 16 µL/s combined, a run generates ~58 mL/hour. |
| Cleaning Supplies | As needed | ~$10 (IPA, wipes) | ~$20 (ethanol, lab wipes) | $20+ | Chip and component cleaning. |
| Safety Glasses | 1 | **~$5-10** | ~$10-20 | $20+ | **Essential** (milling). |
| Gloves | Box | **~$10-15 (nitrile)** | ~$15-25 | $25+ | Handling oils and surfactant. |
| Misc. Hardware | Set | ~$10 (tape, fasteners) | ~$20 | $20+ | Assembly and mounting. |

---

**Summary of Estimated Total Costs (very rough):**

* **Low: ~$400 - 900** — hobby CNC, salvaged printer Z axes, Pi GS camera or
  USB microscope, existing PC. Requires real effort and troubleshooting.
* **Medium: ~$1,200 - 2,200 (recommended)** — benchtop CNC, purpose-built
  linear axes, IMX273-class mono camera with a strobed backlight, existing
  PC. Balances cost and usability.
* **High: ~$5,000 - 9,000** — precision desktop CNC, high-speed camera,
  motorised stages, dedicated workstation.

**If the fab chain is already on hand** (CNC, resin printer, a donor FDM
printer), the actual gap is **~$200-600**: bottles, linear hardware,
resistor tubing, and the camera/illumination chain.

**Key cost drivers:**

1. **Camera and illumination** — now the single biggest driver, and the one
   place not to economise. The binding spec is exposure (≤150-320 µs), which
   is a lighting problem before it is a camera problem.
2. **Milling machine** — but far less critical than it was. At 800 µm this
   is "any machine that holds a 0.8 mm tool without chatter", not a
   precision-micromilling requirement.
3. **Everything else is under $200 combined.**
