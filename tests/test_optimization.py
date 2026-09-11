"""Meaningful design-level regression and dashboard interaction checks."""
import numpy as np
import pytest
from nvl72.config import load_config
from nvl72.solver import solve
from nvl72.optimize import balance_locations,optimize

def test_inverse_balance_verified_by_network():
    c=load_config();r=balance_locations(c)
    assert r['metrics']['RMS_target_error']<1e-7
    assert min(x['restriction_K'] for x in r['config']['branches']['overrides'].values())>=0
    assert r['validation']['pressure_residual_Pa']<.05

def test_local_optimizer_improves_feasible_baseline():
    c=load_config();base=solve(c);r,rows=optimize(c,'C')
    assert r['feasible'] and r['optimization']['local_success']
    assert r['metrics']['RMS_target_error']<.02
    assert r['metrics']['T_out_max_C']<base['metrics']['T_out_max_C']
    assert len(rows)>1

def test_saved_result_reproduces():
    from pathlib import Path
    import json
    p=Path('results/optimized.json')
    if not p.exists():pytest.skip('Study has not run yet')
    saved=json.loads(p.read_text());r=solve(saved['config'])
    for key in ('T_out_max_C','rack_dp_Pa','RMS_target_error'):
        assert r['metrics'][key]==pytest.approx(saved['metrics'][key],rel=1e-7,abs=1e-7)

def test_dashboard_interaction():
    st=pytest.importorskip('streamlit.testing.v1')
    app=st.AppTest.from_file(str(__import__('pathlib').Path('dashboard.py').resolve()),default_timeout=30).run()
    assert not app.exception
    app.sidebar.slider[0].set_value(110).run()
    assert not app.exception
    assert len(app.error)>0  # conservative HX derating rejects this full-load point
