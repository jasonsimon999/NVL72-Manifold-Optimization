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


def test_spike_preserves_requested_duration():
    s=settings(scenario='rack_step',duration_s=100.,event_s=70.,spike_s=30.)
    t,u,_=generate(['compute','switch'],s)
    assert np.all(u[(t>=80)&(t<100),0]==s['high_load'])
    t,u,_=generate(['compute'],settings(scenario='bursts',duty=0.))
    assert np.all(u==.3)


def test_independent_service_schedule(config,short):
    s=dict(short,service_events=[dict(tray=1,disconnect_s=4.,reconnect_s=14.,ramp_s=4.),dict(tray=20,disconnect_s=8.,reconnect_s=None,ramp_s=4.)])
    r=run_comparison(config,s)
    for name in ('fixed','active_candidate'):
        run=r[name]; t=run['time_s']
        assert np.all(run['mass'][(t>=4)&(t<=14),1]==0)
        assert np.all(run['liquid_W'][(t>=8),20]==0)
        assert run['connected'][t==16,1]==.5
        assert np.all(run['connected'][:,0]==1)
        assert run['summary']['energy_residual_W']<1e-6


def test_inverse_sizing_matches_pressure_law(config,short):
    from nvl72.dynamic.hydraulic import size_positions
    from nvl72.orifices import coefficient
    p=prepare(config,short);b=p['branches'][0];rho=p['props'][1].rho[:1]
    u=np.array([.5]);m=np.array([.1]);target=np.array([.09])
    new=size_positions([b],u,m,target,rho,short)
    def loss(position,flow):
        d=b['diameter_m']*short['valve_max_bore_fraction']*np.sqrt(short['valve_min_area_fraction']+(1-short['valve_min_area_fraction'])*position)
        return coefficient(float(d[0]),b['diameter_m'],float(rho[0]),short['valve_Cd'])*flow[0]**2
    assert loss(new,target)==pytest.approx(loss(u,m),rel=1e-10)


@pytest.mark.parametrize('scenario',['steady','heterogeneous','remove_switch','reinstall'])
def test_optimized_selection_does_not_hide_candidate(config,short,scenario):
    r=run_comparison(config,dict(short,controller='optimized',scenario=scenario))
    assert r['held_active'] is not None
    assert np.all(np.isfinite(r['active_candidate']['orifice_diameter_mm']))
    for key in ('peak_chip_C','peak_outlet_C','average_aux_W','peak_head_kPa','rms_flow_error','max_abs_flow_error'):
        assert r['active']['summary'][key]<=r['fixed']['summary'][key]+1e-7
    if r['optimization']['fallback_to_fixed']:
        assert r['economics']['incremental_capex']==0
        assert r['economics']['annual_savings']==0
        np.testing.assert_array_equal(r['active']['mass'],r['fixed']['mass'])


def test_optimized_fault_not_erased(config,short):
    r=run_comparison(config,dict(short,controller='optimized',failure='stuck_closed',valve_min_area_fraction=0.))
    assert not r['optimization']['fallback_to_fixed']
    assert np.all(r['active']['mass'][r['active']['time_s']>=short['event_s'],0]==0)


def test_service_validation():
    with pytest.raises(ValueError):settings(service_events=[dict(tray=0,disconnect_s=20,reconnect_s=10,ramp_s=1)])
    with pytest.raises(ValueError):settings(service_events=[dict(tray=0,disconnect_s=20,reconnect_s=30,ramp_s=0)])


def test_service_widgets_and_equations_render():
    from streamlit.testing.v1 import AppTest
    from pathlib import Path
    app=AppTest.from_file(Path(__file__).resolve().parents[1]/'pages/1_Dynamic_Flow_Control.py',default_timeout=90).run()
    app.multiselect(key='service_trays').select(1).select(20).run()
    assert not app.exception
    app.number_input(key='service_start_1').set_value(10.)
    app.number_input(key='service_end_1').set_value(30.)
    app.number_input(key='service_start_20').set_value(20.)
    app.number_input(key='service_end_20').set_value(40.)
    next(b for b in app.button if b.label=='Run fixed vs active comparison').click().run()
    assert not app.exception
    assert not any('Run could not be evaluated' in item.value for item in app.error)
    result=app.session_state['dynamic_result'][1]
    assert len(result['settings']['service_events'])==2
    assert np.all(result['active_candidate']['mass'][result['active_candidate']['time_s']==20,1]==0)
    assert len(app.get('latex'))>=10


def test_thermal_target_equation_and_unreachable():
    from nvl72.dynamic.control import thermal_demand
    s=settings(temperature_target_C=72.,outlet_limit_C=65.,minimum_flow_fraction=0.)
    power=np.array([5800.,10000.]);R=np.array([.004,.004]);cp=4000.;Tin=40.
    m,impossible=thermal_demand(power,cp,np.array([.1,.1]),R,Tin,s)
    assert Tin+power[0]/(m[0]*cp)+R[0]*power[0]==pytest.approx(72.)
    assert list(impossible)==[False,True]
    assert np.all(np.isfinite(m))


def test_fixed_equilibrium_matches_analytic_temperature(config,short):
    s=dict(short,scenario='steady');p=prepare(config,s);r=simulate(p,s,'fixed')
    cp=float(p['props'][0].cp)
    R=np.array([s[k+'_R_K_W'] for k in p['kinds']])
    predicted=p['inlet']+r['liquid_W']/(r['mass']*cp)+R*r['liquid_W']
    np.testing.assert_allclose(r['chip_C'],predicted,atol=1e-8)


def test_identical_inputs_fixed_bores_and_independent_storage(config,short):
    s=dict(short,controller='optimized',scenario='rack_step',service_events=[dict(tray=3,disconnect_s=8.,reconnect_s=18.,ramp_s=4.)])
    r=run_comparison(config,s)
    for key in ('electrical_W','liquid_W','connected','time_s','target_mass'):
        np.testing.assert_array_equal(r['fixed'][key],r['active_candidate'][key])
    assert np.all(np.ptp(r['fixed']['orifice_diameter_mm'],axis=0)==0)
    for run in (r['fixed'],r['active_candidate']):
        Cs=np.array([s[k+'_C_J_K'] for k in run['kinds']])
        stored=(np.diff(run['chip_C'],axis=0)*Cs+np.diff(run['outlet_C'],axis=0)*s['coolant_C_J_K'])/s['dt_s']
        np.testing.assert_allclose(stored,run['storage_W'][1:],atol=1e-8)
        np.testing.assert_allclose(run['liquid_W'][1:],run['removed_W'][1:]+stored,atol=1e-6)


def test_service_overlay_does_not_multiply_power_twice():
    s=settings(scenario='reinstall',duration_s=40.,event_s=10.,reconnect_s=20.,reconnect_ramp_s=10.,service_events=[dict(tray=0,disconnect_s=10.,reconnect_s=20.,ramp_s=10.)])
    t,u,conn=generate(['compute','switch'],s)
    np.testing.assert_array_equal(u[:,0],conn[:,0])
