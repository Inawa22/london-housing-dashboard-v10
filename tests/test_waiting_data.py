import pandas as pd
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_waiting_list_has_actual_2024_borough_records():
 d=pd.read_csv(ROOT/'data/borough_waiting_lists.csv')
 assert len(d)==33 and d.code.nunique()==33
 assert set(d.year)=={2024}
 assert d.waiting_households.min()>0
 assert d.loc[d.code.eq('E09000025'),'waiting_households'].iloc[0]==38417 # Newham
 assert d.loc[d.code.eq('E09000019'),'waiting_households'].iloc[0]==16747 # Islington
 assert d.waiting_households.sum()==336366


def test_2025_waiting_snapshot_separated_from_2024_boroughs():
 s=(ROOT/'unmet_dashboard.py').read_text()
 assert '341,421' in s and 'March 2025' in s
 assert 'About 380,000' in s and 'Census 2021' in s
 assert '336,357' in s
