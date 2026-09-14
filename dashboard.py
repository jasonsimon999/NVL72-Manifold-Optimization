"""Streamlit Cloud entrypoint. Local shortcut: python run_app.py."""
from pathlib import Path
import sys
PROJECT_ROOT=Path(__file__).resolve().parent
SOURCE_ROOT=str(PROJECT_ROOT/'src')
if SOURCE_ROOT not in sys.path:sys.path.insert(0,SOURCE_ROOT)

import json
import yaml
import numpy as np
import pandas as pd
import streamlit as st
from nvl72.config import load_config,portable_config
from nvl72.solver import solve
from nvl72.dashboard_support import model_fingerprint,compatible_result
from nvl72.dashboard_controls import controls
from nvl72 import dashboard_charts as charts
from nvl72.design_analysis import CHIP_DEFAULTS
from nvl72.equations import EQUATIONS
from nvl72.reporting import native,LIMITATIONS

st.set_page_config(page_title='NVL72 · Manifold lab',page_icon='💧',layout='wide')
st.markdown('''<style>
.block-container {padding-top:2rem;max-width:1450px;}
[data-testid="stMetric"] {background:var(--secondary-background-color);border-radius:12px;padding:14px 18px;}
[data-testid="stMetricLabel"] {font-size:.85rem;}
div[data-testid="stTabs"] button {font-weight:600;}
</style>''',unsafe_allow_html=True)
st.title('Manifold lab')
st.caption('NVL72 · Design, compare and understand your cooling network')
REVISION=model_fingerprint(PROJECT_ROOT)

@st.cache_data(max_entries=128,show_spinner=False)
def _calculate_current(config,model_revision):
    # Imported model code and property changes invalidate this explicit cache key.
    return solve(config)

def calculate(config):
    r=_calculate_current(config,REVISION)
    if r.get('result_schema')!=3:r=solve(config)
    return compatible_result(r)

base_config=load_config(PROJECT_ROOT/'config/baseline.yaml')
try:
    c=controls(PROJECT_ROOT,base_config)
    with st.spinner('Solving hydraulic and thermal balances…'):
        original=calculate(base_config);result=calculate(c)
except (ValueError,RuntimeError,TypeError,KeyError,AttributeError,yaml.YAMLError) as exc:
    st.error(f'This configuration could not be evaluated: {exc}')
    st.info('Check the latest change. Bores must be smaller than branch IDs; temperatures must stay within the coolant table. No previous result is being shown as current.')
    st.stop()

pins=st.session_state.setdefault('design_pins',{})
reference_name=st.selectbox('Compare current design against',['Original reference']+list(pins))
baseline=original if reference_name=='Original reference' else compatible_result(pins[reference_name])
m=result['metrics'];a=baseline['metrics'];df=pd.DataFrame(result['trays']);ref=pd.DataFrame(baseline['trays'])
st.caption(f"{m['heat_W']/1000:.2f} kW liquid load · {c['coolant']['type']} · {m['rack_flow_LPM']:.1f} L/min rack flow · {c['rack']['supply_C']:.1f}°C supply · {c['cdu']['served_racks']} rack(s) per CDU")
cols=st.columns(4)
for col,title,value,delta in [
    (cols[0],'Flow mismatch · RMS',f"{100*m['RMS_target_error']:.2f}%",f"{100*(m['RMS_target_error']-a['RMS_target_error']):+.2f} percentage points"),
    (cols[1],'Hottest tray outlet',f"{m['T_out_max_C']:.2f} °C",f"{m['T_out_max_C']-a['T_out_max_C']:+.2f} °C"),
    (cols[2],'Required system head',f"{m['system_dp_Pa']/1000:.2f} kPa",f"{(m['system_dp_Pa']-a['system_dp_Pa'])/1000:+.2f} kPa"),
    (cols[3],'Estimated pump electricity',f"{m['pump_electrical_W']:.1f} W",f"{m['pump_electrical_W']-a['pump_electrical_W']:+.1f} W")]:
    col.metric(title,value,delta,delta_color='inverse')
st.caption('Deltas compare with the selected reference. Smaller flow mismatch is better; zero means target distribution. Pump electricity excludes CDU overhead.')
failed=[dict(Check=k,Enforced=v.get('enforced',True),Shortfall=-v['margin'],Units=v['units'],Basis=v.get('basis','Historical policy')) for k,v in result['constraints'].items() if not v['pass']]
hard=sum(x['Enforced'] for x in failed);advisory=len(failed)-hard
if hard:st.error(f'Converged · {hard} enforced requirement(s) fail · {advisory} advisory screen(s) need review')
elif advisory:st.warning(f'Converged · enforced requirements pass · {advisory} advisory screen(s) need review')
else:st.success('Converged · enforced requirements and advisory screens pass')
if failed:
    with st.expander('Explain the shortfalls',expanded=bool(hard)):st.dataframe(pd.DataFrame(failed),hide_index=True,width='stretch')
st.info(result['qualification'])
if any(c['branches'][kind].get('qdc_model')=='fixed' or 'qdc_curve' in c['branches'][kind] for kind in ('compute','switch')):
    st.caption('Fixed/measured QD loss mode: changing QD ID changes reported bore velocity, not the fixed coefficient or measured curve.')

overview,hydraulics,thermal,compare,details=st.tabs(['Flow & cooling','Hydraulics & bores','Chip temperatures','Compare & explore','Equations & data'])
with overview:
    filter_kind=st.radio('Trays to show',['All trays','Compute trays','Switch trays'],horizontal=True)
    visible=df if filter_kind=='All trays' else df[df.tray_type==('compute' if filter_kind=='Compute trays' else 'switch')]
    st.subheader('Target versus actual flow')
    st.caption('Grey = target · teal = actual. Side-by-side bars follow rack order; hover for exact values. Targets use the selected heat-proportional or equal-flow objective.')
    st.vega_lite_chart(spec=charts.flow_comparison(visible),width='stretch')
    with st.expander('Which trays receive too little or too much?'):
        st.vega_lite_chart(spec=charts.flow_error(visible),width='stretch')
        st.caption('Orange below zero = below target; teal above zero = above target. Flow error alone is not a thermal-limit failure.')
    st.subheader('Coolant outlet temperature')
    st.vega_lite_chart(spec=charts.temperature(visible,ref,c['constraints']['branch_outlet_max_C']),width='stretch')
    st.caption('Teal = current · dashed grey = reference · orange = configured outlet ceiling. The temperature axis is expanded to show differences.')
    with st.expander('Rack map'):
        from nvl72.plotting import rack_schematic
        import matplotlib.pyplot as plt
        metric=st.selectbox('Schematic color',['T_out_C','actual_flow_LPM','heat_load_W','branch_dP_kPa','flow_error_percent'])
        fig=rack_schematic(result,metric);st.pyplot(fig);plt.close(fig)
        st.caption('Supply left, return right; C = compute, S = switch. Conceptual schematic, not CAD.')
with hydraulics:
    st.subheader('Where the pump pressure goes')
    st.vega_lite_chart(spec=charts.budget(result['pressure_budget_Pa']),width='stretch')
    st.caption('Flow-weighted complete-path contributions. Parallel branches are not summed; signed buoyancy may reduce head.')
    st.subheader('Branch, QD and orifice dimensions')
    fields=['tray_id','branch_ID_mm','QD_ID_mm','orifice_diameter_mm','actual_flow_LPM','branch_velocity_m_s','QD_velocity_m_s','qdc_dP_kPa','orifice_dP_kPa','QD_loss_model']
    st.dataframe(df[[x for x in fields if x in df]],hide_index=True,width='stretch')
    st.caption('All diameters are bores in mm. QD loss covers the complete assumed QD path. Blank orifice bore means no plate.')
    if result.get('fixed_orifice_config'):
        with st.expander('Automatic sizing details'):
            st.dataframe(df[['tray_id','balancing_restriction_K','orifice_diameter_mm','orifice_Cd','orifice_reference_density_kg_m3','orifice_dP_kPa']],hide_index=True,width='stretch')
        st.download_button('Download fixed-orifice design YAML',yaml.safe_dump(portable_config(result['fixed_orifice_config']),sort_keys=False),'fixed_orifice_design.yaml','text/yaml')
        st.caption('Automatic bores are redesigned for this operating point. Export fixed bores before testing unchanged hardware elsewhere.')
    with st.expander('Header pressures & pump curve'):
        st.vega_lite_chart(spec=charts.header_pressure(df),width='stretch')
        from nvl72.cdu import pump_head
        from nvl72.units import lpm_to_m3s
        import matplotlib.pyplot as plt
        flow_axis=np.linspace(0,max(180,m['rack_flow_LPM']*1.2),80)
        fig,ax=plt.subplots(figsize=(9,3))
        ax.plot(flow_axis,pump_head(lpm_to_m3s(flow_axis*c['cdu']['served_racks']),c['cdu'])/1000,color=charts.TEAL,label='Assumed available pump head')
        ax.scatter([m['rack_flow_LPM']],[m['system_dp_Pa']/1000],color=charts.ORANGE,label='Required duty',zorder=3)
        ax.set(xlabel='Per-rack flow [L/min]',ylabel='External head [kPa]',ylim=(0,None));ax.grid(alpha=.15);ax.legend()
        st.pyplot(fig);plt.close(fig)
        st.caption('Duty above this curve is unsupported by the assumed pump. A manufacturer curve is needed for qualification.')
    with st.expander('Facility cooling requirements'):
        f=result['facility'];fc=st.columns(3)
        fc[0].metric('Aggregate cooling duty',f"{f['aggregate_heat_W']/1000:.2f} kW")
        fc[1].metric('Facility return',f"{f['FWS_return_C']:.2f} °C")
        fc[2].metric('Required HX conductance','Not attainable' if f['required_UA_W_K'] is None else f"{f['required_UA_W_K']/1000:.2f} kW/K")
        st.write('Minimum calorimetric facility flow: '+('not attainable' if f['required_flow_LPM'] is None else f"{f['required_flow_LPM']:.1f} L/min"))
        st.caption('Flow covers all racks on this CDU. UA assumes counterflow. Primary pressure losses, control limits and unmodeled pump heat need vendor/site data.')
        st.json(f,expanded=False)
with thermal:
    st.subheader('Estimated chip temperatures')
    chips=pd.DataFrame(result['chip_estimates'])
    chip_kind=st.selectbox('Chip temperature plot component',list(CHIP_DEFAULTS))
    st.vega_lite_chart(spec=charts.chip_band(chips[chips.component==chip_kind]),width='stretch')
    st.caption('Shaded teal = assumed interval · teal line = upper estimate · dashed orange = target. Bounds are not statistical confidence or a verified throttling threshold.')
    with st.expander('All chip estimates'):st.dataframe(chips,hide_index=True,width='stretch')
    st.download_button('Download chip CSV',chips.to_csv(index=False),'chip_estimates.csv','text/csv')
with compare:
    from nvl72.dashboard_explore import explore
    explore(c,result,baseline,pins,calculate,REVISION)
with details:
    st.subheader('Equations and derivations')
    for title,formula,description in EQUATIONS:
        with st.expander(title):st.latex(formula);st.write(description)
    with st.expander('Current numerical derivation'):
        t=result['trays'][0]
        st.write(f"Rack heat = sum of tray loads = {m['heat_W']:.1f} W. Total mass flow = {sum(x['mass_flow_kg_s'] for x in result['trays']):.5f} kg/s.")
        st.write(f"{t['tray_id']}: {t['heat_load_W']:.1f} W / {t['mass_flow_kg_s']:.6f} kg/s = {t['heat_load_W']/t['mass_flow_kg_s']:.1f} J/kg enthalpy rise → {t['T_out_C']:.3f}°C outlet.")
        st.write(f"Pump estimate = {m['system_dp_Pa']:.1f} Pa × {m['rack_flow_LPM']/60000:.6f} m³/s ÷ {c['cdu']['efficiency']:.3f} = {m['pump_electrical_W']:.2f} W.")
    with st.expander('All constraint margins & numerical checks'):
        st.dataframe(pd.DataFrame(result['constraints']).T,width='stretch');st.json(result['validation'])
    with st.expander('Full tray results'):st.dataframe(df,hide_index=True,width='stretch')
    with st.expander('Model audit and evidence'):
        path=PROJECT_ROOT/'docs/MODEL_AUDIT.md'
        if path.exists():st.markdown(path.read_text())
    with st.expander('Model limits'):st.write(LIMITATIONS)
    with st.expander('Resolved configuration'):st.json(portable_config(result['config']),expanded=False)
    st.download_button('Download tray CSV',df.to_csv(index=False),'tray_results.csv','text/csv')
    st.download_button('Download complete result and configuration',json.dumps(native(result),indent=2,allow_nan=False),'design_result.json','application/json')
    st.download_button('Download current design YAML',yaml.safe_dump(portable_config(result['config']),sort_keys=False),'current_design.yaml','text/yaml')
    if st.session_state.get('show_saved'):
        path=PROJECT_ROOT/'results/optimized.json'
        if path.exists():st.subheader('Saved optimized candidate');st.json(json.loads(path.read_text())['metrics'])
        else:st.info('Run the optimization study to create results/optimized.json.')
st.caption('Engineering screening with unmeasured inputs. A numerical pass is not hardware qualification. Model revision '+REVISION[:8])
