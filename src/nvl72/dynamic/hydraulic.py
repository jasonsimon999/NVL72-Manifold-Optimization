"""Pump-boundary coupled network, sharing every passive loss law with the main model."""
from copy import deepcopy
import numpy as np
from scipy.optimize import root, least_squares
from ..hydraulics import network_evaluator
from ..components import pipe_loss, reduced_loss
from ..orifices import coefficient, bore_from_coefficient
from ..cdu import pump_head

def operating_point(c, branches, props, speed, connected, initial=None):
    ps, pb, pr = props
    evaluate, _ = network_evaluator(c,branches,ps,pb,pr)
    n=len(branches); mask=np.asarray(connected)>0
    def extra(m):
        if not c['external']['enabled']: return 0.
        e=c['external']; total=m.sum()
        loss=pipe_loss(total,ps.rho,ps.mu,e['diameter_m'],e['length_m'],c['geometry']['roughness_m'],e['minor_K'])
        return float(loss['friction']+loss['minor']+reduced_loss(total,e['equipment_K']))
    if speed <= 0 or not mask.any():
        shutoff=c['cdu']['shutoff_dp_Pa']*speed**2 if speed>0 else 0.
        return dict(mass=np.zeros(n),head=shutoff,rack_head=shutoff,branch_dp=np.zeros(n),supply=np.full(n,shutoff),
                    return_pressure=np.zeros(n),pressure_error=0.,mass_error=0.,header_velocity=0.)
    pump=deepcopy(c['cdu']);pump['speed']=speed
    idx=np.where(mask)[0]
    def residual(x):
        m=np.zeros(n);m[idx]=x*.1
        sc,rc,loss,_,_=evaluate(m)
        head=float(pump_head(m.sum()/float(ps.rho)*pump['served_racks'],pump))
        return (head-extra(m)-sc[idx]-rc[idx]-sum(loss.values())[idx])/1e5
    x0=np.ones(len(idx)) if initial is None else np.maximum(initial[idx]/.1,1e-5)
    sol=root(residual,x0,tol=1e-9)
    if not sol.success or np.any(sol.x<0) or np.max(abs(residual(sol.x)))>5e-7:
        sol=least_squares(residual,x0,bounds=(0,np.inf),xtol=1e-11,ftol=1e-11,gtol=1e-11,max_nfev=300)
    err=float(np.max(abs(residual(sol.x)))*1e5)
    if not sol.success or err>.1: raise RuntimeError(f'Transient network failed pressure closure: {err:.3g} Pa')
    m=np.zeros(n);m[idx]=sol.x*.1
    sc,rc,loss,sl,rl=evaluate(m)
    head=float(pump_head(m.sum()/float(ps.rho)*pump['served_racks'],pump))
    rack=head-extra(m)
    segments=np.cumsum(m[::-1])[::-1]
    node_error=np.max(abs(segments-np.r_[segments[1:],0]-m))
    return dict(mass=m,head=head,rack_head=rack,branch_dp=sum(loss.values()),supply=rack-sc,
                return_pressure=rc,pressure_error=err,mass_error=float(node_error),
                header_velocity=float(max(np.max(abs(sl['velocity'])),np.max(abs(rl['velocity'])))))

def valve_branches(base, position, connected, rho, controlled, s, active=True):
    branches=deepcopy(base)
    for i,b in enumerate(branches):
        if active and controlled[i]:
            # Replaces passive balancing plate; body loss remains at maximum opening.
            area_fraction=s['valve_min_area_fraction']+(1-s['valve_min_area_fraction'])*position[i]
            bore=b['diameter_m']*s['valve_max_bore_fraction']*np.sqrt(area_fraction)
            b['orifice_diameter_m']=max(bore,1e-9)
            area=np.pi*b['diameter_m']**2/4
            b['restriction_K']=s['valve_body_K']/(2*rho[i]*area**2)
            b['orifice_Cd']=s['valve_Cd']
        # QD opening during reconnection: series loss, exactly shut branch is excluded.
        if 0<connected[i]<1:
            b['restriction_K']=b.get('restriction_K',0.)+coefficient(
                b['diameter_m']*.99*np.sqrt(connected[i]),b['diameter_m'],rho[i],.62)
    return branches

def initial_positions(branches,rho,s):
    """Closest realizable active restriction to each frozen passive restriction."""
    positions=[]
    for i,b in enumerate(branches):
        pipe=b['diameter_m'];area=np.pi*pipe**2/4
        total=b.get('restriction_K',0.)
        if b.get('orifice_diameter_m'):
            total+=coefficient(b['orifice_diameter_m'],pipe,rho[i],b.get('orifice_Cd',.62))
        remaining=max(0,total-s['valve_body_K']/(2*rho[i]*area**2))
        bore=bore_from_coefficient(remaining,pipe,rho[i],s['valve_Cd'])
        fraction=1. if bore is None else (bore/(pipe*s['valve_max_bore_fraction']))**2
        positions.append(np.clip((fraction-s['valve_min_area_fraction'])/(1-s['valve_min_area_fraction']),0,1))
    return np.asarray(positions)


def size_positions(branches, opening, mass, target, rho, s):
    """Invert the same permanent-loss law used by the network solver.

    Local pressure is held for this sizing step, then the entire coupled
    network is re-solved. This is feedback sizing, not a global optimizer.
    """
    result=[]
    for i,b in enumerate(branches):
        D=b['diameter_m']; maximum=D*s['valve_max_bore_fraction']
        fraction=s['valve_min_area_fraction']+(1-s['valve_min_area_fraction'])*opening[i]
        current=max(maximum*np.sqrt(fraction),1e-9)
        if target[i]<=0:result.append(opening[i]);continue
        if mass[i]<=1e-10:result.append(1.);continue
        k=coefficient(current,D,rho[i],s['valve_Cd'])*(mass[i]/target[i])**2
        bore=bore_from_coefficient(k,D,rho[i],s['valve_Cd']) or D
        u=((bore/maximum)**2-s['valve_min_area_fraction'])/(1-s['valve_min_area_fraction'])
        result.append(np.clip(u,0,1))
    return np.asarray(result)
