"""Run the validated engineering study; --reuse uses an existing D optimization."""
import argparse
from nvl72.config import load_config
from nvl72.study import run_study
p=argparse.ArgumentParser();p.add_argument('--reuse',action='store_true');p.add_argument('--samples',type=int,default=32)
a=p.parse_args();run_study(load_config(),'results',a.samples,a.reuse)
