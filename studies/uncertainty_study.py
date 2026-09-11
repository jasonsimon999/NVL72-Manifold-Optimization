from pathlib import Path
import pandas as pd
from nvl72.config import load_config
from nvl72.uncertainty import uncertainty
if __name__=='__main__':
    Path('results/tables').mkdir(parents=True,exist_ok=True)
    configs={'baseline':load_config(),'candidate':load_config('config/optimized_example.yaml')}
    pd.DataFrame(uncertainty(configs)).to_csv('results/tables/uncertainty_standalone.csv',index=False)
