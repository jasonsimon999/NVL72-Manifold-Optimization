# Model audit — 13 September 2026

The equations and implemented conservation checks have been reviewed. This is a design-screening model with public reference data and substantial unmeasured inputs. It cannot verify the installed manifold, CDU or facility without their specifications or measurements. Passing enforced requirements is **not** a statement that all hardware limits have been verified.

## What changed

1. Automatic equivalent orifices convert each entered balancing resistance to a bore at the solved branch mean density. They replace that resistance once. Exported fixed bores allow off-design testing of the same hardware.
2. Results distinguish **enforced requirements**, **advisory screens**, and numerical failure. All individual margins remain visible. The strict checkbox enforces provisional screens too; YAML can set `constraint_policy.enforce_assumptions: true` or override individual checks with `constraint_policy.enforced`.
3. Facility flow has no arbitrary upper UI limit. Supply temperature, return allowance, number of racks, available cooling duty and evaluated HX conductance are independent controls. Unknown capacity/UA remains unknown, not unlimited or verified.
4. A versioned `PG25_Dow2023` fluid option exposes the discrepancy between the retained legacy PG25 assumptions and a published manufacturer table.
5. In-row HX rating calculations now default to water as the secondary reference fluid, matching the XDU1350 guide. The rating reference temperature remains an assumption.

## Automatic bore calculation and accuracy

The balancing coefficient has units Pa/(kg/s)². It is **not** dimensionless fitting K, and it is separate from the cold-plate and QD coefficients. For a positive branch mass flow, its pressure loss is `Δp = Kh × m²`.

With branch internal diameter D, density ρ, and discharge coefficient Cd, the exact inverse of the implemented thin-plate permanent-loss formula is:

`z = (πD²/4) √(2ρKh)`

`d = D / [1 + Cd²(2z + z²)]^(1/4)`

Larger Kh gives a smaller bore. Kh = 0 means no plate. For each tray the table reports Kh, bore, Cd, reference density and permanent pressure loss. The forward and inverse equations are tested across diameters, densities, Cd and resistance values, and against a complete coupled network solve.

This is accurate **within the assumed hydraulic law**. Cd = 0.62 is a provisional sharp-edged thin-plate estimate. Plate thickness, edge shape, beta ratio, Reynolds number, nearby bends and pressure recovery can change actual loss. It is not a calibrated machining specification. A QD's connection designation is not an orifice diameter or a flow curve. The branch IDs of 8 and 6 mm remain assumptions.

Automatic mode redesigns the bores at each operating point. To evaluate manufactured hardware, download the fixed-orifice YAML, then change its load, flow or temperature and run it. Do not use automatically redesigned bores as evidence of fixed-hardware robustness. Changing a class restriction translates your choice; it does not itself find the optimum. The existing optimizer and analytical location-balancing routine choose resistance values separately.

## Inputs and evidence

| Input group | Current values / treatment | Audit conclusion |
|---|---|---|
| Architecture | 18 compute trays, 9 switch trays, 4 GPUs + 2 CPUs per compute tray | NVL72 reference architecture. Actual elevations, ordering and equal spacing over 1.8 m are assumptions. |
| Compute heat | 1,200 W/GPU, 500 W/CPU; 5,800 W/tray; 104.4 kW across compute trays | NVIDIA's GB200 power-budget example supports the combined compute budget. Converting all of it to liquid heat and splitting CPU power equally are assumptions. Electrical budgets are not measured coolant loads. |
| Switch heat | 11,160 W total; 1,240 W/tray; two equal ASIC heat shares | Retained prior source value, **not independently reverified in this audit**. Actual switch/auxiliary liquid capture requires confirmation. |
| Total heat | 115.56 kW at full entered load; auxiliary defaults zero | Arithmetic verified. Excludes other air-cooled loads and unmodeled pump/ambient heat. This is not whole-building cooling duty. |
| Operating point | Rack 120 L/min, 40°C; gravity 9.80665 m/s² | Selected reference point, not a universal requirement. Supply-density reference is used for reported L/min. |
| Headers | Constant 38 mm ID, 1.8 m high, roughness 1.5 µm | Geometry assumptions. At 120 L/min, inlet velocity is about 1.76 m/s. A plausible trial size, not a verified NVIDIA dimension or AN-08 bore. Taper endpoints follow flow direction. |
| Branch tubing | Compute 8 mm × 1.5 m; switch 6 mm × 1 m | Unmeasured equivalent plumbing. Tube multipliers initially 1. |
| Branch reduced losses | Compute cold plate/QD: 5.5/2.3 million; switch: 20/5 million Pa/(kg/s)² | Assumed quadratic coefficients. Need pressure–flow curves for the complete installed paths, including both QD halves/pairs as appropriate. |
| Fittings | Header tee/entrance/exit/reducer/expansion: .08/.2/.2/.05/.05; branch tee/entrance/exit/bend/fittings/valve/orifice: 1/.5/1/1.2/.5/.3/0 | Dimensionless assumed loss coefficients, not measured component data. Header momentum recovery and 3D tee effects are omitted. |
| External loop | Off in baseline; optional 12 m, 40 mm ID, minor K = 8, equipment Kh = 3,000 | Equivalent assumptions; row distribution is not independently solved. |
| Water properties | Existing IAPWS-derived table at 0.1 MPa | Temperature interpolation and enthalpy integration checked. Pressure dependence is not modeled. |
| PG25 properties | Legacy table retained; versioned Dow table selectable | Legacy cp at 40°C is 4,120 J/kg/K; the 2023 Dow LC25 table gives 3,920. Do not merge formulations or assume either identifies the installed fluid. Versioned interpolation is limited to −5–80°C. |
| EG50 | Dow SR-1 proxy, 50% ethylene glycol by volume | Physical-property study option, not confirmed CDU/material compatibility. Fluid composition and inhibitor package matter. |
| CDU121 | Nominal 121 kW at 4 K approach; 120 L/min at 115 kPa; AC rated electrical input 875 W | Nominal rating points verified. They do not establish a complete maximum-flow, pump or HX envelope. Assumed shutoff 160 kPa and efficiency .6 are unverified. Rated unit electricity differs from modeled external hydraulic duty. |
| XDU1350 | Nominal 1,368 kW; two-pump secondary flow 1,200 L/min at 244 kPa; 13.7 kW nominal unit power | Guide also reports higher capacity at a different approach and a separate three-pump configuration. Do not mix those ratings. Eight identical racks is a model assumption; 330 kPa shutoff is assumed. |
| Facility | Baseline water 36°C, 150 L/min per CDU, 12 K design rise, 60°C return ceiling | All are site assumptions. Enter available flow at this CDU, not total building flow. A larger building plant does not guarantee more pressure/flow through the CDU. |
| Chip temperature | GPU R .01–.02; CPU .02–.04; switch .015–.035 K/W; target 80°C | Assumed junction-to-outlet-coolant intervals. No verified optimum band, throttling threshold or calibrated flow dependence. Entered manufacturer limits are enforced but predictions remain uncertain. |
| Optional channel model | 100 channels, 1×1 mm, 80 mm length; area .03 m²; three resistances .0002 K/W; laminar Nu 4.36 | Assumed equivalent channel geometry; disabled by default. Postprocessing is not coupled back to hydraulic cold-plate resistance. |
| Numerical settings | Pressure .05 Pa; mass/energy relative 1e−8; temperature 1e−4 K; flow relative 1e−6; relaxation .65; 60 property iterations; 200 function evaluations | Numerical convergence settings, not hardware accuracy. Conservation does not validate uncertain inputs. |
| Optimization | Heat-proportional target; weighted flow error, temperature spread, pressure, power and header volume | User preference weights/normalizations and search bounds, not physics. Lowest score only compares matching objectives/boundaries. No proof of global optimum. |
| Uncertainty / display | Seeded uniform ranges, sample/iteration budgets and plot DPI | Exploration choices. Sample pass fractions are not measured reliability probabilities. Older exported results retain their historical constraint policy. |

All resolved baseline input values, including nested solver/optimization/uncertainty controls, are exported in `results/audit/resolved_input_inventory.json`. Earlier per-input provenance remains in `data/sources.yaml`; this audit supersedes earlier claims where nominal ratings were treated as universal limits.

## Constraint policy

| Checks | Default treatment | Meaning |
|---|---|---|
| Positive hot and cold HX terminal differences | Always enforced | A passive finite-UA exchanger cannot produce the requested state with zero or negative terminal differences. The 0.0001 K numerical guard is not an engineering design margin. |
| Rack flow 130 L/min, supply 45°C, mixed return 65°C | Enforced reference requirements, editable | QCT reference envelope; applicability to the installed rack must be confirmed. The published flow figure is a reference need, not proof of an absolute hardware maximum. |
| Every tray outlet 65°C and corresponding minimum thermal flow | Enforced conservative requirements | Extends the return limit to each tray. These checks partly duplicate one another by energy balance. |
| Header velocity 3 m/s, ID 15–50 mm | Enforced design choices | Not vendor guarantees. Optimization uses its own narrower search bounds. |
| Facility design rise and return ceiling | Enforced entered requirements | Site choices; increase only to match actual infrastructure. |
| Entered facility duty, entered HX UA, entered chip manufacturer ceiling | Enforced when supplied | Explicit design inputs; absent values are unknown. UA comparison assumes counterflow and the entered operating-point conductance. |
| CDU121 nominal aggregate flow, nominal head, assumed pump curve | Advisory | Exceeding these requires an actual operating envelope, not an automatic claim of infeasibility or feasibility. Pump operating mode still solves its assumed curve. |
| XDU1350 two-pump 1,200 L/min aggregate flow | Enforced | Published maximum for this selected configuration. It is divided across the served racks. |
| Heuristic HX capacity and 4 K rating approach | Advisory | Nominal rating conditions are not a measured performance map or universal minimum approach. |
| Assumed 80°C chip target | Advisory | Useful design preference, not a verified chip limit. Strict mode can enforce it. |
| XDU1350 10–52°C secondary range applied to both ends | Advisory | The correct inlet/return/control boundary needs confirmation before this conservative check is treated as a hard installed-system limit. |

## Facility calculations and the previous failures

Facility return follows `Qaggregate = mFW × [h(return) − h(supply)]`. Required flow is calculated from the allowed return temperature. Required counterflow UA follows `Qaggregate / LMTD`. More facility flow reduces its temperature rise and often reduces required UA. It does not directly increase secondary rack flow. The existing nominal-capacity heuristic remains explicitly advisory; a validated vendor map is still needed to predict actual capacity at a new operating point.

The reproduced audit shows:

| Case | Enforced requirements | Advisory issue / physical result |
|---|---|---|
| Original 120 L/min reference | Pass | All current screens pass; this remains unqualified hardware. |
| 110 L/min | Pass | Heuristic HX capacity and assumed chip target fail; estimated upper chip temperature 81.42°C. |
| 125 L/min | Pass | Exceeds CDU121 nominal flow; maximum deliverable flow is not established. |
| 32 mm headers | Pass | Assumed chip target exceeded by about 0.075 K, far smaller than uncalibrated thermal uncertainty. |
| Rack supply 35°C, facility supply 36°C | Fail | Physically impossible cold-end temperature ordering for this passive liquid-to-liquid model. |
| Versioned PG25 at reference conditions | Pass | Maximum outlet 56.71°C versus 55.97°C with legacy properties; assumed upper chip estimate 80.71°C. |
| Hypothetical facility flow 300 L/min | Pass | Facility return falls from 47.13 to 41.57°C; required UA falls from 22.27 to 15.75 kW/K. This is not a verified site specification. |

See `results/audit/comparison.csv` and individual JSON/reports for complete margins. Reproduce with `PYTHONPATH=src .venv/bin/python studies/audit_study.py` from the repository root.

## What still needs real data

The highest-value missing inputs are installed QD part numbers and pressure–flow curves; branch and header measured IDs; cold-plate hydraulic and junction-to-coolant curves; actual liquid-captured loads; chip thermal limits; CDU pump/HX maps with fluid and control conditions; and facility supply temperature, available differential pressure, allocated flow and cooling duty at this CDU. Until those are supplied, the model supports comparisons and sensitivity studies, not final machining or equipment qualification.

## Sources checked

- [NVIDIA GB200/GB300 power-budget FAQ](https://docs.nvidia.com/mission-control/docs/systems-administration-guide/2.2.0/prs/faq.html): compute power-budget example, not measured liquid heat.
- [NVIDIA DGX GB200 hardware](https://docs.nvidia.com/dgx/dgxgb200-user-guide/hardware.html): reference architecture.
- [QCT cooling reference](https://blog.qct.io/wp-content/uploads/2025/04/QCT-Qoolrack-Stand-Alone_Advanced-Liquid-Cooling-for-NVIDIA-GB200-NVL72-Systems.pdf): reference rack operating envelope.
- [Vertiv CDU121 datasheet](https://www.vertiv.com/4a1be9/globalassets/shared/vertiv-coolchip-cdu-100_datasheet_en.pdf): nominal conditions.
- [Vertiv XDU1350 application guide](https://www.vertiv.com/4a1b3f/globalassets/products/thermal-management/high-density-solutions/liebert-xdu1350-coolant-distribution-unit-application-and-planning-guide-sl-70618.pdf): ratings, configuration differences and facility-flow control cautions. Excess primary flow is not automatically beneficial to control stability.
- [Dow LC25 manufacturer sheet, Form 180-01627-01-0523, hosted by ChemPoint](https://www.chempoint.com/products/download?doctype=tds&documentid=0103000121118930771670&grade=74883&language=English): versioned property profile.
- [Dow SR-1 archived manufacturer sheet](https://users.obs.carnegiescience.edu/crane/pfs/man/Misc/Dowtherm-SR-1.pdf): EG50 proxy properties.
