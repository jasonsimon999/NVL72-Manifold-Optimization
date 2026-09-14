from copy import deepcopy
import json
import pytest
from nvl72.config import load_config
from nvl72.coolant import Coolant
from nvl72.solver import solve
from nvl72.reporting import native
from nvl72.design_analysis import design_summary

def test_eg50_manufacturer_anchor_and_conservation():
    c=load_config('config/eg50_example.yaml')
    p=Coolant('EG50',c['coolant']['property_file']).properties(313.15)
    assert p.rho==pytest.approx(1064.91)
    assert p.cp==pytest.approx(3361)
    assert p.mu==pytest.approx(.0022567)
    r=solve(c)
    assert r['validation']['energy_relative_error']<1e-8
    assert abs(r['facility']['heat_balance_residual_W'])<1e-6
    assert r['facility']['TCS_capacity_rate_ratio']<1
    assert 'EG50' in r['qualification']
    json.dumps(native(r),allow_nan=False)

def test_orifice_rebalances_and_budget_closes():
    c=load_config();a=solve(c)
    c['branches']['overrides']['C01']={'orifice_diameter_m':.004}
    b=solve(c)
    assert b['trays'][0]['actual_flow_LPM']<a['trays'][0]['actual_flow_LPM']
    assert b['trays'][0]['orifice_dP_kPa']>0
    assert b['trays'][1]['orifice_dP_kPa']==0
    assert sum(b['pressure_budget_Pa'].values())==pytest.approx(b['metrics']['system_dp_Pa'],abs=.05)
    c['branches']['overrides']['C01']['orifice_diameter_m']=.008
    with pytest.raises(ValueError,match='Orifice'): solve(c)

def test_chip_failure_and_entered_manufacturer_limit():
    c=load_config();c['chip_temperature']={'GPU':{'target_max_C':60,'manufacturer_limit_C':65}}
    r=solve(c)
    assert not r['constraints']['chip_assumed_target']['pass']
    assert not r['constraints']['chip_entered_manufacturer_limit']['pass']
    assert not r['feasible']
    assert sum(x['count'] for x in r['chip_estimates'] if x['component']=='GPU')==72
    assert sum(x['count']*x['power_each_W'] for x in r['chip_estimates'])==pytest.approx(r['metrics']['heat_W'])

def test_facility_required_flow_meets_design_rise():
    c=load_config();c['facility']['design_deltaT_K']=10.;r=solve(c)
    c['facility']['flow_LPM']=r['facility']['required_flow_LPM']
    b=solve(c)
    assert b['facility']['FWS_deltaT_K']==pytest.approx(10.,abs=1e-6)
    assert b['facility']['required_UA_W_K']>0
    assert len(design_summary({'a':r,'b':b}))==2

def test_dashboard_new_controls():
    st=pytest.importorskip('streamlit.testing.v1')
    from pathlib import Path
    app=st.AppTest.from_file(str(Path('dashboard.py').resolve()),default_timeout=30).run()
    next(x for x in app.selectbox if x.label=='Coolant').set_value('EG50').run()
    assert not app.exception
    assert any('EG50' in x.value for x in app.info)
    next(x for x in app.button if x.label=='Run coolant comparison').click().run()
    assert not app.exception
    assert len(app.session_state['fluid_cases'][1])==3
