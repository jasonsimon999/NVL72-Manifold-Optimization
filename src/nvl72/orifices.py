"""Equivalent thin-plate permanent-loss sizing; not a machining qualification."""
import numpy as np

def loss_coefficient(bore, pipe, cd=.62):
    """Dimensionless permanent-pressure-loss K based on orifice-bore velocity.

    This is the recovered pressure loss for an incompressible thin plate, not
    the larger differential measured directly across pressure taps.  Diameter
    dependence enters through beta=bore/pipe; Cd remains a calibration input.
    """
    if not 0 < bore < pipe or not 0 < cd <= 1:
        raise ValueError('Orifice requires 0 < bore < branch ID and 0 < Cd <= 1')
    beta = bore/pipe
    recovery = np.sqrt(1-beta**4*(1-cd**2))-cd*beta**2
    return float((recovery/cd)**2)

def coefficient(bore, pipe, rho, cd=.62):
    if not 0 < bore < pipe or rho<=0 or not 0<cd<=1:
        raise ValueError('Orifice requires 0 < bore < branch ID, positive density and 0 < Cd <= 1')
    area=np.pi*bore*bore/4
    return loss_coefficient(bore,pipe,cd)/(2*rho*area**2)

def bore_from_coefficient(k, pipe, rho, cd=.62):
    if k<0 or pipe<=0 or rho<=0 or not 0<cd<=1:
        raise ValueError('Equivalent sizing requires nonnegative K, positive diameter/density and 0 < Cd <= 1')
    if k==0: return None  # no plate, rather than a zero-loss full-bore plate
    z=np.pi*pipe**2/4*np.sqrt(2*rho*k)
    return float(pipe/(1+cd**2*(2*z+z*z))**.25)
