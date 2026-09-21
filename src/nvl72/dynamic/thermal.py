"""Conservative implicit two-node tray model with enthalpy-based coolant storage."""
import numpy as np

def advance(chip, outlet, power, mass, inlet, resistance, capacitance, coolant_C, cp, dt):
    # Constant cp within each run (at inlet); same cp used for storage and transport.
    # C_s dTs/dt=P-G(Ts-Tf); C_f dTf/dt=G(Ts-Tf)-m cp(Tf-Tin).
    g = 1/resistance; w = mass*cp
    a = capacitance/dt + g; b = -g; d = coolant_C/dt+g+w
    rhs1 = capacitance/dt*chip+power
    rhs2 = coolant_C/dt*outlet+w*inlet
    ts = (rhs1*d-b*rhs2)/(a*d-b*b)
    tf = (a*rhs2-b*rhs1)/(a*d-b*b)
    removed = w*(tf-inlet)
    storage = (capacitance*(ts-chip)+coolant_C*(tf-outlet))/dt
    residual = power-removed-storage
    return ts, tf, removed, residual
