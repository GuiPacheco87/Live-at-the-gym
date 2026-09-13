"""Combine source records; conservative matching preserves existing OSM IDs."""
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def distance(a, b):
    a, b = a.get('center', a), b.get('center', b)
    lat1, lat2 = math.radians(a['lat']), math.radians(b['lat'])
    dlat, dlon = lat2-lat1, math.radians(b['lon']-a['lon'])
    return 6371000 * 2 * math.asin(min(1, math.sqrt(math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2)))

def combine(osm, official, brand='Smart Fit'):
    elements = json.loads(json.dumps(osm['elements']))
    for e in elements:
        e.setdefault('sources', [{'name': 'OpenStreetMap', 'url': f"https://www.openstreetmap.org/{e['type']}/{e['id']}", 'checked_at': osm['fetched_at']}])
    pattern = r'smart\s*fit' if brand == 'Smart Fit' else r'blue\s*fit'
    candidates = [e for e in elements if re.search(pattern, e.get('tags', {}).get('name', ''), re.I) and 'lat' in e.get('center', e)]
    matched = set()
    for unit in official['elements']:
        source = {'name': brand + ' · diretório oficial', 'url': unit['source_url'], 'checked_at': official['fetched_at']}
        nearby = [e for e in candidates if distance(e, unit) <= 60]
        if len(nearby) == 1 and id(nearby[0]) not in matched:
            target = nearby[0]
            matched.add(id(target))
            target['sources'].append(source)
            for key, value in unit['tags'].items():
                if not target['tags'].get(key):
                    target['tags'][key] = value
                    if key == 'addr:suburb':
                        target['neighborhood_source'] = source['name']
        else:
            unit = json.loads(json.dumps(unit))
            unit['sources'] = [source]
            elements.append(unit)
    return {'elements': elements, 'fetched_at': min(osm['fetched_at'], official['fetched_at']),
            'sources': {**osm.get('sources', {'OpenStreetMap': osm['fetched_at']}), brand: official['fetched_at']},
            'matched_units': osm.get('matched_units', 0) + len(matched)}

def load_catalog():
    result = combine(json.loads((ROOT/'data/osm.json').read_text(encoding='utf-8')),
                     json.loads((ROOT/'data/smartfit_catalog.json').read_text(encoding='utf-8')))
    return combine(result, json.loads((ROOT/'data/bluefit_catalog.json').read_text(encoding='utf-8')), 'Bluefit')
