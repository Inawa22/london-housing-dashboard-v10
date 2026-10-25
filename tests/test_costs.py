"""Run with: python -m pytest tests/test_costs.py"""
import sys, types
from pathlib import Path
import pandas as pd
import pytest

# Streamlit is only needed to render the app; model calculations can be tested
# without the web framework (useful in offline CI).
if 'streamlit' not in sys.modules:
    try: import streamlit
    except ModuleNotFoundError:
        stub=types.ModuleType('streamlit')
        stub.cache_data=lambda *args, **kwargs: (lambda f:f)
        sys.modules['streamlit']=stub
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import cost_dashboard as c


def test_geographical_coverage_and_sources():
    price,rent=c.load_cost_data()
    p=price[price.code.str.startswith('E09')]
    r=rent[rent.code.str.startswith('E09')]
    assert p.code.nunique()==33
    assert r.code.nunique()==32
    assert 'E09000001' not in r.code.unique()
    assert price.date.max()==pd.Timestamp('2026-07-01')
    assert rent.date.max()==pd.Timestamp('2026-08-01')
    assert (price.groupby('date')['code'].nunique()==34).all()
    assert (rent.groupby('date')['code'].nunique()==33).all()
    assert price.loc[price.code.eq(c.LONDON_CODE),'average_price_gbp'].iloc[-1]==550037
    assert rent.loc[rent.code.eq(c.LONDON_CODE),'rent_gbp'].iloc[-1]==2332


def test_london_average_not_borough_average():
    price,rent=c.load_cost_data()
    for df,field in [(price,'average_price_gbp'),(rent,'rent_gbp')]:
        latest=c.get_latest(df,df.date.max())
        published=float(latest[latest.code.eq(c.LONDON_CODE)][field].iloc[0])
        simple_average=latest[latest.code.str.startswith('E09')][field].mean()
        assert abs(published-simple_average)>1


def test_yoy_and_missing():
    prices,rents=c.load_cost_data()
    area='E09000002';dt=prices.date.max()
    current=prices[(prices.code==area)&(prices.date==dt)].average_price_gbp.iloc[0]
    yearago=prices[(prices.code==area)&(prices.date==dt-pd.DateOffset(years=1))].average_price_gbp.iloc[0]
    assert c.annual_price_change(prices,area,dt,'average_price_gbp')==pytest.approx(100*(current/yearago-1))
    assert c.annual_price_change(prices,area,pd.Timestamp('1995-01-01'),'average_price_gbp') is None
    assert c.comparison_row(c.get_latest(rents,rents.date.max()),c.CITY_CODE,'rent_gbp') is None


def test_ranking_trend_bedrooms_and_map_figures():
    prices,rents=c.load_cost_data()
    latest=c.get_latest(rents,rents.date.max())
    london=c.comparison_row(latest,c.LONDON_CODE,'rent_gbp')
    rank=c.bar_ranking(latest,'rent_gbp',c.LONDON_CODE,float(london.rent_gbp),'rent')
    assert len(rank.data)==1
    assert len(rank.data[0].y)==32
    assert len(rank.layout.shapes)==1
    trend=c.trend_chart(rents,'rent_gbp','E09000002',[], 'Last 5 years')
    assert len(trend.data)==2
    bedroom=c.breakdown_chart(london)
    assert len(bedroom.data[0].x)==4
    # Minimal valid polygons to test trace join by GSS code (not geographical accuracy)
    stock=pd.read_csv(c.DATA_DIR/'london_dwelling_stock_2012_2025.csv')
    coords=[[[0,0],[1,0],[1,1],[0,1],[0,0]]]
    geo={'type':'FeatureCollection','features':[{'type':'Feature','properties':{'gss_code':code},'geometry':{'type':'Polygon','coordinates':coords}} for code in stock.code.unique()]}
    fig=c.map_costs(latest,'rent_gbp','E09000002',geo,'rent')
    assert len(fig.data)==3
    assert list(fig.data[0].locations)==[c.CITY_CODE]
    assert len(fig.data[1].locations)==32
