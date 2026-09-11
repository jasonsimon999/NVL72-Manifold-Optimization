"""Reproducible bounded local/global searches with hard feasibility filtering."""
from copy import deepcopy
import numpy as np
from scipy.optimize import minimize, differential_evolution
from .solver import solve
from .objectives import objective, pareto_mask

DESIGNS={'A':'constant diameter optimization','B':'tapered headers','C':'constant headers / two restrictions',
         'D':'tapered headers / two restrictions / flow','E':'tapered headers / location restrictions'}

def variables(c,design):
    b=c['optimization']['bounds']
    names=[]; bounds=[]; initial=[]
    def add(name,bound,value): names.append(name);bounds.append(bound);initial.append(value)
    if design=='A': add('diameter',b['diameter_m'],c['geometry']['supply']['inlet_m'])
    if design in ('B','D','E'):
        add('supply_diameter',b['diameter_m'],c['geometry']['supply']['inlet_m'])
        add('supply_ratio',b['taper_ratio'],1.)
        add('return_diameter',b['diameter_m'],c['geometry']['return']['outlet_m'])
        add('return_ratio',b['taper_ratio'],1.)
    if design in ('C','D'):
        for kind in ('compute','switch'): add(kind+'_K',b['restriction_K'],c['branches'][kind]['restriction_K'])
    if design=='E':
        for tray in c['rack']['layout']: add(tray+'_K',b['restriction_K'],c['branches']['overrides'].get(tray,{}).get('restriction_K',c['branches']['compute' if tray.startswith('C') else 'switch']['restriction_K']))
    if design=='D': add('flow',b['flow_LPM'],c['rack']['flow_LPM'])
    bounds=np.asarray(bounds,float)
    return names,bounds,np.clip((initial-bounds[:,0])/np.ptp(bounds,axis=1),0,1)

def decode(c,design,names,bounds,x):
    d=deepcopy(c); vals=dict(zip(names,bounds[:,0]+np.asarray(x)*np.ptp(bounds,axis=1)))
    if 'diameter' in vals:
        for side in ('supply','return'): d['geometry'][side].update(profile='constant',inlet_m=float(vals['diameter']),outlet_m=float(vals['diameter']))
    if 'supply_diameter' in vals:
        d['geometry']['supply'].update(profile='power',inlet_m=float(vals['supply_diameter']),outlet_m=float(vals['supply_diameter']*vals['supply_ratio']))
        d['geometry']['return'].update(profile='power',inlet_m=float(vals['return_diameter']*vals['return_ratio']),outlet_m=float(vals['return_diameter']))
    for kind in ('compute','switch'):
        if kind+'_K' in vals: d['branches'][kind]['restriction_K']=float(vals[kind+'_K'])
    if design=='E':
        for tray in d['rack']['layout']: d['branches']['overrides'].setdefault(tray,{})['restriction_K']=float(vals[tray+'_K'])
    if 'flow' in vals: d['rack']['flow_LPM']=float(vals['flow'])
    d['name']=f'Design {design}: {DESIGNS[design]}'
    return d

def optimize(c,design='D',method='local'):
    if design not in DESIGNS: raise ValueError('Design must be A, B, C, D or E')
    names,bounds,x0=variables(c,design); archive=[]; cache={}; failures=[]
    def evaluate(x):
        key=tuple(np.round(x,12))
        if key in cache: return cache[key]
        try:
            result=solve(decode(c,design,names,bounds,x))
            margins=np.array([v['normalized_margin'] for v in result['constraints'].values()])
            score=objective(result)+c['constraints']['soft_penalty']*np.sum(np.minimum(0,margins)**2)
            archive.append(result)
            cache[key]=(score,result,margins)
        except (ValueError,RuntimeError,FloatingPointError) as exc:
            failures.append(str(exc));cache[key]=(1e6,None,None)
        return cache[key]
    def fun(x):return evaluate(x)[0]
    def constraints(x):
        margins=evaluate(x)[2]
        return float(np.min(margins)) if margins is not None else -1e3
    evaluate(x0)
    # Interpretability seed: class balance is approximately an order of magnitude
    # higher resistance for low-load switch paths; this is a search point, not output.
    if 'switch_K' in names:
        seed=x0.copy();seed[names.index('switch_K')]=.45;evaluate(seed)
        if fun(seed)<fun(x0):x0=seed
    global_status=None
    if method=='global':
        de=differential_evolution(fun,[(0,1)]*len(x0),seed=c['optimization']['seed'],
                maxiter=c['optimization']['global_maxiter'],popsize=c['optimization']['population_size'],
                polish=False,x0=x0,tol=.01)
        x0=de.x;global_status={'success':bool(de.success),'message':str(de.message),'nfev':de.nfev}
    # Constraint vector length fixed per valid config; scalar minimum also handles invalid trials.
    local=minimize(fun,x0,method='SLSQP',bounds=[(0,1)]*len(x0),constraints=[{'type':'ineq','fun':constraints}],
                   options={'maxiter':c['optimization']['maxiter'],'ftol':1e-7,'eps':1e-4})
    evaluate(local.x)
    feasible=[r for r in archive if r['feasible']]
    if not feasible: raise RuntimeError(f'No feasible design found; {local.message}. Solver failures: {failures[:2]}')
    best=min(feasible,key=objective)
    best['optimization']={'design':design,'method':method,'seed':c['optimization']['seed'],
                         'local_success':bool(local.success),'local_message':str(local.message),
                         'global_status':global_status,'evaluations':len(cache),'failed_evaluations':len(failures),
                         'selection':'lowest objective among actually solved feasible candidates; not proof of global optimality'}
    rows=[dict(r['metrics'],feasible=r['feasible'],design=design,objective=objective(r)) for r in archive]
    return best,rows

if __name__=='__main__':
    from .cli import main
    main(['optimize']+__import__('sys').argv[1:])


def balance_locations(c):
    """Minimum-head exact target balance at fixed geometry by nonnegative added K.

    For prescribed target mass flows the path losses are known. The least
    possible head with passive added restrictions is max(path requirements).
    Branch flows are then independently verified by the coupled network solve.
    """
    from .coolant import Coolant
    from .units import c_to_k,lpm_to_m3s
    from .rack import tray_data
    from .thermal import temperatures
    from .hydraulics import solve_network
    from .objectives import targets
    d=deepcopy(c)
    for kind in ('compute','switch'):d['branches'][kind]['restriction_K']=0.
    for override in d['branches']['overrides'].values():override['restriction_K']=0.
    ids,kinds,heat,branches=tray_data(d)
    fluid=Coolant(d['coolant']['type'],d['coolant']['property_file'],d['coolant']['viscosity_multiplier'])
    ts=c_to_k(d['rack']['supply_C']);ps=fluid.properties(ts)
    total=float(lpm_to_m3s(d['rack']['flow_LPM'])*ps.rho)
    target=targets(total,heat,d['optimization']['target'])
    if np.any(target<=0):raise ValueError('Exact balancing requires positive target flows; use local optimization for zero-load branches')
    tout,tr,_=temperatures(target,heat,ts,fluid)
    path=solve_network(d,branches,total,ps,fluid.properties((ts+tout)/2),fluid.properties(tr),evaluate_mass=target)
    added=(path.max()-path)/target**2
    for tray,k in zip(ids,added):d['branches']['overrides'].setdefault(tray,{})['restriction_K']=float(k)
    d['name']='Design E: minimum-head exact location balance at D geometry'
    r=solve(d)
    r['optimization']={'design':'E','method':'analytical nonnegative restriction sizing; coupled solver verification',
                       'local_success':True,'selection':'Minimum head for exact target flows at the supplied fixed geometry, not global geometry optimum'}
    return r
