"""
TouriSense.AI - Module 1 (version mensuelle)
Prévision des arrivées touristiques avec Prophet
"""

import os
import json
import warnings
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error

warnings.filterwarnings("ignore")

# ============================================================
# CONFIGURATION
# ============================================================
DATA_PATH = Path("../../data/processed/toursense_monthly_total.csv")
MODELS_DIR = Path("../../models")
OUTPUT_DIR = Path("../../data/processed")
MODELS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FORECAST_MONTHS = 24  # 2 ans de prévision


def compute_metrics(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mask = y_true != 0
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100 if mask.any() else np.nan
    return {"MAE": round(mae, 1), "RMSE": round(rmse, 1), "MAPE": round(mape, 2)}


# ============================================================
# 1. CHARGEMENT
# ============================================================
print("=" * 65)
print("TouriSense.AI – Prévision mensuelle (Prophet)")
print("=" * 65)

df = pd.read_csv(DATA_PATH)
df["ds"] = pd.to_datetime(df["Date"])
df = df.rename(columns={"Arrivees_totales": "y"})
df = df[["ds", "y"]].sort_values("ds").reset_index(drop=True)

print(f"Données chargées : {len(df)} mois ({df['ds'].min().date()} → {df['ds'].max().date()})")

# ============================================================
# 2. VALIDATION TEMPORELLE
# ============================================================
split_date = "2023-12-31"
train = df[df["ds"] <= split_date].copy()
test = df[df["ds"] > split_date].copy()

print(f"\nTrain : {len(train)} mois (jusqu'à {split_date})")
print(f"Test  : {len(test)} mois")

model_val = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=False,
    daily_seasonality=False,
    seasonality_mode="multiplicative",
    interval_width=0.90,
    changepoint_prior_scale=0.05,
)
model_val.fit(train)

future_val = model_val.make_future_dataframe(periods=len(test), freq="MS")
pred_val = model_val.predict(future_val)

pred_test = pred_val.set_index("ds").loc[test["ds"].values]["yhat"]
metrics = compute_metrics(test["y"].values, pred_test.values)

print("\nMétriques de validation temporelle :")
print(f"  MAE  : {metrics['MAE']:,.1f}")
print(f"  RMSE : {metrics['RMSE']:,.1f}")
print(f"  MAPE : {metrics['MAPE']:.1f} %")

# ============================================================
# 3. MODÈLE FINAL + PRÉVISION
# ============================================================
model = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=False,
    daily_seasonality=False,
    seasonality_mode="multiplicative",
    interval_width=0.90,
    changepoint_prior_scale=0.05,
)
model.fit(df)

future = model.make_future_dataframe(periods=FORECAST_MONTHS, freq="MS")
forecast = model.predict(future)

# ============================================================
# 4. SAUVEGARDE
# ============================================================
model_path = MODELS_DIR / "prophet_monthly_arrivals.joblib"
joblib.dump(model, model_path)
print(f"\nModèle sauvegardé : {model_path}")

last_date = df["ds"].max()
future_forecast = forecast[forecast["ds"] > last_date][
    ["ds", "yhat", "yhat_lower", "yhat_upper"]
].copy()
future_forecast["Annee"] = future_forecast["ds"].dt.year
future_forecast["Mois"] = future_forecast["ds"].dt.month
future_forecast = future_forecast.rename(columns={
    "yhat": "Prevision",
    "yhat_lower": "Lower",
    "yhat_upper": "Upper",
})

csv_path = OUTPUT_DIR / "forecast_monthly_2026_2027.csv"
future_forecast.to_csv(csv_path, index=False)
print(f"Prévisions CSV    : {csv_path}")

json_path = OUTPUT_DIR / "forecast_monthly_2026_2027.json"
future_forecast.to_json(json_path, orient="records", date_format="iso", indent=2)
print(f"Prévisions JSON   : {json_path}")

metrics_path = OUTPUT_DIR / "prophet_monthly_metrics.json"
with open(metrics_path, "w") as f:
    json.dump(metrics, f, indent=2)
print(f"Métriques         : {metrics_path}")

print("\nAperçu des prévisions (prochains 12 mois) :")
print(future_forecast.head(12)[["ds", "Prevision", "Lower", "Upper"]].round(0).to_string(index=False))
print("\n✅ Prévision mensuelle terminée avec succès.")