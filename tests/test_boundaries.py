"""Offline integration checks for geometry/data linkage (synthetic polygons only).

The synthetic test polygons must NEVER be used in the actual dashboard.
"""
import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from boundaries import validate_geojson, load_uploaded_geojson

with (ROOT / 'data/london_dwelling_stock_2012_2025.csv').open(newline='') as f:
    records = list(csv.DictReader(f))
CODES = sorted({r['code'] for r in records})

def sample_geojson():
    return {'type':'FeatureCollection','features':[
        {'type':'Feature','properties':{'gss_code': code},
         'geometry':{'type':'Polygon', 'coordinates':[[[i,0],[i+0.9,0],[i+0.9,0.9],[i,0.9],[i,0]]]}}
        for i,code in enumerate(CODES)
    ]}

class GeometryTests(unittest.TestCase):
    def test_all_33_codes_are_covered(self):
        self.assertEqual(len(CODES),33)
        self.assertIn('E09000001',CODES)  # City of London
        boundary=validate_geojson(sample_geojson(),CODES)
        self.assertEqual(len(boundary['features']),33)
        self.assertEqual({x['properties']['gss_code'] for x in boundary['features']},set(CODES))

    def test_missing_borough_fails_loudly(self):
        geo=sample_geojson()
        geo['features'].pop()
        with self.assertRaisesRegex(ValueError,'missing'):
            validate_geojson(geo,CODES)

    def test_duplicate_borough_fails_loudly(self):
        geo=sample_geojson()
        geo['features'].append(geo['features'][0])
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            validate_geojson(geo,CODES)

    def test_geojson_upload_accepts_same_schema(self):
        import json
        geo=load_uploaded_geojson(json.dumps(sample_geojson()).encode('utf8'),CODES)
        self.assertEqual(len(geo['features']),33)

    def test_stock_total_and_provider_reconciliation(self):
        subset=[r for r in records if r['year']=='2025']
        self.assertEqual(len(subset),33)
        self.assertEqual(sum(int(r['total_dwellings']) for r in subset),3854594)
        for row in subset:
            self.assertEqual(int(row['total_dwellings']),
                    sum(int(row[c]) for c in ('local_authority','housing_association','other_public','private_sector')))

if __name__=='__main__':unittest.main()
