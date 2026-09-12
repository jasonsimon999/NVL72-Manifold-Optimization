# NVL72-class coolant manifold optimization

A working Python thermal/hydraulic network and design study for **18 compute trays + 9 switch trays**, with heterogeneous heat loads, spatially resolved supply and return headers, and explicit CDU/facility constraints. The primary load is **115.56 kW**. This is an engineering reference model, not NVIDIA's proprietary rack design.

The executed study selected Design C: constant 38 mm headers with an added switch-path restriction. It lowers nominal maximum outlet from 55.97°C to 53.80°C, with pump electrical demand rising from 266.11 W to 350.31 W. It passes the nominal screen; 27 of 32 hardware-uncertainty draws pass, so it is not qualified across the full uncertainty range.

Start with [the computed engineering report](results/reports/engineering_report.md), [baseline inputs](config/baseline.yaml), and [source provenance](data/sources.yaml). The original [agent.md](agent.md) is retained as the primary engineering specification. The results are conditional on assumed component pressure losses.

## Install and reproduce

**Start here:** [Step-by-step VS Code and Streamlit Cloud instructions](docs/RUNNING.md).

For the dashboard only, open this project folder in VS Code and run:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run_app.py
```

You can also select the `.venv` interpreter and press **F5 → Run manifold dashboard**. Streamlit Cloud's main file remains **dashboard.py**. Installing `requirements.txt` now also installs the model package through its `.` entry, so imports work in workers and interactive reruns as well as initial startup. No separate package-install command or `PYTHONPATH` setting is needed. After pushing this dependency change, reboot the Cloud app and check its build log for `nvl72-manifold==0.1.1` or newer.

The dashboard now includes expandable derivations, water/PG25/EG50 comparisons, estimated chip-temperature intervals and configurable targets, independent facility-water controls, a design-summary CSV, and independently editable orifices at all 27 trays. Download the complete result JSON to retain the resolved configuration. New research and explicit defaults are documented in the September 12 addendum to [agent.md](agent.md).

EG50 is 50% ethylene glycol **by volume**, using Dow SR-1 typical properties over 10–120°C. It is not qualified for this CDU/material system. Chip resistances and the default 80°C ceiling are engineering assumptions, not manufacturer-defined optimal temperatures. Enter installed thermal limits and measured resistance data before treating a pass as performance evidence.

Reproduce the seven new cases with `PYTHONPATH=src .venv/bin/python studies/extension_study.py`. View [design comparisons](results/extension_study/design_comparison.csv), plus per-case JSON, chip/tray/design CSVs and equation-bearing reports in `results/extension_study`. Earlier reports and their uncertainty results are historical; the new chip and facility checks were not retroactively included in those Monte Carlo counts.

At matched 115.56 kW, 40°C and 120 L/min, the selected PG25 design estimates an upper chip temperature of 77.80°C and 350.31 W external-duty pump power. Changing only the coolant to EG50 gives 80.09°C and 382.42 W and fails the assumed chip ceiling and conservative HX capacity screen. These differences include resolved coolant-property effects; unmeasured cold-plate and chip-resistance changes remain outside the comparison. The original facility case needs approximately 139.15 L/min for the new assumed 12 K rise allowance; the configured 150 L/min exceeds this requirement.

Python 3.11 or later:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install '.[test,dashboard]'
python -m pytest -q
nvl72 simulate --config config/baseline.yaml
nvl72 optimize --config config/baseline.yaml --design D --method global
nvl72 study --config config/baseline.yaml --samples 32
streamlit run dashboard.py
```

The module equivalents `python -m nvl72 simulate`, `python -m nvl72.simulate`, `python -m nvl72.optimize`, `python -m nvl72.sweep` and `python -m nvl72.report` also work. Run from the project root so output/config paths resolve consistently. On restricted machines, set `MPLCONFIGDIR=/tmp/nvl72-mpl` for Matplotlib.

For the environment created during this build, activate `.venv`; all required packages are installed. The dashboard loads current code directly from `src`, so edits need no reinstall. For the separately installed scientific CLI, reinstall with `python -m pip install . --no-build-isolation --no-deps` after source changes, or run studies with `PYTHONPATH=src`. `requirements-lock.txt` is a historical runtime snapshot; use `requirements.txt` for dashboard installation and Cloud deployment. `iapws` is optional for regenerating the checked-in water table.

A complete study runs sweeps before optimizing. It compares A (optimized constant ID), B (tapers), C (two restrictions), D (tapers + two restrictions + flow), E (analytical minimum-head location balancing at D geometry), and D116 (D at 116 LPM). Every one is compared against the **unchanged original constant-diameter reference**, not against an upgraded baseline. E is exact fixed-geometry sizing followed by an independent coupled solve; full continuous E search is also available through `nvl72 optimize --design E`.

To reuse a completed Design D global search while running all comparisons:

```sh
python studies/run_all.py --reuse --samples 32
```

### Individual commands

```sh
nvl72 simulate --config config/inrow.yaml --name inrow
nvl72 simulate --config config/optimized_example.yaml --name candidate
nvl72 sweep --parameter rack_flow_LPM --min 90 --max 130 --count 9
nvl72 sweep --parameter header_diameter_mm --min 25 --max 50
nvl72 optimize --design C --method local
nvl72 report --result results/optimized.json --output results/reports/regenerated.md
```

## What is factual, derived or assumed?

Every baseline YAML leaf has a record in `data/sources.yaml`, including value, units, category, source, URL and notes. Categories are NVIDIA, OEM, OCP, 3P, DERIVED, ESTIMATE and ASSUMPTION. Alternative 102 kW nominal and 115 kW OEM liquid envelopes are retained. The source's schematic omitted C09; the configured layout restores all 27 branches.

- NVIDIA power budgets: 1200 W/GPU, four GPUs plus two CPUs in a 5800 W tray budget; 11160 W aggregate NVSwitch budget.
- Derived: 500 W/CPU, 1240 W/switch tray, 115560 W primary liquid model. Full capture of these power allocations by coolant is an assumption.
- OEM CDU121 reference: 121 kW at 4 K approach, 120 LPM and 115 kPa external available differential pressure.
- OEM QCT example: 45°C inlet maximum, 65°C return maximum, up to 130 LPM. These are limits, not mandatory operating temperatures.
- Assumed: 38 mm baseline headers, branch elevations/plumbing, cold-plate/QDC K values, minor losses, pump shutoff/efficiency, facility operating point, and uncertainty distributions.

The PG25 table preserves `agent.md` values at 40°C and 50°C. Its other points use labeled estimated extensions: linear density/cp and log-linear viscosity. Conductivity is anchored at 40°C with an assumed slope. It is a PG25-like screening model, not a qualified full DOWFROST product correlation. Water points are generated from IAPWS97 at 0.1 MPa. Interpolation fails outside 5–95°C instead of silently extrapolating. Manufacturer curve/property measurements can replace these inputs without changing the solver.

The GF 232 kPa loss breakdown describes a **broader technical loop**. `GF_reference_comparison.csv` compares fractions only; this model never treats that value as a rack loss measured against a 115 kPa CDU budget. Assumed component scales are not validation of actual hardware compatibility.

## Physics and numerical method

SI is used internally: Pa, m, kg/s, K, W, m³/s. YAML/CLI inputs and exports also provide °C and L/min, converted centrally.

For bottom-connected direct-return headers, segment j carries all branches above it:

\[
\dot m_{s,j}=\dot m_{r,j}=\sum_{i=j}^{n-1}\dot m_i.
\]

Each branch loop satisfies

\[
H=\Delta P_{branch,i}+\sum_{j\le i}
[\Delta P_{s,j}+\Delta P_{r,j}+(\rho_s-\rho_{r,j})g\Delta z_j].
\]

All branch mass flows and H are solved together with `scipy.optimize.root`, falling back to bounded `least_squares`. Header pressures are reconstructed from the same equations; they are not constant-pressure reservoirs. Root trial flows may be signed, but a final reversed-flow solution is rejected because the implemented thermal mixing topology assumes forward branches. Removed trays explicitly remove/close the path.

Pipe and component losses:

\[
V=\dot m/(\rho A),\quad Re=\rho |V|D/\mu,
\qquad \Delta P=[fL/D+K]\rho V|V|/2.
\]

Laminar f=64/Re, turbulent Haaland, and continuous transition from Re 2300 to 4000. `colebrook` supports turbulent validation. Cold plates/QDCs default to `K_hydraulic m|m|` with separate tray classes. Optional SI polynomial/monotone tabulated pressure–volume-flow curves override them.

For variable heat capacity:

\[
h(T)=\int c_p(T)dT,\quad h_{out,i}=h_s+Q_i/\dot m_i,
\qquad h_{mix}=\sum_i\dot m_i h_i/\sum_i\dot m_i.
\]

The piecewise-linear cp integral is inverted analytically. Local branch mean and mixed-return temperatures update density and viscosity until both temperature and mass-flow tolerances pass. Every solve checks mass, energy and pressure closure and reports residuals/iterations. Isothermal hydrostatic head cancels; warm-return density leaves a small buoyancy contribution.

The preferred target is `m_target = m_total Q_i / sum(Q)`. Equal-flow targets are selectable. Zero-load branches have undefined relative thermal error; they are excluded from that metric and their share of rack flow is reported separately. Positive near-zero loads retain mathematically large errors, which should be interpreted with care.

## Engineering boundaries and constraints

The in-rack boundary runs from CDU external supply port through rack trays to CDU return. The in-row overlay adds external pipe/fitting/equipment loss and uses the XDU1350 rating shared by eight identical racks. Its assumed 38°C TCS / 34°C FWS supplies leave room below the conservatively applied 52°C secondary return limit. Aggregate cooling, flow and pump head are checked; a row distribution network is not solved.

`dp_pump(q,N)=dp_shutoff N²−a q²` respects affinity scaling. The unknown shutoff is assumed; the parabola passes through the published nominal point. Fixed flow calculates required duty and flags pump/head violations. Pump mode solves the actual system intersection and can return an **infeasible** operating point outside flow/thermal limits—it never clamps the root to make it pass. An impossible thermal/pump intersection raises an informative error.

The 120 LPM CDU nominal rating is conservatively treated as an operating-envelope limit; this is distinct from QCT's 130 LPM rack limit. HX screening derates nominal capacity by approach and TCS capacity-rate ratios, checks both terminal temperature pinches and calculates FWS return. It is not a manufacturer UA map. At below-rating flow/approach, nominal capacity is not assumed unchanged.

Constraints appear in every result with signed physical and normalized margins. Optimization penalizes violations and filters final selection to solved feasible candidates. Search budget termination is recorded; a feasible improvement is not a proof of global optimality. Sampled Pareto fronts expose thermal error versus pump power and volume.

## Change inputs without editing source

YAML supports `extends: baseline.yaml` with recursive overrides. Set `power.tray_heat_W` to 27 editable values or use class utilization/auxiliary loads. Set explicit ascending `rack.elevations_m` or the assumed height. Header endpoint diameters follow **flow direction**: supply inlet bottom → outlet top; return inlet top → outlet bottom. Profiles are `constant`, `linear`, `power` (exponent), or `piecewise` with `pieces_m` in flow order.

Per-tray overrides are keyed by IDs:

```yaml
branches:
  overrides:
    C01: {coldplate_K: 11000000, restriction_K: 2000000}
    S01:
      qdc_curve:
        flow_m3_s: [0, 0.00005, 0.0001]
        dp_Pa: [0, 10000, 40000]
```

A polynomial curve is `coldplate_curve: {polynomial: [a, b, c]}` with q in m³/s and pressure in Pa. Curves must be passive; no measured-curve extrapolation is allowed. A nonzero c represents a signed cracking-pressure approximation. QDC K is the **combined pair** unless replaced with a measured pair curve. Branch fittings use local configured branch ID. Restrictions use Pa/(kg/s)², not dimensionless minor K.

Enable `coldplate.enabled` for assumed first-order channel Re/Pr/Nu/h and thermal resistance chain. The reported chip temperature is an **equivalent tray quantity**, not each GPU's junction temperature. The channel hydraulic prediction is diagnostic; reduced cold-plate K continues to define the network unless a component curve replaces it.

## Outputs and interpretation

- `results/baseline.json`, `optimized.json`: complete inputs, tray/header results, solver diagnostics, constraints, facility and pressure budget.
- `results/tables`: tray CSVs, component budgets, baseline comparison, A–E ranking, sweeps, sampled Pareto fronts, paired uncertainty, gravity, workload/fault tests and GF reference comparison.
- `results/figures`: supply/return pressure, actual/target flow, normalized flow, heat, temperature, pump duty, rack schematic, sweep/Pareto and baseline/candidate comparisons.
- `results/reports/engineering_report.md`: computed engineering conclusions and tradeoffs; individual detailed reports include all constraints and provenance.
- `notebooks/engineering_demo.ipynb`: small reproducible exploration.

Reported resolved coolant inventory includes headers and branch tubes; unknown QDC/cold-plate internal volumes are excluded. The pressure budget uses mass-flow-weighted **complete-path equivalent head**, which sums to pump-required head. It does not add the 27 parallel branch drops. Signed hydrostatic contribution is separate. Pressures are relative to CDU return, not absolute. L/min values use supply density, making target/actual flow directly comparable; local return volume flow changes with density.

The paired Monte Carlo uses common random draws across baseline/candidates. It covers resistance ±30%, load variation, water/PG25, fluid-model viscosity, roughness, pump efficiency and 90–130 LPM/25–45°C operating variation. Draws outside conservative CDU flow rating fail explicitly. Report sampled feasibility and extremes as sensitivity evidence, not reliability probabilities or mathematical worst cases. Workloads and faults include tray removal, blockage, degraded QDC, reduced pump speed and warmer facility water.

## Validation and scope

Run `pytest` before optimization. Tests cover analytical laminar pipe/parallel branches, turbulent friction cross-check, enthalpy inversion/mixing, mass/energy/pressure closure, monotonic network response, zero-flow/signed losses, property bounds, geometry profiles, source coverage, pump intersection/affinity, no-gravity/hydrostatic cancellation, removed/near-zero-load trays, in-row aggregate boundaries and visible constraint failures. Dashboard smoke tests use Streamlit's AppTest.

This is steady state, one dimensional and adiabatic outside trays. Recoverable axial kinetic-head redistribution and 3D tee momentum are omitted; configured junction losses are a reduced model. Constant mass-flow cold-plate K does not capture viscosity dependence of proprietary channels; resistance uncertainty is essential. Cavitation, absolute-pressure qualification, transients, detailed multi-chip plumbing and manufacturability costs are outside scope. Qualified hardware decisions require measured component curves and vendor pump/HX data.
