"""Optional on user's connected machine: download official *raw* wider-need files.
The core dashboard works without them. Do NOT treat raw source as validated curated data.
After reviewing geographical codes, reference year and missing values, create the optional
curated CSVs documented in OBJECTIVE3_SOURCES.md to activate borough panels.
"""
from pathlib import Path
import json,urllib.request,urllib.error,hashlib
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'data'/'sources'/'wider_need';DEST.mkdir(parents=True,exist_ok=True)
AGENT='London-Housing-Capacity-Research/1.0 official-public-data-only'

def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':AGENT,'Accept':'*/*'})
 with urllib.request.urlopen(req,timeout=30) as f:return f.read()

def save(name,payload):
 p=DEST/name;p.write_bytes(payload)
 print('Saved',p.name,len(payload),'bytes SHA256',hashlib.sha256(payload).hexdigest()[:16])

url='https://assets.publishing.service.gov.uk/media/6a2be263e50716856ed4afc4/Live_Table_600.ods'
try:
 b=get(url)
 if not b.startswith(b'PK'):raise ValueError('Official URL did not return an ODS/ZIP file')
 save('MHCLG_Live_Table_600.ods',b)
except Exception as e:print('Table 600 download unavailable:',e)

metadata_url='https://api.beta.ons.gov.uk/v1/datasets/TS052/editions/2021/versions/5'
try:
 metadata=json.loads(get(metadata_url))
 downloads=metadata.get('downloads') or {}
 csv_info=downloads.get('csv') or {}
 csv_url=csv_info.get('href') if isinstance(csv_info,dict) else None
 if not csv_url:raise ValueError('ONS API returned no CSV download link')
 b=get(csv_url)
 if b'geography' not in b[:4000].lower():raise ValueError('Downloaded file lacks expected geography columns')
 save('ONS_TS052_Census2021.csv',b)
except Exception as e:print('ONS TS052 download unavailable:',e)
print('Next: validate the source schema; manually prepare the borough-level CSVs in OBJECTIVE3_SOURCES.md.')
