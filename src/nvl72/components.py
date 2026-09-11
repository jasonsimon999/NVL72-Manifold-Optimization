"""Passive hydraulic elements; signed pipe laws permit solver trial reversals."""
import numpy as np
from scipy.optimize import brentq

def friction_factor(Re, relative_roughness=0.0):
    re = np.maximum(np.abs(np.asarray(Re, dtype=float)), 1e-20)
    lam = 64/re
    turb = (-1.8*np.log10((np.asarray(relative_roughness)/3.7)**1.11 + 6.9/np.maximum(re, 2300)))**-2
    w = np.clip((re-2300)/1700, 0, 1)
    return (1-w)*lam+w*turb

def colebrook(Re: float, relative_roughness: float) -> float:
    if Re < 4000: raise ValueError('Colebrook validation requires turbulent Re >= 4000')
    return brentq(lambda f: 1/np.sqrt(f)+2*np.log10(relative_roughness/3.7+2.51/(Re*np.sqrt(f))), 0.005, 0.2)

def pipe_loss(m, rho, mu, diameter, length, roughness, minor_K=0.0) -> dict:
    m = np.asarray(m); d = np.asarray(diameter)
    if np.any(d <= 0) or np.any(np.asarray(length) < 0): raise ValueError('Invalid pipe dimensions')
    v = m/(rho*np.pi*d*d/4)
    re = np.abs(rho*v*d/mu)
    f = friction_factor(re, roughness/d)
    dyn = rho*v*np.abs(v)/2
    return {'friction': f*np.asarray(length)/d*dyn, 'minor': np.asarray(minor_K)*dyn,
            'velocity': v, 'Re': re, 'f': f}

def reduced_loss(m, coefficient): return np.asarray(coefficient)*np.asarray(m)*np.abs(m)

def curve_loss(q, spec: dict):
    """SI volume flow curve, polynomial or measured points. No extrapolation."""
    q = np.asarray(q)
    if 'flow_m3_s' in spec:
        x = np.asarray(spec['flow_m3_s']); y = np.asarray(spec['dp_Pa'])
        if len(x) < 2 or np.any(np.diff(x) <= 0) or np.any(np.diff(y) < 0) or x[0] != 0 or y[0] != 0:
            raise ValueError('Passive component curve must be monotone and start at (0,0)')
        if np.any(np.abs(q)>x[-1]): raise ValueError('Component curve flow range exceeded')
        return np.sign(q)*np.interp(np.abs(q), x, y)
    a,b,c = spec['polynomial']
    if min(a,b,c) < 0: raise ValueError('Passive polynomial coefficients must be nonnegative')
    return np.sign(q)*(a*q*q+b*np.abs(q)+c)
