"""Source and assumption registry, including every editable dynamic setting."""
from .settings import DEFAULTS,COSTS

REFERENCES = {
    'NVIDIA hardware': 'https://docs.nvidia.com/dgx/dgxgb200-user-guide/hardware.html',
    'NVIDIA DPS': 'https://docs.nvidia.com/datacenter/dps/versions/latest/guides/runbooks/maxlps-simple-mode-pilot.html',
    'OCP manifold': 'https://www.opencompute.org/documents/ocp-white-paper-rack-manifold-requirements-and-qualification-v3-pdf',
    'OCP loop': 'https://www.opencompute.org/documents/cold-plate-cooling-loop-requirements-rev-2-pdf',
    'OCP modular TCS': 'https://www.opencompute.org/documents/ocp-modular-tcs-rev-1-final-2025-pdf',
    'ASHRAE resiliency research': 'https://www.ashrae.org/File%20Library/Technical%20Resources/Research/Research%20Project%20Bidding/1972-RFP.pdf',
    'Belimo LRB24-SR': 'https://www.belimo.com/us/shop/en_US/p?code=LRB24-SR',
    'Measured H100 training workload': 'https://arxiv.org/abs/2412.08602',
    'NVIDIA power and thermals': 'https://docs.nvidia.com/multi-node-nvlink-systems/multi-node-tuning-guide/power-thermals.html',
}

NOTES = {
    'compute_C_J_K': ('J/K', '3000–30000', 'Effective tray thermal inertia; requires transient test identification.'),
    'switch_C_J_K': ('J/K', '1000–12000', 'Effective tray thermal inertia; not a published NVSwitch value.'),
    'compute_R_K_W': ('K/W', '.002–.008', 'Equivalent whole-tray solid-to-mixed-coolant resistance, not per-GPU junction R.'),
    'switch_R_K_W': ('K/W', '.006–.024', 'Equivalent whole-tray resistance, not per-ASIC junction R.'),
    'coolant_C_J_K': ('J/K', '400–4000', 'Well-mixed local coolant thermal storage; not total CDU inventory.'),
    'compute_liquid_fraction': ('fraction', '.7–1', 'Fraction of electrical-equivalent tray load entering liquid. 1 reproduces legacy heat assignment, not a measured fraction.'),
    'switch_liquid_fraction': ('fraction', '.5–1', 'Separates electrical power from liquid heat; no verified NVL72 calorimetry.'),
    'valve_stroke_s': ('s', '5–120', '90 s representative motorized HVAC actuator; not an NVL72 valve or validated coolant-compatible selection.'),
    'valve_running_W': ('W/valve', '.5–6', 'Representative Belimo actuator running power.'),
    'valve_holding_W': ('W/valve', '0–3', 'Representative Belimo actuator holding power.'),
    'fail_position': ('fraction open', '0–1', 'Commanded communications-loss position, assuming control power remains. The cited LRB24-SR is NON fail-safe; mechanical fail-open requires different hardware.'),
    'chip_limit_C': ('°C', '65–90', 'User screening target for representative thermal node, not NVIDIA throttle specification.'),
    'temperature_target_C': ('°C', '55–78', 'Controller setpoint below screening limit; tuning assumption.'),
    'valve_Cd': ('dimensionless', '.5–.8', 'Effective-area surrogate; must replace with measured Cv versus stroke for hardware selection.'),
    'valve_body_K': ('dimensionless', '.5–10', 'Additional full-open body loss, referenced to branch tube velocity.'),
    'correlation': ('fraction', '0–1', 'Probability of shared burst state, not an asserted Pearson correlation coefficient.'),
    'pump_efficiency': ('fraction', '.3–.8', 'Constant efficiency approximation; actual efficiency map unavailable.'),
    'target_rise_K': ('K', '8–20', 'Power-derived target flow uses this coolant temperature rise.'),
    'minimum_flow_fraction': ('fraction', '.05–.3', 'Minimum flow relative to frozen design flow, not a published cold-plate minimum.'),
}

def registry(s, config=None):
    rows=[]
    def add(parameter,value,units,kind,confidence,source,notes,ranges=''):
        rows.append(dict(parameter=parameter,value=str(value),units=units,classification=kind,
                         confidence=confidence,source=source,reference=REFERENCES.get(source,source),
                         range=ranges,notes=notes))
    add('compute trays',18,'trays','Published','HIGH','NVIDIA hardware','4 GPUs + 2 Grace CPUs per compute tray.')
    add('switch trays',9,'trays','Published','HIGH','NVIDIA hardware','NVLink switch trays.')
    add('switch aggregate electrical reference',11160,'W/rack','Published','HIGH','NVIDIA DPS','Recommended aggregate static power-model input, not measured liquid heat.')
    add('switch tray electrical reference',1240,'W/tray','Derived','MEDIUM','NVIDIA DPS','11160 / 9, assuming equal distribution.')
    add('rack power context',120,'kW','Estimated','LOW','NVIDIA hardware','Approximate context only; actual simulation uses the sum of configured tray electrical loads.')
    add('manifold velocity advisory',1.5,'m/s','Published','HIGH','OCP manifold','Table 3 guideline; applicability depends on geometry/materials. Report separately, not universal NVL72 hard limit.')
    add('disconnected branch flow',0,'kg/s','Derived','MEDIUM','OCP loop','Both ends of dripless QD close; excludes air purge, residual spills and pressure surge.')
    effective=dict(s,costs=s.get('costs',COSTS[s['cost_case']]))
    for key,value in effective.items():
        if key=='costs':
            for cost,v in value.items():add('cost.'+cost,v,'USD or USD/year','User-adjustable assumption','LOW','Engineering budget','Editable budget, not a supplier quotation. Maintenance entries are USD/year.')
            continue
        unit='dimensionless / selection'
        if key.endswith('_s'):unit='s'
        elif key.endswith('_W'):unit='W'
        elif key.endswith('_K'):unit='K'
        elif key.endswith('_C'):unit='°C'
        if key=='operating_hours':unit='hours/year'
        elif key=='electricity_per_kWh':unit='USD/kWh'
        elif key=='payback_horizon_years':unit='years'
        elif key=='kp_per_K':unit='1/K'
        elif key=='ki_per_K_s':unit='1/(K s)'
        elif key=='ramp_per_s':unit='utilization fraction/s'
        unit,ranges,note=NOTES.get(key,(unit,'User editable','Synthetic scenario/control assumption; not published NVL72 data.'))
        source='Engineering assumption';confidence='LOW';kind='User-adjustable assumption'
        if key in ('valve_stroke_s','valve_running_W','valve_holding_W'):
            source='Belimo LRB24-SR'
            note+=' Default matches manufacturer; current setting may be an override.'
        if key in ('duty','spike_s','ramp_per_s','correlation','low_load','high_load'):
            source='Measured H100 training workload';note+=' Motivates fluctuating traces only; numerical settings are synthetic and are not fitted NVL72 telemetry.'
        add(key,value,unit,kind,confidence,source,note,ranges)
    if config:
        def walk(obj,path='baseline'):
            for k,v in obj.items():
                name=path+'.'+k
                if isinstance(v,dict):walk(v,name)
                else:add(name,v,'see baseline schema','User-adjustable assumption','LOW','data/sources.yaml',
                         'Inherited without redesign. Original provenance in baseline Sources & assumptions and data/sources.yaml; no new NVL72 validation claimed.')
        walk({k:config[k] for k in ('rack','power','geometry','branches','cdu','coolant','facility')})
    return rows
