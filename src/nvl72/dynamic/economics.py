"""Scenario-conditioned economics; no automatic assertion of annual representativeness."""
from .settings import COSTS

def compare(fixed, active, s, count, total_count=27):
    costs=dict(COSTS[s['cost_case']]);costs.update(s.get('costs',{}))
    if any(x<0 for x in costs.values()): raise ValueError('Costs cannot be negative')
    cap_fixed=total_count*costs['orifice']
    cap_active=(total_count-count)*costs['orifice']+count*(costs['valve']+costs['temperature_sensor']+costs['flow_sensor'])+sum(costs[k] for k in ('pressure_sensors','controller','wiring','power_supply','integration'))
    incremental=cap_active-cap_fixed
    annual_fixed=fixed['average_aux_W']/1000*s['operating_hours']
    annual_active=active['average_aux_W']/1000*s['operating_hours']
    kwh=annual_fixed-annual_active
    maintenance=costs['active_maintenance']-costs['fixed_maintenance']
    savings=kwh*s['electricity_per_kWh']-maintenance
    horizon=s['payback_horizon_years']
    return dict(fixed_capex=cap_fixed,active_capex=cap_active,incremental_capex=incremental,
                annual_kWh_saved=kwh,annual_savings=savings,
                annual_fixed_cost=annual_fixed*s['electricity_per_kWh']+costs['fixed_maintenance'],
                annual_active_cost=annual_active*s['electricity_per_kWh']+costs['active_maintenance'],
                payback_years=max(0,incremental)/savings if savings>0 else None,
                savings_3_year=3*savings-incremental,savings_5_year=5*savings-incremental,
                savings_10_year=10*savings-incremental,
                break_even_price=(incremental/horizon+maintenance)/kwh if kwh>0 else None,
                affordable_incremental_capex=max(0,horizon*savings),
                affordable_installed_increment_per_branch=max(0,horizon*savings)/max(count,1),
                cost_inputs=costs)
