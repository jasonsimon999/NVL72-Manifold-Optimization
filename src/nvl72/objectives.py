"""Explicit metrics, normalized constraints and multiobjective dominance."""
import numpy as np

def targets(mtotal, heat, mode):
    if mode == 'equal_flow' or np.sum(heat)==0: return np.full(len(heat),mtotal/len(heat))
    return mtotal*heat/np.sum(heat)

def metrics(m, heat, target, tout):
    active=target>0
    error=np.zeros_like(m); error[active]=(m[active]-target[active])/target[active]
    r=m[heat>0]/heat[heat>0]
    return {'M_flow':float(np.ptp(m)/np.mean(m)),'CV_flow':float(np.std(m)/np.mean(m)),
            'M_thermal':float(np.ptp(r)/np.mean(r)) if len(r) else 0.,
            'RMS_target_error':float(np.sqrt(np.mean(error[active]**2))),
            'max_abs_target_error':float(np.max(np.abs(error[active]))),
            'zero_load_flow_fraction':float(m[heat==0].sum()/m.sum()),
            'T_out_max_C':float(tout.max()-273.15),'T_out_min_C':float(tout.min()-273.15),
            'outlet_spread_K':float(np.ptp(tout))},error

def objective(result):
    m=result['metrics']; w=result['config']['optimization']['weights']; n=result['config']['optimization']['normalization']
    return (w['flow_error']*m['RMS_target_error']+w['temperature_spread']*m['outlet_spread_K']/n['temperature_K']+
            w['pressure']*m['system_dp_Pa']/n['pressure_Pa']+w['pump']*m['pump_electrical_W']/n['pump_W']+
            w['size']*m['header_volume_m3']/n['volume_m3'])

def pareto_mask(values):
    values=np.asarray(values)
    return np.array([not np.any(np.all(values<=v,axis=1)&np.any(values<v,axis=1)) for v in values])
