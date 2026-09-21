"""Reuse original location-balancing algorithm; freeze the resulting physical bores."""
from copy import deepcopy
from ..config import load_config
from ..optimize import balance_locations
from ..solver import solve

def optimized_reference(root):
    c=load_config(root/'config/optimized_example.yaml')
    r=balance_locations(c)
    frozen=deepcopy(r['config']);frozen['balancing_mode']='auto_equivalent'
    return solve(frozen)['fixed_orifice_config']
