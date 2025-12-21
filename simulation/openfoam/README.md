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

From `0/p_rgh`:

| Boundary | Pressure | Type |
|----------|----------|------|
| oil_inlet | 50 kPa | totalPressure |
| water_inlet | 30 kPa | totalPressure |
| outlet | 0 (gauge) | fixedValue |
| walls | - | fixedFluxPressure |

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

```bash
python scripts/run_parametric.py \
    --base-case tjunction_2d \
    --output-dir parametric_results \
    --p-cont 20000 40000 60000 80000 100000 \
    --p-disp 10000 20000 30000 40000 50000
```

This generates 25 cases (5×5 grid) with different pressure combinations.

## Modifying Parameters

### Change Inlet Pressures

Edit `0/p_rgh`:
```
oil_inlet
{
    type            totalPressure;
    p0              uniform 50000;  // Change this value (Pa)
}

water_inlet
{
    type            totalPressure;
    p0              uniform 30000;  // Change this value (Pa)
}
```

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

1. **Increase pressure difference**: Try P_oil=60kPa, P_water=40kPa
2. **Run longer**: Increase `endTime` in controlDict
3. **Check contact angle**: Try theta0=90 or theta0=150 in alpha.water

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

