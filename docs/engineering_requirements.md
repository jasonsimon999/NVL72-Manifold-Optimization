# Engineering requirements and decisions

Read `agent.md` in full before implementation. It is the retained primary specification.

- Architecture: 18 compute + 9 switch branches, spatially varying supply and return pressures, bottom-connected direct return. Elevations editable; C09 restored in the illustrative layout (the source schematic lists only 26 IDs).
- Primary load: 18 × 5800 + 9 × 1240 = 115560 W. NVIDIA power budgets are not measurements of simultaneous liquid heat capture; full capture is an explicit model assumption. Preserve nominal 102 kW and OEM 115 kW alternatives.
- PG25 validation: 40°C: 1020 kg/m³, 4120 J/kg/K, 1.47 mPa·s, 0.476 W/m/K; 50°C: 1015, 4130, 1.15. Additional property points must carry provenance.
- Boundary: CDU121 121 kW at 4 K / 120 LPM / 115 kPa external available head. In-row XDU1350: aggregate 1368 kW / 1200 LPM / 244 kPa for two pumps. Never apply aggregate flow to one rack or add internal CDU pressure losses twice.
- GF 232 kPa technical-loop fractions are a reference, not rack component measurements. Reduced resistances are transparent calibration assumptions, not proof of CDU compatibility of actual hardware.
- Numerics: eliminate header mass balances algebraically, solve all branch loop equations and total flow simultaneously. Iterate local temperatures/properties. Enthalpy-integral thermal balances avoid inconsistent variable-cp mixing.
- Unknown geometry, cold-plate/QDC curves, pump shutoff, branch plumbing and facility conditions are configurable. Pump curve inferred from one rating plus assumed shutoff; HX rating scaling is screening only.
- Validation gates: analytic pipe/parallel networks; mass, energy, pressure closure; monotonic sanity; gravity; pump intersection. Optimize only after these pass.
- Compare designs A–E, deterministic sweeps, bounded local/global optimization, Pareto points, paired uncertainty and faults. Report infeasibility visibly and never silently select an infeasible optimum.
- Modules: config/units/coolant/components/manifold/hydraulics/thermal/solver; cdu/facility/coldplate; objectives/optimize/scenarios/uncertainty; plotting/reporting/CLI/dashboard.
