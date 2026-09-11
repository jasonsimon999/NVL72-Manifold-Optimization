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
    rated_mass=lpm_to_m3s(d['nominal_flow_LPM'])*coolant.properties(ts).rho
    rate_ratio=total_mass*racks/rated_mass
    available=d['capacity_W']*max(0,min(1,atd/d['approach_K'],float(rate_ratio)))
    qmax=min(float(fm*fw.properties((tin+fout)/2).cp),float(total_mass*racks*coolant.properties((ts+return_K)/2).cp))*max(0,float(return_K-tin))
    return {'FWS_return_C':float(k_to_c(fout)), 'FWS_supply_C':f['supply_C'],
            'approach_K':atd,'HX_available_W_per_rack':float(available/racks),
            'effectiveness_required':float(heat_W*racks/qmax) if qmax>0 else None,
            'hot_end_pinch_K':float(return_K-fout),
            'model':'conservative rating scaling by cold-end approach and TCS capacity rate; no vendor UA map',
            'aggregate_heat_W':float(heat_W*racks)}
