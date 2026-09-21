"""Explicit scenario, failure, sensitivity, capacity and economic break-even studies."""
from copy import deepcopy
import numpy as np
from .simulation import run_comparison, prepare, simulate
from .settings import SCENARIOS, FAILURES, settings

SWEEPS = {
    'compute_power_scale': (.8,1.2), 'switch_power_scale': (.7,1.3),
    'compute_liquid_fraction': (.7,1.), 'switch_liquid_fraction': (.5,1.),
    'coldplate_scale': (.5,1.5), 'qd_scale': (.5,1.5), 'header_scale': (.8,1.2),
    'valve_max_bore_fraction': (.65,.98), 'valve_Cd': (.5,.8), 'valve_body_K': (.5,10.),
    'pump_efficiency': (.35,.8), 'supply_offset_K': (-5.,5.),
    'target_rise_K': (10.,20.), 'correlation': (0.,1.), 'spike_s': (10.,100.),
    'valve_stroke_s': (5.,120.), 'electricity_per_kWh': (.05,.4),
    'compute_C_J_K': (3000.,30000.), 'switch_C_J_K': (1000.,12000.),
    'compute_R_K_W': (.002,.008), 'switch_R_K_W': (.006,.024),
    'coolant_C_J_K': (400.,4000.), 'valve_tau_s': (2.,40.),
    'valve_min_area_fraction': (.001,.05), 'sensor_noise_K': (0.,1.),
    'pump_tau_s': (2.,40.), 'minimum_flow_fraction': (.05,.3),
}

def compact(r, label):
    a=r['active']['summary'];f=r['fixed']['summary'];e=r['economics']
    return dict(case=label,**r['benefit'],fixed_peak_C=f['peak_chip_C'],active_peak_C=a['peak_chip_C'],
                fixed_thermal_pass=f['thermal_pass'],active_thermal_pass=a['thermal_pass'],
                fixed_flow_LPM=f['average_flow_LPM'],active_flow_LPM=a['average_flow_LPM'],
                annual_savings=e['annual_savings'],payback_years=e['payback_years'],
                break_even_price=e['break_even_price'],affordable_capex=e['affordable_incremental_capex'],
                active_actuations=a['valve_actuations'],pressure_residual_Pa=a['pressure_residual_Pa'])

def scenario_study(c,s,progress=None):
    rows=[]
    for i,name in enumerate(SCENARIOS):
        d=dict(s,scenario=name,failure='none')
        if name=='bursts':d['spike_s']=10.
        if name=='rack_step':d['spike_s']=s['duration_s']*.5
        try:rows.append(compact(run_comparison(c,d),name))
        except (ValueError,RuntimeError) as exc:rows.append(dict(case=name,error=str(exc)))
        if progress:progress((i+1)/len(SCENARIOS))
    d=dict(s,scenario='steady',low_load=.3,high_load=.3)
    rows.append(compact(run_comparison(c,d),'steady_low_utilization'))
    return rows

def failure_study(c,s,progress=None):
    rows=[]
    reference=run_comparison(c,dict(s,failure='none'))
    nominal=reference['active']['flow_LPM'];index=min(len(nominal[0])-1,int(s['failure_tray']))
    for i,failure in enumerate(FAILURES):
        r=run_comparison(c,dict(s,failure=failure))
        row=compact(r,failure)
        others=np.arange(len(nominal[0]))!=index
        row['max_neighbor_flow_change_LPM']=float(np.max(abs(r['active']['flow_LPM'][:,others]-nominal[:,others])))
        row['time_above_limit_s']=r['active']['summary']['time_above_limit_s']
        rows.append(row)
        if progress:progress((i+1)/len(FAILURES))
    # Compare commanded failsafe positions with the same communications fault.
    for position in (0.,.5,1.):
        rows.append(compact(run_comparison(c,dict(s,failure='communications',fail_position=position)),f'communications fail position {position}'))
    return rows

def sensitivity_study(c,s,keys=None,progress=None):
    keys=keys or list(SWEEPS);rows=[]
    for i,key in enumerate(keys):
        for value in SWEEPS[key]:
            d=dict(s);d[key]=value
            try:rows.append(dict(parameter=key,value=value,**compact(run_comparison(c,d),f'{key}={value}')))
            except (ValueError,RuntimeError) as exc:rows.append(dict(parameter=key,value=value,error=str(exc)))
        if progress:progress((i+1)/len(keys))
    return rows

def strategy_study(c,s):
    rows=[]
    for pump in ('constant_speed','constant_dp','demand'):
        for controller in ('reactive','feedforward','combined'):
            rows.append(compact(run_comparison(c,dict(s,pump_mode=pump,controller=controller)),pump+' / '+controller))
    return rows

def break_even_study(c,s):
    # Sweep actual network simulations, not fabricated linear energy scaling.
    axes={'low_load':(.1,.3,.6,.9),'correlation':(0.,.5,1.),
          'design_flow_scale':(.75,1.,1.25),'controlled_branches':(9,18,27),
          'pump_efficiency':(.35,.6,.8)}
    rows=[]
    for key,values in axes.items():
        for value in values:
            try:rows.append(dict(parameter=key,value=value,**compact(run_comparison(c,dict(s,**{key:value})),f'{key}={value}')))
            except (ValueError,RuntimeError) as exc:rows.append(dict(parameter=key,value=value,error=str(exc)))
    return rows

def capacity_study(c,s):
    """Thermal-only sustained capacity at fixed hardware; finite horizon must settle."""
    ss=dict(s,scenario='worst_case',high_load=1.,duration_s=max(600.,s['duration_s']),failure='none',sensor_noise_K=0.)
    p=prepare(c,ss);rows=[]
    for mode in ('fixed',s['controller']):
        def evaluate(scale):
            candidate=deepcopy(p);candidate['electrical']=p['electrical']*scale
            result=simulate(candidate,ss,mode)
            tail=max(2,int(30/ss['dt_s']))
            drift=float(np.max(abs(result['chip_C'][-1]-result['chip_C'][-tail]))/((tail-1)*ss['dt_s']))
            ok=bool(result['chip_C'][-tail:].max()<=ss['chip_limit_C'] and result['outlet_C'][-tail:].max()<=ss['outlet_limit_C'] and drift<.02)
            return ok,result,drift
        lo=0.;hi=3.;ok,_,_=evaluate(hi)
        for _ in range(10):
            mid=(lo+hi)/2;passed,_,_=evaluate(mid)
            if passed:lo=mid
            else:hi=mid
        passed,r,drift=evaluate(lo)
        liquid=float(np.sum(p['electrical']*p['fraction']))*lo
        available=c['cdu']['capacity_W']/c['cdu']['served_racks']
        rows.append(dict(controller=mode,thermal_load_multiplier=lo,thermal_only_liquid_kW=liquid/1000,
                         additional_liquid_kW=(liquid-np.sum(p['electrical']*p['fraction']))/1000,
                         rating_capped_liquid_kW=min(liquid,available)/1000,
                         final_flow_LPM=float(r['flow_LPM'][-1].sum()),final_pump_W=float(r['pump_W'][-1]),
                         settled=drift<.02,drift_K_s=drift,upper_search_bound_reached=ok,
                         note='Thermal-only finite-horizon screen. Rating cap is not HX/site qualification; no IT performance prediction.'))
    return rows
