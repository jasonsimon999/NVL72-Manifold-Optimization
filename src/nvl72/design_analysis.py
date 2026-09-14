"""Transparent engineering screens; chip resistances are uncalibrated assumptions."""
from .objectives import objective

CHIP_DEFAULTS = {'GPU': (.010, .020), 'CPU': (.020, .040), 'NVSwitch': (.015, .035)}

def chip_estimates(c, trays):
    settings = c.get('chip_temperature', {})
    rows = []
    p = c['power']
    for tray in trays:
        if tray['tray_type'] == 'compute':
            total = p['gpu_W_each']*p['gpus_per_compute_tray'] + p['grace_cpu_W_each']*p['cpus_per_compute_tray']
            parts = [('GPU', p['gpus_per_compute_tray'], p['gpu_W_each']/total if total else 0),
                     ('CPU', p['cpus_per_compute_tray'], p['grace_cpu_W_each']/total if total else 0)]
        else:
            parts = [('NVSwitch', 2, .5)]
        for kind,count,fraction in parts:
            spec = settings.get(kind, {})
            lo,hi = spec.get('resistance_range_K_W', CHIP_DEFAULTS[kind])
            target = spec.get('target_max_C', 80.)
            limit = spec.get('manufacturer_limit_C')
            if not 0 <= lo <= hi: raise ValueError('Chip resistance bounds must satisfy 0 <= low <= high')
            power = tray['heat_load_W']*fraction
            low = tray['T_out_C']+power*lo; high = tray['T_out_C']+power*hi
            rows.append(dict(tray_id=tray['tray_id'],component=kind,count=count,power_each_W=power,
                             coolant_reference_C=tray['T_out_C'],resistance_low_K_W=lo,resistance_high_K_W=hi,
                             junction_low_C=low,junction_high_C=high,target_max_C=target,
                             target_margin_K=target-high,manufacturer_limit_C=limit,
                             manufacturer_margin_K=None if limit is None else limit-high))
    return rows

def design_summary(named_results):
    rows=[]
    for name,r in named_results.items():
        m=r['metrics']; f=r['facility']; chips=r['chip_estimates']
        rows.append(dict(design=name,coolant=r['config']['coolant']['type'],heat_kW=m['heat_W']/1000,
            flow_LPM=m['rack_flow_LPM'],supply_C=r['config']['rack']['supply_C'],
            enforced_requirements_pass=r['feasible'],all_screens_pass=r.get('screening_pass',all(v['pass'] for v in r['constraints'].values())),qualification=r['qualification'],
            score_lower_is_better=objective(r),RMS_flow_error=m['RMS_target_error'],
            outlet_max_C=m['T_out_max_C'],outlet_spread_K=m['outlet_spread_K'],
            chip_upper_max_C=max(x['junction_high_C'] for x in chips),
            chip_target_margin_K=min(x['target_margin_K'] for x in chips),
            pressure_kPa=m['system_dp_Pa']/1000,pump_W=m['pump_electrical_W'],
            header_volume_L=m['header_volume_m3']*1000,FWS_required_LPM=f['required_flow_LPM'],
            FWS_return_C=f['FWS_return_C'],minimum_margin=m['minimum_normalized_margin'],
            limiting_constraint=min((k for k,v in r['constraints'].items() if v.get('enforced',True)),key=lambda k:r['constraints'][k]['normalized_margin'])))
    return rows
