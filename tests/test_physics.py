import numpy as np
import pytest
from copy import deepcopy
from nvl72.config import load_config
from nvl72.coolant import Coolant
from nvl72.components import friction_factor,colebrook,pipe_loss
from nvl72.thermal import mix_temperature,temperatures
from nvl72.solver import solve
from nvl72.units import lpm_to_m3s,m3s_to_lpm
from nvl72.cdu import pump_head,intersection

@pytest.fixture
def cfg(): return load_config()

def test_units(): assert m3s_to_lpm(lpm_to_m3s(120))==pytest.approx(120)

def test_pipe_analytical():
    # Hagen-Poiseuille at low Re: dp=128 mu L q/(pi D^4).
    q=1e-6; mu=0.001; d=0.01
    actual=pipe_loss(q*1000,1000,mu,d,1,0)['friction']
    assert actual==pytest.approx(128*mu*q/(np.pi*d**4))
    assert friction_factor(1000)==pytest.approx(.064)
    assert friction_factor(100000,1e-4)==pytest.approx(colebrook(100000,1e-4),rel=.02)
    assert pipe_loss(0,1000,mu,d,1,0)['friction']==0

def test_properties_and_enthalpy(cfg):
    f=Coolant('PG25',cfg['coolant']['property_file'])
    p=f.properties(313.15)
    assert (p.rho,p.cp,p.mu,p.k)==pytest.approx((1020,4120,.00147,.476))
    assert f.properties(323.15).mu==pytest.approx(.00115)
    t=np.linspace(280,365,200)
    assert np.max(abs(f.temperature(f.enthalpy(t))-t))<1e-10
    with pytest.raises(ValueError): f.properties(400)

def test_thermal_mixing(cfg):
    f=Coolant('PG25',cfg['coolant']['property_file'])
    mixed=mix_temperature([1,3],[300,320],f)
    assert f.enthalpy(mixed)==pytest.approx((f.enthalpy(300)+3*f.enthalpy(320))/4)
    out,ret,err=temperatures(np.array([.1,.1]),np.array([1000.,1000.]),300,f)
    assert out[0]==out[1] and err<1e-10
    out2,_,_=temperatures(np.array([.05,.1]),np.array([1000.,2000.]),300,f)
    assert out2[0]>out[0] and out2[1]>out[1]

def test_parallel_analytical(cfg):
    from nvl72.hydraulics import solve_network
    cfg['rack'].update(layout=['C01','C02'],compute_trays=2,switch_trays=0,gravity_enabled=False)
    cfg['geometry']['height_m']=1e-10
    for side in ('supply','return'): cfg['geometry'][side].update(inlet_m=100.,outlet_m=100.)
    for values in cfg['loss_coefficients'].values():
        for k in values: values[k]=0.
    b=dict(cfg['branches']['compute']); b.update(tube_length_m=0,coldplate_K=1e6,qdc_K=0,restriction_K=0)
    fluid=Coolant('PG25',cfg['coolant']['property_file']); p=fluid.properties(np.array([313.15,313.15]))
    r=solve_network(cfg,[b,b],.2,fluid.properties(313.15),p,p)
    assert r.mass_flow==pytest.approx([.1,.1])
    assert r.head_Pa==pytest.approx(10000)

def test_baseline_balances(cfg):
    r=solve(cfg)
    assert len(r['trays'])==27 and r['metrics']['heat_W']==115560
    assert r['validation']['mass_relative_error']<1e-8
    assert r['validation']['energy_relative_error']<1e-8
    assert r['validation']['pressure_residual_Pa']<.05
    assert np.ptp([t['supply_pressure_kPa'] for t in r['trays']])>1
    assert np.ptp([t['return_pressure_kPa'] for t in r['trays']])>1
    assert sum(r['pressure_budget_Pa'].values())==pytest.approx(r['metrics']['system_dp_Pa'],abs=.05)
    assert r['trays'][0]['target_flow_LPM']==pytest.approx(120*5800/115560)

def test_monotonic_network(cfg):
    a=solve(cfg)
    c=deepcopy(cfg); c['branches']['overrides']['C01']={'coldplate_K':11e6}
    assert solve(c)['trays'][0]['actual_flow_LPM']<a['trays'][0]['actual_flow_LPM']
    c=deepcopy(cfg); c['rack']['flow_LPM']=125
    assert solve(c)['metrics']['rack_dp_Pa']>a['metrics']['rack_dp_Pa']
    c=deepcopy(cfg)
    for side in ('supply','return'): c['geometry'][side]['inlet_m']=.05
    assert solve(c)['pressure_budget_Pa']['header_friction']<a['pressure_budget_Pa']['header_friction']

def test_pump_analytical(cfg):
    d=cfg['cdu']; q0=float(lpm_to_m3s(d['nominal_flow_LPM'])); k=2e10
    a=(d['shutoff_dp_Pa']-d['available_dp_Pa'])/q0**2
    q=intersection(lambda x:k*x*x,d,(0,.005))
    assert q==pytest.approx(np.sqrt(d['shutoff_dp_Pa']/(a+k)))
    d2=deepcopy(d); d2['speed']=.7
    assert pump_head(.7*q,d2)==pytest.approx(.49*pump_head(q,d))

def test_gravity_cancellation(cfg):
    cfg['power']['tray_heat_W']=[0.]*27
    a=solve(cfg); cfg['rack']['gravity_enabled']=False; b=solve(cfg)
    assert a['hydraulics']['mass_flow']==pytest.approx(b['hydraulics']['mass_flow'],rel=1e-8)
    rho=1020; dz=cfg['geometry']['height_m']
    assert a['hydraulics']['supply_Pa'][-1]-b['hydraulics']['supply_Pa'][-1]==pytest.approx(-rho*9.80665*dz,abs=.05)
