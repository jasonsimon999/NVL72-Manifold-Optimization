"""External available pump head; single-point curve fit is explicitly assumed."""
import numpy as np
from scipy.optimize import brentq
from .units import lpm_to_m3s

def pump_head(q_m3_s, cdu):
    rated_q = lpm_to_m3s(cdu['nominal_flow_LPM'])
    a = (cdu['shutoff_dp_Pa']-cdu['available_dp_Pa'])/rated_q**2
    return cdu['shutoff_dp_Pa']*cdu['speed']**2-a*np.asarray(q_m3_s)**2

def power(head_Pa, q_m3_s, efficiency):
    return head_Pa*q_m3_s, head_Pa*q_m3_s/efficiency

def intersection(system, cdu, bracket_m3_s):
    def f(q): return pump_head(q,cdu)-system(q)
    a,b = bracket_m3_s
    if f(a)*f(b)>0: raise ValueError('No pump/system intersection in supplied flow bracket')
    return brentq(f,a,b,xtol=1e-12)
