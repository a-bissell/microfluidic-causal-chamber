# OpenFOAM T-Junction Microfluidic Simulation

This directory contains OpenFOAM simulation cases for the microfluidic T-junction causal chamber, providing an open-source alternative to the COMSOL simulation guide.

## Overview

The simulation models two-phase flow (oil-water) droplet generation at a T-junction using:
- **Solver**: `interFoam` (Volume of Fluid method)
- **Physics**: Incompressible Navier-Stokes + VOF interface tracking
- **Surface tension**: Continuum Surface Force (CSF) model

## Directory Structure

```
openfoam/
├── tjunction_2d/           # 2D simulation case (start here)
│   ├── 0/                  # Initial conditions
│   │   ├── U               # Velocity field
│   │   ├── p_rgh           # Pressure
│   │   └── alpha.water     # Phase fraction
│   ├── constant/           # Physical properties
│   │   ├── transportProperties
│   │   ├── turbulenceProperties
│   │   └── g
│   ├── system/             # Solver settings
│   │   ├── blockMeshDict   # Geometry
│   │   ├── controlDict     # Run control
│   │   ├── fvSchemes       # Discretization
│   │   ├── fvSolution      # Linear solvers
│   │   └── setFieldsDict   # Initial interface
│   ├── Allrun              # Run script
│   └── Allclean            # Clean script
│
├── tjunction_2d_serpentine/ # 2D case with inlet resistor channels —
│   │                        # use this for pressure-driven (causal-chamber
│   │                        # actuation) runs; see its README
│   └── gen_blockmesh.py     # parameterized mesh generator
│
├── tjunction_2d_mill/      # digital twin of the millable 400 µm chip
│   │                        # (Makers-Guide PMMA workflow); see its README
│   └── gen_blockmesh.py
│
├── tjunction_3d/           # 3D simulation case
│   └── (same structure with parallel support)
│
├── scripts/                # Python automation
│   ├── extract_droplets.py     # Post-processing
│   ├── run_parametric.py       # Parametric sweeps
│   ├── validate_garstecki.py   # Theory validation
│   └── requirements.txt        # Python dependencies
│
└── README.md               # This file
```

## Quick Start

### Prerequisites

1. **OpenFOAM v2306+** (ESI OpenFOAM or Foundation version)
   - **Linux/Ubuntu**: `sudo apt install openfoam`
   - **Windows**: Use WSL2 (recommended), Docker, or blueCFD-Core
     - See `WINDOWS_SETUP.md` for detailed instructions
   - See: https://www.openfoam.com/download

2. **Python 3.8+** with packages:
   ```bash
   pip install -r scripts/requirements.txt
   ```

3. **ParaView** for visualization:
   ```bash
   sudo apt install paraview    # Linux
   # Windows: Download from https://www.paraview.org/download/
   ```

### Running the 2D Simulation

**Linux / WSL:**
```bash
# Navigate to case directory
cd tjunction_2d

# Make scripts executable
chmod +x Allrun Allclean

# Run the simulation
./Allrun
```

**Windows (with WSL2 installed):**
```powershell
# Navigate to case directory
cd simulation\openfoam\tjunction_2d

# Option 1: Use the batch file
.\Allrun.bat

# Option 2: Run directly through WSL
wsl bash -c "source /opt/openfoam11/etc/bashrc && ./Allrun"
```

This will:
1. Generate the mesh with `blockMesh`
2. Check mesh quality with `checkMesh`
3. Set initial water distribution with `setFields`
4. Run the simulation with `interFoam`
5. Convert results to VTK format

**Expected runtime**: 10-30 minutes (2D), 1-4 hours (3D)

### Viewing Results

```bash
# Open in ParaView
paraview VTK/tjunction_2d.vtk.series

# Or use the OpenFOAM reader
paraFoam
```

In ParaView:
1. Select `alpha.water` to visualize droplets
2. Use "Play" to animate the time series
3. Add velocity vectors with Glyph filter

## Geometry Parameters

From `system/blockMeshDict`:

| Parameter | Value | Description |
|-----------|-------|-------------|
| w_main | 150 μm | Main channel width |
| w_disp | 75 μm | Dispersed channel width |
| depth | 80 μm | Channel depth |
| L_oil | 500 μm | Oil inlet length |
| L_water | 300 μm | Water inlet length |
| L_outlet | 1000 μm | Outlet length |

## Fluid Properties

From `constant/transportProperties`:

| Phase | Property | Value |
|-------|----------|-------|
| Oil (continuous) | ν | 5×10⁻⁵ m²/s (50 cSt) |
| | ρ | 960 kg/m³ |
| Water (dispersed) | ν | 1×10⁻⁶ m²/s |
| | ρ | 1000 kg/m³ |
| Interface | σ | 0.03 N/m |

## Boundary Conditions

From `0/U` and `0/p_rgh` (velocity-driven, the default since the 2026-07 fix):

| Boundary | Condition | Value |
|----------|-----------|-------|
| oil_inlet | fixedValue U | 20 mm/s (Ca = 0.032) |
| water_inlet | fixedValue U | 10 mm/s (Q_disp/Q_cont = 0.25) |
| outlet | fixedValue p | 0 (gauge) |
| walls | noSlip, contact angle | theta0 = 160° (oil-wet) |

> **Why not the original 50/30 kPa pressure inlets?** Over this short
> domain (1.65 mm), 50 kPa drives ~1.2 m/s of oil — a capillary number of
> ~1.9, two orders of magnitude above the droplet-forming regime
> (Ca ≲ 0.02), and the resulting junction pressure (~33 kPa) exceeds the
> 30 kPa water inlet, so water cannot flow in at all. The result is a
> steady stratified film and zero droplets. For pressure-driven runs
> (matching the causal-chamber actuation model), use totalPressure with
> p0 ≈ 850 Pa (oil) and ≈ 650 Pa (water) instead — real chips only see
> tens of kPa because most of it drops across tubing and long serpentine
> channels that this geometry doesn't include.

## Post-Processing

### Extract Droplet Metrics

```bash
python scripts/extract_droplets.py tjunction_2d --output results.csv
```

This extracts:
- Droplet positions and dimensions
- Formation frequency
- Size distribution statistics

### Validate Against Theory

```bash
python scripts/validate_garstecki.py results.csv --plot
```

Compares results to Garstecki scaling law:
```
L/w = 1 + α × (Q_disp/Q_cont)
```

### Parametric Sweep

Preferred: the Docker-based concurrent driver (no local OpenFOAM needed;
runs unchanged on macOS or a many-core Linux/WSL2 box):

```bash
python3 scripts/sweep_pressure.py \
    --base-case tjunction_2d_serpentine \
    --output-dir ~/sweeps/psweep_5x5 \
    --p-cont 10000 11500 13000 14500 16000 \
    --p-disp 2400 2700 3000 3300 3600 \
    --repeats 3 --concurrency 12          # 12 for a 12-core CPU

python3 scripts/analyze_pressure_sweep.py --sweep-dir ~/sweeps/psweep_5x5
```

The analyzer writes per-case metrics, response-map heatmaps, and a
causal-chamber-schema `causal_dataset.csv`. On WSL2, keep `--output-dir`
inside the WSL filesystem (not `/mnt/c/...`) — OpenFOAM's many small
writes are very slow across the Windows bridge; the driver warns if it
detects this.

Legacy sequential driver (requires a local OpenFOAM install):
`scripts/run_parametric.py`.

## Modifying Parameters

### Change Inlet Flow Rates

Edit `0/U`:
```
oil_inlet
{
    type            fixedValue;
    value           uniform (0.02 0 0);   // Keep Ca = mu*U/sigma below ~0.05
}

water_inlet
{
    type            fixedValue;
    value           uniform (0 -0.01 0);  // Sets Q_disp/Q_cont ratio
}
```

For pressure-driven operation, switch both inlets in `0/p_rgh` to
`totalPressure` (see the comments in that file) with p0 of order
100–1000 Pa — **not** tens of kPa; see Boundary Conditions above.

### Change Fluid Properties

Edit `constant/transportProperties`:
```
oil
{
    nu    5e-05;    // Kinematic viscosity (m²/s)
    rho   960;      // Density (kg/m³)
}

sigma   0.03;       // Surface tension (N/m)
```

### Change Simulation Time

Edit `system/controlDict`:
```
endTime         0.1;    // Total simulation time (s)
writeInterval   0.001;  // Output frequency (s)
```

## Troubleshooting

### Simulation Crashes

1. **Reduce time step**: Edit `system/controlDict`:
   ```
   deltaT          1e-8;    // Smaller initial time step
   maxCo           0.3;     // Lower Courant number limit
   ```

2. **Refine mesh near junction**: Add grading in `blockMeshDict`

3. **Check mesh quality**:
   ```bash
   checkMesh -allGeometry -allTopology
   ```

### No Droplets Form

1. **Check the capillary number first**: Ca = mu_cont * U_cont / sigma must
   be ≲ 0.02 (squeezing/dripping regime). Higher Ca means stratified or
   jetting flow — *lowering* velocity/pressure helps, raising it doesn't.
2. **Check the water inlet can actually flow**: with pressure inlets, the
   water p0 must exceed the pressure at the junction (roughly the oil p0
   scaled by the fraction of channel length downstream of the junction),
   or the water phase stalls entirely.
3. **Check contact angle**: walls must be strongly oil-wet — theta0 ≥ 150
   in alpha.water. At theta0 ≤ 120 water spreads as a stable wall film
   instead of necking.
4. **Run longer**: at Ca ~ 0.03 the droplet period is ~0.04 s; `endTime`
   must cover several periods.

### Simulation Too Slow

1. **Use 2D first**: Start with tjunction_2d
2. **Coarser mesh**: Reduce cell count in blockMeshDict
3. **Parallel run** (3D):
   ```bash
   # Decompose
   decomposePar
   # Run on 4 cores
   mpirun -np 4 interFoam -parallel
   # Reconstruct
   reconstructPar
   ```

## Output Data Format

The `extract_droplets.py` script outputs CSV compatible with the causal chamber format:

| Column | Description | Units |
|--------|-------------|-------|
| time | Simulation time | s |
| droplet_id | Droplet identifier | - |
| centroid_x | X position | μm |
| centroid_y | Y position | μm |
| length | Droplet length | μm |
| width | Droplet width | μm |
| d_equivalent | Equivalent diameter | μm |

## References

### Theory
- Garstecki et al. (2006), "Formation of droplets and bubbles in a microfluidic T-junction", Lab Chip
- Christopher & Anna (2007), "Microfluidic methods for generating continuous droplet streams"

### OpenFOAM
- OpenFOAM User Guide: https://www.openfoam.com/documentation/user-guide
- interFoam documentation: https://www.openfoam.com/documentation/guides/latest/doc/guide-applications-solvers-multiphase-interFoam.html

### Causal Chambers
- Gamella et al. (2025), "Causal chambers as a real-world physical testbed for AI methodology", Nature Machine Intelligence
- Microfluidic chamber plan: `hardware/microfluidic/microfluidic_chamber_plan.md`

## Results

- `droplet_verification.png` — filmstrip of the first verified droplet
  formation after the July 2026 BC fix (2D, corrected boundary conditions).
- [`results/mesh_convergence_2026-07/`](results/mesh_convergence_2026-07/) —
  9-point 5 µm vs 7.5 µm check on the serpentine case. Solver-level result
  is solid at every point (droplets form, same regime as 7.5 µm). After a
  follow-up run at 2× endTime, 4 of 9 points have clean, repeatable L/w
  measurements agreeing with the published 7.5 µm data to within 3–19%;
  the other 5 (high total flow) surfaced a genuinely open question — either
  a domain-length-limited clustering artifact or a real regime transition
  at the sweep's highest-flow corner — flagged with a concrete next step.
- [`results/mill_2026-07/`](results/mill_2026-07/) — first solve of the
  millable-chip twin (`tjunction_2d_mill`): reference-point verification
  (droplets within 11–23% of the hydraulic design math) plus a 25-case
  operating-window sweep, L/w and speed perfectly monotonic across the
  whole pressure window. Also fixed a geometry-hardcoding bug in the
  analysis scripts along the way (now parameterized, regression-checked).
- [`results/psweep5x5_2026-07/`](results/psweep5x5_2026-07/) — the first full
  dataset: 75 cases (5×5 grid × 3 noisy repeats), droplets in all of them,
  L/w and speed monotonic across every row and column, median repeat
  CV 2.2%. Includes the causal-chamber-schema `causal_dataset.csv`.
- [`results/protocol_v1_2026-07/`](results/protocol_v1_2026-07/) — first
  time-series (SET/WAIT/MSR-style) dataset: 6 chained runs, each a
  shuffled tour of the same 3×3 grid as `psweep_2026-07`. Cross-checked
  against that independent cold-start pilot: median |ΔL/w| = 0.7%. The
  raw material for changepoint detection / temporal causal discovery.
- [`results/psweep_2026-07/`](results/psweep_2026-07/) — pressure-actuated 3×3
  sweep on the serpentine case: droplets in all 9 cells, monotonic
  L/w and speed response maps (the P → Q → droplet causal mechanism).
- [`results/sweep_2026-07/`](results/sweep_2026-07/) — first parametric
  sweep: 9 velocity-driven cases (all forming droplets, 10–43 Hz) recovering
  the Garstecki scaling law with α = 1.24, R² = 0.94, plus pressure-driven
  pilots mapping the capillary entry-pressure threshold.

## Web Interface

A modern web application is available for controlling simulations through a browser interface.

### Features

- **Parameter Controls**: Easy-to-use sliders for pressure and timing settings
- **Real-time Monitoring**: Live progress updates via WebSocket
- **3D Visualization**: Interactive WebGL droplet viewer
- **Results Dashboard**: Charts for droplet frequency, size distribution, etc.
- **Parametric Sweeps**: Automate multiple simulations across parameter ranges

### Quick Start

```bash
# Navigate to webapp directory
cd webapp

# Start both backend and frontend (Linux/WSL)
chmod +x start_webapp.sh
./start_webapp.sh

# Or on Windows
start_webapp.bat
```

Access the interface at `http://localhost:5173`

See `webapp/README.md` for detailed setup instructions.

## Comparison: OpenFOAM vs COMSOL

| Aspect | OpenFOAM | COMSOL |
|--------|----------|--------|
| Cost | Free (open-source) | ~$5,000+ license |
| Interface method | VOF | Phase Field |
| Ease of use | Command-line, steeper learning | GUI, more intuitive |
| Customization | Full source access | Limited |
| Parallelization | Excellent (MPI) | Good |
| Community | Large, active | Commercial support |

Both approaches are valid for this application. OpenFOAM provides a free, fully open-source solution that can be shared without license restrictions.

## License

This simulation setup is provided under the MIT License as part of the Microfluidic Causal Chamber project.

## Contact

For questions about this simulation:
- Open an issue on GitHub
- See the main project README for contact information

