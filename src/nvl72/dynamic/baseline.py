"""Freeze the user's two-class fixed-page design without per-tray reoptimization."""
from ..config import load_config
from ..solver import solve

def optimized_reference(root):
    c=load_config(root/'config/optimized_example.yaml')
    c['name']='Fixed-page reference: switch Kh 180 million Pa/(kg/s)^2'
    c['branches']['compute']['restriction_K']=0.
    c['branches']['switch']['restriction_K']=180e6
    c['balancing_mode']='auto_equivalent'
    # One full-load design solve converts the specified class resistances to
    # physical bores. No location balancing and no event-specific redesign.
    return solve(c)['fixed_orifice_config']
