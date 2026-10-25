"""Generate a self-contained interactive HTML preview using the same CSV as app.py."""
import csv,json,html
from pathlib import Path
from plotly.offline.offline import get_plotlyjs
root=Path(__file__).resolve().parent
rows=list(csv.DictReader((root/'data/london_dwelling_stock_2012_2025.csv').open()))
values=[]
for r in rows:
    values.append({k:(int(v) if k not in ('code','borough') else v) for k,v in r.items()})
html_doc=r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>London housing capacity | Interactive first-run preview</title>
<style>
:root{--ink:#192c4a;--muted:#66758d;--line:#e8edf5;--nav:#f6f8fd;--blue:#2563eb}
*{box-sizing:border-box}body{background:#f8fafd;color:var(--ink);font-family:Inter,system-ui,-apple-system,'Segoe UI',Arial,sans-serif;margin:0}
.page{max-width:1300px;padding:35px 28px 70px;margin:auto}.eyebrow{letter-spacing:.13em;text-transform:uppercase;font-size:11px;font-weight:800;color:#5f79ae}
h1{font-size:clamp(30px,4vw,44px);margin:10px 0 12px;font-weight:770;letter-spacing:-.04em}
.lead{max-width:910px;font-size:16px;line-height:1.6;color:#5b6a82;margin-bottom:21px}
.filters{display:flex;gap:18px;align-items:center;flex-wrap:wrap;margin:21px 0 24px;border:1px solid var(--line);background:white;padding:15px 18px;border-radius:13px}
.filters label{font-size:12px;color:#66758d;font-weight:680;display:block;margin-bottom:5px}
select{appearance:auto;border:1px solid #d5dfec;background:white;border-radius:8px;padding:9px 12px;min-width:210px;color:var(--ink);font-size:14px}
.stat-row{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.stat{border:1px solid #e3e9f2;border-radius:13px;padding:19px 18px;background:white;min-height:122px;box-shadow:0 1px 2px #162b3e08}
.stat .lbl{font-size:12px;font-weight:600;color:#65758e;margin-bottom:14px}.stat .val{font-size:clamp(18px,2.0vw,29px);font-weight:760;letter-spacing:-.035em;color:#17294a;word-break:break-word}
.stat .hint{font-size:11px;color:#78849b;margin-top:7px}
.section{margin-top:35px}.secnum{letter-spacing:.10em;font-size:10px;font-weight:800;color:#627cb4;text-transform:uppercase}
h2{font-size:22px;margin:7px 0;font-weight:750;letter-spacing:-.025em}.sub{color:#6a7690;margin:0 0 16px;font-size:13px;line-height:1.6}
.panel{background:white;border:1px solid var(--line);border-radius:13px;padding:14px 18px;box-shadow:0 2px 6px #182b4410}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}.data-table{padding:24px 18px}
.data-table h3{font-size:17px;margin:0 0 16px}.tenure-row{display:grid;grid-template-columns:1fr auto auto;gap:14px;align-items:center;margin:13px 0;padding:10px 0;border-bottom:1px solid #eef2f6;font-size:13px}
.small{color:#65758e;font-size:12px;line-height:1.6}.note{border-left:3px solid #9bbbec;padding:12px 16px;background:#f3f7fd;border-radius:3px;font-size:12px;color:#4d607e;line-height:1.6}
.map-controls{display:flex;flex-wrap:wrap;gap:9px;align-items:center;margin-bottom:12px}.map-controls button,.map-controls label{border:1px solid #cfdcef;border-radius:8px;background:#f6faff;padding:9px 12px;color:#173963;font-size:12px;font-weight:650;cursor:pointer}.map-controls input{display:none}.footer{padding-top:25px;color:#7c8ba0;font-size:12px;line-height:1.7}.map-placeholder{min-height:128px;display:flex;justify-content:center;align-items:center;text-align:center;color:#7587a2;font-size:13px}
@media(max-width:900px){.stat-row{grid-template-columns:repeat(2,1fr)}.grid2{grid-template-columns:1fr}.page{padding:22px 15px}.stat .val{font-size:22px}}
@media(max-width:480px){.stat-row{grid-template-columns:1fr}.filters{align-items:stretch}.filters>div,select{width:100%}}
</style>
<script>__PLOTLY_JS__</script></head>
<body><main class="page">
<div class="eyebrow">Objective 01 · Baseline supply</div>
<h1>London housing capacity</h1>
<div class="lead">How many homes already exist across London — and how do they differ by borough, provider category and over time? <b>Current housing capacity means existing dwelling stock</b> in this project.</div>
<div class="filters"><div><label for="year">Reference year</label><select id="year"></select></div><div><label for="borough">Geography</label><select id="borough"></select></div><div class="small">Source: government Table 100<br>32 boroughs + City of London · 2025 provisional</div></div>
<div class="stat-row">
<div class="stat"><div id="k1label" class="lbl">Total dwellings</div><div id="k1value" class="val">—</div><div id="k1hint" class="hint">Existing homes</div></div>
<div class="stat"><div id="k2label" class="lbl">Largest stock</div><div id="k2value" class="val">—</div><div id="k2hint" class="hint"></div></div>
<div class="stat"><div id="k3label" class="lbl">Smallest stock</div><div id="k3value" class="val">—</div><div id="k3hint" class="hint"></div></div>
<div class="stat"><div class="lbl">Change since 2012</div><div id="k4value" class="val">—</div><div id="k4hint" class="hint"></div></div>
</div>
<section class="section"><div class="secnum">View 01</div><h2>Compare the boroughs</h2><p class="sub">London's 33 local authorities ranked by the total number of existing dwellings. Select a borough above to highlight it.</p><div class="panel"><div id="ranking" style="height:810px"></div></div></section>
<section class="section"><div class="secnum">View 02</div><h2>What makes up the housing stock?</h2><p class="sub" id="tenuretitle">Existing dwellings by their government's recorded provider category.</p><div class="grid2"><div class="panel"><div id="tenure" style="height:360px"></div></div><div class="panel data-table"><h3>Dwellings by provider category</h3><div id="tenuretable"></div><div class="note" style="margin-top:20px">Private sector includes owner-occupied and privately rented dwellings. The source does not distinguish between them.</div></div></div></section>
<section class="section"><div class="secnum">View 03</div><h2>How has stock changed?</h2><p class="sub">A historical view of the same measure, using the 2012–2025 extracts.</p><div class="panel"><div id="trend" style="height:370px"></div></div><div class="small" style="padding:8px 4px">Historical stock estimates may be revised. Changes do not necessarily equal net new housebuilding.</div></section>
<section class="section"><div class="secnum">View 04</div><h2>Where is existing stock concentrated?</h2><p class="sub">Total existing dwellings in each borough. Darker areas mean more dwellings, not greater housing density. Change the year or borough above to update the map.</p><div class="panel"><div class="map-controls"><button id="retryMap" type="button">Retry official boundaries</button><label for="mapUpload">Or select borough GeoJSON <input type="file" id="mapUpload" accept=".geojson,.json,application/json"/></label><span class="small" id="mapStatus">Loading borough outlines…</span></div><div id="map" style="height:570px"></div></div><div class="small" style="padding:8px 4px">Geometry source: GLA / Ordnance Survey Open Data, OGL v3. The standalone HTML preview may require internet access to retrieve the boundaries. In the Streamlit project, a successful download is cached for subsequent offline use.</div></section>
<div class="footer">Interactive browser preview generated from your government Table 100 data. 2022–2025 figures are provisional; 2024 was revised. This view describes existing dwellings, not empty homes, homelessness, affordability, available housing or future build capacity.<br>
Source: <a href="https://www.gov.uk/government/statistical-data-sets/live-tables-on-dwelling-stock-including-vacants">MHCLG Table 100</a>.</div>
</main><script>
const rows=__DATA_JSON__;
const tenure=[['local_authority','Local authority','#2563eb'],['housing_association','Housing association','#0e9990'],['other_public','Other public sector','#e3a35b'],['private_sector','Private sector','#8474c7']];
const fmt=n=>Math.round(n).toLocaleString('en-GB');
const sum=(a,key)=>a.reduce((t,r)=>t+Number(r[key]||0),0);
const boroughs=[...new Set(rows.map(r=>r.borough))].sort();
const yEl=document.getElementById('year'),bEl=document.getElementById('borough');
const charts={responsive:true,displayModeBar:false};
let boundaryData=null;
const boundaryUrl='https://gis.london.gov.uk/arcgis/rest/services/apps/cultural_infrastructure_map_context_layers/MapServer/2/query?where=1%3D1&outFields=name%2Cgss_code&returnGeometry=true&outSR=4326&geometryPrecision=5&f=geojson';
const status=document.getElementById('mapStatus');
function validateBoundaryData(geo) {
 const codes=new Set(rows.filter(r=>r.year===2025).map(r=>r.code));
 if(!geo||geo.type!=='FeatureCollection'||!Array.isArray(geo.features)) throw new Error('Expected GeoJSON FeatureCollection');
 const found=new Set();
 for(const f of geo.features){const p=f.properties||{};const code=p.gss_code||p.GSS_CODE; if(!codes.has(code))continue;
  if(!f.geometry || !['Polygon','MultiPolygon'].includes(f.geometry.type)) throw new Error('Polygon geometry missing');
  if(found.has(code))throw new Error('Duplicate '+code);found.add(code);p.gss_code=code;}
 if(found.size!==33)throw new Error('Only '+found.size+'/33 London borough boundaries matched');
 return geo;
}
async function fetchBoundaries(){
 status.textContent='Loading official GLA boundaries…';
 try{ const res=await fetch(boundaryUrl);if(!res.ok)throw new Error('HTTP '+res.status);boundaryData=validateBoundaryData(await res.json());
 status.textContent='33 borough boundaries loaded · GLA';update();
 } catch(err) {status.textContent='Unable to load boundaries in this browser ('+err.message+'). Use the GeoJSON file picker or open the Streamlit app.';}
}
document.getElementById('retryMap').onclick=fetchBoundaries;
document.getElementById('mapUpload').onchange=async ev=>{
 const file=ev.target.files[0];if(!file)return;
 try{boundaryData=validateBoundaryData(JSON.parse(await file.text()));status.textContent='33 matching borough boundaries loaded from file';update();}
 catch(err){status.textContent='Invalid GeoJSON: '+err.message;}
};
function mapView(current,borough){
 if(!boundaryData)return;
 const londonTotal=sum(current,'total_dwellings');
 const main={type:'choropleth',geojson:boundaryData,locations:current.map(r=>r.code),z:current.map(r=>r.total_dwellings),
   featureidkey:'properties.gss_code',colorscale:[[0,'#e8f4fa'],[.2,'#a9d7e8'],[.45,'#63b0d2'],[.7,'#236eae'],[1,'#123a72']],
   marker:{line:{color:'#ffffff',width:0.9}},colorbar:{title:'Dwellings',thickness:15,len:.78},
   customdata:current.map(r=>[r.borough,100*r.total_dwellings/londonTotal]),
   hovertemplate:'<b>%{customdata[0]}</b><br>Total dwellings: %{z:,.0f}<br>Share of London: %{customdata[1]:.2f}%<extra></extra>'};
 const traces=[main];
 if(borough!=='All London'){
  const focus=current.find(r=>r.borough===borough);
  if(focus)traces.push({type:'choropleth',geojson:boundaryData,locations:[focus.code],z:[1],
   featureidkey:'properties.gss_code',colorscale:[[0,'rgba(0,0,0,0)'],[1,'rgba(0,0,0,0)']],showscale:false,
   marker:{line:{color:'#ec8122',width:3.1}},hoverinfo:'skip'});
 }
 Plotly.react('map',traces,{...theme,height:570,geo:{fitbounds:'locations',visible:false,projection:{type:'mercator'}},
    margin:{l:8,r:60,t:4,b:5},showlegend:false},charts);
}

const theme={font:{family:'Inter, Arial, sans-serif',color:'#17294a',size:12},paper_bgcolor:'white',plot_bgcolor:'white',margin:{l:12,r:14,t:10,b:32}};
for(const year of [...new Set(rows.map(r=>r.year))].sort((a,b)=>b-a))yEl.add(new Option(year,year));
bEl.add(new Option('All London','All London'));
for(const borough of boroughs)bEl.add(new Option(borough,borough));
function update(){
const year=Number(yEl.value), borough=bEl.value;
const current=rows.filter(r=>r.year===year).sort((a,b)=>b.total_dwellings-a.total_dwellings);
const inScope=borough==='All London'?current:current.filter(r=>r.borough===borough);
const total=sum(current,'total_dwellings'),value=sum(inScope,'total_dwellings');
const past=rows.filter(r=>r.year===2012&&(borough==='All London'||r.borough===borough));
const old=sum(past,'total_dwellings');
const change=(value/old-1)*100;
mapView(current,borough);
function set(k,v){document.getElementById(k).textContent=v}
if(borough==='All London'){
set('k1label','Total existing dwellings');set('k1value',fmt(total));set('k1hint','Across 33 local authorities');
set('k2label','Largest stock');set('k2value',current[0].borough);set('k2hint',fmt(current[0].total_dwellings)+' dwellings');
set('k3label','Smallest stock');set('k3value',current.at(-1).borough);set('k3hint',fmt(current.at(-1).total_dwellings)+' dwellings');
}else{
set('k1label','Dwellings in '+borough);set('k1value',fmt(value));set('k1hint','Existing dwellings');
set('k2label','Share of London total');set('k2value',(100*value/total).toFixed(1)+'%');set('k2hint','In reference year '+year);
set('k3label','Rank by total dwellings');set('k3value','#'+(current.findIndex(r=>r.borough===borough)+1)+' of 33');set('k3hint','Ranked from highest to lowest');
}
set('k4value',(change>0?'+':'')+change.toFixed(1)+'%');set('k4hint',(value-old>0?'+':'')+fmt(value-old)+' dwellings');
const reversed=[...current].reverse();
Plotly.react('ranking',[{type:'bar',orientation:'h',x:reversed.map(r=>r.total_dwellings),y:reversed.map(r=>r.borough),marker:{color:reversed.map(r=>r.borough===borough?'#2563eb':'#95b7e0')},hovertemplate:'<b>%{y}</b><br>%{x:,.0f} dwellings<extra></extra>'}],
 {...theme,height:810,xaxis:{title:'Existing dwellings',gridcolor:'#eef2f6',tickformat:','},yaxis:{automargin:true,tickfont:{size:10}},showlegend:false,margin:{l:135,r:18,t:10,b:50}},charts);
const labels=tenure.map(t=>t[1]),vals=tenure.map(t=>sum(inScope,t[0]));
Plotly.react('tenure',[{type:'pie',labels:labels,values:vals,hole:.65,sort:false,marker:{colors:tenure.map(t=>t[2])},textinfo:'percent',textposition:'outside',hovertemplate:'<b>%{label}</b><br>%{value:,.0f} dwellings<extra></extra>'}],
 {...theme,height:360,margin:{l:20,r:20,t:14,b:65},legend:{orientation:'h',x:.5,xanchor:'center',y:-.1},annotations:[{x:.5,y:.5,text:'<b>'+fmt(value)+'</b>',showarrow:false,font:{size:21}}]},charts);
set('tenuretitle','Existing stock by recorded provider category · '+(borough==='All London'?'All London':borough)+' · '+year);
const d=document.getElementById('tenuretable');d.innerHTML='';
for(let i=0;i<tenure.length;i++){
const item=document.createElement('div');item.className='tenure-row';
const n=document.createElement('span');n.textContent=labels[i];
const count=document.createElement('b');count.textContent=fmt(vals[i]);
const share=document.createElement('span');share.textContent=(vals[i]*100/value).toFixed(1)+'%';share.style.color='#65758e';
item.append(n,count,share);d.append(item)
}
const trend=rows.filter(r=>borough==='All London'||r.borough===borough);
const byYear=[...new Set(trend.map(r=>r.year))].sort((a,b)=>a-b);
const ys=byYear.map(y=>sum(trend.filter(r=>r.year===y),'total_dwellings'));
Plotly.react('trend',[{type:'scatter',mode:'lines+markers',x:byYear,y:ys,line:{color:'#2563eb',width:3},marker:{size:7,color:'#2563eb'},hovertemplate:'%{x}: %{y:,.0f} dwellings<extra></extra>'}],
 {...theme,height:370,xaxis:{title:'Year',gridcolor:'#f1f4f8',dtick:2},yaxis:{title:'Dwellings',tickformat:',',gridcolor:'#edf1f6'},margin:{l:75,r:25,t:20,b:50}},charts)
}
yEl.onchange=update;bEl.onchange=update;update();fetchBoundaries();
</script></body></html>'''
html_doc=html_doc.replace('__PLOTLY_JS__',get_plotlyjs()).replace('__DATA_JSON__',json.dumps(values,separators=(',',':')))
p=root/'dashboard_preview.html'
p.write_text(html_doc,encoding='utf-8')
print('Created',p,'size',p.stat().st_size)
