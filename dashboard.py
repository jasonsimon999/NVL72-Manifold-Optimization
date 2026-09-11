"""Run: streamlit run dashboard.py (after editable package install)."""
from copy import deepcopy
import pandas as pd
import numpy as np
import streamlit as st
from nvl72.config import load_config
from nvl72.solver import solve
from nvl72.plotting import rack_schematic
from nvl72.cdu import pump_head
from nvl72.units import lpm_to_m3s

st.set_page_config(page_title='NVL72 manifold laboratory',layout='wide')
st.title('NVL72 manifold laboratory')
st.caption('Public-data-grounded engineering model · assumed component hydraulics · not proprietary rack CAD')
@st.cache_data
def calculate(config): return solve(config)
base_config=load_config()
with st.sidebar:
    st.header('Operating condition')
    flow=st.slider('Rack flow [L/min]',90.,130.,120.,1.)
    supply=st.slider('TCS supply [°C]',25.,45.,40.,.5)
    coolant=st.selectbox('Coolant',['PG25','water'])
    compute=st.slider('Compute load fraction',0.05,1.,1.,.05)
    switch=st.slider('Switch load fraction',.05,1.2,1.,.05)
    cdu=st.selectbox('CDU',['in_rack','in_row'])
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
c=load_config('config/inrow.yaml') if cdu=='in_row' else deepcopy(base_config)
c['rack'].update(flow_LPM=flow,supply_C=supply,gravity_enabled=gravity,operating_mode=operating)
c['coolant']['type']=coolant;c['facility']['supply_C']=supply-c['cdu']['approach_K']
c['power'].update(compute_fraction=compute,switch_fraction=switch)
c['geometry']['supply'].update(profile='power' if taper<1 else 'constant',inlet_m=diameter/1000,outlet_m=diameter*taper/1000)
c['geometry']['return'].update(profile='power' if taper<1 else 'constant',inlet_m=diameter*taper/1000,outlet_m=diameter/1000)
c['branches']['compute']['restriction_K']=kc*1e6;c['branches']['switch']['restriction_K']=ks*1e6
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
st.caption('Reference comparison stays at the original 115.56 kW, PG25, 40°C, 120 L/min constant-header case. FWS supply tracks TCS by 4 K in these controls.')
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
st.subheader('Tray results')
st.dataframe(df,width='stretch',hide_index=True)
st.download_button('Download tray CSV',df.to_csv(index=False),'tray_results.csv','text/csv')
if st.session_state.get('show_saved'):
    import json
    from pathlib import Path
    path=Path('results/optimized.json')
    if path.exists():st.subheader('Saved optimized candidate');st.json(json.loads(path.read_text())['metrics'])
    else:st.info('Run the optimization study to create results/optimized.json.')
with st.expander('Model limits'):
    from nvl72.reporting import LIMITATIONS
    st.write(LIMITATIONS)
