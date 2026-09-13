"""Import factual unit addresses from the API used by Bluefit's public directory."""
import json
import time
from datetime import datetime, timezone
from fetch_sources import DATA, download

SOURCE = 'https://x5ps-wz9s-zww5.b2.xano.io/api:DYXo6VdR/unidades'

def main():
    units = {}
    page = 1
    while page <= 150:
        payload = json.loads(download(f'{SOURCE}?page={page}&userLat=&userLng=&estado_id=&cidade_id=&aula_id=&nomeUnidade='))
        before = len(units)
        for unit in payload['unidades']:
            address = unit['endereco']
            position = address['lat_long']['data']
            lat, lon = float(position['lat']), float(position['lng'])
            if not (-34 < lat < 6 and -74 < lon < -28):
                raise ValueError('Unexpected unit coordinates')
            units[str(unit['id'])] = {'type': 'bluefit', 'id': unit['id'],
                'center': {'lat': lat, 'lon': lon},
                'tags': {'name': 'Bluefit ' + unit['nome'], 'addr:street': address['rua'],
                         'addr:housenumber': address['numero'], 'addr:suburb': address['bairro'],
                         'addr:city': address['cidade']['nome'], 'addr:state': address['cidade']['estado']['nome']},
                'source_url': 'https://www.bluefit.com.br/unidade/' + unit['slug']}
        following = payload.get('nextPage')
        if not following:
            break
        if len(units) == before or int(following) != page + 1:
            raise ValueError('Invalid Bluefit pagination')
        page = int(following)
        time.sleep(0.4)
    if not units or following:
        raise ValueError('Incomplete Bluefit directory')
    output = {'source': SOURCE, 'fetched_at': datetime.now(timezone.utc).isoformat(), 'elements': list(units.values())}
    target = DATA / 'bluefit_catalog.json'
    temp = target.with_suffix('.tmp')
    temp.write_text(json.dumps(output, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    temp.replace(target)
    print(f'Bluefit: imported {len(units)} official units', flush=True)

if __name__ == '__main__':
    main()
