# Dynamic flow control: implementation and engineering basis

The new **Dynamic Flow Control** page is separate from the fixed-orifice dashboard. Start the existing app with `python run_app.py`, then select **Dynamic Flow Control** in the sidebar. The same `dashboard.py` entrypoint works on Streamlit Cloud. Commit the new `pages/` directory and `src/nvl72/dynamic/` package with the app; no new dependencies are required.

## Baseline and fair comparison

The page can import the last configuration solved on the original page or a saved fixed-orifice YAML. It does not silently optimize imported hardware. Alternatively, the **Optimized per-tray reference** invokes the existing analytical location-balancing routine at the existing optimized-example geometry. That routine minimizes required head for exact prescribed target flows at that geometry; it is not a global optimum over all possible geometries. Equivalent resistance coefficients are converted to physical bores once. Those bores remain unchanged throughout every transient and sweep.

Both systems use identical electrical workloads, coolant, geometry, passive components, inlet temperature and selected pump-control policy. Active valves replace the balancing plates on the selected branches and add an explicit body loss. Uncontrolled branches keep their passive plates. Initial active positions match the passive resistance as closely as their limits allow. The shared initial thermal state is passive equilibrium at the first workload sample. Initial-condition/startup effects are included, not trimmed away.

The original page receives only a session-state handoff; its controls, rack map, charts, optimizer and constraint policy are preserved. The only original physics change extracts its existing loss evaluator into a reusable function. Regression tests verify unchanged original behavior.

## Research and provenance

Research checked 20 September 2026:

- [NVIDIA hardware](https://docs.nvidia.com/dgx/dgxgb200-user-guide/hardware.html): 18 compute trays, 9 switch trays and liquid-cooling architecture. This does not publish complete tray pressure-loss or transient thermal models.
- [NVIDIA DPS](https://docs.nvidia.com/datacenter/dps/versions/latest/guides/runbooks/maxlps-simple-mode-pilot.html): recommended **11,160 W** aggregate GB200 switch static power input; dividing equally gives **1,240 W/tray**. This is an electrical power-model reference, not calorimetry.
- [OCP rack manifold requirements](https://www.opencompute.org/documents/ocp-white-paper-rack-manifold-requirements-and-qualification-v3-pdf): distribution according to cooling demand, hydraulic interfaces, serviceability and a **1.5 m/s** velocity guideline in Table 3. It is reported as an applicability-dependent advisory, not an NVIDIA hard limit.
- [OCP cold-plate loop requirements](https://www.opencompute.org/documents/cold-plate-cooling-loop-requirements-rev-2-pdf): dripless QDs shut off both sides on disconnection. The simulation removes that branch from the hydraulic equations and turns off its workload.
- [OCP modular TCS](https://www.opencompute.org/documents/ocp-modular-tcs-rev-1-final-2025-pdf) and [ASHRAE direct-to-chip resiliency research scope](https://www.ashrae.org/File%20Library/Technical%20Resources/Research/Research%20Project%20Bidding/1972-RFP.pdf): motivate loop-level resiliency and thermal ride-through analysis. No building-water numeric rule is applied as an NVL72 TCS specification.
- [Belimo LRB24-SR](https://www.belimo.com/us/shop/en_US/p?code=LRB24-SR): representative actuator **90 s** stroke, **1.5 W** running and **0.4 W** holding. This is an HVAC actuator example, not a qualified NVL72 valve; its manufacturer explicitly describes it as **non fail-safe**. Communications fail-open here assumes remaining control power. A physical power-loss fail-open design requires appropriate hardware.
- [Measured H100 training power](https://arxiv.org/abs/2412.08602) and [NVIDIA power/thermal guidance](https://docs.nvidia.com/multi-node-nvlink-systems/multi-node-tuning-guide/power-thermals.html): motivate fluctuating workloads. The six synthetic scenario families are not production NVL72 traces or calibrated statistical distributions.

`src/nvl72/dynamic/sources.py` produces a parameter/value/units/classification/confidence/reference/notes/range table for every dynamic setting and includes the inherited baseline configuration. Original component provenance remains in `data/sources.yaml`. Estimated values are editable; the sensitivity study covers the principal physical and economic uncertainties.

## Equations and timestep sequence

1. Generate a seeded electrical workload and mechanical connection state. Compute liquid heat as `P_liquid = f_liquid × P_electrical`, with different compute and switch fractions. Existing tray heat assignments are electrical-equivalent reference inputs on this separate page; default fractions of one reproduce their legacy liquid load. Neither fraction is claimed as measured.
2. Sample temperature with configurable update interval, noise and bias. Apply fixed, temperature PI, power-derived flow tracking, or combined control. Positive temperature error opens the valve. Integral limiting and conditional anti-windup prevent unchecked accumulation.
3. Move the actuator toward its command with a first-order lag, maximum stroke rate and deadband. `A(u) = Amax [fmin + (1−fmin)u]`. Effective diameter follows the square root of area. The existing permanent-orifice-loss law is reused; a separate dimensionless body K adds full-open loss. This is a Cv/area surrogate, not a measured valve characteristic.
4. Solve all open branch loop equations together against `Δp_pump = p0 N² − a Q²`. Every header segment carries the sum of downstream branch masses. The evaluator includes existing pipe friction, QD, cold-plate, fitting, valve, orifice, gravity and optional external-loop losses. A branch closes exactly when its QD disconnects; zero configured leakage plus zero valve opening also gives exact zero flow. Changing one valve changes neighboring flow and pump/system intersection. The solver checks open-loop pressure residuals and each header node's mass residual.
5. Advance two thermal nodes using conservative implicit Euler:
   - `Cs (Ts_new − Ts_old)/dt = P_liquid − (Ts_new − Tf_new)/R`
   - `Cf (Tf_new − Tf_old)/dt = (Ts_new − Tf_new)/R − m cp (Tf_new − Tin)`
   - Sum: heat input = removed heat + stored heat. `Tf` is a well-mixed local coolant/outlet temperature. `Ts` is an equivalent tray solid/cold-plate temperature, **not** a resolved GPU or CPU junction.
6. Adjust pump speed with a finite lag and speed limits. Constant-speed and constant-pressure modes are available. Demand mode follows the **most under-supplied connected branch**, not just summed target flow; summed targets alone can starve switch trays. This controller is a heuristic, not a globally optimized plant controller. `m_target = max(P_liquid/(cp ΔTtarget), minimum_flow)`. All pump modes apply equally to both designs.
7. Record `P_hydraulic = Δp × Q` and `P_electric = P_hydraulic/η`. Integrate with the same right-endpoint time convention as thermal storage. Include valve running/holding power and controller electronics. Cubic savings are not assumed outside affinity-law conditions.

## Key assumptions and limitations

- Hydraulic density and viscosity are frozen at the full-load reference thermal state, preserving the passive reference pressure/flow solution. Thermal cp is fixed at inlet. The original steady model still uses its temperature-dependent property iteration. The transient approximation is suitable for exploratory comparisons, not arbitrary large-temperature property excursions.
- Default whole-tray `R`: compute 0.004 K/W, switch 0.012 K/W. `Cs`: 12,000 and 4,000 J/K; local `Cf`: 1,200 J/K. These are adjustable sensitivity inputs, not device data. An assumed 80°C screening ceiling is not an NVIDIA performance limit.
- Inlet temperature is prescribed. The page exposes peak heat rejection versus reference HX capacity and flow/velocity screens, but does not solve CDU/HX thermal inventory, facility dynamics or plant electricity. Pump heat, air-side heat rejection, transport delay, boiling, cavitation and water hammer are omitted.
- Shared-pump multi-rack configurations assume identical synchronized rack loading. No other rack's independent network is solved.
- Failure heat can continue to accumulate indefinitely because hardware throttling/shutdown is not modeled. At very high temperatures, results are model extrapolations, not physical operating predictions.
- Detached trays retain stored thermal energy but are excluded from operating thermal screens; warm fluid and thermal limits are considered again after reconnection. The ramp represents a service procedure, not detailed QD kinematics. Purging and trapped-air management remain outside scope.
- Constant pump efficiency omits off-design efficiency and motor idle power. Perfect sensor data are not required, but the branch flow sensor used by tracking control is ideal; its installation cost is included. Temperature sensor uncertainty is modeled explicitly.
- The fraction of trays following a common random burst is an input; it is not exactly the realized Pearson correlation. Switch electrical load remains static at its configurable reference in these scenarios.

## Outputs and how to read them

The page includes a time-selectable 27-branch diagram, paired headline table, ten fixed/active time traces, shared-scale rack heat maps, per-tray peaks, equations and source downloads. No valve-opening plot is invented for passive plates: those entries export as JSON null.

Thermal metrics include compute/switch peaks, mean, simultaneous spread, coolant outlet maximum, time above limits, margin and tray ΔT. Hydraulic metrics include per-branch flow and pressure, header pressures, total flow, pump speed/head and maximum header velocity. Flow error is normalized against **each tray's thermal target**, not equal flow across all trays. Reports include RMS, maximum absolute error, standard deviation and worst tray.

Energy metrics include pump kWh, actuator kWh and net auxiliary kWh. Reliability outputs include command changes above deadband, total travel, equivalent cycles (travel/2), time with any valve near a stop, overshoot, neighboring-branch disturbance and recovery. Recovery is time after the event until all operating thermal screens remain satisfied for the remainder of the run; it is not a rigorous settling-time estimate for arbitrary random workloads.

Explicit studies compare all workload families, three active controllers × three pump policies, seven failures, three communications fallback positions, physical sensitivity ranges, operating-condition break-even sweeps and sustained thermal capacity. Errors are reported as failed study rows; they are never converted to zero or favorable results.

The capacity search holds bores fixed and tests 0–3× load at a minimum 600 s horizon. It requires final 30 s thermal limits and less than 0.02 K/s drift, then bisects ten times. It reports a separate CDU nameplate cap. This is a finite-horizon sustained thermal screen, not a proof of maximum electrical performance or an OEM power-limit recommendation.

## Economics

Low/nominal/high editable budgets include passive plates, valves, temperature and branch-flow sensors, pressure sensing, controller, wiring, power supply, integration and yearly maintenance. They are not procurement quotations. Existing CDU hardware is common to both and cancels from incremental CAPEX; no pump purchase saving is assumed.

`Annual kWh = average auxiliary W × operating hours / 1000`.
`Annual savings = fixed energy + maintenance cost − active energy − maintenance cost`.
`Simple payback = incremental CAPEX / positive annual savings`.
`N-year savings = N × annual savings − incremental CAPEX`.
`Break-even electricity price = (incremental CAPEX / horizon + incremental maintenance) / annual net kWh saved`, only if net kWh saving is positive.

The page reports both pump-only savings and net auxiliary savings as a percentage of actual modeled IT demand. Annualization assumes the selected short workload repeats for the entered hours. NPV, downtime probabilities, IT throughput benefits and avoided pump capital are not invented.

## Reproduce and validate

From the project root with the virtual environment active:

```sh
python run_app.py
python -m pytest -q
python studies/dynamic_flow_study.py --full
```

The last command saves reproducible JSON and CSV files under `results/dynamic/`. It does not change the website or passive design. `docs/DYNAMIC_RESULTS.md` contains the checked default results and interpretation.

Required validation covers: locked-active equals fixed; original full-load hydraulic reproduction; identical branches with negligible headers; zero heat relaxation; disconnected branch zero flow; pump off zero flow and heat storage; finite valve stroke; near-closed leakage; zero-leakage shutoff with continuing heat; open-valve coupled pressure balance; every-step energy/mass/pressure conservation; seed reproducibility; sensor/valve/communications/pump failures; timestep refinement; unchanged inputs; optimized-mode fallback/selection; and strict JSON export. Original model regression tests remain included.

## Files

- `pages/1_Dynamic_Flow_Control.py`: standalone page entrypoint with source-path bootstrap.
- `src/nvl72/dynamic/`: baseline handoff, settings, provenance, workloads, hydraulics, thermal storage, controls, pump response, economics, studies, export, plotting and UI.
- `src/nvl72/hydraulics.py`: shared evaluator extraction; original solve interface retained.
- `src/nvl72/dashboard_support.py`: recursive model fingerprint so nested model edits invalidate caches.
- `dashboard.py`: session-state handoff only.
- `studies/dynamic_flow_study.py`, `tests/test_dynamic.py`: reproducibility and regression validation.
- This document, `DYNAMIC_RESULTS.md`, `agent.md`, and `results/dynamic/`: implementation record and calculated evidence.

Most valuable missing measurements: per-tray Δp–flow curves including real QDs; valve Cv versus stroke and actuator/leakage/failsafe data; device junction-to-fluid resistance versus flow; tray thermal capacitance/transport delay; measured liquid fraction; real AI workload traces; pump efficiency/head maps; facility/CDU transient capacity; qualified device temperature limits; and installed/maintenance quotes.

## Optimized variable-orifice mode

The sidebar's **Optimized variable orifice diameter** controller maps each branch's power-derived target flow to an effective area. Since an incompressible restriction is approximately quadratic in flow, the command uses a `sqrt(m_target/m_actual)` area correction, bounded by the configured minimum area, maximum bore fraction, stroke rate and actuator time constant. A bounded temperature trim protects the entered thermal target. The hydraulic result exports the effective diameter in `orifice_diameter_mm` for every branch and timestep.

The active run is treated as a candidate. The page computes a dimensionless score from thermal overshoot, RMS and worst-case flow error, auxiliary power, peak pressure and actuator travel. It accepts active control only when the candidate passes thermal and numerical closure screens and scores lower than the fixed design. Otherwise it falls back to an exact copy of the fixed result, reports the reason, and uses fixed hardware in the economics. The rejected trial remains in the JSON export as `active_candidate` for auditability. Weights and the fallback tolerance are editable advanced assumptions; this is a transparent screening rule rather than a global optimizer or a substitute for measured valve Cv data.
