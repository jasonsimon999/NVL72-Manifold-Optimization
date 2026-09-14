"""Cache identity and input helpers separated from Streamlit rendering."""
from copy import deepcopy
from pathlib import Path
import hashlib
import yaml
from .config import merge,validate

def model_fingerprint(root):
    digest=hashlib.sha256()
    paths=sorted((Path(root)/'src/nvl72').glob('*.py'))+sorted((Path(root)/'data').glob('*'))
    for path in paths:
        if path.is_file():digest.update(path.name.encode());digest.update(path.read_bytes())
    return digest.hexdigest()

def compatible_result(result):
    """Legacy results retain their original policy, never silently get a new pass."""
    out=deepcopy(result)
    out.setdefault('screening_pass',all(v['pass'] for v in out['constraints'].values()))
    out.setdefault('fixed_orifice_config',None)
    for v in out['constraints'].values():
        v.setdefault('enforced',True)
        v.setdefault('basis','Historical result: original policy retained')
    return out

def apply_yaml_overrides(config,text):
    update=yaml.safe_load(text) or {}
    if not isinstance(update,dict):raise ValueError('Advanced YAML must be a mapping of configuration fields')
    unknown=set(update)-set(config)
    if unknown:raise ValueError(f'Unknown configuration sections: {sorted(unknown)}')
    if 'extends' in update:raise ValueError('Use configuration fields, not extends, in the override editor')
    # Reject misspellings instead of accepting a knob that has no effect.
    branch_template=merge(config['branches']['compute'],{'qdc_model':'fixed','qdc_diameter_m':.008,'qdc_reference_diameter_m':.008,'qdc_reference_density_kg_m3':1020.,'orifice_diameter_m':None,'orifice_Cd':.62,
        'qdc_curve':{'flow_m3_s':[],'dp_Pa':[],'polynomial':[]},'coldplate_curve':{'flow_m3_s':[],'dp_Pa':[],'polynomial':[]}})
    template=merge(config,{'balancing_mode':'resistance','cdu':{'rating_coolant':'PG25','rating_supply_C':40.},'facility':{'design_deltaT_K':12.,'minimum_hot_pinch_K':0.,'UA_W_K':None,'available_capacity_W':None},
        'constraint_policy':{'enforce_assumptions':False,'enforced':{}},'branches':{'compute':branch_template,'switch':merge(branch_template,config['branches']['switch'])}})
    def check(patch,known,path=''):
        if not isinstance(patch,dict):return
        if not isinstance(known,dict):raise ValueError(f'{path} must be a value, not a mapping')
        if path=='constraint_policy.enforced':return  # solver validates constraint names
        for key,value in patch.items():
            full=f'{path}.{key}' if path else key
            if path=='branches.overrides':
                if key not in config['rack']['layout']:raise ValueError(f'Unknown tray {key}')
                check(value,branch_template,full)
            else:
                if key not in known:raise ValueError(f'Unknown parameter {full}')
                check(value,known[key],full)
    check(update,template)
    result=merge(config,update)
    if result['coolant']['property_file']!=config['coolant']['property_file']:
        raise ValueError('The web editor uses the bundled coolant tables; custom server file paths are not accepted')
    validate(result)
    return result
