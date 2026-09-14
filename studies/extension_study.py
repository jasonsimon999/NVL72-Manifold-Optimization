"""Run matched fluid comparisons and export all new engineering outputs."""
from copy import deepcopy
from pathlib import Path
import pandas as pd
from nvl72.config import load_config
from nvl72.solver import solve
from nvl72.reporting import export
from nvl72.design_analysis import design_summary

def main():
    out=Path('results/extension_study'); cases={}
    for design,path in [('baseline','config/baseline.yaml'),('selected','config/optimized_example.yaml')]:
        for fluid in ['water','PG25','EG50']:
            c=deepcopy(load_config(path));c['coolant']['type']=fluid
            name=f'{design}_{fluid}';cases[name]=solve(c)
            export(cases[name],out,name,figures=False)
    cases['individual_orifices']=solve(load_config('config/orifice_example.yaml'))
    export(cases['individual_orifices'],out,'individual_orifices',figures=False)
    table=pd.DataFrame(design_summary(cases))
    table.to_csv(out/'design_comparison.csv',index=False)
    print(table[['design','enforced_requirements_pass','outlet_max_C','chip_upper_max_C','pressure_kPa','pump_W','FWS_required_LPM']].to_string(index=False))

if __name__=='__main__': main()
