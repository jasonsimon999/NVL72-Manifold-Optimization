"""Sample-and-hold PI/flow feedback and finite-speed valve actuator."""
import numpy as np

def demand(power, cp, base_mass, s):
    return np.maximum(power/(cp*s['target_rise_K']), base_mass*s['minimum_flow_fraction'])

def command(mode, opening, temperature, mass, target, integral, s, interval):
    error = temperature-s['temperature_target_C']  # Hotter -> open, never the opposite.
    trial = np.clip(integral+error*interval, -500., 500.)
    flow_error = (target-mass)/np.maximum(target,1e-8)
    if mode == 'reactive': raw = .5+s['kp_per_K']*error+s['ki_per_K_s']*trial
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


def thermal_demand(power, cp, base_mass, resistance, inlet, s):
    """Steady thermal target shared by both designs; not a temperature guarantee.

    Ts = Tin + P/(m cp) + R P. A nonpositive available rise
    cannot be repaired by any finite flow; expose it separately.
    """
    available=np.minimum(s['target_rise_K'],np.minimum(s['outlet_limit_C']-inlet,
                         s['temperature_target_C']-inlet-resistance*power))
    impossible=(available<=0)&(power>0)
    # Infeasible targets use the original heat-rise target; feasibility is
    # reported explicitly instead of dividing by zero or inventing huge flow.
    rise=np.where(available>0,available,s['target_rise_K'])
    return np.maximum(power/(cp*rise),base_mass*s['minimum_flow_fraction']),impossible
