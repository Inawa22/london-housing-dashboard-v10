"""One-off optional GLA boundary download to make the London map fully offline.

Run: python download_boundaries.py
"""
from pathlib import Path
import pandas as pd
from boundaries import GEOMETRY_FILE, fetch_official_geojson
import json

codes = pd.read_csv(Path(__file__).resolve().parent/'data/london_dwelling_stock_2012_2025.csv',dtype={'code':str}).code.unique()
geo, url = fetch_official_geojson(codes)
GEOMETRY_FILE.write_text(json.dumps(geo,separators=(',',':')), encoding='utf-8')
print(f'Saved {len(geo["features"])} GLA borough polygons to {GEOMETRY_FILE}')
print('Source:',url)
