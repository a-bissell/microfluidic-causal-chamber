# References & Further Reading

## Causal Chambers

### Primary Paper
1. **Gamella, J. L., Peters, J., & Bühlmann, P. (2025)**  
   *Causal chambers as a real-world physical testbed for AI methodology*  
   Nature Machine Intelligence.  
   DOI: [10.1038/s42256-024-00964-x](https://doi.org/10.1038/s42256-024-00964-x)  
   **Essential**: Defines the causal chamber concept, describes wind and light tunnels.

### Related Work
2. **Gamella, J. L. & Runge, J. (2025)**  
   *Sanity Checking Causal Representation Learning on a Simple Real-World System*  
   Preprint.  
   **Relevant**: Uses light tunnel for CRL benchmark.

---

## Microfluidic Droplet Generation

### T-Junction Fundamentals
3. **Garstecki, P., Fuerstman, M. J., Stone, H. A., & Whitesides, G. M. (2006)**  
   *Formation of droplets and bubbles in a microfluidic T-junction—scaling and mechanism of break-up*  
   Lab on a Chip, 6(3), 437-446.  
   DOI: [10.1039/B510841A](https://doi.org/10.1039/B510841A)  
   **Essential**: Defines the scaling law L/w ∝ (Q_disp/Q_cont) for squeezing regime.

4. **Thorsen, T., Roberts, R. W., Arnold, F. H., & Quake, S. R. (2001)**  
   *Dynamic pattern formation in a vesicle-generating microfluidic device*  
   Physical Review Letters, 86(18), 4163.  
   DOI: [10.1103/PhysRevLett.86.4163](https://doi.org/10.1103/PhysRevLett.86.4163)  
   **Historical**: One of the first demonstrations of microfluidic droplet generation.

### Reviews
5. **Christopher, G. F., & Anna, S. L. (2007)**  
   *Microfluidic methods for generating continuous droplet streams*  
   Journal of Physics D: Applied Physics, 40(19), R319.  
   DOI: [10.1088/0022-3727/40/19/R01](https://doi.org/10.1088/0022-3727/40/19/R01)  
   **Review**: Comprehensive overview of droplet generation techniques.

6. **Zhu, P., & Wang, L. (2017)**  
   *Passive and active droplet generation with microfluidics: a review*  
   Lab on a Chip, 17(1), 34-75.  
   DOI: [10.1039/C6LC01018K](https://doi.org/10.1039/C6LC01018K)  
   **Recent Review**: State-of-the-art droplet generation methods.

### Regime Transitions
7. **De Menech, M., Garstecki, P., Jousse, F., & Stone, H. A. (2008)**  
   *Transition from squeezing to dripping in a microfluidic T-shaped junction*  
   Journal of Fluid Mechanics, 595, 141-161.  
   DOI: [10.1017/S002211200700910X](https://doi.org/10.1017/S002211200700910X)  
   **Theory**: Detailed analysis of dripping-jetting transition.

---

## Computational Fluid Dynamics

This project's simulation work is all [OpenFOAM](../../simulation/openfoam/)
(`interFoam` / `multiphaseInterFoam`, VOF), not COMSOL — see
[`simulation/openfoam/results/`](../../simulation/openfoam/results/) for the
built and verified cases. The two theory references below are general
interface-tracking / VOF background, independent of tool.

### Interface-Tracking Theory
8. **Jacqmin, D. (2000)**  
   *Contact-line dynamics of a diffuse fluid interface*  
   Journal of Fluid Mechanics, 402, 57-88.  
   DOI: [10.1017/S0022112099006874](https://doi.org/10.1017/S0022112099006874)  
   **Theory**: Foundation for phase field / diffuse-interface modeling of two-phase flow.

9. **Derzsi, L., Kasprzyk, M., Plog, J. P., & Garstecki, P. (2013)**  
   *Flow focusing with viscoelastic liquids*  
   Physics of Fluids, 25(9), 092001.  
   DOI: [10.1063/1.4817995](https://doi.org/10.1063/1.4817995)  
   **Simulation**: droplet-formation model validation methodology (originally COMSOL; the same validation approach applies to the OpenFOAM cases here).

---

## Causal Inference

### Textbooks
11. **Pearl, J. (2009)**  
    *Causality: Models, Reasoning, and Inference* (2nd ed.)  
    Cambridge University Press.  
    **Textbook**: Foundation of modern causal inference.

12. **Peters, J., Janzing, D., & Schölkopf, B. (2017)**  
    *Elements of Causal Inference: Foundations and Learning Algorithms*  
    MIT Press.  
    **Textbook**: Modern methods for causal discovery from data.

### Causal Discovery Methods
13. **Spirtes, P., Glymour, C., & Scheines, R. (2000)**  
    *Causation, Prediction, and Search* (2nd ed.)  
    MIT Press.  
    **Classic**: PC algorithm and constraint-based causal discovery.

14. **Chickering, D. M. (2002)**  
    *Optimal structure identification with greedy search*  
    Journal of Machine Learning Research, 3, 507-554.  
    **Algorithm**: GES (Greedy Equivalence Search) for score-based discovery.

15. **Runge, J., Nowack, P., Kretschmer, M., Flaxman, S., & Sejdinovic, D. (2019)**  
    *Detecting and quantifying causal associations in large nonlinear time series datasets*  
    Science Advances, 5(11), eaau4996.  
    DOI: [10.1126/sciadv.aau4996](https://doi.org/10.1126/sciadv.aau4996)  
    **Algorithm**: PCMCI for time-series causal discovery.

---

## Microfluidic Fabrication

### Soft Lithography / PDMS
16. **Xia, Y., & Whitesides, G. M. (1998)**  
    *Soft lithography*  
    Annual Review of Materials Science, 28(1), 153-184.  
    DOI: [10.1146/annurev.matsci.28.1.153](https://doi.org/10.1146/annurev.matsci.28.1.153)  
    **Technique**: PDMS fabrication method (for future iterations).

### Thermoplastic Micromachining
17. **Becker, H., & Gärtner, C. (2008)**  
    *Polymer microfabrication technologies for microfluidic systems*  
    Analytical and Bioanalytical Chemistry, 390(1), 89-111.  
    DOI: [10.1007/s00216-007-1692-2](https://doi.org/10.1007/s00216-007-1692-2)  
    **Review**: PMMA and thermoplastic fabrication methods.

---

## Machine Learning for Microfluidics

### Droplet Detection
18. **Fei, W., Hsu, T. M., Liou, Y. C., & Chen, B. Y. (2019)**  
    *Real-time microfluidic droplet detection via region proposal-based deep neural network*  
    IEEE Access, 7, 154074-154082.  
    DOI: [10.1109/ACCESS.2019.2948800](https://doi.org/10.1109/ACCESS.2019.2948800)  
    **CV Application**: Deep learning for droplet detection.

### Symbolic Regression
19. **Kamienny, P. A., d'Ascoli, S., Lample, G., & Charton, F. (2022)**  
    *End-to-end symbolic regression with transformers*  
    Advances in Neural Information Processing Systems, 35, 10269-10281.  
    https://arxiv.org/abs/2204.10532  
    **Algorithm**: Used in causal chambers paper for symbolic regression.

---

## Fluid Mechanics Fundamentals

20. **Bruus, H. (2008)**  
    *Theoretical Microfluidics*  
    Oxford University Press.  
    **Textbook**: Comprehensive microfluidics theory (Hagen-Poiseuille, etc.).

21. **Stone, H. A., Stroock, A. D., & Ajdari, A. (2004)**  
    *Engineering flows in small devices: Microfluidics toward a lab-on-a-chip*  
    Annual Review of Fluid Mechanics, 36, 381-411.  
    DOI: [10.1146/annurev.fluid.36.050802.122124](https://doi.org/10.1146/annurev.fluid.36.050802.122124)  
    **Review**: Microfluidics fundamentals.

---

## Out-of-Distribution Generalization

22. **Arjovsky, M., Bottou, L., Gulrajani, I., & Lopez-Paz, D. (2019)**  
    *Invariant risk minimization*  
    arXiv preprint arXiv:1907.02893.  
    **Method**: IRM for causal OOD generalization.

23. **Schölkopf, B., Locatello, F., Bauer, S., Ke, N. R., Kalchbrenner, N., Goyal, A., & Bengio, Y. (2021)**  
    *Toward causal representation learning*  
    Proceedings of the IEEE, 109(5), 612-634.  
    DOI: [10.1109/JPROC.2021.3058954](https://doi.org/10.1109/JPROC.2021.3058954)  
    **Vision**: Causal representation learning framework.

---

## Additional Resources

### Online Courses
- **MIT OCW**: Microfluidics (Course 6.777)
- **Coursera**: Introduction to Causal Inference (Brady Neal)

### Software
- **COMSOL Multiphysics**: www.comsol.com
- **Tigramite**: Time-series causal discovery (github.com/jakobrunge/tigramite)
- **causalchamber**: Python package (github.com/juangamella/causal-chamber-package)

### Communities
- **Microfluidics Forum**: https://www.elveflow.com/microfluidic-reviews/
- **Causal Inference Discord**: https://discord.gg/causalinference

---

## Citation for This Project

If you use the microfluidic causal chamber design, datasets, or code:

```
@misc{microfluidic_chamber_2025,
  author={[Your Name]},
  title={Microfluidic Causal Chamber: T-Junction Design},
  year={2025},
  howpublished={GitHub Repository},
  url={[your_github_url]},
  note={Extension of the Causal Chambers project (Gamella et al. 2025)}
}
```

And please also cite the original Causal Chambers paper:

```
@article{gamella2025chamber,
  author={Gamella, Juan L. and Peters, Jonas and B{\"u}hlmann, Peter},
  title={Causal chambers as a real-world physical testbed for {AI} methodology},
  journal={Nature Machine Intelligence},
  doi={10.1038/s42256-024-00964-x},
  year={2025},
}
```

---

**Last Updated**: October 22, 2025

