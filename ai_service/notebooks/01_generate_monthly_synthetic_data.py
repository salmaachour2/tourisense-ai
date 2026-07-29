"""
TouriSense.AI - Génération de données mensuelles synthétiques réalistes
"""

import os
import numpy as np
import pandas as pd
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================
OUTPUT_DIR = Path("../../data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ANNUAL_TOTALS = {
    2015: 5_360_000,
    2016: 5_720_000,
    2017: 7_050_000,
    2018: 8_300_000,
    2019: 9_430_000,
    2020: 1_400_000,
    2021: 2_500_000,
    2022: 6_400_000,
    2023: 8_500_000,
    2024: 9_800_000,
    2025: 11_300_000,
}

NATIONALITY_SHARES = {
    "Algerie": 0.32,
    "Libye": 0.19,
    "France": 0.11,
    "Allemagne": 0.04,
    "Royaume-Uni": 0.035,
    "Italie": 0.02,
    "Belgique": 0.012,
    "Autres_Europe": 0.08,
    "Autres_Maghreb": 0.025,
    "Autres": 0.158,
}

MONTHLY_SEASONALITY = {
    1: 0.055, 2: 0.060, 3: 0.075, 4: 0.085,
    5: 0.090, 6: 0.105, 7: 0.130, 8: 0.135,
    9: 0.100, 10: 0.080, 11: 0.050, 12: 0.035,
}

np.random.seed(42)

# ============================================================
# GÉNÉRATION
# ============================================================
rows = []

for year, total in ANNUAL_TOTALS.items():
    for month in range(1, 13):
        monthly_base = total * MONTHLY_SEASONALITY[month]
        noise = np.random.normal(1.0, 0.08)
        monthly_total = max(0, monthly_base * noise)

        for nationality, share in NATIONALITY_SHARES.items():
            nat_noise = np.random.normal(1.0, 0.05)
            value = monthly_total * share * nat_noise
            value = max(0, round(value))

            rows.append({
                "Annee": year,
                "Mois": month,
                "Date": f"{year}-{month:02d}-01",
                "Nationalite": nationality,
                "Arrivees": value,
            })

df = pd.DataFrame(rows)
df["Date"] = pd.to_datetime(df["Date"])

# Agrégations
monthly_total = (
    df.groupby(["Annee", "Mois", "Date"], as_index=False)["Arrivees"]
    .sum()
    .rename(columns={"Arrivees": "Arrivees_totales"})
)

monthly_pivot = (
    df.pivot_table(
        index=["Annee", "Mois", "Date"],
        columns="Nationalite",
        values="Arrivees",
        aggfunc="sum",
    )
    .reset_index()
)

# Sauvegarde
path_long = OUTPUT_DIR / "toursense_monthly_synthetic_long.csv"
path_total = OUTPUT_DIR / "toursense_monthly_total.csv"
path_pivot = OUTPUT_DIR / "toursense_monthly_by_nationality.csv"

df.to_csv(path_long, index=False)
monthly_total.to_csv(path_total, index=False)
monthly_pivot.to_csv(path_pivot, index=False)

print("=" * 65)
print("Données mensuelles synthétiques générées avec succès")
print("=" * 65)
print(f"→ {path_long}")
print(f"→ {path_total}")
print(f"→ {path_pivot}")
print(f"\nPériode : {df['Annee'].min()} – {df['Annee'].max()}")
print(f"Nombre de lignes : {len(df):,}")
print("\nAperçu du total mensuel :")
print(monthly_total.tail(12).to_string(index=False))