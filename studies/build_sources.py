"""Record every baseline leaf and retain source-specification alternatives."""
from pathlib import Path
import re
import yaml
root=Path(__file__).resolve().parents[1]
c=yaml.safe_load((root/'config/baseline.yaml').read_text())
urls={
 'architecture':'https://docs.nvidia.com/dgx/dgxgb200-user-guide/hardware.html',
 'power':'https://docs.nvidia.com/mission-control/docs/systems-administration-guide/2.2.0/prs/faq.html',
 'switch':'https://docs.nvidia.com/datacenter/dps/versions/0.8/guides/runbooks/maxlps-simple-mode-pilot/',
 'cdu':'https://www.vertiv.com/4a1be9/globalassets/shared/vertiv-coolchip-cdu-100_datasheet_en.pdf',
 'qct':'https://blog.qct.io/wp-content/uploads/2025/04/QCT-Qoolrack-Stand-Alone_Advanced-Liquid-Cooling-for-NVIDIA-GB200-NVL72-Systems.pdf',
 'gf':'https://www.datacenter-forum.com/georg-fischer/high-performance-polymers-in-secondary-fluid-network-applications-slide-deck/download'}
known={
 'rack.compute_trays':('NVIDIA','architecture','agent.md §2'), 'rack.switch_trays':('NVIDIA','architecture','agent.md §2'),
 'power.gpu_W_each':('NVIDIA','power','Maximum power budget, not workload measurement'),
 'power.gpus_per_compute_tray':('NVIDIA','architecture','Published topology'),
 'power.cpus_per_compute_tray':('NVIDIA','architecture','Published topology'),
 'power.grace_cpu_W_each':('DERIVED','power','(5800-4*1200)/2; allocated budget'),
 'power.switch_rack_total_W':('ASSUMPTION','switch','Historical static power reference; not independently reverified in September 2026 audit. Full liquid heat capture is assumed.'),
 'rack.flow_LPM':('ASSUMPTION','cdu','Selected equal to CDU rated point'),
 'cdu.capacity_W':('OEM','cdu','At stated 4 K approach and nominal flow'),
 'cdu.nominal_flow_LPM':('OEM','cdu','Rated flow, not an independently verified maximum'),
 'cdu.available_dp_Pa':('OEM','cdu','External available head; excludes internal CDU losses'),
 'cdu.approach_K':('OEM','cdu','Rated approach, not full UA map'),
 'cdu.nominal_electric_W':('OEM','cdu','Whole CDU rating, not rack pumping prediction'),
 'constraints.rack_flow_max_LPM':('OEM','qct','QCT reference flow need; using it as a ceiling is a configured design choice, not a verified universal hardware maximum.'),
 'constraints.supply_max_C':('OEM','qct','QCT implementation maximum'),
 'constraints.return_max_C':('OEM','qct','QCT implementation maximum')}
def units(key,value):
    if key.startswith('loss_coefficients.') or key.endswith('minor_K'): return '1'
    if key.endswith('_K_W'): return 'K/W'
    if key.endswith('volume_m3'): return 'm³'
    for suffix,unit in [('_LPM','L/min'),('_m_s2','m/s²'),('_W_each','W'),('_W','W'),('_Pa','Pa'),('_kPa','kPa'),('_C','°C'),('_K','K'),('_m','m')]:
        if key.endswith(suffix):
            return 'Pa/(kg/s)^2' if any(s in key for s in ('coldplate_K','qdc_K','restriction_K','equipment_K')) else unit
    if 'efficiency' in key or 'fraction' in key or 'multiplier' in key or 'coefficients' in key:return '1'
    return 'configuration / dimensionless'
def walk(d,prefix=''):
    for k,v in d.items():
        path=f'{prefix}.{k}' if prefix else k
        if isinstance(v,dict) and v: yield from walk(v,path)
        else: yield path,v
records={}
for key,v in walk(c):
    cat,src,note=known.get(key,('ASSUMPTION',None,'User-editable modeling/design/numerical input; not a measured NVIDIA value.'))
    records[key]={'value':v,'units':units(key,v),'category':cat,'source':src or 'Engineering baseline assumption','url':urls.get(src),'notes':note}
additional={
 'liquid_reference_W':(115560,'W','DERIVED','power','18*5800 + 11160; assumes entire allocated primary silicon heat enters coolant'),
 'nominal_liquid_W':(102000,'W','DERIVED','architecture','120 kW *85%; separate historical envelope, not mixed with primary case'),
 'HPE_rack_W':(132000,'W','OEM',None,'agent.md §3 HPE: 115 kW liquid and 17 kW air'),
 'HPE_liquid_W':(115000,'W','OEM',None,'Separate OEM envelope'),
 'HPE_air_W':(17000,'W','OEM',None,'Residual air heat excluded from liquid network'),
 'OCP_flow_clue_LPM':(5,'L/min','OCP',None,'Scope ambiguous; not a universal per-tray specification'),
 'GF_technical_loop_Pa':(232000,'Pa','3P','gf','Broader technical loop; not bare rack or NVIDIA specification'),
 'GF_fractions':({'coldplates':52,'qdcs':22.2,'tubing':12.5,'equipment':7.7,'fittings':2.9,'pipes':1.9,'valves':1.0,'manifold':.14},'%','3P','gf','Rounded fractions; validation compares categories without automatic fitting'),
 'XDU1350_two_pumps':({'capacity_W':1368000,'flow_LPM':1200,'external_dp_Pa':244000,'power_W':13700},'SI / named fields','OEM',None,'agent.md §12; aggregate, shared across racks'),
 'XDU1350_three_pumps':({'flow_LPM':1800,'external_dp_Pa':198000,'power_W':20500},'SI / named fields','OEM',None,'Alternative three-pump rating, not same pump curve'),
 'XDU1350_temperature_C':([10,52],'°C','OEM',None,'Conservatively applied to secondary supply and return'),
 'PG25_40C':({'rho':1020,'cp':4120,'mu':.00147,'k':.476},'SI','3P',None,'agent.md §8 reference table'),
 'PG25_50C':({'rho':1015,'cp':4130,'mu':.00115},'SI','3P',None,'agent.md §8 reference table'),
 'PG25_extension':({'rho_slope':-.5,'cp_slope':1.,'k_slope':.0009},'SI/K','ESTIMATE',None,'rho/cp linearly continued; log(mu) continued from 40/50°C anchors. k slope assumed. 5–95°C range is numerical, not qualified hardware envelope.'),
 'water_table':('IAPWS97 at 0.1 MPa, 5 K grid','SI','DERIVED',None,'Generated using iapws 1.5.5; see studies/build_property_table.py')}
for key,(v,u,cat,src,note) in additional.items(): records[key]={'value':v,'units':u,'category':cat,'source':src or 'agent.md','url':urls.get(src),'notes':note}
inrow=yaml.safe_load((root/'config/inrow.yaml').read_text())
inrow_url='https://www.vertiv.com/499c46/globalassets/products/thermal-management/high-density-solutions/liebert-xdu-coolant-distribution-units/liebert-xdu1350-coolant-distribution-unitcdu-ds-en-na-sl-70799-web.pdf'
for key,value in walk(inrow):
    if key=='extends': continue
    published=key in ('cdu.capacity_W','cdu.nominal_flow_LPM','cdu.available_dp_Pa','cdu.secondary_min_C','cdu.secondary_max_C','cdu.nominal_electric_W')
    records['inrow.'+key]={'value':value,'units':units(key,value),'category':'OEM' if published else 'ASSUMPTION',
        'source':'Vertiv XDU1350, agent.md section 12' if published else 'In-row design selection',
        'url':inrow_url if published else None,
        'notes':'Two-pump aggregate rating; secondary temperature range conservatively applied at both ends' if published else 'Editable overlay assumption; 38 C supply chosen for return-temperature margin; eight identical racks.'}
records['water_table']['url']='https://iapws.org/relguide/IF97-Rev.html'
records['PG25_extension']['url']='https://www.dow.com/en-us/pdp.dowfrost-lc-25-heat-transfer-fluid.497419z.html'
text=(root/'agent.md').read_text()
(root/'data/sources.yaml').write_text(yaml.safe_dump({'defaults':records,'source_urls_from_agent':sorted(set(re.findall(r'https://[^\s<>]+',text)))},sort_keys=False))
(root/'data/component_defaults.yaml').write_text(yaml.safe_dump({'category':'ASSUMPTION','notes':'Reference only; authoritative executable inputs are config/baseline.yaml. K is Pa/(kg/s)^2. Coefficients selected in the scale of agent.md §39, with separate unmeasured switch resistance.','branches':c['branches'],'loss_coefficients':c['loss_coefficients']},sort_keys=False))
