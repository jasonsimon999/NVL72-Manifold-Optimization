# Network-balanced active control — October 18, 2026

Reproduce with `python studies/audit_network_control.py`. Exact inputs and all metrics are exported to `results/network_control_audit/`. The current reference is the user's fixed-page design: 120 L/min, compute Kh=0, switch Kh=180 million Pa/(kg/s)², frozen to physical bores once without per-tray reoptimization. Tests use a 300 s horizon, deterministic temperature measurements, the same demand-following pump for both designs, default 90 s actuators and all modeled actuator/body losses. No heat loads, hardware penalties or thermal limits are reduced to favor active control.

## What changed and why

The old controller assumed unchanged local pressure while iteratively correcting each orifice. The pump simultaneously changed pressure and the valves moved slowly. This could restrict a demanding path unnecessarily and make pump feedback compensate. The new controller evaluates the entire network at target flows with valves fully open, identifies the highest-pressure path, and adds resistance only to paths requiring less head. The orifice inverse, full hydraulic solver and conservative two-node thermal step remain shared with the fixed model.

The October 18 dimensionless orifice K refactor was algebraically equivalent to the previous law: it did not itself improve physical accuracy. Cd, thermal resistances, actuator characteristics and the pump curve still require calibration. The pump speed default is capped at 100%, replacing unsupported 120% overspeed.

## Earlier controller audit — superseded baseline

The numbers in this section describe the earlier per-tray-balanced reference. The current CSV and input JSON use the corrected two-class switch-180 reference; do not use the historical numbers as current outputs.

Current corrected reference results: at dt=.5 s the rack spike gives fixed/active auxiliary power 287.07/98.35 W and solid peaks 69.653/68.639°C. At dt=1 s, remove-three gives 376.29/389.80 W (fixed selected), reconnect-one 383.54/400.48 W (both fail a thermal screen), and spike-plus-service 282.68/97.37 W (active selected). Localized spikes give 287.01/96.09 W but active increases peak pressure, so the strict selector retains fixed. The passive design is identical in every case and no per-scenario resizing occurs. The old figures below are preserved only as historical context.

For the rack-wide compute pulse (30% to 100% at 100 s, lasting 40 s; switches stay at reference load), 0.5 s steps give:

| Metric | Fixed | Actual active |
|---|---:|---:|
| Average pump + valves + electronics | 289.07 W | 98.47 W |
| Peak equivalent solid temperature | 69.656°C | 68.629°C |
| Peak coolant outlet | 54.879°C | 54.866°C |
| Peak pump head | 111.899 kPa | 107.010 kPa |

Net auxiliary saving is about 65.9% over the entire 300 s scenario, not instantaneous full-load savings or whole-data-center energy savings. Both pass the entered thermal limits. Mean tray temperature can increase as excess coolant is removed. At 2/1/0.5 s the active average auxiliary power is 96.89/97.93/98.47 W, so the benefit persists under timestep refinement; residual time-discretization error remains.

Localized spikes can also save auxiliary energy, but greater peak head can fail the strict no-regression selector. Removal-only tests do not necessarily benefit: dripless QDs already stop removed-branch flow, and the fixed system also has variable pump speed. Reconnection can fail thermal screens for both designs with the assumed QD/power ramp. These failures remain visible. See the full CSV for all five scenarios, including combined servicing/spikes; do not report a fixed fallback as an active-control gain.

At 1 s steps, combined spike/individual servicing reduces auxiliary power from 284.67 to 97.45 W and peak solid temperature from 69.643 to 68.629°C; active is selected. Three-tray removal uses 376.07/389.15 W fixed/active, so fixed is retained. Single-tray reconnect uses 383.43/399.58 W and both fail a thermal screen. All 80 regression tests pass, including network sizing path closure, actuator rate, conservation, identical comparison inputs and Streamlit controls. The smaller-timestep check above establishes robustness only for the rack-wide spike, not every event schedule.

## Equations and evidence

- Continuity and equal pressure between common supply/return boundaries give the network balancing rule `H*=max L_open_i` and `k_i=k_open_i+(H*-L_open_i)/m_i^2`. This is a direct derivation for prescribed positive connected flows, subject to valve limits. Uncontrolled branches can prevent exact target balance.
- [Fluids permanent orifice-loss relationship](https://fluids.readthedocs.io/fluids.flow_meter.html#fluids.flow_meter.discharge_coefficient_to_K) provides the pressure-recovery law. Its documented K references upstream velocity; this model's displayed orifice K references bore velocity, differing by beta^4. The dimensional pressure drop is identical.
- [DOE variable-speed pumping guide](https://www1.eere.energy.gov/manufacturing/tech_assistance/pdfs/variable_speed_pumping.pdf) supports evaluating the coupled system curve and pump speed, rather than assuming savings from throttling alone.
- [Belimo LRB24-SR](https://www.belimo.com/us/shop/en_US/p?code=LRB24-SR) supports the example 90 s actuator stroke; it is not qualified NVL72 hardware. Lag, deadband and the effective area law are additional assumptions.
- Solid/coolant equations are first-law balances: `Cs dTs/dt=P-(Ts-Tf)/R` and `Cf dTf/dt=(Ts-Tf)/R-m cp(Tf-Tin)`. Their implicit-Euler sum is checked independently against stored plus removed heat.

The simulation remains a screening model with frozen hydraulic properties, maintained inlet temperature, constant efficiency and estimated tray thermal nodes. Numerical closure is not validation of actual hardware. No universal active-control advantage or optimality guarantee follows from these cases.
