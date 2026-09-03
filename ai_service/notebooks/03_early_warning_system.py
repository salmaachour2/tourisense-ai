"""
TouriSense.AI - Module 3 : Système d'alerte précoce
Version finale avec chemins robustes
"""

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from prophet import Prophet
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

warnings.filterwarnings("ignore")

# ============================================================
# CHEMINS ROBUSTES (comme preprocessing.py)
# ============================================================
# Ce script est dans : ai_service/notebooks/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = PROJECT_ROOT / "data" / "processed" / "toursense_monthly_total.csv"
REVIEWS_PATH = PROJECT_ROOT / "data" / "processed" / "reviews" / "reviews_cleaned.parquet"
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
ALERTS_DIR = PROJECT_ROOT / "data" / "processed" / "alerts"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ALERTS_DIR.mkdir(parents=True, exist_ok=True)

CONTAMINATION = 0.05
CRITICAL_THRESHOLD = -30
WARNING_THRESHOLD = -15
INFO_THRESHOLD = -8
NEG_SHARE_WARNING = 0.22
NEG_SHARE_CRITICAL = 0.30


# ============================================================
# 1. CHARGEMENT DES ARRIVÉES
# ============================================================
print("=" * 70)
print("TouriSense.AI – Module 3 : Alerte précoce (version finale)")
print("=" * 70)

df = pd.read_csv(DATA_PATH)
df["ds"] = pd.to_datetime(df["Date"])
df = df.rename(columns={"Arrivees_totales": "y"})
df = df[["ds", "y", "Annee", "Mois"]].sort_values("ds").reset_index(drop=True)
print(f"Arrivées chargées : {len(df)} mois")


# ============================================================
# 2. CHARGEMENT DES AVIS
# ============================================================
print("\n→ Chargement des avis...")
if not REVIEWS_PATH.exists():
    raise FileNotFoundError(f"Fichier avis introuvable : {REVIEWS_PATH}")

reviews = pd.read_parquet(REVIEWS_PATH)
print(f"Avis chargés : {len(reviews):,}")

def parse_review_date(date_str):
    if pd.isna(date_str):
        return pd.NaT
    date_str = str(date_str).strip()
    dt = pd.to_datetime(date_str, errors="coerce")
    if pd.notna(dt) and 2000 <= dt.year <= 2026:
        return dt
    for fmt in ["%b %y", "%b %Y", "%B %y", "%B %Y"]:
        try:
            dt = pd.to_datetime(date_str, format=fmt)
            if dt.year < 100:
                dt = dt.replace(year=2000 + dt.year)
            if 2000 <= dt.year <= 2026:
                return dt
        except:
            continue
    return pd.NaT

reviews["date_parsed"] = reviews["date"].apply(parse_review_date)
reviews = reviews.dropna(subset=["date_parsed"]).copy()
reviews["year_month"] = reviews["date_parsed"].dt.to_period("M")

monthly_sentiment = (
    reviews.groupby("year_month")
    .agg(
        n_reviews=("sentiment_label", "count"),
        n_negatif=("sentiment_label", lambda x: (x == "négatif").sum()),
        rating_mean=("rating_5", "mean"),
    )
    .reset_index()
)
monthly_sentiment["neg_share"] = monthly_sentiment["n_negatif"] / monthly_sentiment["n_reviews"]
monthly_sentiment["ds"] = monthly_sentiment["year_month"].dt.to_timestamp()
print(f"Sentiment mensuel : {len(monthly_sentiment)} mois ({monthly_sentiment['ds'].min().date()} → {monthly_sentiment['ds'].max().date()})")


# ============================================================
# 3. FUSION + PROPHET + ISOLATION FOREST
# ============================================================
df = df.merge(monthly_sentiment[["ds", "n_reviews", "neg_share", "rating_mean"]], on="ds", how="left")
df["n_reviews"] = df["n_reviews"].fillna(0)
df["neg_share"] = df["neg_share"].fillna(df["neg_share"].median())
df["rating_mean"] = df["rating_mean"].fillna(df["rating_mean"].median())

print("\n→ Entraînement Prophet...")
model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False,
                seasonality_mode="multiplicative", interval_width=0.90, changepoint_prior_scale=0.05)
model.fit(df[["ds", "y"]])
forecast = model.predict(df[["ds"]])
df["yhat"] = forecast["yhat"].values
df["residual"] = df["y"] - df["yhat"]
df["residual_pct"] = (df["residual"] / df["yhat"]) * 100

df["month_sin"] = np.sin(2 * np.pi * df["Mois"] / 12)
df["month_cos"] = np.cos(2 * np.pi * df["Mois"] / 12)
df["y_lag1"] = df["y"].shift(1)
df["y_lag12"] = df["y"].shift(12)
df["y_rolling_mean_3"] = df["y"].rolling(3).mean()
df["neg_share_lag1"] = df["neg_share"].shift(1)
df["rating_mean_lag1"] = df["rating_mean"].shift(1)

df_feat = df.dropna().copy()
features = ["y", "residual", "residual_pct", "month_sin", "month_cos", "y_lag1", "y_lag12",
            "y_rolling_mean_3", "neg_share", "rating_mean", "n_reviews", "neg_share_lag1", "rating_mean_lag1"]
X = df_feat[features].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print("→ Entraînement Isolation Forest...")
iso_forest = IsolationForest(n_estimators=200, contamination=CONTAMINATION, random_state=42, n_jobs=-1)
df_feat["anomaly_score"] = iso_forest.fit_predict(X_scaled)
df_feat["anomaly_score_raw"] = iso_forest.decision_function(X_scaled)


# ============================================================
# 4. ALERTES
# ============================================================
def assign_alert_level(row):
    residual = row["residual_pct"]
    neg_share = row["neg_share"]
    is_anomaly = row["anomaly_score"] == -1
    if residual <= CRITICAL_THRESHOLD or (residual <= WARNING_THRESHOLD and neg_share >= NEG_SHARE_CRITICAL):
        return "CRITICAL"
    if residual <= WARNING_THRESHOLD or (residual <= INFO_THRESHOLD and neg_share >= NEG_SHARE_WARNING) or (is_anomaly and neg_share >= NEG_SHARE_WARNING):
        return "WARNING"
    if residual <= INFO_THRESHOLD or (is_anomaly and residual < 0) or neg_share >= NEG_SHARE_WARNING:
        return "INFO"
    return "NORMAL"

def generate_message(row):
    if row["alert_level"] == "NORMAL":
        return "Situation normale"
    parts = []
    if row["residual_pct"] < -5:
        parts.append(f"baisse arrivées de {abs(row['residual_pct']):.1f}%")
    if row["neg_share"] >= NEG_SHARE_WARNING:
        parts.append(f"{row['neg_share']*100:.1f}% d'avis négatifs")
    if not parts:
        parts.append("anomalie détectée")
    prefix = {"CRITICAL": "ALERTE CRITIQUE", "WARNING": "Alerte", "INFO": "Signal faible"}
    return f"{prefix.get(row['alert_level'], 'Alerte')} : " + " + ".join(parts)

df_feat["alert_level"] = df_feat.apply(assign_alert_level, axis=1)
df_feat["alert_message"] = df_feat.apply(generate_message, axis=1)

alerts = df_feat[df_feat["alert_level"] != "NORMAL"][
    ["ds", "Annee", "Mois", "y", "yhat", "residual_pct", "neg_share", "rating_mean",
     "anomaly_score_raw", "alert_level", "alert_message"]
].copy()
alerts = alerts.rename(columns={
    "ds": "Date", "y": "Arrivees_reelles", "yhat": "Arrivees_attendues",
    "residual_pct": "Ecart_pct", "neg_share": "Part_avis_negatifs", "rating_mean": "Note_moyenne"
})

print("\n" + "=" * 70)
print("RÉSUMÉ DES ALERTES")
print("=" * 70)
print(df_feat["alert_level"].value_counts())
print(f"\nFichiers seront sauvegardés dans : {ALERTS_DIR}")


# ============================================================
# 5. SAUVEGARDE
# ============================================================
joblib.dump(model, MODELS_DIR / "prophet_early_warning_v2.joblib")
joblib.dump(iso_forest, MODELS_DIR / "isolation_forest_early_warning_v2.joblib")
joblib.dump(scaler, MODELS_DIR / "scaler_early_warning_v2.joblib")

alerts.to_csv(ALERTS_DIR / "alerts_monthly_v2.csv", index=False)
alerts_json = alerts.copy()
alerts_json["Date"] = alerts_json["Date"].dt.strftime("%Y-%m-%d")
alerts_json.to_json(ALERTS_DIR / "alerts_monthly_v2.json", orient="records", indent=2, force_ascii=False)
df_feat.to_csv(OUTPUT_DIR / "early_warning_full_results_v2.csv", index=False)

print(f"\n→ Alertes CSV  : {ALERTS_DIR / 'alerts_monthly_v2.csv'}")
print(f"→ Alertes JSON : {ALERTS_DIR / 'alerts_monthly_v2.json'}")
print("✅ Terminé avec succès.")