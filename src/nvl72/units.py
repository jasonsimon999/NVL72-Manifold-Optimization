"""Boundary unit conversions. Internal hydraulics: SI; temperature: kelvin."""
import numpy as np
LPM_TO_M3_S = 1.0 / 60000.0

def lpm_to_m3s(x): return np.asarray(x) * LPM_TO_M3_S

def m3s_to_lpm(x): return np.asarray(x) / LPM_TO_M3_S

def c_to_k(x): return np.asarray(x) + 273.15

def k_to_c(x): return np.asarray(x) - 273.15

def kpa_to_pa(x): return np.asarray(x) * 1000.0

def mm_to_m(x): return np.asarray(x) / 1000.0
