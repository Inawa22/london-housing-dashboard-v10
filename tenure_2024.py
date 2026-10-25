"""ONS 2024 dwellings by tenure (not Census 2021 occupied-household counts).

The official ONS workbook is intentionally not replaced with fabricated values.
Use the file itself (downloaded at runtime or placed in data/raw) and validate
all 33 London LA codes before rendering its donut.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re
from urllib.request import Request, urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parent
SOURCE_PAGE = ('https://www.ons.gov.uk/peoplepopulationandcommunity/housing/'
               'datasets/subnationaldwellingstockbytenureestimates')
SOURCE_DOWNLOAD = ('https://www.ons.gov.uk/file?uri=%2Fpeoplepopulationandcommunity%2Fhousing'
                   '%2Fdatasets%2Fsubnationaldwellingstockbytenureestimates%2Fcurrent'
                   '%2Fsubnationaldwellingsbytenure2024.xlsx')

CATEGORY_ORDER = ['Owned outright', 'Owned with mortgage or loan', 'Private rented', 'Social rented']
CATEGORY_COLOURS = ['#2563eb', '#78a6e1', '#8474c7', '#0e9990']
_LA = re.compile(r'\bE09\d{6}\b')


def _txt(v) -> str:
    if pd.isna(v): return ''
    return re.sub(r'\s+', ' ', str(v).strip()).lower()


def _category(header: str) -> str | None:
    h=_txt(header).replace('-', ' ')
    if any(x in h for x in ('percentage','proportion','%','rate','confidence','sampling','lower bound','upper bound')):
        return None
    if 'outright' in h and any(x in h for x in ('own','occup')): return CATEGORY_ORDER[0]
    if ('mortgage' in h or 'loan' in h) and any(x in h for x in ('own','occup')): return CATEGORY_ORDER[1]
    if 'private' in h and ('rent' in h or 'rented' in h): return CATEGORY_ORDER[2]
    if 'social' in h and ('rent' in h or 'rented' in h): return CATEGORY_ORDER[3]
    return None


def _num(v):
    if pd.isna(v): return None
    if isinstance(v,str):
        raw=v.strip().replace(',','')
        if raw in ('','..','-','x','z','c','[x]','[z]'): return None
        v=raw
    try:
        f=float(v)
        return int(round(f)) if f>=0 and f < 10_000_000 and abs(f-round(f)) < 0.1 else None
    except (TypeError,ValueError):return None


def validate_2024(frame:pd.DataFrame) -> pd.DataFrame:
    """Reject year, geography, category or measurement inconsistencies."""
    required={'code','borough','tenure','dwellings','year'}
    if not required.issubset(frame):raise ValueError('Required: code, borough, tenure, dwellings and year.')
    df=frame[list(required)].copy()
    df['code']=df['code'].astype(str).str.strip()
    df['tenure']=df['tenure'].astype(str).str.strip()
    df['year']=pd.to_numeric(df.year,errors='coerce')
    df['dwellings']=pd.to_numeric(df.dwellings,errors='coerce')
    df=df[df['code'].str.fullmatch(r'E09\d{6}')]
    if df.empty or df.year.isna().any() or not df.year.eq(2024).all():
        raise ValueError('The input must contain 2024 dwelling estimates for London local authorities.')
    if not df.tenure.isin(CATEGORY_ORDER).all():raise ValueError('Unexpected tenure categories.')
    if df[['code','tenure']].duplicated().any():raise ValueError('Repeated authority/category pair.')
    if df.code.nunique()!=33:
        raise ValueError(f'Expected all 33 London authorities; found {df.code.nunique()}.')
    if not df.groupby('code').tenure.nunique().eq(len(CATEGORY_ORDER)).all():
        raise ValueError('Each authority needs all four non-overlapping dwelling tenure categories.')
    if df.dwellings.isna().any() or df.dwellings.lt(0).any() or not df.dwellings.apply(lambda x: float(x).is_integer()).all():
        raise ValueError('Dwelling counts must be non-negative whole numbers.')
    total=df.dwellings.sum()
    if not 3_200_000<=total<=4_300_000:
        raise ValueError(f'2024 London dwelling total {total:,} is implausible: check columns and units.')
    # Protect against percentages inadvertently parsed as counts.
    if df.groupby('code').dwellings.sum().min()<1_000:
        raise ValueError('At least one area total looks like a percentage, not a dwelling count.')
    df['dwellings']=df.dwellings.astype(int)
    df['year']=2024
    return df[['code','borough','tenure','dwellings','year']].sort_values(['borough','tenure']).reset_index(drop=True)


def _from_tidy(frame:pd.DataFrame) -> pd.DataFrame | None:
    fields={re.sub(r'[^a-z0-9]','',str(c).lower()):c for c in frame.columns}
    synonyms={
        'code':('code','geographycode','areacode','ladcode','localauthoritycode'),
        'borough':('borough','geography','areaname','ladname','localauthorityname'),
        'tenure':('tenure','category'),
        'dwellings':('dwellings','count','estimateddwellings','numberofdwellings'),
        'year':('year','referenceyear'),
    }
    cols={key:next((fields[s] for s in choices if s in fields),None) for key,choices in synonyms.items()}
    if all(cols.values()):
        out=frame.rename(columns={v:k for k,v in cols.items()})
        return validate_2024(out)
    return None


def _parse_sheet(raw: pd.DataFrame, sheet_name: str) -> pd.DataFrame | None:
    """Extract a normal broad ONS table with LA GSS codes and multi-row headers.

    We prefer a 2024 worksheet/column. If the sheet mixes years without a clear
    2024 column, we fail closed rather than silently use a historic value.
    """
    raw=raw.fillna('')
    rows=[]
    for ix in range(len(raw)):
        matches=[(j,_LA.search(str(v)).group()) for j,v in enumerate(raw.iloc[ix]) if _LA.search(str(v))]
        if matches:rows.append((ix,matches))
    if not rows:return None
    indices=[ix for ix,m in rows if any(code.startswith('E09') for _,code in m)]
    if len(indices)<30:return None
    first=min(indices)
    headers=raw.iloc[max(0,first-16):first]
    # If a sheet mixes multiple years, field or sheet headers must unambiguously
    # identify which columns correspond to 2024.
    contains_other_years=any(re.search(r'\b20(2[0-35-9]|1\d)\b',str(v)) for v in headers.to_numpy().ravel())
    mapping={}
    for col in range(raw.shape[1]):
        pieces=[str(v).strip() for v in headers.iloc[:,col] if str(v).strip()]
        descriptor=' '.join(pieces)
        cat=_category(descriptor)
        if cat:
            year_hits=re.findall(r'\b20\d{2}\b',descriptor)
            if year_hits and '2024' not in year_hits:continue
            if contains_other_years and '2024' not in year_hits and '2024' not in sheet_name:
                continue
            mapping.setdefault(cat,[]).append(col)
    if set(mapping)!=set(CATEGORY_ORDER) or any(len(x)!=1 for x in mapping.values()):return None
    code_col=max(set(j for _,matches in rows for j,code in matches),key=lambda j:sum(1 for _,matches in rows if any(k==j for k,_ in matches)))
    out=[]
    for ix,_ in rows:
        line=raw.iloc[ix]
        code_match=_LA.search(str(line.iloc[code_col]))
        if code_match is None:continue
        code=code_match.group()
        # Prefer proper local authority name in immediate neighbouring cells.
        names=[str(v).strip() for j,v in enumerate(line[:min(raw.shape[1],code_col+4)])
               if j!=code_col and isinstance(v,str) and len(v.strip())>3 and 'E09' not in v]
        borough=next((v for v in names if not re.match(r'^\d',v)),code)
        for cat in CATEGORY_ORDER:
            v=_num(line.iloc[mapping[cat][0]])
            if v is None:return None
            out.append({'code':code,'borough':borough,'tenure':cat,'dwellings':v,'year':2024})
    return pd.DataFrame(out)


def read_ons_workbook(content: bytes) -> pd.DataFrame:
    try:
        sheets=pd.read_excel(BytesIO(content),sheet_name=None,header=None,engine='openpyxl')
    except Exception as exc:
        raise ValueError('Unable to read the official ONS Excel workbook.') from exc
    errors=[]
    for name,raw in sheets.items():
        try:
            result=_parse_sheet(raw,name)
            if result is not None:return validate_2024(result)
        except ValueError as exc: errors.append(f'{name}: {exc}')
    raise ValueError('Could not identify four non-overlapping 2024 dwelling-tenure count columns for all 33 London authorities. '
                     'Please use the official 2024 ONS dwelling (not household) workbook. '+ '; '.join(errors[:2]))


def load_local_or_online() -> pd.DataFrame:
    """Use a verified processed extract or official raw workbook. Network is optional."""
    csv=ROOT/'data'/'ons_2024_dwelling_tenure.csv'
    if csv.is_file():return validate_2024(pd.read_csv(csv,dtype={'code':str}))
    candidates=[ROOT/'data'/'raw'/'subnationaldwellingsbytenure2024.xlsx',
                ROOT/'data'/'subnationaldwellingsbytenure2024.xlsx']
    for path in candidates:
        if path.is_file():return read_ons_workbook(path.read_bytes())
    req=Request(SOURCE_DOWNLOAD,headers={'User-Agent':'Mozilla/5.0 (compatible; HousingDashboard/1.0)'})
    try:
        with urlopen(req,timeout=12) as response:
            blob=response.read()
    except Exception as exc:
        raise RuntimeError('The ONS download could not be reached from this computer.') from exc
    return read_ons_workbook(blob)


def area_rows(data:pd.DataFrame, stock:pd.DataFrame, selected:str) -> pd.DataFrame:
    """Select borough by GSS code, not spelling; All London is summed across 33 LAs."""
    if selected=='All London':return data
    one=stock[stock.borough.eq(selected)]
    if len(one)!=1:raise ValueError(f'Unknown borough: {selected}')
    rows=data[data.code.eq(str(one.iloc[0].code))]
    if len(rows)!=len(CATEGORY_ORDER):raise ValueError(f'No validated 2024 dwelling-tenure figures for {selected}.')
    return rows
