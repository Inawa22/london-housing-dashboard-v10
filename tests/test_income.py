from pathlib import Path
import pandas as pd

HERE=Path(__file__).resolve().parents[1]
DATA=HERE/'data'

def test_income_data_integrity():
    d=pd.read_csv(DATA/'resident_fulltime_earnings_ashe_2025.csv',dtype={'code':str})
    boroughs=d[d.code.str.startswith('E09')]
    london=d[d.code=='E12000007']
    assert len(boroughs)==32 and len(london)==1
    assert boroughs.code.nunique()==32
    assert 'E09000001' not in boroughs.code.values
    assert all(boroughs.median_gross_weekly_fulltime_gbp.between(300,2500))
    assert float(london.iloc[0].median_gross_weekly_fulltime_gbp)==902.7
    assert round(float(london.iloc[0].monthly_equivalent_gbp))==3912
    assert all(d.source_url.str.startswith('https://www.nomisweb.co.uk/'))
    assert (d['monthly_equivalent_gbp']-(d['median_gross_weekly_fulltime_gbp']*52/12)).abs().max()<.006


def test_income_history_and_latest():
    d=pd.read_csv(DATA/'london_pay_history_gla_2015_2025.csv',parse_dates=['date'])
    assert len(d)==128
    assert d.date.min()==pd.Timestamp('2015-01-01')
    assert d.date.max()==pd.Timestamp('2025-08-01')
    assert d.date.is_monotonic_increasing and d.date.is_unique
    assert d.london_median_monthly_pay_gbp.gt(0).all()
    assert d.london_monthly_rent_gbp.gt(0).all()
    r=pd.read_csv(DATA/'london_payroll_latest_2026.csv')
    x=r.set_index('month').loc['2026-09-01']
    assert x.london_median_monthly_pay_gbp==3120
    assert x.uk_median_monthly_pay_gbp==2660
    assert x.london_annual_change_pct==3.9


def test_income_tab_is_integrated():
    cost=(HERE/'cost_dashboard.py').read_text()
    inc=(HERE/'income_dashboard.py').read_text()
    assert "'💷  Income'" in cost
    assert 'render_income_tab(selected,expected_codes)' in cost
    assert '2025' in inc and '2026' in inc
    assert 'not a household budget' in inc.lower() or 'not a household' in inc.lower()
    assert 'st.download_button' not in inc


def test_income_plotly_figures_and_geojson_join():
    import sys
    sys.path.insert(0,str(HERE))
    import income_dashboard as inc
    annual,hist,latest=inc.load_income_data()
    ranking=inc.make_ranking(annual,'E09000025')
    assert len(ranking.data[0].y)==32
    assert len(ranking.layout.shapes)==1
    assert len(inc.make_history_chart(hist,'Earnings and rent growth (index)').data)==2
    assert len(inc.make_history_chart(hist,'Monthly earnings (£)').data)==1
    assert len(inc.make_gender_chart(annual,'E09000025').data)==2
    coords=[[[0,0],[1,0],[1,1],[0,1],[0,0]]]
    geo={'type':'FeatureCollection','features':[{'type':'Feature','properties':{'gss_code':code},'geometry':{'type':'Polygon','coordinates':coords}} for code in pd.read_csv(HERE/'data/london_dwelling_stock_2012_2025.csv').code.unique()]}
    m=inc.make_income_map(annual,'E09000025',geo)
    assert len(m.data)==3
    assert len(m.data[1].locations)==32
    assert list(m.data[0].locations)==['E09000001']
