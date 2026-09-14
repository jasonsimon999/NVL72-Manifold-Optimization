"""Equivalent thin-plate permanent-loss sizing; not a machining qualification."""
import numpy as np

def coefficient(bore, pipe, rho, cd=.62):
    if not 0 < bore < pipe or rho<=0 or not 0<cd<=1:
        raise ValueError('Orifice requires 0 < bore < branch ID, positive density and 0 < Cd <= 1')
    beta=bore/pipe;area=np.pi*bore*bore/4
    return (np.sqrt(1-beta**4*(1-cd**2))-cd*beta**2)**2/(2*rho*cd**2*area**2)

def bore_from_coefficient(k, pipe, rho, cd=.62):
    if k<0 or pipe<=0 or rho<=0 or not 0<cd<=1:
        raise ValueError('Equivalent sizing requires nonnegative K, positive diameter/density and 0 < Cd <= 1')
    if k==0: return None  # no plate, rather than a zero-loss full-bore plate
    z=np.pi*pipe**2/4*np.sqrt(2*rho*k)
    return float(pipe/(1+cd**2*(2*z+z*z))**.25)
