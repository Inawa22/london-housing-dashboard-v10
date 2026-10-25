"""London borough geometry loader and data-integrity checks.

Boundary polygons: Greater London Authority (GLA) London boroughs,
Ordnance Survey Open Data, Open Government Licence v3.0.
https://data.london.gov.uk/dataset/london-boroughs-e55pw
"""
from __future__ import annotations
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent
GEOMETRY_FILE = BASE_DIR / 'data' / 'london_boroughs.geojson'
# The first endpoint is already used in the initial prototype and explicitly
# exposes name and gss_code. The other official GLA endpoints provide backup.
GLA_LAYERS = [
    'https://gis.london.gov.uk/arcgis/rest/services/apps/cultural_infrastructure_map_context_layers/MapServer/2/query',
    'https://gis.london.gov.uk/arcgis/rest/services/apps/Air_Quality_map_service_01/MapServer/0/query',
    'https://gis.london.gov.uk/arcgis/rest/services/apps/planning_data_map_02/MapServer/301/query',
]


def validate_geojson(geojson: dict, stock_codes) -> dict:
    """Validate geometry and ensure exactly one polygon per expected stock code.

    Returns the normalised feature collection (extra features removed), raises
    ValueError with actionable diagnostics otherwise. Never silently paint the
    wrong borough or treat a missing area as zero dwellings.
    """
    if geojson.get('type') != 'FeatureCollection' or not isinstance(geojson.get('features'), list):
        raise ValueError('Expected a GeoJSON FeatureCollection containing borough polygon features.')
    expected = {str(code).strip().upper() for code in stock_codes}
    if len(expected) != 33:
        raise ValueError(f'The housing-stock dataset must contain 33 unique area codes; found {len(expected)}.')
    matching = {}
    for feature in geojson['features']:
        props = feature.get('properties') or {}
        # The official GLA layer has 'gss_code'; tolerate uppercase & ONS field name.
        code = next((str(props[k]).strip().upper() for k in ('gss_code','GSS_CODE','LAD24CD','LAD25CD','lad_code')
                     if props.get(k)), None)
        if code not in expected: continue
        geom = feature.get('geometry') or {}
        if geom.get('type') not in ('Polygon','MultiPolygon') or not geom.get('coordinates'):
            raise ValueError(f'Missing polygon geometry for {code}.')
        if code in matching:
            raise ValueError(f'Duplicate boundary for {code}.')
        # Standardize join property, preserve original names for attribution.
        feature['properties'] = dict(props, gss_code=code)
        matching[code] = feature
    missing = expected - matching.keys()
    if missing:
        raise ValueError('Boundary file is missing housing-stock area codes: ' + ', '.join(sorted(missing)))
    if len(matching) != 33:
        raise ValueError(f'Expected 33 joined polygons; found {len(matching)}.')
    return {'type':'FeatureCollection','features':[matching[k] for k in sorted(matching)]}


def fetch_official_geojson(stock_codes, timeout=6):
    errors = []
    params = {'where': '1=1', 'outFields': 'name,gss_code', 'returnGeometry': 'true',
              'outSR': '4326', 'geometryPrecision': 5, 'f': 'geojson'}
    for endpoint in GLA_LAYERS:
        try:
            url = endpoint + '?' + urlencode(params)
            request = Request(url, headers={'User-Agent': 'London-Housing-Stock-Dashboard/2.0',
                                             'Accept': 'application/geo+json, application/json'})
            with urlopen(request, timeout=timeout) as r:
                raw = json.load(r)
            validated = validate_geojson(raw, stock_codes)
            return validated, endpoint
        except Exception as ex:
            errors.append(f'{endpoint}: {ex}')
    raise RuntimeError('Unable to obtain the 33 official borough boundaries from the GLA services. ' + ' | '.join(errors))


def load_boundaries(stock_codes, allow_network=True):
    """Read included geojson if valid; otherwise attempt GLA download and cache.

    Works offline after the first successful download. On read-only hosts,
    downloading still succeeds in memory even if caching does not.
    """
    if GEOMETRY_FILE.exists():
        try:
            return validate_geojson(json.loads(GEOMETRY_FILE.read_text(encoding='utf-8')), stock_codes), 'Bundled GLA boundary file'
        except (ValueError, OSError):
            if not allow_network:
                raise
            # Recover from a corrupt/outdated cache by re-downloading.
    if not allow_network:
        raise FileNotFoundError('GLA boundary file has not yet been downloaded.')
    data, source = fetch_official_geojson(stock_codes)
    try:
        GEOMETRY_FILE.parent.mkdir(parents=True, exist_ok=True)
        GEOMETRY_FILE.write_text(json.dumps(data, separators=(',', ':')), encoding='utf-8')
    except OSError:
        pass
    return data, f'GLA geographic service: {source}'


def load_uploaded_geojson(upload, stock_codes):
    return validate_geojson(json.loads(upload), stock_codes)
