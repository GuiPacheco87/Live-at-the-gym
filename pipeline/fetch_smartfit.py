"""Read the public Brazilian unit directory, with bounded, paced pagination."""
import json
import time
from datetime import datetime, timezone
from fetch_sources import DATA, download

SOURCE = 'https://www.smartfit.com.br/academias.json'

def main():
    units = {}
    page = 1
    expected = None
    origins = ['', '&lat=-3.73&lng=-38.52', '&lat=-30.03&lng=-51.23', '&lat=-3.12&lng=-60.02']
    origin_index = 0
    # The public endpoint clamps page 126 to page 125 (1,000 results).
    # Geographic orderings expose units beyond the first 1,000 results.
    while page <= 250:
        payload = json.loads(download(f'{SOURCE}?page={page}{origins[origin_index]}'))
        expected = expected or payload['locations_count']
        if payload['locations_count'] != expected:
            raise ValueError('Directory changed during import; retry later')
        for unit in payload['locations']:
            address = unit['address']
            position = address['position']
            lat, lon = float(position['latitude']), float(position['longitude'])
            if not (-34 < lat < 6 and -74 < lon < -28):
                raise ValueError('Unexpected unit coordinates')
            units[str(unit['id'])] = {
                'type': 'smartfit', 'id': unit['id'],
                'center': {'lat': lat, 'lon': lon},
                'tags': {'name': 'Smart Fit ' + unit['name'],
                         'addr:street': address['first_line'],
                         'opening_hours': '; '.join(day + ' ' + ', '.join(s['table']['time'] for s in hours) for day, hours in unit.get('schedules', {}).items())},
                'source_url': 'https://www.smartfit.com.br/academias/' + unit['permalink'],
            }
        if len(units) == expected:
            break
        if page % 10 == 0:
            print(f'Smart Fit: {len(units)}/{expected}', flush=True)
        following = payload.get('next_page')
        if page == 125:
            origin_index += 1
            if origin_index == len(origins):
                break
            page = 1
            time.sleep(0.4)
            continue
        if not following:
            break
        if int(following) != page + 1:
            raise ValueError('Unexpected pagination')
        page = int(following)
        time.sleep(0.4)
    if len(units) != expected:
        raise ValueError(f'Incomplete directory: {len(units)}/{expected}')
    output = {'source': SOURCE, 'fetched_at': datetime.now(timezone.utc).isoformat(), 'elements': list(units.values())}
    target = DATA / 'smartfit_catalog.json'
    temp = target.with_suffix('.tmp')
    temp.write_text(json.dumps(output, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    temp.replace(target)
    print(f'Smart Fit: imported {len(units)} official units', flush=True)

if __name__ == '__main__':
    main()
