"""Deterministic sweeps, including coupled geometry aliases."""
from copy import deepcopy
from .solver import solve

def set_parameter(c,parameter,value):
    d=deepcopy(c);value=float(value)
    if parameter=='rack_flow_LPM':d['rack']['flow_LPM']=value
    elif parameter=='header_diameter_mm':
        for side in ('supply','return'):d['geometry'][side].update(profile='constant',inlet_m=value/1000,outlet_m=value/1000)
    elif parameter=='taper_ratio':
        s=d['geometry']['supply'];r=d['geometry']['return']
        s.update(profile='power',outlet_m=s['inlet_m']*value);r.update(profile='power',inlet_m=r['outlet_m']*value)
    elif parameter=='supply_C':
        d['rack']['supply_C']=value;d['facility']['supply_C']=value-d['cdu']['approach_K']
    elif parameter in ('compute_restriction_K','switch_restriction_K'):d['branches'][parameter.split('_')[0]]['restriction_K']=value
    else:
        keys=parameter.split('.');obj=d
        for k in keys[:-1]:obj=obj[k]
        if keys[-1] not in obj: raise ValueError(f'Unknown parameter {parameter}')
        obj[keys[-1]]=value
    return d

def sweep(c,parameter,values):
    rows=[]
    for v in values:
        row={'parameter':parameter,'value':float(v)}
        try:
            r=solve(set_parameter(c,parameter,v));row.update(r['metrics'],feasible=r['feasible'],error=None)
        except (ValueError,RuntimeError) as exc:row.update(feasible=False,error=str(exc))
        rows.append(row)
    return rows

if __name__=='__main__':
    from .cli import main
    main(['sweep']+__import__('sys').argv[1:])
