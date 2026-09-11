"""Command-line entry points for reproducible engineering studies."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .config import load_config
from .solver import solve
from .reporting import export,write_report

def main(argv=None):
    parser=argparse.ArgumentParser(description='NVL72-class coolant distribution engineering model')
    sub=parser.add_subparsers(dest='command',required=True)
    for name in ('simulate','optimize','sweep','study'):
        p=sub.add_parser(name);p.add_argument('--config',default='config/baseline.yaml');p.add_argument('--output',default='results')
        if name=='simulate':p.add_argument('--name',default='baseline')
        if name=='optimize':p.add_argument('--design',choices=list('ABCDE'),default='D');p.add_argument('--method',choices=['local','global'],default='local')
        if name=='sweep':
            p.add_argument('--parameter',default='rack_flow_LPM');p.add_argument('--min',type=float,default=90);p.add_argument('--max',type=float,default=130);p.add_argument('--count',type=int,default=9)
        if name=='study':p.add_argument('--samples',type=int,default=32)
    p=sub.add_parser('report');p.add_argument('--result',required=True);p.add_argument('--output',default='results/reports/regenerated.md')
    args=parser.parse_args(argv)
    if args.command=='report':
        r=json.loads(Path(args.result).read_text());Path(args.output).parent.mkdir(parents=True,exist_ok=True);write_report(r,args.output,Path(args.result).stem);return
    cfg=load_config(args.config)
    if args.command=='simulate':r=solve(cfg);export(r,args.output,args.name)
    elif args.command=='optimize':
        from .optimize import optimize
        r,rows=optimize(cfg,args.design,args.method);export(r,args.output,'optimized');pd.DataFrame(rows).to_csv(Path(args.output)/'tables/optimization_archive.csv',index=False)
    elif args.command=='sweep':
        from .sweep import sweep
        rows=sweep(cfg,args.parameter,np.linspace(args.min,args.max,args.count));Path(args.output).mkdir(parents=True,exist_ok=True)
        pd.DataFrame(rows).to_csv(Path(args.output)/f'sweep_{args.parameter}.csv',index=False);return
    else:
        from .study import run_study
        run_study(cfg,args.output,args.samples);return
    print(json.dumps({'feasible':r['feasible'],'metrics':r['metrics'],'validation':r['validation']},indent=2))
