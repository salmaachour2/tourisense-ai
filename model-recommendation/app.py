from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

ROOT = Path(__file__).resolve().parent

app = FastAPI(title='TouriSense Recommendation API')

class Req(BaseModel):
    query: str
    lang: str = 'fr'
    governorate: str | None = None
    top_k: int = 5

_model = None
_index = None
_ids = None
_catalog = None

def load_resources():
    global _model, _index, _ids, _catalog
    if _model is None:
        _model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    if _index is None:
        idx_path = ROOT / 'ml_index' / 'catalog.index'
        if not idx_path.exists():
            raise RuntimeError('Index not found. Run ml/build_embeddings.py first.')
        _index = faiss.read_index(str(idx_path))
        with (ROOT / 'ml_index' / 'ids.json').open('r', encoding='utf-8') as f:
            _ids = json.load(f)
    if _catalog is None:
        with (ROOT / 'data' / 'catalog.json').open('r', encoding='utf-8') as f:
            _catalog = {c['id']: c for c in json.load(f)}

@app.post('/recommend')
def recommend(r: Req):
    load_resources()
    q = r.query
    emb = _model.encode([q], normalize_embeddings=True)
    D, I = _index.search(np.array(emb, dtype='float32'), r.top_k)
    results = []
    for score, idx in zip(D[0], I[0]):
        if idx < 0:
            continue
        _id = _ids[idx]
        item = _catalog.get(_id)
        if r.governorate and item.get('governorate') != r.governorate:
            continue
        results.append({
            'id': item['id'],
            'title': item.get('title'),
            'description': item.get('description'),
            'governorate': item.get('governorate'),
            'score': float(score)
        })
    return {'query': q, 'results': results}
