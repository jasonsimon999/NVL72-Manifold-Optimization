"""Streamlit Cloud entrypoint. Local shortcut: python run_app.py."""
from pathlib import Path
import sys

# Cloud installs requirements.txt, not necessarily this src-layout package.
# Resolve from this file so startup also works outside the repository directory.
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from copy import deepcopy
import pandas as pd
import numpy as np
import streamlit as st
from nvl72.config import load_config
from nvl72.solver import solve
from nvl72.plotting import rack_schematic
from nvl72.cdu import pump_head
from nvl72.units import lpm_to_m3s
from nvl72.design_analysis import CHIP_DEFAULTS, design_summary
from nvl72.equations import EQUATIONS
from nvl72.rack import tray_data

st.set_page_config(page_title='NVL72 manifold laboratory',layout='wide')
st.title('NVL72 manifold laboratory')
st.caption('Public-data-grounded engineering model · assumed component hydraulics · not proprietary rack CAD')
@st.cache_data
def calculate(config): return solve(config)
base_config=load_config(PROJECT_ROOT / 'config/baseline.yaml')
with st.sidebar:
    st.header('Operating condition')
    flow=st.slider('Rack flow [L/min]',90.,130.,120.,1.)
    supply=st.slider('TCS supply [°C]',25.,45.,40.,.5)
    coolant=st.selectbox('Coolant',['PG25','water','EG50'],help='EG50 = 50% ethylene glycol by volume; Dow SR-1 property proxy, not approved rack coolant.')
    compute=st.slider('Compute load fraction',0.05,1.,1.,.05)
    switch=st.slider('Switch load fraction',.05,1.2,1.,.05)
    cdu=st.selectbox('CDU',['in_rack','in_row'])
    fw_supply=st.number_input('Facility water supply [°C]',5.,60.,36.,.5)
    fw_flow=st.number_input('Facility water flow, entire CDU [L/min]',10.,3000.,150. if cdu=='in_rack' else 1200.,10.)
    fw_rise=st.number_input('Facility design temperature rise [K]',1.,30.,12.,.5)
    fw_pinch=st.number_input('Minimum HX hot-end pinch [K]',0.,15.,0.,.5)
    st.header('Manifold and balancing')
    diameter=st.slider('Main header ID [mm]',25.,50.,38.,.5)
    taper=st.slider('Tip / main diameter ratio',.6,1.,1.,.01)
    kc=st.number_input('Compute restriction [million Pa/(kg/s)²]',0.,200.,0.,.1)
    ks=st.number_input('Switch restriction [million Pa/(kg/s)²]',0.,200.,0.,1.)
    gravity=st.checkbox('Include gravity',True)
    operating=st.selectbox('Operating mode',['fixed_flow','pump'])
    metric=st.selectbox('Schematic color',['T_out_C','actual_flow_LPM','heat_load_W','branch_dP_kPa','flow_error_percent'])
    if st.button('Show saved optimized result'):
        st.session_state['show_saved']=True
c=load_config(PROJECT_ROOT / 'config/inrow.yaml') if cdu=='in_row' else deepcopy(base_config)
c['rack'].update(flow_LPM=flow,supply_C=supply,gravity_enabled=gravity,operating_mode=operating)
c['coolant']['type']=coolant;c['facility'].update(supply_C=fw_supply,flow_LPM=fw_flow,design_deltaT_K=fw_rise,minimum_hot_pinch_K=fw_pinch)
c['power'].update(compute_fraction=compute,switch_fraction=switch)
c['geometry']['supply'].update(profile='power' if taper<1 else 'constant',inlet_m=diameter/1000,outlet_m=diameter*taper/1000)
c['geometry']['return'].update(profile='power' if taper<1 else 'constant',inlet_m=diameter*taper/1000,outlet_m=diameter/1000)
c['branches']['compute']['restriction_K']=kc*1e6;c['branches']['switch']['restriction_K']=ks*1e6
with st.expander('Individual tray orifices — edit bore and discharge coefficient'):
    st.caption('Enable any tray independently. Bore must be smaller than its branch ID. Orifices add to the class restriction controls; Cd and the thin-plate loss approximation need measured calibration.')
    ids,kinds,_,branches=tray_data(c)
    edited=st.data_editor(pd.DataFrame([dict(tray_id=i,enabled=False,bore_mm=4. if kind=='compute' else 2.5,Cd=.62,branch_ID_mm=b['diameter_m']*1000) for i,kind,b in zip(ids,kinds,branches)]),
        hide_index=True,disabled=['tray_id','branch_ID_mm'],key='orifice_editor',
        column_config={'bore_mm':st.column_config.NumberColumn(min_value=.1,step=.1),'Cd':st.column_config.NumberColumn(min_value=.01,max_value=1.,step=.01)})
    for row in edited.to_dict('records'):
        if row['enabled']: c['branches']['overrides'].setdefault(row['tray_id'],{}).update(orifice_diameter_m=row['bore_mm']/1000,orifice_Cd=row['Cd'])
with st.expander('Chip thermal assumptions and performance targets'):
    st.caption('80°C is an editable engineering target, not an NVIDIA optimal-performance specification. Enter measured junction-to-coolant resistances and installed thermal limits to improve this screen. Zero manufacturer limit means unknown.')
    c['chip_temperature']={}
    for kind,(low,high) in CHIP_DEFAULTS.items():
        cols=st.columns(4)
        lo=cols[0].number_input(f'{kind} R low [K/W]',0.,1.,low,.001,format='%.3f')
        hi=cols[1].number_input(f'{kind} R high [K/W]',0.,1.,high,.001,format='%.3f')
        target=cols[2].number_input(f'{kind} target ceiling [°C]',20.,150.,80.,1.)
        limit=cols[3].number_input(f'{kind} manufacturer limit [°C; 0 unknown]',0.,150.,0.,1.)
        c['chip_temperature'][kind]=dict(resistance_range_K_W=[lo,hi],target_max_C=target,manufacturer_limit_C=limit or None)
try:
    baseline=calculate(base_config);result=calculate(c)
except (ValueError,RuntimeError) as exc:
    st.error(str(exc));st.stop()
m=result['metrics'];a=baseline['metrics']
columns=st.columns(4)
for col,title,key,format_str,unit in [(columns[0],'Maximum outlet','T_out_max_C','.2f','°C'),(columns[1],'RMS target error','RMS_target_error','.4f',''),(columns[2],'System pressure','system_dp_Pa','.0f','Pa'),(columns[3],'Pump electrical','pump_electrical_W','.1f','W')]:
    col.metric(title,f'{m[key]:{format_str}} {unit}',f'{m[key]-a[key]:+.{2}f} vs reference',delta_color='inverse')
if result['feasible']:st.success('All configured nominal constraints pass')
else:st.error('Constraint violation — this candidate is not acceptable under the selected envelope')
st.caption('Reference stays at 115.56 kW, PG25, 40°C, 120 L/min with constant headers. Facility water is controlled independently. A nominal pass is an engineering screen, not hardware qualification.')
st.info(result['qualification'])
df=pd.DataFrame(result['trays']);ref=pd.DataFrame(baseline['trays'])
left,right=st.columns([1,2])
with left:
    st.pyplot(rack_schematic(result,metric))
with right:
    st.subheader('Target and actual tray flow')
    st.bar_chart(df.set_index('tray_id')[['target_flow_LPM','actual_flow_LPM']])
    st.subheader('Tray outlet temperatures [°C]')
    temp=pd.DataFrame({'Candidate':df.T_out_C.to_numpy(),'Reference':ref.T_out_C.to_numpy()},index=df.tray_id)
    st.line_chart(temp)
pressure_tab,budget_tab,constraint_tab,pump_tab=st.tabs(['Header pressure','Pressure budget','Constraints and balances','Pump and facility'])
with pressure_tab:
    st.line_chart(df.set_index('elevation_m')[['supply_pressure_kPa','return_pressure_kPa']]);st.caption('kPa relative to CDU return; height in m')
with budget_tab:
    st.bar_chart(pd.Series(result['pressure_budget_Pa'],name='Equivalent head [Pa]'))
    st.caption('Flow-weighted complete path contributions. Parallel branch losses are not summed.')
with constraint_tab:
    st.dataframe(pd.DataFrame(result['constraints']).T,width='stretch')
    st.json(result['validation'])
with pump_tab:
    flow_axis=np.linspace(0,180,60)
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(7,3))
    ax.plot(flow_axis,pump_head(lpm_to_m3s(flow_axis*c['cdu']['served_racks']),c['cdu'])/1000,label='Assumed available pump head')
    ax.scatter([m['rack_flow_LPM']],[m['system_dp_Pa']/1000],color='red',label='Required duty')
    ax.set(xlabel='Per-rack flow [L/min]',ylabel='External head [kPa]',ylim=(0,None));ax.legend()
    st.pyplot(fig);plt.close(fig)
    st.write(f"Required duty: {m['rack_flow_LPM']:.2f} L/min at {m['system_dp_Pa']/1000:.2f} kPa")
    st.json(result['facility'])
    f=result['facility']
    st.write(f"Facility cooling duty: {f['aggregate_heat_W']/1000:.2f} kW across {c['cdu']['served_racks']} rack(s). Maximum supply: {f['maximum_FWS_supply_C']:.1f}°C. Actual return: {f['FWS_return_C']:.2f}°C.")
    if f['required_flow_LPM'] is None: st.warning('No finite facility flow meets the selected temperature/pinch limits.')
    else: st.write(f"Minimum facility flow for the selected rise, return ceiling and pinch: {f['required_flow_LPM']:.1f} L/min.")
    st.caption('Required UA assumes counterflow. Facility cooling duty excludes unmodeled pump heat. Facility pump head cannot be sized without its pipe/equipment curves.')
st.subheader('Chip temperature estimates')
chips=pd.DataFrame(result['chip_estimates'])
st.dataframe(chips,width='stretch',hide_index=True)
chip_kind=st.selectbox('Chip temperature plot component',list(CHIP_DEFAULTS))
st.line_chart(chips[ chips.component==chip_kind ].set_index('tray_id')[['junction_low_C','junction_high_C','target_max_C']])
st.caption('Lines show the selected component’s temperature bounds and target in each applicable tray. Bounds reflect assumed thermal resistance, not statistical confidence. Passing an assumed target does not establish absence of throttling. NVIDIA GPU limits: nvidia-smi -q -d TEMPERATURE; Grace CPU limits: platform thermal-zone trip points.')
st.download_button('Download chip CSV',chips.to_csv(index=False),'chip_estimates.csv','text/csv')
st.subheader('Design analysis summary')
summary=pd.DataFrame(design_summary({'Original reference':baseline,'Current candidate':result}))
st.dataframe(summary,width='stretch',hide_index=True)
st.download_button('Download design summary CSV',summary.to_csv(index=False),'design_summary.csv','text/csv')
st.caption('Compare scores at equal load, coolant, supply, flow and objective weights. Reject failed constraints before ranking; a low score cannot override a failure. Header volume represents space/material tendency, not manufactured cost.')
with st.expander('Compare water, PG25 and EG50 using this design'):
    if st.button('Run coolant comparison'):
        cases={}
        for fluid in ['water','PG25','EG50']:
            case=deepcopy(c);case['coolant']['type']=fluid
            try: cases[fluid]=calculate(case)
            except (ValueError,RuntimeError) as exc: st.warning(f'{fluid}: {exc}')
        st.session_state['fluid_cases']=(deepcopy(c),cases)
    saved=st.session_state.get('fluid_cases')
    if saved and saved[0]==c:
        comparison=pd.DataFrame(design_summary(saved[1]))
        st.dataframe(comparison,width='stretch',hide_index=True)
        st.download_button('Download coolant comparison CSV',comparison.to_csv(index=False),'coolant_comparison.csv','text/csv')
    elif saved: st.caption('Controls changed; rerun the comparison to update its results.')
st.subheader('Equations and derivations')
for title,formula,description in EQUATIONS:
    with st.expander(title):
        st.latex(formula);st.write(description)
with st.expander('Current numerical derivation and objective settings'):
    t=result['trays'][0]
    st.write(f"Rack heat = sum of 27 tray loads = {m['heat_W']:.1f} W. Total mass flow = sum of branch flows = {sum(x['mass_flow_kg_s'] for x in result['trays']):.5f} kg/s.")
    st.write(f"{t['tray_id']}: {t['heat_load_W']:.1f} W / {t['mass_flow_kg_s']:.6f} kg/s = {t['heat_load_W']/t['mass_flow_kg_s']:.1f} J/kg enthalpy rise → {t['T_out_C']:.3f}°C outlet.")
    st.write(f"Pump electricity = {m['system_dp_Pa']:.1f} Pa × {m['rack_flow_LPM']/60000:.6f} m³/s / {c['cdu']['efficiency']:.3f} = {m['pump_electrical_W']:.2f} W.")
    st.json(c['optimization'])
st.caption('Sources: [Dow SR-1 fluid properties](https://users.obs.carnegiescience.edu/crane/pfs/man/Misc/Dowtherm-SR-1.pdf) · [NVIDIA thermal-limit guidance](https://docs.nvidia.com/dccpu/grace-perf-tuning-guide/power-thermals.html) · [Orifice pressure-loss research](https://www.sciencedirect.com/science/article/abs/pii/S0263224125000466). Provenance and assumptions are recorded in agent.md.')
st.subheader('Tray results')
st.dataframe(df,width='stretch',hide_index=True)
st.download_button('Download tray CSV',df.to_csv(index=False),'tray_results.csv','text/csv')
import json
from nvl72.reporting import native
st.download_button('Download complete result and configuration',json.dumps(native(result),indent=2,allow_nan=False),'design_result.json','application/json')
if st.session_state.get('show_saved'):
    import json
    from pathlib import Path
    path=PROJECT_ROOT / 'results/optimized.json'
    if path.exists():st.subheader('Saved optimized candidate');st.json(json.loads(path.read_text())['metrics'])
    else:st.info('Run the optimization study to create results/optimized.json.')
with st.expander('Model limits'):
    from nvl72.reporting import LIMITATIONS
    st.write(LIMITATIONS)
