# Dataset: mf\_tjunction\_test\_v1

[<<< Back to all datasets](https://github.com/juangamella/causal-chamber)

If you use any of the datasets or source code in your work, please consider citing:

```
﻿@article{gamella2025chamber,
  author={Gamella, Juan L. and Peters, Jonas and B{\"u}hlmann, Peter},
  title={Causal chambers as a real-world physical testbed for {AI} methodology},
  journal={Nature Machine Intelligence},
  doi={10.1038/s42256-024-00964-x},
  year={2025},
}
```

## Download

| Link     | MD5 Checksum                     |
|:--------:|:--------------------------------:|
| [ZIP file](TBD) | TBD |

You can also import the dataset directly into your Python code with the [`causalchamber`](https://github.com/juangamella/causal-chamber-package) package. Install it using pip, e.g.

```
pip install causalchamber
```

Then, load the data from any experiment as follows.

```python
from causalchamber.datasets import Dataset

# Download the dataset and store it, e.g., in the current directory
dataset = Dataset('mf_tjunction_test_v1', root='./', download=True)

# Load the data from an experiment (see experiment names below)
experiment = dataset.get_experiment(name='pressure_flow_calibration')
df = experiment.as_pandas_dataframe()
```

See the table [below](#dataset-description) for all the available experiments and their names.

## Dataset Description

| Chamber  | Configuration |
|:--------:|:-------------:|
| Microfluidic T-junction | pressure_driven |

The dataset contains characterization experiments for the microfluidic T-junction causal chamber. These experiments validate the physical relationships between pressure, flow rate, and droplet formation metrics, establishing the ground truth causal structure.

The file [variables.csv](variables.csv) contains a brief description of each variable (column) in the `.csv` files. The table below describes the experiments in the dataset. For a precise description of each experiment protocol, see the corresponding Python script used to generate it.

| Experiment | Generator | Description |
|:----------------------:|:---------:|:------------|
| pressure\_flow\_calibration | [`generators/pressure_flow_calibration.py`](generators/pressure_flow_calibration.py) | Measures the relationship between inlet pressure and volumetric flow rate to validate Hagen-Poiseuille equation and determine channel hydraulic resistance. Flow rates measured by weighing outlet fluid over time. |
| formation\_regimes | [`generators/formation_regimes.py`](generators/formation_regimes.py) | Systematic sweep of (P\_cont, P\_disp) parameter space to map droplet formation regimes (dripping, jetting, co-flow). Records 100 droplets per condition with high-speed video. Used to identify stable operating region and validate COMSOL predictions. |
| frequency\_scaling | [`generators/frequency_scaling.py`](generators/frequency_scaling.py) | Tests the scaling relationship between total flow rate and droplet frequency. Fixes flow rate ratio Q\_disp/Q\_cont while varying total flow. Validates scaling law f ∝ Q\_total. |
| size\_scaling | [`generators/size_scaling.py`](generators/size_scaling.py) | Tests the scaling relationship between flow rate ratio and droplet size. Fixes total flow rate while varying Q\_disp/Q\_cont. Validates Garstecki (2006) scaling law: L/w ∝ (Q\_disp/Q\_cont)^α. |
| sensor\_noise | [`generators/sensor_noise.py`](generators/sensor_noise.py) | Characterizes pressure sensor noise and stability at fixed pressure values. Measures N=1000 samples at constant pressure for each sensor. Determines sensor precision and drift characteristics. |
| camera\_calibration | [`generators/camera_calibration.py`](generators/camera_calibration.py) | Calibrates camera spatial resolution (pixels to micrometers) using precision test target. Validates droplet detection algorithm accuracy using manually annotated ground truth. |
| temperature\_effects | [`generators/temperature_effects.py`](generators/temperature_effects.py) | Measures effect of chip temperature on fluid viscosity and droplet formation. Temperature varied from 20-30°C. Important for accounting for environmental variability. |
| transient\_response | [`generators/transient_response.py`](generators/transient_response.py) | Applies step changes in pressure and measures time to reach steady-state droplet formation. Characterizes system dynamics and time constants for causal discovery time-series studies. |

## Changelog

| Dataset version | Date       | Description                     |
|:---------------:|:----------:|:-------------------------------:|
| v1.0            | TBD | Initial release of the dataset. |

## Compiling the Experiment Protocols

You can generate the experiment protocols by running `make protocols` in a make-capable machine. This will execute the Python scripts in `generators/` and store the resulting protocols in `protocols/`. The file [`generators/requirements.txt`](generators/requirements.txt) contains the dependencies needed to run the scripts.

## Ground Truth Causal Graph

The ground truth causal structure for the microfluidic T-junction in pressure-driven configuration is:

### Configuration 1: Pressure-Driven

**Exogenous variables (actuators):**
- P_cont: Continuous phase pressure
- P_disp: Dispersed phase pressure  
- P_out: Outlet pressure
- Fluid properties (mu_cont, mu_disp, sigma, etc.)
- Geometry (w_main, w_disp, depth)

**Endogenous variables:**
- Q_cont, Q_disp: Flow rates (caused by pressure gradients via Hagen-Poiseuille)
- Junction dynamics: Interface forces, velocity fields
- f_droplet: Formation frequency (caused by flow rates)
- d_droplet, L_droplet, w_droplet: Droplet dimensions (caused by flow rate ratio)
- v_droplet: Droplet velocity (caused by total flow rate and channel geometry)

**Observed variables (sensors):**
- P_cont_meas, P_disp_meas, P_out_meas: Noisy pressure measurements
- f_droplet, d_droplet, etc.: Droplet metrics from image processing

**Key causal relationships:**
```
P_cont → Q_cont → [Junction Physics] → {f_droplet, d_droplet, L_droplet, v_droplet}
P_disp → Q_disp ────────────┘

P_cont → P_cont_meas (sensor noise)
P_disp → P_disp_meas (sensor noise)
P_out → P_out_meas (sensor noise)

Q_cont / Q_disp → d_droplet, L_droplet (flow rate ratio determines size)
(Q_cont + Q_disp) → f_droplet (total flow rate determines frequency)
```

The graph is validated through:
1. Interventional experiments (set pressure, measure flow/droplets)
2. Comparison to COMSOL simulations
3. Consistency with established microfluidics literature (Garstecki 2006, etc.)

## Physics Background

### Hagen-Poiseuille Flow

For laminar flow in rectangular channels:

Q = (ΔP / R_h)

where R_h is hydraulic resistance (depends on geometry and viscosity).

### Droplet Scaling Laws (Garstecki 2006)

In the squeezing regime (low Capillary number):

L/w = 1 + α·(Q_disp/Q_cont)

where α ≈ 1-3 depending on geometry.

### Capillary Number

Ca = (μ·v) / σ

Characterizes relative importance of viscous forces vs. surface tension.
- Ca << 1: Squeezing regime (droplet size controlled by flow rates)
- Ca >> 1: Jetting regime (different physics)

## Licenses

We use different licenses for the datasets and software.

### Dataset License

All images and `.csv` files in the dataset are licensed under a [CC BY 4.0 license](https://creativecommons.org/licenses/by/4.0/). A copy of the license can be found in [LICENSE_DATASETS.txt](LICENSE_DATASETS.txt).

### Software License

All other software, including but not limited to Makefiles and Python scripts, are licensed under the [MIT license](https://opensource.org/license/mit/). A copy of the license can be found in [LICENSE_SOFTWARE.txt](LICENSE_SOFTWARE.txt).

## Contact

For questions about this dataset or the microfluidic causal chamber:
- Open an issue on GitHub
- Email: [your_email@domain.com]

For questions about the broader Causal Chambers project:
- Email: juan@causalchamber.ai

