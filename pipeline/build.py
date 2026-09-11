"""Materialize a read-only SQL snapshot and a static browser fallback."""
import csv
import json
import sqlite3
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from geography import locator

ROOT = Path(__file__).resolve().parents[1]

def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.lower()) if unicodedata.category(c) != 'Mn')

def aggregate_csv(path):
    buckets = defaultdict(list)
    dates = []
    with path.open(encoding='utf-8-sig') as file:
        for row in csv.DictReader(file):
            dt = datetime.fromisoformat(row['date'])
            count = float(row['number_people'])
            if count < 0:
                continue
            buckets[(dt.weekday(), dt.hour)].append(count)
            dates.append(dt.date().isoformat())
    if not buckets:
        raise ValueError('No valid attendance observations')
    means = {k: sum(v) / len(v) for k,v in buckets.items()}
    peak = max(means.values()) or 1
    profiles = [{'weekday':d,'hour':h,'score':round(means[(d,h)]/peak*100),'samples':len(buckets[(d,h)])} for d,h in sorted(means)]
    return profiles, {'observation_start':min(dates),'observation_end':max(dates)}

def main():
    raw = json.loads((ROOT/'data/osm.json').read_text(encoding='utf-8'))
    find_city = locator()
    gyms = []
    for element in raw['elements']:
        tags = element.get('tags', {})
        center = element.get('center', element)
        if not tags.get('name') or 'lat' not in center:
            continue
        gym = dict(id=f"{element['type']}/{element['id']}", name=tags['name'], city=tags.get('addr:city',''), state=tags.get('addr:state',''), address=', '.join(filter(None,[tags.get('addr:street'),tags.get('addr:housenumber'),tags.get('addr:suburb')])), latitude=center['lat'], longitude=center['lon'], opening_hours=tags.get('opening_hours',''))
        gym['neighborhood'] = tags.get('addr:suburb', tags.get('addr:neighbourhood',''))
        city, state = find_city(gym['longitude'], gym['latitude'])
        if city:
            gym['city'],gym['state'] = city,state
        gym['search_text'] = normalize(' '.join(str(v) for v in gym.values()))
        gyms.append(gym)
    profiles, period = aggregate_csv(ROOT/'data/kaggle.csv')
    benefits = json.loads((ROOT/'data/benefits.json').read_text(encoding='utf-8'))
    known_ids = {g['id'] for g in gyms}
    benefits = [b for b in benefits if b['gym_id'] in known_ids]
    for gym in gyms:
        gym['benefits'] = {}
    by_id = {g['id']:g for g in gyms}
    for benefit in benefits:
        age = (datetime.now(timezone.utc).date() - datetime.fromisoformat(benefit['checked_at']).date()).days
        entry = dict(benefit)
        if age > 30 or age < 0:
            entry['status'] = 'unknown'
        by_id[benefit['gym_id']]['benefits'][benefit['provider']] = entry
    spark_file = ROOT/'data/spark_profiles.json'
    if spark_file.exists():
        profiles = json.loads(spark_file.read_text(encoding='utf-8'))
    kaggle_meta = json.loads((ROOT/'data/kaggle_meta.json').read_text())
    meta = dict(built_at=datetime.now(timezone.utc).isoformat(), catalog_updated_at=raw['fetched_at'], model_checked_at=kaggle_meta['fetched_at'], source=kaggle_meta['source'], coverage='Academias mapeadas no OpenStreetMap; cobertura parcial do Brasil.', methodology='Perfil genérico de uma academia universitária do Kaggle, aplicado igualmente a todas as unidades. Não representa medições destas academias, capacidade, número de pessoas ou dados do Google.', **period)
    temp = ROOT/'data/gyms.next.db'
    if temp.exists():
        temp.unlink()
    with sqlite3.connect(temp) as db:
        db.executescript((ROOT/'sql/schema.sql').read_text())
        db.executemany('INSERT INTO gyms VALUES (:id,:name,:city,:state,:neighborhood,:address,:latitude,:longitude,:opening_hours,:search_text)', gyms)
        db.executemany('INSERT INTO profiles VALUES (:weekday,:hour,:score,:samples)', profiles)
        db.executemany('INSERT INTO benefits VALUES (:gym_id,:provider,:status,:source_url,:checked_at)', [b for g in gyms for b in g['benefits'].values()])
        db.executemany('INSERT INTO metadata VALUES (?,?)', [(key,json.dumps(value,ensure_ascii=False)) for key,value in meta.items()])
    db.close()
    temp.replace(ROOT/'data/gyms.db')
    (ROOT/'dist/data.json').write_text(json.dumps(dict(gyms=gyms,profiles=profiles,meta=meta), ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(f'Built {len(gyms)} gyms / {len(profiles)} hourly buckets')

if __name__ == '__main__':
    main()
