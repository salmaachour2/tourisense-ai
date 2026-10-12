import json
from pathlib import Path
import numpy as np

from sentence_transformers import SentenceTransformer
import faiss

ROOT = Path(__file__).resolve().parents[1]

MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'

def load_catalog(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)

def build(catalog_path: Path, out_dir: Path, model_name=MODEL_NAME):
    catalog = load_catalog(catalog_path)
    texts = [ (c['id'], f"{c.get('title','')} - {c.get('description','')} {' '.join(c.get('tags',[]))}") for c in catalog]

    model = SentenceTransformer(model_name)
    sentences = [t[1] for t in texts]
    embeddings = model.encode(sentences, show_progress_bar=True)
    embeddings = np.asarray(embeddings).astype('float32')

    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / 'embeddings.npy', embeddings)
    with (out_dir / 'ids.json').open('w', encoding='utf-8') as f:
        json.dump([t[0] for t in texts], f, ensure_ascii=False)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    faiss.normalize_L2(embeddings)
    index.add(embeddings)
    faiss.write_index(index, str(out_dir / 'catalog.index'))
    print('Built index, saved to', out_dir)

if __name__ == '__main__':
    catalog = ROOT / 'data' / 'catalog.json'
    out = ROOT / 'ml_index'
    build(catalog, out)
