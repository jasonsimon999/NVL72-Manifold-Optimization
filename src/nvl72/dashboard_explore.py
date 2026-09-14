"""Compare and explore tools, separate from primary controls and charts."""
from copy import deepcopy
import numpy as np
import pandas as pd
import streamlit as st
import yaml
from .config import portable_config
from .design_analysis import design_summary
from .dashboard_support import compatible_result
from .experiments import PARAMETERS,sweep_design
from . import dashboard_charts as charts

def explore(c,result,baseline,pins,calculate,revision):
    st.subheader('Save designs for comparison')
    name=st.text_input('Design name',value=f'Design {len(pins)+1}',max_chars=60).strip()
    if st.button('Pin current design'):
        if not name or name=='Original reference':st.warning('Choose a nonempty name other than Original reference.')
        elif name in pins:st.warning('That name is already pinned; choose a new name.')
        elif len(pins)>=6:st.warning('Six designs are pinned. Clear the comparison to start a new set.')
        else:pins[name]=deepcopy(result);st.rerun()
    if pins and st.button('Clear pinned designs'):st.session_state['design_pins']={};st.rerun()
    named={'Reference':baseline,'Current':result,**{k:compatible_result(v) for k,v in pins.items()}}
    summary=pd.DataFrame(design_summary(named))
    fields=['design','flow_LPM','RMS_flow_error','outlet_max_C','pressure_kPa','pump_W','enforced_requirements_pass','all_screens_pass']
    st.dataframe(summary[fields],hide_index=True,width='stretch')
    st.caption('RMS_flow_error is a fraction (0.01 = 1%). Compare at matched load, fluid, supply, flow and weights. Pins last for this session; download designs to retain them.')
    with st.expander('Complete design analysis table'):st.dataframe(summary,hide_index=True,width='stretch')
    st.download_button('Download design summary CSV',summary.to_csv(index=False),'design_summary.csv','text/csv')
    with st.expander('Find a balanced candidate'):
        st.caption('Calculates per-tray added restrictions for exact target flow at current geometry and solved rack flow. Replaces existing balancing plates in a separate candidate. Review pump cost and constraints.')
        if st.button('Calculate exact flow balance'):
            from .optimize import balance_locations
            proposal=deepcopy(c);proposal['balancing_mode']='auto_equivalent'
            proposal['rack'].update(operating_mode='fixed_flow',flow_LPM=result['metrics']['rack_flow_LPM'])
            for kind in ('compute','switch'):proposal['branches'][kind]['orifice_diameter_m']=None
            for override in proposal['branches']['overrides'].values():override['orifice_diameter_m']=None
            try:st.session_state['balanced_candidate']=(revision,deepcopy(c),compatible_result(balance_locations(proposal)))
            except (ValueError,RuntimeError) as exc:st.warning(str(exc))
        saved=st.session_state.get('balanced_candidate')
        if saved and saved[:2]==(revision,c):
            br=saved[2];st.dataframe(pd.DataFrame(design_summary({'Balanced proposal':br})),hide_index=True)
            st.download_button('Download balanced fixed-bore candidate',yaml.safe_dump(portable_config(br['fixed_orifice_config']),sort_keys=False),'balanced_design.yaml','text/yaml')
        elif saved:st.caption('Inputs changed; recalculate the proposal.')
    with st.expander('Sweep one parameter'):
        parameter=st.selectbox('Parameter to sweep',list(PARAMETERS))
        default_low,default_high=(90.,130.) if parameter.startswith('Rack') else ((25.,50.) if parameter.startswith('Header') else ((1.5,4.) if 'orifice' in parameter else (4.,10.)))
        lo=st.number_input('Sweep start',min_value=.1,value=default_low,step=.5,key='lo_'+parameter)
        hi=st.number_input('Sweep end',min_value=.1,value=default_high,step=.5,key='hi_'+parameter)
        count=st.slider('Samples',3,15,7)
        st.caption('Uses fixed physical bores. Header sweeps use constant headers; class-bore sweeps replace that class’s individual bores. Flow sweeps prescribe flow even if starting from pump mode. Failed points stay visible.')
        signature=(revision,c,parameter,lo,hi,count)
        if st.button('Run parameter sweep'):
            if hi<=lo:st.warning('Sweep end must exceed start.')
            else:
                try:st.session_state['sweep_result']=(deepcopy(signature),sweep_design(result,parameter,np.linspace(lo,hi,count)))
                except (ValueError,RuntimeError) as exc:st.warning(str(exc))
        swept=st.session_state.get('sweep_result')
        if swept and swept[0]==signature:
            frame=pd.DataFrame(swept[1]);st.dataframe(frame,hide_index=True,width='stretch')
            measure=st.selectbox('Sweep output',['Flow error [% RMS]','Max outlet [°C]','Pump [W]','Head [kPa]'])
            if measure in frame:
                spec=charts.chart(frame.dropna(subset=[measure]),mark={'type':'point','filled':True,'size':90},encoding={'x':{'field':'Value','type':'quantitative','title':parameter,'scale':{'zero':False}},'y':{'field':measure,'type':'quantitative','scale':{'zero':False}},'color':{'field':'Enforced pass','type':'nominal','scale':{'domain':[True,False],'range':[charts.TEAL,charts.ORANGE]}},'tooltip':[{'field':'Value'},{'field':measure},{'field':'Issues'}]})
                st.vega_lite_chart(spec=spec,width='stretch')
            st.download_button('Download sweep CSV',frame.to_csv(index=False),'parameter_sweep.csv','text/csv')
        elif swept:st.caption('Inputs changed; rerun the sweep.')
    with st.expander('Compare water, PG25 and EG50 using this design'):
        st.caption('Automatic designs use exported fixed bores so fluids are compared on unchanged hardware.')
        if st.button('Run coolant comparison'):
            cases={}
            for fluid in ['water','PG25','EG50']:
                case=deepcopy(result.get('fixed_orifice_config') or c);case['coolant']['type']=fluid
                try:cases[fluid]=calculate(case)
                except (ValueError,RuntimeError) as exc:st.warning(f'{fluid}: {exc}')
            st.session_state['fluid_cases']=(deepcopy(c),cases);st.session_state['fluid_revision']=revision
        saved=st.session_state.get('fluid_cases')
        if saved and saved[0]==c and st.session_state.get('fluid_revision')==revision:
            frame=pd.DataFrame(design_summary({k:compatible_result(v) for k,v in saved[1].items()}))
            st.dataframe(frame,hide_index=True,width='stretch')
            st.download_button('Download coolant comparison CSV',frame.to_csv(index=False),'coolant_comparison.csv','text/csv')
        elif saved:st.caption('Controls/model changed; rerun the comparison.')
