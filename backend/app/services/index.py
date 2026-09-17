import json
import unicodedata
from app.config import INDEX_PATH

def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(value).casefold()) if not unicodedata.combining(c))

class MediaIndex:
    def __init__(self):
        self.products = json.loads(INDEX_PATH.read_text(encoding='utf-8'))
    def search(self, query):
        terms = normalize(query).split()
        return [p for p in self.products if all(t in normalize(' '.join(str(p[k]) for k in ['code','name','reference','ean','description','line','category'])) for t in terms)]
    def get(self, code):
        return next((p for p in self.products if p['code'] == code), None)

index = MediaIndex()
