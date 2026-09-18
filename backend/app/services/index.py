import json
import os
import sqlite3
import unicodedata
from pathlib import Path
from app.config import INDEX_PATH, ROOT

def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(value).casefold()) if not unicodedata.combining(c))

class MediaIndex:
    def __init__(self, path=None):
        self.path = Path(path or INDEX_PATH)
        self.stamp = None
        self._products = []
        self.files = {}
        self.meta = {}
        self.reload()
    def reload(self):
        stamp = self.path.stat().st_mtime_ns if self.path.exists() else None
        if stamp == self.stamp: return
        data = json.loads(self.path.read_text(encoding='utf-8'))
        products = data if isinstance(data,list) else data['products']
        self.meta = {'source':'demo'} if isinstance(data,list) else {k:v for k,v in data.items() if k!='products'}
        self.files = {}
        for p in products:
            p.setdefault('id',p['code'])
            p.setdefault('documents',[])
            for group in ['images','videos','documents']:
                for f in p[group]:
                    if f.get('id'): self.files[f['id']] = f
            p['_search'] = normalize(' '.join(str(p.get(k,'')) for k in ['code','name','reference','ean','description','line','category'])+' '+ ' '.join(f.get('file','') for k in ['images','videos','documents'] for f in p[k]))
        self._products = products
        self.stamp = stamp
    @property
    def products(self):
        self.reload()
        return self._products
    def search(self, query):
        terms = normalize(query).split()
        return [p for p in self.products if all(t in p['_search'] for t in terms)]
    def get(self, key):
        matches = [p for p in self.products if p['id']==key]
        if matches: return matches[0]
        matches = [p for p in self.products if p['code']==key]
        return matches[0] if len(matches)==1 else None

index = MediaIndex()

def public(product):
    return {k:v for k,v in product.items() if not k.startswith('_')}

def views(increment=None):
    path = ROOT / 'backend/data/private/views.sqlite3'
    path.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS views (id TEXT PRIMARY KEY, count INTEGER NOT NULL)')
        if increment:
            db.execute('INSERT INTO views VALUES (?,1) ON CONFLICT(id) DO UPDATE SET count=count+1',(increment,))
        return dict(db.execute('SELECT id,count FROM views'))
