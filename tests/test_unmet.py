import sys
import types
from pathlib import Path
import pandas as pd

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
if 'streamlit' not in sys.modules:
    try:import streamlit
    except ImportError:
        stub=types.ModuleType('streamlit');stub.cache_data=lambda *a,**k:lambda f:f
        sys.modules['streamlit']=stub
from unmet_dashboard import source_data, census_context, bar_ranking, trend_chart, pretty

def test_local_authority_coverage():
    stat,reasons,rough=source_data()
    assert stat.groupby('period').code.nunique().eq(34).all()
    assert rough.groupby('period').code.nunique().eq(34).all()
    assert set(stat[stat.code.str.startswith('E09')].code)==set(rough[rough.code.str.startswith('E09')].code)
    assert len(reasons)==3536

def test_official_published_london_figures():
    stat,_,rough=source_data()
    r=stat[(stat.period=='2025 Q4')&(stat.code=='E12000007')].iloc[0]
    assert r.owed_duty==16290 and r.prevention==6540 and r.relief==9750
    assert r.ta_households==75600 and r.ta_children==100930
    assert abs(r.ta_rate_1000-21.14550)<0.001
    assert rough[(rough.period=='2026-27 Q1')&(rough.code=='E12000007')].iloc[0].people_seen==3959

def test_missing_borough_counts_preserved():
    stat,_,_=source_data()
    q4=stat[(stat.period=='2025 Q4')&(stat.level=='Borough')]
    assert q4[q4.ta_households.isna()].borough.tolist()==['Brent','Ealing']
    assert len(q4.dropna(subset=['ta_households']))==31
    assert q4.ta_households.sum()!=stat[(stat.period=='2025 Q4')&(stat.code=='E12000007')].iloc[0].ta_households

def test_charts_do_not_crash():
    stat,_,rough=source_data()
    b=bar_ranking(stat[(stat.period=='2025 Q4')&(stat.level=='Borough')],'ta_rate_1000','E09000002','per 1000')
    assert len(b.data[0].x)==31
    ch=trend_chart(rough,'people_seen','E09000007','CHAIN','People',sorted(rough.period.unique()))
    assert len(ch.data)==2

def test_regional_overcrowding_not_borough():
    c=census_context()
    assert c.tenure.nunique()==4
    assert max(c.year)==2023
    assert 0<=c.overcrowding_pct.min()<=c.overcrowding_pct.max()<=100


def test_missing_data_placeholders_are_not_shown():
    """The public dashboard should not show CSV instructions for missing data."""
    from pathlib import Path
    source=(Path(__file__).resolve().parents[1]/'unmet_dashboard.py').read_text()
    assert "st.markdown('**Social housing waiting lists — additional borough dataset required**')" not in source
    assert "st.markdown('**Overcrowding by borough — Census 2021 source pending**')" not in source
    assert "st.code('data/borough_waiting_lists.csv" not in source
    assert "st.code('data/borough_overcrowding_census2021.csv" not in source
    assert 'if wait is not None:' in source
    assert 'if census is not None:' in source
