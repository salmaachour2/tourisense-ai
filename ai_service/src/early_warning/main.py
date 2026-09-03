"""
TouriSense.AI - Module 3 : Système d'alerte précoce
API FastAPI
"""

from pathlib import Path
from typing import List, Optional
from enum import Enum

import pandas as pd
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ============================================================
# CONFIGURATION DES CHEMINS
# ============================================================
# Ce fichier est dans : ai_service/src/early_warning/main.py
# On remonte de 3 niveaux pour arriver à la racine du projet
PROJECT_ROOT = Path(__file__).resolve().parents[3]

ALERTS_CSV = PROJECT_ROOT / "data" / "processed" / "alerts" / "alerts_monthly_v2.csv"
ALERTS_JSON = PROJECT_ROOT / "data" / "processed" / "alerts" / "alerts_monthly_v2.json"

# ============================================================
# APP FASTAPI
# ============================================================
app = FastAPI(
    title="TouriSense.AI - Early Warning API",
    description="API du Module 3 : Système d'alerte précoce (arrivées + sentiment)",
    version="1.0.0",
)

# Autoriser le frontend (Next.js / Streamlit) à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SCHEMAS
# ============================================================
class AlertLevel(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"
    NORMAL = "NORMAL"


class Alert(BaseModel):
    Date: str
    Annee: int
    Mois: int
    Arrivees_reelles: float
    Arrivees_attendues: float
    Ecart_pct: float
    Part_avis_negatifs: Optional[float] = None
    Note_moyenne: Optional[float] = None
    alert_level: str
    alert_message: str


class AlertSummary(BaseModel):
    total_alerts: int
    critical: int
    warning: int
    info: int
    normal: int


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================
def load_alerts() -> pd.DataFrame:
    """Charge le fichier des alertes."""
    if ALERTS_CSV.exists():
        df = pd.read_csv(ALERTS_CSV)
    elif ALERTS_JSON.exists():
        df = pd.read_json(ALERTS_JSON)
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Fichier d'alertes introuvable. Attendu : {ALERTS_CSV}"
        )
    
    # S'assurer que la date est en string
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
    
    return df


# ============================================================
# ENDPOINTS
# ============================================================
@app.get("/")
def root():
    return {
        "service": "TouriSense.AI - Early Warning API",
        "module": 3,
        "status": "running",
        "endpoints": [
            "/alerts",
            "/alerts/latest",
            "/alerts/summary",
            "/health"
        ]
    }


@app.get("/health")
def health():
    alerts_exist = ALERTS_CSV.exists() or ALERTS_JSON.exists()
    return {
        "status": "ok" if alerts_exist else "warning",
        "alerts_file_found": alerts_exist,
        "alerts_path": str(ALERTS_CSV)
    }


@app.get("/alerts", response_model=List[Alert])
def get_all_alerts(
    level: Optional[AlertLevel] = Query(None, description="Filtrer par niveau d'alerte"),
    year: Optional[int] = Query(None, description="Filtrer par année"),
    limit: int = Query(100, ge=1, le=500, description="Nombre maximum d'alertes")
):
    """
    Retourne la liste des alertes.
    Possibilité de filtrer par niveau (CRITICAL, WARNING, INFO) et par année.
    """
    df = load_alerts()

    if level:
        df = df[df["alert_level"] == level.value]

    if year:
        df = df[df["Annee"] == year]

    # Trier du plus récent au plus ancien
    df = df.sort_values("Date", ascending=False).head(limit)

    return df.to_dict(orient="records")


@app.get("/alerts/latest", response_model=List[Alert])
def get_latest_alerts(
    n: int = Query(10, ge=1, le=50, description="Nombre des dernières alertes")
):
    """Retourne les N dernières alertes (les plus récentes)."""
    df = load_alerts()
    df = df.sort_values("Date", ascending=False).head(n)
    return df.to_dict(orient="records")


@app.get("/alerts/summary", response_model=AlertSummary)
def get_alerts_summary():
    """Retourne un résumé du nombre d'alertes par niveau."""
    df = load_alerts()

    # On charge aussi le fichier complet des résultats pour avoir les NORMAL
    full_path = PROJECT_ROOT / "data" / "processed" / "early_warning_full_results_v2.csv"
    
    if full_path.exists():
        full_df = pd.read_csv(full_path)
        counts = full_df["alert_level"].value_counts().to_dict()
    else:
        counts = df["alert_level"].value_counts().to_dict()

    return {
        "total_alerts": int(counts.get("CRITICAL", 0) + counts.get("WARNING", 0) + counts.get("INFO", 0)),
        "critical": int(counts.get("CRITICAL", 0)),
        "warning": int(counts.get("WARNING", 0)),
        "info": int(counts.get("INFO", 0)),
        "normal": int(counts.get("NORMAL", 0)),
    }


# ============================================================
# LANCEMENT
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)