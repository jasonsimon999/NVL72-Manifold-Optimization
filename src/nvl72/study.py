"""End-to-end repeatable study and final comparison report."""
from copy import deepcopy
from pathlib import Path
import json
import numpy as np
import pandas as pd
import yaml
from .solver import solve
from .optimize import optimize,balance_locations
from .reporting import export,comparison,table,LIMITATIONS,native
from .plotting import comparison_figures,sweep_figures,pareto_figures
from .sweep import sweep,set_parameter
from .uncertainty import uncertainty
from .scenarios import scenario
from .objectives import pareto_mask


def run_study(c,output='results',samples=32,reuse=False):
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    for p in ('tables','reports','figures'): (out/p).mkdir(exist_ok=True)
    base=solve(c);export(base,out,'baseline');print('Baseline validated',flush=True)
    sweep_rows=[]
    for parameter,values in [('header_diameter_mm',np.linspace(25,50,11)),('rack_flow_LPM',np.linspace(90,130,9)),('taper_ratio',np.linspace(.6,1,9)),('compute_restriction_K',np.linspace(0,2e7,9)),('switch_restriction_K',np.linspace(0,2e8,11)),('supply_C',np.linspace(25,45,9))]:
        sweep_rows+=sweep(c,parameter,values)
    sweeps=pd.DataFrame(sweep_rows);sweeps.to_csv(out/'tables/sweeps.csv',index=False);sweep_figures(sweeps,out/'figures');print('Six parameter sweeps complete',flush=True)
    designs={'baseline':base};archives=[]
    if reuse and (out/'optimized.json').exists():
        designs['D']=json.loads((out/('design_D.json' if (out/'design_D.json').exists() else 'optimized.json')).read_text())
        if (out/'tables/optimization_archive.csv').exists():archives.extend(pd.read_csv(out/'tables/optimization_archive.csv').to_dict('records'))
    else:
        designs['D'],rows=optimize(c,'D','global');archives+=rows
    for label in 'ABC':
        designs[label],rows=optimize(c,label,'local');archives+=rows
        export(designs[label],out,'design_'+label,figures=False)
        print(f'Design {label} complete: RMS={designs[label]["metrics"]["RMS_target_error"]:.5f}',flush=True)
    designs['E']=balance_locations(designs['D']['config'])
    export(designs['E'],out,'design_E',figures=False)
    # Low-flow alternative explicitly trades thermal rise for more head margin.
    margin=deepcopy(designs['D']['config']);margin['rack']['flow_LPM']=116.;margin['name']='D116: two-class candidate at 116 LPM'
    designs['D116']=solve(margin)
    export(designs['D116'],out,'design_D116',figures=False)
    selected=designs['C'];export(designs['D'],out,'design_D',figures=False);export(selected,out,'optimized');comparison_figures(base,selected,out/'figures')
    for label,r in designs.items():archives.append(dict(r['metrics'],feasible=r['feasible'],design=label))
    archive=pd.DataFrame(archives).drop_duplicates();archive.to_csv(out/'tables/optimization_archive.csv',index=False)
    eligible=archive[archive.feasible].copy()
    for x in ('pump_electrical_W','header_volume_m3'):
        mask=pareto_mask(eligible[[x,'RMS_target_error']].to_numpy());eligible[mask].to_csv(out/'tables'/f'pareto_{x}.csv',index=False)
    pareto_figures(archive,out/'figures')
    unc=pd.DataFrame(uncertainty({k:designs[k]['config'] for k in ('baseline','C','D','E')},samples))
    unc.to_csv(out/'tables/uncertainty.csv',index=False)
    hardware=pd.DataFrame(uncertainty({k:designs[k]['config'] for k in ('baseline','C','D','E','D116')},samples,operating_variation=False))
    hardware.to_csv(out/'tables/hardware_uncertainty.csv',index=False)
    print('Paired uncertainty complete',flush=True)
    scenarios=['full','compute75','compute50','nonuniform','switch_heavy','near_zero','blocked','degraded_qdc','double_resistance','compute_removed','switch_removed','pump_reduced','pump_unavailable','warm_coolant','warm_facility','nominal102','OEM115']
    faults=[]
    for label in ('baseline','C','D116'):
        for name in scenarios:
            row={'design':label,'scenario':name}
            try:
                r=solve(scenario(designs[label]['config'],name));row.update(r['metrics'],feasible=r['feasible'],error=None,
                    failed_constraints=', '.join(k for k,v in r['constraints'].items() if not v['pass']))
            except (ValueError,RuntimeError) as exc:row.update(feasible=False,error=str(exc))
            faults.append(row)
    fault_frame=pd.DataFrame(faults);fault_frame.to_csv(out/'tables/faults_workloads.csv',index=False)
    gravity=[]
    for label in ('baseline','D'):
        d=deepcopy(designs[label]['config']);d['rack']['gravity_enabled']=False;r=solve(d)
        gravity.append({'design':label,'head_with_gravity_Pa':designs[label]['metrics']['rack_dp_Pa'],'head_without_gravity_Pa':r['metrics']['rack_dp_Pa'],
                        'max_flow_change_LPM':float(np.max(np.abs(np.array([t['actual_flow_LPM'] for t in r['trays']])-np.array([t['actual_flow_LPM'] for t in designs[label]['trays']]))))})
    pd.DataFrame(gravity).to_csv(out/'tables/gravity.csv',index=False)
    # Compare broad-loop reference fractions; this is a diagnostic, not calibration.
    reference={'coldplates':52.,'qdcs':22.2,'tubing':12.5,'external_equipment':7.7,'fittings':2.9,'external_piping':1.9,'valves':1.,'header_friction':.14}
    gf=[{'component':k,'GF_reference_percent':v,'baseline_equivalent_percent':100*base['pressure_budget_Pa'].get(k,0)/base['metrics']['system_dp_Pa']} for k,v in reference.items()]
    pd.DataFrame(gf).to_csv(out/'tables/GF_reference_comparison.csv',index=False)
    comparison_rows=comparison(base,selected);pd.DataFrame(comparison_rows).to_csv(out/'tables/baseline_vs_optimized.csv',index=False)
    ranking=[]
    for label,r in designs.items():
        coeff=[r['config']['branches']['overrides'].get(t['tray_id'],{}).get('restriction_K',r['config']['branches'][t['tray_type']]['restriction_K']) for t in r['trays']]
        ranking.append({'design':label,**r['metrics'],'unique_restrictions':len(set(round(x,2) for x in coeff)),
                        'header_profiles':r['config']['geometry']['supply']['profile']+'/'+r['config']['geometry']['return']['profile'],'feasible':r['feasible']})
    pd.DataFrame(ranking).to_csv(out/'tables/design_ranking.csv',index=False)
    cfg_export=deepcopy(selected['config']);cfg_export['coolant']['property_file']='data/coolant_properties.csv'
    (Path('config')/'optimized_example.yaml').write_text(yaml.safe_dump(native(cfg_export),sort_keys=False))
    generate_summary(out,designs,unc,fault_frame,gravity,comparison_rows,hardware)
    print('Study complete: '+str(out/'reports/engineering_report.md'),flush=True)
    return designs


def generate_summary(out,designs,unc,faults,gravity,comparisons,hardware):
    a=designs['baseline']['metrics'];b=designs['C']['metrics'];e=designs['E']['metrics']
    summary=f'''# NVL72-class manifold engineering study

Under the modeled 115.56 kW primary liquid load, the constant 38 mm reference headers at {a['rack_flow_LPM']:.2f} LPM give {100*a['RMS_target_error']:.2f}% RMS heat-proportional flow error and {a['T_out_max_C']:.3f}°C maximum tray outlet. The preferred constant-header two-class candidate at {b['rack_flow_LPM']:.3f} LPM gives {100*b['RMS_target_error']:.3f}% error and {b['T_out_max_C']:.3f}°C maximum outlet. This is a {100*(1-b['RMS_target_error']/a['RMS_target_error']):.2f}% error reduction and {a['T_out_max_C']-b['T_out_max_C']:.3f} K peak-outlet reduction.

This improvement costs pressure and energy: {a['rack_dp_Pa']/1000:.3f} → {b['rack_dp_Pa']/1000:.3f} kPa and {a['pump_electrical_W']:.2f} → {b['pump_electrical_W']:.2f} W modeled electrical pump power. The candidate passes the nominal configured CDU screen with {(115000-b['system_dp_Pa'])/1000:.3f} kPa external head reserve. It is a nominal thermal-distribution improvement, not an unconditional energy or robustness improvement.

# Configuration and source data

Full resolved inputs are in `baseline.json` and `optimized.json`. Additional source checks and remaining data gaps are recorded in `docs/public_source_followup.md`. `agent.md` is retained unchanged. `data/sources.yaml` records every baseline input, evidence category, source URLs, conflicting envelopes and estimates. The 115.56 kW reference is derived from NVIDIA component power budgets; the 102 kW nominal and 115 kW OEM cases are evaluated separately. Primary silicon power is assumed fully captured by liquid.

# Assumptions and baseline architecture

The baseline has 27 branches (C01–C18, S01–S09), assumed elevations over 1.8 m, two constant 38 mm headers and class-specific estimated cold-plate/QDC losses. Branch dimensions, resistance coefficients and minor losses are not proprietary NVIDIA data. All rack branches are solved simultaneously. The source's illustrative omission of C09 is corrected.

# Hydraulic and thermal equations

Each direct-return loop satisfies `H = branch loss + cumulative supply loss + cumulative return loss + cumulative (rho_supply-rho_return) g dz`. Supply and return segment mass flows follow exact continuity. Darcy–Weisbach uses local rho and mu with laminar/Haaland friction; configured fittings add K rho V²/2. Enthalpy integration conserves branch heat and return mixing with variable cp. The return mixes from top to bottom. Supply heat gain is neglected.

# CDU model and facility-loop compatibility

The CDU121 screen uses 121 kW at 4 K approach, 120 LPM and 115 kPa external head. A quadratic pump curve passes through that rated point and an assumed 160 kPa shutoff. The 120 LPM rating is conservatively used as an aggregate flow screen; QCT's 130 LPM rack envelope remains a separate constraint. Required electrical power excludes CDU internal losses and controls. FWS is water at 36°C and 150 LPM; the candidate TCS return is {b['T_return_C']:.3f}°C. HX screening and pinch margins are listed in the detailed report.

# Baseline versus optimized results

'''
    summary+=table(['Metric','Baseline','Candidate','Candidate − baseline'],[(r['metric'],f"{r['baseline']:.6g}",f"{r['candidate']:.6g}",f"{r['candidate_minus_baseline']:+.6g}") for r in comparisons])
    summary+='\n![Flow comparison](../figures/comparison_flow.png)\n\n![Temperature comparison](../figures/comparison_temperature.png)\n'
    summary+='\n# Physical explanation\n\nThe switch heat load is only 1.24/5.8 of the compute heat, but its baseline hydraulic resistance does not produce the required 4.68:1 compute/switch mass-flow ratio. Switches are overfed and compute trays underfed relative to equal coolant rise. Added switch restriction redistributes flow to compute trays, raising required head. Larger/tapered headers adjust smaller position-dependent errors; they cannot alone correct this load mismatch. Raw flow CV increases as thermal allocation improves, which is expected for unequal loads.\n'
    summary+='\n# Design comparison and practical selection\n'+table(['Design','RMS error %','Max outlet °C','Head kPa','Pump W','Header L','Nominal feasible'],[(name,f"{r['metrics']['RMS_target_error']*100:.5f}",f"{r['metrics']['T_out_max_C']:.3f}",f"{r['metrics']['system_dp_Pa']/1000:.3f}",f"{r['metrics']['pump_electrical_W']:.2f}",f"{r['metrics']['header_volume_m3']*1000:.3f}",r['feasible']) for name,r in designs.items()])
    summary+=f"\nDesign A optimizes one constant diameter; B optimizes the two header tapers; C uses two restriction classes with fixed baseline headers; D combines geometry, restrictions and flow. E uses the minimum-head nonnegative location restrictions for exact targets at D geometry, verified by the full solver. It is not a global geometry optimum.\n\nThe preferred two-class C design's simplification penalty relative to E is {b['T_out_max_C']-e['T_out_max_C']:.4f} K maximum outlet and {100*(b['RMS_target_error']-e['RMS_target_error']):.4f} percentage points RMS error. E requires many distinct restriction settings. C is preferred over the searched D because it uses simpler constant headers and achieves lower thermal error and pump power, at the cost of slightly more header volume. The low-flow D116 alternative increases head reserve but raises coolant temperature. These alternatives are shown separately rather than combined into a misleading single ranking score.\n"
    summary+='\n## Selected candidate geometry and restrictions\n```yaml\n'+yaml.safe_dump({'geometry':designs['C']['config']['geometry'],'branches':designs['C']['config']['branches']},sort_keys=False)+'```\n'
    summary+='\n# Parameter sweeps and Pareto analysis\n\nSix deterministic sweeps are saved in sweeps.csv. The following are sampled nondominated fronts among feasible optimizer evaluations; no claim of a complete mathematical Pareto frontier is made.\n\n![Pump Pareto](../figures/pareto_pump_electrical_W.png)\n\n![Size Pareto](../figures/pareto_header_volume_m3.png)\n\n![Diameter sweep](../figures/sweep_header_diameter_mm_M_thermal.png)\n\n![Taper pressure](../figures/sweep_taper_ratio_rack_dp_Pa.png)\n'
    summary+='\n# Pressure-drop breakdown\n\nDetailed flow-weighted path budgets are in baseline_pressure_budget.csv and optimized_pressure_budget.csv. GF_reference_comparison.csv compares relative fractions with the 232 kPa broader technical-loop example. Differences are retained; this is not forced calibration of unmeasured tray curves.\n\n![Candidate pressure budget](../figures/optimized_pressure_budget.png)\n'
    summary+='\n# Uncertainty analysis\n\nPaired seeded draws vary class cold-plate/QDC/tubing/restriction coefficients, individual cold-plate scatter, loads, supply temperature, rack flow, fluid (water/PG25), PG model viscosity, roughness and pump efficiency. FWS temperature tracks TCS by 4 K for this study; an independently warmed FWS is tested in the fault study. Extrema below include infeasible solved points. Draws above the conservative 120 LPM CDU rating can fail by construction. These rates are stress-test results, not measured failure probabilities.\n'
    rows=[]
    for name,sub in unc.groupby('design',sort=False):
        rows.append([name,len(sub),f'{100*sub.feasible.mean():.1f}%',f'{sub.T_out_max_C.min():.2f}–{sub.T_out_max_C.max():.2f}',f'{sub.system_dp_Pa.max()/1000:.2f}',f'{sub.RMS_target_error.max()*100:.2f}',int(sub.error.notna().sum())])
    summary+=table(['Design','Draws','Feasible','Outlet range °C','Worst head kPa','Worst RMS error %','Solver failures'],rows)
    summary+='\nHardware-only uncertainty holds each design at its own nominal flow, fluid, load and temperatures, varying hydraulic coefficients, roughness, model viscosity and pump efficiency. This separates resistance sensitivity from deliberate operating-envelope excursions.\n'+table(['Design','Feasible draws','Worst head kPa','Worst outlet °C'],[(name,f'{100*sub.feasible.mean():.1f}%',f'{sub.system_dp_Pa.max()/1000:.2f}',f'{sub.T_out_max_C.max():.2f}') for name,sub in hardware.groupby('design',sort=False)])
    summary+='\nA nominally balanced restriction pattern cannot maintain heat-proportional flow under every changed workload. Designs with little nominal head reserve are sensitive to unknown component losses. No design is declared deployment-qualified or robust across the full uncertainty box.\n'
    summary+='\n# Workloads and faults\n'+table(['Design','Scenario','Max outlet °C','Head kPa','Feasible','Failures'],[(r.design,r.scenario,f'{r.T_out_max_C:.2f}' if pd.notna(r.get('T_out_max_C')) else 'unsolved',f'{r.system_dp_Pa/1000:.2f}' if pd.notna(r.get('system_dp_Pa')) else 'unsolved',r.feasible,r.get('failed_constraints') if pd.isna(r.error) else r.error) for _,r in faults.iterrows()])
    summary+='\nPump-unavailable uses an explicitly assumed equivalent speed reduction, not a measured redundant-pump curve. Removed trays close the hydraulic path and remove its heat, preserving other elevations.\n'
    summary+='\n# Gravity study\n'+table(['Design','Head gravity Pa','Head no gravity Pa','Maximum branch flow change LPM'],[(x['design'],f"{x['head_with_gravity_Pa']:.3f}",f"{x['head_without_gravity_Pa']:.3f}",f"{x['max_flow_change_LPM']:.6f}") for x in gravity])
    summary+='\nThe isothermal analytical test cancels hydrostatic head exactly. Heated runs retain a small positive supply-minus-return density term; its distribution effect is small for this configuration.\n'
    summary+='\n# Constraint margins\n'+table(['Constraint','Margin','Units','Pass'],[(k,f"{v['margin']:.6g}",v['units'],v['pass']) for k,v in designs['C']['constraints'].items()])
    summary+='\n# Validation and optimization termination\n'+table(['Check','Baseline','Candidate'],[(k,str(v),str(designs['C']['validation'].get(k))) for k,v in designs['baseline']['validation'].items()])
    summary+='\n```json\n'+json.dumps({k:designs[k].get('optimization') for k in ('A','B','C','D','E')},indent=2)+'\n```\n'
    summary+='\n# Limitations\n'+LIMITATIONS+'\n\n# Conclusions\n\nThe calculated two-class balancing design strongly improves thermal allocation relative to the specified reference. The price is greater hydraulic resistance and pumping demand. A 27-location balance yields only a small additional temperature benefit at nominal load; its parts complexity needs justification. Physical component measurements, PG25 property qualification, a manufacturer pump/HX map and selected operating reserve are the next inputs needed before hardware decisions.\n'
    (out/'reports/engineering_report.md').write_text(summary)
