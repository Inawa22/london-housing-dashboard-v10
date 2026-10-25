"""Reproducible extraction from user-provided government/CHAIN ODS workbooks.
Only standard-library XML processing; no fabricated or inferred source values.
Missing source cells ('..', 'z', ':', blanks) remain missing, NOT zero.
Statutory reports are quarterly household flows (A1) / period-end stock (TA1).
CHAIN P1 counts distinct people seen during a quarter, not households.
"""
from __future__ import annotations
import csv
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data'/'sources'
DATA=ROOT/'data'
NS={'table':'urn:oasis:names:tc:opendocument:xmlns:table:1.0','text':'urn:oasis:names:tc:opendocument:xmlns:text:1.0','office':'urn:oasis:names:tc:opendocument:xmlns:office:1.0'}
STAT_FILES={
 '2025 Q1':'Detailed_LA_202503.ods',
 '2025 Q2':'Statutory_Homelessness_Detailed_Local_Authority_Data_202506_corrected.ods',
 '2025 Q3':'Statutory_Homelessness_Detailed_Local_Authority_Data_202509.ods',
 '2025 Q4':'Statutory_Homelessness_Detailed_Local_Authority_Data_202512.ods',
}
CHAIN_FILE='CHAIN quarterly data tables 2026-27 Q1 (P2 Number of people seen rough sleeping in London, by area, 202021 to 202425).ods'
STAT_SOURCE_URL='https://www.gov.uk/government/collections/homelessness-statistics'
CHAIN_SOURCE_URL='https://data.london.gov.uk/dataset/chain-reports'

def read_sheets(path,selected):
 with zipfile.ZipFile(path) as z:
  root=ET.fromstring(z.read('content.xml'))
  for t in root.findall('.//table:table',NS):
   name=t.get('{%s}name'%NS['table'])
   if name not in selected:continue
   rows=[]
   for r in t.findall('table:table-row',NS):
    vals=[]
    for c in r.findall('table:table-cell',NS):
     repeat=int(c.get('{%s}number-columns-repeated'%NS['table'],'1'))
     value=c.get('{%s}value'%NS['office'])
     if value is None:value=' '.join(''.join(p.itertext()) for p in c.findall('text:p',NS)).strip()
     vals.extend([str(value).strip()]*min(repeat,140))
     if len(vals)>160:break
    rows.append(vals)
   yield name,rows

def at(r,i):return r[i] if i<len(r) else ''
def number(value):
 t=str(value or '').strip().replace(',','')
 if t in ('','..',':','z','-','[x]','[z]','c','u','n/a','Not available'):return ''
 try:return round(float(t),5)
 except (ValueError,TypeError):return ''

def write_csv(path,rows,columns):
 with open(path,'w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');w.writeheader();w.writerows(rows)

def main():
 rows=[]; reasons=[]
 reason_fields={6:'End of assured shorthold private tenancy',26:'End of other private tenancy',27:'Family/friends cannot accommodate',28:'Non-violent partner relationship breakdown',30:'Domestic abuse',35:'Other violence or harassment',37:'End of social rented tenancy',42:'Eviction from supported housing',47:'Left institution without accommodation',54:'Home Office asylum support ended',55:'Home unsuitable due to disability/ill health',56:'Resettlement placement ended',57:'Other / unknown reasons'}
 for quarter,filename in STAT_FILES.items():
  tables=dict(read_sheets(SOURCE/filename,{'A1','TA1','A2P','A2R'}))
  tables={key:{at(r,0):r for r in v if re.fullmatch(r'E09\d{6}|E12000007',at(r,0))} for key,v in tables.items()}
  codes=sorted(set().union(*(x.keys() for x in tables.values())))
  assert len([k for k in codes if k.startswith('E09')])==33,(quarter,len(codes))
  for code in codes:
   a=tables['A1'].get(code,[]); ta=tables['TA1'].get(code,[])
   borough=at(a,1) or at(ta,1)
   rows.append(dict(period=quarter,code=code,borough=borough,level='London' if code=='E12000007' else 'Borough',
     assessed_total=number(at(a,4)),owed_duty=number(at(a,6)),prevention=number(at(a,7)),relief=number(at(a,9)),
     ta_households=number(at(ta,4)),ta_rate_1000=number(at(ta,6)),households_in_area_thousands=number(at(ta,5)),
     ta_households_children=number(at(ta,7)),ta_children=number(at(ta,8)),
     ta_bed_breakfast=number(at(ta,10)),ta_nightly_private=number(at(ta,16)),ta_hostel_refuge=number(at(ta,19)),
     ta_private_leased=number(at(ta,22)),ta_social_stock=number(at(ta,25)),ta_other=number(at(ta,28)),
     ta_outside_authority=number(at(ta,31)),source_file=filename,source_url=STAT_SOURCE_URL))
   for duty,sheet in [('Prevention','A2P'),('Relief','A2R')]:
    sr=tables[sheet].get(code,[])
    for col,label in reason_fields.items():
     reasons.append(dict(period=quarter,code=code,borough=borough,level='London' if code=='E12000007' else 'Borough',
      duty=duty,reason=label,households=number(at(sr,col)),source_file=filename))
 write_csv(DATA/'statutory_homelessness_2025.csv',rows,list(rows[0]))
 write_csv(DATA/'homelessness_reasons_2025.csv',reasons,list(reasons[0]))
 chain=[]
 for name,records in read_sheets(SOURCE/CHAIN_FILE,{'P1'}):
  headers=records[1]
  for rec in records[2:]:
   code=at(rec,1);borough=at(rec,0)
   if not re.fullmatch(r'E09\d{6}|E12000007',code):continue
   for idx in range(2,10):
    val=number(at(rec,idx))
    chain.append(dict(period=at(headers,idx),code=code,borough=borough,level='London' if code=='E12000007' else 'Borough',
       people_seen=val,source_file=CHAIN_FILE,source_url=CHAIN_SOURCE_URL))
 assert len([x for x in chain if x['code']=='E12000007'])==8
 write_csv(DATA/'chain_rough_sleeping.csv',chain,list(chain[0]))
 latest=next(r for r in rows if r['period']=='2025 Q4' and r['code']=='E12000007')
 recent_chain=next(r for r in chain if r['period']=='2026-27 Q1' and r['code']=='E12000007')
 assert int(latest['owed_duty'])==16290 and int(latest['ta_households'])==75600 and int(latest['ta_children'])==100930
 assert int(recent_chain['people_seen'])==3959
 print('Extracted',len(rows),'statutory rows,',len(reasons),'reason rows,',len(chain),'CHAIN rows.')
 print('Q4 London published:', {k:latest[k] for k in ('owed_duty','prevention','relief','ta_households','ta_children','ta_rate_1000')})
 for q in STAT_FILES:
  miss=[r['borough'] for r in rows if r['period']==q and r['level']=='Borough' and r['ta_households']=='']
  print(q, 'TA missing',len(miss),miss)
if __name__=='__main__':main()
