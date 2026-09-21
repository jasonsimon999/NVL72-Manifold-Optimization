"""Sample-and-hold PI/flow feedback and finite-speed valve actuator."""
import numpy as np

def demand(power, cp, base_mass, s):
    return np.maximum(power/(cp*s['target_rise_K']), base_mass*s['minimum_flow_fraction'])

def command(mode, opening, temperature, mass, target, integral, s, interval):
    error = temperature-s['temperature_target_C']  # Hotter -> open, never the opposite.
    trial = np.clip(integral+error*interval, -500., 500.)
    flow_error = (target-mass)/np.maximum(target,1e-8)
    if mode == 'optimized':
        # Flow demand maps directly to an area (and therefore an effective
        # orifice diameter).  For a quadratic restriction, d ∝ sqrt(m_dot).
        # The small temperature trim protects the thermal target without
        # turning the controller into an unconstrained pressure chase.
        area_ratio=np.sqrt(np.clip(target/np.maximum(mass,1e-8),0.,4.))
        trim=np.clip(s['kp_per_K']*error+s['ki_per_K_s']*trial,0.,.25)
        raw=opening*area_ratio + .2*flow_error + trim
    elif mode == 'reactive': raw = .5+s['kp_per_K']*error+s['ki_per_K_s']*trial
    elif mode == 'feedforward': raw = opening+s['flow_gain']*flow_error
    else:
        # Temperature trims the flow-tracking error, rather than integrating
        # a large temperature increment directly into valve travel each sample.
        trim=np.clip(s['kp_per_K']*error+s['ki_per_K_s']*trial,0.,1.)
        raw = opening+s['flow_gain']*(flow_error+trim)
    # Conditional integration prevents windup at either travel stop.
    accept = ((raw >= 0)&(raw <= 1)) | ((raw > 1)&(error < 0)) | ((raw < 0)&(error > 0))
    integral = np.where(accept,trial,integral)
    return np.clip(raw,0,1), integral

def actuate(position, target, s, dt):
    error = target-position
    delta = np.where(abs(error)>s['valve_deadband'],error*(1-np.exp(-dt/s['valve_tau_s'])),0.)
    return np.clip(position+np.clip(delta,-dt/s['valve_stroke_s'],dt/s['valve_stroke_s']),0,1)
