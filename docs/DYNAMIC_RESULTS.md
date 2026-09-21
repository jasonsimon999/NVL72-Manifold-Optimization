# Dynamic flow control: checked results

Generated 20 September 2026 using the separate transient model. Raw data are in `results/dynamic/`. Reproduce with `python studies/dynamic_flow_study.py --full`. These are synthetic engineering comparisons, not measured NVL72 performance.

## Main finding

Active control is **not an automatic improvement**. In the default heterogeneous workload, both designs meet the entered thermal screens. Active control reduces peak representative tray temperature by **0.68°C**, but consumes **187.9 W more auxiliary electricity**, equivalent to **0.242%** of the modeled average IT load. It has **no positive simple payback** at the nominal cost assumptions.

Lower active flow does not necessarily mean lower pump power: a throttled branch can demand higher pump pressure. Here the demand controller follows the most under-supplied branch and the slow valves cause high-head operation. This is a finding about the implemented controller/actuator pairing, not proof that every active-control design is inferior. Controller tuning, measured valve curves and pump reset design remain important.

## Default setup and results

Optimized passive location-balanced bores at the saved example geometry; 18 compute and 9 switch trays; PG25 coolant; 40°C supply; 120 L/min reference flow; 115.56 kW full-load liquid/electrical-equivalent reference; 300 s seeded heterogeneous trace with 2 s timestep. Compute workload ranges 30–100%; switches use a static reference. Both liquid fractions are one for legacy-baseline reproduction. Both designs use demand-following pump control, 60% pump efficiency and a 0.2–1.2 speed envelope. Active uses combined power/temperature control, 90 s stroke and 15 s actuator lag. These settings are assumptions, not NVIDIA specifications.

| Metric | Fixed | Active | Active − fixed |
| --- | --- | --- | --- |
| Peak representative temperature (°C) | 77.9929 | 77.3162 | -0.6767 |
| Peak coolant outlet (°C) | 54.9254 | 60.3054 | +5.3800 |
| Average rack flow (L/min) | 110.3209 | 93.6155 | -16.7054 |
| Average pump electricity (W) | 275.6852 | 432.3890 | +156.7038 |
| Average total auxiliary electricity (W) | 275.6852 | 463.5890 | +187.9038 |
| Pump energy over 300 s (kWh) | 0.0230 | 0.0360 | +0.0131 |
| Thermal margin (K) | 2.0071 | 2.6838 | +0.6767 |

Average IT demand is 77.50 kW. Pump-only reduction is -56.8% (negative = increase). The reference thermal/HX screens and all entered assumptions are stored in the complete JSON. Operating thermal screens do not mean hardware qualification.

Nominal fixed incremental hardware: $675; active hardware: $16,080; difference: **$15,405**. At 8,760 equivalent hours/year and $0.12/kWh, net energy saving is -1,646 kWh/year and annual saving after maintenance is **$-523**. Negative values are additional cost. Five-/ten-year undiscounted net savings are $-18,018 / $-20,630.

## Operating conditions

Positive power saving favors active. Both designs use the same pump policy in each row. Every row uses nominal cost assumptions, so none has positive annual savings after added maintenance.

| Scenario | Peak solid °C: fixed → active | Pump reduction | Net auxiliary W saved | Active thermal screen |
| --- | --- | --- | --- | --- |
| steady | 78.16 → 77.63 | -15.5% | -58.7 | Pass |
| rack_step | 73.40 → 73.80 | -47.9% | -159.9 | Pass |
| localized | 69.79 → 69.73 | +6.2% | -8.8 | Pass |
| heterogeneous | 77.99 → 77.32 | -56.8% | -187.9 | Pass |
| worst_case | 78.16 → 77.63 | -15.5% | -58.7 | Pass |
| bursts | 76.98 → 76.99 | -29.2% | -116.4 | Pass |
| remove_compute | 78.16 → 77.63 | -15.4% | -57.2 | Pass |
| remove_switch | 78.16 → 77.63 | -15.5% | -58.4 | Pass |
| remove_several | 78.16 → 77.43 | -20.2% | -66.5 | Pass |
| reinstall | 78.17 → 77.64 | -15.4% | -58.2 | Fail |
| steady_low_utilization | 69.80 → 69.78 | +36.3% | +76.6 | Pass |

- **Steady full load / worst case:** modest temperature reduction but more electricity; no energy justification.
- **Low steady utilization:** active saves 76.6 W net and 36.3% of pump energy, with almost unchanged peak temperature. Financial savings are still insufficient at nominal costs.
- **Heterogeneous load:** default slow-valve/demand-pump pairing consumes more energy; thermal benefit is under 1°C in this trace.
- **Short bursts:** 10 s pulses are much faster than 90 s full valve stroke. Thermal storage matters more than fast area changes; this pairing saves no energy.
- **Sustained rack-wide spike:** both remain within thermal screens, with no default active energy advantage.
- **Removal:** zero flow in disconnected branches, with the remaining rack satisfying the thermal screen. Active introduces extra energy and does not show a meaningful thermal advantage in these examples.
- **Reinstallation:** both fail the outlet screen after warm trapped fluid reconnects. The selected ramp is insufficient under the assumptions. Purging/air removal is not simulated; this is a reason to test the service procedure, not a predicted field failure rate.

## Pump/control policy changes the answer

Same heterogeneous trace and same hardware assumptions:

| Pump / branch controller | Pump energy reduction | Net auxiliary W saved |
| --- | --- | --- |
| constant_speed / reactive | +13.0% | +6.2 |
| constant_speed / feedforward | +13.1% | +12.1 |
| constant_speed / combined | +12.2% | +10.3 |
| constant_dp / reactive | +26.1% | +52.6 |
| constant_dp / feedforward | +25.2% | +56.3 |
| constant_dp / combined | +24.6% | +55.0 |
| demand / reactive | -72.9% | -240.4 |
| demand / feedforward | -54.8% | -183.4 |
| demand / combined | -56.8% | -187.9 |

Constant-speed and constant-pressure comparisons can save pump energy, but the savings remain a small fraction of IT demand and do not offset the assumed maintenance and CAPEX. Do not compare different pump policies and attribute all gains to the valves.

## Economics and break-even

For the low-utilization case, net energy saving is approximately 671 kWh/year. That is only $81/year at $0.12/kWh, before $325/year incremental maintenance. At the nominal $15,405 incremental CAPEX, **five-year break-even requires about $5.07/kWh**, conditional on repeating this scenario all year. Merely achieving positive operating savings requires about $0.48/kWh. With zero incremental maintenance, the same CAPEX still takes approximately 191 years at $0.12/kWh.

At default heterogeneous demand control, net energy increases, so no positive electricity price can provide an energy-only payback. The page reports the affordable incremental CAPEX and installed cost per branch, and calculates 3-, 5- and 10-year cash flows. Low/nominal/high costs are editable budgets.

The break-even study sweeps average load floor, shared-burst probability, design flow, controlled branch count and pump efficiency. The physical sensitivity study varies 27 assumptions at low/high values (54 cases). All rows computed without solver errors. The sign of the energy benefit can change; for example, a different switch load changes which branches constrain the pump. One-at-a-time sensitivities do not quantify probabilities or interacting uncertainties.

## Thermal capacity

| Controller | Thermal-only liquid capacity · kW | Additional vs baseline · kW | CDU rating-capped · kW | Final flow · L/min |
| --- | --- | --- | --- | --- |
| fixed | 124.25 | 8.69 | 121.00 | 118.27 |
| combined | 124.25 | 8.69 | 121.00 | 118.97 |

Both reached the same thermal-only capacity to the search resolution. The original reference is 115.56 kW; the 121 kW CDU nameplate cap limits any practical interpretation. Neither figure is a validated allowable NVL72 power limit. The actual HX map, facility limits and device temperatures can be more restrictive.

## Failures and validation

With the default heterogeneous trace, a single stuck-near-closed valve raised representative peak temperature to **93.58°C** and failed the thermal screen; commanding all valves closed after communications loss raised it to **105.29°C**. Stuck-open, stuck-half and commanded fail-open retained thermal screening compliance in this example, while changing other branches' flows. Fail-open is therefore thermally preferable to fail-closed for this tested case, not a universal hardware-safety conclusion. The actuator reference itself is non-fail-safe.

Default active maximum pressure residual: 6.83e-05 Pa; node mass residual: 1.94e-16 kg/s; per-tray transient energy residual: 1.34e-10 W. Automated tests cover locked-valve equivalence, original full-load hydraulic reproduction, symmetry, heat/mass/pressure conservation, zero heat, zero pump flow, removal, leakage/shutoff, realistic actuator rate, all faults, timestep refinement, strict export and Streamlit rendering/reruns. Conservation verifies implementation, not physical calibration.

## What would improve confidence most?

Measured branch/QD/cold-plate pressure curves; valve Cv versus stroke and real failure modes; pump efficiency/head map; thermal resistance versus flow and transient capacitance; measured liquid fractions; device-specific temperature/flow limits; real synchronized compute/switch workload traces; facility/CDU dynamic capacity; and vendor installation/maintenance quotes. See [model documentation](DYNAMIC_FLOW_CONTROL.md) for equations, complete limitations, sources and changed files.
