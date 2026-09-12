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
  type: water
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
| M_flow | 1.081751 |
| CV_flow | 0.503339 |
| M_thermal | 0.01760679 |
| RMS_target_error | 0.005294119 |
| max_abs_target_error | 0.01054666 |
| zero_load_flow_fraction | 0 |
| T_out_max_C | 54.03253 |
| T_out_min_C | 53.78845 |
| outlet_spread_K | 0.2440784 |
| rack_dp_Pa | 98271.46 |
| system_dp_Pa | 98271.46 |
| rack_flow_LPM | 120 |
| heat_W | 115560 |
| T_return_C | 53.93382 |
| rack_deltaT_K | 13.93382 |
| pump_hydraulic_W | 196.5429 |
| pump_electrical_W | 327.5715 |
| header_volume_m3 | 0.004082814 |
| min_header_ID_m | 0.038 |
| max_header_ID_m | 0.038 |
| max_header_velocity_m_s | 1.774251 |
| resolved_fluid_volume_m3 | 0.005694451 |
| minimum_normalized_margin | 0 |
| T_junction_upper_max_C | 77.99873 |

# Optimized results
See engineering_report.md for the executed baseline-versus-candidate study.

# Pressure-drop breakdown
| Component | Pa | kPa | % equivalent system head |
| --- | --- | --- | --- |
| coldplates | 50240.18 | 50.240 | 51.12 |
| qdcs | 20864.52 | 20.865 | 21.23 |
| tubing | 8293.91 | 8.294 | 8.44 |
| fittings | 7656.56 | 7.657 | 7.79 |
| valves | 546.90 | 0.547 | 0.56 |
| restrictions | 7782.96 | 7.783 | 7.92 |
| orifices | 0.00 | 0.000 | 0.00 |
| header_friction | 641.20 | 0.641 | 0.65 |
| header_minor | 2190.14 | 2.190 | 2.23 |
| hydrostatic_net | 55.10 | 0.055 | 0.06 |
| external_piping | 0.00 | 0.000 | 0.00 |
| external_fittings | 0.00 | 0.000 | 0.00 |
| external_equipment | 0.00 | 0.000 | 0.00 |

# Thermal distribution
| Tray | Heat W | Actual LPM | Target LPM | Outlet °C | Rise K |
| --- | --- | --- | --- | --- | --- |
| C01 | 5800.0 | 6.0864 | 6.0228 | 53.788 | 13.788 |
| C02 | 5800.0 | 6.0765 | 6.0228 | 53.811 | 13.811 |
| C03 | 5800.0 | 6.0675 | 6.0228 | 53.831 | 13.831 |
| C04 | 5800.0 | 6.0595 | 6.0228 | 53.850 | 13.850 |
| C05 | 5800.0 | 6.0524 | 6.0228 | 53.866 | 13.866 |
| C06 | 5800.0 | 6.0461 | 6.0228 | 53.880 | 13.880 |
| C07 | 5800.0 | 6.0405 | 6.0228 | 53.893 | 13.893 |
| C08 | 5800.0 | 6.0357 | 6.0228 | 53.904 | 13.904 |
| C09 | 5800.0 | 6.0316 | 6.0228 | 53.914 | 13.914 |
| S01 | 1240.0 | 1.2836 | 1.2876 | 53.978 | 13.978 |
| S02 | 1240.0 | 1.2829 | 1.2876 | 53.986 | 13.986 |
| S03 | 1240.0 | 1.2822 | 1.2876 | 53.993 | 13.993 |
| S04 | 1240.0 | 1.2815 | 1.2876 | 54.000 | 14.000 |
| S05 | 1240.0 | 1.2809 | 1.2876 | 54.007 | 14.007 |
| S06 | 1240.0 | 1.2803 | 1.2876 | 54.014 | 14.014 |
| S07 | 1240.0 | 1.2797 | 1.2876 | 54.020 | 14.020 |
| S08 | 1240.0 | 1.2791 | 1.2876 | 54.027 | 14.027 |
| S09 | 1240.0 | 1.2786 | 1.2876 | 54.033 | 14.033 |
| C10 | 5800.0 | 6.0020 | 6.0228 | 53.982 | 13.982 |
| C11 | 5800.0 | 6.0000 | 6.0228 | 53.987 | 13.987 |
| C12 | 5800.0 | 5.9984 | 6.0228 | 53.991 | 13.991 |
| C13 | 5800.0 | 5.9972 | 6.0228 | 53.993 | 13.993 |
| C14 | 5800.0 | 5.9964 | 6.0228 | 53.995 | 13.995 |
| C15 | 5800.0 | 5.9957 | 6.0228 | 53.997 | 13.997 |
| C16 | 5800.0 | 5.9953 | 6.0228 | 53.998 | 13.998 |
| C17 | 5800.0 | 5.9951 | 6.0228 | 53.998 | 13.998 |
| C18 | 5800.0 | 5.9949 | 6.0228 | 53.999 | 13.999 |

# Pump requirements
Rack 98.271 kPa; system 98.271 kPa; hydraulic 196.54 W; electrical 327.57 W.

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
| required_UA_W_K | 21896.82712613286 |
| heat_balance_residual_W | -1.8917489796876907e-10 |
| TCS_capacity_rate_ratio | 0.986593866975245 |
| rating_coolant | PG25 |
| approach_K | 4.0 |
| HX_available_W_per_rack | 119377.85790400465 |
| effectiveness_required | 0.7769881552136321 |
| hot_end_pinch_K | 6.801689101730631 |
| model | conservative rating scaling by cold-end approach and TCS capacity rate; no vendor UA map |
| aggregate_heat_W | 115560.0 |

# Uncertainty analysis
See uncertainty.csv and engineering_report.md for paired baseline/candidate draws, worst sampled outcomes and feasibility rates. A nominal pass alone does not establish robustness.

# Constraint margins
Overall: **PASS**
| Constraint | Margin | Units | Pass |
| --- | --- | --- | --- |
| CDU_external_head | 16728.5 | Pa | True |
| pump_curve | 16728.5 | Pa | True |
| rack_flow | 10 | LPM | True |
| CDU_aggregate_flow | 0 | LPM | True |
| supply_temperature | 5 | K | True |
| return_temperature | 11.0662 | K | True |
| branch_outlet | 10.9675 | K | True |
| minimum_thermal_flow | 0.00928016 | kg/s | True |
| header_velocity | 1.22575 | m/s | True |
| minimum_diameter | 0.023 | m | True |
| maximum_diameter | 0.012 | m | True |
| HX_capacity | 3817.86 | W | True |
| HX_approach | 0 | K | True |
| HX_hot_pinch | 6.80169 | K | True |
| FWS_design_temperature_rise | 0.867867 | K | True |
| FWS_return | 12.8679 | K | True |
| chip_assumed_target | 2.00127 | K | True |

# Validation
| Check | Result |
| --- | --- |
| mass_relative_error | 0.0 |
| energy_relative_error | 2.5185038470693755e-16 |
| pressure_residual_Pa | 4.3655745685100555e-11 |
| property_iterations | 12 |
| nfev | 436 |
| temperature_error_K | 4.7141285733687255e-05 |
| flow_relative_error | 8.125638836281905e-09 |
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
This candidate passes the configured nominal engineering screen.

# Chip estimates and qualification
Unverified chip thermal model and hardware limits
| Tray | Component | Lower °C | Upper °C | Target margin K |
| --- | --- | --- | --- | --- |
| C01 | GPU | 65.79 | 77.79 | 2.21 |
| C01 | CPU | 63.79 | 73.79 | 6.21 |
| C02 | GPU | 65.81 | 77.81 | 2.19 |
| C02 | CPU | 63.81 | 73.81 | 6.19 |
| C03 | GPU | 65.83 | 77.83 | 2.17 |
| C03 | CPU | 63.83 | 73.83 | 6.17 |
| C04 | GPU | 65.85 | 77.85 | 2.15 |
| C04 | CPU | 63.85 | 73.85 | 6.15 |
| C05 | GPU | 65.87 | 77.87 | 2.13 |
| C05 | CPU | 63.87 | 73.87 | 6.13 |
| C06 | GPU | 65.88 | 77.88 | 2.12 |
| C06 | CPU | 63.88 | 73.88 | 6.12 |
| C07 | GPU | 65.89 | 77.89 | 2.11 |
| C07 | CPU | 63.89 | 73.89 | 6.11 |
| C08 | GPU | 65.9 | 77.9 | 2.1 |
| C08 | CPU | 63.9 | 73.9 | 6.1 |
| C09 | GPU | 65.91 | 77.91 | 2.09 |
| C09 | CPU | 63.91 | 73.91 | 6.09 |
| S01 | NVSwitch | 63.28 | 75.68 | 4.32 |
| S02 | NVSwitch | 63.29 | 75.69 | 4.31 |
| S03 | NVSwitch | 63.29 | 75.69 | 4.31 |
| S04 | NVSwitch | 63.3 | 75.7 | 4.3 |
| S05 | NVSwitch | 63.31 | 75.71 | 4.29 |
| S06 | NVSwitch | 63.31 | 75.71 | 4.29 |
| S07 | NVSwitch | 63.32 | 75.72 | 4.28 |
| S08 | NVSwitch | 63.33 | 75.73 | 4.27 |
| S09 | NVSwitch | 63.33 | 75.73 | 4.27 |
| C10 | GPU | 65.98 | 77.98 | 2.02 |
| C10 | CPU | 63.98 | 73.98 | 6.02 |
| C11 | GPU | 65.99 | 77.99 | 2.01 |
| C11 | CPU | 63.99 | 73.99 | 6.01 |
| C12 | GPU | 65.99 | 77.99 | 2.01 |
| C12 | CPU | 63.99 | 73.99 | 6.01 |
| C13 | GPU | 65.99 | 77.99 | 2.01 |
| C13 | CPU | 63.99 | 73.99 | 6.01 |
| C14 | GPU | 66.0 | 78.0 | 2.0 |
| C14 | CPU | 64.0 | 74.0 | 6.0 |
| C15 | GPU | 66.0 | 78.0 | 2.0 |
| C15 | CPU | 64.0 | 74.0 | 6.0 |
| C16 | GPU | 66.0 | 78.0 | 2.0 |
| C16 | CPU | 64.0 | 74.0 | 6.0 |
| C17 | GPU | 66.0 | 78.0 | 2.0 |
| C17 | CPU | 64.0 | 74.0 | 6.0 |
| C18 | GPU | 66.0 | 78.0 | 2.0 |
| C18 | CPU | 64.0 | 74.0 | 6.0 |

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
