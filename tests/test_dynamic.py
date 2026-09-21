"""Conservation, coupling, limiting cases and fairness of transient comparison."""
from copy import deepcopy
import json
import numpy as np
import pytest
from nvl72.config import load_config
from nvl72.dynamic.settings import settings
from nvl72.dynamic.simulation import prepare,simulate,run_comparison
from nvl72.dynamic.hydraulic import operating_point,valve_branches
from nvl72.dynamic.thermal import advance
from nvl72.dynamic.workloads import generate
from nvl72.dynamic.economics import compare
from nvl72.dynamic.export import dumps

@pytest.fixture
def config():return load_config('config/optimized_example.yaml')

@pytest.fixture
def short():return settings(duration_s=30.,event_s=10.,reconnect_s=20.,spike_s=10.,sensor_noise_K=0.,pump_mode='constant_speed')

def test_locked_equals_passive(config,short):
    r=run_comparison(config,dict(short,controller='locked'))
    for key in ('mass','chip_C','outlet_C','pump_W','head_Pa'):
        np.testing.assert_array_equal(r['fixed'][key],r['active'][key])

def test_original_full_load_reference_reproduced(config,short):
    p=prepare(config,short)
    r=simulate(p,dict(short,scenario='steady'),'fixed')
    np.testing.assert_allclose(r['mass'][0],p['reference']['hydraulics']['mass_flow'],rtol=1e-6)
    assert abs(r['head_Pa'][0]-p['reference']['metrics']['system_dp_Pa'])<.05
    legacy=np.array([x['T_out_C'] for x in p['reference']['trays']])
    assert np.max(abs(r['outlet_C'][0]-legacy))<.2

@pytest.mark.parametrize('scenario',['heterogeneous','reinstall','rack_step'])
def test_balances(config,short,scenario):
    r=run_comparison(config,dict(short,scenario=scenario))
    for name in ('fixed','active'):
        a=r[name]['summary']
        assert a['node_mass_residual_kg_s']<1e-12
        assert a['pressure_residual_Pa']<.1
        assert a['energy_residual_W']<1e-6
        np.testing.assert_allclose(r[name]['liquid_W'][1:],r[name]['removed_W'][1:]+r[name]['storage_W'][1:],atol=1e-6)

def test_removed_exact_zero(config,short):
    r=run_comparison(config,dict(short,scenario='remove_compute'))
    for name in ('fixed','active'):
        off=r[name]['connected']==0
        assert np.all(r[name]['mass'][off]==0)
        assert np.all(r[name]['liquid_W'][off]==0)

def test_pump_off_heats_storage(config,short):
    r=run_comparison(config,dict(short,pump_enabled=False))
    assert np.all(r['active']['mass']==0)
    assert np.all(r['active']['pump_W']==0)
    assert np.max(r['active']['chip_C'][-1])>np.max(r['active']['chip_C'][0])

def test_valve_changes_neighbors_and_pump(config,short):
    p=prepare(config,short);rho=p['props'][1].rho;n=len(rho)
    controlled=np.ones(n,dtype=bool);conn=np.ones(n);u=np.ones(n)
    base=valve_branches(p['branches'],u,conn,rho,controlled,short)
    a=operating_point(p['config'],base,p['props'],p['reference_speed'],conn)
    u[0]=0
    shut=valve_branches(p['branches'],u,conn,rho,controlled,short)
    b=operating_point(p['config'],shut,p['props'],p['reference_speed'],conn)
    assert b['mass'][0]<a['mass'][0]*.1
    assert abs(b['mass'][1]-a['mass'][1])>1e-5
    assert b['head']!=a['head'] and b['mass'].sum()!=a['mass'].sum()
    assert b['pressure_error']<.1

def test_identical_branches_negligible_headers(config,short):
    config['rack']['gravity_enabled']=False
    p=prepare(config,short)
    c=deepcopy(p['config']);c['geometry']['height_m']=.001
    for side in ('supply','return'):c['geometry'][side]['inlet_m']=1.
    b=[deepcopy(p['branches'][0]) for _ in p['branches']]
    from nvl72.coolant import Properties
    ps=p['props'][0];pb=Properties(*[np.full(len(b),float(getattr(ps,k))) for k in ('rho','cp','mu','k')])
    r=operating_point(c,b,(ps,pb,pb),p['reference_speed'],np.ones(len(b)))
    assert np.std(r['mass'])/np.mean(r['mass'])<1e-5

def test_zero_heat_relaxes_to_inlet():
    chip=np.array([80.]);out=np.array([60.])
    for _ in range(500):chip,out,_,error=advance(chip,out,np.zeros(1),np.ones(1)*.1,40.,np.array([.004]),np.array([12000.]),1200.,4000.,2.)
    assert abs(chip[0]-40)<.2
    assert abs(error[0])<1e-7

def test_seed_and_liquid_fraction(config,short):
    kinds=['compute']*18+['switch']*9
    a=generate(kinds,short);b=generate(kinds,short)
    np.testing.assert_array_equal(a[1],b[1])
    r=run_comparison(config,dict(short,compute_liquid_fraction=.8))
    np.testing.assert_allclose(r['fixed']['liquid_W'][:,0],.8*r['fixed']['electrical_W'][:,0])

def test_finite_actuator_rate(config,short):
    r=run_comparison(config,short)['active']
    assert np.max(abs(np.diff(r['opening'],axis=0)))<=short['dt_s']/short['valve_stroke_s']+1e-10

def test_no_energy_saving_no_payback(short):
    e=compare({'average_aux_W':100},{'average_aux_W':110},short,27)
    assert e['annual_savings']<0 and e['payback_years'] is None and e['break_even_price'] is None

def test_serialization_and_input_immutability(config,short):
    original=deepcopy(config);r=run_comparison(config,short)
    assert config==original
    serialized=dumps(r)
    assert 'NaN' not in serialized
    assert json.loads(serialized)['fixed']['opening'][0][0] is None

def test_timestep_refinement(config,short):
    short=dict(short,scenario='rack_step',duration_s=60.,spike_s=30.)
    a=run_comparison(config,short);b=run_comparison(config,dict(short,dt_s=1.))
    assert abs(a['active']['summary']['peak_chip_C']-b['active']['summary']['peak_chip_C'])<1.

@pytest.mark.parametrize('failure',['stuck_closed','stuck_open','stuck_half','sensor_low','sensor_high','communications','pump_lag'])
def test_faults_are_finite_and_conservative(config,short,failure):
    r=run_comparison(config,dict(short,failure=failure))['active']
    assert np.all(np.isfinite(r['chip_C']))
    assert r['summary']['energy_residual_W']<1e-6

def test_invalid_settings():
    with pytest.raises(ValueError):settings(dt_s=0)
    with pytest.raises(ValueError):settings(pump_efficiency=1.1)

def test_zero_leakage_stuck_closed_still_generates_heat(config,short):
    r=run_comparison(config,dict(short,valve_min_area_fraction=0.,failure='stuck_closed'))['active']
    after=r['time_s']>=short['event_s']
    assert np.all(r['mass'][after,0]==0)
    assert np.all(r['liquid_W'][after,0]>0)

def test_new_page_renders_and_reruns():
    from streamlit.testing.v1 import AppTest
    from pathlib import Path
    app=AppTest.from_file(Path(__file__).resolve().parents[1]/'pages/1_Dynamic_Flow_Control.py',default_timeout=60).run()
    assert not app.exception
    app.selectbox[1].select('localized')
    next(b for b in app.button if b.label=='Run fixed vs active comparison').click().run()
    assert not app.exception
    assert len(app.metric)==2
    assert app.session_state['dynamic_result'][1]['settings']['scenario']=='localized'
