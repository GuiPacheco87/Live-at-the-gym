import json
import sqlite3
import unicodedata
from pathlib import Path
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from contextlib import closing

def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFD',value.lower()) if unicodedata.category(c) != 'Mn')

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        value = query.get('q',[''])[0][:200].lower()
        value = ''.join(c for c in unicodedata.normalize('NFD',value) if unicodedata.category(c) != 'Mn')
        path = Path(__file__).resolve().parents[1]/'data/gyms.db'
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
            db.row_factory = sqlite3.Row
            db.create_function('normalize',1,normalize)
            terms = value.split()
            clauses = ['instr(search_text, ?) > 0']*len(terms)
            for key in ('city','state','neighborhood'):
                term=query.get(key,[''])[0][:200].strip()
                if term:
                    clauses.append(f'instr(normalize({key}), ?) > 0')
                    terms.append(normalize(term))
            provider=query.get('benefit',[''])[0]
            if provider in ('wellhub','totalpass','both'):
                for selected in (['wellhub','totalpass'] if provider=='both' else [provider]):
                    clauses.append("EXISTS (SELECT 1 FROM benefits b WHERE b.gym_id=gyms.id AND b.provider=? AND b.status='yes' AND date(b.checked_at)>=date('now','-30 days'))")
                    terms.append(selected)
            where = ' AND '.join(clauses) or '1=1'
            rows = db.execute('SELECT * FROM gyms WHERE '+where+' ORDER BY name LIMIT 100', terms).fetchall()
        body = json.dumps({'gyms':[dict(row) for row in rows]}, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','public, max-age=300, s-maxage=3600')
        self.end_headers()
        self.wfile.write(body)
