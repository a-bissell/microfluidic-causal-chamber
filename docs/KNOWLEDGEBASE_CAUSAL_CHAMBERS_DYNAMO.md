# Knowledgebase: Causal Chambers for Alternative Investment Management

> **Purpose**: This document provides context for AI agents working on integrating causal chambers methodology into Dynamo Software's R&D efforts.
>
> **Audience**: AI agents, ML engineers, research scientists at Dynamo
>
> **Last Updated**: December 2025

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [What Are Causal Chambers?](#what-are-causal-chambers)
3. [Why This Matters for Dynamo](#why-this-matters-for-dynamo)
4. [Technical Deep Dive](#technical-deep-dive)
5. [Integration Opportunities](#integration-opportunities)
6. [Implementation Guide](#implementation-guide)
7. [Key Datasets Reference](#key-datasets-reference)
8. [Glossary](#glossary)
9. [Further Reading](#further-reading)

---

## Executive Summary

**Causal Chambers** are physical testbeds with **known causal ground truth** that enable rigorous validation of AI/ML methodologies. Published in *Nature Machine Intelligence* (2025) by Gamella, Peters, and Bühlmann, they represent a breakthrough in bridging the gap between theoretical causal inference and real-world application.

**For Dynamo**, causal chambers offer:
- A validation framework for ML models before deployment on financial data
- Methodologies for alternative data integration (satellite imagery, ESG)
- Blueprints for building financial simulation environments
- Battle-tested algorithms for regime detection and change-point analysis

**Key Insight**: Financial data lacks ground truth for causal claims. Causal chambers provide that ground truth in physical systems, allowing us to validate methods that can then be applied to finance with confidence.

---

## What Are Causal Chambers?

### Definition

A **causal chamber** is a physical apparatus designed to:

1. **Generate real-world data** from controlled physical processes
2. **Provide known causal structure** (the ground-truth DAG is derivable from physics)
3. **Support interventional experiments** (we can manipulate causes and observe effects)
4. **Enable benchmarking** of causal discovery, representation learning, and other AI methods

### The Three Chambers

| Chamber | Domain | Key Physics | Primary Use Cases |
|---------|--------|-------------|-------------------|
| **Wind Tunnel** | Aerodynamics | Bernoulli's principle, fan dynamics | Time-series analysis, change-point detection |
| **Light Tunnel** | Optics | Malus' law, color mixing | Causal discovery, symbolic regression |
| **Microfluidic** | Fluid dynamics | Hagen-Poiseuille, interfacial tension | Temporal dynamics, multi-modal data (planned) |

### Why Physical Systems?

```
Traditional ML Validation:
    Train on Data A → Test on Data B → Hope it generalizes

Causal Chamber Validation:
    Train on Chamber Data → Compare to KNOWN ground truth → 
    Measure ACTUAL causal accuracy → Deploy with confidence
```

The chambers solve the **fundamental problem of causal validation**: in observational data, we can never know if discovered relationships are causal or spurious. In chambers, we **know the answer**.

---

## Why This Matters for Dynamo

### The Problem with Financial ML

Dynamo's clients (PE funds, hedge funds, institutional investors) increasingly rely on ML for:
- Investor behavior prediction
- Fund flow forecasting  
- Portfolio optimization
- Alternative data analysis
- Risk management

**The challenge**: Financial data is:
- **Observational only** (we can't randomize market interventions)
- **Non-stationary** (regimes change)
- **Confounded** (countless hidden variables)
- **Ground-truth free** (we never know "true" causal structure)

### How Causal Chambers Help

| Financial Challenge | Chamber Solution |
|---------------------|------------------|
| No ground truth for causal claims | Chambers provide known causal graphs |
| Can't validate causal discovery | Test algorithms on chambers first |
| Spurious correlations in backtests | Learn to distinguish correlation from causation |
| Regime changes are opaque | Chambers provide labeled regime changes |
| Alternative data is uninterpretable | Chamber image data has known causal drivers |

### Strategic Value for Dynamo

1. **Differentiation**: "Our AI is validated on physical ground truth" is a defensible claim
2. **Risk Reduction**: Catch model failures before deployment
3. **Research Leadership**: Publish methodology papers, attract talent
4. **Client Trust**: Demonstrate rigorous ML governance

---

## Technical Deep Dive

### Causal Graph Structure

The light tunnel's causal graph (standard configuration):

```
Actuators (Exogenous):
    R, G, B          → RGB LED intensities
    θ₁, θ₂           → Polarizer angles
    L₁₁...L₃₂       → Light source intensities

Sensors (Endogenous):
    I₁, I₂, I₃       → Light sensor readings
    V₁, V₂, V₃       → Voltage measurements
    C_R, C_G, C_B    → Color sensor readings

Causal Relationships:
    R → C_R (direct)
    θ₁ → I₁ (Malus' law: I ∝ cos²(θ₁ - θ₂))
    Multiple confounders and mediators
```

### Intervention Types

The chambers support multiple intervention types critical for causal inference:

| Intervention Type | Chamber Example | Financial Analog |
|-------------------|-----------------|------------------|
| **Hard intervention** | Set LED to fixed value | Fed sets interest rate |
| **Soft intervention** | Shift LED distribution | Policy guidance changes expectations |
| **Observational** | Record without manipulation | Normal market observation |

### Data Modalities

```python
# Tabular time-series (all chambers)
observations = experiment.as_pandas_dataframe()
# Columns: timestamps, actuator values, sensor readings

# Image data (light tunnel camera config)
images = experiment.as_image_array(size='200')
# Shape: (N, 200, 200, 3) RGB images

# Ground truth graphs (all chambers)
from causalchamber.ground_truth import get_graph
true_dag = get_graph('lt_standard')
```

### Key Mathematical Relationships

**Malus' Law** (Light Tunnel):
```
I = I₀ · cos²(θ₁ - θ₂)
```
Where I is transmitted intensity through crossed polarizers.

**Bernoulli's Principle** (Wind Tunnel):
```
P₁ + ½ρv₁² = P₂ + ½ρv₂²
```
Relates pressure and velocity in the airflow.

**Hagen-Poiseuille** (Microfluidic):
```
Q = (πr⁴ΔP) / (8μL)
```
Flow rate Q depends on pressure differential ΔP, channel radius r, fluid viscosity μ, and length L.

---

## Integration Opportunities

### Tier 1: Immediate Implementation (0-3 months)

#### 1.1 ML Validation Pipeline

**Goal**: Establish causal chambers as a mandatory validation step for ML models.

```python
# validation_pipeline.py
from causalchamber.datasets import Dataset
from dynamo.ml.validators import CausalValidator

class ChamberValidation:
    """
    Validate Dynamo ML models against causal chamber ground truth.
    
    Any model claiming causal relationships must pass chamber validation
    before deployment to production.
    """
    
    BENCHMARK_DATASETS = [
        'lt_interventions_standard_v1',  # Causal discovery
        'wt_changepoints_v1',             # Regime detection
        'lt_walks_v1',                    # Time-series
    ]
    
    def __init__(self, model):
        self.model = model
        self.results = {}
    
    def validate_causal_discovery(self):
        """Test if model recovers known causal structure."""
        dataset = Dataset('lt_interventions_standard_v1', download=True)
        
        # Model discovers graph from observational data
        discovered = self.model.discover_graph(
            dataset.get_experiment('uniform_reference').as_pandas_dataframe()
        )
        
        # Compare to ground truth
        true_graph = get_ground_truth('lt_standard')
        
        metrics = {
            'structural_hamming_distance': shd(discovered, true_graph),
            'precision': edge_precision(discovered, true_graph),
            'recall': edge_recall(discovered, true_graph),
            'orientation_accuracy': orientation_accuracy(discovered, true_graph)
        }
        
        self.results['causal_discovery'] = metrics
        return metrics
    
    def validate_intervention_prediction(self):
        """Test if model correctly predicts intervention effects."""
        dataset = Dataset('lt_interventions_standard_v1', download=True)
        
        # Train on observational
        obs_data = dataset.get_experiment('uniform_reference').as_pandas_dataframe()
        self.model.fit(obs_data)
        
        # Predict interventional
        predictions = []
        actuals = []
        
        for intervention in ['red_mid', 'green_mid', 'blue_mid']:
            int_data = dataset.get_experiment(f'uniform_{intervention}').as_pandas_dataframe()
            pred = self.model.predict_intervention(intervention, obs_data)
            predictions.append(pred)
            actuals.append(int_data)
        
        return compute_intervention_metrics(predictions, actuals)
```

**Acceptance Criteria**:
- Structural Hamming Distance < 5 on light tunnel
- Intervention prediction RMSE within 2σ of physical noise floor
- Change-point detection F1 > 0.8 on wind tunnel

#### 1.2 Change-Point Detection Benchmark

**Goal**: Validate regime detection algorithms before deploying to investor behavior monitoring.

```python
# changepoint_benchmark.py
from causalchamber.datasets import Dataset
import numpy as np

def benchmark_changepoint_detector(detector, threshold=0.8):
    """
    Benchmark a change-point detector against wind tunnel ground truth.
    
    The wind tunnel changepoints dataset contains KNOWN regime changes
    (fan speed changes, valve operations) with exact timestamps.
    
    Args:
        detector: Any detector with .detect(timeseries) -> List[int] method
        threshold: Minimum F1 score to pass
    
    Returns:
        dict: Metrics including F1, precision, recall, detection_delay
    """
    dataset = Dataset('wt_changepoints_v1', download=True)
    
    results = []
    for experiment in dataset.experiments:
        df = dataset.get_experiment(experiment).as_pandas_dataframe()
        
        # Ground truth changepoints are in metadata
        true_cps = get_changepoint_labels(experiment)
        
        # Run detector
        detected_cps = detector.detect(df['pressure'].values)
        
        # Score with tolerance window (physical systems have transition periods)
        metrics = score_changepoints(
            detected=detected_cps,
            true=true_cps,
            tolerance_samples=50  # ~0.5 seconds at 100Hz
        )
        results.append(metrics)
    
    aggregate = aggregate_metrics(results)
    
    if aggregate['f1'] < threshold:
        raise ValidationError(
            f"Detector F1 ({aggregate['f1']:.3f}) below threshold ({threshold}). "
            f"Do not deploy to production."
        )
    
    return aggregate
```

### Tier 2: Near-Term R&D (3-12 months)

#### 2.1 Alternative Data Causal Integration

**Goal**: Apply chamber-validated representation learning to satellite imagery and ESG data.

**Methodology Transfer**:

```
Light Tunnel Camera Data          →    Satellite Imagery
─────────────────────────────────────────────────────────
Known causal drivers:                  Unknown causal drivers:
  - LED RGB values                       - Store traffic
  - Polarizer angles                     - Supply chain activity
  - Light source intensity               - Environmental factors

Chamber provides:                      We seek:
  - Ground truth for latent factors      - Causal factors in imagery
  - Validated ICA methods                - Apply validated methods
  - Benchmark scores                     - Confidence in results
```

**Implementation Approach**:

1. Train representation learners on `lt_camera_walks_v1`
2. Validate recovery of known latent factors (RGB, angles)
3. Measure disentanglement metrics against ground truth
4. Apply identical architecture to satellite data
5. Use chamber performance as uncertainty estimate

#### 2.2 Symbolic Regression for Financial Laws

**Goal**: Discover interpretable mathematical relationships in financial data using chamber-validated methods.

The chambers demonstrated symbolic regression recovering physical laws:
- Malus' law: `I = I₀ * cos²(θ)`
- Bernoulli's principle: `P + ½ρv² = constant`

**Financial Application**:

```python
# symbolic_finance.py
from pysr import PySRRegressor

def discover_financial_laws(fund_data, chamber_validated=True):
    """
    Use symbolic regression to discover interpretable relationships.
    
    Method is validated on causal chambers where we KNOW the true
    functional form exists and can be recovered.
    """
    
    if chamber_validated:
        # First validate on chamber data
        chamber_score = validate_on_malus_law()
        if chamber_score < 0.95:
            raise Warning("Symbolic regressor underperforming on known physics")
    
    # Apply to financial data
    model = PySRRegressor(
        niterations=100,
        binary_operators=["+", "-", "*", "/", "^"],
        unary_operators=["exp", "log", "sqrt"],
        constraints={'^': (3, 1)},  # Limit complexity
    )
    
    # Discover relationships
    # e.g., fund_flow ~ f(returns, volatility, peer_flows)
    model.fit(X=fund_data[['returns', 'vol', 'peer_flows']], 
              y=fund_data['fund_flow'])
    
    return model.get_best()
```

### Tier 3: Strategic R&D (12-24 months)

#### 3.1 Synthetic Financial Causal Chamber

**Goal**: Build a simulation environment with known causal structure for strategy validation.

**Design Principles** (from physical chambers):

1. **Explicit Causal Graph**: Define the DAG before generating data
2. **Known Functional Forms**: Specify exact mathematical relationships
3. **Interventional Capability**: Allow manipulation of any variable
4. **Multiple Regimes**: Include regime changes with known timing
5. **Realistic Noise**: Calibrate to real market statistics

```python
# synthetic_chamber.py
import networkx as nx
import numpy as np

class FinancialCausalChamber:
    """
    A synthetic financial environment with KNOWN causal structure.
    
    Inspired by physical causal chambers - we define the ground truth
    so we can rigorously validate any method tested on this data.
    
    Causal Graph:
        macro_sentiment → market_return → fund_return
                       → volatility ────┘
        
        fund_return → lp_satisfaction → redemption_probability
        peer_returns ─────────────────┘
        
        fund_aum + redemptions → next_period_aum
    """
    
    def __init__(self, seed=42):
        self.rng = np.random.default_rng(seed)
        self.dag = self._build_dag()
        self.scm = self._build_scm()  # Structural Causal Model
    
    def _build_dag(self):
        G = nx.DiGraph()
        G.add_edges_from([
            ('macro_sentiment', 'market_return'),
            ('macro_sentiment', 'volatility'),
            ('market_return', 'fund_return'),
            ('volatility', 'fund_return'),
            ('fund_return', 'lp_satisfaction'),
            ('peer_returns', 'lp_satisfaction'),
            ('lp_satisfaction', 'redemption_prob'),
            ('fund_aum', 'next_aum'),
            ('redemption_prob', 'next_aum'),
        ])
        return G
    
    def _build_scm(self):
        """Define the structural equations (KNOWN ground truth)."""
        return {
            'macro_sentiment': lambda n: self.rng.normal(0, 1),
            'market_return': lambda n, macro: 0.05 + 0.3*macro + n*0.15,
            'volatility': lambda n, macro: 0.2 - 0.05*macro + n*0.03,
            'fund_return': lambda n, mkt, vol: 0.8*mkt + n*vol,
            'lp_satisfaction': lambda n, fund_ret, peer: (
                0.5 + 0.3*fund_ret - 0.2*(peer - fund_ret) + n*0.1
            ),
            'redemption_prob': lambda n, sat: (
                np.clip(0.1 - 0.15*sat + n*0.05, 0, 1)
            ),
            # ... etc
        }
    
    def sample_observational(self, n_samples):
        """Generate observational data from the SCM."""
        pass
    
    def sample_interventional(self, intervention, n_samples):
        """Generate data under do(X=x) intervention."""
        pass
    
    def get_ground_truth_dag(self):
        """Return the true causal graph for validation."""
        return self.dag.copy()
    
    def get_ground_truth_effects(self, cause, effect):
        """Return true causal effect size for validation."""
        pass
```

#### 3.2 Microfluidic Capital Flow Analog (Experimental)

**Goal**: Explore physical analog computing for fund flow dynamics.

**Conceptual Mapping**:

| Microfluidic System | Financial System |
|---------------------|------------------|
| Pressure differential | Expected return differential |
| Flow rate | Capital flow rate |
| Viscosity | Market friction / illiquidity |
| Channel diameter | Fund capacity |
| Droplet formation | Discrete investment tranches |
| T-junction | Fund-of-funds allocation point |

**Research Questions**:
1. Do capital flows exhibit dynamics analogous to fluid mechanics?
2. Can physical intuition from microfluidics inform financial modeling?
3. Could an actual physical system serve as an analog computer?

**This is speculative R&D** but aligns with Dynamo's innovation brand and could yield breakthrough insights.

---

## Implementation Guide

### Getting Started

#### Prerequisites

```bash
# Install causal chamber package
pip install causalchamber

# Install dependencies for analysis
pip install pandas numpy networkx matplotlib
pip install causal-learn  # Causal discovery
pip install pysr  # Symbolic regression
```

#### First Experiment

```python
from causalchamber.datasets import Dataset

# Download a dataset
dataset = Dataset('lt_interventions_standard_v1', root='./data/', download=True)

# List available experiments
print(dataset.experiments)

# Load observational data
obs = dataset.get_experiment('uniform_reference')
df = obs.as_pandas_dataframe()

print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(df.describe())
```

### Recommended Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    DYNAMO ML DEVELOPMENT WORKFLOW                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. HYPOTHESIS                                                   │
│     └── Define causal claim (e.g., "X causes Y in fund data")   │
│                                                                  │
│  2. CHAMBER VALIDATION                                           │
│     ├── Select analogous chamber dataset                        │
│     ├── Implement method on chamber data                        │
│     ├── Compare to ground truth                                 │
│     └── MUST PASS: SHD < 5, F1 > 0.8                           │
│                                                                  │
│  3. FINANCIAL APPLICATION                                        │
│     ├── Apply validated method to Dynamo data                   │
│     ├── Interpret results with chamber calibration              │
│     └── Document uncertainty based on chamber performance       │
│                                                                  │
│  4. DEPLOYMENT                                                   │
│     ├── Include chamber benchmark scores in model card          │
│     ├── Set up monitoring for distribution shift                │
│     └── Re-validate quarterly on new chamber releases           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Code Organization

Recommended structure for Dynamo's causal ML codebase:

```
dynamo-causal-ml/
├── benchmarks/
│   ├── chamber_validation.py      # Core validation logic
│   ├── test_causal_discovery.py   # CD algorithm tests
│   ├── test_changepoint.py        # CPD algorithm tests
│   └── test_representation.py     # ICA/VAE tests
│
├── methods/
│   ├── causal_discovery/
│   │   ├── pc_algorithm.py
│   │   ├── fci_algorithm.py
│   │   └── notears.py
│   ├── changepoint/
│   │   ├── bocpd.py
│   │   └── prophet.py
│   └── representation/
│       ├── ica.py
│       └── causal_vae.py
│
├── applications/
│   ├── investor_behavior.py       # LP prediction models
│   ├── fund_flow.py               # Flow forecasting
│   ├── regime_detection.py        # Market regime models
│   └── alt_data_integration.py    # Satellite, ESG, etc.
│
├── data/
│   ├── chambers/                  # Downloaded chamber datasets
│   └── dynamo/                    # Internal financial data
│
└── configs/
    ├── validation_thresholds.yaml # Acceptance criteria
    └── model_registry.yaml        # Deployed model versions
```

---

## Key Datasets Reference

### For Causal Discovery

| Dataset | Use Case | Key Features |
|---------|----------|--------------|
| `lt_interventions_standard_v1` | **Primary benchmark** | Interventional data, known DAG, multiple intervention strengths |
| `lt_validate_v1` | Validation | Randomized experiments for DAG validation |
| `wt_validate_v1` | Cross-domain | Wind tunnel equivalent |

### For Time-Series / Regime Detection

| Dataset | Use Case | Key Features |
|---------|----------|--------------|
| `wt_changepoints_v1` | **Change-point detection** | Labeled regime changes, exact timestamps |
| `wt_walks_v1` | Time-series forecasting | Random walks, deterministic patterns |
| `lt_walks_v1` | Multi-variate time-series | Light tunnel actuator walks |

### For Representation Learning

| Dataset | Use Case | Key Features |
|---------|----------|--------------|
| `lt_camera_walks_v1` | **ICA / Disentanglement** | Image data with known latent factors |
| `lt_camera_v1` | Causal representation | Multiple SCM configurations |
| `lt_color_regression_v1` | OOD generalization | Distribution shift experiments |

### For Symbolic Regression

| Dataset | Use Case | Key Features |
|---------|----------|--------------|
| `lt_malus_v1` | **Equation discovery** | Malus' law (I = I₀cos²θ) |
| `wt_bernoulli_v1` | Physics discovery | Bernoulli's principle |

---

## Glossary

| Term | Definition |
|------|------------|
| **Causal Discovery** | Algorithms that learn causal graph structure from data |
| **DAG** | Directed Acyclic Graph - represents causal relationships |
| **Do-calculus** | Mathematical framework for reasoning about interventions |
| **Ground Truth** | The known correct answer (available in chambers, not in finance) |
| **Intervention** | Manipulating a variable to observe downstream effects |
| **ICA** | Independent Component Analysis - recovers latent sources |
| **SCM** | Structural Causal Model - defines causal mechanisms |
| **SHD** | Structural Hamming Distance - measures graph similarity |

---

## Further Reading

### Essential Papers

1. **Gamella, Peters, Bühlmann (2025)**. "Causal chambers as a real-world physical testbed for AI methodology." *Nature Machine Intelligence*.
   - The foundational paper. Read this first.
   - DOI: 10.1038/s42256-024-00964-x

2. **Peters, Janzing, Schölkopf (2017)**. "Elements of Causal Inference."
   - Comprehensive textbook on causal inference
   - Free PDF: https://mitpress.mit.edu/books/elements-causal-inference

3. **Pearl (2009)**. "Causality: Models, Reasoning, and Inference."
   - The foundational text on causal inference

### Domain-Specific

4. **Microfluidics**: Garstecki et al. (2006). "Formation of droplets and bubbles in a microfluidic T-junction."
   
5. **Financial Causality**: Peters et al. (2013). "Causal Discovery with Continuous Additive Noise Models."

### Code Resources

- **Causal Chamber Package**: https://github.com/juangamella/causal-chamber-package
- **Paper Repository**: https://github.com/juangamella/causal-chamber-paper
- **Causal Discovery Toolbox**: https://github.com/FenTechSolutions/CausalDiscoveryToolbox

---

## Appendix: Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│               CAUSAL CHAMBERS QUICK REFERENCE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  INSTALL:     pip install causalchamber                         │
│                                                                  │
│  LOAD DATA:   from causalchamber.datasets import Dataset        │
│               ds = Dataset('lt_interventions_standard_v1',       │
│                           root='./', download=True)             │
│               df = ds.get_experiment('uniform_reference')        │
│                     .as_pandas_dataframe()                      │
│                                                                  │
│  GROUND TRUTH: from causalchamber.ground_truth import get_graph │
│                true_dag = get_graph('lt_standard')              │
│                                                                  │
│  KEY DATASETS:                                                   │
│    • Causal Discovery: lt_interventions_standard_v1             │
│    • Change Points:    wt_changepoints_v1                       │
│    • Images/ICA:       lt_camera_walks_v1                       │
│    • Symbolic Reg:     lt_malus_v1, wt_bernoulli_v1             │
│                                                                  │
│  VALIDATION THRESHOLDS (Dynamo Standard):                        │
│    • SHD < 5 on light tunnel DAG                                │
│    • F1 > 0.8 on change-point detection                         │
│    • R² > 0.95 on known physical laws                           │
│                                                                  │
│  SUPPORT:     juangamella@gmail.com (original authors)          │
│               dynamo-ml-team@dynamosoftware.com (internal)      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Dec 2025 | AI Agent | Initial creation |

---

*This document is part of Dynamo's AI/ML Knowledge Base. For questions or updates, contact the ML Platform team.*
