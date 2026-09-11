from copy import deepcopy
import json
import numpy as np
import pytest
from nvl72.config import load_config
from nvl72.solver import solve
from nvl72.components import curve_loss,pipe_loss
from nvl72.manifold import diameter_profile
from nvl72.objectives import pareto_mask
from nvl72.scenarios import scenario

@pytest.fixture
def cfg():return load_config()

def test_profiles():
    s={'profile':'power','inlet_m':.04,'outlet_m':.02,'exponent':2,'pieces_m':[.04,.03,.02]}
    assert diameter_profile(s,np.array([0,.5,1]))==pytest.approx([.04,.035,.02])
    s['profile']='piecewise'
    assert diameter_profile(s,np.array([0,.4,1]))==pytest.approx([.04,.03,.02])

def test_curve():
    assert curve_loss(.001,{'polynomial':[1e10,2e5,0]})==pytest.approx(10200)
    assert curve_loss(.001,{'flow_m3_s':[0,.001,.002],'dp_Pa':[0,10000,40000]})==10000
    with pytest.raises(ValueError):curve_loss(.003,{'flow_m3_s':[0,.001],'dp_Pa':[0,1]})
    assert pipe_loss(-.1,1000,.001,.01,1,0)['friction']<0

def test_pareto():
    assert pareto_mask([[1,3],[2,2],[3,1],[4,4]]).tolist()==[True,True,True,False]

def test_near_zero_and_closed_branch(cfg):
    r=solve(scenario(cfg,'near_zero'));assert np.isfinite(r['metrics']['RMS_target_error'])
    r=solve(scenario(cfg,'compute_removed'));assert len(r['trays'])==26 and r['validation']['converged']

def test_invalid_inputs_and_nonconvergence(cfg):
    c=deepcopy(cfg);c['rack']['flow_LPM']=-1
    with pytest.raises(ValueError):solve(c)
    c=deepcopy(cfg);c['solver']['max_property_iterations']=1
    with pytest.raises(RuntimeError,match='iteration failed'):solve(c)
    c=deepcopy(cfg);c['rack']['supply_C']=100
    with pytest.raises(ValueError,match='property range'):solve(c)

def test_pump_actual_intersection(cfg):
    cfg['rack']['operating_mode']='pump'
    r=solve(cfg)
    assert r['validation']['pump_intersection_residual_Pa']<.05
    # A root outside rated flow remains visible as infeasible, never clamped.
    assert not r['feasible']

def test_facility_and_head_fail_visible(cfg):
    cfg['facility']['supply_C']=39
    r=solve(cfg)
    assert not r['constraints']['HX_capacity']['pass'] and not r['constraints']['HX_approach']['pass']
    cfg=load_config();cfg['external']['enabled']=True;cfg['external']['equipment_K']=1e5
    r=solve(cfg);assert not r['constraints']['CDU_external_head']['pass']

def test_optional_channels_and_water(cfg):
    cfg['coldplate']['enabled']=True;cfg['coolant']['type']='water'
    r=solve(cfg)
    assert np.isfinite(r['metrics']['T_chip_max_C'])
    assert np.all(r['coldplate']['h_W_m2_K']>0)

def test_provenance_covers_baseline():
    import yaml
    from nvl72.config import ROOT
    cfg=yaml.safe_load((ROOT/'config/baseline.yaml').read_text());sources=yaml.safe_load((ROOT/'data/sources.yaml').read_text())['defaults']
    def paths(d,p=''):
        for k,v in d.items():
            key=f'{p}.{k}' if p else k
            if isinstance(v,dict) and v:yield from paths(v,key)
            else:yield key
    assert set(paths(cfg))<=set(sources)
    assert all(s['category'] in ('NVIDIA','OEM','OCP','3P','DERIVED','ESTIMATE','ASSUMPTION') for s in sources.values())

def test_inrow_aggregate(cfg):
    c=load_config('config/inrow.yaml');r=solve(c)
    assert r['facility']['aggregate_heat_W']==pytest.approx(115560*8)
    assert r['metrics']['system_dp_Pa']>r['metrics']['rack_dp_Pa']
    assert r['constraints']['CDU_aggregate_flow']['margin']==240
