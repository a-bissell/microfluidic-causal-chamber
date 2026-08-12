# Microfluidic Causal Chamber: T-Junction Design Plan

> **Status (2026-08): the simulation phase described below is done — via
> OpenFOAM, not the COMSOL plan this document originally proposed.** See
> [`simulation/openfoam/`](../../simulation/openfoam/) and especially
> [`results/scaleup_2026-07`](../../simulation/openfoam/results/scaleup_2026-07/)
> and [`results/encoder_dye_2026-08`](../../simulation/openfoam/results/encoder_dye_2026-08/)
> for what's been verified: droplet formation, scale-up to 600–800 µm
> (revising the 100–200 µm geometry originally planned here — see §2.1), and
> a full 3D encoded-droplet result. Sections below have been updated where
> the OpenFOAM work supersedes or corrects the original plan (marked inline);
> the hardware/fluids/software/protocol sections are otherwise still the
> forward plan for the physical build, which has **not yet started**.

## Executive Summary

This document outlines the design, implementation, and validation plan for a **T-junction microfluidic causal chamber** - a droplet generation system with known causal structure for testing AI methodologies in fluid dynamics.

---

## 1. System Overview

### 1.1 Physical Principle: T-Junction Droplet Generation

The T-junction is one of the simplest and most well-characterized microfluidic geometries for droplet generation. It consists of:

- **Continuous Phase Inlet**: Oil flows through the main channel
- **Dispersed Phase Inlet**: Aqueous solution enters perpendicular to main channel  
- **Outlet Channel**: Droplets form and flow downstream

**Physical Phenomena:**
- Droplet formation controlled by pressure balance and interfacial forces
- Formation frequency depends on flow rates (controlled by inlet pressures)
- Droplet size controlled by flow rate ratio
- Well-established theoretical models (dimensionless numbers: Capillary number, Reynolds number)

### 1.2 Causal Structure

#### Configuration 1: Standard (Pressure-Driven)

**Actuators (Exogenous Variables):**
- `P_cont`: Continuous phase pressure (Pa)
- `P_disp`: Dispersed phase pressure (Pa)
- `P_out`: Outlet pressure (Pa) [optional, could be atmospheric]

**Intermediate Variables:**
- `Q_cont`: Continuous phase flow rate (μL/min)
- `Q_disp`: Dispersed phase flow rate (μL/min)
- Fluid velocities at junction
- Interfacial forces at junction

**Sensors (Observed Variables):**
- `P_cont_meas`: Measured continuous phase pressure
- `P_disp_meas`: Measured dispersed phase pressure
- `P_out_meas`: Measured outlet pressure
- `f_droplet`: Droplet formation frequency (Hz)
- `d_droplet`: Droplet diameter (μm)
- `L_droplet`: Droplet length (μm)
- `spacing`: Inter-droplet spacing (μm)
- `v_droplet`: Droplet velocity (mm/s)
- Images: High-speed camera capturing junction

**Ground Truth Causal Graph:**

```
P_cont → Q_cont → [Junction Physics] → Droplet Formation → f_droplet, d_droplet, L_droplet
                           ↑
P_disp → Q_disp -----------┘

All pressures → corresponding P_*_meas (with sensor noise)
```

**Key Causal Relationships:**
1. Pressures cause flow rates (Hagen-Poiseuille for laminar flow)
2. Flow rate ratio determines droplet size
3. Total flow rate influences formation frequency
4. Downstream pressure affects flow resistance

#### Configuration 2: Flow-Rate Controlled

Replace pressure controllers with syringe pumps to directly control flow rates. This changes the causal graph by making Q_cont and Q_disp exogenous instead of P_cont and P_disp.

---

## 2. Hardware Design

### 2.1 Microfluidic Chip Specifications

**Geometry** (revised from the original 100–200 µm plan — see
[scale-up study](../../simulation/openfoam/results/scaleup_2026-07/)):
- Main channel width: **600–800 μm** — 400 µm forms droplets too, but needs a
  fragile 1/64" endmill; 600–800 µm is milling-robust ("anyone with a $500
  mill") and verified to reproduce the same regime (Ca has no length, so
  holding velocity fixed preserves the physics across this range)
- Dispersed phase channel width: same as main channel (cross-merge geometry;
  see [`tjunction_3d_encoder`](../../simulation/openfoam/tjunction_3d_encoder/)
  if building the encoded-droplet variant)
- Channel depth: match width (square cross-section) — the 3D simulation work
  models half-depth with a symmetry plane; full depth wetting (floor vs. lid)
  is unverified and worth checking on the real chip (PMMA vs. adhesive film
  may wet differently)
- Outlet channel: same as main channel
- Total chip size: scale up from ~25mm × 75mm accordingly
- **Contact angle is load-bearing**: the simulation found wall wetting
  determines dripping vs. jetting outright — 120° (a commonly-assumed
  "oil-wet" default) produces a stable wall film with *no* droplets at all;
  160° is what actually drips. If the real chip doesn't drip, check surface
  treatment / PMMA wetting before suspecting geometry or flow rates.

**Material:** PMMA (acrylic) - good for initial prototyping
- Transparent for imaging
- Easy to machine/laser cut
- Compatible with many fluids
- Can be upgraded to PDMS or glass later

**Fabrication Method:**
- Option A: CNC micromilling (recommended - see BOM for Desktop CNC)
- Option B: Laser cutting + layer bonding (faster but limited depth control)
- Option C: 3D printed master → PDMS casting (for future iterations)

**Interface:**
- 3× Luer lock ports (2 inlets, 1 outlet) - 3D printed or commercial
- Bonding: PDMS gasket or adhesive layer (3M 468MP)

### 2.2 Fluid Actuation System

**Architecture: pressure-driven, hydrostatic, motorised.**

Pressure control (rather than syringe pumps) is still the right default, and
for a sharper reason than the original "richer dynamics" argument. The
cyclicity work
([`results/cyclicity_2026-07`](../../simulation/openfoam/results/cyclicity_2026-07/))
showed **the actuation mode decides the causal graph**: with pressure
sources the flow rates are emergent and mutually determined through the
shared junction, so the equilibrium graph contains a cycle; with syringe
pumps Q is imposed, the incoming edges are severed, and the graph is close
to a DAG — a syringe pump acts as a physical do-operator. Both are worth
having. **Actuation mode is an experimental variable, not a procurement
decision.**

**Components:**

- **2× Mariotte bottles** — 0.5 L Nalgene, sealed cap, with a vertical open
  air tube through the cap whose lower end sits at a fixed depth. Delivered
  head is set by the *tube tip* elevation, not the liquid surface, so it
  stays constant as the bottle drains.

  Not a nicety. A plain reservoir's head falls as it empties: at the 800 µm
  flow rates, a 63 mm-diameter bottle drops **14.7 mm/hour on the oil side
  and 4.3 mm/hour on the water side**. Against a 10 cm and 5 cm column that
  is 15% and 9% per hour — enough to walk out of the ±30% droplet-forming
  window (§5.1) in two to four hours, mid-protocol.

- **2× motorised vertical axes** to set the two heads independently. A
  retired 3D printer's Z axis is ideal and free; otherwise a NEMA17 + T8
  leadscrew rail is ~$30–50 each. Travel of 200 mm covers the full window
  several times over.

- **Off-chip flow resistors** — both resistors are off-chip in the v2 design
  (a millable on-chip water resistor would need sub-250 µm features).
  Sized from the simulated operating point via Hagen–Poiseuille,
  R = 128 µL/(πd⁴), after subtracting the ~6 mm of on-chip channel:

  | Phase | needs | first-cut tubing |
  |---|---|---|
  | Oil (50 cSt, µ = 0.048) | 5.7 × 10¹⁰ Pa·s/m³ | **≈ 19 cm of 1/16" ID** |
  | Water (µ = 0.001) | 1.3 × 10¹¹ Pa·s/m³ | **≈ 20 cm of 0.5 mm ID** |

  These are analytic first cuts for the **800 µm** chip; trim on the bench
  to match measured flow. (For 600 µm the equivalents are ~12 cm of 1.0 mm
  ID oil-side and ~23 cm of 0.4 mm ID water-side.) Note the oil resistor is
  short because 50 cSt silicone oil is doing most of the work already — the
  chip itself is 26% of the oil circuit but under 1% of the water circuit,
  which is why the water side needs a deliberate resistor and the oil side
  barely does.

- **Tubing/fittings**: Luer-lock to barb, 1/16" OD PTFE or Tygon.

**Instrumentation: the actuator is the sensor.**

The original plan listed 3× pressure sensors on a 0–200 kPa range. At these
pressures that is worse than useless: an MPX5010-class transducer (0–10 kPa,
±2.5% FS) is **±250 Pa**, which is half the entire water-side operating
pressure. A **0.1 mm step on the Z axis is 0.98 Pa** — about 250× better.

So the manipulated variable and its measurement are the same quantity:
record axis position, and P_cont/P_disp follow from geometry with no
calibration drift. A single low-range differential sensor across the chip is
still worth having to confirm the junction is behaving, but it is not on the
critical path and it is not how the SET variables get logged.

**Alternative: syringe pumps.** Retained for Configuration 2 — see the
cyclicity note above. This is the DAG arm of the experiment, not a fallback.

### 2.3 Observation System

> **Revised 2026-08, same root cause as §2.2.** The specs below originally
> assumed 50–200 µm droplets. At 800 µm the measured slug is **1080 µm**
> moving at **33.5 mm/s** at **9.1 Hz**
> ([`results/mill3d800_2026-08`](../../simulation/openfoam/results/mill3d800_2026-08/)),
> so the optics requirement inverts: you need *de*magnification, not 5–10×.

**Primary: Machine-Vision Camera**
- Resolution: 1280×1024 is ample — the binding constraint is not pixels
- Frame rate: **≥140 fps** (15 frames per 110 ms formation period). 120 fps
  is marginal; 200 fps is comfortable. Avoid small-integer multiples of the
  droplet rate, which sample the same phase every cycle and hide jitter.
- Sensor: mono CMOS (Bayer costs 3× the light and softens the edges you are
  measuring). Global shutter preferred but not required — see illumination.
- Recommended: IMX273-class USB3 (~$150–300), or a Raspberry Pi Global
  Shutter Camera (~$50) with the readout cropped to the channel strip.

**Optics:**
- **~0.5× magnification** for a 10 × 6 mm field of view at 5–10 µm/px —
  *not* 5–10×. A 1440×1080 sensor with 3.45 µm pixels at 0.5× gives
  6.9 µm/px over 10 × 7.5 mm.
- Stop down to **f/8–f/11**: depth of field must exceed the 800 µm channel
  depth, since the interface is a vertical wall spanning it.
- Plain C-mount lens. Telecentric optics are the usual metrology reflex but
  are not needed here — the chip is planar at a fixed working distance.

**Illumination:**
- Backlight (transmitted light) — best for droplet edges
- **Exposure ≤ 150–320 µs.** At 33.5 mm/s the interface moves 33.5 µm per
  millisecond, so this, not frame rate, is the hard constraint — and it is a
  lighting problem, not a camera problem.
- **Strobe the LED for 50–100 µs per frame** in a light-tight enclosure. The
  flash becomes the shutter: blur is set by pulse width, peak flux can be
  20–50× the continuous rating at that duty cycle (which pays for f/11), and
  a rolling-shutter sensor becomes usable if exposure is set to the frame
  period so every row is integrating when the flash fires.
- Diffuser for uniform illumination; stable supply (no mains flicker)

**Mounting:**
- Rigid optical breadboard or microscope stage
- XYZ positioning for chip alignment
- Vibration isolation (rubber feet or isolation pad)

### 2.4 Control & Data Acquisition

**Computer:**
- Laptop/Desktop with:
  - USB3 ports (camera + sensors)
  - Python 3.8+ environment
  - Moderate specs: i5/Ryzen 5, 16GB RAM, SSD storage
  
**Microcontroller (Optional):**
- Arduino Mega or Teensy 4.1
- Handles fast sensor polling if needed
- Serial communication to main PC
- Can use existing wind tunnel Arduino firmware as template

**Software Stack:**
```
┌─────────────────────────────────────┐
│   Experiment Control (Python)      │  ← Protocol interpreter (SET/WAIT/MSR)
├─────────────────────────────────────┤
│   Data Acquisition                  │
│   - Camera: OpenCV/Pylon            │
│   - Sensors: Serial/I2C             │
├─────────────────────────────────────┤
│   Actuator Control                  │
│   - Pressure controllers: Serial/USB│
├─────────────────────────────────────┤
│   Image Processing (Real-time)      │  ← Droplet detection, tracking
│   - OpenCV, scikit-image            │
└─────────────────────────────────────┘
```

---

## 3. Fluids & Consumables

### 3.1 Standard Operating Fluids

**Continuous Phase (Oil):**
- Silicone oil, 10-50 cSt viscosity
- Mineral oil (alternative, cheaper)
- ~100-500 mL sufficient for many experiments

**Dispersed Phase (Aqueous):**
- DI water + food coloring (for visualization)
- Glycerol can be added to tune viscosity
- ~50-200 mL sufficient

**Surfactant (Critical!):**
- Span 80 (for oil continuous phase)
- Concentration: 1-5% w/w in oil
- Prevents droplet coalescence
- Small amount needed (~5-10 mL)

### 3.2 Calibration Standards

- Known viscosity oils (for flow calibration)
- Particle solutions (for velocity calibration)
- Precision syringes (for volume measurements)

---

## 4. Simulation: OpenFOAM (done)

This section originally proposed a COMSOL Multiphysics model. That was never
built. Instead, an open-source OpenFOAM simulation was built and has been
extensively verified over several months — see
[`simulation/openfoam/`](../../simulation/openfoam/) for the cases and
[`results/`](../../simulation/openfoam/results/) for write-ups. No license
needed (`opencfd/openfoam-default` Docker image).

### 4.1 What's built and verified

- **Solver**: `interFoam` (2D/3D VOF, two-phase) and `multiphaseInterFoam`
  (N-phase, used for the encoded-droplet variant). Geometry, meshing and BCs
  are fully scripted (`gen_blockmesh.py`), not hand-built in a GUI.
- **Droplet formation, verified against theory**: the Garstecki (2006) scaling
  law is recovered across a parametric sweep (`results/sweep_2026-07`) —
  9/9 cases formed droplets, L/w = 0.80 + 1.24·q, R² = 0.94.
- **Scale-up, 400 → 800 µm**: same regime reproduced to within a few percent
  across widths (`results/scaleup_2026-07`) — this is what revised the
  channel geometry in §2.1.
- **Mesh convergence**: `results/mesh_convergence_2026-07`.
- **3D fidelity**: 3D droplet formation matches the 2D-verified case on all
  four droplet observables (`results/mill3d800_2026-08`), and a 3D
  encoded-droplet (multi-dye) case ran to a full result
  (`results/encoder_dye_2026-08`) — see the interactive 3D visualization
  tooling there if building the multi-dye encoder variant of this chip.
- **The wall-wetting finding in §2.1** (160°, not the more commonly assumed
  120°) came out of this work and is worth carrying into the real chip.

### 4.2 What OpenFOAM still needs to do for this plan

The parametric sweep, validation against Garstecki, and geometry
finalization that §4.1–4.3 of the original COMSOL plan called for are
**done** (above). What's *not* yet done, and would still be useful before or
alongside fabrication:
- A sweep matched to the exact final chip dimensions and fluid pair chosen
  for the physical build (the existing sweeps use velocity or pressure
  ranges chosen for simulation convenience, not necessarily the real
  actuator's range).
- Export of a lookup table / fitted mechanistic model (§4.3 below) from the
  existing sweep data, if a fast forward model is wanted for real-time
  comparison during bench characterization.

### 4.3 Mechanistic Model Development

Same structure as originally planned, now fit against OpenFOAM sweep data
rather than COMSOL:

```python
class MicrofluidicModel:
    """
    Mechanistic model of T-junction droplet generation.
    Fit against OpenFOAM sweep data (simulation/openfoam/results/sweep_2026-07)
    rather than COMSOL.
    """

    def __init__(self, params):
        # Channel geometry
        self.w_main = params['w_main']  # μm
        self.w_disp = params['w_disp']  # μm
        self.depth = params['depth']     # μm

        # Fluid properties
        self.mu_cont = params['mu_cont']  # Pa·s
        self.mu_disp = params['mu_disp']  # Pa·s
        self.gamma = params['gamma']      # N/m (interfacial tension)

        # Fitted parameters — from the Garstecki fit in results/sweep_2026-07
        # (L/w = 0.80 + 1.24*q); refit against the real chip's sweep once run
        self.alpha_freq = params['alpha_freq']
        self.beta_size = params['beta_size']

    def compute_flow_rates(self, P_cont, P_disp, P_out):
        """Hagen-Poiseuille flow in rectangular channel"""
        R_cont = self.compute_resistance('continuous')
        R_disp = self.compute_resistance('dispersed')

        Q_cont = (P_cont - P_out) / R_cont
        Q_disp = (P_disp - P_out) / R_disp
        return Q_cont, Q_disp

    def compute_droplet_frequency(self, Q_cont, Q_disp):
        """Empirical correlation fitted from the OpenFOAM sweep"""
        Q_total = Q_cont + Q_disp
        Ca = self.capillary_number(Q_cont)
        f = self.alpha_freq * Q_total / self.w_main**2
        return f

    def compute_droplet_size(self, Q_cont, Q_disp):
        """Garstecki scaling law, calibrated against the OpenFOAM sweep"""
        Q_ratio = Q_disp / Q_cont
        d = self.w_main * self.beta_size * Q_ratio**0.3
        return d

    def forward(self, P_cont, P_disp, P_out):
        """Full forward model: pressures → observables"""
        Q_cont, Q_disp = self.compute_flow_rates(P_cont, P_disp, P_out)
        f = self.compute_droplet_frequency(Q_cont, Q_disp)
        d = self.compute_droplet_size(Q_cont, Q_disp)

        # Add sensor noise model
        P_cont_meas = P_cont + np.random.normal(0, self.sigma_pressure)
        # ... etc

        return {
            'P_cont_meas': P_cont_meas,
            'f_droplet': f,
            'd_droplet': d,
            # ...
        }
```

---

## 5. Experimental Protocols

### 5.1 Characterization Experiments

Following the pattern from `wt_test_v1` and `lt_test_v1`:

**Experiment 1: Pressure-Flow Calibration**
- Vary P_cont from 0–2 kPa (0–20 cm H₂O), measure Q_cont (by weighing outlet over time)
- Repeat for P_disp
- Validates Hagen-Poiseuille model
- Measures channel resistance

**Experiment 2: Droplet Formation Regimes**
- Systematic sweep of (P_cont, P_disp) grid
- Identify: dripping, jetting, co-flow regimes
- Measure f, d, L for each condition
- N=100 droplets per condition

**Experiment 3: Frequency Scaling**
- Fix Q_disp/Q_cont, vary total flow rate
- Test scaling law: f ∝ Q_total

**Experiment 4: Size Scaling**
- Fix total flow rate, vary Q_disp/Q_cont
- Test scaling law: d ∝ (Q_disp/Q_cont)^α

**Experiment 5: Sensor Characterization**
- Measure pressure sensor noise at constant pressure
- Measure camera frame rate stability
- Validate droplet detection algorithm accuracy

### 5.2 Case Study Experiments

**Case Study A: Causal Discovery**
- Observational data: Random walks in (P_cont, P_disp) space
- Interventional data: Hold P_cont fixed, vary P_disp (and vice versa)
- Test constraint-based, score-based, and hybrid algorithms
- Expected graph:
  ```
  P_cont → Q_cont → f_droplet, d_droplet, ...
  P_disp → Q_disp ↗
  ```

**Case Study B: Out-of-Distribution Generalization**
- Train ML model on droplet images from one fluid pair
- Test on different viscosity ratio (different glycerol concentration)
- Test on different channel geometry (if multiple chips fabricated)

**Case Study C: Symbolic Regression**
- Rediscover scaling laws from data
- Input: P_cont, P_disp, fluid properties
- Output: f_droplet, d_droplet
- Compare to Garstecki correlation and the OpenFOAM sweep results

**Case Study D: Change Point Detection**
- Steady droplet generation, then sudden pressure change
- Algorithm should detect regime transition
- Could simulate channel clogging (increase outlet resistance)

**Case Study E: Time-Series Causal Discovery**
- Droplet formation is inherently temporal
- Test dynamic causal discovery (e.g., PCMCI from Tigramite)
- Identify time lags: pressure change → flow rate change → frequency change

### 5.3 Dataset Structure

Following existing format:

```
datasets/
  mf_tjunction_v1/
    ├── README.md
    ├── LICENSE_DATASETS.txt
    ├── LICENSE_SOFTWARE.txt
    ├── Makefile
    ├── variables.csv              ← Variable descriptions
    ├── generators/
    │   ├── requirements.txt
    │   ├── pressure_flow_calibration.py
    │   ├── formation_regimes.py
    │   ├── frequency_scaling.py
    │   └── ...
    ├── protocols/
    │   ├── pressure_flow_calibration.txt
    │   └── ...
    ├── data/
    │   ├── pressure_flow_calibration/
    │   │   ├── data.csv           ← Sensor time series
    │   │   └── metadata.yaml
    │   ├── formation_regimes/
    │   │   ├── data.csv
    │   │   ├── images/            ← High-speed camera frames
    │   │   │   ├── frame_0000.png
    │   │   │   ├── frame_0001.png
    │   │   │   └── ...
    │   │   └── metadata.yaml
    │   └── ...
    └── ground_truth/
        ├── graph_config1.yaml     ← Causal graph definition
        ├── scm_params.py          ← Structural equation parameters
        └── openfoam_validation/
            ├── (link or copy of the relevant simulation/openfoam/results/ case)
            ├── droplet_dye.csv    ← Simulation outputs (see existing results/ dirs)
            └── comparison.ipynb   ← Compare sim to experiment
```

---

## 6. Software Development

### 6.1 Control Software

**Main Module: `microfluidic_chamber.py`**

```python
class MicrofluidicChamber:
    """
    Interface to T-junction microfluidic causal chamber
    Similar to WindTunnel and LightTunnel classes
    """
    
    def __init__(self, config):
        self.pressure_controllers = PressureControllerArray(config)
        self.pressure_sensors = PressureSensorArray(config)
        self.camera = HighSpeedCamera(config)
        self.droplet_detector = DropletDetector(config)
        
    def set(self, variable, value):
        """Set actuator value"""
        if variable in ['P_cont', 'P_disp', 'P_out']:
            self.pressure_controllers.set(variable, value)
        else:
            raise ValueError(f"Unknown variable: {variable}")
    
    def measure(self):
        """Take single measurement"""
        # Read pressure sensors
        pressures = self.pressure_sensors.read()
        
        # Capture camera frame
        frame = self.camera.capture()
        
        # Process image for droplet metrics
        droplets = self.droplet_detector.detect(frame)
        
        return {
            'timestamp': time.time(),
            'P_cont_meas': pressures['continuous'],
            'P_disp_meas': pressures['dispersed'],
            'P_out_meas': pressures['outlet'],
            'f_droplet': droplets['frequency'],
            'd_droplet': droplets['mean_diameter'],
            # ...
            'frame': frame,  # Store raw image
        }
    
    def run_protocol(self, protocol_file):
        """Execute experiment protocol"""
        # Parse protocol (SET/WAIT/MSR commands)
        # Similar to existing chamber protocol runners
        pass
```

### 6.2 Image Processing Pipeline

**Droplet Detection Module:**

```python
import cv2
import numpy as np
from scipy import ndimage

class DropletDetector:
    """
    Real-time droplet detection and measurement
    """
    
    def __init__(self, config):
        self.threshold_method = config.get('threshold', 'otsu')
        self.min_area = config.get('min_area', 100)  # pixels
        self.pixels_per_um = config.get('calibration', 1.0)
        
    def detect(self, frame, visualize=False):
        """
        Detect droplets in single frame
        Returns: dict with droplet metrics
        """
        # Preprocessing
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Thresholding (droplets should be darker/brighter than background)
        if self.threshold_method == 'otsu':
            _, binary = cv2.threshold(blurred, 0, 255, 
                                     cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Find contours (droplets)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        # Measure droplets
        droplets = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < self.min_area:
                continue
            
            # Fit ellipse to get major/minor axes
            if len(cnt) >= 5:
                ellipse = cv2.fitEllipse(cnt)
                (x, y), (minor, major), angle = ellipse
                
                droplets.append({
                    'x': x * self.pixels_per_um,
                    'y': y * self.pixels_per_um,
                    'diameter': major * self.pixels_per_um,  # μm
                    'length': major * self.pixels_per_um,    # μm
                    'width': minor * self.pixels_per_um,     # μm
                    'area': area * self.pixels_per_um**2,
                    'angle': angle,
                })
        
        # Aggregate metrics
        if len(droplets) > 0:
            diameters = [d['diameter'] for d in droplets]
            metrics = {
                'n_droplets': len(droplets),
                'mean_diameter': np.mean(diameters),
                'std_diameter': np.std(diameters),
                'droplets': droplets,
            }
        else:
            metrics = {'n_droplets': 0}
        
        if visualize:
            vis_frame = self._draw_droplets(frame, droplets)
            return metrics, vis_frame
        else:
            return metrics
    
    def compute_frequency(self, frames, fps):
        """
        Compute droplet formation frequency from video sequence
        Detects droplets crossing a fixed line in each frame
        """
        # Track droplets crossing detection line over time
        crossings = []
        detection_x = frames[0].shape[1] // 2  # Middle of frame
        
        for frame in frames:
            droplets = self.detect(frame)['droplets']
            # Count droplets near detection line
            # ... (implement crossing detection logic)
        
        # Compute frequency from crossing timestamps
        f_droplet = len(crossings) / (len(frames) / fps)
        return f_droplet
```

### 6.3 Protocol Interpreter

Use existing protocol format from wind tunnel:

```
# Example protocol: formation_regimes.txt

# Set all parameters to baseline (800 um chip -- see 2.2; these are
# hydrostatic heads, so P_cont 980 Pa == a 10.0 cm column)
SET,P_cont,980        # 980 Pa  = 10.0 cm H2O
SET,P_disp,490        # 490 Pa  =  5.0 cm H2O
SET,P_out,0           # Atmospheric
WAIT,5000             # Wait 5 seconds to stabilize

# Sweep dispersed phase pressure across the measured +-30% window
SET,flag,0
SET,P_disp,345        # 3.5 cm H2O
WAIT,3000
MSR,100,50           # 100 measurements, 50ms interval (record video during this)

SET,flag,1
SET,P_disp,20000
WAIT,3000
MSR,100,50

# ... continue sweep
```

---

## 7. Validation Protocol

### 7.1 Causal Graph Validation

Following Appendix V of the original paper:

**Randomized Control Trials:**
- Interventional data: Do(P_cont = p)
- Measure effect on Q_cont, f_droplet, d_droplet
- Verify: Intervening on P_cont affects Q_cont but not Q_disp (independence)
- Verify: Intervening on P_disp affects droplet size but not via P_cont

**Expected Conditional Independencies:**
- P_cont ⊥ P_disp (exogenous)
- P_cont_meas ⊥ P_disp_meas | P_cont, P_disp (measurement noise independent)
- d_droplet ⊥ P_cont | Q_cont, Q_disp (d-separation)

### 7.2 Mechanistic Model Validation

**Quantitative Metrics:**
1. **Flow Rate Prediction:**
   - RMSE between predicted Q and measured Q (from weight)
   - R² for Hagen-Poiseuille model fit

2. **Frequency Prediction:**
   - RMSE between model-predicted f and measured f
   - Percentage error across operating range

3. **Size Prediction:**
   - RMSE between model-predicted d and measured d
   - Comparison to Garstecki correlation (2006)

4. **OpenFOAM Validation:**
   - Compare simulation droplet metrics to experimental (see
     `simulation/openfoam/results/` for the existing simulation baseline)
   - Identify regime boundaries (dripping → jetting)

### 7.3 Comparison to Literature

**Key References for Validation:**
- Garstecki et al. (2006) - Scaling law for droplet formation
- Christopher & Anna (2007) - Microfluidic methods for droplet generation
- Zhu & Wang (2017) - Droplet formation review

---

## 8. Expected Research Contributions

### 8.1 To Causal Chambers Project

1. **New Physical Domain**: First fluid dynamics causal chamber
   - Complements optics (light tunnel) and aerodynamics (wind tunnel)
   - Introduces continuous-time dynamics (droplet formation is cyclic)

2. **Richer Temporal Dynamics**:
   - Droplet formation has intrinsic time scale (~0.01-1 Hz)
   - Tests dynamic causal discovery algorithms
   - Oscillatory/periodic phenomena

3. **Multi-Modal Data**:
   - Time-series sensors (pressure)
   - Video data (droplet images)
   - Derived features (frequency, size from image processing)

4. **Accessible & Low-Cost**:
   - Medium-budget build: ~$3k-5k
   - Smaller footprint than wind/light tunnels
   - No high-voltage, minimal safety concerns

### 8.2 To Microfluidics Community

1. **Benchmark Dataset**:
   - First large-scale, open dataset for droplet generation
   - Multiple operating regimes, fluid pairs, geometries
   - Ground truth causal graph

2. **ML Applications**:
   - Test computer vision for droplet detection
   - Test ML for predicting formation frequency
   - Test symbolic regression for rediscovering physics

3. **Educational Resource**:
   - Open-source OpenFOAM model for teaching microfluidics (no license needed)
   - Dataset for classroom exercises
   - Open-source control software

---

## 9. Development Timeline

The original week-numbered timeline below assumed simulation (Phase 1) as the
first four weeks. That work happened instead as an extended OpenFOAM
investigation (months, not weeks — see §4) that also caught and fixed real
physics issues (contact angle, geometry) a from-literature guess wouldn't
have. Absolute week numbers for the *remaining* phases would just go stale
the same way, so they're given here relative to whenever hardware fabrication
actually starts, not to a fixed calendar.

### Phase 1: Simulation & Design — ✅ Done

- [x] Two-phase VOF model (OpenFOAM `interFoam`), 2D and 3D
- [x] Parametric sweep, validated against Garstecki (2006)
- [x] Channel geometry finalized: 600–800 µm (§2.1), revised from this
      document's original 100–200 µm guess based on a dedicated scale-up study
- [x] Critical finding banked: wall contact angle is load-bearing (160°, not
      120°) — would have caused a real chip to jet a wall film instead of
      dripping, likely read as "wrong regime" rather than "wrong wetting"
- [ ] CAD model of the physical chip (Fusion 360) — not started
- [ ] Design 3D printed Luer ports — not started
- [ ] Order components (long lead time: camera, pressure controllers) — not started

### Phase 2: Fabrication & Assembly (from hardware start, Weeks 1-4)

**Weeks 1-2: Chip Fabrication**
- [ ] Machine/laser cut PMMA chip at 600–800 µm (not the original 100–200 µm)
- [ ] 3D print Luer ports
- [ ] Bond chip layers
- [ ] Leak test with DI water

**Weeks 3-4: System Integration**
- [ ] Assemble fluid handling (reservoirs, tubing, controllers)
- [ ] Set up camera + optics + illumination
- [ ] Integrate pressure sensors
- [ ] Wire electronics, test communication

### Phase 3: Software Development (Weeks 5-8)

**Weeks 5-6: Control Software**
- [ ] Pressure controller interface
- [ ] Sensor acquisition
- [ ] Protocol interpreter (adapt from wind tunnel)
- [ ] Basic GUI for manual control

**Weeks 7-8: Image Processing**
- [ ] Droplet detection algorithm
- [ ] Frequency measurement algorithm
- [ ] Real-time visualization
- [ ] Calibration procedure (pixels → μm)

### Phase 4: Characterization (Weeks 9-12)

**Weeks 9-10: Basic Characterization**
- [ ] Pressure-flow calibration
- [ ] Formation regime mapping
- [ ] Sensor noise characterization
- [ ] Compare bench results to the existing OpenFOAM predictions

**Weeks 11-12: Test Experiments**
- [ ] Run test protocols
- [ ] Collect initial dataset (`mf_tjunction_test_v1`)
- [ ] Debug issues
- [ ] Refine protocols

### Phase 5: Validation & Case Studies (Weeks 13-20)

**Weeks 13-14: Ground Truth Validation**
- [ ] Randomized control trials
- [ ] Test conditional independencies
- [ ] Finalize causal graph
- [ ] Document in manuscript appendix

**Weeks 15-18: Case Study Data Collection**
- [ ] Causal discovery datasets
- [ ] OOD datasets (different fluids)
- [ ] Symbolic regression datasets
- [ ] Time-series datasets

**Weeks 19-20: Analysis & Publication**
- [ ] Run case study algorithms
- [ ] Compare to wind/light tunnel results
- [ ] Write manuscript
- [ ] Prepare code/data release

---

## 10. Budget Estimate

Based on BOM (medium-cost options):

| Category | Items | Cost (USD) |
|----------|-------|------------|
| **Chip Fabrication** | Desktop CNC (Nomad/Bantam), PMMA, end mills, adhesive, 3D printer + resin | $2,000 - 3,500 |
| **Fluid Handling** | 2× Mariotte bottles, 2× motorised Z axes, tubing, fittings | $150 - 350 |
| **Observation** | Machine vision camera, lens, LED illumination, mounting stage | $400 - 1,000 |
| **Sensors** | Optional low-range differential sensor (axis position is the primary measurement — see §2.2) | $0 - 120 |
| **Control/DAQ** | Computer (if needed), microcontroller, cables, proto boards | $100 - 600 |
| **Consumables** | Oils, surfactant, dyes, cleaning supplies, safety gear | $100 - 200 |

**Total: $2,750 - 5,450** — revised 2026-08. Hydrostatic actuation removed
$1,350–2,650 of pressure-control hardware and $300–780 of pressure sensors.

**For this build specifically the gap is ~$200–600**: the CNC, laser, resin
printer and the donor 3D printer are already on hand, so what is actually
missing is the camera-and-illumination chain plus bottle hardware.

*(Simulation is OpenFOAM, which is free/open-source — no license line needed
here anymore; see §4.)*

**Minimum Viable Build: ~$3,000** (using existing computer, DIY pressure control, hobby CNC)

---

## 11. Risk Mitigation

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Chip fabrication fails (leaks, wrong dimensions) | Medium | High | Make multiple chips, have backup fabrication method (e.g., 3D print master), test bonding on scrap first |
| Droplet formation doesn't work (wrong regime) | **Low** *(was Medium — largely de-risked)* | Medium | Dimensions, flow rates and — critically — **wall contact angle (160°, not the more typical 120°)** are now verified in OpenFOAM (§4), not just from literature. If it still doesn't drip on the real chip, suspect surface wetting/treatment first. |
| Pressure controllers too expensive | Low | High | Plan DIY alternative with Arduino + proportional valves, budget for this in Phase 2 |
| Camera frame rate insufficient | Low | Medium | Verify specs before purchase (>200 fps), have manual high-speed camera option (borrow?) |
| Droplet detection algorithm fails | Medium | Medium | Use multiple algorithms (Hough circles, thresholding, ML), manually annotate ground truth |
| Outlet clogging during experiments | Medium | Low | Frequent cleaning protocols, filters on inlets, flush system between experiments |

### Schedule Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Long lead time for components (camera, controllers) | High | Medium | Order components as early as possible in Phase 2, have backup vendors, check stock before finalizing |
| Software development delays | Medium | Medium | Reuse wind tunnel code architecture, have modular design (can test hardware without full pipeline) |

---

## 12. Next Steps

Simulation (the original "Phase 1 / Immediate Actions") is done — see §4.
What's actually next is the physical build:

### Immediate Actions

1. **Finalize chip geometry** for fabrication — start from 600–800 µm (§2.1),
   verified in OpenFOAM; adjust for whatever fluid pair is actually sourced
2. **CAD model of the chip** (Fusion 360 or similar), including Luer ports
3. **Order long-lead items**:
   - Machine vision camera (research Basler, FLIR models)
   - Pressure controllers (get quotes from vendors)
4. **Confirm the wall-wetting plan** for the real chip (§2.1) — PMMA surface
   treatment or adhesive-film choice needs to land near 160° contact angle,
   not the more commonly assumed 120°, or expect a wall film instead of
   droplets

### Phase 2 Deliverables (Fabrication & Assembly)

1. **Hardware Design**:
   - CAD files for chip (Fusion 360 or similar)
   - 3D models for Luer ports
   - Finalized BOM with vendors and prices
   - Circuit diagrams for sensor integration

2. **Fabricated Chip**:
   - Leak-free, milled at the finalized geometry
   - Verified wetting behavior (droplets form, not a wall film)

3. **Initial Software**:
   - Pressure controller communication script
   - Basic camera capture script
   - Protocol file parser (adapt from wind tunnel)

---

## 13. References & Resources

### Key Papers on T-Junction Microfluidics

1. **Garstecki et al. (2006)**: "Formation of droplets and bubbles in a microfluidic T-junction—scaling and mechanism of break-up"
   - Lab on a Chip, 6(3), 437-446
   - **Essential**: Defines scaling law d/w ~ (Q_disp/Q_cont)^α

2. **Christopher & Anna (2007)**: "Microfluidic methods for generating continuous droplet streams"
   - Journal of Physics D: Applied Physics, 40(19), R319
   - Review of droplet generation techniques

3. **Zhu & Wang (2017)**: "Droplet formation in microfluidic cross-junctions"
   - Physics of Fluids, 29(7), 072102
   - Recent review with dimensionless analysis

### Simulation Resources

- [`simulation/openfoam/README.md`](../../simulation/openfoam/README.md) —
  case overview and how to run them
- [OpenFOAM User Guide](https://www.openfoam.com/documentation/user-guide) —
  `interFoam` / VOF two-phase flow

### Causal Inference Background

- Pearl, J. (2009): *Causality: Models, Reasoning, and Inference*
- Peters, J., Janzing, D., & Schölkopf, B. (2017): *Elements of Causal Inference*
- Gamella, Peters, & Bühlmann (2025): Causal Chambers paper (original Nature MI paper)

### Microfluidics Fabrication

- **Soft Lithography**: Whitesides lab protocols (if switching to PDMS)
- **CNC Milling**: Bantam Tools blog on microfluidic chip milling
- **Bonding**: 3M datasheets for adhesive bonding

---

## 14. Contact & Collaboration

For this project, key stakeholders:

1. **Microfluidics Expertise**: (You) - design, fabrication, validation
2. **Causal Inference**: Gamella lab (paper authors) - methodology, comparison to existing chambers
3. **Machine Learning**: Collaborators for case studies - causal discovery, symbolic regression, etc.
4. **Simulation**: OpenFOAM / CFD community (open-source, no institutional license dependency)

Consider reaching out to Juan Gamella (juangamella@gmail.com) to:
- Share this plan and get feedback
- Discuss dataset format compatibility
- Coordinate on adding to causal chamber ecosystem
- Potential collaboration/co-authorship

---

## Appendix A: Variables Definition (variables.csv)

```csv
column_name,latex_name,description
timestamp,,Unix timestamp of measurement (ms precision)
config,,Configuration: "pressure_driven" or "flowrate_driven"
counter,,Measurement counter for error checking
flag,,User-defined experiment flag
intervention,,1 if first measurement after SET, 0 otherwise
P_cont,P_c,Continuous phase pressure setpoint (Pa)
P_disp,P_d,Dispersed phase pressure setpoint (Pa)
P_out,P_o,Outlet pressure setpoint (Pa)
P_cont_meas,\tilde{P}_c,Measured continuous phase pressure (Pa)
P_disp_meas,\tilde{P}_d,Measured dispersed phase pressure (Pa)
P_out_meas,\tilde{P}_o,Measured outlet pressure (Pa)
f_droplet,f,Droplet formation frequency (Hz)
d_droplet,d,Mean droplet diameter (μm)
L_droplet,L,Mean droplet length (μm)
w_droplet,w,Mean droplet width (μm)
spacing,s,Mean inter-droplet spacing (μm)
v_droplet,v,Mean droplet velocity (mm/s)
n_droplets,N,Number of droplets detected in frame
polydispersity,PDI,Coefficient of variation of droplet sizes
regime,,Formation regime: "dripping", "jetting", or "coflow"
camera,,Boolean: was high-speed video captured?
Q_cont_calc,Q_c,Calculated continuous phase flow rate (μL/min)
Q_disp_calc,Q_d,Calculated dispersed phase flow rate (μL/min)
```

---

## Appendix B: Example Generator Script

```python
# generators/formation_regimes.py
"""
Generate protocol for characterizing droplet formation regimes
Systematic sweep of (P_cont, P_disp) parameter space
"""

OUTPUT_DIR = "./protocols"

# Baseline parameters
exogenous_zeros = {
    "P_cont": 0,
    "P_disp": 0,
    "P_out": 0,  # Atmospheric
}

# Parameter sweep -- 5x5 at +-30% about the 800 um reference point.
# The window was measured at 600 um (25/25 cells form droplets at +-30%,
# results/window600_2026-07) and its edges were never reached, so this grid
# sits comfortably inside verified territory. Pa; hydrostatic cm in comments.
P_cont_values = [690, 830, 980, 1130, 1270]   # 7.0  8.5 10.0 11.5 12.9 cm H2O
P_disp_values = [345, 415, 490,  565,  635]   # 3.5  4.2  5.0  5.8  6.5 cm H2O

protocol_name = "formation_regimes.txt"
print(f"Generating {protocol_name}...")

with open(f"{OUTPUT_DIR}/{protocol_name}", "w") as f:
    # Initialize
    for var, val in exogenous_zeros.items():
        print(f"SET,{var},{val}", file=f)
    
    print("WAIT,10000", file=f)  # 10 sec to stabilize
    
    # Sweep parameter space
    for i, P_cont in enumerate(P_cont_values):
        for j, P_disp in enumerate(P_disp_values):
            flag = i * len(P_disp_values) + j
            
            print(f"SET,flag,{flag}", file=f)
            print(f"SET,P_cont,{P_cont}", file=f)
            print(f"SET,P_disp,{P_disp}", file=f)
            print("WAIT,5000", file=f)  # 5 sec to reach steady state
            
            # Measure for 10 seconds at 10 Hz (100 measurements)
            # During MSR, camera records video
            print("MSR,100,100", file=f)  # 100 measurements, 100ms interval
    
    # Return to safe state
    print("SET,P_cont,0", file=f)
    print("SET,P_disp,0", file=f)

print("Protocol generated successfully!")
```

---

**Document Version**: 1.1  
**Original Date**: 2025-10-22 · **Revised**: 2026-08-12 (simulation section
and geometry updated to reflect the completed OpenFOAM work — see the note
at the top of this document)  
**Status**: Simulation phase done (OpenFOAM); physical build not yet started


