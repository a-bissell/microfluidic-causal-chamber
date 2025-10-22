# Microfluidic Causal Chamber

![T-Junction Schematic](https://via.placeholder.com/800x300.png?text=T-Junction+Microfluidic+Droplet+Generator)

This directory contains the complete design, simulation, and implementation plan for the **microfluidic causal chamber** - a T-junction droplet generator with known causal structure for testing AI methodologies.

---

## 📋 Documentation Overview

| Document | Purpose | Length | When to Read |
|----------|---------|--------|--------------|
| **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** | Executive summary, vision, contributions | 8 pages | **Start here** - High-level overview |
| **[QUICKSTART.md](QUICKSTART.md)** | Week-by-week action plan | 5 pages | **Next** - Practical getting started |
| **[microfluidic_chamber_plan.md](microfluidic_chamber_plan.md)** | Comprehensive technical plan | 30 pages | Reference - Detailed design |
| **[comsol_simulation_guide.md](comsol_simulation_guide.md)** | Step-by-step COMSOL tutorial | 20 pages | Week 1-2 - Build simulation |
| **[chip_bom.md](chip_bom.md)** | Bill of materials with costs | 3 pages | Week 1 - Order components |
| **[REFERENCES.md](REFERENCES.md)** | Bibliography & further reading | 5 pages | As needed - Citations |

---

## 🚀 Quick Start (30 seconds)

**New to the project?** Read in this order:

1. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** (10 min) - Understand the vision
2. **[QUICKSTART.md](QUICKSTART.md)** (10 min) - See the Week 1 tasks
3. **[chip_bom.md](chip_bom.md)** (5 min) - Check budget and start ordering

**Ready to simulate?**  
→ **[comsol_simulation_guide.md](comsol_simulation_guide.md)** - Build your first COMSOL model

**Need detailed specs?**  
→ **[microfluidic_chamber_plan.md](microfluidic_chamber_plan.md)** - Hardware, software, protocols

---

## 🎯 Project Goals

1. **Extend Causal Chambers** to fluid dynamics domain
2. **Build working T-junction** droplet generator
3. **Validate causal structure** through experiments
4. **Create open datasets** for AI research
5. **Compare to COMSOL** simulations

**Timeline**: ~6 months from start to publication-ready  
**Budget**: $4k-9k (medium-cost options)

---

## 📊 System Overview

### Physical System

```
                    Water + Dye
                         ↓
    Oil + Surfactant → ╪══════> Droplets
                         
    Actuators:           Sensors:
    - P_cont (pressure)  - Pressure sensors (3×)
    - P_disp (pressure)  - High-speed camera (>200 fps)
    - P_out (pressure)
```

### Causal Graph

```
P_cont → Q_cont → Junction → f_droplet, d_droplet, L_droplet
P_disp → Q_disp ────┘

(Pressures cause flow rates via Hagen-Poiseuille,
 flow rates cause droplet metrics via interfacial physics)
```

### Hardware Components

- **Chip**: PMMA, 150 μm channels, milled or laser cut
- **Actuation**: Electronic pressure controllers (2×)
- **Observation**: Machine vision camera (>200 fps)
- **Sensing**: Digital pressure sensors (3×)
- **Control**: Python + Arduino/PC

---

## 📁 Related Directories

### Dataset Template

```
../../datasets/mf_tjunction_test_v1/
├── README.md               ← Dataset description
├── variables.csv           ← Variable definitions
├── Makefile                ← Generate protocols
├── generators/
│   └── pressure_flow_calibration.py  ← Example experiment
└── protocols/              ← Generated experiment protocols
```

**Usage:**
```bash
cd ../../datasets/mf_tjunction_test_v1/
make protocols   # Generate all .txt protocol files
```

### Paper Analysis (Example)

```
../../causal-chamber-paper/case_studies/
├── causal_discovery_iid.ipynb    ← Example analysis notebook
├── mechanistic_models.ipynb      ← Mechanistic model examples
└── src/                          ← Shared code (reusable)
```

---

## 🛠️ Development Phases

### ✅ Phase 0: Planning (This Document)
- [x] Literature review
- [x] System design
- [x] Documentation
- [x] BOM creation

### 🔄 Phase 1: Simulation (Weeks 1-4)
- [ ] COMSOL model (2D T-junction)
- [ ] Parametric sweep
- [ ] Order components

### ⏳ Phase 2: Fabrication (Weeks 5-8)
- [ ] Mill chip
- [ ] Assemble fluid handling
- [ ] Integrate sensors/camera

### ⏳ Phase 3: Software (Weeks 9-12)
- [ ] Control software
- [ ] Image processing
- [ ] Protocol interpreter

### ⏳ Phase 4: Characterization (Weeks 13-16)
- [ ] Calibration experiments
- [ ] Validate causal graph
- [ ] Compare to COMSOL

### ⏳ Phase 5: Datasets & Publication (Weeks 17-24)
- [ ] Case study experiments
- [ ] Dataset release
- [ ] Manuscript preparation

---

## 💡 Key Features

### Why This is a Good Causal Chamber

1. **Known Ground Truth**: Physics-based causal graph (P → Q → droplets)
2. **Controllable**: Direct actuation of pressures (exogenous variables)
3. **Observable**: Rich sensor data (pressure, video)
4. **Validated**: Compare to 20+ years of microfluidics literature
5. **Accessible**: Medium budget, safe operation, small footprint

### What Makes This Novel

1. **First fluid dynamics causal chamber** (complements optics/aerodynamics)
2. **Intrinsic temporal dynamics** (periodic droplet formation)
3. **Multi-modal data** (time-series + video)
4. **Open COMSOL model** for simulation benchmarking

---

## 📖 Background Reading

### Essential (Read First)

1. **Gamella et al. (2025)**: Causal Chambers paper (Nature MI)  
   → Defines causal chamber concept

2. **Garstecki et al. (2006)**: T-junction scaling laws (Lab Chip)  
   → Key physics for droplet size prediction

3. **Peters et al. (2017)**: Elements of Causal Inference  
   → Causal discovery methods

### Recommended

- **Christopher & Anna (2007)**: Microfluidic droplet review
- **Bruus (2008)**: Theoretical Microfluidics textbook
- COMSOL Application Gallery: "Droplet Formation in a T-Junction"

**Full bibliography**: [REFERENCES.md](REFERENCES.md)

---

## 🤝 Contributing

This is an **open project** following the Causal Chambers philosophy:

- **Hardware**: CC BY 4.0 (schematics, CAD files)
- **Software**: MIT License (control code, analysis scripts)
- **Datasets**: CC BY 4.0 (CSV files, images)

**Want to help?**
- Build your own version (report back!)
- Improve documentation
- Contribute datasets with different geometries/fluids
- Add analysis notebooks

---

## 📞 Contact

**Project Lead**: [Your Name]  
**Email**: [your_email@domain.com]  
**Institution**: [Your Institution]

**Causal Chambers Team**:  
Juan L. Gamella: juan@causalchamber.ai  
Website: https://causalchamber.org  
GitHub: https://github.com/juangamella/causal-chamber

---

## 🙏 Acknowledgments

This project builds on:
- **Causal Chambers** (Gamella, Peters, Bühlmann)
- **Microfluidics community** (Garstecki, Whitesides, Stone, Anna, and many others)
- **Causal inference community** (Pearl, Peters, Schölkopf, Runge, and colleagues)

---

## 📝 Citation

If you use this design:

```bibtex
@misc{microfluidic_chamber_2025,
  author={[Your Name]},
  title={Microfluidic Causal Chamber: T-Junction Design},
  year={2025},
  howpublished={GitHub Repository},
  url={[your_github_url]}
}
```

And please cite the original Causal Chambers paper:

```bibtex
@article{gamella2025chamber,
  author={Gamella, Juan L. and Peters, Jonas and B{\"u}hlmann, Peter},
  title={Causal chambers as a real-world physical testbed for {AI} methodology},
  journal={Nature Machine Intelligence},
  doi={10.1038/s42256-024-00964-x},
  year={2025}
}
```

---

## 🔗 Quick Links

| Resource | Link |
|----------|------|
| **Main Repository** | [Causal Chambers GitHub](https://github.com/juangamella/causal-chamber) |
| **Python Package** | [causalchamber PyPI](https://pypi.org/project/causalchamber/) |
| **Original Paper** | [Nature MI](https://www.nature.com/articles/s42256-024-00964-x) |
| **COMSOL Models** | [Application Gallery](https://www.comsol.com/models) |
| **Microfluidics Resources** | [Elveflow](https://www.elveflow.com/microfluidic-reviews/) |

---

**Ready to start?** Open [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) and [QUICKSTART.md](QUICKSTART.md)!

**Questions?** Check [REFERENCES.md](REFERENCES.md) or reach out to the contacts above.

---

*Last updated: October 22, 2025*  
*Version: 1.0 (Planning Phase)*

