"""Download public sources. Failure never overwrites the last successful snapshot."""
import json
import gzip
import io
import zipfile
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'

def download(url, body=None):
    request = urllib.request.Request(url, data=body, headers={'User-Agent': 'HoraLivreAcademias/1.0 (public data research)'})
    with urllib.request.urlopen(request, timeout=240) as response:
        body = response.read()
        return gzip.decompress(body) if body[:2] == b'\x1f\x8b' else body

def main():
    DATA.mkdir(exist_ok=True)
    query = '[out:json][timeout:180];area["ISO3166-1"="BR"][admin_level=2]->.br;nwr[leisure=fitness_centre][name](area.br);out center tags;'
    raw = json.loads(download('https://overpass-api.de/api/interpreter', urllib.parse.urlencode({'data':query}).encode()))
    if raw.get('remark') or not raw.get('elements'):
        raise RuntimeError('Incomplete OSM response; keeping previous snapshot')
    raw['fetched_at'] = datetime.now(timezone.utc).isoformat()
    (DATA / 'osm.json').write_text(json.dumps(raw, ensure_ascii=False), encoding='utf-8')
    print('OSM gyms:', len(raw['elements']), flush=True)
    archive = download('https://www.kaggle.com/api/v1/datasets/download/nsrose7224/crowdedness-at-the-campus-gym')
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        names = [name for name in z.namelist() if name.lower().endswith('.csv')]
        if len(names) != 1:
            raise RuntimeError('Unexpected Kaggle archive; inspect before importing')
        content = z.read(names[0])
        if b'number_people' not in content[:2000]:
            raise RuntimeError('Kaggle schema changed')
        (DATA / 'kaggle.csv').write_bytes(content)
    (DATA / 'kaggle_meta.json').write_text(json.dumps({'fetched_at':datetime.now(timezone.utc).isoformat(), 'source':'https://www.kaggle.com/datasets/nsrose7224/crowdedness-at-the-campus-gym'}), encoding='utf-8')
    print('Kaggle CSV downloaded:', len(content), flush=True)

if __name__ == '__main__':
    main()
