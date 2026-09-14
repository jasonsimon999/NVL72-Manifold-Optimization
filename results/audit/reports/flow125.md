# constant-diameter reference manifold

# Configuration
```yaml
name: constant-diameter reference manifold
rack:
  compute_trays: 18
  switch_trays: 9
  layout:
  - C01
  - C02
  - C03
  - C04
  - C05
  - C06
  - C07
  - C08
  - C09
  - S01
  - S02
  - S03
  - S04
  - S05
  - S06
  - S07
  - S08
  - S09
  - C10
  - C11
  - C12
  - C13
  - C14
  - C15
  - C16
  - C17
  - C18
  elevations_m: null
  flow_LPM: 125
  supply_C: 40
  operating_mode: fixed_flow
  gravity_enabled: true
  gravity_m_s2: 9.80665
coolant:
  type: PG25
  property_file: /Users/jasonsimon/Desktop/Rack Manifold Optimization/data/coolant_properties.csv
  viscosity_multiplier: 1.0
power:
  gpu_W_each: 1200
  gpus_per_compute_tray: 4
  grace_cpu_W_each: 500
  cpus_per_compute_tray: 2
  switch_rack_total_W: 11160
  compute_fraction: 1.0
  switch_fraction: 1.0
  compute_aux_W: 0
  switch_aux_W: 0
  tray_heat_W: null
geometry:
  height_m: 1.8
  roughness_m: 1.5e-06
  supply:
    profile: constant
    inlet_m: 0.038
    outlet_m: 0.038
    exponent: 1.0
    pieces_m:
    - 0.038
    - 0.032
    - 0.025
  return:
    profile: constant
    inlet_m: 0.038
    outlet_m: 0.038
    exponent: 1.0
    pieces_m:
    - 0.025
    - 0.032
    - 0.038
branches:
  compute:
    diameter_m: 0.008
    tube_length_m: 1.5
    tube_multiplier: 1.0
    coldplate_K: 5500000.0
    qdc_K: 2300000.0
    restriction_K: 0.0
  switch:
    diameter_m: 0.006
    tube_length_m: 1.0
    tube_multiplier: 1.0
    coldplate_K: 20000000.0
    qdc_K: 5000000.0
    restriction_K: 0.0
  overrides: {}
loss_coefficients:
  header:
    tee: 0.08
    entrance: 0.2
    exit: 0.2
    reducer: 0.05
    expansion: 0.05
  branch:
    tee: 1.0
    entrance: 0.5
    exit: 1.0
    bend: 1.2
    fittings: 0.5
    valve: 0.3
    orifice: 0.0
external:
  enabled: false
  length_m: 12.0
  diameter_m: 0.04
  minor_K: 8.0
  equipment_K: 3000.0
cdu:
  mode: in_rack
  reference: Vertiv CoolChip CDU121-like
  capacity_W: 121000
  nominal_flow_LPM: 120
  available_dp_Pa: 115000
  approach_K: 4
  shutoff_dp_Pa: 160000
  speed: 1.0
  efficiency: 0.6
  served_racks: 1
  secondary_min_C: null
  secondary_max_C: null
  nominal_electric_W: 875
  rating_coolant: PG25
  rating_supply_C: 40.0
facility:
  supply_C: 36
  flow_LPM: 150
  coolant: water
  max_return_C: 60
  hx_model: rating_scaled
  design_deltaT_K: 12.0
  minimum_hot_pinch_K: 0.0
solver:
  pressure_tolerance_Pa: 0.05
  mass_relative_tolerance: 1.0e-08
  energy_relative_tolerance: 1.0e-08
  temperature_tolerance_K: 0.0001
  flow_relative_tolerance: 1.0e-06
  max_property_iterations: 60
  max_nfev: 200
  relaxation: 0.65
constraints:
  rack_flow_max_LPM: 130
  supply_max_C: 45
  return_max_C: 65
  branch_outlet_max_C: 65
  header_velocity_max_m_s: 3.0
  diameter_min_m: 0.015
  diameter_max_m: 0.05
  soft_penalty: 1000
coldplate:
  enabled: false
  channels: 100
  channel_width_m: 0.001
  channel_height_m: 0.001
  length_m: 0.08
  heated_area_m2: 0.03
  tim_K_W: 0.0002
  spreader_K_W: 0.0002
  plate_K_W: 0.0002
  laminar_Nu: 4.36
optimization:
  target: heat_proportional
  seed: 72
  maxiter: 35
  global_maxiter: 8
  population_size: 5
  normalization:
    temperature_K: 20
    pressure_Pa: 115000
    pump_W: 400
    volume_m3: 0.004
  weights:
    flow_error: 1.0
    temperature_spread: 0.05
    pressure: 0.02
    pump: 0.02
    size: 0.015
  bounds:
    diameter_m:
    - 0.025
    - 0.05
    taper_ratio:
    - 0.6
    - 1.0
    restriction_K:
    - 0.0
    - 200000000.0
    flow_LPM:
    - 90
    - 130
uncertainty:
  samples: 32
  seed: 720
  coldplate_multiplier:
  - 0.7
  - 1.3
  qdc_multiplier:
  - 0.7
  - 1.3
  tubing_multiplier:
  - 0.7
  - 1.3
  restriction_multiplier:
  - 0.7
  - 1.3
  compute_load_multiplier:
  - 0.75
  - 1.0
  switch_load_multiplier:
  - 0.8
  - 1.2
  supply_C:
  - 25
  - 45
  flow_LPM:
  - 90
  - 130
  viscosity_multiplier:
  - 0.9
  - 1.1
  coolants:
  - water
  - PG25
  roughness_m:
  - 1.0e-06
  - 5.0e-05
  efficiency:
  - 0.5
  - 0.8
plots:
  dpi: 180
chip_temperature:
  GPU:
    resistance_range_K_W:
    - 0.01
    - 0.02
    target_max_C: 80.0
    manufacturer_limit_C: null
  CPU:
    resistance_range_K_W:
    - 0.02
    - 0.04
    target_max_C: 80.0
    manufacturer_limit_C: null
  NVSwitch:
    resistance_range_K_W:
    - 0.015
    - 0.035
    target_max_C: 80.0
    manufacturer_limit_C: null
```

# Source data
The retained `agent.md` is the primary source specification. Full categories, URLs, alternatives and every default are in `data/sources.yaml`.
| Input | Value | Category | Source |
| --- | --- | --- | --- |
| rack.compute_trays | 18 | NVIDIA | architecture |
| rack.switch_trays | 9 | NVIDIA | architecture |
| power.gpu_W_each | 1200 | NVIDIA | power |
| power.gpus_per_compute_tray | 4 | NVIDIA | architecture |
| power.grace_cpu_W_each | 500 | DERIVED | power |
| power.cpus_per_compute_tray | 2 | NVIDIA | architecture |
| cdu.capacity_W | 121000 | OEM | cdu |
| cdu.nominal_flow_LPM | 120 | OEM | cdu |
| cdu.available_dp_Pa | 115000 | OEM | cdu |
| cdu.approach_K | 4 | OEM | cdu |
| cdu.nominal_electric_W | 875 | OEM | cdu |
| constraints.rack_flow_max_LPM | 130 | OEM | qct |
| constraints.supply_max_C | 45 | OEM | qct |
| constraints.return_max_C | 65 | OEM | qct |
| liquid_reference_W | 115560 | DERIVED | power |
| nominal_liquid_W | 102000 | DERIVED | architecture |
| HPE_rack_W | 132000 | OEM | agent.md |
| HPE_liquid_W | 115000 | OEM | agent.md |
| HPE_air_W | 17000 | OEM | agent.md |
| OCP_flow_clue_LPM | 5 | OCP | agent.md |
| GF_technical_loop_Pa | 232000 | 3P | gf |
| XDU1350_temperature_C | [10, 52] | OEM | agent.md |
| water_table | IAPWS97 at 0.1 MPa, 5 K grid | DERIVED | agent.md |
| inrow.cdu.capacity_W | 1368000 | OEM | Vertiv XDU1350, agent.md section 12 |
| inrow.cdu.nominal_flow_LPM | 1200 | OEM | Vertiv XDU1350, agent.md section 12 |
| inrow.cdu.available_dp_Pa | 244000 | OEM | Vertiv XDU1350, agent.md section 12 |
| inrow.cdu.secondary_min_C | 10 | OEM | Vertiv XDU1350, agent.md section 12 |
| inrow.cdu.secondary_max_C | 52 | OEM | Vertiv XDU1350, agent.md section 12 |
| inrow.cdu.nominal_electric_W | 13700 | OEM | Vertiv XDU1350, agent.md section 12 |

# Assumptions
All geometry, branch K values, minor-loss coefficients, pump shutoff, pump efficiency, facility conditions and workload capture factors are editable assumptions. PG25 40/50°C anchors are retained; other points are modeled extensions. The C09 omission in the source schematic is corrected to retain 27 trays.

# Baseline architecture
Constant 38 mm supply and return headers; direct return to bottom CDU ports; 18 compute and 9 switch paths, two resistance classes and no location balancing. This baseline is not claimed to be NVIDIA’s actual design.

# Hydraulic equations
`m_header[j] = sum(m_branch[j:])`; `Re = rho V D / mu`; `dp = (f L/D + K) rho V|V|/2`; `dp_component = K_hyd m|m|`. All branch loops and total rack flow solve simultaneously. Gravity enters each header as `rho g dz`; warm-return density leaves a small buoyancy term. Laminar f=64/Re; turbulent Haaland with continuous transition 2300–4000.

# Thermal equations
`h(T)=integral cp(T)dT`; `h_out = h_supply + Q/m`; `h_mix = sum(m h)/sum(m)`. The code analytically inverts the piecewise-linear cp integral. This is the variable-property extension of Q=m cp ΔT.

# CDU model
`dp_pump(q,N) = dp_shutoff N² - a q²`, with a fixed from the nominal point. `P_h=dp q`, `P_e=P_h/eta`. External head boundary excludes internal CDU losses.

# Baseline results / current design
| Metric | Value |
| --- | --- |
| M_flow | 0.5363008 |
| CV_flow | 0.2444784 |
| M_thermal | 1.057314 |
| RMS_target_error | 0.7350056 |
| max_abs_target_error | 1.265409 |
| zero_load_flow_fraction | 0 |
| T_out_max_C | 55.33175 |
| T_out_min_C | 45.82235 |
| outlet_spread_K | 9.509403 |
| rack_dp_Pa | 86524.47 |
| system_dp_Pa | 86524.47 |
| rack_flow_LPM | 125 |
| heat_W | 115560 |
| T_return_C | 53.17824 |
| rack_deltaT_K | 13.17824 |
| pump_hydraulic_W | 180.2593 |
| pump_electrical_W | 300.4322 |
| header_volume_m3 | 0.004082814 |
| min_header_ID_m | 0.038 |
| max_header_ID_m | 0.038 |
| max_header_velocity_m_s | 1.848912 |
| resolved_fluid_volume_m3 | 0.005694451 |
| minimum_normalized_margin | 0.03846154 |
| minimum_screening_margin | -0.04166667 |
| T_junction_upper_max_C | 79.33175 |

# Optimized results
See engineering_report.md for the executed baseline-versus-candidate study.

# Pressure-drop breakdown
| Component | Pa | kPa | % equivalent system head |
| --- | --- | --- | --- |
| coldplates | 48216.65 | 48.217 | 55.73 |
| qdcs | 18217.04 | 18.217 | 21.05 |
| tubing | 9162.27 | 9.162 | 10.59 |
| fittings | 6941.64 | 6.942 | 8.02 |
| valves | 495.83 | 0.496 | 0.57 |
| restrictions | 0.00 | 0.000 | 0.00 |
| orifices | 0.00 | 0.000 | 0.00 |
| header_friction | 879.07 | 0.879 | 1.02 |
| header_minor | 2551.67 | 2.552 | 2.95 |
| hydrostatic_net | 60.31 | 0.060 | 0.07 |
| external_piping | 0.00 | 0.000 | 0.00 |
| external_fittings | 0.00 | 0.000 | 0.00 |
| external_equipment | 0.00 | 0.000 | 0.00 |

# Thermal distribution
| Tray | Heat W | Actual LPM | Target LPM | Outlet °C | Rise K |
| --- | --- | --- | --- | --- | --- |
| C01 | 5800.0 | 5.5052 | 6.2738 | 55.015 | 15.015 |
| C02 | 5800.0 | 5.4931 | 6.2738 | 55.048 | 15.048 |
| C03 | 5800.0 | 5.4820 | 6.2738 | 55.078 | 15.078 |
| C04 | 5800.0 | 5.4720 | 6.2738 | 55.106 | 15.106 |
| C05 | 5800.0 | 5.4628 | 6.2738 | 55.131 | 15.131 |
| C06 | 5800.0 | 5.4545 | 6.2738 | 55.154 | 15.154 |
| C07 | 5800.0 | 5.4471 | 6.2738 | 55.175 | 15.175 |
| C08 | 5800.0 | 5.4405 | 6.2738 | 55.193 | 15.193 |
| C09 | 5800.0 | 5.4346 | 6.2738 | 55.209 | 15.209 |
| S01 | 1240.0 | 3.0386 | 1.3413 | 45.822 | 5.822 |
| S02 | 1240.0 | 3.0359 | 1.3413 | 45.827 | 5.827 |
| S03 | 1240.0 | 3.0334 | 1.3413 | 45.832 | 5.832 |
| S04 | 1240.0 | 3.0311 | 1.3413 | 45.837 | 5.837 |
| S05 | 1240.0 | 3.0290 | 1.3413 | 45.841 | 5.841 |
| S06 | 1240.0 | 3.0271 | 1.3413 | 45.844 | 5.844 |
| S07 | 1240.0 | 3.0253 | 1.3413 | 45.848 | 5.848 |
| S08 | 1240.0 | 3.0238 | 1.3413 | 45.851 | 5.851 |
| S09 | 1240.0 | 3.0223 | 1.3413 | 45.854 | 5.854 |
| C10 | 5800.0 | 5.3981 | 6.2738 | 55.312 | 15.312 |
| C11 | 5800.0 | 5.3962 | 6.2738 | 55.317 | 15.317 |
| C12 | 5800.0 | 5.3947 | 6.2738 | 55.322 | 15.322 |
| C13 | 5800.0 | 5.3936 | 6.2738 | 55.325 | 15.325 |
| C14 | 5800.0 | 5.3927 | 6.2738 | 55.327 | 15.327 |
| C15 | 5800.0 | 5.3921 | 6.2738 | 55.329 | 15.329 |
| C16 | 5800.0 | 5.3917 | 6.2738 | 55.330 | 15.330 |
| C17 | 5800.0 | 5.3914 | 6.2738 | 55.331 | 15.331 |
| C18 | 5800.0 | 5.3912 | 6.2738 | 55.332 | 15.332 |

# Pump requirements
Rack 86.524 kPa; system 86.524 kPa; hydraulic 180.26 W; electrical 300.43 W.

# Facility-loop compatibility
| Quantity | Value |
| --- | --- |
| FWS_return_C | 47.13213280558631 |
| FWS_supply_C | 36 |
| FWS_flow_LPM | 150 |
| FWS_deltaT_K | 11.13213280558631 |
| required_flow_LPM | 139.15059989265876 |
| entered_available_capacity_W | None |
| entered_UA_W_K | None |
| design_deltaT_K | 12.0 |
| minimum_hot_pinch_K | 0.0 |
| maximum_FWS_supply_C | 36 |
| required_UA_W_K | 23332.200475973157 |
| heat_balance_residual_W | -1.8917489796876907e-10 |
| TCS_capacity_rate_ratio | 1.0416666666666667 |
| rating_coolant | PG25 |
| approach_K | 4.0 |
| HX_available_W_per_rack | 121000.0 |
| effectiveness_required | 0.7671472571978837 |
| hot_end_pinch_K | 6.046105903842545 |
| model | Heuristic rating screen, not a capacity guarantee. maximum_FWS_supply_C is the nominal approach reference only; required flow is calorimetric, not a vendor control-flow limit. |
| aggregate_heat_W | 115560.0 |

# Uncertainty analysis
See uncertainty.csv and engineering_report.md for paired baseline/candidate draws, worst sampled outcomes and feasibility rates. A nominal pass alone does not establish robustness.

# Constraint margins
Enforced requirements: **PASS**. All screens including advisories: **FAIL**.
| Constraint | Margin | Units | Pass | Enforced | Basis |
| --- | --- | --- | --- | --- | --- |
| CDU_external_head | 28475.5 | Pa | True | False | Published nominal head point, not a measured pump envelope. |
| pump_curve | 24647.4 | Pa | True | False | Assumed shutoff parabola; manufacturer curve unavailable. |
| rack_flow | 5 | LPM | True | True | Physical condition or explicitly configured design requirement. |
| CDU_aggregate_flow | -5 | LPM | False | False | CDU121 nominal flow is not a verified maximum. |
| supply_temperature | 5 | K | True | True | Physical condition or explicitly configured design requirement. |
| return_temperature | 11.8218 | K | True | True | Physical condition or explicitly configured design requirement. |
| branch_outlet | 9.66825 | K | True | True | Physical condition or explicitly configured design requirement. |
| minimum_thermal_flow | 0.0355095 | kg/s | True | True | Physical condition or explicitly configured design requirement. |
| header_velocity | 1.15109 | m/s | True | True | Physical condition or explicitly configured design requirement. |
| minimum_diameter | 0.023 | m | True | True | Physical condition or explicitly configured design requirement. |
| maximum_diameter | 0.012 | m | True | True | Physical condition or explicitly configured design requirement. |
| HX_capacity | 5440 | W | True | False | Heuristic rating scaling, not a measured HX capacity map. |
| HX_approach | 0 | K | True | False | Published rating approach, not a universal minimum approach. |
| HX_cold_pinch | 3.9999 | K | True | True | Physical condition or explicitly configured design requirement. |
| HX_hot_pinch | 6.04601 | K | True | True | Physical condition or explicitly configured design requirement. |
| FWS_design_temperature_rise | 0.867867 | K | True | True | Physical condition or explicitly configured design requirement. |
| FWS_return | 12.8679 | K | True | True | Physical condition or explicitly configured design requirement. |
| chip_assumed_target | 0.668251 | K | True | False | Assumed resistance and 80°C design target; not a verified hardware limit. |

# Validation
| Check | Result |
| --- | --- |
| mass_relative_error | 0.0 |
| energy_relative_error | 2.5185038470693755e-16 |
| pressure_residual_Pa | 5.820766091346741e-11 |
| property_iterations | 11 |
| nfev | 377 |
| temperature_error_K | 6.865118245968915e-05 |
| flow_relative_error | 2.8695795363073627e-08 |
| converged | True |

# Improvement over baseline
The executed comparison is in engineering_report.md; no proprietary manifold comparison is implied.

# Limitations
This is an NVL72-class engineering model, not a reverse-engineered NVIDIA rack. Exact header dimensions/taper, cold-plate pressure curves, QDC Cv, internal tray plumbing, liquid heat-capture fraction, workload and installed pump curves are unavailable here. Component losses and PG25 property extensions require measurements for design qualification.

The header is a one-dimensional dissipative static-pressure network. It includes Darcy and configured junction losses but neglects recoverable axial kinetic-head redistribution and three-dimensional tee momentum effects. Diameter profiles are discretized into one segment per branch. Headers are adiabatic. Branch reduced K is fixed versus mass flow; viscosity dependence enters resolved tubing/headers, not an unmeasured cold-plate curve. This limitation is included in resistance uncertainty.

Resolved fluid volume includes headers and configured branch tubes; unmeasured QDC and reduced-model cold-plate inventory is excluded. Pressures are relative to the CDU return, not absolute pressure. No cavitation, boiling, transient control, corrosion or structural qualification is inferred. Final return mixing uses enthalpy. Flow in L/min is referenced to supply density; local return volume flow differs. The pressure budget is the mass-flow-weighted equivalent of complete branch paths, including signed buoyancy head, not a sum of parallel pressure drops. Pump power uses inlet volume flow and ignores small thermal expansion corrections and internal CDU overhead. Rated CDU power is separately recorded.

The pump parabola uses one published rating and an assumed shutoff; it is not a measured manufacturer curve. Fixed-flow operation assumes speed control/throttling is available. The HX screen derates its nominal capacity with approach and TCS heat-capacity rate and checks both terminal pinches and facility heat balance; this is not a vendor UA/performance map. XDU1350 is represented by identical parallel racks, not a solved row distribution network. Its temperature range is conservatively checked at both secondary ends.

The optional channel model predicts an equivalent tray-level chip temperature using assumed area and resistances, not 72 individual GPU temperatures. Local optimization success and global iteration-budget termination are reported separately; a feasible candidate is not a certified global optimum. Monte Carlo extrema cover the sampled parameter range only, and the assumed uniform distributions are not measured reliability probabilities.

# Conclusions
This candidate passes enforced requirements. Advisory screens and unverified hardware/site assumptions still require review.

# Chip estimates and qualification
Design screening only: unverified chip resistances, component losses, pump envelope, HX performance and site limits
| Tray | Component | Lower °C | Upper °C | Target margin K |
| --- | --- | --- | --- | --- |
| C01 | GPU | 67.01 | 79.01 | 0.99 |
| C01 | CPU | 65.01 | 75.01 | 4.99 |
| C02 | GPU | 67.05 | 79.05 | 0.95 |
| C02 | CPU | 65.05 | 75.05 | 4.95 |
| C03 | GPU | 67.08 | 79.08 | 0.92 |
| C03 | CPU | 65.08 | 75.08 | 4.92 |
| C04 | GPU | 67.11 | 79.11 | 0.89 |
| C04 | CPU | 65.11 | 75.11 | 4.89 |
| C05 | GPU | 67.13 | 79.13 | 0.87 |
| C05 | CPU | 65.13 | 75.13 | 4.87 |
| C06 | GPU | 67.15 | 79.15 | 0.85 |
| C06 | CPU | 65.15 | 75.15 | 4.85 |
| C07 | GPU | 67.17 | 79.17 | 0.83 |
| C07 | CPU | 65.17 | 75.17 | 4.83 |
| C08 | GPU | 67.19 | 79.19 | 0.81 |
| C08 | CPU | 65.19 | 75.19 | 4.81 |
| C09 | GPU | 67.21 | 79.21 | 0.79 |
| C09 | CPU | 65.21 | 75.21 | 4.79 |
| S01 | NVSwitch | 55.12 | 67.52 | 12.48 |
| S02 | NVSwitch | 55.13 | 67.53 | 12.47 |
| S03 | NVSwitch | 55.13 | 67.53 | 12.47 |
| S04 | NVSwitch | 55.14 | 67.54 | 12.46 |
| S05 | NVSwitch | 55.14 | 67.54 | 12.46 |
| S06 | NVSwitch | 55.14 | 67.54 | 12.46 |
| S07 | NVSwitch | 55.15 | 67.55 | 12.45 |
| S08 | NVSwitch | 55.15 | 67.55 | 12.45 |
| S09 | NVSwitch | 55.15 | 67.55 | 12.45 |
| C10 | GPU | 67.31 | 79.31 | 0.69 |
| C10 | CPU | 65.31 | 75.31 | 4.69 |
| C11 | GPU | 67.32 | 79.32 | 0.68 |
| C11 | CPU | 65.32 | 75.32 | 4.68 |
| C12 | GPU | 67.32 | 79.32 | 0.68 |
| C12 | CPU | 65.32 | 75.32 | 4.68 |
| C13 | GPU | 67.32 | 79.32 | 0.68 |
| C13 | CPU | 65.32 | 75.32 | 4.68 |
| C14 | GPU | 67.33 | 79.33 | 0.67 |
| C14 | CPU | 65.33 | 75.33 | 4.67 |
| C15 | GPU | 67.33 | 79.33 | 0.67 |
| C15 | CPU | 65.33 | 75.33 | 4.67 |
| C16 | GPU | 67.33 | 79.33 | 0.67 |
| C16 | CPU | 65.33 | 75.33 | 4.67 |
| C17 | GPU | 67.33 | 79.33 | 0.67 |
| C17 | CPU | 65.33 | 75.33 | 4.67 |
| C18 | GPU | 67.33 | 79.33 | 0.67 |
| C18 | CPU | 65.33 | 75.33 | 4.67 |

# Equation reference
## Heat load and mass balance
$$Q_{rack}=\sum_i Q_i,\quad \dot m=\rho(T_s)\dot V,\quad \sum_i\dot m_i=\dot m,\quad \dot m_{header,j}=\sum_{i\geq j}\dot m_i$$
Heat is component power × count × load fraction plus auxiliary power, or an entered tray heat load. Each header segment carries all downstream branches. L/min is converted to m³/s by dividing by 60,000.

## Energy and return mixing
$$h(T)=\int c_p(T)dT,\quad Q_i=\dot m_i[h(T_{out,i})-h(T_s)],\quad h(T_{mix})=\frac{\sum_i\dot m_i h(T_{out,i})}{\sum_i\dot m_i}$$
Temperature follows the inverse enthalpy function, preserving energy with temperature-dependent heat capacity. Q = mass flow × cp × temperature rise is the constant-cp approximation.

## Pressure and velocity
$$A=\pi D^2/4,\quad v=\dot m/(\rho A),\quad Re=\rho |v|D/\mu,\quad \Delta p=(fL/D+K)\rho v|v|/2,\quad \Delta p_{component}=K_h\dot m|\dot m|$$
Darcy friction uses 64/Re in laminar flow and Haaland in turbulent flow, blended from Re 2300 to 4000. Reduced component Kh has units Pa/(kg/s)²; fitting K is dimensionless.

## Friction and loop closure
$$f_{lam}=64/Re,\quad f_{turb}=\left[-1.8\log_{10}\left((\epsilon/(3.7D))^{1.11}+6.9/Re\right)\right]^{-2},\quad \Delta p_{loop,i}=\Delta p_{s,i}+\Delta p_{branch,i}+\Delta p_{r,i}$$
Every complete parallel path has the same required head. Header terms include signed rho g dz. Pump duty adds configured external piping/equipment; the reported budget weights complete paths by branch mass fraction.

## Individual tray orifices
$$\beta=d/D,\ A_o=\pi d^2/4,\quad \Delta p_{perm}=\frac{\dot m|\dot m|}{2\rho C_d^2 A_o^2}\left[\sqrt{1-\beta^4(1-C_d^2)}-C_d\beta^2\right]^2$$
Thin-plate incompressible permanent-loss approximation includes downstream recovery. Bore d must be smaller than branch ID D. Cd defaults to an assumed 0.62. Calibrate measured losses before machining. Manual bores add to configured restrictions; automatic equivalent sizing replaces the balancing restriction once.

## Automatic equivalent bore
$$z=\frac{\pi D^2}{4}\sqrt{2\rho K_h},\quad d=\frac{D}{[1+C_d^2(2z+z^2)]^{1/4}},\quad \Delta p=K_h\dot m^2$$
Exact algebraic inverse of the preceding permanent-loss model. Higher balancing Kh produces a smaller bore; zero Kh means no plate. Density is evaluated at each branch mean temperature. Export fixed bores before changing the operating point to evaluate the same manufactured design. This translates a chosen resistance; it does not independently optimize flow distribution.

## Pump curve and electricity
$$a=(\Delta p_0-\Delta p_{rated})/\dot V_{rated}^2,\quad \Delta p_{pump}=\Delta p_0 N^2-a\dot V_{aggregate}^2,\quad P_{hyd}=\Delta p_{system}\dot V_{rack},\quad P_{electric}=P_{hyd}/\eta$$
Shutoff head and efficiency are assumptions. Pump mode solves the intersection with system demand. Fixed-flow mode checks whether available head can support the requested flow. Electrical power is per-rack external hydraulic duty, excluding CDU overhead.

## Heat exchanger and facility water
$$Q_{aggregate}=n_{racks}Q_{rack}=\dot m_{FW}[h(T_{FW,out})-h(T_{FW,in})],\quad \dot m_{FW,required}=\frac{Q_{aggregate}}{h(T_{FW,allowed})-h(T_{FW,in})}$$
Allowed facility return is the minimum of supply + design rise, configured return ceiling, and secondary return minus required hot-end pinch. TCS supply − rated approach is a nominal reference, not a universal maximum facility supply. This duty excludes unmodeled pump heat and ambient heat gains.

## HX rating screen and required conductance
$$Q_{available}=Q_{rated}\max(0,\min(1,\Delta T_{cold}/\Delta T_{rated},C_{TCS}/C_{rated})),\quad UA_{required}=Q_{aggregate}/\Delta T_{lm},\quad \Delta T_{lm}=\frac{\Delta T_{hot}-\Delta T_{cold}}{\ln(\Delta T_{hot}/\Delta T_{cold})}$$
C = mass flow × cp; reference defaults to PG25 for CDU121 and water for XDU1350, at an assumed 40°C. Terminal differences are TCS supply − FWS supply and TCS return − FWS return. Equal positive differences use their common value. Required UA is a counterflow sizing estimate, not a measured HX map. Nonpositive pinches cannot support a finite positive UA. Rating scaling is advisory unless explicitly enforced.

## Chip-temperature interval
$$T_{j,low/high}=T_{tray,out}+Q_{chip}R_{j-c,low/high},\quad M_T=T_{target,max}-T_{j,high}$$
Conservative outlet coolant reference with assumed total junction-to-coolant resistance. Compute heat is split in proportion to configured GPU/CPU powers; switch heat is divided across two ASICs. Auxiliary/custom tray heat follows those same shares. The interval is an assumption envelope, not a confidence interval or a guaranteed optimal band. Resistance is not yet flow- or coolant-calibrated.

## Design score, volume and constraints
$$\dot m_i^*=\dot m Q_i/Q_{rack},\quad E=\sqrt{\mathrm{mean}[(\dot m_i/\dot m_i^*-1)^2]},\quad J=w_E E+w_T\Delta T_{spread}/T_0+w_p\Delta p/p_0+w_P P/P_0+w_V V/V_0,\quad V=\sum_j A_j\Delta z_j$$
Equal-flow targeting is also available. Zero-load branches are excluded from relative target error and reported separately. Lower J is better only after all constraints pass and boundary conditions/weights are comparable. Margin = limit − demand for upper limits; demand − limit for lower limits. Normalized margins divide by the configured scale. Volume term is both headers; resolved inventory adds branch tubes.
