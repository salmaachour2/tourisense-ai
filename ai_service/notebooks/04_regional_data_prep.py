"""
TouriSense.AI - Module 4 : Cartographie intelligente
Étape 1 (v2) : Préparation des données régionales (nettoyée)
"""

import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED = PROJECT_ROOT / "data" / "processed"
REVIEWS_PATH = PROCESSED / "reviews" / "reviews_cleaned.parquet"
OUTPUT_PATH = PROCESSED / "regions_performance.csv"

print("=" * 70)
print("TouriSense.AI – Module 4 | Préparation des données régionales (v2)")
print("=" * 70)


def clean_text(s: str) -> str:
    s = str(s)
    s = s.replace("–", "-").replace("—", "-").replace("−", "-")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def extract_region_name(indicateur: str) -> str:
    if pd.isna(indicateur):
        return None

    text = clean_text(indicateur)

    # Ignorer les totaux nationaux
    low = text.lower()
    if "ensemble des régions" in low or "total" == low:
        return None

    # ".... région touristique XXX"
    match = re.search(r"région touristique\s+(.+)$", text, flags=re.IGNORECASE)
    if match:
        return clean_text(match.group(1))

    # Déjà un nom de région (taux_occupation)
    return text


def normalize_official_region(name: str) -> str:
    if not name or str(name).lower() == "nan":
        return None

    name = clean_text(name)
    low = name.lower()

    # Règles d'unification
    if "jerba" in low or "djerba" in low or "zarzis" in low:
        return "Djerba - Zarzis"
    if "nabeul" in low or "hammamet" in low or "yasmine" in low:
        return "Nabeul - Hammamet"
    if "sousse" in low or "kairouan" in low:
        return "Sousse - Kairouan"
    if "tunis" in low or "zaghouan" in low:
        return "Tunis - Zaghouan"
    if "monastir" in low or "skanes" in low or "skanès" in low:
        return "Monastir - Skanes"
    if "mahdia" in low or "sfax" in low:
        return "Mahdia - Sfax"
    if "tozeur" in low or "gafsa" in low or "nefta" in low:
        return "Gafsa - Tozeur"
    if "tabarka" in low or "draham" in low:
        return "Tabarka - Aïn Draham"
    if "bizerte" in low or "bej" in low or "béj" in low:
        return "Bizerte - Beja"
    if "sbeitla" in low or "kasserine" in low:
        return "Sbeitla - Kasserine"

    return name


# Mapping avis -> région officielle
REVIEW_TO_OFFICIAL = {
    "Hammamet": "Nabeul - Hammamet",
    "Nabeul": "Nabeul - Hammamet",
    "Port": "Sousse - Kairouan",  # Port El Kantaoui
    "Sousse": "Sousse - Kairouan",
    "Kairouan": "Sousse - Kairouan",
    "Monastir": "Monastir - Skanes",
    "Mahdia": "Mahdia",
    "Tunis": "Tunis - Zaghouan",
    "Gammarth": "Tunis - Zaghouan",
    "La": "Tunis - Zaghouan",
    "Djerba": "Djerba - Zarzis",
    "Midoun": "Djerba - Zarzis",
    "Houmt": "Djerba - Zarzis",
    "Zarzis": "Djerba - Zarzis",
    "Tozeur": "Tozeur - Nefta",
    "Douz": "Tozeur - Nefta",
    "Tabarka": "Tabarka - Aïn Draham",
}


def load_official_indicator(path: Path, value_name: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["region"] = df["Indicateur"].apply(extract_region_name).apply(normalize_official_region)
    df = df.dropna(subset=["region", "Valeur", "Annee"])
    df["Annee"] = df["Annee"].astype(int)
    df["Valeur"] = pd.to_numeric(df["Valeur"], errors="coerce")
    df = df.dropna(subset=["Valeur"])

    # moyenne sur les 3 dernières années disponibles
    latest_years = sorted(df["Annee"].unique())[-3:]
    df_recent = df[df["Annee"].isin(latest_years)].copy()

    agg = (
        df_recent.groupby("region", as_index=False)
        .agg(**{value_name: ("Valeur", "mean")})
    )
    return agg


print("\n→ Chargement des indicateurs officiels...")
capacite = load_official_indicator(PROCESSED / "capacite_region.csv", "capacite_lits")
etablissements = load_official_indicator(PROCESSED / "etablissements_region.csv", "nb_etablissements")
occupation = load_official_indicator(PROCESSED / "taux_occupation.csv", "taux_occupation")

print(f"  Capacité        : {len(capacite)} régions")
print(f"  Établissements  : {len(etablissements)} régions")
print(f"  Taux occupation : {len(occupation)} régions")

official = capacite.merge(etablissements, on="region", how="outer")
official = official.merge(occupation, on="region", how="outer")
print(f"  → Régions officielles : {len(official)}")
print(official.sort_values("capacite_lits", ascending=False).to_string(index=False))


print("\n→ Agrégation des avis...")
reviews = pd.read_parquet(REVIEWS_PATH)
reviews["region_officielle"] = reviews["region"].map(REVIEW_TO_OFFICIAL)
reviews = reviews.dropna(subset=["region_officielle"])
reviews["is_negatif"] = (reviews["sentiment_label"] == "négatif").astype(int)

reviews_agg = (
    reviews.groupby("region_officielle", as_index=False)
    .agg(
        nb_avis=("sentiment_label", "count"),
        note_moyenne=("rating_5", "mean"),
        part_negatif=("is_negatif", "mean"),
    )
    .rename(columns={"region_officielle": "region"})
)

# garder les zones d'avis suffisamment représentatives
reviews_agg = reviews_agg[reviews_agg["nb_avis"] >= 100].copy()
print(reviews_agg.sort_values("nb_avis", ascending=False).to_string(index=False))


print("\n→ Fusion finale...")
final = official.merge(reviews_agg, on="region", how="outer")

# Ne garder que les régions avec au moins 1 indicateur officiel OU beaucoup d'avis
mask = (
    final["capacite_lits"].notna()
    | final["nb_etablissements"].notna()
    | final["taux_occupation"].notna()
    | (final["nb_avis"].fillna(0) >= 100)
)
final = final[mask].copy()


def safe_norm(s):
    s = pd.to_numeric(s, errors="coerce")
    if s.notna().sum() <= 1 or s.max() == s.min():
        return pd.Series(np.nan, index=s.index)
    return (s - s.min()) / (s.max() - s.min())


final["score_occupation"] = safe_norm(final["taux_occupation"])
final["score_note"] = safe_norm(final["note_moyenne"])
final["score_capacite"] = safe_norm(final["capacite_lits"])
final["score_performance"] = final[["score_occupation", "score_note", "score_capacite"]].mean(axis=1, skipna=True)

cols = [
    "region", "capacite_lits", "nb_etablissements", "taux_occupation",
    "nb_avis", "note_moyenne", "part_negatif", "score_performance"
]
final = final[cols].sort_values("score_performance", ascending=False)
# Fusion des régions synonymes
final = (
    final.groupby("region", as_index=False)
    .agg({
        "capacite_lits": "mean",
        "nb_etablissements": "mean",
        "taux_occupation": "mean",
        "nb_avis": "sum",
        "note_moyenne": "mean",
        "part_negatif": "mean",
        "score_performance": "mean",
    })
)

# Supprimer les régions vides
final = final[final["region"].notna()].copy()
final = final.sort_values("score_performance", ascending=False)

final.to_csv(OUTPUT_PATH, index=False)

print("\n" + "=" * 70)
print("RÉSULTAT FINAL")
print("=" * 70)
print(f"Fichier : {OUTPUT_PATH}")
print(f"Nombre de régions : {len(final)}")
print(final.to_string(index=False))
print("\n✅ Étape 1 (v2) terminée.")