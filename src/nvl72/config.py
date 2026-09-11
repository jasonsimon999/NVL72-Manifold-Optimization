"""YAML inheritance and input validation; no implicit hardware defaults."""
from copy import deepcopy
from pathlib import Path
import numpy as np
import yaml

import sys

ROOT = next((p for p in (Path(__file__).resolve().parents[2],Path.cwd(),Path(sys.prefix)/'share/nvl72')
             if (p/'config/baseline.yaml').exists()),Path.cwd())

def merge(base: dict, update: dict) -> dict:
    out = deepcopy(base)
    for key, value in update.items():
        out[key] = merge(out[key], value) if isinstance(value, dict) and isinstance(out.get(key), dict) else deepcopy(value)
    return out

def load_config(path: str | Path = ROOT / 'config/baseline.yaml') -> dict:
    path = Path(path).resolve()
    cfg = yaml.safe_load(path.read_text())
    if 'extends' in cfg:
        cfg = merge(load_config(path.parent / cfg.pop('extends')), cfg)
    prop = Path(cfg['coolant']['property_file'])
    if not prop.is_absolute():
        local = path.parent / prop
        cfg['coolant']['property_file'] = str((local if local.exists() else ROOT / prop).resolve())
    validate(cfg)
    return cfg

def validate(c: dict) -> None:
    def require(ok, message):
        if not ok: raise ValueError(message)
    def finite_tree(value):
        if isinstance(value, dict):
            for child in value.values(): finite_tree(child)
        elif isinstance(value, list):
            for child in value: finite_tree(child)
        elif isinstance(value, (int,float)):
            require(np.isfinite(value), 'Configuration contains non-finite numeric input')
    finite_tree(c)
    r = c['rack']; layout = r['layout']
    require(len(layout) == len(set(layout)) and len(layout) > 0, 'Tray IDs must be unique and nonempty')
    require(sum(x.startswith('C') for x in layout) == r['compute_trays'], 'Compute count and layout differ')
    require(sum(x.startswith('S') for x in layout) == r['switch_trays'], 'Switch count and layout differ')
    require(len(layout) == r['compute_trays'] + r['switch_trays'], 'Unknown tray ID class')
    require(r['flow_LPM'] > 0, 'Rack flow must be positive')
    require(r['operating_mode'] in ('fixed_flow', 'pump'), 'Unknown operating mode')
    require(c['optimization']['target'] in ('heat_proportional', 'equal_flow'), 'Unknown target')
    require(c['cdu']['mode'] in ('in_rack', 'in_row'), 'Unknown CDU mode')
    require(0 < c['cdu']['efficiency'] <= 1 and 0 < c['cdu']['speed'] <= 1, 'Invalid pump efficiency or speed')
    require(c['cdu']['shutoff_dp_Pa'] > c['cdu']['available_dp_Pa'] > 0, 'Pump curve requires shutoff above rated head')
    require(c['facility']['flow_LPM'] > 0, 'Facility flow must be positive')
    for side in ('supply', 'return'):
        g = c['geometry'][side]
        require(g['profile'] in ('constant', 'linear', 'power', 'piecewise'), 'Unknown diameter profile')
        require(min(g['inlet_m'], g['outlet_m'], *g['pieces_m']) > 0 and g['exponent'] > 0, 'Invalid diameter/exponent')
    require(c['geometry']['height_m'] > 0 and c['geometry']['roughness_m'] >= 0, 'Invalid height or roughness')
    if r['elevations_m'] is not None:
        z = np.asarray(r['elevations_m'])
        require(len(z) == len(layout) and np.all(np.diff(np.r_[0, z]) > 0), 'Elevations must be positive and ascending')
    heat = c['power']['tray_heat_W']
    if heat is not None: require(len(heat) == len(layout) and np.all(np.asarray(heat) >= 0), 'Invalid per-tray heat array')
    for kind in ('compute', 'switch'):
        b = c['branches'][kind]
        require(b['diameter_m'] > 0 and all(b[k] >= 0 for k in ('tube_length_m', 'tube_multiplier', 'coldplate_K', 'qdc_K', 'restriction_K')), 'Invalid branch geometry/resistance')
    require(c['coolant']['viscosity_multiplier'] > 0, 'Viscosity multiplier must be positive')
    require(all(v >= 0 for d in c['loss_coefficients'].values() for v in d.values()), 'Minor losses must be nonnegative')

    require(c['facility']['hx_model'] == 'rating_scaled', 'Supported HX model is rating_scaled')
    require(c['cdu']['capacity_W'] > 0 and c['cdu']['nominal_flow_LPM'] > 0 and c['cdu']['served_racks'] >= 1 and c['cdu']['approach_K'] > 0, 'Invalid CDU rating')
    require(0 < c['solver']['relaxation'] <= 1, 'Property relaxation must be in (0,1]')
    for tray, override in c['branches']['overrides'].items():
        require(tray in layout, f'Unknown override tray {tray}')
        for key,value in override.items():
            if key in ('coldplate_K','qdc_K','restriction_K','tube_length_m','tube_multiplier'):
                require(value >= 0, f'Negative branch input {tray}.{key}')
            if key == 'diameter_m': require(value > 0, f'Invalid diameter {tray}')
    if c['external']['enabled']:
        e = c['external']
        require(e['diameter_m'] > 0 and min(e['length_m'],e['minor_K'],e['equipment_K']) >= 0, 'Invalid external-loop dimensions or losses')
    if c['coldplate']['enabled']:
        cp = c['coldplate']
        require(all(cp[k] > 0 for k in ('channels','channel_width_m','channel_height_m','length_m','heated_area_m2','laminar_Nu')), 'Invalid channel geometry')
        require(all(cp[k] >= 0 for k in ('tim_K_W','spreader_K_W','plate_K_W')), 'Negative thermal resistance')
