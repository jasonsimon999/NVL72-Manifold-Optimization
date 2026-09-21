"""Bounded speed commands; affinity curve reused from nvl72.cdu."""
import numpy as np

def update(speed, point, target_mass, reference_head, reference_speed, s, dt, lag=False):
    mode=s['pump_mode']
    if mode=='constant_speed': desired=reference_speed
    elif mode=='constant_dp': desired=speed*np.sqrt(reference_head/max(point['head'],1.))
    else:
        # Track the most under-supplied connected branch for BOTH designs.
        # Tracking only total demand can starve high-load switch/compute branches.
        mask=np.asarray(target_mass)>0
        ratio=np.max(np.asarray(target_mass)[mask]/np.maximum(point['mass'][mask],1e-10)) if mask.any() else 0.
        desired=speed*np.clip(ratio,.5,1.5)
    desired=np.clip(desired,s['pump_min_speed'],s['pump_max_speed'])
    tau=s['pump_tau_s']*(10 if lag else 1)
    return float(speed+(desired-speed)*(1-np.exp(-dt/tau))) if s['pump_enabled'] else 0.
