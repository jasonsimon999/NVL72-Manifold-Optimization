# Acceptance evidence

All required primary acceptance items have a working implementation and executed artifact.

| Requirement | Evidence |
|---|---|
| 27 branches, unequal compute/switch loads | baseline.yaml; baseline_trays.csv |
| Spatial supply/return pressures; solved flows | hydraulics.py; baseline pressure-height figure |
| Coupled nonlinear network and diagnostics | root / bounded least_squares; validation block in every result |
| Mass, energy, pressure closure | analytical and network tests; baseline/optimized JSON |
| Temperature-dependent water and PG25 | coolant.py; checked-in properties; anchor and enthalpy tests |
| Cold-plate, QDC, tubing, fitting and valve losses | component configuration; pressure budgets |
| Optional physical channel/thermal resistance chain | coldplate.py; enabled-mode test |
| CDU pump, fixed flow and operating point | cdu.py; solver.py; intersection and envelope tests |
| Facility heat balance and HX screening | facility.py; terminal pinch/approach/capacity constraints |
| Constant, tapered and balanced configurations | design A–E results and ranking |
| Linear, power and piecewise profiles | manifold.py; profile test and examples |
| Heat-proportional/equal targets; thermal/conventional metrics | objectives.py; tray exports |
| Thermal maps, head and pump power | all result JSON/CSV/plots |
| Deterministic sweeps | six sweeps in sweeps.csv |
| Local and global optimization | C local convergence; D differential evolution plus successful local polish |
| Pareto analysis | nondominated sampled fronts versus power and volume |
| Uncertainty | paired operating and hardware-only Monte Carlo tables |
| Baseline versus optimized comparison | engineering_report.md; baseline_vs_optimized.csv |
| Manufacturability and simplification penalty | design_ranking.csv; 2-class vs 27-location comparison |
| Workloads, faults and gravity | faults_workloads.csv; gravity.csv |
| Publication plots and rack schematic | results/figures |
| JSON and tray-by-tray CSV | results/*.json; results/tables/*_trays.csv |
| Engineering Markdown report | results/reports/engineering_report.md |
| Dashboard controls, comparison, constraints and plots | dashboard.py; Streamlit AppTest default/changed-flow validation |
| CLI and notebook | installed nvl72 command; notebooks/engineering_demo.ipynb |
| Reproduction and uncertainty labeling | README.md; sources.yaml; public_source_followup.md |

The global optimizer exhausted its deliberately limited evolutionary budget; local polishing converged and the selected C design's local optimization converged. This meets the requirement for an executed feasible improvement, not a claim of a globally optimal design. The report explicitly records failing sensitivity/fault points. Hardware geometry/curves and PG25 extensions remain conditional engineering assumptions.
