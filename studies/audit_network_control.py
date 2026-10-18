"""Reproduce the network-controller comparison without selecting favorable cases."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import json
import numpy as np
import pandas as pd
from nvl72.dynamic.baseline import optimized_reference
from nvl72.dynamic.simulation import run_comparison
from nvl72.config import portable_config


def main():
    out=ROOT/'results/network_control_audit';out.mkdir(parents=True,exist_ok=True)
    c=optimized_reference(ROOT)
    cases=[('rack_spike',dict(scenario='rack_step')),
           ('local_spike',dict(scenario='localized')),
           ('remove_three',dict(scenario='remove_several')),
           ('reconnect_one',dict(scenario='reinstall')),
           ('spike_and_service',dict(scenario='rack_step',service_events=[
               dict(tray=0,disconnect_s=80.,reconnect_s=180.,ramp_s=20.),
               dict(tray=10,disconnect_s=120.,reconnect_s=220.,ramp_s=20.)]))]
    rows=[]
    for name,case in cases:
        for dt in ([2.,1.,.5] if name=='rack_spike' else [1.]):
            r=run_comparison(c,dict(controller='optimized',sensor_noise_K=0.,dt_s=dt,**case))
            fixed=r['fixed'];active=r['active_candidate']
            for key in ('time_s','electrical_W','liquid_W','connected','target_mass'):
                np.testing.assert_array_equal(fixed[key],active[key])
            assert np.all(np.ptp(fixed['orifice_diameter_mm'],axis=0)==0)
            for label,run in [('fixed',fixed),('active',active)]:
                s=run['summary']
                np.testing.assert_allclose(run['liquid_W'][1:],run['removed_W'][1:]+run['storage_W'][1:],atol=1e-6)
                assert s['pressure_residual_Pa']<.1 and s['node_mass_residual_kg_s']<1e-9
                assert np.all(run['mass'][run['connected']==0]==0)
                rows.append(dict(case=name,dt_s=dt,design=label,selected=r['optimization']['selected_from'],**s))
            if name=='rack_spike' and dt==.5:
                (out/'inputs.json').write_text(json.dumps(dict(config=portable_config(c),settings=r['settings']),indent=2))
            print(name,dt,'fixed/active W',round(fixed['summary']['average_aux_W'],2),round(active['summary']['average_aux_W'],2),'selected',r['optimization']['selected_from'],flush=True)
    frame=pd.DataFrame(rows);frame.to_csv(out/'comparison.csv',index=False)
    print(frame[['case','dt_s','design','average_aux_W','peak_chip_C','thermal_pass','selected']].to_string(index=False))


if __name__=='__main__': main()
