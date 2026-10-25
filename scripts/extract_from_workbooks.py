"""One-time source extraction from the two uploaded official housing-price workbooks.
Reads OOXML using stdlib (no extra Excel dependency)."""
from pathlib import Path
import csv, zipfile, re, datetime, xml.etree.ElementTree as ET, collections, json
BASE=Path(__file__).resolve().parents[1] / 'data' / 'raw'; OUT=BASE.parent; OUT.mkdir(exist_ok=True)
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main';q=lambda n:f'{{{NS}}}{n}'
def col_number(cell):
    m=re.match(r'^([A-Z]+)',cell); n=0
    for ch in m.group(1):n=n*26+ord(ch)-64
    return n
def cells_in_row(row,shared):
    d={}
    for c in row.findall(q('c')):
        v=c.find(q('v'))
        if v is None: continue
        t=v.text or ''
        if c.get('t')=='s': t=shared[int(t)]
        d[col_number(c.get('r'))]=t
    return d
def shared_strings(z):
    out=[]
    for event,el in ET.iterparse(z.open('xl/sharedStrings.xml'),events=('end',)):
        if el.tag==q('si'):
            out.append(''.join(t.text or '' for t in el.iter(q('t'))));el.clear()
    return out
def rows_for_sheet(z,n,shared):
    with z.open(f'xl/worksheets/sheet{n}.xml') as fh:
        for _,el in ET.iterparse(fh,events=('end',)):
            if el.tag==q('row'):
                ix=int(el.get('r')); values=cells_in_row(el,shared)
                yield ix,values
                el.clear()
def dt(num):return (datetime.datetime(1899,12,30)+datetime.timedelta(days=float(num))).date().isoformat()
def value(d,i):
    v=d.get(i)
    if not v or v in ('[x]','[z]','-'):return ''
    try:return float(v)
    except: return ''
# HPI
infile=BASE/'UK House price index.xlsx'
with zipfile.ZipFile(infile) as z:
    ss=shared_strings(z)
    it=rows_for_sheet(z,3,ss)
    head=next(it)[1]; codes=next(it)[1]
    locations={col:(head[col],code) for col,code in codes.items() if col>=2 and isinstance(code,str) and (code.startswith('E09') or code=='E12000007')}
    print('HPI borough columns',len(locations),'example',list(locations.items())[:2])
    records=[]
    for ix,d in it:
        if 1 not in d:continue
        date=dt(d[1])
        for col,(name,code) in locations.items():
            price=value(d,col)
            if price!='':records.append([date,code,name,round(price,2)])
    with (OUT/'house_prices.csv').open('w',newline='') as fp:
        w=csv.writer(fp);w.writerow(['date','code','borough','average_price_gbp']);w.writerows(records)
    print('HPI',len(records),'from',min(r[0] for r in records),'to',max(r[0] for r in records),'unique',len(set(r[1] for r in records)))
# Rental PIPR
infile=BASE/'priceindexofprivaterentsukmonthlypricestatistics.xlsx'
with zipfile.ZipFile(infile) as z:
    ss=shared_strings(z)
    wanted={5:'rent_index',7:'rent_annual_change_pct',8:'rent_gbp',12:'rent_1bed_gbp',16:'rent_2bed_gbp',20:'rent_3bed_gbp',24:'rent_4plus_gbp',28:'rent_detached_gbp',32:'rent_semi_gbp',36:'rent_terraced_gbp',40:'rent_flat_gbp'}
    records=[]; seen=collections.Counter()
    for ix,d in rows_for_sheet(z,4,ss):
        if ix <=3:continue
        code=d.get(2,'');
        if not (code.startswith('E09') or code=='E12000007'):continue
        rec=[dt(d[1]),code,d.get(3,''),d.get(4,'')]+[value(d,j) for j in wanted]
        records.append(rec);seen[code]+=1
    with (OUT/'private_rents.csv').open('w',newline='') as fp:
        w=csv.writer(fp);w.writerow(['date','code','borough','region']+list(wanted.values()));w.writerows(records)
    print('RENT',len(records),'from',min(r[0] for r in records),'to',max(r[0] for r in records),'unique',len(seen))
    print('Rent count and last:',sorted(seen.items())[:5]);print('Latest London:',[r for r in records if r[1]=='E12000007'][-1]);print('first latest borough', [r for r in records if r[1].startswith('E09')][-1]);print('Borough coverage',sorted(seen))
