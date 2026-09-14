"""Temperature/property-coupled rack solver and CDU/facility boundary checks."""
from copy import deepcopy
from dataclasses import asdict
import numpy as np
from scipy.optimize import brentq
from .config import validate
from .coolant import Coolant
from .rack import tray_data
from .thermal import temperatures
from .hydraulics import solve_network
from .manifold import geometry, volume
from .components import pipe_loss, reduced_loss
from .objectives import targets, metrics
from .cdu import pump_head, power
from .facility import facility_check
from .coldplate import channel_model
from .design_analysis import chip_estimates, CHIP_DEFAULTS
from .constraint_policy import apply_policy
from .orifices import bore_from_coefficient
from .units import c_to_k,k_to_c,lpm_to_m3s,m3s_to_lpm

def solve(c: dict) -> dict:
    c=deepcopy(c)
    if c.get('balancing_mode','resistance') not in ('resistance','auto_equivalent'):
        raise ValueError('Unknown balancing mode')
    c['facility'].setdefault('design_deltaT_K',12.)
    c['facility'].setdefault('minimum_hot_pinch_K',0.)
    c['cdu'].setdefault('rating_coolant','water' if c['cdu']['mode']=='in_row' else 'PG25')
    c['cdu'].setdefault('rating_supply_C',40.)
    for kind,bounds in CHIP_DEFAULTS.items():
        spec=c.setdefault('chip_temperature',{}).setdefault(kind,{})
        spec.setdefault('resistance_range_K_W',list(bounds))
        spec.setdefault('target_max_C',80.)
        spec.setdefault('manufacturer_limit_C',None)
    validate(c)
    if c['rack']['operating_mode']=='pump': return _pump_solve(c)
    ids,kinds,heat,branches=tray_data(c); n=len(ids)
    coolant=Coolant(c['coolant']['type'],c['coolant']['property_file'],c['coolant']['viscosity_multiplier'])
    ts=float(c_to_k(c['rack']['supply_C'])); ps=coolant.properties(ts)
    total=float(lpm_to_m3s(c['rack']['flow_LPM'])*ps.rho)
    # Equal-flow thermal initialization is less fragile than near-zero workload targets.
    m=np.full(n,total/n)
    tout,tr,energy=temperatures(m,heat,ts,coolant)
    tb=(ts+tout)/2; opts=c['solver']; count=0
    for iteration in range(1,opts['max_property_iterations']+1):
        hp=solve_network(c,branches,total,ps,coolant.properties(tb),coolant.properties(tr),m)
        count+=hp.nfev
        tn,rn,energy=temperatures(hp.mass_flow,heat,ts,coolant)
        temp_error=max(float(np.max(abs(tn-tout))),float(np.max(abs(rn-tr))))
        flow_error=float(np.max(abs(hp.mass_flow-m)/np.maximum(m,1e-12)))
        m=hp.mass_flow
        tout=tn
        if temp_error<opts['temperature_tolerance_K'] and flow_error<opts['flow_relative_tolerance']:
            # Re-evaluate hydraulic closure at final thermal state, not stale properties.
            final=solve_network(c,branches,total,ps,coolant.properties((ts+tout)/2),coolant.properties(rn),m)
            if np.max(abs(final.mass_flow-m)/m)<opts['flow_relative_tolerance']:
                hp=final; m=hp.mass_flow; tout,tr,energy=temperatures(m,heat,ts,coolant)
                break
        a=opts['relaxation']; tb=(1-a)*tb+a*(ts+tn)/2; tr=(1-a)*tr+a*rn
    else: raise RuntimeError(f'Fluid property iteration failed after {iteration} iterations')
    if energy>opts['energy_relative_tolerance']: raise RuntimeError('Global energy conservation failed')
    z,dz,ds,dr=geometry(c)
    extra={'external_piping':0.,'external_fittings':0.,'external_equipment':0.}
    if c['external']['enabled']:
        e=c['external']; pmean=coolant.properties((ts+tr[0])/2)
        loss=pipe_loss(total,pmean.rho,pmean.mu,e['diameter_m'],e['length_m'],c['geometry']['roughness_m'],e['minor_K'])
        extra={'external_piping':float(loss['friction']),'external_fittings':float(loss['minor']),
               'external_equipment':float(reduced_loss(total,e['equipment_K']))}
    system=hp.head_Pa+sum(extra.values()); q=float(lpm_to_m3s(c['rack']['flow_LPM']))
    hyd,elec=power(system,q,c['cdu']['efficiency'])
    target=targets(total,heat,c['optimization']['target']); met,error=metrics(m,heat,target,tout)
    met.update({'rack_dp_Pa':hp.head_Pa,'system_dp_Pa':system,'rack_flow_LPM':c['rack']['flow_LPM'],
                'heat_W':float(heat.sum()),'T_return_C':float(k_to_c(tr[0])), 'rack_deltaT_K':float(tr[0]-ts),
                'pump_hydraulic_W':hyd,'pump_electrical_W':elec,'header_volume_m3':volume(c),
                'min_header_ID_m':float(min(ds.min(),dr.min())),'max_header_ID_m':float(max(ds.max(),dr.max())),
                'max_header_velocity_m_s':float(max(abs(hp.supply_losses['velocity']).max(),abs(hp.return_losses['velocity']).max()))})
    facility=facility_check(c,float(heat.sum()),total,tr[0],coolant)
    limit=c['constraints']; d=c['cdu']; constraints={}
    def add(name,margin,scale,unit):
        constraints[name]={'margin':float(margin),'normalized_margin':float(margin/scale),'units':unit,'pass':bool(margin>=-1e-6)}
    add('CDU_external_head',d['available_dp_Pa']-system,d['available_dp_Pa'],'Pa')
    add('pump_curve',float(pump_head(q*d['served_racks'],d))-system,d['available_dp_Pa'],'Pa')
    add('rack_flow',limit['rack_flow_max_LPM']-c['rack']['flow_LPM'],limit['rack_flow_max_LPM'],'LPM')
    add('CDU_aggregate_flow',d['nominal_flow_LPM']-c['rack']['flow_LPM']*d['served_racks'],d['nominal_flow_LPM'],'LPM')
    add('supply_temperature',limit['supply_max_C']-c['rack']['supply_C'],20,'K')
    add('return_temperature',limit['return_max_C']-met['T_return_C'],20,'K')
    add('branch_outlet',limit['branch_outlet_max_C']-met['T_out_max_C'],20,'K')
    dh_allowed=coolant.enthalpy(c_to_k(limit['branch_outlet_max_C']))-coolant.enthalpy(ts)
    add('minimum_thermal_flow',float(np.min(m-heat/max(float(dh_allowed),1e-12))),total/n,'kg/s')
    add('header_velocity',limit['header_velocity_max_m_s']-met['max_header_velocity_m_s'],limit['header_velocity_max_m_s'],'m/s')
    # Check endpoint and piecewise diameters too, beyond finite-volume midpoints.
    gx=np.linspace(0,1,1001)
    from .manifold import diameter_profile
    all_d=np.r_[diameter_profile(c['geometry']['supply'],gx),diameter_profile(c['geometry']['return'],gx)]
    met['min_header_ID_m']=float(all_d.min());met['max_header_ID_m']=float(all_d.max())
    met['resolved_fluid_volume_m3']=met['header_volume_m3']+sum(np.pi*b['diameter_m']**2/4*b['tube_length_m'] for b in branches)
    add('minimum_diameter',float(all_d.min())-limit['diameter_min_m'],limit['diameter_min_m'],'m')
    add('maximum_diameter',limit['diameter_max_m']-float(all_d.max()),limit['diameter_max_m'],'m')
    add('HX_capacity',facility['HX_available_W_per_rack']-heat.sum(),d['capacity_W']/d['served_racks'],'W')
    add('HX_approach',facility['approach_K']-d['approach_K'],d['approach_K'],'K')
    add('HX_cold_pinch',facility['approach_K']-1e-4,20,'K')
    add('HX_hot_pinch',facility['hot_end_pinch_K']-max(1e-4,facility['minimum_hot_pinch_K']),20,'K')
    add('FWS_design_temperature_rise',facility['design_deltaT_K']-facility['FWS_deltaT_K'],facility['design_deltaT_K'],'K')
    add('FWS_return',c['facility']['max_return_C']-facility['FWS_return_C'],20,'K')
    if c['facility'].get('available_capacity_W') is not None:
        cap=c['facility']['available_capacity_W']
        if cap<=0: raise ValueError('Facility available capacity must be positive')
        add('facility_available_duty',cap-facility['aggregate_heat_W'],cap,'W')
    if c['facility'].get('UA_W_K') is not None:
        ua=c['facility']['UA_W_K']
        if ua<=0: raise ValueError('HX UA must be positive')
        add('HX_user_UA',ua-(facility['required_UA_W_K'] if facility['required_UA_W_K'] is not None else 2*ua),ua,'W/K')
    if d.get('secondary_max_C') is not None:
        add('CDU_secondary_max_temperature',d['secondary_max_C']-max(met['T_return_C'],c['rack']['supply_C']),20,'K')
    if d.get('secondary_min_C') is not None:
        add('CDU_secondary_min_temperature',min(met['T_return_C'],c['rack']['supply_C'])-d['secondary_min_C'],20,'K')
    met['minimum_normalized_margin']=min(x['normalized_margin'] for x in constraints.values())
    # Flow-weighted PATH head budget, not sum of parallel branch pressure losses.
    weights=m/total
    budget={k:float(np.dot(weights,v)) for k,v in hp.branch_losses.items()}
    for label,key in [('header_friction','friction'),('header_minor','minor')]:
        budget[label]=float(np.dot(weights,np.cumsum(hp.supply_losses[key]+hp.return_losses[key])))
    budget['hydrostatic_net']=float(np.dot(weights,hp.gravity_path_Pa)); budget.update(extra)
    if abs(sum(budget.values())-system)>opts['pressure_tolerance_Pa']: raise RuntimeError('Pressure budget closure failed')
    trays=[]
    for i,tray in enumerate(ids):
        trays.append({'tray_id':tray,'tray_type':kinds[i],'rack_position':i+1,'elevation_m':float(z[i]),'heat_load_W':float(heat[i]),
                      'mass_flow_kg_s':float(m[i]),'target_flow_LPM':float(m3s_to_lpm(target[i]/ps.rho)),
                      'actual_flow_LPM':float(m3s_to_lpm(m[i]/ps.rho)),
                      'flow_error_percent':float(error[i]*100) if target[i]>0 else None,
                      'supply_pressure_kPa':float(hp.supply_Pa[i]/1000),'return_pressure_kPa':float(hp.return_Pa[i]/1000),
                      'branch_dP_kPa':float((hp.supply_Pa[i]-hp.return_Pa[i])/1000),
                      'T_in_C':float(k_to_c(ts)),'T_out_C':float(k_to_c(tout[i])), 'deltaT_C':float(tout[i]-ts),
                      'return_mix_C':float(k_to_c(tr[i])), 'coldplate_dP_kPa':float(hp.branch_losses['coldplates'][i]/1000),
                      'qdc_dP_kPa':float(hp.branch_losses['qdcs'][i]/1000),
                      'branch_other_dP_kPa':float(sum(v[i] for k,v in hp.branch_losses.items() if k not in ('coldplates','qdcs'))/1000)})
    channel=None
    if c['coldplate']['enabled']:
        channel=channel_model(m,heat,(ts+tout)/2,coolant.properties((ts+tout)/2),c['coldplate'])
        met.update(T_chip_max_C=float(k_to_c(channel['T_chip_equivalent_K']).max()),chip_spread_K=float(np.ptp(channel['T_chip_equivalent_K'])))
    for i,tray in enumerate(trays):
        bore=branches[i].get('orifice_diameter_m')
        density=float(coolant.properties((ts+tout[i])/2).rho)
        if c.get('balancing_mode')=='auto_equivalent':
            bore=bore_from_coefficient(branches[i]['restriction_K'],branches[i]['diameter_m'],density,branches[i].get('orifice_Cd',.62))
        tray['orifice_diameter_mm']=None if bore is None else bore*1000
        tray['orifice_reference_density_kg_m3']=density
        tray['balancing_restriction_K']=branches[i]['restriction_K']
        tray['orifice_Cd']=branches[i].get('orifice_Cd',.62)
        tray['orifice_dP_kPa']=float(hp.branch_losses['orifices'][i]/1000)
    chips=chip_estimates(c,trays)
    add('chip_assumed_target',min(x['target_margin_K'] for x in chips),20,'K')
    known=[x['manufacturer_margin_K'] for x in chips if x['manufacturer_margin_K'] is not None]
    if known: add('chip_entered_manufacturer_limit',min(known),20,'K')
    apply_policy(c,constraints)
    met['minimum_normalized_margin']=min(x['normalized_margin'] for x in constraints.values() if x['enforced'])
    met['minimum_screening_margin']=min(x['normalized_margin'] for x in constraints.values())
    met['T_junction_upper_max_C']=max(x['junction_high_C'] for x in chips)
    frozen=None
    if c.get('balancing_mode')=='auto_equivalent':
        frozen=deepcopy(c);frozen['balancing_mode']='resistance'
        for kind in ('compute','switch'): frozen['branches'][kind]['restriction_K']=0.
        for tray in trays:
            frozen['branches']['overrides'].setdefault(tray['tray_id'],{}).update(restriction_K=0.,orifice_diameter_m=None if tray['orifice_diameter_mm'] is None else tray['orifice_diameter_mm']/1000)
    return {'config':c,'metrics':met,'trays':trays,'constraints':constraints,'feasible':all(v['pass'] for v in constraints.values() if v['enforced']),
            'screening_pass':all(v['pass'] for v in constraints.values()),'fixed_orifice_config':frozen,
            'chip_estimates':chips,'qualification':'Design screening only: unverified chip resistances, component losses, pump envelope, HX performance and site limits'+('; EG50 CDU/material compatibility unverified' if c['coolant']['type']=='EG50' else ''),
            'facility':facility,'pressure_budget_Pa':budget,'hydraulics':asdict(hp),'coldplate':channel,
            'validation':{'mass_relative_error':hp.mass_error,'energy_relative_error':energy,'pressure_residual_Pa':hp.residual_Pa,
                          'property_iterations':iteration,'nfev':count,'temperature_error_K':temp_error,'flow_relative_error':flow_error,'converged':True}}

def _pump_solve(c):
    fixed=deepcopy(c); fixed['rack']['operating_mode']='fixed_flow'
    d=c['cdu']; qfree=d['nominal_flow_LPM']*(d['shutoff_dp_Pa']/(d['shutoff_dp_Pa']-d['available_dp_Pa']))**0.5*d['speed']/d['served_racks']
    cache={}
    def f(flow):
        fixed['rack']['flow_LPM']=float(flow)
        r=solve(fixed); cache[float(flow)]=r
        return float(pump_head(lpm_to_m3s(flow*d['served_racks']),d))-r['metrics']['system_dp_Pa']
    valid=[]
    for flow in np.linspace(max(1,qfree*0.15),qfree,18):
        try: valid.append((float(flow),f(float(flow))))
        except (ValueError,RuntimeError): continue
    bracket=next(((a[0],b[0]) for a,b in zip(valid[:-1],valid[1:]) if a[1]*b[1]<=0),None)
    if bracket is None: raise ValueError('No thermally valid pump/system intersection; inspect speed, load, property limits and pump curve')
    flow=brentq(f,*bracket,xtol=1e-7); f(flow); r=cache[flow]
    r['config']['rack']['operating_mode']='pump'
    r['validation']['pump_intersection_residual_Pa']=abs(f(flow))
    return r
