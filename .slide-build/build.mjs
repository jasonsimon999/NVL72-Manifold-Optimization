import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
import {finalizePresentation,applyPresentationChartFont} from '/Users/jasonsimon/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations/container_tools/artifact_tool_utils.mjs';
const wd='/Users/jasonsimon/Desktop/Rack Manifold Optimization';
const tmp=wd+'/.slide-build';
const skill='/Users/jasonsimon/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations';
const pdf='/Users/jasonsimon/Downloads/MEAM 5020 Final Project (1).pdf';
const py='/Users/jasonsimon/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const p=Presentation.create({slideSize:{width:960,height:540}});
const red='#95001A',blue='#00144D',light='#82AED3',ink='#242B35';
const sources={
1:'Sogunuru A, Menon YK, Niranjanappa AC, Reddy KH. Numerical and Experimental Investigations on Patterned Flow Distribution through Manifolds in Electronics Cooling. IJMPERD. 2020;10(2):975–986. https://scispace.com/pdf/numerical-and-experimental-investigations-of-patterned-flow-6skn0d5dfr.pdf',
2:'Hassan JM, Mohamed TA, Mohammed WS, Alawee WH. Modeling the Uniformity of Manifold with Various Configurations. Journal of Fluids. 2014;325259. https://doi.org/10.1155/2014/325259',
3:'Anbumeenakshi C, Thansekhar MR. Experimental investigation of header shape and inlet configuration on flow maldistribution in microchannel. Experimental Thermal and Fluid Science. 2016;75:156–161. https://doi.org/10.1016/j.expthermflusci.2016.02.004',
4:'NVIDIA. DGX GB Rack Scale Systems User Guide, Hardware. https://docs.nvidia.com/dgx/dgxgb200-user-guide/hardware.html',
5:'CoolProp. Incompressible Fluids documentation. https://coolprop.org/fluid_properties/Incompressibles.html',
6:'SciPy. scipy.optimize.least_squares documentation. https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html',
7:'Local project source and recalculated results, 15 September 2026. config/baseline.yaml, config/optimized_example.yaml, src/nvl72/{solver,hydraulics,thermal,orifices,cdu,facility,objectives}.py. Repository: https://github.com/jasonsimon999/NVL72-Manifold-Optimization',
};
const logo=await fs.readFile(tmp+'/p1-image0.png');
const mark=await fs.readFile(tmp+'/p1-image1.png');
const coverMark=await fs.readFile(tmp+'/p0-image2.png');
const coverLogo=await fs.readFile(tmp+'/p0-image1.png');
function text(s,t,x,y,w,h,size=22,color=ink,bold=false,font='Arial'){
 const o=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 o.text=t; o.text.style={typeface:font==='Gill Sans'?'GillSans':font,fontSize:size,color,bold,autoFit:'none',verticalAlignment:'top'};return o;
}
function shape(s,g,x,y,w,h,fill='none',stroke=ink,sw=1){return s.shapes.add({geometry:g,position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width:sw}});}
function img(s,b,x,y,w,h,alt){s.images.add({blob:b,contentType:'image/png',alt,fit:'contain',position:{left:x,top:y,width:w,height:h}});}
function slide(title,refs=[],note=''){
 const s=p.slides.add();s.background.fill='#FFFFFF';img(s,mark,21,11,350,393,'Penn shield watermark from supplied template');
 text(s,title,40,17,885,54,35.2,red,false,'Gill Sans');
 shape(s,'rect',0,76,940,3,light,light,0);shape(s,'rect',0,76,395,3,red,red,0);
 img(s,logo,48,493,190,36.5,'Penn Engineering template logo');
 text(s,String(p.slides.items.length),890,500,60,22,12,'#555555');
 if(refs.length)text(s,refs.map(i=>'['+i+']').join(' ')+'  Sources and calculation details in speaker notes.',42,464,850,25,12,'#555555');
 s.speakerNotes.textFrame.setText(note+'\n\n'+refs.map(i=>'['+i+'] '+sources[i]).join('\n'));
 return s;
}
function table(s,values,x=42,y=110,w=875,h=320,widths=null,size=19){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,columnWidths:widths||undefined});
 t.borders.assign({fill:'#A6AAB0',width:.6,style:'solid'});
 t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({textStyle:{typeface:'Arial',fontSize:size,color:ink},margins:{left:9,right:8,top:4,bottom:4},anchor:'center'});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++)t.getCell(r,c).fill=r===0?'#E9EEF5':(r%2?'#FFFFFF':'#F5F6F8');
 t.cells.block({row:0,column:0,rowCount:1,columnCount:values[0].length}).assign({textStyle:{typeface:'Arial',fontSize:size,bold:true,color:blue}});
 return t;
}
function section(s,label,body,y,x=44,w=865){text(s,label,x,y,w,28,23,blue,true);text(s,body,x,y+34,w,70,21);}
function arrow(s,x,y,w,h,color=red,dir='rightArrow'){shape(s,dir,x,y,w,h,color,color,0);}
function rack(s,x,y,scale=1,orifice=false){
 const S=scale;shape(s,'rect',x,y,18*S,220*S,'#DCECF7','#3979AB',2);shape(s,'rect',x+285*S,y,18*S,220*S,'#F6DFDF','#B84145',2);
 ['Compute','Switch','Compute'].forEach((a,i)=>{const yy=y+(30+i*66)*S;shape(s,'line',x+18*S,yy+17*S,267*S,0,'none','#596773',3);shape(s,'rect',x+95*S,yy,135*S,34*S,'#FFFFFF','#596773',1.2);text(s,a,x+104*S,yy+4*S,125*S,25*S,18*S);if(orifice){shape(s,'rect',x+49*S,yy+7*S,8*S,20*S,red,red,1);shape(s,'ellipse',x+34*S,yy-3*S,40*S,40*S,'none',red,2);}});
 text(s,'Supply',x-9*S,y-30*S,95*S,25*S,18*S,'#3979AB');text(s,'Return',x+267*S,y-30*S,100*S,25*S,18*S,'#B84145');
 arrow(s,x+2*S,y+183*S,13*S,26*S,'#3979AB','upArrow');arrow(s,x+288*S,y+183*S,13*S,26*S,'#B84145','downArrow');
}
// 1: Preserve the template cover composition and authors.
{
const s=p.slides.add();s.background.fill=blue;img(s,coverMark,21,16,323,363,'Penn shield from template');
text(s,'MEAM 5020 Final Project\nRack Manifold Optimization',108,169,795,126,44,'#FFFFFF',true,'Gill Sans');
shape(s,'rect',0,315,875,3,light,light,0);shape(s,'rect',744,315,131,3,red,red,0);
text(s,'Constantin de Lint, David Kim, Jason Simon, Sam Vasington',108,341,780,40,23,light,false,'Gill Sans');
text(s,'Assignment 4: Previous work, design changes, and calculation plan',108,392,755,40,20,'#FFFFFF');
img(s,coverLogo,691,451,186,68,'Penn Engineering cover logo');
s.speakerNotes.textFrame.setText('Template supplied by the user: MEAM 5020 Final Project (1).pdf. The supplied group names are retained. The PDF design is rebuilt as editable slide elements, with original brand assets. This is an NVL72-inspired design study, not a validated NVIDIA product design.');
}
// 2
{
const s=slide('Coolant Distribution Across an AI Rack',[4,7]);rack(s,65,160,1.02);
section(s,'Purpose','Deliver the cooling flow each tray needs while limiting pressure loss and pump power.',110,445,465);
section(s,'How it works','A supply header feeds parallel tray branches. Cold plates absorb heat; a return header carries it to the CDU heat exchanger.',235,445,465);
text(s,'18 compute trays + 9 switch trays\n72 GPUs + 36 CPUs',58,404,395,55,21,blue,true);
text(s,'Different heat loads and flow resistances create different cooling needs.',445,370,462,67,22,red);
}
// 3
{
const s=slide('Three Approaches From Previous Work',[1,2,3],'The three core references are original research. Study [1] is the selected baseline method. Reported nonuniformity in [2] is its own metric, not the project RMS metric.');
table(s,[['Previous approach','Evidence','Use in this project'],['[1] Patterned branch orifices\nSogunuru et al., 2020','Electronics cooling with unequal flow targets','Selected baseline: tune branch resistance to heat load'],['[2] Tapered header\nHassan et al., 2014','At Re = 150,000, reported Φ falls from 0.0345 to 0.0140','Compare header taper against added restrictions'],['[3] Header shape and inlet\nAnbumeenakshi & Thansekhar, 2016','25 water microchannels; best shape depends on flow rate','Test operating range before selecting geometry']],42,111,875,322,[290,290,295],20);
}
// 4
{
const s=slide('Selected Baseline: Patterned Orifice Sizing',[1,7],'Reference [1], sections 3–6 and Table 1. Its narrative and Table 2 disagree on experimental deviation, so no accuracy percentage is adopted. The paper benchmark has not yet been reproduced by our code.');
table(s,[['Published setup [1]','Value'],['Configuration','Z-type, water, 1 L/min total'],['Header / branch ID','12 mm / 6.5 mm'],['Channels / length','10 channels / 700 mm'],['Pattern 1 example','2.1–2.4 mm bores in branches 1, 3, 5, 7, 9']],42,112,488,279,[214,274],20);
text(s,'Why this baseline?',567,111,350,35,25,blue,true);
text(s,'It directly links unequal electronics heat loads to individually sized restrictions.',567,156,342,89,23);
text(s,'Our extension',567,269,340,35,25,blue,true);
text(s,'Couple 27 tray branches to temperature-dependent properties, component losses, and CDU limits.',567,313,345,102,22);
text(s,'Rack geometry is assumed; reproducing the literature benchmark is a future validation step.',43,427,871,32,18,red);
}
// 5 physical changes
{
const s=slide('Physical Changes to the Manifold',[1,7],'Conceptual editable diagram, not a dimensioned NVIDIA drawing. Red circles identify added replaceable orifice inserts. Header sizing/taper and quick disconnect bore are additional design variables. Three representative branches stand for 27.');
rack(s,63,175,.91,true);
text(s,'Replaceable orifice inserts',454,119,450,33,25,red,true);text(s,'Set compute and switch bores separately; allow a different bore at each tray.',454,160,453,65,22);
arrow(s,106,176,12,22,red,'downArrow');
text(s,'Header diameter and taper',454,242,450,33,25,blue,true);text(s,'Adjust the main passage to manage pressure variation along the rack.',454,283,448,62,22);
shape(s,'ellipse',48,172,50,220,'none',red,2);arrow(s,13,303,42,14,red);
text(s,'Branch and QD passage sizes',454,367,457,33,25,blue,true);text(s,'Vary flow area; verify with measured loss curves.',454,405,452,58,21);
text(s,'Schematic, not to scale',64,421,324,28,17,'#555555');
}
// 6
{
const s=slide('Goal and Design',[7],'Targets shown here are proposed study criteria, not measured product specifications. Compare candidates at matched coolant, total rack flow, inlet temperature, and heat load. A flow error metric must use heat-proportional targets rather than equal flow.');
table(s,[['Project item','Definition'],['Problem / project type','Unequal cooling allocation / component design'],['Primary goal','Match each tray flow to its heat load'],['Proposed target','RMS flow-target error ≤ 5% at the design point'],['Design variables','Header ID/taper; compute, switch, and per-tray bores'],['Secondary objectives','Minimize outlet temperature, pump power, and header volume'],['Study constraints','Outlet ≤ 65 °C; header velocity ≤ 3 m/s; 0 < bore < branch ID'],['Decision rule','Check fixed hardware and pump capability off-design']],42,104,875,337,[239,636],19);
}
// 7
{
const s=slide('Rack Calculation Inputs and Assumptions',[4,7],'These inputs reproduce config/baseline.yaml and config/optimized_example.yaml. Electrical component power is treated as heat entering coolant in this scenario. Actual liquid heat capture and switch load need measurements. Legacy PG25 is retained to reproduce the earlier study, not endorsed over manufacturer properties.');
table(s,[['Input','Study value','Evidence status'],['Rack topology','18 compute + 9 switch trays','Published topology [4]'],['Liquid heat scenario','18 × 5.80 + 9 × 1.24 = 115.56 kW','Model load assumptions'],['Rack coolant / supply / flow','Legacy PG25 / 40 °C / 120 L/min','Chosen operating point'],['Headers / branch IDs','38 mm / compute 8 mm, switch 6 mm','Assumed internal diameters'],['QD and cold-plate losses','Separate reduced resistance coefficients','Estimated, not measured curves'],['Facility water','36 °C, 150 L/min, one rack','Scenario, not a facility limit']],42,109,875,326,[234,337,304],19);
}
// 8
{
const s=slide('Mass Balance and Heat-Proportional Flow',[7],'Notation: ṁ = mass flow (kg/s), Q̇ = thermal power (W), V̇ = volume flow (m³/s), h = specific enthalpy (J/kg), cp = specific heat (J/kg/K). Common inlet state makes inlet-reference volume targets proportional to heat. Exact thermal calculation integrates the tabulated cp(T).');
section(s,'1. Conserve coolant at every junction','Σ ṁin = Σ ṁout        and        Σ ṁi = ṁrack',107);
section(s,'2. Allocate flow according to heat','ṁi* = ṁrack × Q̇i / Σ Q̇i',214);
text(s,'At 120 L/min: compute target = 6.02 L/min per tray; switch = 1.29 L/min.',44,298,860,35,21,red);
section(s,'3. Solve each tray energy balance','Q̇i = ṁi [h(Tout,i) − h(Tin)]        h(T) = ∫ cp(T) dT',353);
text(s,'Flow error (%) = 100 √{(1/n) Σ [(ṁi / ṁi*) − 1]²}',44,428,865,28,18,blue);
}
// 9
{
const s=slide('Pressure Loss and Orifice Sizing',[7],'Equations implemented in components.py and orifices.py. Kh has units Pa/(kg/s)^2 and differs from dimensionless minor-loss K. Cd = 0.62 is a screening assumption for a thin, sharp-edged plate. The permanent-loss relation accounts for recovery; pressure-tap differential alone is not permanent loss. Header model omits 3D tee momentum recovery.');
text(s,'Pipe and fitting losses',43,106,445,32,24,blue,true);
text(s,'Δp = (f L/D + ΣK) ρv²/2\nRe = ρvD/μ',43,148,437,74,25);
text(s,'Use 64/Re in laminar flow; a Haaland relation in turbulent flow, with a transition blend.',43,233,411,77,21);
text(s,'Network closure',43,330,431,32,24,blue,true);
text(s,'Each complete supply–tray–return path has the same end-to-end pressure difference. Include elevation head.',43,371,415,82,21);
text(s,'Permanent orifice loss',502,106,412,32,24,blue,true);
text(s,'Δporifice = Kh ṁ²\nβ = d/D     Ao = πd²/4',502,148,415,75,25);
text(s,'Kh = [√(1 − β⁴(1 − Cd²)) − Cd β²]²\n                 / (2ρ Cd² Ao²)',502,235,415,79,22);
text(s,'For required Kh, invert this relation to obtain bore d. Smaller bores increase resistance.',502,337,415,77,21);
text(s,'0 < d < D; Cd = 0.62 is assumed.',502,423,415,28,20,red);
}
// 10
{
const s=slide('Pump and Facility Heat-Exchanger Balance',[7],'Pump curve uses an assumed parabolic shape fitted to a nominal point and assumed shutoff head. It is not a measured manufacturer curve. Pinches: ΔT1 = rack return minus facility return; ΔT2 = rack supply minus facility supply. Both must be positive. Equal terminal differences use the continuous LMTD limit. No ambient heat loss or pump heat is included in the quoted rack balance.');
section(s,'Pump operating point and electrical power','Δppump = Δp0 N² − aV̇² = Δpsystem        Pe = Δp V̇ / η',105);
text(s,'Fixed-flow mode evaluates the head required. Pump mode solves the curve intersection.',44,189,868,31,20,red);
section(s,'Facility water removes the rack heat','Q̇HX = Σ Q̇i = ṁFWS [h(TFWS,out) − h(TFWS,in)]',240);
section(s,'Heat-exchanger conductance required','UArequired = Q̇HX / ΔTlm        ΔTlm = (ΔT1 − ΔT2) / ln(ΔT1/ΔT2)',347);
}
// 11 native chart
const data=JSON.parse(await fs.readFile(tmp+'/results.json','utf8'));
{
const s=slide('Flow Redistribution Matches Cooling Demand',[7],'Fresh solve on 15 September 2026. Chart values are the arithmetic mean per tray class, in inlet-reference L/min. This is a comparison at the same total 120 L/min. The class means hide within-class variation, so the next slide includes a 27-tray RMS metric.');
const mean=(key,kind)=>{let t=data[key].trays.filter(t=>t.tray_type===kind);return Number((t.reduce((a,t)=>a+t.actual_flow_LPM,0)/t.length).toFixed(2));};
const ch=s.charts.add('bar',{position:{left:55,top:126,width:600,height:299},categories:['Compute tray','Switch tray'],series:[{name:'Target',values:[6.02,1.29],fill:'#7F858C'},{name:'Reference',values:[mean('reference','compute'),mean('reference','switch')],fill:'#95001A'},{name:'Balanced',values:[mean('balanced','compute'),mean('balanced','switch')],fill:'#245F9C'}],barOptions:{direction:'column',grouping:'clustered'},hasLegend:true,dataLabels:{showValue:true,position:'outEnd',textStyle:{fontSize:17,bold:true}},xAxis:{textStyle:{fontSize:17}},yAxis:{title:{text:'Flow per tray (L/min)',textStyle:{fontSize:17}},numberFormatCode:'0.0',textStyle:{fontSize:15}},legend:{position:'bottom',textStyle:{fontSize:17}}});applyPresentationChartFont(ch,{fontFamily:'Arial'});
text(s,'Same total flow',685,131,240,33,25,blue,true);text(s,'Restricting over-supplied switch branches redirects coolant to compute trays.',685,181,228,111,22);
text(s,'Equal flow is not the objective: the modeled compute heat load is 4.68× larger.',685,327,232,106,22,red);
}
// 12
{
const a=data.reference.metrics,b=data.balanced.metrics;
const s=slide('Better Distribution Requires More Pumping',[7],'Recalculated from baseline.yaml and optimized_example.yaml. Balanced design retains 38 mm constant headers, compute added Kh = 0 and switch added Kh = 180528785.8784 Pa/(kg/s)^2. Pump efficiency is 0.60. Results are modeled, not hardware measurements or a proven global optimum. Legacy PG25 properties and fixed component resistance coefficients reproduce the earlier study.');
table(s,[['Metric','Reference','Balanced'],['RMS flow-target error','73.49%','0.44%'],['Maximum tray outlet','55.97 °C','53.80 °C'],['Tray outlet temperature spread','9.90 K','0.21 K'],['Required system pressure','79.83 kPa','105.09 kPa'],['Modeled pump electrical power','266.1 W','350.3 W'],['Mixed rack return temperature','53.73 °C','53.73 °C']],42,106,875,302,[427,224,224],21);
text(s,'Maximum outlet falls 2.17 K; pumping rises 84.2 W (+31.6%).',43,416,870,31,22,red,true);
text(s,'Heat and total flow are unchanged, so the mixed return stays the same.',43,442,870,25,17);
}
// 13
{
const s=slide('Existing Code and Data to Reuse',[5,6,7],'Existing code requirement: the repository already calls SciPy least_squares for hydraulic closure; it is not a solver written from scratch. CoolProp is a proposed independent property cross-check and is not the current runtime property engine. Its fluid-specific composition convention must be respected.');
table(s,[['Resource','Role','Status'],['SciPy least_squares [6]','Solve nonlinear hydraulic residuals with bounds','Already used'],['Project Python model [7]','Network, coolant properties, sweeps, constraints, Streamlit','Already implemented'],['CoolProp INCOMP database [5]','Independent water/glycol property check','Proposed cross-check']],42,113,875,239,[260,411,204],21);
text(s,'Calculation workflow',44,375,850,31,24,blue,true);
text(s,'Solve flows and temperatures, update properties, and iterate.\nThen check constraints and compare designs.',44,408,865,58,20);
}
// 14
{
const s=slide('Checks Needed Before Choosing Hardware',[7],'Recalculated numerical closure for both cases: mass relative error ≤ 2.18e-16; energy relative error ≤ 2.40e-15; pressure residual ≤ 4.37e-11 Pa. These show numerical closure only. Review properties, chip thermal resistance, QD curves, and actual pump/HX maps. Do not treat the 80 °C assumed target as an NVIDIA throttling threshold.');
section(s,'Numerical checks passed','Both example cases converge and satisfy mass, energy, and pressure closure.',110);
section(s,'Validate the inputs that drive the answer','Measure tray/QD pressure–flow curves and orifice discharge behavior. Obtain chip limits, thermal resistance, and facility/CDU performance maps.',217);
section(s,'Test fixed hardware across operating conditions','Sweep flow, workload split, coolant, and inlet temperature. Include bore tolerances, partial blockage, and reduced pump capability.',350);
text(s,'The 1D model omits 3D tee momentum recovery. Verify header-shape benefits with CFD.',44,436,865,26,17,red);
}
// 15 references
{
const s=slide('References and Calculation Record');
const refs=[
'[1] Sogunuru et al. (2020). Patterned flow distribution through manifolds in electronics cooling. IJMPERD 10(2), 975–986. Selected calculation baseline.',
'[2] Hassan et al. (2014). Modeling the Uniformity of Manifold with Various Configurations. Journal of Fluids. doi:10.1155/2014/325259.',
'[3] Anbumeenakshi & Thansekhar (2016). Header shape and inlet configuration in microchannels. Experimental Thermal and Fluid Science 75, 156–161. doi:10.1016/j.expthermflusci.2016.02.004.',
'[4] NVIDIA DGX GB Rack Scale Systems User Guide: Hardware.',
'[5] CoolProp: Incompressible Fluids database and documentation.',
'[6] SciPy: scipy.optimize.least_squares documentation.',
'[7] NVL72-Manifold-Optimization repository. Matched reference and balanced runs recalculated on 15 September 2026. Full source links and details are in slide notes.'
];
let y=108;for(let i=0;i<refs.length;i++){let h=[52,52,72,31,31,31,55][i];text(s,refs[i],45,y,870,h,18);y+=h+3;}
s.speakerNotes.textFrame.setText(Object.entries(sources).map(([i,v])=>'['+i+'] '+v).join('\n\n')+'\n\nAssignment coverage: three previous works (3), selected baseline (4), physical changes with circles/arrows (5), governing equations (8–10), existing code/database (13). No contribution hours are invented.');
}
await (await PresentationFile.exportPptx(p)).save(tmp+'/candidate.pptx');
const final=wd+'/deliverables/Rack_Manifold_Optimization_MEAM5020_Reviewed.pptx';
const result=await finalizePresentation({workspaceDir:wd,candidatePath:tmp+'/candidate.pptx',finalPath:final,pythonExecutable:py,integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','9144000,5143500','--validate-heading-fit',...[3,4,6,7,12,13].flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:[3,4,6,7,12,13],requiredNativeChartOwnerSlides:[11],materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'reference',families:['GillSans','Arial'],referencePath:pdf,referenceSha256:crypto.createHash('sha256').update(await fs.readFile(pdf)).digest('hex')},verifyArtifactToolImport:true,receiptPath:tmp+'/validation-reviewed.json'});
console.log(JSON.stringify(result));
