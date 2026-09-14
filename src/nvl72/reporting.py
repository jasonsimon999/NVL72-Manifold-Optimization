"""Strict JSON/CSV exports and traceable Markdown engineering reports."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import yaml
from .config import ROOT, portable_config

def native(value):
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,np.generic):return value.item()
    if isinstance(value,dict):return {k:native(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [native(v) for v in value]
    return value

def export(result,directory='results',name='baseline',figures=True):
    directory=Path(directory)
    for sub in ('tables','reports','figures'): (directory/sub).mkdir(parents=True,exist_ok=True)
    (directory/f'{name}.json').write_text(json.dumps(native(result),indent=2,allow_nan=False))
    if result.get('fixed_orifice_config'):
        (directory/f'{name}_fixed_orifices.yaml').write_text(yaml.safe_dump(portable_config(result['fixed_orifice_config']),sort_keys=False))
    pd.DataFrame(result['trays']).to_csv(directory/'tables'/f'{name}_trays.csv',index=False)
    if 'chip_estimates' in result:
        from .design_analysis import design_summary
        pd.DataFrame(result['chip_estimates']).to_csv(directory/'tables'/f'{name}_chips.csv',index=False)
        pd.DataFrame(design_summary({name:result})).to_csv(directory/'tables'/f'{name}_design_summary.csv',index=False)
    pd.DataFrame([dict(component=k,Pa=v,kPa=v/1000,percent=100*v/result['metrics']['system_dp_Pa']) for k,v in result['pressure_budget_Pa'].items()]).to_csv(directory/'tables'/f'{name}_pressure_budget.csv',index=False)
    if figures:
        from .plotting import result_figures
        result_figures(result,directory/'figures',name)
    write_report(result,directory/'reports'/f'{name}.md',name)

def table(headers,rows):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(str(v) for v in row)+' |' for row in rows)+'\n'

def comparison(a,b):
    keys=[('Maximum tray outlet [°C]','T_out_max_C'),('Outlet spread [K]','outlet_spread_K'),
          ('RMS thermal-flow error','RMS_target_error'),('Maximum target-flow error','max_abs_target_error'),
          ('Rack pressure drop [Pa]','rack_dp_Pa'),('System pressure drop [Pa]','system_dp_Pa'),
          ('Rack flow [L/min]','rack_flow_LPM'),('Pump hydraulic power [W]','pump_hydraulic_W'),
          ('Pump electrical power [W]','pump_electrical_W'),('Header volume [m³]','header_volume_m3'),
          ('Minimum normalized constraint margin','minimum_normalized_margin')]
    return [{'metric':label,'baseline':a['metrics'][key],'candidate':b['metrics'][key],
             'candidate_minus_baseline':b['metrics'][key]-a['metrics'][key]} for label,key in keys]

LIMITATIONS='''This is an NVL72-class engineering model, not a reverse-engineered NVIDIA rack. Exact header dimensions/taper, cold-plate pressure curves, QDC Cv, internal tray plumbing, liquid heat-capture fraction, workload and installed pump curves are unavailable here. Component losses and PG25 property extensions require measurements for design qualification.

The header is a one-dimensional dissipative static-pressure network. It includes Darcy and configured junction losses but neglects recoverable axial kinetic-head redistribution and three-dimensional tee momentum effects. Diameter profiles are discretized into one segment per branch. Headers are adiabatic. Branch reduced K is fixed versus mass flow; viscosity dependence enters resolved tubing/headers, not an unmeasured cold-plate curve. This limitation is included in resistance uncertainty.

Resolved fluid volume includes headers and configured branch tubes; unmeasured QDC and reduced-model cold-plate inventory is excluded. Pressures are relative to the CDU return, not absolute pressure. No cavitation, boiling, transient control, corrosion or structural qualification is inferred. Final return mixing uses enthalpy. Flow in L/min is referenced to supply density; local return volume flow differs. The pressure budget is the mass-flow-weighted equivalent of complete branch paths, including signed buoyancy head, not a sum of parallel pressure drops. Pump power uses inlet volume flow and ignores small thermal expansion corrections and internal CDU overhead. Rated CDU power is separately recorded.

The pump parabola uses one published rating and an assumed shutoff; it is not a measured manufacturer curve. Fixed-flow operation assumes speed control/throttling is available. The HX screen derates its nominal capacity with approach and TCS heat-capacity rate and checks both terminal pinches and facility heat balance; this is not a vendor UA/performance map. XDU1350 is represented by identical parallel racks, not a solved row distribution network. Its temperature range is conservatively checked at both secondary ends.

The optional channel model predicts an equivalent tray-level chip temperature using assumed area and resistances, not 72 individual GPU temperatures. Local optimization success and global iteration-budget termination are reported separately; a feasible candidate is not a certified global optimum. Monte Carlo extrema cover the sampled parameter range only, and the assumed uniform distributions are not measured reliability probabilities.'''

def write_report(r,path,prefix='baseline'):
    m=r['metrics'];source=yaml.safe_load((ROOT/'data/sources.yaml').read_text())['defaults']
    published=[(k,v['value'],v['category'],v['source']) for k,v in source.items() if v['category']!='ASSUMPTION' and not isinstance(v['value'],dict)]
    sections=[f'# {r["config"]["name"]}\n', '# Configuration\n```yaml\n'+yaml.safe_dump(r['config'],sort_keys=False)+'```\n',
      '# Source data\nThe retained `agent.md` is the primary source specification. Full categories, URLs, alternatives and every default are in `data/sources.yaml`.\n'+table(['Input','Value','Category','Source'],published),
      '# Assumptions\nAll geometry, branch K values, minor-loss coefficients, pump shutoff, pump efficiency, facility conditions and workload capture factors are editable assumptions. PG25 40/50°C anchors are retained; other points are modeled extensions. The C09 omission in the source schematic is corrected to retain 27 trays.\n',
      '# Baseline architecture\nConstant 38 mm supply and return headers; direct return to bottom CDU ports; 18 compute and 9 switch paths, two resistance classes and no location balancing. This baseline is not claimed to be NVIDIA’s actual design.\n',
      '# Hydraulic equations\n`m_header[j] = sum(m_branch[j:])`; `Re = rho V D / mu`; `dp = (f L/D + K) rho V|V|/2`; `dp_component = K_hyd m|m|`. All branch loops and total rack flow solve simultaneously. Gravity enters each header as `rho g dz`; warm-return density leaves a small buoyancy term. Laminar f=64/Re; turbulent Haaland with continuous transition 2300–4000.\n',
      '# Thermal equations\n`h(T)=integral cp(T)dT`; `h_out = h_supply + Q/m`; `h_mix = sum(m h)/sum(m)`. The code analytically inverts the piecewise-linear cp integral. This is the variable-property extension of Q=m cp ΔT.\n',
      '# CDU model\n`dp_pump(q,N) = dp_shutoff N² - a q²`, with a fixed from the nominal point. `P_h=dp q`, `P_e=P_h/eta`. External head boundary excludes internal CDU losses.\n',
      '# Baseline results / current design\n'+table(['Metric','Value'],[(k,f'{v:.7g}') for k,v in m.items()]),
      '# Optimized results\n'+(json.dumps(r['optimization'],indent=2) if 'optimization' in r else 'See engineering_report.md for the executed baseline-versus-candidate study.')+'\n',
      '# Pressure-drop breakdown\n'+table(['Component','Pa','kPa','% equivalent system head'],[(k,f'{v:.2f}',f'{v/1000:.3f}',f'{100*v/m["system_dp_Pa"]:.2f}') for k,v in r['pressure_budget_Pa'].items()]),
      f'![Pressure budget](../figures/{prefix}_pressure_budget.png)\n',
      '# Thermal distribution\n'+table(['Tray','Heat W','Actual LPM','Target LPM','Outlet °C','Rise K'],[(t['tray_id'],t['heat_load_W'],f'{t["actual_flow_LPM"]:.4f}',f'{t["target_flow_LPM"]:.4f}',f'{t["T_out_C"]:.3f}',f'{t["deltaT_C"]:.3f}') for t in r['trays']]),
      f'![Thermal target](../figures/{prefix}_target_comparison.png)\n',
      '# Pump requirements\n'+f'Rack {m["rack_dp_Pa"]/1000:.3f} kPa; system {m["system_dp_Pa"]/1000:.3f} kPa; hydraulic {m["pump_hydraulic_W"]:.2f} W; electrical {m["pump_electrical_W"]:.2f} W.\n',
      '# Facility-loop compatibility\n'+table(['Quantity','Value'],r['facility'].items()),
      '# Uncertainty analysis\nSee uncertainty.csv and engineering_report.md for paired baseline/candidate draws, worst sampled outcomes and feasibility rates. A nominal pass alone does not establish robustness.\n',
      '# Constraint margins\n'+f'Enforced requirements: **{"PASS" if r["feasible"] else "FAIL"}**. All screens including advisories: **{"PASS" if r.get("screening_pass",all(v["pass"] for v in r["constraints"].values())) else "FAIL"}**.\n'+table(['Constraint','Margin','Units','Pass','Enforced','Basis'],[(k,f'{v["margin"]:.6g}',v['units'],v['pass'],v.get('enforced',True),v.get('basis','Historical result: original enforcement policy retained.')) for k,v in r['constraints'].items()]),
      '# Validation\n'+table(['Check','Result'],r['validation'].items()),
      '# Improvement over baseline\nThe executed comparison is in engineering_report.md; no proprietary manifold comparison is implied.\n',
      '# Limitations\n'+LIMITATIONS+'\n',
      '# Conclusions\n'+('This candidate passes enforced requirements. Advisory screens and unverified hardware/site assumptions still require review.' if r['feasible'] else 'This design violates one or more enforced requirements.')+'\n']
    import re
    sections=[section for section in sections if not section.startswith('![') or all((Path(path).parent/link).exists() for link in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',section))]
    Path(path).write_text('\n'.join(sections))
    if 'chip_estimates' in r:
        from .equations import EQUATIONS
        with Path(path).open('a') as out:
            out.write('\n# Chip estimates and qualification\n'+r['qualification']+'\n')
            out.write(table(['Tray','Component','Lower °C','Upper °C','Target margin K'],[(x['tray_id'],x['component'],round(x['junction_low_C'],2),round(x['junction_high_C'],2),round(x['target_margin_K'],2)) for x in r['chip_estimates']]))
            out.write('\n# Equation reference\n'+'\n'.join('## '+title+'\n$$'+formula+'$$\n'+description+'\n' for title,formula,description in EQUATIONS))
