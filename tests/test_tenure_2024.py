"""Validate that the ONS 2024 donut cannot silently show old or invented data."""
import sys
from pathlib import Path
from io import BytesIO

import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tenure_2024 import CATEGORY_ORDER,validate_2024,read_ons_workbook,area_rows,_category


def make_rows():
    rows=[]
    for i in range(1,34):
        code=f'E09{i:06d}'
        for j,cat in enumerate(CATEGORY_ORDER):
            rows.append({'code':code,'borough':f'Area {i}','tenure':cat,'dwellings':28000+j*2500,'year':2024})
    return pd.DataFrame(rows)


def test_all_33_areas_and_categories():
    d=validate_2024(make_rows())
    assert len(d)==132
    assert d.dwellings.sum()==33*(28000+30500+33000+35500)
    assert area_rows(d,pd.DataFrame([{'code':'E09000005','borough':'Brent'}]),'Brent').dwellings.sum()==127000
    assert area_rows(d,pd.DataFrame([]),'All London').dwellings.sum()==4191000


def test_reject_wrong_year_missing_boroughs_and_percentages():
    d=make_rows()
    with pytest.raises(ValueError,match='2024'):validate_2024(d.assign(year=2021))
    with pytest.raises(ValueError,match='33'):validate_2024(d[d.code.ne('E09000001')])
    with pytest.raises(ValueError,match='implausible'):validate_2024(d.assign(dwellings=25))


def test_parse_headered_ons_like_excel():
    df=pd.DataFrame([
       ['ONS dwelling estimates 2024','','','','',''],
       ['Area code','Local authority','Owned outright','Owned with a mortgage or loan','Private rented','Social rented'],
    ]+[[f'E09{i:06d}',f'Area {i}',28000,30500,33000,35500] for i in range(1,34)])
    bio=BytesIO()
    with pd.ExcelWriter(bio,engine='openpyxl') as xw:
        df.to_excel(xw,index=False,header=False,sheet_name='2024')
    out=read_ons_workbook(bio.getvalue())
    assert len(out)==132
    assert out.dwellings.sum()==4191000


def test_no_misreading_percent_share():
    assert _category('private rented (%)') is None
    assert _category('Social rented: Percentage') is None
    assert _category('Owner occupied outright (estimated count)') == 'Owned outright'
