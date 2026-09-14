"""Reproduce the constraint audit without overwriting historical study outputs.

Run: PYTHONPATH=src .venv/bin/python studies/audit_study.py
Facility examples are hypotheses, not specifications for the user's site.
"""
from copy import deepcopy
from pathlib import Path
import json
import pandas as pd
from nvl72.config import ROOT,load_config
from nvl72.reporting import export,native
from nvl72.solver import solve

def main():
    base=load_config();cases={'reference':base}
    for name,flow in [('flow110',110),('flow125',125)]:
        c=deepcopy(base);c['rack']['flow_LPM']=flow;cases[name]=c
    c=deepcopy(base);c['rack']['supply_C']=35;cases['impossible_35C_supply_36C_facility']=c
    c=deepcopy(base)
    for side in ['supply','return']:c['geometry'][side].update(inlet_m=.032,outlet_m=.032)
    cases['header32mm']=c
    c=deepcopy(base);c['coolant']['type']='PG25_Dow2023';cases['versioned_pg25']=c
    c=deepcopy(base);c['facility'].update(flow_LPM=300,available_capacity_W=500000,UA_W_K=50000)
    cases['hypothetical_stronger_facility']=c
    c=deepcopy(base);c['balancing_mode']='auto_equivalent';c['branches']['switch']['restriction_K']=150e6
    cases['automatic_switch150M']=c
    out=ROOT/'results/audit';out.mkdir(parents=True,exist_ok=True);rows=[]
    for name,c in cases.items():
        r=solve(c);export(r,out,name,figures=False)
        rows.append(dict(case=name,enforced_pass=r['feasible'],all_screens_pass=r['screening_pass'],
            failed_enforced=', '.join(k for k,v in r['constraints'].items() if v['enforced'] and not v['pass']),
            failed_advisory=', '.join(k for k,v in r['constraints'].items() if not v['enforced'] and not v['pass']),
            outlet_max_C=r['metrics']['T_out_max_C'],chip_upper_C=r['metrics']['T_junction_upper_max_C'],
            pressure_kPa=r['metrics']['system_dp_Pa']/1000,facility_return_C=r['facility']['FWS_return_C'],
            required_UA_kW_K=r['facility']['required_UA_W_K']/1000 if r['facility']['required_UA_W_K'] else None))
    pd.DataFrame(rows).to_csv(out/'comparison.csv',index=False)
    (out/'comparison.json').write_text(json.dumps(native(rows),indent=2,allow_nan=False))
    # Every resolved baseline leaf, including solver-added thermal settings.
    resolved=solve(base)['config'];inventory=[]
    def walk(value,path=''):
        if isinstance(value,dict):
            for key,child in value.items():walk(child,f'{path}.{key}' if path else key)
        else:inventory.append({'parameter':path,'value':value})
    walk(resolved)
    (out/'resolved_input_inventory.json').write_text(json.dumps(inventory,indent=2))
    print(pd.DataFrame(rows).to_string(index=False))

if __name__=='__main__':main()
