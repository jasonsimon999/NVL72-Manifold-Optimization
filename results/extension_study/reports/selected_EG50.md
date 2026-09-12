# Design C: constant headers / two restrictions

# Configuration
```yaml
name: 'Design C: constant headers / two restrictions'
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
  flow_LPM: 120
  supply_C: 40
  operating_mode: fixed_flow
  gravity_enabled: true
  gravity_m_s2: 9.80665
coolant:
  type: EG50
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
    restriction_K: 180528785.87842363
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
| power.switch_rack_total_W | 11160 | NVIDIA | switch |
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
| M_flow | 1.077947 |
| CV_flow | 0.501482 |
| M_thermal | 0.01538268 |
| RMS_target_error | 0.004964035 |
| max_abs_target_error | 0.009668133 |
| zero_load_flow_fraction | 0 |
| T_out_max_C | 56.08861 |
| T_out_min_C | 55.84543 |
| outlet_spread_K | 0.2431848 |
| rack_dp_Pa | 114726 |
| system_dp_Pa | 114726 |
| rack_flow_LPM | 120 |
| heat_W | 115560 |
| T_return_C | 55.99725 |
| rack_deltaT_K | 15.99725 |
| pump_hydraulic_W | 229.452 |
| pump_electrical_W | 382.42 |
| header_volume_m3 | 0.004082814 |
| min_header_ID_m | 0.038 |
| max_header_ID_m | 0.038 |
| max_header_velocity_m_s | 1.779378 |
| resolved_fluid_volume_m3 | 0.005694451 |
| minimum_normalized_margin | -0.1033465 |
| T_junction_upper_max_C | 80.08861 |

# Optimized results
See engineering_report.md for the executed baseline-versus-candidate study.

# Pressure-drop breakdown
| Component | Pa | kPa | % equivalent system head |
| --- | --- | --- | --- |
| coldplates | 57732.96 | 57.733 | 50.32 |
| qdcs | 23971.23 | 23.971 | 20.89 |
| tubing | 11687.84 | 11.688 | 10.19 |
| fittings | 8210.43 | 8.210 | 7.16 |
| valves | 586.46 | 0.586 | 0.51 |
| restrictions | 9212.48 | 9.212 | 8.03 |
| orifices | 0.00 | 0.000 | 0.00 |
| header_friction | 883.08 | 0.883 | 0.77 |
| header_minor | 2354.50 | 2.355 | 2.05 |
| hydrostatic_net | 87.03 | 0.087 | 0.08 |
| external_piping | 0.00 | 0.000 | 0.00 |
| external_fittings | 0.00 | 0.000 | 0.00 |
| external_equipment | 0.00 | 0.000 | 0.00 |

# Thermal distribution
| Tray | Heat W | Actual LPM | Target LPM | Outlet °C | Rise K |
| --- | --- | --- | --- | --- | --- |
| C01 | 5800.0 | 6.0811 | 6.0228 | 55.845 | 15.845 |
| C02 | 5800.0 | 6.0712 | 6.0228 | 55.871 | 15.871 |
| C03 | 5800.0 | 6.0623 | 6.0228 | 55.894 | 15.894 |
| C04 | 5800.0 | 6.0543 | 6.0228 | 55.915 | 15.915 |
| C05 | 5800.0 | 6.0471 | 6.0228 | 55.934 | 15.934 |
| C06 | 5800.0 | 6.0408 | 6.0228 | 55.950 | 15.950 |
| C07 | 5800.0 | 6.0352 | 6.0228 | 55.965 | 15.965 |
| C08 | 5800.0 | 6.0303 | 6.0228 | 55.978 | 15.978 |
| C09 | 5800.0 | 6.0262 | 6.0228 | 55.989 | 15.989 |
| S01 | 1240.0 | 1.2953 | 1.2876 | 55.903 | 15.903 |
| S02 | 1240.0 | 1.2946 | 1.2876 | 55.912 | 15.912 |
| S03 | 1240.0 | 1.2939 | 1.2876 | 55.921 | 15.921 |
| S04 | 1240.0 | 1.2932 | 1.2876 | 55.929 | 15.929 |
| S05 | 1240.0 | 1.2926 | 1.2876 | 55.937 | 15.937 |
| S06 | 1240.0 | 1.2919 | 1.2876 | 55.945 | 15.945 |
| S07 | 1240.0 | 1.2913 | 1.2876 | 55.952 | 15.952 |
| S08 | 1240.0 | 1.2908 | 1.2876 | 55.959 | 15.959 |
| S09 | 1240.0 | 1.2902 | 1.2876 | 55.966 | 15.966 |
| C10 | 5800.0 | 5.9959 | 6.0228 | 56.069 | 16.069 |
| C11 | 5800.0 | 5.9938 | 6.0228 | 56.074 | 16.074 |
| C12 | 5800.0 | 5.9922 | 6.0228 | 56.078 | 16.078 |
| C13 | 5800.0 | 5.9909 | 6.0228 | 56.082 | 16.082 |
| C14 | 5800.0 | 5.9900 | 6.0228 | 56.084 | 16.084 |
| C15 | 5800.0 | 5.9893 | 6.0228 | 56.086 | 16.086 |
| C16 | 5800.0 | 5.9888 | 6.0228 | 56.087 | 16.087 |
| C17 | 5800.0 | 5.9885 | 6.0228 | 56.088 | 16.088 |
| C18 | 5800.0 | 5.9883 | 6.0228 | 56.089 | 16.089 |

# Pump requirements
Rack 114.726 kPa; system 114.726 kPa; hydraulic 229.45 W; electrical 382.42 W.

# Facility-loop compatibility
| Quantity | Value |
| --- | --- |
| FWS_return_C | 47.13213280558631 |
| FWS_supply_C | 36 |
| FWS_flow_LPM | 150 |
| FWS_deltaT_K | 11.13213280558631 |
| required_flow_LPM | 139.15059989265876 |
| design_deltaT_K | 12.0 |
| minimum_hot_pinch_K | 0.0 |
| maximum_FWS_supply_C | 36 |
| required_UA_W_K | 18903.16126243477 |
| heat_balance_residual_W | -1.8917489796876907e-10 |
| TCS_capacity_rate_ratio | 0.8516948672187322 |
| rating_coolant | PG25 |
| approach_K | 4.0 |
| HX_available_W_per_rack | 103055.0789334666 |
| effectiveness_required | 0.7999724904146848 |
| hot_end_pinch_K | 8.865116614218778 |
| model | conservative rating scaling by cold-end approach and TCS capacity rate; no vendor UA map |
| aggregate_heat_W | 115560.0 |

# Uncertainty analysis
See uncertainty.csv and engineering_report.md for paired baseline/candidate draws, worst sampled outcomes and feasibility rates. A nominal pass alone does not establish robustness.

# Constraint margins
Overall: **FAIL**
| Constraint | Margin | Units | Pass |
| --- | --- | --- | --- |
| CDU_external_head | 273.992 | Pa | True |
| pump_curve | 273.992 | Pa | True |
| rack_flow | 10 | LPM | True |
| CDU_aggregate_flow | 0 | LPM | True |
| supply_temperature | 5 | K | True |
| return_temperature | 9.00275 | K | True |
| branch_outlet | 8.91139 | K | True |
| minimum_thermal_flow | 0.00834942 | kg/s | True |
| header_velocity | 1.22062 | m/s | True |
| minimum_diameter | 0.023 | m | True |
| maximum_diameter | 0.012 | m | True |
| HX_capacity | -12504.9 | W | False |
| HX_approach | 0 | K | True |
| HX_hot_pinch | 8.86512 | K | True |
| FWS_design_temperature_rise | 0.867867 | K | True |
| FWS_return | 12.8679 | K | True |
| chip_assumed_target | -0.0886134 | K | False |

# Validation
| Check | Result |
| --- | --- |
| mass_relative_error | 2.0851020736497105e-16 |
| energy_relative_error | 2.5185038470693755e-16 |
| pressure_residual_Pa | 4.3655745685100555e-11 |
| property_iterations | 12 |
| nfev | 559 |
| temperature_error_K | 5.338453951253541e-05 |
| flow_relative_error | 7.708792160617072e-09 |
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
This design violates one or more configured constraints and must not be presented as acceptable.

# Chip estimates and qualification
Unverified chip thermal model and hardware limits; EG50 CDU/material compatibility unverified
| Tray | Component | Lower °C | Upper °C | Target margin K |
| --- | --- | --- | --- | --- |
| C01 | GPU | 67.85 | 79.85 | 0.15 |
| C01 | CPU | 65.85 | 75.85 | 4.15 |
| C02 | GPU | 67.87 | 79.87 | 0.13 |
| C02 | CPU | 65.87 | 75.87 | 4.13 |
| C03 | GPU | 67.89 | 79.89 | 0.11 |
| C03 | CPU | 65.89 | 75.89 | 4.11 |
| C04 | GPU | 67.92 | 79.92 | 0.08 |
| C04 | CPU | 65.92 | 75.92 | 4.08 |
| C05 | GPU | 67.93 | 79.93 | 0.07 |
| C05 | CPU | 65.93 | 75.93 | 4.07 |
| C06 | GPU | 67.95 | 79.95 | 0.05 |
| C06 | CPU | 65.95 | 75.95 | 4.05 |
| C07 | GPU | 67.96 | 79.96 | 0.04 |
| C07 | CPU | 65.96 | 75.96 | 4.04 |
| C08 | GPU | 67.98 | 79.98 | 0.02 |
| C08 | CPU | 65.98 | 75.98 | 4.02 |
| C09 | GPU | 67.99 | 79.99 | 0.01 |
| C09 | CPU | 65.99 | 75.99 | 4.01 |
| S01 | NVSwitch | 65.2 | 77.6 | 2.4 |
| S02 | NVSwitch | 65.21 | 77.61 | 2.39 |
| S03 | NVSwitch | 65.22 | 77.62 | 2.38 |
| S04 | NVSwitch | 65.23 | 77.63 | 2.37 |
| S05 | NVSwitch | 65.24 | 77.64 | 2.36 |
| S06 | NVSwitch | 65.24 | 77.64 | 2.36 |
| S07 | NVSwitch | 65.25 | 77.65 | 2.35 |
| S08 | NVSwitch | 65.26 | 77.66 | 2.34 |
| S09 | NVSwitch | 65.27 | 77.67 | 2.33 |
| C10 | GPU | 68.07 | 80.07 | -0.07 |
| C10 | CPU | 66.07 | 76.07 | 3.93 |
| C11 | GPU | 68.07 | 80.07 | -0.07 |
| C11 | CPU | 66.07 | 76.07 | 3.93 |
| C12 | GPU | 68.08 | 80.08 | -0.08 |
| C12 | CPU | 66.08 | 76.08 | 3.92 |
| C13 | GPU | 68.08 | 80.08 | -0.08 |
| C13 | CPU | 66.08 | 76.08 | 3.92 |
| C14 | GPU | 68.08 | 80.08 | -0.08 |
| C14 | CPU | 66.08 | 76.08 | 3.92 |
| C15 | GPU | 68.09 | 80.09 | -0.09 |
| C15 | CPU | 66.09 | 76.09 | 3.91 |
| C16 | GPU | 68.09 | 80.09 | -0.09 |
| C16 | CPU | 66.09 | 76.09 | 3.91 |
| C17 | GPU | 68.09 | 80.09 | -0.09 |
| C17 | CPU | 66.09 | 76.09 | 3.91 |
| C18 | GPU | 68.09 | 80.09 | -0.09 |
| C18 | CPU | 66.09 | 76.09 | 3.91 |

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
Thin-plate incompressible permanent-loss approximation includes downstream recovery. Bore d must be smaller than branch ID D. Cd defaults to an assumed 0.62. Small rack tubes are not claimed to meet ISO metering geometry or Reynolds requirements; calibrate measured losses before machining. These losses ADD to existing restrictions.

## Pump curve and electricity
$$a=(\Delta p_0-\Delta p_{rated})/\dot V_{rated}^2,\quad \Delta p_{pump}=\Delta p_0 N^2-a\dot V_{aggregate}^2,\quad P_{hyd}=\Delta p_{system}\dot V_{rack},\quad P_{electric}=P_{hyd}/\eta$$
Shutoff head and efficiency are assumptions. Pump mode solves the intersection with system demand. Fixed-flow mode checks whether available head can support the requested flow. Electrical power is per-rack external hydraulic duty, excluding CDU overhead.

## Heat exchanger and facility water
$$Q_{aggregate}=n_{racks}Q_{rack}=\dot m_{FW}[h(T_{FW,out})-h(T_{FW,in})],\quad \dot m_{FW,required}=\frac{Q_{aggregate}}{h(T_{FW,allowed})-h(T_{FW,in})}$$
Allowed facility return is the minimum of supply + design rise, configured return ceiling, and secondary return minus required hot-end pinch. Maximum facility supply = TCS supply − CDU approach. This duty excludes unmodeled pump heat and ambient heat gains.

## HX rating screen and required conductance
$$Q_{available}=Q_{rated}\max(0,\min(1,\Delta T_{cold}/\Delta T_{rated},C_{TCS}/C_{rated})),\quad UA_{required}=Q_{aggregate}/\Delta T_{lm},\quad \Delta T_{lm}=\frac{\Delta T_{hot}-\Delta T_{cold}}{\ln(\Delta T_{hot}/\Delta T_{cold})}$$
C = mass flow × cp, referenced to PG25 at 40°C unless configured otherwise. Terminal differences are TCS supply − FWS supply and TCS return − FWS return. Equal positive differences use their common value. Required UA is a counterflow sizing estimate, not a measured HX map. Nonpositive pinches cannot support a finite positive UA.

## Chip-temperature interval
$$T_{j,low/high}=T_{tray,out}+Q_{chip}R_{j-c,low/high},\quad M_T=T_{target,max}-T_{j,high}$$
Conservative outlet coolant reference with assumed total junction-to-coolant resistance. Compute heat is split in proportion to configured GPU/CPU powers; switch heat is divided across two ASICs. Auxiliary/custom tray heat follows those same shares. The interval is an assumption envelope, not a confidence interval or a guaranteed optimal band. Resistance is not yet flow- or coolant-calibrated.

## Design score, volume and constraints
$$\dot m_i^*=\dot m Q_i/Q_{rack},\quad E=\sqrt{\mathrm{mean}[(\dot m_i/\dot m_i^*-1)^2]},\quad J=w_E E+w_T\Delta T_{spread}/T_0+w_p\Delta p/p_0+w_P P/P_0+w_V V/V_0,\quad V=\sum_j A_j\Delta z_j$$
Equal-flow targeting is also available. Zero-load branches are excluded from relative target error and reported separately. Lower J is better only after all constraints pass and boundary conditions/weights are comparable. Margin = limit − demand for upper limits; demand − limit for lower limits. Normalized margins divide by the configured scale. Volume term is both headers; resolved inventory adds branch tubes.
