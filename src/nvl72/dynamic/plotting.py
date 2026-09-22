"""Readable paired plots; fixed gray dashed, active teal solid everywhere."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

def time_series(result, tray=0):
    f,a=result['fixed'],result['active'];t=f['time_s']
    specs=[('Rack electrical demand','kW',lambda r:r['electrical_W'].sum(axis=1)/1000),
           (f"{f['ids'][tray]} electrical demand",'W',lambda r:r['electrical_W'][:,tray]),
           ('Selected tray flow','L/min',lambda r:r['flow_LPM'][:,tray]),
           ('Selected valve position','% open',lambda r:r['opening'][:,tray]*100),
           ('Representative solid temperature','°C',lambda r:r['chip_C'][:,tray]),
           ('Selected coolant outlet','°C',lambda r:r['outlet_C'][:,tray]),
           ('Total rack flow','L/min',lambda r:r['flow_LPM'].sum(axis=1)),
           ('Pump speed / rated speed','ratio',lambda r:r['speed']),
           ('Rack differential pressure','kPa',lambda r:r['rack_head_Pa']/1000),
           ('Pump electricity','W',lambda r:r['pump_W'])]
    fig,axes=plt.subplots(5,2,figsize=(12,15),constrained_layout=True)
    for ax,(title,unit,fn) in zip(axes.flat,specs):
        for r,color,style,label in [(f,'#667085','--','Fixed'),(a,'#008c95','-','Active')]:
            y=fn(r)
            if np.isfinite(y).any():ax.plot(t,y,color=color,linestyle=style,label=label,lw=1.7)
        if title=='Selected tray flow':ax.plot(t,a['target_flow_LPM'][:,tray],':',color='#d77b18',label='Thermal target')
        if title=='Representative solid temperature':ax.axhline(result['settings']['chip_limit_C'],color='#c34835',ls=':',label='Screening ceiling')
        if title=='Selected coolant outlet':ax.axhline(result['settings']['outlet_limit_C'],color='#c34835',ls=':')
        ax.set(title=title,xlabel='Time · s',ylabel=unit);ax.grid(alpha=.15)
        if ax.get_legend_handles_labels()[0]:ax.legend(fontsize=8)
        ax.spines[['top','right']].set_visible(False)
    return fig

def heatmap(result,variable='chip_C'):
    fig,axes=plt.subplots(1,2,figsize=(12,7),constrained_layout=True)
    data=[]
    for side in ('fixed','active'):
        r=result[side]
        if variable=='flow_error':v=np.divide(r['mass']-r['target_mass'],r['target_mass'],out=np.zeros_like(r['mass']),where=r['target_mass']>0)*100
        elif variable=='electrical_W':v=r[variable]
        else:v=r[variable]
        data.append(v)
    finite=np.concatenate([v[np.isfinite(v)] for v in data])
    lo,hi=(finite.min(),finite.max()) if finite.size else (0,1)
    for ax,v,side in zip(axes,data,('fixed','active')):
        r=result[side];im=ax.imshow(v.T,aspect='auto',origin='upper',extent=[0,r['time_s'][-1],len(r['ids'])-.5,-.5],vmin=lo,vmax=hi,cmap='viridis')
        ax.set_yticks(range(len(r['ids'])),r['ids'],fontsize=8);ax.set(title=side.title(),xlabel='Time · s')
    labels={'chip_C':'Representative solid temperature · °C','flow_LPM':'Coolant flow · L/min',
            'flow_error':'Error relative to thermal target · %','electrical_W':'Electrical demand · W',
            'opening':'Valve opening · fraction'}
    fig.colorbar(im,ax=axes,label=labels.get(variable,variable))
    return fig

def system_snapshot(result,index):
    r=result['active'];n=len(r['ids']);fig,ax=plt.subplots(figsize=(6,8))
    ax.set_xlim(0,10);ax.set_ylim(-2,n+3);ax.axis('off')
    ax.plot([1,1],[-.5,n],color='#3189c7',lw=5);ax.plot([9,9],[-.5,n],color='#d06f4b',lw=5)
    ax.text(1,n+1,'SUPPLY',ha='center',fontsize=10);ax.text(9,n+1,'RETURN',ha='center',fontsize=10)
    ax.add_patch(Rectangle((3,-1.8),4,1,facecolor='#243b53'));ax.text(5,-1.3,'CDU / PUMP',ha='center',va='center',color='white')
    ax.annotate('',(1,-.5),(3,-1.3),arrowprops=dict(arrowstyle='->'));ax.annotate('',(7,-1.3),(9,-.5),arrowprops=dict(arrowstyle='->'))
    for i,id in enumerate(r['ids']):
        y=n-1-i;connected=r['connected'][index,i]>0
        color=('#d8eeee' if id.startswith('C') else '#e5ddf1') if connected else '#ddd'
        ax.plot([1,9],[y,y],color='#b3bec9',lw=1)
        ax.add_patch(Rectangle((3,y-.37),4,.74,facecolor=color,zorder=3))
        ax.text(5,y,f"{id}  {r['flow_LPM'][index,i]:.1f} L/min" if connected else f'{id}  DISCONNECTED',ha='center',va='center',fontsize=8,zorder=4)
        position=r['opening'][index,i];position=.5 if not np.isfinite(position) else position
        fixed_mode=r.get('controller') in ('fixed','fixed_fallback')
        face='#9aa4ad' if fixed_mode and connected else (plt.cm.Greens(.2+.8*position) if connected else '#999')
        ax.add_patch(Circle((2,y),.23,facecolor=face,edgecolor='#456',zorder=4))
    mode_label='fixed plates' if r.get('controller') in ('fixed','fixed_fallback') else 'variable orifices'
    ax.set_title(f"27 parallel branches · {mode_label} · t = {r['time_s'][index]:g} s",fontsize=12)
    fig.tight_layout();return fig

def tornado(rows):
    import pandas as pd
    df=pd.DataFrame(rows)
    fig,ax=plt.subplots(figsize=(9,max(4,len(df.parameter.unique())*.3)))
    if 'net_savings_W' in df:
        df=df.dropna(subset=['net_savings_W']);groups=df.groupby('parameter').net_savings_W.agg(['min','max'])
        groups=groups.loc[(groups['max']-groups['min']).sort_values().index]
        for i,(name,row) in enumerate(groups.iterrows()):ax.plot([row['min'],row['max']],[i,i],color='#008c95',lw=6,solid_capstyle='round')
        ax.set_yticks(range(len(groups)),groups.index)
    ax.axvline(0,color='#777',ls='--');ax.set_xlabel('Net auxiliary power saved · W (negative = active uses more)')
    ax.spines[['top','right']].set_visible(False);fig.tight_layout();return fig


def bore_history(result):
    trial=result.get('active_candidate',result['active']); fixed=result['fixed']
    base=fixed['orifice_diameter_mm']
    values=trial['orifice_diameter_mm']; disconnected=trial['connected']<=0
    return paired_maps(trial,[np.where(disconnected,np.nan,values),np.where(disconnected,np.nan,values-base)],['Adaptive bore · mm','Adaptive minus fixed bore · mm'],['viridis','RdBu_r'])

def service_response(result):
    trial=result.get('active_candidate',result['active']); fixed=result['fixed']
    return paired_maps(trial,[trial['flow_LPM'],trial['flow_LPM']-fixed['flow_LPM']],['Adaptive flow · L/min','Adaptive minus fixed flow · L/min'],['viridis','RdBu_r'])

def paired_maps(run,arrays,titles,maps):
    fig,axes=plt.subplots(1,2,figsize=(13,8),constrained_layout=True)
    for ax,data,title,cmap in zip(axes,arrays,titles,maps):
        cmap=plt.get_cmap(cmap).with_extremes(bad='#d0d5dd')
        finite=data[np.isfinite(data)]; bound=max(np.max(abs(finite)),1e-6) if finite.size else 1.
        options=dict(vmin=-bound,vmax=bound) if 'minus' in title else {}
        im=ax.imshow(data.T,aspect='auto',interpolation='nearest',extent=[0,run['time_s'][-1],len(run['ids'])-.5,-.5],cmap=cmap,**options)
        ax.set_yticks(range(len(run['ids'])),run['ids'],fontsize=8)
        ax.set(title=title,xlabel='Time · s');fig.colorbar(im,ax=ax,shrink=.7)
    return fig
