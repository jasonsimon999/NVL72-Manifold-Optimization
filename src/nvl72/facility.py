"""Two-loop heat balance and explicitly approximate rating-envelope screening."""
from .coolant import Coolant
from .units import c_to_k, k_to_c, lpm_to_m3s

def facility_check(c, heat_W, total_mass, return_K, coolant):
    f=c['facility']; d=c['cdu']; racks=d['served_racks']
    fw=Coolant(f['coolant'],c['coolant']['property_file'])
    tin=c_to_k(f['supply_C']); ts=c_to_k(c['rack']['supply_C'])
    fm=lpm_to_m3s(f['flow_LPM'])*fw.properties(tin).rho
    fout=fw.temperature(fw.enthalpy(tin)+heat_W*racks/fm)
    atd=float(ts-tin)
    rated=Coolant(d.get('rating_coolant','PG25'),c['coolant']['property_file']).properties(c_to_k(d.get('rating_supply_C',40.)))
    rated_mass=lpm_to_m3s(d['nominal_flow_LPM'])*rated.rho
    rate_ratio=total_mass*racks*coolant.properties(ts).cp/(rated_mass*rated.cp)
    available=d['capacity_W']*max(0,min(1,atd/d['approach_K'],float(rate_ratio)))
    qmax=min(float(fm*fw.properties((tin+fout)/2).cp),float(total_mass*racks*coolant.properties((ts+return_K)/2).cp))*max(0,float(return_K-tin))
    rise=f.get('design_deltaT_K',12.)
    pinch=f.get('minimum_hot_pinch_K',0.)
    if rise<=0 or pinch<0: raise ValueError('Facility design rise must be positive and pinch nonnegative')
    allowed=min(float(tin+rise),float(c_to_k(f['max_return_C'])),float(return_K-pinch))
    dh=float(fw.enthalpy(allowed)-fw.enthalpy(tin)) if allowed>tin else 0.
    required=heat_W*racks/dh/fw.properties(tin).rho*60000 if dh>0 else None
    hot=float(return_K-fout)
    import math
    lmtd=((atd+hot)/2 if abs(atd-hot)<1e-8 else (hot-atd)/math.log(hot/atd)) if min(atd,hot)>0 else None
    return {'FWS_return_C':float(k_to_c(fout)), 'FWS_supply_C':f['supply_C'],
            'FWS_flow_LPM':f['flow_LPM'],'FWS_deltaT_K':float(fout-tin),
            'required_flow_LPM':None if required is None else float(required),
            'design_deltaT_K':rise,'minimum_hot_pinch_K':pinch,
            'maximum_FWS_supply_C':c['rack']['supply_C']-d['approach_K'],
            'required_UA_W_K':float(heat_W*racks/lmtd) if lmtd and lmtd>0 else None,
            'heat_balance_residual_W':float(fm*(fw.enthalpy(fout)-fw.enthalpy(tin))-heat_W*racks),
            'TCS_capacity_rate_ratio':float(rate_ratio),'rating_coolant':d.get('rating_coolant','PG25'),
            'approach_K':atd,'HX_available_W_per_rack':float(available/racks),
            'effectiveness_required':float(heat_W*racks/qmax) if qmax>0 else None,
            'hot_end_pinch_K':float(return_K-fout),
            'model':'conservative rating scaling by cold-end approach and TCS capacity rate; no vendor UA map',
            'aggregate_heat_W':float(heat_W*racks)}
