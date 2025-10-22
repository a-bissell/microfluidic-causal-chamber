# Microfluidic Causal Chamber: T-Junction Design Plan

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

**Geometry:**
- Main channel width: 100-200 μm
- Dispersed phase channel width: 50-100 μm  
- Channel depth: 50-100 μm (uniform)
- Outlet channel: Same as main channel
- Total chip size: ~25mm × 75mm (fits on microscope slide)

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

**Architecture: Pressure-Driven (Recommended for Config 1)**

Why pressure control over syringe pumps?
- More similar to existing wind tunnel design (pressure → flow)
- Creates richer causal dynamics (pressure → resistance → flow)
- Cheaper at medium quality level ($500-1500 per channel vs $2000+ for good pumps)
- Better for perturbation experiments

**Components:**
- Pressure source: Lab air compressor or regulated N₂ cylinder (150-400 kPa range)
- 2× Electronic pressure controllers (continuous and dispersed phases)
  - Range: 0-200 kPa (0-30 psi)
  - Resolution: <0.1 kPa
  - Response time: <100 ms
  - Options: Fluigent, Elveflow (high-end) or DIY Arduino + proportional valves (budget)
- 2× Sealed liquid reservoirs (pressure vessels)
- Low-compliance tubing (PEEK or Teflon, 1/16" OD)
- 3× Pressure sensors (0-200 kPa range, digital output)
  - Honeywell HSC or similar
  - Resolution: <0.1 kPa
  - Located at: continuous inlet, dispersed inlet, outlet

**Alternative: Syringe Pump Control**
- For Configuration 2
- Allows direct control of flow rates (different causal graph)
- More expensive but more deterministic

### 2.3 Observation System

**Primary: High-Speed Camera**
- Resolution: 1280×1024 minimum  
- Frame rate: **>200 fps** (critical for droplet tracking)
- Sensor: CMOS (global shutter preferred)
- Interface: USB3 or GigE
- Recommended: Basler, FLIR, or IDS mid-range industrial camera (~$400-800)

**Optics:**
- 5-10× magnification (to resolve 50-200 μm droplets)
- C-mount lens or microscope objective
- Working distance: >5mm (to fit chip/tubing)

**Illumination:**
- Backlight (transmitted light) - best for droplet edges
- Bright LED panel (~100W equivalent) or ring light
- Diffuser for uniform illumination
- Stable power supply (no flickering)

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

## 4. COMSOL Multiphysics Simulation

### 4.1 Purpose

- **Validate causal model**: Confirm P → Q → droplet relationships
- **Design optimization**: Test channel geometries before fabrication  
- **Ground truth generation**: Create "perfect" data for algorithm benchmarking
- **Parameter exploration**: Identify interesting operating regimes

### 4.2 COMSOL Model Specifications

**Physics Modules:**
1. **Laminar Flow (spf)**
   - Incompressible Navier-Stokes
   - Inlet: Pressure boundary conditions
   - Outlet: Pressure or open boundary
   - Walls: No-slip

2. **Phase Field (pf)** or **Level Set (ls)**
   - Two-phase flow (oil-water interface)
   - Surface tension effects
   - Contact angle at walls
   - Captures droplet formation dynamics

**Geometry:**
- 2D initially (faster, sufficient for T-junction)
- 3D for complex effects (depth variations, 3D droplets)

**Mesh:**
- Fine mesh near junction (<5 μm elements)
- Coarser in far-field
- Boundary layer mesh at walls
- ~50k-500k elements depending on 2D/3D

**Solver:**
- Time-dependent study
- Time steps: 0.01-0.1 ms (capture droplet formation)
- Simulation time: 0.5-2 seconds (5-50 droplet formations)
- Direct or iterative solver (MUMPS, PARDISO)

### 4.3 Simulation Outputs

**Parametric Sweep:**
- Vary P_cont, P_disp systematically
- Extract: droplet frequency, size, formation regime (dripping/jetting)
- Create lookup tables for mechanistic model

**Validation Metrics:**
- Compare to literature correlations (Garstecki 2006, etc.)
- Validate against experimental data once available

**Export:**
- Time series of droplet metrics → CSV (same format as experimental data)
- Videos of simulations for visualization
- Sensitivity analysis: ∂f/∂P_cont, ∂d/∂(Q_disp/Q_cont)

### 4.4 Mechanistic Model Development

Similar to wind tunnel/light tunnel models in appendix IV of the paper:

```python
class MicrofluidicModel:
    """
    Mechanistic model of T-junction droplet generation
    Based on COMSOL simulations and theory
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
        
        # Fitted parameters from COMSOL
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
        """Empirical correlation fitted from COMSOL"""
        Q_total = Q_cont + Q_disp
        Ca = self.capillary_number(Q_cont)
        f = self.alpha_freq * Q_total / self.w_main**2
        return f
    
    def compute_droplet_size(self, Q_cont, Q_disp):
        """Scaling law from literature + COMSOL calibration"""
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
- Vary P_cont from 0-150 kPa, measure Q_cont (by weighing outlet over time)
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
- Compare to Garstecki correlation and COMSOL model

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
        └── comsol_validation/
            ├── model.mph          ← COMSOL model file
            ├── results.csv        ← Simulation outputs
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

# Set all parameters to baseline
SET,P_cont,50000      # 50 kPa
SET,P_disp,30000      # 30 kPa
SET,P_out,0           # Atmospheric
WAIT,5000             # Wait 5 seconds to stabilize

# Sweep dispersed phase pressure
SET,flag,0
SET,P_disp,10000
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

4. **COMSOL Validation:**
   - Compare simulation droplet metrics to experimental
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
   - COMSOL model for teaching microfluidics
   - Dataset for classroom exercises
   - Open-source control software

---

## 9. Development Timeline

### Phase 1: Simulation & Design (Weeks 1-4)

**Week 1-2: COMSOL Model Development**
- [ ] Build 2D T-junction geometry in COMSOL
- [ ] Implement two-phase flow (Phase Field)
- [ ] Run parametric sweep (P_cont, P_disp)
- [ ] Validate against literature (Garstecki 2006)
- [ ] Export simulation results to CSV

**Week 3-4: Hardware Design Finalization**
- [ ] Finalize channel dimensions (based on COMSOL)
- [ ] CAD model of microfluidic chip (Fusion 360)
- [ ] Design 3D printed Luer ports
- [ ] Create shopping list from BOM
- [ ] Order components (long lead time: camera, pressure controllers)

### Phase 2: Fabrication & Assembly (Weeks 5-8)

**Week 5-6: Chip Fabrication**
- [ ] Machine/laser cut PMMA chip
- [ ] 3D print Luer ports
- [ ] Bond chip layers
- [ ] Leak test with DI water

**Week 7-8: System Integration**
- [ ] Assemble fluid handling (reservoirs, tubing, controllers)
- [ ] Set up camera + optics + illumination
- [ ] Integrate pressure sensors
- [ ] Wire electronics, test communication

### Phase 3: Software Development (Weeks 9-12)

**Week 9-10: Control Software**
- [ ] Pressure controller interface
- [ ] Sensor acquisition
- [ ] Protocol interpreter (adapt from wind tunnel)
- [ ] Basic GUI for manual control

**Week 11-12: Image Processing**
- [ ] Droplet detection algorithm
- [ ] Frequency measurement algorithm
- [ ] Real-time visualization
- [ ] Calibration procedure (pixels → μm)

### Phase 4: Characterization (Weeks 13-16)

**Week 13-14: Basic Characterization**
- [ ] Pressure-flow calibration
- [ ] Formation regime mapping
- [ ] Sensor noise characterization
- [ ] Compare to COMSOL predictions

**Week 15-16: Test Experiments**
- [ ] Run test protocols
- [ ] Collect initial dataset (lt_test_v1 equivalent)
- [ ] Debug issues
- [ ] Refine protocols

### Phase 5: Validation & Case Studies (Weeks 17-24)

**Week 17-18: Ground Truth Validation**
- [ ] Randomized control trials
- [ ] Test conditional independencies
- [ ] Finalize causal graph
- [ ] Document in manuscript appendix

**Week 19-22: Case Study Data Collection**
- [ ] Causal discovery datasets
- [ ] OOD datasets (different fluids)
- [ ] Symbolic regression datasets
- [ ] Time-series datasets

**Week 23-24: Analysis & Publication**
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
| **Fluid Handling** | Pressure controllers (2×), compressor, reservoirs, tubing, fittings | $1,500 - 3,000 |
| **Observation** | Machine vision camera, lens, LED illumination, mounting stage | $400 - 1,000 |
| **Sensors** | Pressure sensors (3×) with interface hardware | $300 - 900 |
| **Control/DAQ** | Computer (if needed), microcontroller, cables, proto boards | $100 - 600 |
| **Consumables** | Oils, surfactant, dyes, cleaning supplies, safety gear | $100 - 200 |
| **COMSOL License** | (if not already available) | $0 - 5,000* |

**Total: $4,400 - 9,200** (excluding COMSOL if not available)

*COMSOL: Check if university/institution has license. Student version ~$100. Full license ~$5k.

**Minimum Viable Build: ~$3,000** (using existing computer, DIY pressure control, hobby CNC)

---

## 11. Risk Mitigation

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Chip fabrication fails (leaks, wrong dimensions) | Medium | High | Make multiple chips, have backup fabrication method (e.g., 3D print master), test bonding on scrap first |
| Droplet formation doesn't work (wrong regime) | Medium | Medium | COMSOL simulation first, use literature-validated dimensions, have tunable fluids (glycerol) |
| Pressure controllers too expensive | Low | High | Plan DIY alternative with Arduino + proportional valves, budget for this in Phase 1 |
| Camera frame rate insufficient | Low | Medium | Verify specs before purchase (>200 fps), have manual high-speed camera option (borrow?) |
| Droplet detection algorithm fails | Medium | Medium | Use multiple algorithms (Hough circles, thresholding, ML), manually annotate ground truth |
| Outlet clogging during experiments | Medium | Low | Frequent cleaning protocols, filters on inlets, flush system between experiments |

### Schedule Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Long lead time for components (camera, controllers) | High | Medium | Order components in Phase 1, have backup vendors, check stock before finalizing |
| COMSOL model takes longer than expected | Medium | Low | Start with 2D (faster), use literature params as starting point, this is not blocking |
| Software development delays | Medium | Medium | Reuse wind tunnel code architecture, have modular design (can test hardware without full pipeline) |

---

## 12. Next Steps

### Immediate Actions (This Week)

1. **Review COMSOL tutorials** on two-phase flow (Phase Field interface)
2. **Finalize chip geometry** (channel widths, lengths) based on literature review
3. **Order long-lead items**:
   - Machine vision camera (research Basler, FLIR models)
   - Pressure controllers (get quotes from vendors)
4. **Set up COMSOL** (install, license, run tutorial model)

### Phase 1 Deliverables (Month 1)

1. **COMSOL Model**:
   - Working 2D T-junction simulation
   - Droplet formation in dripping regime
   - Parametric study: f(P_cont, P_disp)
   - Report with simulation results

2. **Hardware Design**:
   - CAD files for chip (Fusion 360 or similar)
   - 3D models for Luer ports
   - Finalized BOM with vendors and prices
   - Circuit diagrams for sensor integration

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

### COMSOL Resources

- COMSOL Application Gallery: "Droplet Formation in a T-Junction"
  - https://www.comsol.com/model/droplet-formation-in-a-t-junction-34591
  
- COMSOL Learning Center: Phase Field Method for Two-Phase Flow
  - Video tutorials, documentation

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
4. **Simulation**: COMSOL support, CFD experts at institution

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

# Parameter sweep
P_cont_values = [20000, 40000, 60000, 80000, 100000]  # Pa (20-100 kPa)
P_disp_values = [10000, 20000, 30000, 40000, 50000]   # Pa (10-50 kPa)

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

**Document Version**: 1.0  
**Date**: 2025-10-22  
**Author**: [Your Name], Microfluidics Engineer  
**Status**: Planning Phase


