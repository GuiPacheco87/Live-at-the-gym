"""Import the full IBGE neighborhood directory and locate gyms inside polygons."""
import json
from pathlib import Path
from datetime import datetime, timezone
import shapefile
from fetch_sources import download
from geography import ring_contains
from catalog import load_catalog

ROOT=Path(__file__).resolve().parents[1]
SOURCE='https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_de_setores_censitarios__divisoes_intramunicipais/censo_2022/bairros/shp/BR/BR_bairros_CD2022.zip'
UFS=dict(zip(['11','12','13','14','15','16','17','21','22','23','24','25','26','27','28','29','31','32','33','35','41','42','43','50','51','52','53'],['RO','AC','AM','RR','PA','AP','TO','MA','PI','CE','RN','PB','PE','AL','SE','BA','MG','ES','RJ','SP','PR','SC','RS','MS','MT','GO','DF']))

def main():
    archive=ROOT/'data/neighborhoods.zip'
    if not archive.exists():
        archive.write_bytes(download(SOURCE))
    elements=load_catalog()['elements']
    points=[]
    for e in elements:
        c=e.get('center',e)
        if 'lon' in c:
            points.append((f"{e['type']}/{e['id']}",c['lon'],c['lat']))
    names=[];located={}
    with shapefile.Reader(str(archive)) as reader:
        for item in reader.iterShapeRecords():
            r=item.record.as_dict();shape=item.shape
            names.append({'id':r['CD_BAIRRO'],'name':r['NM_BAIRRO'],'city':r['NM_MUN'],'city_id':r['CD_MUN'],'state':UFS[r['CD_UF']]})
            xmin,ymin,xmax,ymax=shape.bbox
            candidates=[p for p in points if p[0] not in located and xmin<=p[1]<=xmax and ymin<=p[2]<=ymax]
            if not candidates:
                continue
            offsets=list(shape.parts)+[len(shape.points)]
            rings=[shape.points[a:b] for a,b in zip(offsets,offsets[1:])]
            for gid,x,y in candidates:
                if sum(ring_contains(ring,x,y) for ring in rings)%2:
                    located[gid]={'neighborhood':r['NM_BAIRRO'],'city':r['NM_MUN'],'state':UFS[r['CD_UF']]}
    output={'source':SOURCE,'reference_year':2022,'imported_at':datetime.now(timezone.utc).isoformat(),'neighborhoods':names,'located':located}
    (ROOT/'data/neighborhoods.json').write_text(json.dumps(output,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(f'{len(names)} official neighborhoods; {len(located)} gyms located',flush=True)

if __name__=='__main__':
    main()
