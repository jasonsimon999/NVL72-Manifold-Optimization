"""Streamlit interface isolated from the fixed-orifice dashboard."""
from copy import deepcopy
import json
import hashlib
import numpy as np
import pandas as pd
import yaml
import streamlit as st
import matplotlib.pyplot as plt
from ..config import load_config,portable_config,merge
from ..solver import solve
from .baseline import optimized_reference as build_reference
from ..reporting import native
from ..dashboard_support import model_fingerprint
from .settings import DEFAULTS,COSTS,SCENARIOS,FAILURES,settings
from .simulation import run_comparison
from .sources import registry,REFERENCES
from . import studies,plotting
from .export import dumps

@st.cache_data(show_spinner=False)
def optimized_reference(root,revision):
    return build_reference(root)

@st.cache_data(show_spinner=False,max_entries=12)
def calculate(c,s,revision):return run_comparison(c,s)

def show_figure(fig):
    st.pyplot(fig,width='stretch');plt.close(fig)

def render(root):
    st.markdown('<style>.block-container{max-width:1450px;padding-top:2rem;}[data-testid="stMetric"]{background:var(--secondary-background-color);padding:14px;border-radius:12px;}</style>',unsafe_allow_html=True)
    st.title('Dynamic flow control')
    if st.button('🎛️ Return to Fixed-Orifice Manifold', help='Return to the passive fixed-orifice page in this same Streamlit tab.'):
        st.session_state['show_dynamic_flow'] = False
        st.rerun()
    st.markdown('**Does actively varying coolant flow to individual trays provide enough thermal and pumping-energy benefit to justify its added cost and complexity compared with an optimized passive fixed-orifice manifold?**')
    st.caption('1 · Choose a workload   →   2 · Compare the same hardware boundary   →   3 · Check thermal limits and net savings')
    st.info('Research model: temperatures represent an equivalent tray thermal node, not a validated hottest GPU junction. Workloads, thermal inertia, valve sizing and installed costs are assumptions. The fixed-orifice homepage is unchanged.')
    revision=model_fingerprint(root)
    options=['Optimized per-tray reference']
    if 'dynamic_baseline_config' in st.session_state:options.insert(0,'Current fixed-page design — unchanged')
    selection=st.selectbox('Passive reference design',options,help='The optimized reference uses the existing analytical minimum-head location-balancing routine at fixed geometry. It is not a global geometry optimum. Imported designs are never automatically redesigned.')
    try:
        c=deepcopy(st.session_state['dynamic_baseline_config']) if selection.startswith('Current') else optimized_reference(root,revision)
    except (ValueError,RuntimeError) as exc:st.error(str(exc));return
    with st.expander('Baseline, coolant and CDU details'):
        st.write(f"{c['name']} · {c['coolant']['type']} · {c['rack']['supply_C']} °C supply · {c['rack']['flow_LPM']} L/min design flow")
        st.caption('Export a fixed-orifice YAML from the original page to compare a saved design. This page freezes its bores for the full transient.')
        upload=st.file_uploader('Import fixed design YAML',type=['yaml','yml'])
        if upload:
            try:
                incoming=yaml.safe_load(upload.getvalue());c=merge(c,incoming)
                c['coolant']['property_file']=str(root/'data/coolant_properties.csv')
            except (ValueError,TypeError,yaml.YAMLError) as exc:st.error(f'Invalid design: {exc}');return
        st.json(portable_config(c),expanded=False)
    with st.form('dynamic_configuration'):
        cols=st.columns(3)
        with cols[0]:
            scenario=st.selectbox('Workload / service event',SCENARIOS,index=3,format_func=lambda x:x.replace('_',' ').title())
            controller=st.selectbox('Active branch controller',['combined','feedforward','reactive'],format_func=lambda x:{'combined':'Power + temperature feedback','feedforward':'Power target + flow tracking','reactive':'Temperature PI'}[x])
        with cols[1]:
            pump=st.selectbox('Pump control — same for both designs',['demand','constant_speed','constant_dp'],format_func=lambda x:{'demand':'Demand-following variable speed','constant_speed':'Constant speed','constant_dp':'Constant differential pressure'}[x],help='Demand-following is a flow-tracking heuristic, not a proven global minimum-energy optimizer. Fixed branches receive the same pump policy.')
            duration=st.number_input('Simulation duration · s',60.,3600.,300.,60.)
        with cols[2]:
            price=st.number_input('Electricity · $/kWh',0.,5.,.12,.01)
            cost_case=st.selectbox('Hardware cost case',['low','nominal','high'],index=1)
        s=dict(DEFAULTS,scenario=scenario,controller=controller,pump_mode=pump,duration_s=duration,electricity_per_kWh=price,cost_case=cost_case)
        with st.expander('Workload, thermal response, valves, sensors and pump — advanced'):
            st.caption('All settings are available here. Fractions run from 0 to 1. Use smaller timesteps to check transient accuracy. The motorized actuator default takes 90 s for a full stroke; faster valves must be justified separately.')
            groups={
                'Workload & maintenance':['low_load','high_load','spike_s','duty','correlation','ramp_per_s','localized_count','seed','event_s','reconnect_s','reconnect_ramp_s'],
                'Thermal assumptions':['compute_power_scale','switch_power_scale','compute_liquid_fraction','switch_liquid_fraction','compute_C_J_K','switch_C_J_K','compute_R_K_W','switch_R_K_W','coolant_C_J_K','chip_limit_C','outlet_limit_C','target_rise_K','minimum_flow_fraction','supply_offset_K'],
                'Valves & controls':['valve_min_area_fraction','valve_max_bore_fraction','valve_Cd','valve_body_K','valve_tau_s','valve_stroke_s','valve_deadband','valve_running_W','valve_holding_W','electronics_W','fail_position','controlled_branches','temperature_target_C','kp_per_K','ki_per_K_s','flow_gain','control_s','sensor_s','sensor_noise_K','sensor_bias_K'],
                'Hydraulics & numerical settings':['coldplate_scale','qd_scale','header_scale','design_flow_scale','pump_tau_s','pump_min_speed','pump_max_speed','pump_efficiency','dt_s'],
            }
            tabs=st.tabs(list(groups))
            metadata={r['parameter']:r for r in registry(s)}
            for tab,keys in zip(tabs,groups.values()):
                with tab:
                    cs=st.columns(3)
                    for i,key in enumerate(keys):
                        row=metadata[key]
                        s[key]=cs[i%3].number_input(key.replace('_',' '),value=float(s[key]),format='%.4f',help=row['notes']+' Suggested range: '+row['range'],key='dynamic_'+key)
            s['pump_enabled']=st.checkbox('Pump enabled',True)
        with st.expander('Fault injection'):
            s['failure']=st.selectbox('Failure',FAILURES)
            s['failure_tray']=st.selectbox('Affected tray',range(len(c['rack']['layout'])),format_func=lambda i:c['rack']['layout'][i])
            s['sensor_failure_bias_K']=st.number_input('Fault sensor bias magnitude · K',0.,40.,8.)
            st.caption('Faults begin at event time. Communications fallback assumes actuator power remains. A mechanical stuck valve ignores fallback commands.')
        with st.expander('Cost assumptions & annualization'):
            s['operating_hours']=st.number_input('Annual operating hours represented by this workload',0.,8760.,8760.)
            s['payback_horizon_years']=st.number_input('Break-even horizon · years',1.,30.,5.)
            st.caption('Annualization assumes this short scenario repeats for these hours. Cost ranges are budgets, not quotes. Flow sensors are included because feed-forward control tracks measured branch flow.')
            edited=st.data_editor(pd.DataFrame(COSTS).rename_axis('item').reset_index(),hide_index=True,disabled=['item'],key='dynamic_cost_table')
            s['costs']=dict(zip(edited['item'],edited[cost_case]))
        submitted=st.form_submit_button('Run fixed vs active comparison',type='primary')
    try:s=settings(**s)
    except ValueError as exc:st.error(str(exc));return
    signature=hashlib.sha256((json.dumps(native(c),sort_keys=True)+json.dumps(s,sort_keys=True)+revision).encode()).hexdigest()
    if submitted or 'dynamic_result' not in st.session_state:
        try:
            with st.spinner('Solving the coupled network at every timestep…'):r=calculate(c,s,revision)
            st.session_state['dynamic_result']=(signature,r)
        except (ValueError,RuntimeError,KeyError,TypeError) as exc:
            st.error(f'Run could not be evaluated: {exc}');return
    old,r=st.session_state['dynamic_result']
    if old!=signature:st.warning('Inputs changed. Run the comparison to update results. Results below are hidden to prevent mixing old outputs with new settings.');return
    f,a=r['fixed']['summary'],r['active']['summary'];b=r['benefit'];e=r['economics']
    if a['thermal_pass'] and f['thermal_pass']:st.success('Both simulations remain within the entered thermal screening limits.')
    else:st.error('At least one design exceeds a thermal screening limit. Energy savings alone do not make it an acceptable design.')
    with st.expander('Facility, flow and velocity screens'):
        st.dataframe(pd.DataFrame(r['facility_screen']).astype(str),width='stretch')
        st.caption('A maintained inlet temperature requires the facility/CDU to reject actual heat; a failed rating screen invalidates that boundary assumption.')
    left,right=st.columns([1,1.8])
    with left:
        st.subheader('The shared network')
        instant=st.slider('Inspect time · s',0.,float(r['active']['time_s'][-1]),0.,float(s['dt_s']))
        index=int(round(instant/s['dt_s']));show_figure(plotting.system_snapshot(r,index))
        st.caption('Teal = compute · purple = switch · gray = disconnected. Green circles show actuator opening. Every branch shares both headers and the pump.')
    with right:
        st.subheader('Fixed | active | difference')
        metrics=[('Peak solid temp · °C','peak_chip_C'),('Average rack flow · L/min','average_flow_LPM'),('Pump electricity · W','average_pump_W'),('Pump energy · kWh/run','pump_energy_kWh'),('Thermal margin · K','thermal_margin_K'),('Flow mismatch RMS · %','rms_flow_error')]
        rows=[dict(Measure=label,Fixed=f[key],Active=a[key],Difference=a[key]-f[key]) for label,key in metrics]
        for key in ('Fixed','Active','Difference'):rows[-1][key]*=100
        rows.extend([dict(Measure='Hardware CAPEX · $',Fixed=e['fixed_capex'],Active=e['active_capex'],Difference=e['incremental_capex']),dict(Measure='Annual operating cost · $',Fixed=e['annual_fixed_cost'],Active=e['annual_active_cost'],Difference=-e['annual_savings'])])
        st.dataframe(pd.DataFrame(rows),hide_index=True,width='stretch',column_config={key:st.column_config.NumberColumn(format='%.3f') for key in ('Fixed','Active','Difference')})
        cards=st.columns(2)
        cards[0].metric('Pump energy reduction',f"{b['pump_reduction_percent']:.1f}%" if b['pump_reduction_percent'] is not None else 'N/A')
        cards[1].metric('Net savings / rack IT power',f"{b['savings_percent_IT']:.3f}%" if b['savings_percent_IT'] is not None else 'N/A')
        st.caption('Net savings subtract valve and electronics electricity. Negative savings mean active control uses more energy. Temperature margin is relative to the assumed ceiling.')
        st.write(conclusion(r))
    timeline,energy,reliability,explore,equations=st.tabs(['Performance over time','Energy & economics','Reliability','Studies & sensitivity','Equations & sources'])
    with timeline:
        tray=st.selectbox('Tray to inspect',range(len(r['fixed']['ids'])),format_func=lambda i:r['fixed']['ids'][i])
        st.caption('Gray dashed = passive fixed hardware · teal solid = active hardware. Electrical power traces overlap because the workload is identical. Valve position is a commandable area proxy; it is not delivered flow.')
        show_figure(plotting.time_series(r,tray))
        variable=st.selectbox('Rack heat map',['chip_C','flow_LPM','flow_error','electrical_W','opening'],format_func=lambda x:{'chip_C':'Representative temperature · °C','flow_LPM':'Flow · L/min','flow_error':'Thermal-target error · %','electrical_W':'Electrical demand · W','opening':'Actuator position · fraction'}[x])
        show_figure(plotting.heatmap(r,variable))
        st.dataframe(pd.DataFrame(r['active']['per_tray']),hide_index=True,width='stretch')
        st.caption('Both panels share the same color scale. Fixed hardware has no actuator position. Disconnected branches are excluded from flow-error statistics.')
    with energy:
        st.subheader('Does the pump saving survive the added hardware?')
        st.dataframe(pd.DataFrame([e]).drop(columns=['cost_inputs']),hide_index=True,width='stretch')
        st.write(f"Net auxiliary energy saved: **{e['annual_kWh_saved']:.1f} kWh/year**. Annual savings after maintenance: **${e['annual_savings']:,.0f}**. Simple payback: **{format_payback(e['payback_years'])}**.")
        st.subheader('When does active flow control become worthwhile?')
        st.write(f"At the chosen {s['payback_horizon_years']:g}-year horizon, the affordable incremental installed cost is **${e['affordable_incremental_capex']:,.0f} total**, or **${e['affordable_installed_increment_per_branch']:,.0f} per controlled branch**.")
        st.write(f"Break-even electricity price: **${e['break_even_price']:.2f}/kWh**." if e['break_even_price'] is not None else 'No positive electricity price produces energy-only payback here because net auxiliary energy is not reduced.')
        cases=[]
        from .economics import compare
        for case in COSTS:
            case_s=dict(s,cost_case=case);case_s.pop('costs',None)
            cases.append(dict(case=case,**{k:v for k,v in compare(f,a,case_s,min(27,int(s['controlled_branches']))).items() if k!='cost_inputs'}))
        st.dataframe(pd.DataFrame(cases),hide_index=True,width='stretch')
        st.caption('Undiscounted cash flow; excludes cooling-plant energy, IT throughput value, financing, downtime and speculative reliability probabilities. Thermal failures invalidate an energy-only recommendation.')
    with reliability:
        st.write(f"Adds up to {min(27,int(s['controlled_branches']))} valves, temperature and flow sensors, rack pressure sensing, wiring and a controller.")
        st.dataframe(pd.DataFrame({'Fixed':f,'Active':a}).astype(str),width='stretch')
        st.caption('Actuations count command changes above deadband; equivalent full cycles = accumulated normalized travel / 2. Saturation is time with any valve near an end stop. Recovery means all thermal limits remain satisfied thereafter, not return to the original hydraulic state.')
        st.caption('Dripless-QD closure sets disconnected flow exactly to zero and disables its heat input. Detached stored temperatures are tracked but excluded from operating thermal screens. Reinstallation ramps connection area and tray power; its warm trapped coolant is included again. Air purge, water hammer and residual spill volumes are not modeled.')
    with explore:
        st.caption('These studies run explicitly so normal controls remain responsive. They can take several minutes. Each study preserves the selected passive hardware; no controller is assumed superior.')
        choices={'Workload scenarios':studies.scenario_study,'Controllers × pump modes':studies.strategy_study,
                 'Failure / failsafe comparison':studies.failure_study,'Sensitivity tornado':studies.sensitivity_study,
                 'Break-even operating conditions':studies.break_even_study,'Sustained thermal capacity':studies.capacity_study}
        choice=st.selectbox('Study',list(choices))
        if st.button('Run selected study'):
            try:
                with st.spinner('Running study…'):rows=choices[choice](c,s)
                st.session_state['dynamic_study']=(signature,choice,rows)
            except (ValueError,RuntimeError) as exc:st.error(str(exc))
        saved=st.session_state.get('dynamic_study')
        if saved and saved[0]==signature:
            st.subheader(saved[1]);frame=pd.DataFrame(saved[2]);st.dataframe(frame,hide_index=True,width='stretch')
            if saved[1]=='Sensitivity tornado':show_figure(plotting.tornado(saved[2]))
            st.download_button('Download study CSV',frame.to_csv(index=False),'dynamic_study.csv','text/csv')
        st.caption('Capacity study searches a 0–3× power envelope on unchanged hardware. It reports thermal-only capacity, settling, and a separate CDU rating cap. It cannot establish actual allowable NVL72 power without device limits and an HX performance map.')
    with equations:
        st.markdown(EQUATIONS)
        with st.expander('Why can active flow help — or fail to help?'):
            st.write('Lower-load trays can tolerate less flow, allowing a variable-speed pump to slow. Opening a valve changes the entire pump/network operating point; it does not create cooling capacity. At uniform maximum load, there may be little flow to redistribute. Slow valves can miss short bursts; thermal storage can make those bursts harmless even with fixed hardware. Actuator electricity and maintenance can outweigh pump savings.')
        with st.expander('Sources & Modeling Assumptions'):
            frame=pd.DataFrame(registry(s,c));st.dataframe(frame,hide_index=True,width='stretch')
            st.download_button('Download assumptions CSV',frame.to_csv(index=False),'dynamic_assumptions.csv','text/csv')
            for label,url in REFERENCES.items():st.markdown(f'- [{label}]({url})')
            st.caption('HIGH = published statement; MEDIUM = derived; LOW = engineering assumption. ASHRAE resiliency research motivates testing loss of flow; it does not supply NVL72 thermal capacitance. HVAC actuator data do not prove rack compatibility. Original baseline provenance is retained in data/sources.yaml.')
        st.json({'fixed':{k:f[k] for k in ('pressure_residual_Pa','node_mass_residual_kg_s','energy_residual_W')},'active':{k:a[k] for k in ('pressure_residual_Pa','node_mass_residual_kg_s','energy_residual_W')}})
    st.download_button('Download complete simulation JSON',dumps(r),'dynamic_comparison.json','application/json')

def format_payback(value):return 'no positive savings' if value is None else f'{value:.1f} years'

def conclusion(r):
    b=r['benefit'];e=r['economics'];a=r['active']['summary'];f=r['fixed']['summary']
    pump_phrase=f"saves {b['pump_savings_W']:.1f}" if b['pump_savings_W']>=0 else f"uses an additional {-b['pump_savings_W']:.1f}"
    net_phrase=f"saves {b['net_savings_W']:.1f}" if b['net_savings_W']>=0 else f"uses an additional {-b['net_savings_W']:.1f}"
    text=f"Active control {pump_phrase} W of pump electricity and {net_phrase} W including valve/electronics power. Peak representative temperature changes by {-b['peak_temperature_reduction_K']:+.2f} °C. Incremental CAPEX is ${e['incremental_capex']:,.0f}; simple payback is {format_payback(e['payback_years'])}. "
    if not all(x['rating_screen_pass'] for x in r['facility_screen'].values()):return text+'A reference HX capacity screen fails; the maintained-inlet assumption needs a stronger facility/CDU before drawing a design conclusion.'
    if not a['thermal_pass']:return text+'Active operation fails the entered thermal screen; do not select it based on energy savings.'
    if not f['thermal_pass']:return text+'Only active operation passes this thermal screen; investigate the thermal benefit before valuing energy savings.'
    return text+('Under these assumptions, energy savings do not justify the added hardware.' if e['annual_savings']<=0 or e['payback_years']>r['settings']['payback_horizon_years'] else 'Energy-only payback meets the entered horizon; hardware compatibility and reliability still require validation.')

EQUATIONS=r'''
### Coupled hydraulic network
$\Delta p_{pump}(Q,N)=p_0N^2-aQ^2$; $Q=\sum_i\dot m_i/\rho_{in}$.
Every open loop satisfies $\Delta p_{pump}=\Delta p_{external}+\Delta p_{supply,i}+\Delta p_{branch,i}+\Delta p_{return,i}$.
Header segment mass flow is the sum of all downstream branches; closed branches have exactly zero flow.
The original pipe, QD, cold-plate, gravity and permanent-orifice-loss equations are reused.

Valve area: $A(u)=A_{max}[f_{min}+(1-f_{min})u]$, with added body loss $K_b\rho v^2/2$.
Actuator: $du/dt=(u_{command}-u)/\tau$, bounded by stroke rate and deadband.
The effective-area model is a surrogate for a measured Cv-versus-position curve; Cd=0.62 is not a universal valve constant.

### Thermal storage and control
$P_{liquid,i}=f_{liquid,i}P_{electrical,i}$.
$C_s\,dT_s/dt=P_{liquid}-(T_s-T_f)/R$.
$C_f\,dT_f/dt=(T_s-T_f)/R-\dot m c_p(T_f-T_{in})$.
Both equations use conservative implicit Euler. $T_f$ is the well-mixed tray coolant outlet.
Representative $T_s$ is an equivalent solid/cold-plate node, not a resolved GPU junction.

$\dot m_{target}=\max(P_{liquid}/(c_p\Delta T_{target}),\dot m_{minimum})$.
Flow error is $(\dot m_i-\dot m_{target,i})/\dot m_{target,i}$; disconnected branches are excluded.
Temperature PI opens on positive $T_{measured}-T_{target}$ with anti-windup.
Feed-forward uses power-derived demand plus flow tracking; combined control adds temperature correction.

### Pumping and economics
$P_{hyd}=\Delta p\,Q$; $P_{electric}=P_{hyd}/\eta$; $E=\sum P\Delta t$.
Affinity laws set the pump curve; electricity is calculated from its actual operating point, not assumed cubic savings.
$E_{annual}=\bar P\,h_{annual}/1000$ in kWh for power in W.
Annual savings = energy cost difference − incremental maintenance.
Payback = incremental CAPEX / positive annual savings; no positive savings means no finite payback.

**Model boundary:** hydraulic density/viscosity are frozen at the full-load reference thermal state;
thermal cp is fixed at inlet temperature. This keeps the two transient designs on identical property assumptions,
but is an approximation for large temperature excursions. The original steady solver still uses temperature-dependent properties.
Inlet temperature is prescribed: no CDU/HX thermal inventory, pump heat, air cooling, transport delay, cavitation or water hammer.
No plant-wide energy savings or performance/throttling gain is inferred. A small balance residual proves numerical closure, not physical calibration.
'''
