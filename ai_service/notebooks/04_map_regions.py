"""
TouriSense.AI - Module 4 : Cartographie intelligente
Étape 3 : Carte interactive des régions touristiques
"""

import warnings
from pathlib import Path

import pandas as pd
import folium
from folium.plugins import MarkerCluster

warnings.filterwarnings("ignore")

# ============================================================
# CHEMINS
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUT_HTML = PROCESSED / "regions_map.html"
INPUT_PATH = PROCESSED / "regions_clusters.csv"

print("=" * 70)
print("TouriSense.AI – Module 4 | Carte interactive des régions")
print("=" * 70)

# ============================================================
# 1. COORDONNÉES APPROXIMATIVES DES RÉGIONS
# ============================================================
# Centroïdes approximatifs (latitude, longitude)
REGION_COORDS = {
    "Nabeul - Hammamet": (36.40, 10.62),
    "Sousse - Kairouan": (35.83, 10.64),
    "Monastir - Skanes": (35.78, 10.83),
    "Mahdia - Sfax": (35.50, 11.05),
    "Mahdia": (35.50, 11.05),
    "Tunis - Zaghouan": (36.65, 10.18),
    "Djerba - Zarzis": (33.80, 10.85),
    "Gafsa - Tozeur": (34.10, 8.70),
    "Tozeur - Nefta": (33.92, 8.13),
    "Tabarka - Aïn Draham": (36.95, 8.76),
    "Bizerte - Beja": (37.10, 9.50),
    "Sbeitla - Kasserine": (35.20, 8.80),
}

CLUSTER_COLORS = {
    "Performante": "green",
    "Intermédiaire": "orange",
    "Fragile": "red",
}

CLUSTER_HEX = {
    "Performante": "#27ae60",
    "Intermédiaire": "#f39c12",
    "Fragile": "#e74c3c",
}

# ============================================================
# 2. CHARGEMENT DES DONNÉES
# ============================================================
df = pd.read_csv(INPUT_PATH)
print(f"Régions chargées : {len(df)}")

df["lat"] = df["region"].map(lambda r: REGION_COORDS.get(r, (None, None))[0])
df["lon"] = df["region"].map(lambda r: REGION_COORDS.get(r, (None, None))[1])

missing = df[df["lat"].isna()]["region"].tolist()
if missing:
    print(f"[!] Régions sans coordonnées (ignorées sur la carte) : {missing}")

df_map = df.dropna(subset=["lat", "lon"]).copy()
print(f"Régions affichées sur la carte : {len(df_map)}")

# ============================================================
# 3. CRÉATION DE LA CARTE
# ============================================================
# Centre approximatif de la Tunisie
m = folium.Map(
    location=[34.8, 9.5],
    zoom_start=6,
    tiles="OpenStreetMap",
)

# Légende HTML
legend_html = """
<div style="
    position: fixed;
    bottom: 30px; left: 30px; width: 200px; z-index: 9999;
    background: white; padding: 12px 14px; border: 2px solid #333;
    border-radius: 8px; font-size: 13px; font-family: Arial;
">
<b>Clusters touristiques</b><br>
<span style="color:#27ae60;">●</span> Performante<br>
<span style="color:#f39c12;">●</span> Intermédiaire<br>
<span style="color:#e74c3c;">●</span> Fragile
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# Ajouter un marqueur par région
for _, row in df_map.iterrows():
    label = row.get("cluster_label", "Intermédiaire")
    color = CLUSTER_COLORS.get(label, "blue")

    # Taille du cercle selon capacité (si dispo)
    capacite = row.get("capacite_lits", 0)
    if pd.isna(capacite) or capacite <= 0:
        radius = 12
    else:
        radius = 10 + min(capacite / 3000, 25)

    popup_html = f"""
    <div style="font-family: Arial; min-width: 220px;">
        <h4 style="margin:0 0 8px 0;">{row['region']}</h4>
        <b>Cluster :</b> {label}<br>
        <b>Capacité lits :</b> {row.get('capacite_lits', float('nan')):,.0f}<br>
        <b>Établissements :</b> {row.get('nb_etablissements', float('nan')):,.0f}<br>
        <b>Taux occupation :</b> {row.get('taux_occupation', float('nan')):.1f}%<br>
        <b>Nb avis :</b> {row.get('nb_avis', float('nan')):,.0f}<br>
        <b>Note moyenne :</b> {row.get('note_moyenne', float('nan')):.2f}/5<br>
        <b>Part négatif :</b> {row.get('part_negatif', float('nan')):.1%}<br>
        <b>Score perf. :</b> {row.get('score_performance', float('nan')):.2f}
    </div>
    """

    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=radius,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.75,
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"{row['region']} ({label})",
    ).add_to(m)

# ============================================================
# 4. SAUVEGARDE
# ============================================================
m.save(str(OUTPUT_HTML))

print("\n" + "=" * 70)
print("CARTE GÉNÉRÉE")
print("=" * 70)
print(f"→ Fichier HTML : {OUTPUT_HTML}")
print("Ouvre ce fichier dans ton navigateur pour voir la carte.")
print("\n✅ Étape 3 terminée avec succès.")