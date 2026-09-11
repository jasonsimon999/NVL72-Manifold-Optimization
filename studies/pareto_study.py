from pathlib import Path
import pandas as pd
from nvl72.plotting import pareto_figures
if __name__=='__main__':
    pareto_figures(pd.read_csv('results/tables/optimization_archive.csv'),Path('results/figures'))
