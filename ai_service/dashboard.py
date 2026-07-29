"""
TouriSense.AI - Dashboard Module 1
Prévisions Annuelles + Mensuelles
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="TouriSense.AI | Module Prévision",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="expanded",
)

LABELS = {
    "wb_arrivals": "Arrivées touristiques",
    "recettes_devises": "Recettes (TND)",
    "capacite_lits": "Capacité en lits",
    "taux_occupation": "Taux d'occupation (%)",
    "emplois": "Emplois touristiques",
}

# ============================================================
# CHARGEMENT DES DONNÉES
# ============================================================
@st.cache_data
def load_all_data():
    candidates = [
        Path(__file__).parent.parent / "data" / "processed",
        Path("../data/processed"),
        Path("../../data/processed"),
        Path("data/processed"),
    ]

    base = None
    for c in candidates:
        if (c / "toursense_all_annual_long.csv").exists() or (c / "toursense_monthly_total.csv").exists():
            base = c
            break

    if base is None:
        st.error("Dossier data/processed introuvable.")
        st.stop()

    # --- Annuelles ---
    df_hist = pd.read_csv(base / "toursense_all_annual_long.csv") if (base / "toursense_all_annual_long.csv").exists() else pd.DataFrame()
    df_forecast = pd.read_csv(base / "forecast_summary_2025_2029.csv") if (base / "forecast_summary_2025_2029.csv").exists() else pd.DataFrame()
    df_metrics = pd.read_csv(base / "prophet_metrics_report.csv", index_col=0) if (base / "prophet_metrics_report.csv").exists() else pd.DataFrame()

    # --- Mensuelles ---
    df_monthly = pd.read_csv(base / "toursense_monthly_total.csv") if (base / "toursense_monthly_total.csv").exists() else pd.DataFrame()
    df_monthly_forecast = pd.read_csv(base / "forecast_monthly_2026_2027.csv") if (base / "forecast_monthly_2026_2027.csv").exists() else pd.DataFrame()

    return df_hist, df_forecast, df_metrics, df_monthly, df_monthly_forecast


df_hist, df_forecast, df_metrics, df_monthly, df_monthly_forecast = load_all_data()

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.title("🕌 TouriSense.AI")
st.sidebar.markdown("**Module 1 – Forecasting**")
st.sidebar.markdown("---")

vue = st.sidebar.radio(
    "Type de prévision",
    options=["Annuel (données réelles)", "Mensuel (synthétique)"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.info(
    "Ce tableau de bord présente les prévisions Prophet "
    "annuelles (données réelles) et mensuelles (données synthétiques réalistes)."
)

# ============================================================
# TITRE
# ============================================================
st.title("Tableau de bord prévisionnel – Tourisme Tunisien")
st.caption("Prototype TouriSense.AI | Module 1 : Prévision des flux touristiques (Prophet)")

# ============================================================
# ===================== VUE ANNUELLE ========================
# ============================================================
if vue == "Annuel (données réelles)":

    indicateurs_dispo = df_forecast["Indicateur"].unique().tolist() if not df_forecast.empty else list(LABELS.keys())
    indicateur = st.sidebar.selectbox(
        "Indicateur",
        options=indicateurs_dispo,
        format_func=lambda x: LABELS.get(x, x),
    )

    data_f = df_forecast[df_forecast["Indicateur"] == indicateur].copy() if not df_forecast.empty else pd.DataFrame()

    # Métriques
    col1, col2, col3, col4 = st.columns(4)
    if not data_f.empty:
        for year, col in zip([2025, 2026, 2027, 2028], [col1, col2, col3, col4]):
            row = data_f[data_f["Annee"] == year]
            if not row.empty:
                val = row["Prevision"].values[0]
                low = row["Lower"].values[0]
                up = row["Upper"].values[0]
                col.metric(f"Prévision {year}", f"{val:,.0f}", help=f"IC 90% : [{low:,.0f} – {up:,.0f}]")
            else:
                col.metric(f"Prévision {year}", "N/A")
    else:
        st.warning("Aucune prévision annuelle disponible.")

    st.markdown("---")
    st.subheader(f"Évolution et prévision – {LABELS.get(indicateur, indicateur)}")

    hist = df_hist[df_hist["Dataset"] == indicateur].copy() if not df_hist.empty else pd.DataFrame()
    if not hist.empty:
        hist["Annee"] = hist["Annee"].astype(int)
        hist = hist.sort_values("Annee")

    fig = go.Figure()
    if not hist.empty:
        fig.add_trace(go.Scatter(
            x=hist["Annee"], y=hist["Valeur"],
            mode="lines+markers", name="Historique",
            line=dict(color="#1f77b4", width=2)
        ))
    if not data_f.empty:
        data_f = data_f.sort_values("Annee")
        fig.add_trace(go.Scatter(
            x=data_f["Annee"], y=data_f["Prevision"],
            mode="lines+markers", name="Prévision Prophet",
            line=dict(color="#ff7f0e", width=2, dash="dash")
        ))
        fig.add_trace(go.Scatter(
            x=list(data_f["Annee"]) + list(data_f["Annee"][::-1]),
            y=list(data_f["Upper"]) + list(data_f["Lower"][::-1]),
            fill="toself", fillcolor="rgba(255,127,14,0.15)",
            line=dict(color="rgba(255,255,255,0)"),
            name="Intervalle de confiance 90 %", hoverinfo="skip"
        ))

    fig.update_layout(
        xaxis_title="Année", yaxis_title=LABELS.get(indicateur, "Valeur"),
        hovermode="x unified", height=450,
        legend=dict(orientation="h", y=1.02)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tableau + métriques
    col_left, col_right = st.columns([1.4, 1])
    with col_left:
        st.subheader("Détail des prévisions 2025-2029")
        if not data_f.empty:
            display_df = data_f[["Annee", "Prevision", "Lower", "Upper"]].copy()
            display_df.columns = ["Année", "Prévision", "Borne inf.", "Borne sup."]
            st.dataframe(display_df.style.format({
                "Prévision": "{:,.0f}", "Borne inf.": "{:,.0f}", "Borne sup.": "{:,.0f}"
            }), use_container_width=True, hide_index=True)
    with col_right:
        st.subheader("Performance du modèle")
        if not df_metrics.empty and indicateur in df_metrics.index:
            m = df_metrics.loc[indicateur]
            st.metric("MAE", f"{m['MAE']:,.1f}")
            st.metric("RMSE", f"{m['RMSE']:,.1f}")
            st.metric("MAPE", f"{m['MAPE']:.1f} %")
            st.caption("Validation temporelle (train ≤ 2019)")
        else:
            st.info("Métriques non disponibles.")

# ============================================================
# ===================== VUE MENSUELLE ========================
# ============================================================
else:
    st.subheader("Prévisions mensuelles des arrivées touristiques")
    st.caption("Données synthétiques réalistes + modèle Prophet mensuel")

    if df_monthly.empty or df_monthly_forecast.empty:
        st.warning("Données mensuelles non trouvées. Lance d'abord les scripts de génération et de prévision mensuelle.")
    else:
        # Préparation
        df_monthly["Date"] = pd.to_datetime(df_monthly["Date"])
        df_monthly_forecast["ds"] = pd.to_datetime(df_monthly_forecast["ds"])

        # Métriques rapides (prochains mois)
        prochain = df_monthly_forecast.head(6)
        cols = st.columns(6)
        for i, (_, row) in enumerate(prochain.iterrows()):
            with cols[i]:
                st.metric(
                    f"{row['ds'].strftime('%b %Y')}",
                    f"{row['Prevision']:,.0f}",
                    help=f"IC : [{row['Lower']:,.0f} – {row['Upper']:,.0f}]"
                )

        st.markdown("---")

        # Graphique
        fig = go.Figure()

        # Historique
        fig.add_trace(go.Scatter(
            x=df_monthly["Date"], y=df_monthly["Arrivees_totales"],
            mode="lines", name="Historique mensuel",
            line=dict(color="#1f77b4", width=2)
        ))

        # Prévisions
        fig.add_trace(go.Scatter(
            x=df_monthly_forecast["ds"], y=df_monthly_forecast["Prevision"],
            mode="lines", name="Prévision Prophet",
            line=dict(color="#ff7f0e", width=2, dash="dash")
        ))

        # Intervalle de confiance
        fig.add_trace(go.Scatter(
            x=list(df_monthly_forecast["ds"]) + list(df_monthly_forecast["ds"][::-1]),
            y=list(df_monthly_forecast["Upper"]) + list(df_monthly_forecast["Lower"][::-1]),
            fill="toself", fillcolor="rgba(255,127,14,0.15)",
            line=dict(color="rgba(255,255,255,0)"),
            name="Intervalle de confiance 90 %", hoverinfo="skip"
        ))

        fig.update_layout(
            xaxis_title="Date", yaxis_title="Arrivées touristiques",
            hovermode="x unified", height=500,
            legend=dict(orientation="h", y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Tableau
        st.subheader("Détail des prévisions mensuelles")
        display = df_monthly_forecast[["ds", "Prevision", "Lower", "Upper"]].copy()
        display.columns = ["Date", "Prévision", "Borne inf.", "Borne sup."]
        display["Date"] = display["Date"].dt.strftime("%Y-%m")
        st.dataframe(
            display.style.format({
                "Prévision": "{:,.0f}",
                "Borne inf.": "{:,.0f}",
                "Borne sup.": "{:,.0f}"
            }),
            use_container_width=True,
            hide_index=True
        )

# ============================================================
# PIED DE PAGE
# ============================================================
st.markdown("---")
st.caption(
    "TouriSense.AI – Prototype d'aide à la décision | "
    "Module 1 : Prophet | Données annuelles (réelles) + mensuelles (synthétiques réalistes)"
)