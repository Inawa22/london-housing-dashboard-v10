"""Extract published London regional (not borough) overcrowding series from GLA Housing in London 2025 table 4.9.
These values cannot substitute for borough-level ONS Census 2021 TS052 figures.
"""
import csv,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'data'/'sources'/'Housing_in_London_2025.xlsx'
N={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(p) as z:
 root=ET.fromstring(z.read('xl/worksheets/sheet48.xml'))
 shared=[]
 if 'xl/sharedStrings.xml' in z.namelist():
  sr=ET.fromstring(z.read('xl/sharedStrings.xml'))
  shared=[''.join(e.itertext()) for e in sr.findall('m:si',N)]
 records=[]
 for row in root.findall('.//m:sheetData/m:row',N):
  d={}
  for c in row.findall('m:c',N):
   v=c.find('m:v',N)
   if v is None:continue
   val=v.text or ''
   if c.get('t')=='s':val=shared[int(val)]
   key=''.join(x for x in c.get('r','') if x.isalpha())
   d[key]=val
  if d.get('B','').strip()=='London' and d.get('C','') in ('All tenures','Owners','Private renters','Social sector'):
   try:
    year=int(float(d['A']));rate=float(d['D'])
   except(ValueError,KeyError):continue
   if 1994<=year<=2024 and 0<=rate<=1:
    records.append(dict(year=year,tenure=d['C'],overcrowding_pct=round(rate*100,3)))
assert len(records)>=75, len(records)
with open(ROOT/'data'/'london_overcrowding_ehs_gla.csv','w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
print('Extracted',len(records),'regional tenure-year records, years',min(x['year'] for x in records),max(x['year'] for x in records),'latest', [x for x in records if x['year']==max(x['year'] for x in records) and x['tenure']=='All tenures'])
