"""Reproducible input fairness, conservation and raw thermal-performance audit."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from nvl72.dynamic.baseline import optimized_reference
from nvl72.dynamic.simulation import run_comparison
from nvl72.dynamic import plotting
from nvl72.dynamic.export import dumps


def main():
    out=ROOT/'results/dynamic_audit';out.mkdir(exist_ok=True)
    c=optimized_reference(ROOT);rows=[]
    cases=[('steady',dict(scenario='steady')),('rack_spike',dict(scenario='rack_step')),
           ('local_spike',dict(scenario='localized')),('heterogeneous',dict(scenario='heterogeneous')),
           ('service_spike',dict(scenario='rack_step',service_events=[dict(tray=0,disconnect_s=80.,reconnect_s=180.,ramp_s=20.),dict(tray=10,disconnect_s=120.,reconnect_s=220.,ramp_s=20.)]))]
    for name,case in cases:
        r=run_comparison(c,dict(controller='optimized',duration_s=300.,sensor_noise_K=0.,**case))
        f,a=r['fixed'],r['active_candidate']
        for key in ('time_s','electrical_W','liquid_W','connected','target_mass'):
            np.testing.assert_array_equal(f[key],a[key])
        assert np.max(np.ptp(f['orifice_diameter_mm'],axis=0))==0
        for run in (f,a,r['held_active']):
            np.testing.assert_allclose(run['liquid_W'][1:],run['removed_W'][1:]+run['storage_W'][1:],atol=1e-6)
            assert run['summary']['pressure_residual_Pa']<.1
            assert np.all(run['mass'][run['connected']==0]==0)
        row=dict(case=name,fixed_peak_C=f['summary']['peak_chip_C'],active_peak_C=a['summary']['peak_chip_C'],
                 peak_reduction_K=f['summary']['peak_chip_C']-a['summary']['peak_chip_C'],
                 mean_reduction_K=f['summary']['mean_chip_C']-a['summary']['mean_chip_C'],
                 fixed_over_limit_s=f['summary']['time_above_limit_s'],active_over_limit_s=a['summary']['time_above_limit_s'],
                 fixed_aux_W=f['summary']['average_aux_W'],active_aux_W=a['summary']['average_aux_W'],
                 selected=r['optimization']['selected_from'],max_pressure_residual_Pa=max(x['summary']['pressure_residual_Pa'] for x in (f,a)),
                 max_energy_residual_W=max(x['summary']['energy_residual_W'] for x in (f,a)))
        rows.append(row)
        if name=='service_spike':
            (out/'service_spike.json').write_text(dumps(r))
            for label,fn in [('applied_heat',plotting.applied_loads),('fixed_active_bores',plotting.fixed_active_bores),('tray_C01',lambda x:plotting.tray_audit(x,0))]:
                fig=fn(r);fig.savefig(out/(label+'.png'),dpi=160);plt.close(fig)
            frame=[]
            for name_,run in [('fixed',f),('active',a)]:
                for j,t in enumerate(run['time_s']):
                    for i,tray in enumerate(run['ids']):
                        frame.append(dict(design=name_,time_s=t,tray=tray,liquid_W=run['liquid_W'][j,i],electrical_W=run['electrical_W'][j,i],connection=run['connected'][j,i],bore_mm=run['orifice_diameter_mm'][j,i],flow_LPM=run['flow_LPM'][j,i],solid_C=run['chip_C'][j,i]))
            pd.DataFrame(frame).to_csv(out/'service_spike_samples.csv',index=False)
    pd.DataFrame(rows).to_csv(out/'comparison.csv',index=False)
    print(pd.DataFrame(rows).to_string(index=False))

if __name__=='__main__':main()
