from copy import deepcopy
import numpy as np
import pytest
from nvl72.config import load_config
from nvl72.coolant import Coolant
from nvl72.orifices import coefficient, bore_from_coefficient
from nvl72.solver import solve

def test_inverse_over_geometry_and_resistance_range():
    for diameter in [.004,.006,.008,.0127]:
        for rho in [990,1020,1070]:
            for cd in [.5,.62,.8]:
                ks=np.geomspace(1e3,2e8,12)
                bores=[bore_from_coefficient(k,diameter,rho,cd) for k in ks]
                assert np.all(np.diff(bores)<0)
                for k,bore in zip(ks,bores):
                    assert 0<bore<diameter
                    assert coefficient(bore,diameter,rho,cd)==pytest.approx(k,rel=1e-9)
    assert bore_from_coefficient(0,.008,1020) is None

def test_auto_no_double_count_and_fixed_hardware_reproduction():
    c=load_config();c['branches']['switch']['restriction_K']=150e6
    c['branches']['overrides']['C01']={'restriction_K':1e6}
    reference=solve(c)
    c['balancing_mode']='auto_equivalent';auto=solve(c)
    fixed=solve(auto['fixed_orifice_config'])
    for r in [auto,fixed]:
        assert r['metrics']['system_dp_Pa']==pytest.approx(reference['metrics']['system_dp_Pa'],abs=.05)
        assert [t['actual_flow_LPM'] for t in r['trays']]==pytest.approx([t['actual_flow_LPM'] for t in reference['trays']],rel=2e-6)
    assert auto['trays'][0]['orifice_diameter_mm']>0
    assert auto['trays'][1]['orifice_diameter_mm'] is None
    assert sum(auto['pressure_budget_Pa'].values())==pytest.approx(auto['metrics']['system_dp_Pa'],abs=.05)
    c['branches']['overrides']['C01']['orifice_diameter_m']=.004
    with pytest.raises(ValueError,match='[Aa]uto'): solve(c)

def test_advisories_and_unavoidable_physical_failure():
    c=load_config();c['rack']['flow_LPM']=110
    r=solve(c)
    assert r['feasible'] and not r['screening_pass']
    c['constraint_policy']={'enforce_assumptions':True}
    assert not solve(c)['feasible']
    c=load_config();c['facility']['supply_C']=40
    c['constraint_policy']={'enforced':{'HX_cold_pinch':False}}
    r=solve(c)
    assert not r['feasible'] and r['constraints']['HX_cold_pinch']['enforced']
    c=load_config();c['rack']['flow_LPM']=131
    assert not solve(c)['constraints']['rack_flow']['pass']

def test_facility_boundaries_and_higher_flow():
    c=load_config();a=solve(c)
    c['facility'].update(flow_LPM=300,available_capacity_W=500000,UA_W_K=50000)
    b=solve(c)
    assert b['facility']['FWS_return_C']<a['facility']['FWS_return_C']
    assert b['facility']['required_UA_W_K']<a['facility']['required_UA_W_K']
    assert b['constraints']['facility_available_duty']['pass']
    c['facility']['available_capacity_W']=100000
    assert not solve(c)['constraints']['facility_available_duty']['pass']
    c['facility']['available_capacity_W']=500000;c['facility']['UA_W_K']=1000
    assert not solve(c)['constraints']['HX_user_UA']['pass']

def test_versioned_pg25_and_inrow_reference():
    c=load_config();p=Coolant('PG25_Dow2023',c['coolant']['property_file']).properties(313.15)
    assert (p.rho,p.cp,p.mu,p.k)==pytest.approx((1022.5,3920,.00158,.476))
    c['coolant']['type']='PG25_Dow2023';r=solve(c)
    assert r['validation']['energy_relative_error']<1e-8
    assert solve(load_config('config/inrow.yaml'))['facility']['rating_coolant']=='water'

def test_dashboard_automatic_and_manual_modes():
    from streamlit.testing.v1 import AppTest
    from pathlib import Path
    app=AppTest.from_file(str(Path('dashboard.py').resolve()),default_timeout=40).run()
    switch=next(x for x in app.number_input if x.label.startswith('Switch restriction'))
    switch.set_value(150.).run()
    assert not app.exception

    table=next(x.value for x in app.dataframe if 'orifice_diameter_mm' in x.value.columns)
    assert table.loc[table.tray_id=='S01','orifice_diameter_mm'].iloc[0]>0
    next(x for x in app.selectbox if x.label=='Balancing representation').set_value('Manual orifice bores').run()
    assert not app.exception
    next(x for x in app.selectbox if x.label=='Coolant').set_value('PG25_Dow2023').run()
    assert not app.exception

def test_legacy_report_preserves_original_policy(tmp_path):
    from nvl72.reporting import write_report
    r=solve(load_config());r.pop('screening_pass')
    for v in r['constraints'].values():
        v.pop('enforced');v.pop('basis')
    path=tmp_path/'legacy.md';write_report(r,path)
    assert 'Historical result: original enforcement policy retained.' in path.read_text()
