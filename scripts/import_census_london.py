"""Import officially downloaded ONS 2021 census CSV files into dashboard CSVs.

Examples (from project root):
  python scripts/import_census_london.py --ts044 data/raw/TS044.csv --ts052 data/raw/TS052.csv
  python scripts/import_census_london.py --ts001 data/raw/TS001.csv --ts054 data/raw/TS054.csv

Original ONS files must be obtained from:
 TS044: https://www.ons.gov.uk/datasets/TS044/editions/2021/versions/4
 TS052: https://www.ons.gov.uk/datasets/TS052/editions/2021/versions/5
 TS001: https://www.ons.gov.uk/datasets/TS001
 TS054: https://www.ons.gov.uk/datasets/TS054

This script never substitutes guesses for Census records. Exactly 33 London authority
GSS codes are required to generate a borough-level output.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'


def read_ons(path):
    df=pd.read_csv(path,low_memory=False,dtype=str,encoding='utf-8-sig')
    codes=next((c for c in df if 'geography code' in c.lower()),None)
    if not codes:raise ValueError('ONS CSV must have a Geography Code column.')
    # Nine-character GSS codes for the 33 London local authorities: E09 + six digits.
    df=df[df[codes].str.match(r'^E09\d{6}$',na=False)].copy()
    df['code']=df[codes].str.upper()
    if df.code.nunique()!=33 or df.code.duplicated().any():
        raise ValueError(f'Expected one row for each of 33 London borough/City GSS codes, found {df.code.nunique()} unique areas and {len(df)} rows. Use local-authority ONS 2021 CSV, not LSOA or ward files.')
    names=next((c for c in df if c.lower() in ('geography','area name','geography name')),None)
    df['borough']=df[names] if names else df.code
    return df


def col(df,*parts,excludes=()):
    candidates=[k for k in df if all(p.casefold() in k.casefold() for p in parts) and not any(e.casefold() in k.casefold() for e in excludes)]
    if len(candidates)!=1:raise ValueError(f'Expected one ONS column matching {parts}; found {candidates}.')
    return candidates[0]


def numeric(series):
    s=series.str.replace(',','',regex=False).str.replace(' ','',regex=False)
    result=pd.to_numeric(s,errors='raise')
    if result.isna().any() or (result<0).any():raise ValueError('Missing or negative Census values cannot be used in the published borough chart.')
    return result.astype(int)


def import_accommodation(path):
    d=read_ons(path)
    items=[('Detached',['Accommodation type','Detached'],['Semi-detached']),('Semi-detached',['Accommodation type','Semi-detached'],[]),
           ('Terraced',['Accommodation type','Terraced'],[])]
    columns=[]
    for label,words,excluded in items:columns.append((label,col(d,*words,excludes=excluded)))
    flat_columns=[c for c in d if 'Accommodation type' in c and any(t in c.lower() for t in ('purpose-built','converted','commercial building'))]
    if not flat_columns:raise ValueError('Could not identify flats/maisonettes categories in TS044.')
    total_col=col(d,'Accommodation type','Total')
    for _,c in columns:d[c]=numeric(d[c])
    for c in flat_columns:d[c]=numeric(d[c])
    out=[]
    for _,r in d.iterrows():
        for label,c in columns:
            out.append({'code':r.code,'borough':r.borough,'property_type':label,'households':int(r[c]),'year':2021,'source':'ONS Census 2021 TS044'})
        out.append({'code':r.code,'borough':r.borough,'property_type':'Flats / maisonettes (all types)','households':sum(int(r[c]) for c in flat_columns),'year':2021,'source':'ONS Census 2021 TS044'})
    out=pd.DataFrame(out)
    if out.code.nunique()!=33:raise ValueError('Not all areas present')
    out.to_csv(DATA/'borough_accommodation_types_census2021.csv',index=False)
    print('Wrote borough accommodation type distribution:',out.shape)


def import_overcrowding(path):
    d=read_ons(path)
    total=col(d,'Occupancy rating','Total')
    # TS052 includes -1 and -2 or less, we choose exact minus labels (not 'rating -1 or less' combined).
    minus_one=col(d,'Occupancy rating','-1',excludes=['-2','or less'])
    minus_two=col(d,'Occupancy rating','-2')
    out=d[['code','borough']].copy()
    out['total_households']=numeric(d[total])
    out['overcrowded_households']=numeric(d[minus_one])+numeric(d[minus_two])
    if not out['overcrowded_households'].le(out['total_households']).all():raise ValueError('Census overcrowding exceeds household denominator')
    out['year']=2021;out['source']='ONS Census 2021 TS052'
    out.to_csv(DATA/'borough_overcrowding_census2021.csv',index=False)
    print('Wrote borough overcrowding:',out.shape)


def import_population(path):
    d=read_ons(path)
    # TS001 has population groups; sum household and communal residents, OR use published total if available.
    total=col(d,'Residence type','Total')
    out=d[['code','borough']].copy()
    out['year']=2021;out['population']=numeric(d[total]);out['source']='ONS Census 2021 TS001'
    out.to_csv(DATA/'borough_population_2021.csv',index=False)
    print('Wrote borough population 2021:',out.shape)


def import_tenure(path):
    d=read_ons(path)
    categories={
      'Owned':('Tenure of household','Owned'),
      'Shared ownership':('Tenure of household','Shared ownership'),
      'Social rented':('Tenure of household','Social rented'),
      'Private rented':('Tenure of household','Private rented'),
      'Lives rent free':('Tenure of household','Lives rent free'),
    }
    excludes={
      'Owned':['Owns outright','Owns with','mortgage','shared'],
      'Shared ownership':['Shared ownership: Shared ownership'],
      'Social rented':['Rents from','Other social'],
      'Private rented':['Private landlord','Other private'],
      'Lives rent free':[],
    }
    for label,parts in categories.items():
        d[col(d,*parts,excludes=excludes[label])]=numeric(d[col(d,*parts,excludes=excludes[label])])
    rows=[]
    for _,r in d.iterrows():
        for label,parts in categories.items():
            c=col(d,*parts,excludes=excludes[label]);rows.append({'code':r.code,'borough':r.borough,'tenure':label,'households':int(r[c]),'year':2021,'source':'ONS Census 2021 TS054'})
    df=pd.DataFrame(rows)
    df.to_csv(DATA/'borough_tenure_census2021.csv',index=False)
    print('Wrote borough household tenure:',df.shape)


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__)
    for k in ['ts044','ts052','ts001','ts054']:a.add_argument('--'+k,type=Path)
    args=a.parse_args()
    if not any((args.ts044,args.ts052,args.ts001,args.ts054)):a.error('Provide at least one downloaded ONS CSV')
    for code,fn in [('ts044',import_accommodation),('ts052',import_overcrowding),('ts001',import_population),('ts054',import_tenure)]:
        f=getattr(args,code)
        if f:fn(f)
