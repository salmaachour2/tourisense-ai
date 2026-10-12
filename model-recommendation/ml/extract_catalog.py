import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def extract(samples_path: Path, out_path: Path):
    with samples_path.open('r', encoding='utf-8') as f:
        data = json.load(f)

    items = {}
    for s in data.get('samples', []):
        for r in s.get('response', {}).get('results', []):
            _id = r.get('id')
            if _id and _id not in items:
                items[_id] = {
                    'id': _id,
                    'title': r.get('title'),
                    'description': r.get('description'),
                    'tags': r.get('tags', []),
                    'lat': r.get('lat'),
                    'lon': r.get('lon'),
                    'governorate': r.get('governorate')
                }

    out = list(items.values())
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open('w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    # Prefer samples in data/ if present (user may have organized files there)
    samples = ROOT / 'data' / 'samples.json'
    if not samples.exists():
        samples = ROOT / 'samples.json'
    out = ROOT / 'data' / 'catalog.json'
    extract(samples, out)
    print(f'Wrote {out}')
