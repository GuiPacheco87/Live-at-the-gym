"""Recheck only mapped official unit pages; never infer a negative from failure."""
import json
import re
import html
import unicodedata
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse
from fetch_sources import download
ROOT=Path(__file__).resolve().parents[1]
def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFD',s.lower()) if unicodedata.category(c)!='Mn')
def main():
    path=ROOT/'data/benefits.json'
    rows=json.loads(path.read_text(encoding='utf-8'))
    for row in rows:
        expected={'wellhub':'wellhub.com','totalpass':'totalpass.com'}[row['provider']]
        url=urlparse(row['source_url'])
        if url.scheme!='https' or url.hostname!=expected:
            raise ValueError('Benefit URL must be an official provider page')
        if row['status']!='yes' or not row.get('verification_markers'):
            continue
        try:
            text=html.unescape(re.sub('<[^>]+>',' ',download(row['source_url']).decode('utf-8')))
            if all(norm(marker) in norm(text) for marker in row['verification_markers']):
                row['checked_at']=datetime.now(timezone.utc).date().isoformat()
                print('Rechecked',row['gym_id'],row['provider'])
            else:
                row['status']='unknown'
                print('Unit page changed; marked unknown:',row['gym_id'])
        except Exception as error:
            print('Could not recheck',row['gym_id'],type(error).__name__)
    path.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':
    main()
