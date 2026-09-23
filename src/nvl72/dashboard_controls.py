"""Progressive disclosure: design knobs first, calibration and site data folded away."""
from copy import deepcopy
import pandas as pd
import streamlit as st
import yaml
from .config import load_config,portable_config
from .design_analysis import CHIP_DEFAULTS
from .dashboard_support import apply_yaml_overrides

def controls(root,base):
    with st.sidebar:
        st.markdown('### Design controls')
        st.caption('Start with flow and pipe size. Results update automatically.')
        flow=st.slider('Rack flow [L/min]',20.,300.,120.,1.,key='rack_flow',help='Total coolant volume through the rack each minute. More flow usually lowers coolant temperature rise but increases pumping effort. Pump mode solves its own flow.')
        diameter=st.slider('Main header ID [mm]',15.,65.,38.,.5,key='header_id',help='Main supply and return internal diameter, independent of tray QDs.')
        with st.expander('Orifices & tray connections'):
            balancing=st.selectbox('Balancing representation',['Automatic equivalent orifices','Manual orifice bores','Resistance coefficients'],key='balancing')
            if balancing=='Manual orifice bores':
                st.caption('Enter a physical hole size for each tray type. Smaller holes add more resistance. Enter 0 for no plate.')
            elif balancing=='Automatic equivalent orifices':
                st.caption('Choose added resistance below; the model calculates an equivalent hole size. See Hydraulics & bores for the resulting dimensions.')
            else:
                st.caption('Study added resistance directly, without assigning a physical orifice bore.')
            with st.container(border=True):
                st.markdown('**Tray geometry**')
                st.caption('ID = internal diameter. Branch = tray hose; QD = quick disconnect; orifice = added balancing hole.')
                left,right=st.columns(2)
                values={}
                for kind,col,dflt in [('compute',left,8.),('switch',right,6.)]:
                    with col:
                        st.markdown(f'**{kind.title()}**')
                        bd=st.number_input(f'{kind.title()} branch ID [mm]',min_value=1.,max_value=30.,value=dflt,step=.25,key=f'{kind}_branch',help='Inside diameter of this tray type’s tubing. A larger ID usually reduces tubing pressure loss; it does not change the QD or cold plate.')
                        qd=st.number_input(f'{kind.title()} QD ID [mm]',min_value=1.,max_value=30.,value=dflt,step=.25,key=f'{kind}_qd',help='Flow bore, not AN size. Diameter alone uses the assumed QD scaling below.')
                        if balancing=='Manual orifice bores':
                            bore=st.number_input(f'{kind.title()} orifice bore [mm; 0 none]',min_value=0.,max_value=30.,value=0.,step=.1,key=f'{kind}_bore',help='Applies to every tray of this class. Must be smaller than branch ID.')
                            kh=0.
                        else:
                            bore=0.
                            kh=st.number_input(f'{kind.title()} restriction [million Pa/(kg/s)²]',min_value=0.,max_value=500.,value=0.,step=1.,key=f'{kind}_restriction',help='Added resistance to flow. Larger values restrict this tray type more and give smaller equivalent bores in Automatic mode.')*1e6
                        values[kind]=(bd,qd,bore,kh)
                st.caption('Automatic: resistance → equivalent bore. Manual: enter the bore directly. Zero means no added plate.')
        with st.expander('Coolant & heat load'):
            st.caption('Set the test conditions. TCS is the rack coolant loop; load fraction scales the modeled chip heat (1.0 = full reference load).')
            supply=st.slider('TCS supply [°C]',10.,60.,40.,.5,key='supply')
            coolant=st.selectbox('Coolant',['PG25','water','EG50','PG25_Dow2023'],key='coolant',help='PG25 is the legacy assumption profile. PG25_Dow2023 is a versioned manufacturer table. EG50 is not hardware-qualified.')
            compute=st.slider('Compute load fraction',.05,1.2,1.,.05)
            switch=st.slider('Switch load fraction',.05,1.2,1.,.05)
            operating=st.selectbox('Operating mode',['fixed_flow','pump'],help='Pump mode finds flow on an assumed curve; the flow slider is then an initial setting, not a prescribed output.')
            if operating=='pump':st.info('Pump mode: the displayed result is the flow the assumed pump can deliver. The rack-flow slider does not prescribe that result.')
        with st.expander('Facility & CDU'):
            st.caption('The CDU transfers rack heat to facility water. These settings describe the separate building-water loop and the selected cooling unit.')
            cdu=st.selectbox('CDU',['in_rack','in_row'],key='cdu')
            c=load_config(root/'config/inrow.yaml') if cdu=='in_row' else deepcopy(base)
            racks=st.number_input('Racks served by CDU',1,32,1 if cdu=='in_rack' else 8,1)
            fw_supply=st.number_input('Facility water supply [°C]',5.,60.,36.,.5)
            fw_flow=st.number_input('Facility water flow, entire CDU [L/min]',min_value=10.,value=150. if cdu=='in_rack' else 1200.,step=10.)
            fw_rise=st.number_input('Facility design temperature rise [K]',1.,30.,12.,.5)
            fw_pinch=st.number_input('Minimum HX hot-end pinch [K]',0.,15.,0.,.5)
            fw_ceiling=st.number_input('Facility return ceiling [°C]',10.,90.,60.,1.)
            capacity=st.number_input('Available facility duty [kW; 0 unknown]',min_value=0.,value=0.,step=100.)
            ua=st.number_input('Evaluated HX UA [kW/K; 0 unknown]',min_value=0.,value=0.,step=1.)
            st.caption('Flow and duty apply to this CDU. More facility flow does not directly increase rack flow.')
        with st.expander('Advanced: component losses & taper'):
            st.caption('Use component data here when available. Taper reduces header size toward the tip; Cd describes how the orifice passes flow; Kh describes pressure loss.')
            taper=st.slider('Tip / main diameter ratio',.4,1.,1.,.01)
            gravity=st.checkbox('Include gravity',True)
            cd=st.number_input('Orifice Cd',.01,1.,.62,.01)
            qd_mode=st.selectbox('QD loss model',['Diameter-scaled estimate','Fixed resistance / measured curve'])
            st.caption('Diameter scaling assumes the same dimensionless loss coefficient. Reference Kh covers all QDs in one branch path; do not multiply by connector count again. A supplied measured curve overrides the estimate.')
            for kind in ('compute','switch'):
                b=c['branches'][kind]
                b['tube_length_m']=st.number_input(f'{kind.title()} branch tube length [m]',min_value=0.,value=float(b['tube_length_m']),step=.1)
                b['coldplate_K']=st.number_input(f'{kind.title()} cold-plate Kh [million]',min_value=0.,value=b['coldplate_K']/1e6,step=.1)*1e6
                b['qdc_K']=st.number_input(f'{kind.title()} reference QD Kh [million]',min_value=0.,value=b['qdc_K']/1e6,step=.1)*1e6
                b['qdc_reference_diameter_m']=st.number_input(f'{kind.title()} reference QD ID [mm]',min_value=1.,value=8. if kind=='compute' else 6.,step=.25)/1000
                b['qdc_reference_density_kg_m3']=st.number_input(f'{kind.title()} reference QD density [kg/m³]',min_value=100.,value=1020.,step=5.)
        with st.expander('Advanced: limits & temperature assumptions'):
            strict=st.checkbox('Enforce provisional assumptions as hard constraints',False)
            for key,label in [('rack_flow_max_LPM','Rack flow ceiling [L/min]'),('supply_max_C','Rack supply ceiling [°C]'),('return_max_C','Rack return ceiling [°C]'),('branch_outlet_max_C','Tray outlet ceiling [°C]'),('header_velocity_max_m_s','Header velocity ceiling [m/s]')]:
                c['constraints'][key]=st.number_input(label,min_value=.1,value=float(c['constraints'][key]),step=.5)
            st.caption('Rack limits are an editable reference envelope. Chip resistance intervals and 80°C targets are assumptions, not verified optimal-performance limits.')
            c['chip_temperature']={}
            for kind,(low,high) in CHIP_DEFAULTS.items():
                lo=st.number_input(f'{kind} R low [K/W]',0.,1.,low,.001,format='%.3f')
                hi=st.number_input(f'{kind} R high [K/W]',0.,1.,high,.001,format='%.3f')
                target=st.number_input(f'{kind} target ceiling [°C]',20.,150.,80.,1.)
                limit=st.number_input(f'{kind} manufacturer limit [°C; 0 unknown]',0.,150.,0.,1.)
                c['chip_temperature'][kind]=dict(resistance_range_K_W=[lo,hi],target_max_C=target,manufacturer_limit_C=limit or None)
        c['rack'].update(flow_LPM=flow,supply_C=supply,operating_mode=operating,gravity_enabled=gravity)
        c['cdu']['served_racks']=racks;c['coolant']['type']=coolant
        c['power'].update(compute_fraction=compute,switch_fraction=switch)
        c['facility'].update(supply_C=fw_supply,flow_LPM=fw_flow,design_deltaT_K=fw_rise,minimum_hot_pinch_K=fw_pinch,max_return_C=fw_ceiling,available_capacity_W=capacity*1000 or None,UA_W_K=ua*1000 or None)
        c['constraint_policy']={'enforce_assumptions':strict}
        c['geometry']['supply'].update(profile='power' if taper<1 else 'constant',inlet_m=diameter/1000,outlet_m=diameter*taper/1000)
        c['geometry']['return'].update(profile='power' if taper<1 else 'constant',inlet_m=diameter*taper/1000,outlet_m=diameter/1000)
        c['balancing_mode']='auto_equivalent' if balancing=='Automatic equivalent orifices' else 'resistance'
        for kind,(bd,qd,bore,kh) in values.items():
            c['branches'][kind].update(diameter_m=bd/1000,qdc_diameter_m=qd/1000,orifice_diameter_m=bore/1000 or None,restriction_K=kh,orifice_Cd=cd,qdc_model='diameter_scaled' if qd_mode=='Diameter-scaled estimate' else 'fixed')
        with st.expander('Individual tray overrides'):
            st.caption('Enable a row to replace its class bore. A bore of zero removes the class plate for that tray. Available in Manual mode.')
            rows=[dict(tray_id=tray,override=False,bore_mm=values['compute' if tray.startswith('C') else 'switch'][2],Cd=cd) for tray in c['rack']['layout']]
            edited=st.data_editor(pd.DataFrame(rows),hide_index=True,key='orifice_editor',disabled=['tray_id'] if balancing=='Manual orifice bores' else True,
                column_config={'bore_mm':st.column_config.NumberColumn(min_value=0.,max_value=30.,step=.1),'Cd':st.column_config.NumberColumn(min_value=.01,max_value=1.,step=.01)})
            if balancing=='Manual orifice bores':
                for row in edited.to_dict('records'):
                    if row['override']:c['branches']['overrides'][row['tray_id']]={'orifice_diameter_m':row['bore_mm']/1000 or None,'orifice_Cd':row['Cd']}
        with st.expander('Expert settings — every model parameter'):
            st.caption('YAML overrides apply after the controls above. Includes measured QD/cold-plate curves, per-tray geometry, fitting losses, pump curves, solver tolerances and optimization weights. Download the template to see every current field.')
            st.download_button('Download configuration template',yaml.safe_dump(portable_config(c),sort_keys=False),'design_config.yaml','text/yaml')
            active=st.checkbox('Apply expert YAML overrides',False)
            text=st.text_area('Configuration overrides',value='{}',height=180,help='Example: geometry:\n  roughness_m: 0.000005\nUse the downloaded configuration as a field reference.')
            if active:
                # Exported bundled path remains portable; resolve it to the current trusted table.
                parsed=yaml.safe_load(text) or {}
                if isinstance(parsed,dict) and isinstance(parsed.get('coolant'),dict) and parsed['coolant'].get('property_file')=='data/coolant_properties.csv':
                    parsed['coolant']['property_file']=c['coolant']['property_file'];text=yaml.safe_dump(parsed)
                c=apply_yaml_overrides(c,text)
                st.warning('Expert overrides are active and take precedence over the controls above.')
        with st.expander('Saved study & maintenance'):
            st.caption('The saved optimized result is a historical study. For your current experiments, use Compare & explore to pin designs.')
            if st.button('Show saved optimized result'):st.session_state['show_saved']=True
            if st.button('Clear calculation cache'):
                st.cache_data.clear();st.session_state.pop('fluid_cases',None);st.rerun()
    return c
