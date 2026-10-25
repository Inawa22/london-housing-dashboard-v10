"""Regression checks for hypothesis-first dashboard; no network needed."""
import sys
import types
from pathlib import Path
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if "streamlit" not in sys.modules:
    try:
        import streamlit
    except ImportError:
        stub = types.ModuleType("streamlit")
        stub.cache_data = lambda *a, **k: lambda f: f
        sys.modules["streamlit"] = stub

from hypothesis_dashboard import (
    borough_pressure, compare_deliveries, comparison_chart,
    london_stock_series, chart_stock, chart_ta, chart_borough,
)


def test_annual_gap_from_official_source_and_current_planning_benchmark():
    net = pd.read_csv(ROOT / 'data/london_net_additions_verified.csv')
    benchmarks = pd.read_csv(ROOT / 'data/housing_need_benchmarks.csv')
    assert list(net.financial_year) == ['2024-25']
    assert net.net_additions.iloc[0] == 32680
    assert len(benchmarks) == 3
    result = compare_deliveries(32680, 88000)
    assert result['annual_difference'] == 55320
    assert result['delivery_share'] == pytest.approx(37.13636, abs=1e-4)
    with pytest.raises(ValueError):
        compare_deliveries(100, 0)


def test_stock_growth_is_computed_not_looked_up():
    stock = pd.read_csv(ROOT / 'data/london_dwelling_stock_2012_2025.csv')
    series = london_stock_series(stock)
    assert series.year.iloc[0] == 2012
    assert series.year.iloc[-1] == 2025
    assert int(series.total_dwellings.iloc[0]) == 3387821
    assert int(series.total_dwellings.iloc[-1]) == 3854594
    assert int(series.stock_change.iloc[-1]) == 32678
    assert series.stock_change.iloc[0] != series.stock_change.iloc[0]  # no false growth for first year


def test_borough_pressure_uses_gss_not_name_and_preserves_unknown():
    stock = pd.read_csv(ROOT / 'data/london_dwelling_stock_2012_2025.csv',dtype={'code': str})
    stat = pd.read_csv(ROOT / 'data/statutory_homelessness_2025.csv',dtype={'code': str})
    joined = borough_pressure(stock, stat)
    assert joined.code.nunique() == 33
    assert len(joined) == 33
    assert set(joined[joined.ta_rate_1000.isna()].borough) == {'Brent','Ealing'}
    assert int(joined[joined.borough.eq('Newham')].ta_households.iloc[0]) == 7412
    assert joined[~joined.ta_rate_1000.isna()].ta_rate_1000.max() > 59


def test_plotly_charts_use_actual_inputs():
    stock = pd.read_csv(ROOT / 'data/london_dwelling_stock_2012_2025.csv',dtype={'code': str})
    stat = pd.read_csv(ROOT / 'data/statutory_homelessness_2025.csv',dtype={'code': str})
    joined = borough_pressure(stock, stat)
    assert len(comparison_chart(compare_deliveries(32680, 88000)).data) == 1
    assert len(chart_stock(london_stock_series(stock)).data) == 1
    assert len(chart_ta(stat).data) == 1
    assert len(chart_borough(joined, 'Newham').data) >= 1


def test_new_entry_point_and_sources_and_no_causality_claim():
    app=(ROOT/'app.py').read_text(encoding='utf-8')
    hypothesis=(ROOT/'hypothesis_dashboard.py').read_text(encoding='utf-8')
    assert "🔎 · Are we building enough?" in app
    assert "render_hypothesis_dashboard()" in app
    assert "they don’t prove what caused the pressure" in hypothesis
    for f in ['data/housing_need_benchmarks.csv','data/london_net_additions_verified.csv']:
        assert (ROOT / f).exists()


def test_visitor_sees_short_readable_benchmark_choices_and_real_sources():
    from hypothesis_dashboard import BENCHMARK_CHOICES, benchmark_record
    benchmarks = pd.read_csv(ROOT / 'data/housing_need_benchmarks.csv')
    assert len(BENCHMARK_CHOICES) == 3
    expected_sources = {
        'Government method · 88k/year': 'london.gov.uk',
        'GLA study · 66k/year': 'london.gov.uk',
        'London Plan · 52k/year': 'london.gov.uk',
    }
    for label, domain in expected_sources.items():
        assert len(label) < 35
        record, details = benchmark_record(benchmarks, label)
        assert domain in record.source_url
        fig = comparison_chart(compare_deliveries(32680, int(record.homes_per_year)), details['bar_label'])
        assert fig.data[0].y[1] == details['bar_label']
        assert 'Selected annual benchmark' not in list(fig.data[0].y)


def test_first_screen_uses_radio_not_long_selectbox():
    text = (ROOT / 'hypothesis_dashboard.py').read_text(encoding='utf-8')
    assert 'choice = st.radio(' in text
    assert 'choice = st.selectbox(' not in text
    assert 'Where this estimate or target comes from' in text
