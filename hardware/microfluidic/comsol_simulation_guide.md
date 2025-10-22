# COMSOL Multiphysics Simulation Guide: T-Junction Droplet Generation

## Overview

This guide provides step-by-step instructions for building a COMSOL Multiphysics model of the T-junction microfluidic causal chamber. The model will simulate two-phase flow (oil-water) and droplet formation.

**Prerequisites:**
- COMSOL Multiphysics 6.0+ with CFD Module
- Microfluidics Module (recommended but not required)
- ~8GB RAM minimum, 16GB+ recommended
- Basic familiarity with COMSOL interface

---

## Part 1: Geometry Creation

### Step 1: Create New Model

1. Launch COMSOL Multiphysics
2. Model Wizard → 2D → Next
3. Select Physics:
   - **Fluid Flow → Single-Phase Flow → Laminar Flow (spf)**
   - **Mathematics → PDE Interfaces → Phase Field (pf)**
   - Click Finish

### Step 2: Define Parameters

Go to `Global Definitions → Parameters`:

```
Name              Value        Description
w_main            150[um]      Main channel width
w_disp            75[um]       Dispersed phase channel width  
depth             80[um]       Channel depth (3D effect via area calc)
L_main_in         500[um]      Main channel inlet length
L_disp_in         300[um]      Dispersed channel inlet length
L_outlet          1000[um]     Outlet channel length

mu_cont           0.048[Pa*s]  Continuous phase viscosity (50 cSt silicone oil)
rho_cont          960[kg/m^3]  Continuous phase density
mu_disp           0.001[Pa*s]  Dispersed phase viscosity (water)
rho_disp          1000[kg/m^3] Dispersed phase density

sigma             0.03[N/m]    Interfacial tension (oil-water + surfactant)
theta_contact     120[deg]     Contact angle at walls (oil-wet PMMA)

P_cont            50000[Pa]    Continuous phase inlet pressure (50 kPa)
P_disp            30000[Pa]    Dispersed phase inlet pressure (30 kPa)
P_out             0[Pa]        Outlet pressure (atmospheric)

eps_pf            w_main/20    Phase field interface thickness
chi_pf            sigma*w_main Phase field mobility parameter
```

### Step 3: Draw Geometry

Under `Geometry 1`:

**Method A: Using Rectangles (Simplest)**

1. **Main channel inlet:**
   - Insert → Rectangle
   - Width: `w_main`, Height: `L_main_in`
   - Position: (0, 0)
   - Name: `main_inlet`

2. **Dispersed channel:**
   - Insert → Rectangle
   - Width: `w_disp`, Height: `L_disp_in`
   - Position: (w_main/2 - w_disp/2, L_main_in)
   - Name: `disp_inlet`

3. **Junction region:**
   - Insert → Rectangle
   - Width: `w_main`, Height: `w_main` (make it square for smooth junction)
   - Position: (0, L_main_in)
   - Name: `junction`

4. **Outlet channel:**
   - Insert → Rectangle
   - Width: `w_main`, Height: `L_outlet`
   - Position: (0, L_main_in + w_main)
   - Name: `outlet`

5. **Union all:**
   - Select all rectangles
   - Right-click → Boolean Operations → Union
   - Build geometry (click "Build All")

**Method B: Using Bezier/Lines (More flexible)**

See COMSOL documentation for drawing with lines and filleting corners for smooth junctions.

### Step 4: Define Selections (Important!)

Create domain selections for initial conditions:

1. Right-click `Definitions` → Explicit
2. Create selections:
   - `sel_continuous`: Main inlet + junction (where oil starts)
   - `sel_dispersed`: Dispersed inlet (where water starts)

---

## Part 2: Physics Setup

### Laminar Flow (spf)

#### Fluid Properties

1. **Fluid Properties 1**:
   - Domain: All domains
   - Fluid: User defined
   - Density: `(pf.Vf1*rho_cont + pf.Vf2*rho_disp)`  ← Phase field weighted average
   - Dynamic viscosity: `(pf.Vf1*mu_cont + pf.Vf2*mu_disp)`

   This couples the flow to the phase field (Vf1 = volume fraction of phase 1)

#### Boundary Conditions

2. **Inlet - Continuous Phase**:
   - Boundary: Main inlet (bottom)
   - Type: Pressure, No viscous stress
   - Pressure: `P_cont`

3. **Inlet - Dispersed Phase**:
   - Boundary: Dispersed inlet (top of perpendicular channel)
   - Type: Pressure, No viscous stress
   - Pressure: `P_disp`

4. **Outlet**:
   - Boundary: Outlet (top)
   - Type: Pressure, No viscous stress
   - Pressure: `P_out`

5. **Walls**:
   - All other boundaries
   - Type: Wall (No slip) - automatically applied

#### Surface Tension (Critical!)

6. Add: **Laminar Flow → Volume Force**
   - Domain: All
   - Force: Surface tension force from phase field
   - `F = pf.Ftsx` (x-component)
   - `F = pf.Ftsy` (y-component)

This is how the phase field (interface) affects the flow!

### Phase Field (pf)

#### Phase Field Properties

1. **Phase Field Material 1** (Continuous - oil):
   - Density: `rho_cont`
   - Dynamic viscosity: `mu_cont`

2. **Phase Field Material 2** (Dispersed - water):
   - Density: `rho_disp`
   - Dynamic viscosity: `mu_disp`

3. **Phase Field Properties**:
   - Mobility tuning parameter: `chi_pf`
   - Interface thickness: `eps_pf`

#### Phase Field Settings

4. **Phase Field**:
   - Under "Phase Field", set:
     - Mixing energy density: Default (OK)
     - Surface tension coefficient: `sigma`

#### Initial Conditions

5. **Initial Values**:
   - Phase field variable φ: Use conditions to set initial interface
   - Continuous phase domain (sel_continuous): `pf.phase = 1` (phase 1)
   - Dispersed phase domain (sel_dispersed): `pf.phase = -1` (phase 2)

   **Option A: Use Initial Interface feature**
   - Add: Phase Field → Initial Interface
   - Phase 1 domains: sel_continuous
   - Phase 2 domains: sel_dispersed

   **Option B: Manual (advanced)**
   - Under Initial Values, set:
     - φ = `1` for continuous
     - φ = `-1` for dispersed

#### Boundary Conditions

6. **Inlets and Outlet**:
   - Continuous inlet: `pf.phase = 1` (oil)
   - Dispersed inlet: `pf.phase = -1` (water)
   - Outlet: Phase field, Convective flux (default, lets droplets exit)

7. **Walls** (Wetting):
   - Add: Phase Field → Wetting
   - Boundaries: All walls
   - Contact angle: `theta_contact`
   - This sets the wall affinity (oil-wet vs water-wet)

#### Coupling

8. **Velocity field**:
   - Under Phase Field → Convection, set:
     - Velocity field: `u = spf.U` (velocity from Laminar Flow)
   
This couples the phase field to the flow (phase field is advected by flow).

---

## Part 3: Mesh

### Mesh Settings

1. Click **Mesh 1**
2. Set Sequence Type: **Physics-controlled mesh**
3. Element size: **Finer** or **Extra fine**

For better results (but slower):
4. Switch to User-controlled mesh:
   - **Size → Predefined: Finer**
   - Add **Boundary Layer** on walls:
     - Number of layers: 3
     - Stretching factor: 1.2
     - Thickness: 5 μm

5. **Refinement near junction** (important!):
   - Add: **Mesh → Free Triangular**
   - Selection: Junction domain
   - Maximum element size: `w_main/20` (very fine near junction)

6. Build mesh → Check quality
   - Should have ~50k-200k elements for 2D
   - Mesh should be dense near junction, coarser in far-field

---

## Part 4: Study (Time-Dependent)

### Study Setup

1. Add **Study → Time Dependent**

2. **Step 1: Time Dependent**:
   - Times: `range(0, 0.0001, 0.1)` 
     - Start: 0 s
     - Step: 0.0001 s (0.1 ms) - small time steps for stability
     - End: 0.1 s (100 ms) - adjust based on droplet formation time
   
   **Estimating simulation time:**
   - Typical droplet formation: 0.01-0.1 seconds
   - Simulate 5-10 droplet formations: 0.5-1 second total
   - Start small (0.1 s) to test, then extend

3. **Study Settings**:
   - Under Step 1: Time Dependent
   - Click to expand
   - Values of dependent variables: **Use solution from previous time step**

4. **Solver Configurations**:
   - Should auto-configure (Direct solver, MUMPS or PARDISO)
   - For large models, switch to iterative solver (GMRES)

### Physics-Controlled Solver Settings

The default solver should work, but if you have convergence issues:

1. **Study → Solver Configurations → Time Dependent Solver**
2. Time stepping: **Intermediate (default)** or **Strict**
3. **Fully Coupled** (recommended for two-phase flow)

Advanced: If solver fails:
- Reduce time step (0.00001 s)
- Increase max iterations (50+)
- Add ramping to pressure BCs (start from 0, ramp up)

---

## Part 5: Run Simulation

### Initial Run (Quick Test)

1. **Reduce simulation time to 0.01 s** for quick test
2. Click **Compute** (or Study → Compute)
3. Should take 5-30 minutes depending on mesh size

**Monitor progress:**
- Watch Solver Log (bottom panel)
- Check for convergence warnings
- Look for "Time: 0.001 s" etc. progressing

### Visualization (While Running)

1. Right-click **Phase Field (pf)** in Model Builder
2. **Add Plot → Surface**
   - Expression: `pf.Vf2` (volume fraction of water, i.e., droplets)
   - Coloring: Rainbow
   - Range: 0 to 1

3. **Add velocity arrows**:
   - Right-click Surface plot → Arrow Surface
   - Expression: `spf.U`, `spf.V`

4. Click **Plot** to update visualization

### Expected Results

You should see:
- Oil (phase 1) flowing from bottom
- Water (phase 2) flowing from side
- Interface forming at junction
- Droplet "pinching off" after some time
- Droplet flowing downstream in outlet channel

---

## Part 6: Post-Processing & Data Export

### Extract Droplet Metrics

#### Method 1: Isosurface (Interface tracking)

1. **Results → Derived Values → Integration → Line Integration**
   - Selection: Outlet channel centerline
   - Expression: `pf.Vf2` (water volume fraction)
   - Compute
   - This gives volume of water in outlet over time

2. **Count droplets**:
   - Plot `pf.Vf2` along a vertical line in the outlet
   - Count peaks → number of droplets
   - Time between peaks → frequency

#### Method 2: Export to MATLAB/Python

1. **Results → Export → Data**
   - Select Phase Field variable (`pf.Vf2`)
   - Export at all time steps
   - Format: CSV or MATLAB
   - This gives 2D field data at each timestep

2. **Post-process with Python:**

```python
import numpy as np
import pandas as pd
from scipy.signal import find_peaks

# Load COMSOL exported data
# Process to find droplet centers, count, measure size
```

#### Method 3: Probes (Real-time tracking)

1. **Results → Derived Values → Point Evaluation**
   - Define a point in outlet channel (x, y)
   - Expression: `pf.Vf2`
   - Evaluate for all time steps
   - Export to CSV

2. **Analyze time series:**
   - When `pf.Vf2 > 0.5`, a droplet is at that point
   - Count transitions → frequency

### Droplet Size Measurement

1. **At a specific time** (when droplet is fully formed):
   - Results → Derived Values → Surface Integration
   - Selection: Domain where `pf.Vf2 > 0.5` (water phase)
   - Expression: `1` (just area)
   - Compute → This gives droplet area

2. **Calculate diameter:**
   - Assuming circular: `d = 2*sqrt(Area/pi)`
   - For elongated droplet: `L = Area / w_main` (length if droplet spans channel width)

### Export for Causal Chamber Dataset

1. **Parametric sweep results** (see next section)
2. Export table with columns:
   ```
   P_cont, P_disp, f_droplet, d_droplet, L_droplet, Q_cont, Q_disp
   ```
3. Save as `comsol_results.csv`

---

## Part 7: Parametric Sweep

### Setup Parametric Study

To generate the dataset for the mechanistic model:

1. Right-click **Study 1** → **Parametric Sweep**
2. Add **Sweep → P_cont**:
   - Parameter name: `P_cont`
   - Values: `range(20000, 10000, 100000)` (20 kPa to 100 kPa, step 10 kPa)

3. Add **Sweep → P_disp**:
   - Parameter name: `P_disp`
   - Values: `range(10000, 5000, 50000)` (10 kPa to 50 kPa, step 5 kPa)

This creates a grid: 9 × 9 = 81 simulations

**Note:** Each simulation takes ~10-30 min, so 81 simulations = ~14-40 hours total!

**Strategy:**
- Start with coarse sweep (4-5 values each, ~16-25 simulations)
- Run overnight on workstation
- Refine in regions of interest

### Automated Post-Processing

Use COMSOL with MATLAB or Python LiveLink to automate extraction:

**MATLAB Example:**

```matlab
% Load model
model = mphload('tjunction.mph');

% Loop over sweep
results = [];
for i = 1:model.study('std1').getSolverSequences('sol1').getNumSolutions()
    model.result().setIndex('solutionIndex', i-1, 0);
    
    % Extract droplet frequency (count peaks in outlet)
    % ... (custom logic)
    
    results(i,:) = [P_cont(i), P_disp(i), f_droplet, d_droplet];
end

% Save results
csvwrite('comsol_parametric_sweep.csv', results);
```

Alternatively, export all manually after sweep completes.

---

## Part 8: Validation Against Literature

### Compare to Garstecki Scaling Law (2006)

**Expected relationship:**
```
L_droplet / w_main = 1 + α * (Q_disp / Q_cont)
```

Where:
- L_droplet: Droplet length
- w_main: Main channel width
- α ≈ 1-3 (depends on geometry, Ca number)
- Q_disp, Q_cont: Flow rates

**To extract Q from COMSOL:**

1. **Continuous phase flow rate:**
   - Results → Derived Values → Surface Integration
   - Selection: Continuous inlet boundary
   - Expression: `spf.U * depth` (velocity × depth = volumetric flow per unit width)
   - Units: m³/s → convert to μL/min

2. **Dispersed phase flow rate:**
   - Same, but for dispersed inlet

3. **Plot L/w vs Q_disp/Q_cont:**
   - Should be linear in dripping regime
   - Slope α should match literature (~1-3)

### Compare Frequency

**Expected:**
```
f ~ Q_total / w_main²
```

Where Q_total = Q_cont + Q_disp

This is approximate; exact form depends on regime.

---

## Part 9: Troubleshooting

### Simulation Fails / Does Not Converge

**Problem:** Solver fails, "Failed to find a solution"

**Solutions:**
1. **Reduce time step**: Change to `range(0, 0.00001, 0.1)` (smaller steps)
2. **Improve mesh**: Finer mesh near junction
3. **Ramp inlet pressures**: Instead of step change, ramp from 0 to P_cont over first 0.01 s
   - Use `P_cont * min(t/0.01, 1)` in BC
4. **Check phase field parameters**:
   - `eps_pf` should be ~w_main/20 to w_main/10 (not too small!)
   - `chi_pf` should be ~sigma*w_main
5. **Initial conditions**: Make sure oil and water are clearly separated initially

### Droplets Don't Form

**Problem:** Interface deforms but doesn't pinch off

**Possible causes:**
1. **Pressure ratio wrong**: Try higher P_cont or lower P_disp
2. **Surface tension too low**: Increase `sigma` (try 0.03-0.05 N/m)
3. **Viscosity ratio**: Try different mu_cont/mu_disp
4. **Channel geometry**: Dispersed channel might be too wide (try w_disp = w_main/2)
5. **Simulation time too short**: Run longer (0.5-1 second)
6. **Contact angle**: Try different theta_contact (90-150 deg)

### Simulation Very Slow

**Problem:** Takes >1 hour per simulation

**Solutions:**
1. **Coarser mesh**: Reduce elements (but keep junction fine)
2. **Larger time steps**: Increase to 0.0002 s (but watch for instability)
3. **2D only**: Don't do 3D unless necessary (10-100× slower)
4. **Reduce simulation time**: Only simulate 2-3 droplet formations
5. **Use iterative solver**: Study → Solver → Solver Configurations → Suggested Iterative

### Phase Field Smears Out

**Problem:** Interface becomes diffuse, droplets not sharp

**Solutions:**
1. **Reduce interface thickness**: `eps_pf = w_main/30` (smaller)
2. **Finer mesh**: Must resolve interface (need ~3-5 elements across eps_pf)
3. **Adjust mobility**: Decrease `chi_pf` (makes interface stiffer)

---

## Part 10: Advanced Extensions

### 3D Simulation

For more realistic results (but 10-100× slower):

1. Start 2D model, then extrude:
   - Geometry → Extrude
   - Distance: `depth` (80 μm)

2. All boundaries become domains, faces become boundaries

3. Adjust BCs to 3D faces

4. Mesh: Use tetrahedral, boundary layers on all walls

5. Run time: Expect 10× longer than 2D

### Surfactant Transport

To model Marangoni effects (surfactant concentration gradients):

1. Add Physics: Chemical Species Transport (chds)
2. Couple surfactant concentration to surface tension: `sigma = sigma0 * (1 - beta*c)`
3. Requires Microfluidics Module

### Non-Newtonian Fluids

If dispersed phase is shear-thinning (polymer solution):

1. In Fluid Properties, change:
   - Dynamic viscosity → Carreau model or Power Law
   - Requires material parameters (n, lambda, etc.)

---

## Part 11: Deliverables Checklist

For the microfluidic causal chamber project, generate:

- [ ] **Working COMSOL model file** (`tjunction_droplet.mph`)
- [ ] **Parametric sweep results** (`comsol_parametric_sweep.csv`)
  - Columns: P_cont, P_disp, f_droplet, d_droplet, L_droplet, Q_cont, Q_disp, regime
- [ ] **Validation plots**:
  - L/w vs Q_disp/Q_cont (compare to Garstecki)
  - f vs Q_total (frequency scaling)
  - Phase diagram: (P_cont, P_disp) colored by regime (dripping, jetting, etc.)
- [ ] **Videos** (export animations):
  - Droplet formation sequence (5-10 droplets)
  - Different regimes (dripping vs jetting)
  - Save as MP4 or GIF for documentation
- [ ] **Report** (Jupyter notebook or PDF):
  - Model description
  - Validation against literature
  - Comparison to experiments (after hardware built)

---

## Resources

**COMSOL Documentation:**
- Application Library: "Droplet Break-Up in a T-Junction" (model 34591)
- User Guide: CFD Module > Two-Phase Flow > Phase Field Method
- Blog: "Modeling Microfluidics with the Phase Field Method"

**Papers:**
- Garstecki (2006) - T-junction scaling laws
- Derzsi (2013) - COMSOL model of T-junction (good reference!)

**COMSOL Forums:**
- Search for "T-junction", "droplet formation", "phase field"
- Community often helps with convergence issues

---

**Good luck with your simulation!** Feel free to iterate and experiment. Start simple (2D, coarse mesh, short time) and gradually increase complexity.

**Next step:** Open COMSOL and follow Part 1-3 to build your first model. Aim to see at least one droplet form!

