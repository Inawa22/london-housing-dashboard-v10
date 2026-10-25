"""Extract London-authority dwelling stock (2012–2025) from MHCLG Table 100 ODS.

Only the government workbook supplied for this project is used for housing figures.
Uses the ODS XML specification directly so no extra spreadsheet reader is required.
"""
from __future__ import annotations
import csv
import os
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

T = 'urn:oasis:names:tc:opendocument:xmlns:table:1.0'
O = 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'
X = 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'
SOURCE = Path(__file__).parent / 'data' / 'LiveTable100.ods'
DEST = Path(__file__).parent / 'data' / 'london_dwelling_stock_2012_2025.csv'

def parse_number(s):
    s = (s or '').strip().replace(',', '')
    if s in ('', '[x]', '..', 'n/a'):return None
    if s == '-':return 0  # Table 100 convention: nil or negligible for category
    return int(float(s))

def expand_row(row):
    result=[]
    for cell in row:
        if cell.tag not in (f'{{{T}}}table-cell', f'{{{T}}}covered-table-cell'):
            continue
        paragraphs=[p.text or '' for p in cell.iter(f'{{{X}}}p')]
        value=cell.get(f'{{{O}}}value') or (' '.join(paragraphs).strip() if paragraphs else '')
        repeat=min(int(cell.get(f'{{{T}}}number-columns-repeated', '1')), 30)
        result += [value] * repeat
        if len(result)>=20: break
    return result[:15]

def extract(path=SOURCE):
    with zipfile.ZipFile(path) as z:
        root=ET.fromstring(z.read('content.xml'))
    tables={t.get(f'{{{T}}}name'):t for t in root.iter(f'{{{T}}}table')}
    records=[]
    for year in range(2012, 2026):
        for row in tables[str(year)].findall(f'{{{T}}}table-row'):
            cells=expand_row(row)
            if len(cells)<8 or not cells[1].startswith('E090'):
                continue
            code=cells[1]
            record=dict(year=year,code=code,borough=cells[2],
                local_authority=parse_number(cells[3]),
                housing_association=parse_number(cells[4]),
                other_public=parse_number(cells[5]),
                private_sector=parse_number(cells[6]),
                total_dwellings=parse_number(cells[7]))
            records.append(record)
    for year in range(2012,2026):
        subset=[r for r in records if r['year']==year]
        if len(subset)!=33 or len({r['code'] for r in subset})!=33:
            raise ValueError(f'{year}: expected 33 unique local authorities, found {len(subset)}')
        if any(r['total_dwellings'] is None for r in subset):
            raise ValueError(f'{year}: missing total stock')
    with open(DEST,'w',newline='',encoding='utf-8') as f:
        out=csv.DictWriter(f,fieldnames=list(records[0]))
        out.writeheader();out.writerows(records)
    for y in (2012,2024,2025):
        s=[r for r in records if r['year']==y]
        print(y,'boroughs',len(s),'dwellings',sum(r['total_dwellings'] for r in s))
    print('Saved',DEST,'records',len(records))
    return records

if __name__=='__main__':
    if not SOURCE.exists():
        raise FileNotFoundError(f'Copy Table 100 source ODS to {SOURCE}')
    extract()
