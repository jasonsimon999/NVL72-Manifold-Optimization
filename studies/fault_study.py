import pandas as pd
from pathlib import Path
from nvl72.config import load_config
from nvl72.solver import solve
from nvl72.scenarios import scenario
if __name__=='__main__':
    rows=[]
    for name in ['blocked','degraded_qdc','compute_removed','pump_reduced','warm_facility']:
        try:
            r=solve(scenario(load_config(),name));rows.append(dict(scenario=name,**r['metrics'],feasible=r['feasible']))
        except (RuntimeError,ValueError) as e:rows.append(dict(scenario=name,feasible=False,error=str(e)))
    Path('results/tables').mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv('results/tables/faults_standalone.csv',index=False)
