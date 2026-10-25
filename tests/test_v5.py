import sys
from pathlib import Path
import types

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
if 'streamlit' not in sys.modules:
    try:import streamlit
    except ImportError:
        stub=types.ModuleType('streamlit')
        stub.cache_data=lambda *a,**kw: lambda f:f
        sys.modules['streamlit']=stub

from housing_assistant import build_source_context,scoped_facts,offline_answer,geography


def test_published_hpi_type_price_and_borough_volume_extracts():
    types_df=pd.read_csv(ROOT/'data/london_purchase_prices_by_type.csv')
    volumes=pd.read_csv(ROOT/'data/borough_sales_volume.csv',dtype={'code':str})
    assert types_df.date.max()=='2026-07-01'
    assert types_df.groupby('date').type.nunique().eq(4).all()
    last=types_df[types_df.date.eq('2026-07-01')].set_index('type')
    assert last.loc['Detached','average_price_gbp']==1_167_718
    assert last.loc['Semi-detached','average_price_gbp']==724_106
    assert last.loc['Terraced','average_price_gbp']==642_452
    assert last.loc['Flat / maisonette','average_price_gbp']==424_013
    assert volumes.code.nunique()==33
    assert volumes.date.max()=='2026-06-01'
    assert not volumes.duplicated(['date','code']).any()
    assert volumes.groupby('date').code.nunique().eq(33).all()
    assert 'type' not in volumes.columns  # never label borough volume as by type


def test_replaced_2021_tenure_chart():
    app=(ROOT/'app.py').read_text()
    assert 'Owner-occupied vs privately rented: ONS Census 2021' not in app
    assert 'census2021_london_tenure.csv' not in app
    assert 'render_ons_2024_tenure(selected,current)' in app
    assert not (ROOT/'data'/'census2021_london_tenure.csv').exists()


def test_assistant_grounding_and_missing_data():
    ctx=build_source_context()
    london=scoped_facts('London',ctx)
    assert london['existing_dwellings']>3_800_000
    assert london['households_in_temporary_accommodation']==75_600
    assert london['people_seen_rough_sleeping']==3959
    assert 'Kensington and Chelsea' == geography('What is rent in Kensington and Chelsea?',ctx)
    assert 'borough-level Census' in offline_answer('How many households are overcrowded?',ctx)
    assert 'cannot identify' in offline_answer('Which property type is most bought?',ctx)
    assert 'not a general AI model' in offline_answer('random question ?',ctx)
    selected=offline_answer('How much is the rent?',ctx,'Camden')
    assert '**Camden rent:' in selected


def test_no_download_buttons_and_map_checkbox():
    for fn in ['app.py','cost_dashboard.py','unmet_dashboard.py']:
        s=(ROOT/fn).read_text()
        assert 'st.download_button(' not in s
    assert 'unmet_load_ta_map' not in (ROOT/'unmet_dashboard.py').read_text()


def test_reference_sources_present():
    guide=(ROOT/'housing_explainer.py').read_text()
    for name in ['MHCLG Table 100','ONS Price Index of Private Rents','UK House Price Index','CHAIN','ONS Census 2021']:
        assert name in guide


def test_census_importer_validates_and_calculates(tmp_path,monkeypatch):
    sys.path.insert(0,str(ROOT/'scripts'))
    import import_census_london as imp
    monkeypatch.setattr(imp,'DATA',tmp_path)
    codes=[f'E09{i:06d}' for i in range(1,34)]
    rows=[{
      'geography code':code,'geography':f'Area{i}',
      'Occupancy rating of bedrooms: Total: All households':'1000',
      'Occupancy rating of bedrooms: -1':'80',
      'Occupancy rating of bedrooms: -2 or less':'20',
      'Accommodation type: Total: All households':'1000',
      'Accommodation type: Detached':'150',
      'Accommodation type: Semi-detached':'200',
      'Accommodation type: Terraced':'250',
      'Accommodation type: In a purpose-built block of flats or tenement':'300',
      'Accommodation type: Part of a converted or shared house':'50',
      'Accommodation type: In a commercial building':'50'
    } for i,code in enumerate(codes,1)]
    f=tmp_path/'ons_test.csv'
    pd.DataFrame(rows).to_csv(f,index=False)
    imp.import_overcrowding(f)
    result=pd.read_csv(tmp_path/'borough_overcrowding_census2021.csv')
    assert len(result)==33
    assert result.overcrowded_households.eq(100).all()
    imp.import_accommodation(f)
    result=pd.read_csv(tmp_path/'borough_accommodation_types_census2021.csv')
    assert len(result)==33*4
    assert result[result.property_type.eq('Flats / maisonettes (all types)')].households.eq(400).all()
