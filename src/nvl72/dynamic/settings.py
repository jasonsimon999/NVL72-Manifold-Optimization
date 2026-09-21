"""Editable research assumptions; none are proprietary NVL72 specifications."""
from copy import deepcopy

DEFAULTS = {
    'duration_s': 300., 'dt_s': 2., 'seed': 72, 'scenario': 'heterogeneous',
    'low_load': .3, 'high_load': 1., 'spike_s': 40., 'duty': .4,
    'correlation': .4, 'ramp_per_s': .2, 'localized_count': 4,
    'compute_power_scale': 1., 'switch_power_scale': 1.,
    'compute_liquid_fraction': 1., 'switch_liquid_fraction': 1.,
    'compute_C_J_K': 12000., 'switch_C_J_K': 4000.,
    'compute_R_K_W': .004, 'switch_R_K_W': .012,
    'coolant_C_J_K': 1200., 'chip_limit_C': 80., 'outlet_limit_C': 65.,
    'target_rise_K': 15., 'minimum_flow_fraction': .15,
    # Optimized mode uses the measured flow target to choose an effective
    # variable orifice area.  The comparison layer can still fall back to the
    # fixed plate when that trial is not an improvement.
    'controller': 'combined', 'control_s': 2., 'sensor_s': 2.,
    'sensor_noise_K': .1, 'sensor_bias_K': 0., 'temperature_target_C': 72.,
    'kp_per_K': .025, 'ki_per_K_s': .0005, 'flow_gain': .3,
    'valve_min_area_fraction': .015, 'valve_max_bore_fraction': .95,
    'valve_Cd': .62, 'valve_body_K': 2., 'valve_tau_s': 15.,
    'valve_stroke_s': 90., 'valve_deadband': .005,
    'valve_running_W': 1.5, 'valve_holding_W': .4, 'electronics_W': 5.,
    'fail_position': 1., 'controlled_branches': 27,
    'pump_mode': 'demand', 'pump_tau_s': 10., 'pump_min_speed': .2,
    'pump_max_speed': 1.2, 'pump_efficiency': .6, 'pump_enabled': True,
    'coldplate_scale': 1., 'qd_scale': 1., 'header_scale': 1.,
    'supply_offset_K': 0., 'design_flow_scale': 1.,
    'event_s': 100., 'reconnect_s': 200., 'reconnect_ramp_s': 20.,
    'failure': 'none', 'failure_tray': 0, 'sensor_failure_bias_K': 8.,
    'electricity_per_kWh': .12, 'operating_hours': 8760.,
    'cost_case': 'nominal', 'payback_horizon_years': 5.,
    'optimization_temperature_weight': 1.0,
    'optimization_flow_weight': .5,
    'optimization_worst_flow_weight': .25,
    'optimization_pump_weight': .5,
    'optimization_pressure_weight': .25,
    'optimization_actuation_weight': .1,
    'optimization_fallback_tolerance': 1e-6,
}

COSTS = {
    'low': dict(orifice=10., valve=100., temperature_sensor=15., flow_sensor=30.,
                pressure_sensors=100., controller=150., wiring=100., power_supply=50.,
                integration=300., fixed_maintenance=30., active_maintenance=100.),
    'nominal': dict(orifice=25., valve=350., temperature_sensor=40., flow_sensor=100.,
                    pressure_sensors=300., controller=500., wiring=400., power_supply=150.,
                    integration=1500., fixed_maintenance=75., active_maintenance=400.),
    'high': dict(orifice=50., valve=800., temperature_sensor=100., flow_sensor=250.,
                 pressure_sensors=800., controller=1500., wiring=1200., power_supply=400.,
                 integration=5000., fixed_maintenance=150., active_maintenance=1200.),
}

SCENARIOS = ['steady', 'rack_step', 'localized', 'heterogeneous', 'worst_case',
             'bursts', 'remove_compute', 'remove_switch', 'remove_several', 'reinstall']
CONTROLLERS = ['fixed', 'reactive', 'feedforward', 'combined', 'optimized', 'locked']
FAILURES = ['none', 'stuck_closed', 'stuck_open', 'stuck_half', 'sensor_high',
            'sensor_low', 'communications', 'pump_lag']

def settings(**overrides):
    s = deepcopy(DEFAULTS)
    s.update(overrides)
    validate(s)
    return s

def validate(s):
    import math
    for k, v in s.items():
        if isinstance(v, (float, int)) and not math.isfinite(v):
            raise ValueError(f'{k} must be finite')
    for k in ('duration_s','dt_s','compute_C_J_K','switch_C_J_K','coolant_C_J_K',
              'compute_R_K_W','switch_R_K_W','control_s','sensor_s','valve_tau_s',
              'valve_stroke_s','pump_tau_s','target_rise_K','spike_s','reconnect_ramp_s',
              'pump_efficiency','header_scale','design_flow_scale','valve_Cd'):
        if s[k] <= 0: raise ValueError(f'{k} must be positive')
    for k in ('low_load','high_load','duty','correlation','compute_liquid_fraction',
              'switch_liquid_fraction','minimum_flow_fraction','valve_min_area_fraction',
              'valve_max_bore_fraction','fail_position'):
        if not 0 <= s[k] <= 1: raise ValueError(f'{k} must be between 0 and 1')
    if not 0 < s['valve_max_bore_fraction'] < 1: raise ValueError('Maximum bore must be below branch ID')
    if s['valve_min_area_fraction']>=1: raise ValueError('Minimum valve area fraction must be below 1')
    if s['pump_efficiency'] > 1 or s['valve_Cd'] > 1: raise ValueError('Efficiency and Cd cannot exceed 1')
    if s['pump_min_speed'] < 0 or s['pump_max_speed'] < s['pump_min_speed']: raise ValueError('Invalid pump speed limits')
    if s['duration_s']/s['dt_s'] > 5000: raise ValueError('Limit a run to 5000 timesteps')
    if s['duration_s'] < s['dt_s']: raise ValueError('Duration must include at least one timestep')
    if s['payback_horizon_years'] <= 0: raise ValueError('Payback horizon must be positive')
    if not 0 <= s['controlled_branches'] <= 27: raise ValueError('Controlled branches must be between 0 and 27')
    if s['dt_s'] > min(s['control_s'],s['sensor_s']): raise ValueError('Timestep must not exceed sensor/control interval')
    if s['scenario'] not in SCENARIOS or s['controller'] not in CONTROLLERS or s['failure'] not in FAILURES: raise ValueError('Unknown scenario/controller/failure')
    if s['pump_mode'] not in ('constant_speed','constant_dp','demand'): raise ValueError('Unknown pump mode')
    for k in ('coldplate_scale','qd_scale','compute_power_scale','switch_power_scale','ramp_per_s',
              'sensor_noise_K','valve_body_K','valve_running_W','valve_holding_W','electronics_W',
              'electricity_per_kWh','operating_hours','pump_max_speed','valve_deadband',
              'optimization_temperature_weight','optimization_flow_weight','optimization_worst_flow_weight',
              'optimization_pump_weight','optimization_pressure_weight','optimization_actuation_weight',
              'optimization_fallback_tolerance'):
        if s[k] < 0: raise ValueError(f'{k} cannot be negative')
    if s['low_load'] > s['high_load']: raise ValueError('Low load cannot exceed high load')
