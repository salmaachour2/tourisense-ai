"""
TouriSense.AI - Module 4 : Cartographie intelligente
Étape 2 : Clustering des régions touristiques (KMeans)
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import joblib

warnings.filterwarnings("ignore")

# ============================================================
# CHEMINS
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
INPUT_PATH = PROCESSED / "regions_performance.csv"
OUTPUT_PATH = PROCESSED / "regions_clusters.csv"

MODELS_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("TouriSense.AI – Module 4 | Clustering des régions")
print("=" * 70)

# ============================================================
# 1. CHARGEMENT
# ============================================================
df = pd.read_csv(INPUT_PATH)
print(f"Régions chargées : {len(df)}")
print(df[["region", "capacite_lits", "taux_occupation", "note_moyenne", "nb_avis"]].to_string(index=False))

# ============================================================
# 2. FEATURES POUR LE CLUSTERING
# ============================================================
feature_cols = [
    "capacite_lits",
    "nb_etablissements",
    "taux_occupation",
    "note_moyenne",
    "part_negatif",
]

# Garder seulement les colonnes existantes
feature_cols = [c for c in feature_cols if c in df.columns]

X = df[feature_cols].copy()

# Imputation des valeurs manquantes (médiane)
imputer = SimpleImputer(strategy="median")
X_imputed = imputer.fit_transform(X)

# Standardisation
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_imputed)

print(f"\nFeatures utilisées : {feature_cols}")

# ============================================================
# 3. CHOIX DU NOMBRE DE CLUSTERS (k=3 par défaut)
# ============================================================
# Pour un prototype métier : 3 groupes sont interprétables
# (Fort / Moyen / Fragile)

K = 3
kmeans = KMeans(n_clusters=K, random_state=42, n_init=20)
clusters = kmeans.fit_predict(X_scaled)

df["cluster_id"] = clusters

# ============================================================
# 4. INTERPRÉTATION DES CLUSTERS
# ============================================================
print("\n→ Profil moyen par cluster :")

profile = (
    df.groupby("cluster_id")[feature_cols]
    .mean()
    .round(2)
)
print(profile.to_string())

# Score moyen de performance par cluster (si disponible)
if "score_performance" in df.columns:
    score_by_cluster = df.groupby("cluster_id")["score_performance"].mean().sort_values(ascending=False)
    print("\nScore performance moyen par cluster :")
    print(score_by_cluster.round(3).to_string())

    # Ordre des clusters du plus fort au plus faible
    ordered = score_by_cluster.index.tolist()
else:
    # fallback : trier par taux d'occupation + note
    tmp = df.groupby("cluster_id")[["taux_occupation", "note_moyenne"]].mean()
    tmp["rank_score"] = tmp.mean(axis=1)
    ordered = tmp.sort_values("rank_score", ascending=False).index.tolist()

# Mapping cluster_id -> label métier
label_map = {}
labels_ordered = ["Performante", "Intermédiaire", "Fragile"]

for i, cluster_id in enumerate(ordered):
    label_map[cluster_id] = labels_ordered[i] if i < len(labels_ordered) else f"Groupe {i+1}"

df["cluster_label"] = df["cluster_id"].map(label_map)

print("\n→ Affectation des labels :")
for cid, label in label_map.items():
    regions = df.loc[df["cluster_id"] == cid, "region"].tolist()
    print(f"  Cluster {cid} = {label} → {regions}")

# ============================================================
# 5. SAUVEGARDE
# ============================================================
# Réordonner les colonnes
cols = [
    "region", "cluster_id", "cluster_label",
    "capacite_lits", "nb_etablissements", "taux_occupation",
    "nb_avis", "note_moyenne", "part_negatif", "score_performance"
]
cols = [c for c in cols if c in df.columns]
result = df[cols].sort_values(["cluster_label", "score_performance"], ascending=[True, False])

result.to_csv(OUTPUT_PATH, index=False)

# Sauvegarde des modèles
joblib.dump(kmeans, MODELS_DIR / "kmeans_regions.joblib")
joblib.dump(scaler, MODELS_DIR / "scaler_regions.joblib")
joblib.dump(imputer, MODELS_DIR / "imputer_regions.joblib")
joblib.dump(feature_cols, MODELS_DIR / "regions_features.joblib")

print("\n" + "=" * 70)
print("RÉSULTAT CLUSTERING")
print("=" * 70)
print(result.to_string(index=False))
print(f"\n→ Fichier sauvegardé : {OUTPUT_PATH}")
print(f"→ Modèles sauvegardés dans : {MODELS_DIR}")
print("\n✅ Étape 2 terminée avec succès.")