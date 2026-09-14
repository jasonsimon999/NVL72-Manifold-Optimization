"""Single-variable experiments on fixed hardware, retaining failed points."""
from copy import deepcopy
from .solver import solve

PARAMETERS={'Rack flow [L/min]':('rack','flow_LPM',1.),'Header ID [mm]':('header',None,.001),
 'Compute branch ID [mm]':('compute','diameter_m',.001),'Switch branch ID [mm]':('switch','diameter_m',.001),
 'Compute QD ID [mm]':('compute','qdc_diameter_m',.001),'Switch QD ID [mm]':('switch','qdc_diameter_m',.001),
 'Compute orifice bore [mm]':('compute','orifice_diameter_m',.001),'Switch orifice bore [mm]':('switch','orifice_diameter_m',.001)}

def sweep_design(result,parameter,values):
    group,key,scale=PARAMETERS[parameter]
    base=deepcopy(result.get('fixed_orifice_config') or result['config'])
    if group=='rack':base['rack']['operating_mode']='fixed_flow'
    rows=[]
    for value in values:
        c=deepcopy(base);converted=float(value)*scale
        if group=='header':
            for side in ['supply','return']:c['geometry'][side].update(profile='constant',inlet_m=converted,outlet_m=converted)
        elif group=='rack':c['rack'][key]=converted
        else:
            if key=='orifice_diameter_m':
                c['balancing_mode']='resistance';c['branches'][group]['restriction_K']=0.;converted=converted or None
            c['branches'][group][key]=converted
            for tray,override in c['branches']['overrides'].items():
                if tray.startswith('C' if group=='compute' else 'S'):
                    override.pop(key,None)
                    if key=='orifice_diameter_m':override['restriction_K']=0.
            if key=='qdc_diameter_m' and (c['branches'][group].get('qdc_model')!='diameter_scaled' or 'qdc_curve' in c['branches'][group] or any('qdc_curve' in v for t,v in c['branches']['overrides'].items() if t.startswith('C' if group=='compute' else 'S'))):
                raise ValueError('QD diameter sweep requires diameter-scaled estimates without measured QD curves')
        row={'Value':float(value)}
        try:
            r=solve(c);m=r['metrics']
            row.update({'Enforced pass':r['feasible'],'All screens pass':r['screening_pass'],'Flow error [% RMS]':100*m['RMS_target_error'],
                'Max outlet [°C]':m['T_out_max_C'],'Pump [W]':m['pump_electrical_W'],'Head [kPa]':m['system_dp_Pa']/1000,
                'Issues':', '.join(k for k,v in r['constraints'].items() if not v['pass'])})
        except (ValueError,RuntimeError) as exc:row.update({'Enforced pass':False,'All screens pass':False,'Issues':str(exc)})
        rows.append(row)
    return rows
