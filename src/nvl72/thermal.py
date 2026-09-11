"""Adiabatic supply, branch heat addition and direct-return enthalpy mixing."""
import numpy as np

def mix_temperature(m, T, coolant):
    m = np.asarray(m)
    if np.any(m < 0) or m.sum() <= 0: raise ValueError('Mixing requires nonnegative flows and positive total')
    return coolant.temperature(np.sum(m*coolant.enthalpy(T))/m.sum())

def temperatures(m, heat, supply_K, coolant):
    m = np.asarray(m)
    if np.any(m <= 0): raise ValueError('Heated network requires positive branch flow; reversal unsupported for this topology')
    hout = coolant.enthalpy(supply_K)+heat/m
    tout = coolant.temperature(hout)
    tail_m = np.cumsum(m[::-1])[::-1]
    mixed = coolant.temperature(np.cumsum((m*hout)[::-1])[::-1]/tail_m)
    q_check = m.sum()*(coolant.enthalpy(mixed[0])-coolant.enthalpy(supply_K))
    return tout, mixed, float(abs(q_check-heat.sum())/max(heat.sum(), 1.0))
