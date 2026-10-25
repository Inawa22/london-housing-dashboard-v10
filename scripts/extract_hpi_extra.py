"""Extract published HPI London property-type prices and borough total sales volumes.
Uses the user's UK House Price Index.xlsx. Do NOT interpret prices as sales counts.
"""
from pathlib import Path
from datetime import datetime, timedelta
import csv
from artifact_tool import Blob, SpreadsheetFile

base=Path(__file__).resolve().parents[1]
source=base/'data'/'sources'/'UK_House_Price_Index.xlsx'
if not source.exists():
    source=Path('/mnt/data/UK House price index.xlsx')
w=SpreadsheetFile.import_xlsx(Blob.load(str(source)))

# London By type worksheet records prices in columns C:F; year specified in January.
s=w.worksheets.get_item('By type')
raw=s.get_range('A1:F383').values
rows=[]; yr=None
months={'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
for r in raw[4:]:
    if isinstance(r[0],(float,int)) and 1990<=r[0]<=2030:yr=int(r[0])
    m=months.get(str(r[1]).strip()[:3]);
    if m and yr:
        for i,label in enumerate(['Detached','Semi-detached','Terraced','Flat / maisonette'],start=2):
            value=r[i]
            if isinstance(value,(int,float)) and value>0:rows.append({'date':f'{yr}-{m:02d}-01','area':'London','type':label,'average_price_gbp':round(float(value),2),'source':'UK House Price Index, By type worksheet'})
with (base/'data'/'london_purchase_prices_by_type.csv').open('w',newline='',encoding='utf-8') as f:
    dw=csv.DictWriter(f,fieldnames=['date','area','type','average_price_gbp','source']);dw.writeheader();dw.writerows(rows)
print('London by type records:',len(rows),'last',rows[-4:])
# 'Sales Volume' worksheet provides borough-level total transactions; not per type.
s=w.worksheets.get_item('Sales Volume')
raw=s.get_range('A1:AW379').values
codes=raw[1]
areas=raw[0]
rows=[]
for r in raw[2:]:
    v=r[0]
    if not isinstance(v,(int,float)):continue
    date=(datetime(1899,12,30)+timedelta(days=float(v))).strftime('%Y-%m-%d')
    for j,code in enumerate(codes[1:],start=1):
        if isinstance(code,str) and code.startswith('E09') and isinstance(r[j],(int,float)) and r[j]>=0:
            rows.append({'date':date,'code':code,'borough':areas[j],'sales':round(float(r[j])),'source':'UK House Price Index, Sales Volume worksheet'})
with (base/'data'/'borough_sales_volume.csv').open('w',newline='',encoding='utf-8') as f:
    dw=csv.DictWriter(f,fieldnames=['date','code','borough','sales','source']);dw.writeheader();dw.writerows(rows)
print('Sales volume records:',len(rows),'last',rows[-4:])
