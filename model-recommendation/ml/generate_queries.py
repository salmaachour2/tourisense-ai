import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'data' / 'catalog.json'
OUT = ROOT / 'data' / 'user_queries.jsonl'

TEMPLATES = {
    'fr': [
        'Je cherche une {tag} pour {audience}',
        'Destination avec {tag} proche de {governorate}',
        'Quel endroit pour {audience} et {tag} ?'
    ],
    'en': [
        'Looking for a {tag} for {audience}',
        'Place with {tag} near {governorate}',
        'Which destination fits {audience} and {tag} ?'
    ],
    'ar': [
        'أبحث عن {tag} ل{audience}',
        'مكان فيه {tag} قرب {governorate}',
        'ما أفضل وجهة لـ{audience} و{tag}؟'
    ]
}

AUDIENCES = ['famille', 'couple', 'aventuriers', 'families', 'couples', 'adventurers', 'عائلة', 'زوجان']

def load_catalog():
    with CATALOG.open('r', encoding='utf-8') as f:
        return json.load(f)

def generate(n=200):
    catalog = load_catalog()
    tags = set(t for c in catalog for t in c.get('tags', []))
    queries = []
    for _ in range(n):
        lang = random.choice(['fr','en','ar'])
        tag = random.choice(list(tags)) if tags else 'plage'
        audience = random.choice(AUDIENCES)
        gov = random.choice(catalog)['governorate'] if catalog else ''
        tmpl = random.choice(TEMPLATES[lang])
        q = tmpl.format(tag=tag, audience=audience, governorate=gov)
        queries.append({'lang':lang,'query':q,'governorate':gov})

    with OUT.open('w', encoding='utf-8') as f:
        for q in queries:
            f.write(json.dumps(q, ensure_ascii=False) + '\n')
    print('Wrote', OUT)

if __name__ == '__main__':
    generate(500)
