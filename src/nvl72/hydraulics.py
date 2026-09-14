"""Coupled direct-return network: all branch loop balances plus total mass flow."""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import root, least_squares
from .components import pipe_loss, reduced_loss, curve_loss
from .manifold import geometry
from .orifices import coefficient, bore_from_coefficient
from .quick_disconnect import mass_coefficient

@dataclass
class HydraulicResult:
    mass_flow: np.ndarray
    head_Pa: float
    supply_Pa: np.ndarray
    return_Pa: np.ndarray
    branch_losses: dict
    supply_losses: dict
    return_losses: dict
    gravity_path_Pa: np.ndarray
    residual_Pa: float
    mass_error: float
    nfev: int
    converged: bool

def solve_network(c, branches, total_mass, supply_props, branch_props, return_props, initial=None, evaluate_mass=None):
    z,dz,ds,dr = geometry(c); n = len(z)
    b = {key: np.array([item[key] for item in branches]) for key in ('diameter_m','tube_length_m','tube_multiplier','coldplate_K','qdc_K','restriction_K')}
    b['qdc_K']=np.array([mass_coefficient(item,float(branch_props.rho[i])) for i,item in enumerate(branches)])
    minor = c['loss_coefficients']; rough = c['geometry']['roughness_m']
    hs = np.full(n, minor['header']['tee']); hr = hs.copy()
    hs[0] += minor['header']['entrance']; hr[0] += minor['header']['exit']
    hs[1:] += minor['header']['reducer']*(np.abs(np.diff(ds))>1e-12)
    hr[1:] += minor['header']['expansion']*(np.abs(np.diff(dr))>1e-12)
    g = c['rack']['gravity_m_s2'] if c['rack']['gravity_enabled'] else 0.0
    gs = supply_props.rho*g*dz; gr = return_props.rho*g*dz
    scale_m = total_mass/n
    orifice_coeff = np.zeros(n)
    auto=c.get('balancing_mode','resistance')=='auto_equivalent'
    for i,item in enumerate(branches):
        bore=item.get('orifice_diameter_m')
        if auto:
            if bore is not None: raise ValueError('Automatic sizing and fixed orifice bores cannot be combined; choose one mode')
            bore=bore_from_coefficient(b['restriction_K'][i],item['diameter_m'],float(branch_props.rho[i]),item.get('orifice_Cd',.62))
            b['restriction_K'][i]=0.
        if bore is None: continue
        orifice_coeff[i]=coefficient(bore,item['diameter_m'],float(branch_props.rho[i]),item.get('orifice_Cd',.62))

    def evaluate(m):
        # Exact continuity elimination: segment j carries branches j..n-1.
        mh = np.cumsum(m[::-1])[::-1]
        sl = pipe_loss(mh, supply_props.rho, supply_props.mu, ds, dz, rough, hs)
        rl = pipe_loss(mh, return_props.rho, return_props.mu, dr, dz, rough, hr)
        bp = pipe_loss(m, branch_props.rho, branch_props.mu, b['diameter_m'], b['tube_length_m'], rough)
        dynamic = branch_props.rho*bp['velocity']*np.abs(bp['velocity'])/2
        losses = {
            'coldplates': reduced_loss(m, b['coldplate_K']),
            'qdcs': reduced_loss(m, b['qdc_K']),
            'tubing': bp['friction']*b['tube_multiplier'],
            'fittings': dynamic*sum(v for k,v in minor['branch'].items() if k not in ('valve','orifice')),
            'valves': dynamic*minor['branch']['valve'],
            'restrictions': reduced_loss(m,b['restriction_K'])+dynamic*minor['branch']['orifice'],
            'orifices': reduced_loss(m,orifice_coeff)}
        for i, item in enumerate(branches):
            for component, key in [('coldplates','coldplate_curve'), ('qdcs','qdc_curve')]:
                if key in item: losses[component][i] = curve_loss(m[i]/branch_props.rho[i],item[key])
        sc = np.cumsum(sl['friction']+sl['minor']+gs)
        rc = np.cumsum(rl['friction']+rl['minor']-gr)
        return sc,rc,losses,sl,rl

    if evaluate_mass is not None:
        sc,rc,losses,sl,rl = evaluate(np.asarray(evaluate_mass))
        return sc+rc+sum(losses.values())

    def residual(x):
        m = x[:n]*scale_m; head = x[n]*1e5
        sc,rc,losses,_,_ = evaluate(m)
        loops = head-sc-rc-sum(losses.values())
        return np.r_[loops/1e5, (m.sum()-total_mass)/total_mass]
    x0 = np.r_[np.ones(n) if initial is None else initial/scale_m, 0.8]
    sol = root(residual, x0, options={'maxfev': c['solver']['max_nfev']*(n+1), 'xtol': 1e-10})
    if not sol.success or np.min(sol.x[:n])<=0 or np.max(np.abs(residual(sol.x)))>c['solver']['pressure_tolerance_Pa']/1e5:
        sol = least_squares(residual, np.r_[np.maximum(x0[:n],1e-5), max(x0[n],1e-5)],
                            bounds=(np.r_[np.full(n,1e-10),-np.inf], np.full(n+1,np.inf)),
                            xtol=1e-12, ftol=1e-12, gtol=1e-12, max_nfev=c['solver']['max_nfev'])
    m = sol.x[:n]*scale_m; head = float(sol.x[n]*1e5)
    sc,rc,losses,sl,rl = evaluate(m)
    pres = float(np.max(np.abs(head-sc-rc-sum(losses.values()))))
    merr = float(abs(m.sum()-total_mass)/total_mass)
    good = sol.success and pres<c['solver']['pressure_tolerance_Pa'] and merr<c['solver']['mass_relative_tolerance'] and np.all(m>0)
    if not good: raise RuntimeError(f'Network did not converge: {sol.message}; closure={pres:g} Pa, mass={merr:g}')
    return HydraulicResult(m,head,head-sc,rc,losses,sl,rl,np.cumsum(gs-gr),pres,merr,sol.nfev,True)
