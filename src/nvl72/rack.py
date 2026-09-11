"""Resolve tray loads and optional per-tray overrides from a configuration."""
import numpy as np
from .config import merge

def tray_data(c: dict):
    ids = c['rack']['layout']
    kinds = ['compute' if i.startswith('C') else 'switch' for i in ids]
    p = c['power']
    qc = (p['gpu_W_each']*p['gpus_per_compute_tray']+p['grace_cpu_W_each']*p['cpus_per_compute_tray'])*p['compute_fraction']+p['compute_aux_W']
    qs = p['switch_rack_total_W']/max(c['rack']['switch_trays'], 1)*p['switch_fraction']+p['switch_aux_W']
    heat = np.asarray(p['tray_heat_W'] if p['tray_heat_W'] is not None else [qc if k == 'compute' else qs for k in kinds], dtype=float)
    branches = [merge(c['branches'][kind], c['branches']['overrides'].get(i, {})) for i, kind in zip(ids, kinds)]
    if np.any(~np.isfinite(heat)) or np.any(heat < 0): raise ValueError('Heat loads must be finite and nonnegative')
    return ids, kinds, heat, branches
