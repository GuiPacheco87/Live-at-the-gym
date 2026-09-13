import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'pipeline'))
from catalog import combine

class CatalogTests(unittest.TestCase):
    def unit(self, kind, number, lat, name='Smart Fit Centro'):
        return {'type': kind, 'id': number, 'center': {'lat': lat, 'lon': -43.94}, 'tags': {'name': name}, 'source_url': 'https://www.smartfit.com.br/academias/centro'}

    def catalog(self, units):
        return {'fetched_at': '2026-09-12T00:00:00+00:00', 'elements': units}

    def test_same_brand_nearby_retains_osm_id_and_sources(self):
        result = combine(self.catalog([self.unit('node', 1, -19.92)]), self.catalog([self.unit('smartfit', 2, -19.9201)]))
        self.assertEqual(len(result['elements']), 1)
        self.assertEqual(result['elements'][0]['type'], 'node')
        self.assertEqual(len(result['elements'][0]['sources']), 2)

    def test_different_brand_or_distant_unit_stays_separate(self):
        for name, lat in [('Academia Local', -19.92), ('Smart Fit Sul', -19.94)]:
            result = combine(self.catalog([self.unit('node', 1, lat, name)]), self.catalog([self.unit('smartfit', 2, -19.92)]))
            self.assertEqual(len(result['elements']), 2)

    def test_ambiguous_matches_are_not_merged(self):
        result = combine(self.catalog([self.unit('node', 1, -19.92), self.unit('way', 2, -19.9201)]), self.catalog([self.unit('smartfit', 3, -19.92)]))
        self.assertEqual(len(result['elements']), 3)

    def test_oldest_source_controls_freshness(self):
        older = self.catalog([])
        older['fetched_at'] = '2026-09-10T00:00:00+00:00'
        self.assertEqual(combine(older, self.catalog([]))['fetched_at'], older['fetched_at'])

    def test_second_directory_preserves_provenance(self):
        result = combine(self.catalog([self.unit('node', 1, -19.92, 'Bluefit Centro')]), self.catalog([]))
        result = combine(result, self.catalog([self.unit('bluefit', 2, -19.92, 'Bluefit Centro')]), 'Bluefit')
        self.assertEqual(len(result['elements']), 1)
        self.assertEqual([s['name'] for s in result['elements'][0]['sources']], ['OpenStreetMap', 'Bluefit · diretório oficial'])
