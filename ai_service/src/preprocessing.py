"""
TouriSense.AI - Module 1 (Forecasting)
Etape 1 : Nettoyage des donnees brutes ONTT/INS + World Bank
-------------------------------------------------------------
A placer dans : ai_service/src/preprocessing.py
Puis appele depuis le notebook : ai_service/notebooks/01_forecasting_data_prep.ipynb

Ce script est adapte a la structure REELLE de tes fichiers (verifiee ligne par ligne) :
- Fichiers ONTT/INS : separateur ";", 6 lignes de metadonnees (NoFilter, Unite, Source, Titre, vides),
  puis une ligne d'annees, puis une ligne par indicateur/region/nationalite.
- Fichiers World Bank (API_ST_INT_...) : format Banque Mondiale standard, 4 lignes a sauter,
  colonnes = annees 1960-2025, une ligne par pays (on filtre sur 'TUN').
"""

import pandas as pd
from pathlib import Path

# Ce fichier est dans tourisense-ai/ai_service/src/preprocessing.py
# On remonte de 2 niveaux (src -> ai_service -> tourisense-ai) pour trouver data/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def clean_ontt_file(filepath, indicateur_col_name="Indicateur"):
    """Nettoie un fichier CSV ONTT/INS (format ';' avec en-tete de metadonnees)."""
    with open(filepath, "r", encoding="utf-8-sig", errors="ignore") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    # Reperer la ligne des annees (ex: ;2015;2016;2017...)
    header_idx = None
    for i, line in enumerate(lines):
        parts = [p.strip().strip('"') for p in line.split(";")]
        if any(p.isdigit() and len(p) == 4 for p in parts):
            header_idx = i
            break
    if header_idx is None:
        raise ValueError(f"Pas de ligne d'annees trouvee dans {filepath}")

    header = [p.strip().strip('"') for p in lines[header_idx].split(";")]
    header[0] = indicateur_col_name

    rows = []
    for line in lines[header_idx + 1:]:
        parts = [p.strip().strip('"') for p in line.split(";")]
        if len(parts) != len(header):
            continue
        rows.append(parts)

    df = pd.DataFrame(rows, columns=header)
    df = df[df[indicateur_col_name] != ""]

    year_cols = [c for c in df.columns if c.isdigit()]
    df_long = df.melt(
        id_vars=[indicateur_col_name],
        value_vars=year_cols,
        var_name="Annee",
        value_name="Valeur",
    )
    df_long["Valeur"] = (
        df_long["Valeur"].str.replace(" ", "").str.replace("\xa0", "")
    )
    df_long["Valeur"] = pd.to_numeric(df_long["Valeur"], errors="coerce")
    df_long["Annee"] = df_long["Annee"].astype(int)
    return df_long


def clean_worldbank_file(filepath, indicator_label):
    """Nettoie un fichier World Bank (API_ST_INT_...), garde uniquement la Tunisie (TUN)."""
    df = pd.read_csv(filepath, skiprows=4)
    tun = df[df["Country Code"] == "TUN"]
    year_cols = [c for c in df.columns if c.isdigit()]
    df_long = tun.melt(
        id_vars=["Country Name", "Country Code"],
        value_vars=year_cols,
        var_name="Annee",
        value_name="Valeur",
    )
    df_long["Annee"] = df_long["Annee"].astype(int)
    df_long["Indicateur"] = indicator_label
    return df_long[["Indicateur", "Annee", "Valeur"]].dropna(subset=["Valeur"])


if __name__ == "__main__":
    # --- Fichiers ONTT / INS ---
    ontt_files = {
        "capacite_region": "Capacité d'hébergement par région touristique.csv",
        "capacite_lits": "Capacité en lits.csv",
        "duree_sejour": "Durée moyenne de séjour (en jours).csv",
        "emplois": "Emplois touristiques directs.csv",
        "entrees_tunisiens": "Entrées des tunisiens par voie de transport et poste frontière.csv",
        "entrees_nationalite": "Entrées des voyageurs non résidents par nationalité .csv",
        "etablissements": "Nombre d’établissements touristiques.csv",
        "etablissements_region": "Nombre d'établissements par région touristique.csv",
        "recettes_devises": "Recettes touristiques en devises.csv",
        "taux_occupation": "Taux d'occupation par région touristique.csv",
        "nuitees_nationalite": "Nuitées touristiques globales par nationalité.csv",
        "investissements": "Investissements touristiques.csv",
    }

    all_frames = []
    for key, fname in ontt_files.items():
        path = RAW_DIR / fname
        if not path.exists():
            print(f"[!] Fichier manquant, ignore : {fname}")
            continue
        df = clean_ontt_file(path)
        df["Dataset"] = key
        all_frames.append(df)
        out_path = PROCESSED_DIR / f"{key}.csv"
        df.to_csv(out_path, index=False)
        print(f"[OK] {fname} -> {out_path} ({df.shape[0]} lignes)")

    # --- Fichiers World Bank ---
    wb_files = {
        "wb_arrivals": ("API_ST.INT.ARVL_DS2_en_csv_v2_35089.csv", "Arrivees_touristiques_WB"),
        "wb_departures": ("API_ST.INT.DPRT_DS2_en_csv_v2_35531.csv", "Departs_touristiques_WB"),
        "wb_receipts": ("API_ST.INT.TVLR.CD_DS2_en_csv_v2_38285.csv", "Recettes_touristiques_USD_WB"),
        "wb_expenditures": ("API_ST.INT.XPND.CD_DS2_en_csv_v2_38276.csv", "Depenses_touristiques_USD_WB"),

    }
    for key, (fname, label) in wb_files.items():
        path = RAW_DIR / fname
        if not path.exists():
            print(f"[!] Fichier manquant, ignore : {fname}")
            continue
        df = clean_worldbank_file(path, label)
        df["Dataset"] = key
        all_frames.append(df)
        out_path = PROCESSED_DIR / f"{key}.csv"
        df.to_csv(out_path, index=False)
        print(f"[OK] {fname} -> {out_path} ({df.shape[0]} lignes)")

    # --- Fusion complete (format long, une ligne = un indicateur/an) ---
    if all_frames:
        merged = pd.concat(all_frames, ignore_index=True)
        merged.to_csv(PROCESSED_DIR / "toursense_all_annual_long.csv", index=False)
        print(f"\n[OK] Fusion complete -> {PROCESSED_DIR / 'toursense_all_annual_long.csv'}")
        print(f"Total : {merged.shape[0]} lignes, periode : {merged['Annee'].min()}-{merged['Annee'].max()}")
