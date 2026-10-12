import re
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
OUT_DIR = DATA_DIR / 'cleaned'
OUT_DIR.mkdir(exist_ok=True)

YEAR_RE = re.compile(r'20\d{2}')

def find_header_row(df):
    for i in range(min(10, len(df))):
        row = df.iloc[i].astype(str).str.lower()
        if row.str.contains(YEAR_RE).any() or row.str.contains('2015').any():
            return i
    # fallback: first row with more than one non-null cell
    for i in range(min(10, len(df))):
        if df.iloc[i].count() > 1:
            return i
    return 0

def clean_file(path: Path):
    print('Processing', path.name)
    try:
        df = pd.read_csv(path, sep=';', header=None, engine='python', encoding='utf-8', dtype=str)
    except Exception:
        df = pd.read_csv(path, sep=';', header=None, engine='python', encoding='latin-1', dtype=str)

    # Drop fully empty columns
    df = df.dropna(axis=1, how='all')

    header_idx = find_header_row(df)
    header = df.iloc[header_idx].fillna('').astype(str).str.strip()
    data = df.iloc[header_idx+1:].reset_index(drop=True)
    data.columns = [c if c != '' else f'col_{i}' for i, c in enumerate(header)]

    # Save cleaned CSV
    out_path = OUT_DIR / path.name
    data.to_csv(out_path, index=False, encoding='utf-8')
    print('Wrote', out_path)

def main():
    csvs = list(DATA_DIR.glob('*.csv'))
    if not csvs:
        print('No CSV files found in', DATA_DIR)
        return
    for c in csvs:
        clean_file(c)

if __name__ == '__main__':
    main()
