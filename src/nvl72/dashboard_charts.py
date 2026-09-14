"""Explicit Vega-Lite charts with units, stable tray order and hover values."""
import json
import pandas as pd
import matplotlib.pyplot as plt

TEAL='#087f8c';SLATE='#94a3b8';ORANGE='#c26724'

def flow_figure(df):
    fig,ax=plt.subplots(figsize=(11,4));x=range(len(df));w=.38
    ax.bar([i-w/2 for i in x],df.target_flow_LPM,w,color=SLATE,label='Target');ax.bar([i+w/2 for i in x],df.actual_flow_LPM,w,color=TEAL,label='Actual')
    ax.set(ylabel='Flow at supply density [L/min]',xlabel='Tray · rack order',xticks=list(x),xticklabels=df.tray_id);ax.tick_params(axis='x',rotation=90);ax.grid(axis='y',alpha=.2);ax.legend();fig.tight_layout();return fig
def flow_error_figure(df):
    fig,ax=plt.subplots(figsize=(11,3));x=range(len(df));v=df.flow_error_percent.to_numpy();ax.bar(x,v,color=[ORANGE if y<0 else TEAL for y in v]);ax.axhline(0,color='#334155');ax.set(ylabel='Flow error [%]',xlabel='Tray · rack order',xticks=list(x),xticklabels=df.tray_id);ax.tick_params(axis='x',rotation=90);fig.tight_layout();return fig
def temperature_figure(df,reference,limit):
    fig,ax=plt.subplots(figsize=(11,4));x=range(len(df));ref=reference.set_index('tray_id').loc[df.tray_id].T_out_C
    ax.plot(x,df.T_out_C,'o-',color=TEAL,label='Current');ax.plot(x,ref,'o--',color=SLATE,label='Reference');ax.axhline(limit,color=ORANGE,ls='--',label=f'Ceiling {limit:g}°C');ax.set(ylabel='Outlet temperature [°C]',xlabel='Tray · rack order',xticks=list(x),xticklabels=df.tray_id);ax.tick_params(axis='x',rotation=90);ax.grid(alpha=.2);ax.legend();fig.tight_layout();return fig
def budget_figure(values):
    names={'qdcs':'Quick disconnects','coldplates':'Cold plates','tubing':'Branch tubing','restrictions':'Balancing resistance','orifices':'Orifice plates','header_friction':'Header friction','header_minor':'Header fittings','hydrostatic_net':'Net buoyancy','fittings':'Branch fittings','valves':'Valves','external_piping':'External pipes','external_fittings':'External fittings','external_equipment':'External equipment'}
    f=pd.Series({names.get(k,k):v/1000 for k,v in values.items()}).sort_values();fig,ax=plt.subplots(figsize=(9,5));ax.barh(f.index,f.values,color=TEAL);ax.set(xlabel='Equivalent system head contribution [kPa]');ax.grid(axis='x',alpha=.2);fig.tight_layout();return fig
def pressure_figure(df):
    fig,ax=plt.subplots(figsize=(9,4));ax.plot(df.elevation_m,df.supply_pressure_kPa,'o-',color=TEAL,label='Supply');ax.plot(df.elevation_m,df.return_pressure_kPa,'o-',color=ORANGE,label='Return');ax.set(xlabel='Elevation from bottom [m]',ylabel='Pressure relative to CDU return [kPa]');ax.grid(alpha=.2);ax.legend();fig.tight_layout();return fig

def records(frame):return json.loads(frame.to_json(orient='records'))
def chart(frame,**spec):
    # Streamlit 1.63 bundles Vega-Lite 5; using its schema avoids silent NaN
    # scales when a newer schema is supplied to the embedded renderer.
    return {'$schema':'https://vega.github.io/schema/vega-lite/v5.json','data':{'values':records(frame)},'height':300,
        'config':{'view':{'stroke':None},'axis':{'labelFontSize':11,'titleFontSize':12,'gridColor':'#e8edf2'},'legend':{'orient':'top','title':None}},**spec}

def flow_comparison(df):
    f=df[['tray_id','actual_flow_LPM','target_flow_LPM']].rename(columns={'tray_id':'Tray','actual_flow_LPM':'Actual','target_flow_LPM':'Target'})
    long=f.melt('Tray',var_name='Series',value_name='Flow')
    return chart(long,mark={'type':'bar','cornerRadiusTopLeft':2,'cornerRadiusTopRight':2},encoding={
        'x':{'field':'Tray','type':'nominal','sort':f.Tray.tolist(),'axis':{'labelAngle':-45,'title':'Tray · rack order'}},
        'xOffset':{'field':'Series','sort':['Target','Actual']},
        'y':{'field':'Flow','type':'quantitative','stack':None,'scale':{'zero':True}},
        'color':{'field':'Series','scale':{'domain':['Target','Actual'],'range':[SLATE,TEAL]}},
        'tooltip':[{'field':'Tray'},{'field':'Series'},{'field':'Flow','format':'.3f','type':'quantitative'}]})

def flow_error(df):
    f=df[['tray_id','flow_error_percent']].rename(columns={'tray_id':'Tray','flow_error_percent':'FlowError'})
    return chart(f,layer=[{'mark':'bar','encoding':{
        'x':{'field':'Tray','type':'nominal','sort':f.Tray.tolist(),'axis':{'labelAngle':-45}},
        'y':{'field':'FlowError','type':'quantitative'},
        'color':{'condition':{'test':"datum.FlowError < 0",'value':ORANGE},'value':TEAL},
        'tooltip':[{'field':'Tray'},{'field':'FlowError','type':'quantitative','format':'.2f'}]}},
        {'mark':{'type':'rule','color':'#334155'},'encoding':{'y':{'datum':0}}}])

def temperature(df,reference,limit):
    f=df[['tray_id','T_out_C']].rename(columns={'tray_id':'Tray','T_out_C':'Current'})
    f['Reference']=f.Tray.map(reference.set_index('tray_id').T_out_C)
    f=f.melt('Tray',var_name='Series',value_name='Outlet')
    return chart(f,layer=[{'mark':{'type':'line','point':True},'encoding':{
        'x':{'field':'Tray','type':'nominal','sort':df.tray_id.tolist(),'axis':{'labelAngle':-45,'title':'Tray · rack order'}},
        'y':{'field':'Outlet','type':'quantitative','scale':{'zero':False}},
        'color':{'field':'Series','scale':{'domain':['Current','Reference'],'range':[TEAL,SLATE]}},
        'strokeDash':{'field':'Series','scale':{'domain':['Current','Reference'],'range':[[1,0],[5,3]]}},
        'tooltip':[{'field':'Tray'},{'field':'Series'},{'field':'Outlet','type':'quantitative','format':'.2f'}]}},
        {'mark':{'type':'rule','color':ORANGE,'strokeDash':[6,4]},'encoding':{'y':{'datum':limit},'tooltip':{'value':f'Configured outlet ceiling: {limit:g}°C'}}}])

def budget(values):
    names={'qdcs':'Quick disconnects','coldplates':'Cold plates','tubing':'Branch tubing','restrictions':'Balancing resistance','orifices':'Orifice plates','header_friction':'Header friction','header_minor':'Header fittings','hydrostatic_net':'Net buoyancy','fittings':'Branch fittings','valves':'Valves','external_piping':'External pipes','external_fittings':'External fittings','external_equipment':'External equipment'}
    f=pd.DataFrame([{'Component':names.get(k,k),'Head':v/1000} for k,v in values.items()])
    return chart(f,height=360,mark={'type':'bar','color':TEAL},encoding={
        'y':{'field':'Component','type':'nominal','sort':'-x','axis':{'title':None,'labelLimit':170}},
        'x':{'field':'Head','type':'quantitative','title':'Equivalent system head contribution [kPa]'},
        'tooltip':[{'field':'Component'},{'field':'Head','type':'quantitative','format':'.3f'}]})

def chip_band(df):
    x={'field':'tray_id','type':'nominal','sort':df.tray_id.tolist(),'axis':{'title':'Tray','labelAngle':-45}}
    return chart(df,layer=[
        {'mark':{'type':'area','color':TEAL,'opacity':.18},'encoding':{'x':x,'y':{'field':'junction_low_C','type':'quantitative','title':'Estimated junction temperature [°C]','scale':{'zero':False}},'y2':{'field':'junction_high_C'}}},
        {'mark':{'type':'line','color':TEAL,'point':True},'encoding':{'x':x,'y':{'field':'junction_high_C','type':'quantitative'},'tooltip':[{'field':'tray_id','title':'Tray'},{'field':'junction_low_C','title':'Lower [°C]','format':'.2f'},{'field':'junction_high_C','title':'Upper [°C]','format':'.2f'}]}},
        {'mark':{'type':'line','color':ORANGE,'strokeDash':[6,4]},'encoding':{'x':x,'y':{'field':'target_max_C','type':'quantitative'},'tooltip':[{'field':'target_max_C','title':'Assumed target [°C]'}]}}])

def header_pressure(df):
    f=df[['elevation_m','supply_pressure_kPa','return_pressure_kPa']].rename(columns={'elevation_m':'Height','supply_pressure_kPa':'Supply','return_pressure_kPa':'Return'}).melt('Height',var_name='Header',value_name='Pressure')
    return chart(f,mark={'type':'line','point':True},encoding={
        'x':{'field':'Height','type':'quantitative','title':'Elevation from bottom [m]'},
        'y':{'field':'Pressure','type':'quantitative','title':'Pressure relative to CDU return [kPa]'},
        'color':{'field':'Header','scale':{'domain':['Supply','Return'],'range':[TEAL,ORANGE]}},
        'tooltip':[{'field':'Header'},{'field':'Height','format':'.3f'},{'field':'Pressure','format':'.3f'}]})
