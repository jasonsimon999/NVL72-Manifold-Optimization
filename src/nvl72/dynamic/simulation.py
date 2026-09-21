"""Quasi-steady coupled hydraulics + two-node transient heat storage + sampled controls."""
from copy import deepcopy
import numpy as np
from ..solver import solve
from ..rack import tray_data
from ..coolant import Coolant
from ..thermal import temperatures
from ..orifices import bore_from_coefficient
from .settings import settings, validate
from .workloads import generate
from .hydraulic import operating_point, valve_branches, initial_positions
from .thermal import advance
from .control import demand, command, actuate
from .pump import update as pump_update
from .economics import compare as economic_compare

def prepare(config, s):
    c=deepcopy(config)
    c['rack']['operating_mode']='fixed_flow'
    c['rack']['flow_LPM']*=s['design_flow_scale']
    c['rack']['supply_C']+=s['supply_offset_K']
    for side in ('supply','return'):
        for key in ('inlet_m','outlet_m'): c['geometry'][side][key]*=s['header_scale']
        c['geometry'][side]['pieces_m']=[d*s['header_scale'] for d in c['geometry'][side]['pieces_m']]
    ids,kinds,heat,branches=tray_data(c)
    # Existing heat assignment is interpreted as electrical-equivalent reference input
    # on this separate page. f_liquid=1 preserves the original liquid-load baseline.
    electrical=heat*np.array([s[k+'_power_scale'] for k in kinds])
    fraction=np.array([s[k+'_liquid_fraction'] for k in kinds])
    for i,b in enumerate(branches):
        b['coldplate_K']*=s['coldplate_scale'];b['qdc_K']*=s['qd_scale']
        if 'qdc_reference_K' in b:b['qdc_reference_K']*=s['qd_scale']
        for component,factor in [('coldplate_curve',s['coldplate_scale']),('qdc_curve',s['qd_scale'])]:
            if component in b:
                curve=b[component]
                key='dp_Pa' if 'dp_Pa' in curve else 'polynomial'
                curve[key]=[v*factor for v in curve[key]]
        c['branches']['overrides'][ids[i]]=b
    c['power']['tray_heat_W']=(electrical*fraction).tolist()
    r=solve(c)
    # Freeze physical bores once, never re-balance during a workload.
    if r.get('fixed_orifice_config'): c=deepcopy(r['fixed_orifice_config'])
    ids,kinds,_,branches=tray_data(c)
    fluid=Coolant(c['coolant']['type'],c['coolant']['property_file'],c['coolant']['viscosity_multiplier'])
    inlet=c['rack']['supply_C'];ps=fluid.properties(inlet+273.15)
    m=np.asarray(r['hydraulics']['mass_flow'])
    tout,mixed,_=temperatures(m,electrical*fraction,inlet+273.15,fluid)
    pb=fluid.properties((inlet+273.15+tout)/2);pr=fluid.properties(mixed)
    # Legacy resistance-only balancing becomes an equivalent physical fixed plate.
    for i,b in enumerate(branches):
        if b.get('orifice_diameter_m') is None and b['restriction_K']>0:
            b['orifice_diameter_m']=bore_from_coefficient(b['restriction_K'],b['diameter_m'],float(pb.rho[i]),b.get('orifice_Cd',.62))
            b['restriction_K']=0.
    q=m.sum()/float(ps.rho)*c['cdu']['served_racks']
    rated=c['cdu']['nominal_flow_LPM']/60000
    slope=(c['cdu']['shutoff_dp_Pa']-c['cdu']['available_dp_Pa'])/rated**2
    if slope<=0: raise ValueError('Pump curve must have falling head with increasing flow')
    speed=np.sqrt((r['metrics']['system_dp_Pa']+slope*q*q)/c['cdu']['shutoff_dp_Pa'])
    return dict(config=c,reference=r,ids=ids,kinds=kinds,electrical=electrical,fraction=fraction,
                branches=branches,props=(ps,pb,pr),base_mass=m,inlet=inlet,
                reference_speed=float(speed),reference_head=r['metrics']['system_dp_Pa'])

def simulate(prepared, s, controller='fixed'):
    validate(s)
    p=prepared;c=p['config'];n=len(p['ids']);ps,pb,pr=p['props'];cp=float(ps.cp)
    t,util,connection=generate(p['kinds'],s);dt=s['dt_s']
    electrical=util*p['electrical'];power=electrical*p['fraction']
    active=controller not in ('fixed','locked')
    controlled=np.arange(n)<min(n,int(s['controlled_branches']))
    resistance=np.array([s[k+'_R_K_W'] for k in p['kinds']])
    capacity=np.array([s[k+'_C_J_K'] for k in p['kinds']])
    opening=initial_positions(p['branches'],pb.rho,s);integral=np.zeros(n);target_open=opening.copy()
    speed=min(s['pump_max_speed'],max(s['pump_min_speed'],p['reference_speed'])) if s['pump_enabled'] else 0.
    point=operating_point(c,p['branches'],p['props'],speed,np.ones(n),p['base_mass'])
    mass=point['mass']
    # Shared physical initial condition: fixed baseline equilibrium at first load.
    outlet=p['inlet']+power[0]/np.maximum(mass*cp,1e-9)
    if not s['pump_enabled']:outlet=np.full(n,p['inlet'])
    chip=outlet+resistance*power[0] if s['pump_enabled'] else outlet.copy()
    measured=chip.copy();rng=np.random.default_rng(int(s['seed'])+9)
    next_sensor=0.;next_control=0.;last_command=opening.copy();actuations=0
    travel=0.;energy_error=0.;pressure_error=0.;mass_error=0.
    arrays={k:[] for k in ('chip_C','outlet_C','mass','target_mass','opening','orifice_diameter_mm','branch_dp_Pa',
                           'supply_Pa','return_Pa','pump_W','valve_W','speed','head_Pa',
                           'rack_head_Pa','energy_residual_W','header_velocity_m_s','removed_W','storage_W')}
    failure_index=min(n-1,max(0,int(s['failure_tray'])))
    for j,time in enumerate(t):
        conn=connection[j];target=demand(power[j],cp,p['base_mass'],s)*(conn>0)
        failed=time>=s['event_s'];failure=s['failure'] if failed and active else 'none'
        if time+1e-8>=next_sensor:
            measured=chip+s['sensor_bias_K']+rng.normal(0,s['sensor_noise_K'],n)
            if failure in ('sensor_high','sensor_low'):measured[failure_index]+=s['sensor_failure_bias_K']*(1 if failure=='sensor_high' else -1)
            next_sensor=time+s['sensor_s']
        if active and time+1e-8>=next_control:
            target_open,integral=command(controller,opening,measured,mass,target,integral,s,s['control_s'])
            next_control=time+s['control_s']
        if failure=='communications':target_open[:]=s['fail_position']
        previous=opening.copy()
        if active and j>0:opening=actuate(opening,target_open,s,dt)
        if failure.startswith('stuck_'):
            opening[failure_index]={'stuck_closed':0.,'stuck_open':1.,'stuck_half':.5}[failure]
        changed=abs(target_open-last_command)>s['valve_deadband']
        actuations+=int(np.sum(changed&controlled)) if active else 0
        last_command=target_open.copy()
        travel+=float(np.sum(abs(opening-previous)[controlled])) if active else 0.
        branches=valve_branches(p['branches'],opening,conn,pb.rho,controlled,s,active)
        hydraulic_connection=conn.copy()
        if active and s['valve_min_area_fraction']==0:
            hydraulic_connection[controlled&(opening<=0)]=0.
        point=operating_point(c,branches,p['props'],speed,hydraulic_connection,mass)
        mass=point['mass']
        if j:
            chip,outlet,removed,res=advance(chip,outlet,power[j],mass,p['inlet'],resistance,capacity,s['coolant_C_J_K'],cp,dt)
        else:
            res=np.zeros(n);removed=mass*cp*(outlet-p['inlet'])
        energy_error=max(energy_error,float(np.max(abs(res))))
        pressure_error=max(pressure_error,point['pressure_error']);mass_error=max(mass_error,point['mass_error'])
        moving=abs(opening-previous)>1e-8
        valves=float(np.sum(np.where(moving,s['valve_running_W'],s['valve_holding_W'])[controlled])+s['electronics_W']) if active else 0.
        pump=max(0,point['head'])*mass.sum()/float(ps.rho)/s['pump_efficiency']
        values=dict(chip_C=chip.copy(),outlet_C=outlet.copy(),mass=mass.copy(),target_mass=target,
                    opening=np.where(controlled,opening,np.nan) if active else np.full(n,np.nan),
                    orifice_diameter_mm=np.array([1000*float(b.get('orifice_diameter_m') or np.nan) if controlled[i] or not active else np.nan for i,b in enumerate(branches)]),
                    branch_dp_Pa=point['branch_dp'],
                    supply_Pa=point['supply'],return_Pa=point['return_pressure'],pump_W=pump,valve_W=valves,
                    speed=speed,head_Pa=point['head'],rack_head_Pa=point['rack_head'],energy_residual_W=float(np.max(abs(res))),
                    header_velocity_m_s=point['header_velocity'],removed_W=removed.copy(),storage_W=power[j]-removed-res)
        for k,v in values.items():arrays[k].append(v)
        speed=pump_update(speed,point,target,p['reference_head'],p['reference_speed'],s,dt,
                          lag=failed and s['failure']=='pump_lag')
    result={k:np.asarray(v) for k,v in arrays.items()}
    result.update(time_s=t,electrical_W=electrical,liquid_W=power,connected=connection,
                  controller=controller,ids=p['ids'],kinds=p['kinds'])
    result['flow_LPM']=result['mass']/float(ps.rho)*60000
    result['summary']=summarize(result,s,p)
    result['summary'].update(valve_actuations=actuations,valve_full_cycles=travel/2,
                             valve_travel=travel,pressure_residual_Pa=pressure_error,
                             node_mass_residual_kg_s=mass_error,energy_residual_W=energy_error)
    result['per_tray']=[dict(tray_id=id,peak_solid_C=float(result['chip_C'][:,i].max()),
                            peak_outlet_C=float(result['outlet_C'][:,i].max()),
                            peak_deltaT_K=float(result['outlet_C'][:,i].max()-p['inlet']),
                            time_above_limit_s=float(np.sum(result['chip_C'][1:,i]>s['chip_limit_C'])*dt))
                        for i,id in enumerate(p['ids'])]
    return result

def summarize(r,s,p):
    dt=s['dt_s'];elapsed=r['time_s'][-1]
    # Backward-Euler/right-endpoint quadrature matches discrete heat balance.
    avg=lambda a:float(np.sum(a[1:])*dt/elapsed)
    target=r['target_mass'];mask=(target>0)&(r['connected']>0)
    error=np.divide(r['mass']-target,target,out=np.zeros_like(target),where=mask)
    relevant=np.where(mask,error,np.nan)
    worst=int(np.nanargmax(np.nanmax(abs(relevant),axis=0)))
    compute=np.array(r['kinds'])=='compute';chip=r['chip_C'];out=r['outlet_C']
    operating=r['connected']>0
    live_chip=np.where(operating,chip,np.nan);live_out=np.where(operating,out,np.nan)
    pump_energy=avg(r['pump_W'])*elapsed/3600000
    valve_energy=avg(r['valve_W'])*elapsed/3600000
    after=r['time_s']>=s['event_s']
    acceptable=np.all((chip<=s['chip_limit_C'])|~operating,axis=1)&np.all((out<=s['outlet_limit_C'])|~operating,axis=1)
    bad=np.where(after&~acceptable)[0]
    recovery=None
    if after.any() and (len(bad)==0 or bad[-1]<len(chip)-1):
        recovery=0. if len(bad)==0 else float(r['time_s'][bad[-1]+1]-s['event_s'])
    return dict(peak_compute_C=float(np.nanmax(live_chip[:,compute])),peak_switch_C=float(np.nanmax(live_chip[:,~compute])),
                peak_chip_C=float(np.nanmax(live_chip)),mean_chip_C=float(np.nanmean(live_chip)),
                max_temperature_spread_K=float(np.nanmax(np.nanmax(live_chip,axis=1)-np.nanmin(live_chip,axis=1))),peak_outlet_C=float(np.nanmax(live_out)),
                time_above_limit_s=float(np.sum(np.any((chip[1:]>s['chip_limit_C'])&operating[1:],axis=1))*dt),
                outlet_time_above_limit_s=float(np.sum(np.any((out[1:]>s['outlet_limit_C'])&operating[1:],axis=1))*dt),
                thermal_margin_K=float(s['chip_limit_C']-np.nanmax(live_chip)),
                peak_deltaT_K=float(np.nanmax(live_out)-p['inlet']),average_flow_LPM=avg(r['flow_LPM'].sum(axis=1)),
                peak_flow_LPM=float(r['flow_LPM'].sum(axis=1).max()),
                peak_head_kPa=float(r['head_Pa'].max()/1000),
                min_branch_dp_kPa=float(r['branch_dp_Pa'][r['connected']>0].min()/1000),
                max_branch_dp_kPa=float(r['branch_dp_Pa'].max()/1000),
                average_pump_W=avg(r['pump_W']),average_aux_W=avg(r['pump_W']+r['valve_W']),
                pump_energy_kWh=pump_energy,valve_energy_kWh=valve_energy,
                auxiliary_energy_kWh=pump_energy+valve_energy,
                rms_flow_error=float(np.sqrt(np.nanmean(relevant**2))),
                max_abs_flow_error=float(np.nanmax(abs(relevant))),flow_error_std=float(np.nanstd(relevant)),
                worst_tray=p['ids'][worst],average_IT_W=avg(r['electrical_W'].sum(axis=1)),
                maximum_flow_overshoot_percent=float(np.nanmax(relevant)*100),
                temperature_overshoot_K=float(max(0,np.nanmax(live_chip)-s['temperature_target_C'])),
                recovery_s=recovery,
                valve_saturation_s=float(np.sum(np.any((r['opening'][1:]<.01)|(r['opening'][1:]>.99),axis=1))*dt),
                peak_header_velocity_m_s=float(r['header_velocity_m_s'].max()),
                thermal_pass=bool(acceptable.all()))

def run_comparison(config, s=None):
    s=settings(**(s or {}));p=prepare(config,s)
    fixed=simulate(p,s,'fixed');trial=simulate(p,s,s['controller'])
    # Active control is a candidate, not an automatic winner.  Select it only
    # when its constrained score improves on the same fixed-orifice boundary;
    # otherwise expose the fixed result as the active design so the UI never
    # recommends a worse configuration.
    fixed_score=objective_score(fixed['summary'],s,fixed['summary'])
    trial_score=objective_score(trial['summary'],s,fixed['summary'])
    hard_pass=bool(trial['summary']['thermal_pass'] and trial['summary']['pressure_residual_Pa']<1.0
                   and trial['summary']['node_mass_residual_kg_s']<1e-9
                   and trial['summary']['energy_residual_W']<1e-5)
    # The automatic winner rule is specific to the optimized diameter mode.
    # The other controllers remain available as diagnostic experiments, where
    # their raw behavior is intentionally shown even when it is worse.
    choose_optimized=s['controller']=='optimized'
    selected=trial if (not choose_optimized or (hard_pass and trial_score < fixed_score-s['optimization_fallback_tolerance'])) else deepcopy(fixed)
    fallback=selected is not trial
    selected['selected_from']='fixed' if fallback else 'optimized_active'
    selected['controller']='fixed_fallback' if fallback else s['controller']
    active=selected
    f,a=fixed['summary'],active['summary']
    selected_count=0 if fallback else min(len(p['ids']),int(s['controlled_branches']))
    econ=economic_compare(f,a,s,selected_count,len(p['ids']))
    pump_saving=f['average_pump_W']-a['average_pump_W']
    net=f['average_aux_W']-a['average_aux_W']
    benefit=dict(pump_reduction_percent=100*pump_saving/f['average_pump_W'] if f['average_pump_W']>0 else None,
                 pump_savings_W=pump_saving,net_savings_W=net,
                 savings_percent_IT=100*net/f['average_IT_W'] if f['average_IT_W']>0 else None,
                 peak_temperature_reduction_K=f['peak_chip_C']-a['peak_chip_C'])
    facility={}
    for name,result in [('fixed',fixed),('active',active)]:
        max_removed=float(result['removed_W'].sum(axis=1).max())
        rating=p['reference']['facility']['HX_available_W_per_rack']
        facility[name]=dict(peak_rejected_heat_W=max_removed,reference_HX_available_W=rating,
                            HX_reference_margin_W=rating-max_removed,
                            rating_screen_pass=bool(max_removed<=rating),
                            peak_flow_LPM=result['summary']['peak_flow_LPM'],
                            configured_flow_screen_pass=bool(result['summary']['peak_flow_LPM']<=config['constraints']['rack_flow_max_LPM']),
                            OCP_velocity_advisory_pass=bool(result['summary']['peak_header_velocity_m_s']<1.5),
                            note='HX capacity frozen at reference rating, not a dynamic heat exchanger calculation; inlet is externally maintained.')
    reason=('Fixed-orifice design retained: active diameter trial did not improve the constrained score '
            'or failed a numerical/thermal screen.' if fallback else
            ('Optimized active orifice diameters selected: constrained score improved while screens passed.'
             if choose_optimized else 'Diagnostic controller shown without automatic winner selection.'))
    return dict(settings=s,baseline_config=p['config'],baseline_reference=p['reference'],
                fixed=fixed,active=active,active_candidate=trial,economics=econ,benefit=benefit,
                optimization=dict(selected_from=selected['selected_from'],fallback_to_fixed=fallback,
                                  fixed_score=float(fixed_score),active_trial_score=float(trial_score),
                                  hard_pass=hard_pass,reason=reason),facility_screen=facility)

def objective_score(summary,s,reference):
    """Dimensionless engineering score used only to choose active vs fixed.

    Thermal and flow tracking are normalized by entered limits; pumping,
    pressure and actuator activity are normalized by the fixed baseline.  This
    is a transparent screening objective, not a claim of global optimality.
    """
    scale_p=max(float(reference['average_pump_W']),1.)
    scale_h=max(float(reference['peak_head_kPa']),1.)
    thermal=max(0.,float(summary['peak_chip_C']-s['chip_limit_C']))/max(s['chip_limit_C'],1.)
    return (s['optimization_temperature_weight']*thermal
            +s['optimization_flow_weight']*float(summary['rms_flow_error'])
            +s['optimization_worst_flow_weight']*float(summary['max_abs_flow_error'])
            +s['optimization_pump_weight']*float(summary['average_aux_W'])/scale_p
            +s['optimization_pressure_weight']*float(summary['peak_head_kPa'])/scale_h
            +s['optimization_actuation_weight']*float(summary['valve_full_cycles'])/max(1.,len(reference.get('per_tray',[]))))
