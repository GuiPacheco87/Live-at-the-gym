"""Enrich missing municipality/UF using simplified IBGE boundaries."""
import json
from pathlib import Path
from fetch_sources import download
ROOT=Path(__file__).resolve().parents[1]

def main():
    for name,url in {
        'municipalities.json':'https://servicodados.ibge.gov.br/api/v1/localidades/municipios',
        'boundaries.json':'https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo%2Bjson&qualidade=minima&intrarregiao=municipio',
    }.items():
        path=ROOT/'data'/name
        if not path.exists():
            body=download(url)
            json.loads(body)
            path.write_bytes(body)
            print(name,len(body),flush=True)

def ring_contains(ring,x,y):
    inside=False
    previous=ring[-1]
    for current in ring:
        x1,y1=previous[:2];x2,y2=current[:2]
        if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:
            inside=not inside
        previous=current
    return inside

def locator():
    municipalities=json.loads((ROOT/'data/municipalities.json').read_text(encoding='utf-8'))
    by_id={str(m['id']):m for m in municipalities}
    boundaries=json.loads((ROOT/'data/boundaries.json').read_text(encoding='utf-8'))
    index=[]
    for f in boundaries['features']:
        code=str(f['properties']['codarea'])
        m=by_id.get(code)
        if not m:
            continue
        polygons=f['geometry']['coordinates']
        if f['geometry']['type']=='Polygon':
            polygons=[polygons]
        for polygon in polygons:
            exterior=polygon[0]
            index.append((min(p[0] for p in exterior),min(p[1] for p in exterior),max(p[0] for p in exterior),max(p[1] for p in exterior),polygon,m))
    def find(x,y):
        for xmin,ymin,xmax,ymax,polygon,m in index:
            if xmin<=x<=xmax and ymin<=y<=ymax and ring_contains(polygon[0],x,y) and not any(ring_contains(hole,x,y) for hole in polygon[1:]):
                region=m.get('microrregiao')
                uf=region['mesorregiao']['UF'] if region else m['regiao-imediata']['regiao-intermediaria']['UF']
                return m['nome'],uf['sigla']
        return '', ''
    return find

if __name__=='__main__':
    main()
