"""Run reproducible dynamic design studies without Streamlit.

python studies/dynamic_flow_study.py --full
"""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import argparse
import pandas as pd
from nvl72.dynamic.baseline import optimized_reference
from nvl72.dynamic.settings import settings
from nvl72.dynamic.simulation import run_comparison
from nvl72.dynamic.export import dumps
from nvl72.dynamic.sources import registry
from nvl72.dynamic import studies

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--full',action='store_true')
    parser.add_argument('--output',type=Path,default=ROOT/'results/dynamic')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    c=optimized_reference(ROOT);s=settings();result=run_comparison(c,s)
    (args.output/'default_comparison.json').write_text(dumps(result))
    pd.DataFrame(registry(s,c)).to_csv(args.output/'assumptions.csv',index=False)
    jobs={'scenarios':studies.scenario_study,'strategies':studies.strategy_study}
    if args.full:jobs.update(failures=studies.failure_study,sensitivity=studies.sensitivity_study,
                             break_even=studies.break_even_study,capacity=studies.capacity_study)
    all_results={}
    for name,fn in jobs.items():
        print('Running',name,flush=True);rows=fn(c,s);all_results[name]=rows
        pd.DataFrame(rows).to_csv(args.output/f'{name}.csv',index=False)
        (args.output/f'{name}.json').write_text(dumps(rows))
    (args.output/'summary.json').write_text(dumps(dict(default={key:result[key] for key in ('benefit','economics','facility_screen')},studies=all_results)))
    print('Saved',args.output,flush=True)

if __name__=='__main__':main()
