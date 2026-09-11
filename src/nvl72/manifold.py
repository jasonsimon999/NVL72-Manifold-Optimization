"""Finite-volume header geometry, with diameters defined along flow direction."""
import numpy as np

def diameter_profile(spec: dict, x):
    x = np.asarray(x)
    mode = spec['profile']
    if mode == 'constant': return np.full_like(x, spec['inlet_m'], dtype=float)
    if mode == 'piecewise':
        values = np.asarray(spec['pieces_m'])
        return values[np.minimum((x*len(values)).astype(int), len(values)-1)]
    u = x if mode == 'linear' else x**spec['exponent']
    return spec['inlet_m']+(spec['outlet_m']-spec['inlet_m'])*u

def geometry(c: dict):
    n = len(c['rack']['layout']); g = c['geometry']
    z = np.asarray(c['rack']['elevations_m'] if c['rack']['elevations_m'] is not None else np.linspace(g['height_m']/n, g['height_m'], n))
    dz = np.diff(np.r_[0, z]); x = (z-dz/2)/z[-1]
    return z, dz, diameter_profile(g['supply'], x), diameter_profile(g['return'], 1-x)

def volume(c: dict):
    _, dz, ds, dr = geometry(c)
    return float(np.sum(np.pi/4*(ds*ds+dr*dr)*dz))
