import json
import sqlite3
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class DataTests(unittest.TestCase):
    def test_snapshot_integrity(self):
        data=json.loads((ROOT/'dist/data.json').read_text(encoding='utf-8'))
        self.assertGreater(len(data['gyms']),1000)
        self.assertEqual(len({g['id'] for g in data['gyms']}),len(data['gyms']))
        self.assertEqual(len(data['profiles']),168)
        self.assertTrue(all(0<=p['score']<=100 and p['samples']>0 for p in data['profiles']))
        self.assertTrue(all(-34<g['latitude']<6 and -74<g['longitude']<-28 for g in data['gyms']))
        self.assertGreater(sum(g['state']=='MG' for g in data['gyms']),100)
        self.assertGreater(sum(g['city']=='Belo Horizonte' for g in data['gyms']),10)
        confirmed=next(g for g in data['gyms'] if g['id']=='node/5210983323')
        self.assertEqual(confirmed['benefits']['totalpass']['source_url'],'https://totalpass.com/br/academias/smart-fit-luxemburgo/')
        self.assertTrue(confirmed['neighborhood'])
        with sqlite3.connect(ROOT/'data/gyms.db') as db:
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            self.assertEqual(db.execute('SELECT count(*) FROM gyms').fetchone()[0],len(data['gyms']))
            self.assertEqual(db.execute('SELECT count(*) FROM gyms WHERE instr(search_text,?)>0',("' OR 1=1 --",)).fetchone()[0],0)

    def test_local_hour_preserved(self):
        import sys
        sys.path.insert(0,str(ROOT/'pipeline'))
        from build import aggregate_csv
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'source.csv'
            path.write_text('date,number_people\n2015-08-14 23:00:00-07:00,20\n2015-08-14 23:30:00-07:00,40\n')
            profiles,_=aggregate_csv(path)
            self.assertEqual(profiles,[{'weekday':4,'hour':23,'score':100,'samples':2}])

if __name__=='__main__':
    unittest.main()
