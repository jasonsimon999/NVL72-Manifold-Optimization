"""Workload and fault transformations; no changes hidden in the solver."""
from copy import deepcopy
from .rack import tray_data

def scenario(c,name):
    d=deepcopy(c); ids,kinds,heat,_=tray_data(c)
    if name=='full': pass
    elif name in ('compute75','compute50'): d['power']['compute_fraction']*=.75 if name=='compute75' else .5
    elif name=='nonuniform':
        d['power']['tray_heat_W']=[float(q*(.5 if i<len(ids)//2 and k=='compute' else 1)) for i,(q,k) in enumerate(zip(heat,kinds))]
    elif name=='switch_heavy':d['power']['switch_fraction']*=1.2
    elif name=='near_zero':
        heat[0]=.001;d['power']['tray_heat_W']=heat.tolist()
    elif name in ('blocked','degraded_qdc','double_resistance'):
        key='qdc_K' if name=='degraded_qdc' else 'coldplate_K'
        d['branches']['overrides'].setdefault(ids[0],{})[key]=d['branches']['compute'][key]*(4 if name=='blocked' else 2)
    elif name in ('compute_removed','switch_removed'):
        kind='compute' if name=='compute_removed' else 'switch'; idx=kinds.index(kind)
        # Physically closed removed path: delete branch; preserve remaining explicit heat loads.
        removed=d['rack']['layout'].pop(idx);d['rack'][kind+'_trays']-=1
        d['branches']['overrides'].pop(removed,None)
        from .manifold import geometry
        z=geometry(c)[0].tolist();z.pop(idx);d['rack']['elevations_m']=z
        d['power']['tray_heat_W']=[float(q) for i,q in enumerate(heat) if i!=idx]
    elif name in ('pump_reduced','pump_unavailable'):
        d['cdu']['speed']=.8 if name=='pump_reduced' else .65
        d['rack']['operating_mode']='pump'
    elif name=='warm_coolant': d['rack']['supply_C']+=5
    elif name=='warm_facility':d['facility']['supply_C']+=5
    elif name=='nominal102':d['power']['tray_heat_W']=(heat*102000/heat.sum()).tolist()
    elif name=='OEM115':d['power']['tray_heat_W']=(heat*115000/heat.sum()).tolist()
    else:raise ValueError(f'Unknown scenario {name}')
    d['name']=c['name']+' / '+name
    return d
