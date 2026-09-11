"""Publication-oriented plots; pressure-budget bars are flow-weighted path heads."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':120,'savefig.bbox':'tight'})

def save(fig,path,dpi=180):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(path,dpi=dpi);plt.close(fig)

def rack_schematic(result,metric='T_out_C'):
    df=pd.DataFrame(result['trays']); fig,ax=plt.subplots(figsize=(5,8))
    values=df[metric].to_numpy();norm=plt.Normalize(values.min(),max(values.max(),values.min()+1e-6))
    cmap=plt.get_cmap('viridis')
    for i,row in df.iterrows():
        ax.add_patch(plt.Rectangle((.22,i),.56,.78,facecolor=cmap(norm(row[metric])),edgecolor='white'))
        ax.text(.5,i+.39,row.tray_id,ha='center',va='center',fontsize=8,color='white' if norm(row[metric])<.65 else 'black')
        ax.plot([.12,.22],[i+.39]*2,color='#2765a6',lw=1)
        ax.plot([.78,.88],[i+.39]*2,color='#c85732',lw=1)
    ax.plot([.12,.12],[0,len(df)],color='#2765a6',lw=5);ax.plot([.88,.88],[0,len(df)],color='#c85732',lw=5)
    ax.set(xlim=(0,1),ylim=(-1,len(df)+1),xticks=[],yticks=[],title='Parametric rack schematic · not proprietary CAD')
    labels={'T_out_C':'Outlet temperature [°C]','actual_flow_LPM':'Flow at supply density [L/min]','heat_load_W':'Heat load [W]','branch_dP_kPa':'Branch differential [kPa]','flow_error_percent':'Target-flow error [%]'}
    fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),ax=ax,label=labels.get(metric,metric))
    return fig

def result_figures(result,directory,prefix='baseline'):
    directory=Path(directory);df=pd.DataFrame(result['trays']);x=np.arange(len(df));dpi=result['config']['plots']['dpi']
    specifications=[('supply_pressure','supply_pressure_kPa','Supply pressure relative to CDU return [kPa]'),
      ('return_pressure','return_pressure_kPa','Return pressure relative to CDU return [kPa]'),
      ('branch_differential','branch_dP_kPa','Branch differential pressure [kPa]'),
      ('actual_flow','actual_flow_LPM','Flow at supply density [L/min]'),
      ('target_flow','target_flow_LPM','Target flow at supply density [L/min]'),
      ('heat_load','heat_load_W','Liquid heat load [W]'),('outlet_temperature','T_out_C','Tray outlet [°C]'),
      ('temperature_rise','deltaT_C','Tray coolant rise [K]')]
    for filename,column,label in specifications:
        fig,ax=plt.subplots(figsize=(10,3.6));ax.plot(x,df[column],marker='o',ms=3,color='#1c648a')
        ax.set(ylabel=label,xticks=x,xticklabels=df.tray_id,title=result['config']['name']);ax.tick_params(axis='x',rotation=90);ax.grid(alpha=.2)
        if 'pressure' in filename:
            ax.set_xlabel('Tray position (bottom → top); elevations in CSV')
        save(fig,directory/f'{prefix}_{filename}.png',dpi)
    fig,ax=plt.subplots(figsize=(10,3.6));ratio=np.divide(df.actual_flow_LPM,df.target_flow_LPM,out=np.full(len(df),np.nan),where=df.target_flow_LPM>0)
    ax.bar(x,ratio,color=['#1c648a' if k=='compute' else '#d88232' for k in df.tray_type]);ax.axhline(1,color='black',ls='--')
    ax.set(ylabel='Actual / target flow',xticks=x,xticklabels=df.tray_id);ax.tick_params(axis='x',rotation=90)
    save(fig,directory/f'{prefix}_flow_ratio.png',dpi)
    fig,ax=plt.subplots(figsize=(10,4));ax.bar(x-.18,df.actual_flow_LPM,.36,label='Actual');ax.bar(x+.18,df.target_flow_LPM,.36,label='Thermal target')
    ax.set(ylabel='Flow at supply density [L/min]',xticks=x,xticklabels=df.tray_id);ax.tick_params(axis='x',rotation=90);ax.legend()
    save(fig,directory/f'{prefix}_target_comparison.png',dpi)
    fig,ax=plt.subplots(figsize=(8,4));budget=result['pressure_budget_Pa'];ax.barh(list(budget),np.array(list(budget.values()))/1000,color='#1c648a')
    ax.set_xlabel('Equivalent head contribution [kPa] · flow-weighted paths')
    save(fig,directory/f'{prefix}_pressure_budget.png',dpi)
    save(rack_schematic(result),directory/f'{prefix}_rack.png',dpi)
    fig,ax=plt.subplots(figsize=(5,4));ax.plot(df.supply_pressure_kPa,df.elevation_m,label='Supply');ax.plot(df.return_pressure_kPa,df.elevation_m,label='Return')
    ax.set(xlabel='Pressure relative to CDU return [kPa]',ylabel='Elevation [m]');ax.legend();save(fig,directory/f'{prefix}_pressure_height.png',dpi)
    from .cdu import pump_head
    from .units import lpm_to_m3s
    flows=np.linspace(0,180,100);d=result['config']['cdu'];fig,ax=plt.subplots(figsize=(6,4))
    ax.plot(flows,pump_head(lpm_to_m3s(flows*d['served_racks']),d)/1000,label='Assumed maximum-speed curve' if d['speed']==1 else 'Assumed selected-speed curve')
    met=result['metrics'];ax.scatter([met['rack_flow_LPM']],[met['system_dp_Pa']/1000],color='#c85732',label='Required duty')
    ax.set(xlabel='Per-rack flow [L/min]',ylabel='External head [kPa]',ylim=(0,None));ax.legend()
    save(fig,directory/f'{prefix}_pump.png',dpi)

def comparison_figures(a,b,directory):
    for field,unit,name in [('actual_flow_LPM','Flow at supply density [L/min]','flow'),('T_out_C','Tray outlet temperature [°C]','temperature')]:
        fig,ax=plt.subplots(figsize=(10,4));da=pd.DataFrame(a['trays']);db=pd.DataFrame(b['trays']);x=np.arange(len(da))
        ax.plot(x,da[field],'o-',ms=3,label='Reference');ax.plot(x,db[field],'s-',ms=3,label='Selected candidate')
        ax.set(ylabel=unit,xticks=x,xticklabels=da.tray_id);ax.tick_params(axis='x',rotation=90);ax.legend();ax.grid(alpha=.2)
        save(fig,Path(directory)/f'comparison_{name}.png')

def sweep_figures(frame,directory):
    mappings={'header_diameter_mm':[('M_thermal','Thermal maldistribution'),('RMS_target_error','RMS target-flow error')],
      'taper_ratio':[('M_thermal','Thermal maldistribution'),('rack_dp_Pa','Rack pressure drop [Pa]'),('pump_electrical_W','Pump electrical power [W]')],
      'rack_flow_LPM':[('T_out_max_C','Maximum tray outlet [°C]'),('rack_deltaT_K','Rack coolant rise [K]')],
      'compute_restriction_K':[('RMS_target_error','RMS target-flow error')],
      'switch_restriction_K':[('RMS_target_error','RMS target-flow error')],
      'supply_C':[('rack_dp_Pa','Rack pressure drop [Pa]')]}
    for parameter,axes in mappings.items():
        sub=frame[frame.parameter==parameter]
        for field,label in axes:
            fig,ax=plt.subplots(figsize=(6,4));ax.plot(sub.value,sub[field],'o-',label='Solved')
            failed=sub[~sub.feasible];ax.scatter(failed.value,failed[field],marker='x',color='red',label='Constraint violation')
            ax.set(xlabel=parameter,ylabel=label);ax.grid(alpha=.2);ax.legend();save(fig,Path(directory)/f'sweep_{parameter}_{field}.png')

def pareto_figures(frame,directory):
    from .objectives import pareto_mask
    frame=frame[frame.feasible].dropna(subset=['RMS_target_error'])
    for x,label in [('pump_electrical_W','Pump electrical power [W]'),('header_volume_m3','Header fluid volume [m³]')]:
        fig,ax=plt.subplots(figsize=(6,4));ax.scatter(frame[x],frame.RMS_target_error,s=12,alpha=.15,label='Feasible sampled designs')
        mask=pareto_mask(frame[[x,'RMS_target_error']].to_numpy());front=frame[mask].sort_values(x)
        ax.plot(front[x],front.RMS_target_error,'o-',ms=4,color='#c85732',label='Sampled nondominated frontier')
        ax.set(xlabel=label,ylabel='RMS thermal-flow error');ax.grid(alpha=.2);ax.legend();save(fig,Path(directory)/f'pareto_{x}.png')
