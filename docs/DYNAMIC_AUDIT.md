# Active-orifice calculation audit — 2026-09-22

## What was checked

Both designs use the same generated electrical heat, liquid-capture fractions, service connection histories, time samples, thermal targets, inlet temperature, coolant properties and initial thermal state. Runtime assertions enforce array equality. Passive bores are frozen before the transient; another assertion rejects any bore drift. The active trial is shown independently of the selected design so a passive fallback cannot hide active performance.

The fixed design is solved at each time step against the pump curve with its original bores. It therefore has changing flows and temperatures during heat spikes and servicing, despite constant bores. Active hardware replaces balancing plates, retaining the pipe/QD/cold-plate losses and adding explicit valve-body loss. A stationary valve is not assumed to eliminate this loss or its holding electricity.

## Calculation corrections

- Shared thermal demand now follows `Ts = Tin + P/(m cp) + R P`: allowed coolant rise is the minimum of the user rise, outlet ceiling minus inlet, and controller setpoint minus inlet minus RP. Nonpositive available rise is flagged as unreachable at finite flow; the original coolant-rise target remains a finite fallback, not a claim of feasibility.
- Adaptive sizing uses `K_new = K_current (m_actual/m_target)^2`, then the exact inverse permanent-orifice-loss equation already used in the hydraulic network. Temperature above the setpoint adds bounded proportional demand trim. This is local feedback with finite actuator lag/rate and a coupled re-solve, not a proof of global optimality.
- Overlapping preset and individual service procedures combine connection fractions by minimum, then scale heat once. The earlier code could multiply the same power ramp twice.
- Initial hydraulic conditions respect trays disconnected at t=0.
- Exported stored heat is independently computed from changes in solid and coolant temperatures, instead of reconstructed from power minus removal.
- Per-tray peak temperatures and time above limit now exclude detached trays, consistent with rack-level thermal screening.
- The fixed temperature solution was checked against its analytic steady equilibrium; the sizing inverse against the exact pressure-loss law; and full transient storage independently against `Cs ΔTs/dt + Cf ΔTf/dt`.

## Reproduced results

Run `python studies/audit_dynamic.py` from the project root. Reference: location-balanced fixed geometry, PG25, 40°C inlet, 300-second runs, 2-second timestep, deterministic zero sensor noise, demand-following pump, adaptive sizing, and default actuator/thermal assumptions. The combined service case removes C01 at 80 s and S02 at 120 s; reconnects at 180/220 s with 20-second ramps; the compute heat pulse is 100–140 s.

Positive temperature reduction means active is cooler. These are **raw active trials**, not the passive fallback.

| Scenario | Fixed peak °C | Active peak °C | Peak reduction K | Mean reduction K | Fixed auxiliary W | Active auxiliary W |
|---|---:|---:|---:|---:|---:|---:|
| Steady | 76.949 | 76.949 | 0.000 | -0.638 | 655.59 | 669.96 |
| Rack spike | 69.432 | 69.553 | -0.121 | -1.457 | 323.03 | 313.18 |
| Local spike | 69.432 | 69.558 | -0.127 | -2.015 | 323.03 | 280.69 |
| Heterogeneous | 76.949 | 76.949 | 0.000 | -1.170 | 655.59 | 650.32 |
| Spike + servicing | 69.418 | 69.339 | +0.079 | -1.438 | 318.18 | 317.61 |

No run exceeded the entered solid temperature limit. Across these cases, maximum pressure closure residual was approximately 0.00014 Pa and maximum per-tray energy residual was 1.74e-10 W. All fixed/active input histories matched exactly and fixed bores remained constant. The full test suite passed 77 tests.

**Finding:** the sizing law is internally consistent, but the tested active system is not universally thermally better. It often exchanges excess cooling for lower power. The service case has a slightly lower peak but a warmer mean; these are different objectives. The selection rule retained fixed hardware in all five cases. A small peak difference is not validated hardware improvement; timestep sensitivity and experimental calibration are necessary before relying on it.

## Timestep sensitivity

The combined service/spike case was repeated at 2, 1 and 0.5 seconds (`results/dynamic_audit/timestep_refinement.csv`). Peak reductions were 0.079, 0.118 and 0.111 K, respectively; mean temperatures remained approximately 1.43 K warmer with active control. At 0.5 seconds, fixed auxiliary power was 318.89 W versus active 329.73 W. Thus the tiny apparent 2-second power saving does not survive refinement. The 1- and 0.5-second peak benefits differ by 0.0074 K; this is encouraging numerical agreement, not a hardware validation or a full convergence proof. Use smaller timesteps when judging small controller benefits.

## Diagrams and exact samples

`results/dynamic_audit/applied_heat.png` shows fixed and active total electrical/liquid inputs and all-tray liquid heat maps. `fixed_active_bores.png` uses a shared mm color scale, with detached trays gray. `tray_C01.png` overlays exact sampled heat, bore and temperature. `service_spike_samples.csv` contains every fixed/active tray sample; `service_spike.json` retains full results. The app renders the corresponding diagrams for the currently selected simulation.

## Limits of this audit

The transient uses frozen hydraulic properties and inlet cp, two lumped thermal nodes, constant thermal resistance, a prescribed inlet, an assumed pump curve/efficiency, and an effective-area valve approximation. This audit verifies their equations and implementation, not their fit to NVIDIA hardware. The original steady page uses a different temperature-dependent property iteration; its temperatures need not match this approximation exactly. Pressure, mass and energy closure establish numerical consistency, not component qualification. Implicit Euler uses right-endpoint forcing, so events are resolved on the timestep; plotted load steps follow that convention. Startup thermal states are shared to avoid bias, not independently equilibrated for each active valve state.
