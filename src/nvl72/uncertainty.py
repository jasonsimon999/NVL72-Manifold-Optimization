"""Paired Monte Carlo; same draw applied to baseline and candidate hardware."""
from copy import deepcopy
import numpy as np
from .solver import solve

def uncertainty(configs:dict,samples=None,operating_variation=True):
    first=next(iter(configs.values()));u=first['uncertainty'];rng=np.random.default_rng(u['seed'])
    count=samples or u['samples'];rows=[]
    ranges={k:v for k,v in u.items() if isinstance(v,list) and len(v)==2 and k!='coolants'}
    for sample in range(count):
        draw={k:float(rng.uniform(*v)) for k,v in ranges.items()};fluid=str(rng.choice(u['coolants']))
        # Independent tray factors plus correlated class factors expose location sensitivity.
        location=rng.uniform(.9,1.1,len(first['rack']['layout']))
        for name,c in configs.items():
            d=deepcopy(c)
            for kind in ('compute','switch'):
                b=d['branches'][kind]
                for key,range_key in [('coldplate_K','coldplate_multiplier'),('qdc_K','qdc_multiplier'),('tube_multiplier','tubing_multiplier'),('restriction_K','restriction_multiplier')]: b[key]*=draw[range_key]
            for i,tray in enumerate(d['rack']['layout']):
                kind='compute' if tray.startswith('C') else 'switch';ov=d['branches']['overrides'].setdefault(tray,{})
                # Apply uncertainty to per-location restrictions as well as class designs.
                if 'restriction_K' in ov: ov['restriction_K']*=draw['restriction_multiplier']
                ov['coldplate_K']=d['branches'][kind]['coldplate_K']*location[i]
            if operating_variation:
                d['power']['compute_fraction']*=draw['compute_load_multiplier'];d['power']['switch_fraction']*=draw['switch_load_multiplier']
                d['rack']['supply_C']=draw['supply_C'];d['rack']['flow_LPM']=draw['flow_LPM']
                d['facility']['supply_C']=d['rack']['supply_C']-d['cdu']['approach_K']
                d['coolant']['type']=fluid
            d['coolant']['viscosity_multiplier']=draw['viscosity_multiplier']
            d['geometry']['roughness_m']=draw['roughness_m'];d['cdu']['efficiency']=draw['efficiency']
            row={'sample':sample,'design':name,'coolant':d['coolant']['type'],'operating_variation':operating_variation,
                 'actual_supply_C':d['rack']['supply_C'],'actual_compute_fraction':d['power']['compute_fraction'],
                 'actual_switch_fraction':d['power']['switch_fraction'],**{'draw_'+k:v for k,v in draw.items()}}
            try:
                r=solve(d);row.update(r['metrics'],feasible=r['feasible'],all_screens_pass=r['screening_pass'],error=None)
            except (ValueError,RuntimeError) as exc:row.update(feasible=False,error=str(exc))
            rows.append(row)
    return rows
