"""
TouriSense.AI - Dashboard Module 1
Prévisions Annuelles + Mensuelles
Module 2 : Analyse des tendances (Sentiment + Topics)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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

   # --- Module 2 ---
    reviews_dir = base / "reviews"
    df_bert = pd.DataFrame()
    df_topics = pd.DataFrame()
    df_topic_info = pd.DataFrame()

    if reviews_dir.exists():
        if (reviews_dir / "reviews_sample_with_bert.parquet").exists():
            df_bert = pd.read_parquet(reviews_dir / "reviews_sample_with_bert.parquet")
        elif (reviews_dir / "reviews_sample_with_bert.csv").exists():
            df_bert = pd.read_csv(reviews_dir / "reviews_sample_with_bert.csv")

        if (reviews_dir / "reviews_with_topics.parquet").exists():
            df_topics = pd.read_parquet(reviews_dir / "reviews_with_topics.parquet")
        elif (reviews_dir / "reviews_with_topics.csv").exists():
            df_topics = pd.read_csv(reviews_dir / "reviews_with_topics.csv")

        if (reviews_dir / "bertopic_topics_info.csv").exists():
            df_topic_info = pd.read_csv(reviews_dir / "bertopic_topics_info.csv")

    return df_hist, df_forecast, df_metrics, df_monthly, df_monthly_forecast, df_bert, df_topics, df_topic_info


df_hist, df_forecast, df_metrics, df_monthly, df_monthly_forecast, df_bert, df_topics, df_topic_info = load_all_data()

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.title("🕌 TouriSense.AI")
st.sidebar.markdown("---")

module = st.sidebar.radio(
    "Module",
    options=["Module 1 – Forecasting", "Module 2 – Tendances (NLP)"],
    index=0
)

st.sidebar.markdown("---")
# ============================================================
# ===================== MODULE 1 =============================
# ============================================================
if module == "Module 1 – Forecasting":

    st.sidebar.markdown("**Prévision des flux**")
    vue = st.sidebar.radio(
        "Type de prévision",
        options=["Annuel (données réelles)", "Mensuel (synthétique)"],
        index=0
    )

    st.title("Tableau de bord prévisionnel – Tourisme Tunisien")
    st.caption("Prototype TouriSense.AI | Module 1 : Prévision des flux touristiques (Prophet)")

    # ---------- VUE ANNUELLE ----------
    if vue == "Annuel (données réelles)":
        indicateurs_dispo = df_forecast["Indicateur"].unique().tolist() if not df_forecast.empty else list(LABELS.keys())
        indicateur = st.sidebar.selectbox(
            "Indicateur",
            options=indicateurs_dispo,
            format_func=lambda x: LABELS.get(x, x),
        )

        data_f = df_forecast[df_forecast["Indicateur"] == indicateur].copy() if not df_forecast.empty else pd.DataFrame()

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

    # ---------- VUE MENSUELLE ----------
    else:
        st.subheader("Prévisions mensuelles des arrivées touristiques")
        st.caption("Données synthétiques réalistes + modèle Prophet mensuel")

        if df_monthly.empty or df_monthly_forecast.empty:
            st.warning("Données mensuelles non trouvées.")
        else:
            df_monthly["Date"] = pd.to_datetime(df_monthly["Date"])
            df_monthly_forecast["ds"] = pd.to_datetime(df_monthly_forecast["ds"])

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
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_monthly["Date"], y=df_monthly["Arrivees_totales"],
                mode="lines", name="Historique mensuel",
                line=dict(color="#1f77b4", width=2)
            ))
            fig.add_trace(go.Scatter(
                x=df_monthly_forecast["ds"], y=df_monthly_forecast["Prevision"],
                mode="lines", name="Prévision Prophet",
                line=dict(color="#ff7f0e", width=2, dash="dash")
            ))
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
# ===================== MODULE 2 =============================
# ============================================================
else:
    st.sidebar.markdown("**Analyse des tendances**")
    vue_nlp = st.sidebar.radio(
        "Vue NLP",
        options=["Sentiment Analysis", "Topics / Tendances"],
        index=0
    )

    st.title("Analyse des tendances émergentes – Avis touristiques")
    st.caption("Prototype TouriSense.AI | Module 2 : BERT + BERTopic")

    # ---------- SENTIMENT ----------
    if vue_nlp == "Sentiment Analysis":
        if df_bert.empty:
            st.warning("Données de sentiment non trouvées. Lance d'abord le notebook NLP.")
        else:
            # ----- Filtres -----
            st.sidebar.markdown("### Filtres")
            regions = ["Toutes"] + sorted(df_bert["region"].dropna().unique().tolist()) if "region" in df_bert.columns else ["Toutes"]
            region_filter = st.sidebar.selectbox("Région", regions)

            df_filtered = df_bert.copy()
            if region_filter != "Toutes" and "region" in df_filtered.columns:
                df_filtered = df_filtered[df_filtered["region"] == region_filter]

            # ----- KPIs -----
            st.subheader("Indicateurs clés")
            total = len(df_filtered)
            counts = df_filtered["bert_sentiment"].value_counts()
            pct_pos = counts.get("positif", 0) / total * 100 if total > 0 else 0
            pct_neu = counts.get("neutre", 0) / total * 100 if total > 0 else 0
            pct_neg = counts.get("négatif", 0) / total * 100 if total > 0 else 0
            note_moy = df_filtered["rating_5"].mean() if "rating_5" in df_filtered.columns else None

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Avis analysés", f"{total:,}")
            c2.metric("Positif", f"{pct_pos:.1f} %")
            c3.metric("Neutre", f"{pct_neu:.1f} %")
            c4.metric("Négatif", f"{pct_neg:.1f} %")
            if note_moy is not None:
                c5.metric("Note moyenne", f"{note_moy:.2f} / 5")

            st.markdown("---")

            # ----- Graphiques répartition -----
            col_a, col_b = st.columns(2)

            with col_a:
                fig_bar = px.bar(
                    x=counts.index,
                    y=counts.values,
                    color=counts.index,
                    color_discrete_map={"positif": "#2ecc71", "neutre": "#f1c40f", "négatif": "#e74c3c"},
                    labels={"x": "Sentiment", "y": "Nombre d'avis"},
                    title="Distribution des sentiments (BERT)"
                )
                fig_bar.update_layout(showlegend=False, height=380)
                st.plotly_chart(fig_bar, use_container_width=True)

            with col_b:
                fig_pie = px.pie(
                    names=counts.index,
                    values=counts.values,
                    color=counts.index,
                    color_discrete_map={"positif": "#2ecc71", "neutre": "#f1c40f", "négatif": "#e74c3c"},
                    title="Répartition en %"
                )
                fig_pie.update_layout(height=380)
                st.plotly_chart(fig_pie, use_container_width=True)

            # ----- Heatmap Région × Sentiment -----
            if "region" in df_filtered.columns and region_filter == "Toutes":
                st.subheader("Sentiment par région")
                heat = pd.crosstab(df_bert["region"], df_bert["bert_sentiment"], normalize="index") * 100
                # Garder les régions les plus représentées
                top_regions = df_bert["region"].value_counts().head(10).index
                heat = heat.loc[heat.index.isin(top_regions)]
                fig_heat = px.imshow(
                    heat,
                    text_auto=".1f",
                    aspect="auto",
                    color_continuous_scale="RdYlGn",
                    labels=dict(x="Sentiment", y="Région", color="%"),
                    title="Répartition des sentiments par région (%)"
                )
                fig_heat.update_layout(height=420)
                st.plotly_chart(fig_heat, use_container_width=True)

            # ----- Top / Flop hôtels -----
            if "hotel" in df_filtered.columns and "rating_5" in df_filtered.columns:
                st.subheader("Hôtels – Top & Flop")
                hotel_stats = (
                    df_filtered.groupby("hotel")
                    .agg(note_moyenne=("rating_5", "mean"), nb_avis=("rating_5", "count"))
                    .reset_index()
                )
                hotel_stats = hotel_stats[hotel_stats["nb_avis"] >= 5]  # au moins 5 avis

                col_top, col_flop = st.columns(2)
                with col_top:
                    st.markdown("**Top 10 – Mieux notés**")
                    top10 = hotel_stats.sort_values("note_moyenne", ascending=False).head(10)
                    st.dataframe(
                        top10.rename(columns={"hotel": "Hôtel", "note_moyenne": "Note moy.", "nb_avis": "Nb avis"})
                        .style.format({"Note moy.": "{:.2f}"}),
                        use_container_width=True,
                        hide_index=True
                    )
                with col_flop:
                    st.markdown("**Flop 10 – Moins bien notés**")
                    flop10 = hotel_stats.sort_values("note_moyenne", ascending=True).head(10)
                    st.dataframe(
                        flop10.rename(columns={"hotel": "Hôtel", "note_moyenne": "Note moy.", "nb_avis": "Nb avis"})
                        .style.format({"Note moy.": "{:.2f}"}),
                        use_container_width=True,
                        hide_index=True
                    )

            # ----- Comparaison rating vs BERT -----
            if "sentiment_label" in df_filtered.columns:
                st.subheader("Comparaison Note (rating) vs BERT")
                cross = pd.crosstab(df_filtered["sentiment_label"], df_filtered["bert_sentiment"])
                st.dataframe(cross, use_container_width=True)

            # ----- Exemples d'avis -----
            st.subheader("Exemples d'avis")
            sentiment_filter = st.selectbox(
                "Filtrer par sentiment BERT",
                ["Tous", "positif", "neutre", "négatif"]
            )
            sample = df_filtered if sentiment_filter == "Tous" else df_filtered[df_filtered["bert_sentiment"] == sentiment_filter]
            cols_show = [c for c in ["hotel", "region", "rating_5", "bert_sentiment", "bert_score", "content_clean"] if c in sample.columns]
            st.dataframe(sample[cols_show].head(25), use_container_width=True, hide_index=True)

            # Meilleurs / pires selon score BERT
            if "bert_score" in df_filtered.columns:
                st.subheader("Avis les plus confidents (BERT)")
                col_best, col_worst = st.columns(2)
                with col_best:
                    st.markdown("**Très positifs (score élevé)**")
                    best = df_filtered[df_filtered["bert_sentiment"] == "positif"].nlargest(3, "bert_score")
                    for _, row in best.iterrows():
                        st.info(f"**{row.get('hotel', '')}** ({row.get('rating_5', '')}/5)\n\n{row.get('content_clean', '')[:280]}...")
                with col_worst:
                    st.markdown("**Très négatifs (score élevé)**")
                    worst = df_filtered[df_filtered["bert_sentiment"] == "négatif"].nlargest(3, "bert_score")
                    for _, row in worst.iterrows():
                        st.error(f"**{row.get('hotel', '')}** ({row.get('rating_5', '')}/5)\n\n{row.get('content_clean', '')[:280]}...")

    # ---------- TOPICS ----------
    else:
        if df_topics.empty and df_topic_info.empty:
            st.warning("Données de topics non trouvées. Lance d'abord BERTopic dans le notebook.")
        else:
            st.subheader("Thèmes détectés (BERTopic)")

            if not df_topic_info.empty:
                display_topics = df_topic_info[df_topic_info["Topic"] != -1].copy()
                total_docs = display_topics["Count"].sum()
                display_topics["Pourcentage"] = (display_topics["Count"] / total_docs * 100).round(1)

                st.dataframe(
                    display_topics[["Topic", "Count", "Pourcentage", "Name"]].head(15)
                    .rename(columns={"Name": "Mots-clés / Nom", "Count": "Nb avis"}),
                    use_container_width=True,
                    hide_index=True
                )

                fig_topics = px.bar(
                    display_topics.head(10),
                    x="Name",
                    y="Count",
                    title="Taille des principaux topics",
                    labels={"Name": "Topic", "Count": "Nombre d'avis"},
                    color="Count",
                    color_continuous_scale="Blues"
                )
                fig_topics.update_layout(xaxis_tickangle=-40, height=450)
                st.plotly_chart(fig_topics, use_container_width=True)

            if not df_topics.empty and "topic" in df_topics.columns:
                st.subheader("Explorer un topic")
                topic_ids = sorted([t for t in df_topics["topic"].unique() if t != -1])
                selected_topic = st.selectbox("Choisir un topic", topic_ids)

                sample_topic = df_topics[df_topics["topic"] == selected_topic]
                st.caption(f"{len(sample_topic)} avis dans ce topic")

                # Stats du topic
                if "rating_5" in sample_topic.columns:
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Note moyenne", f"{sample_topic['rating_5'].mean():.2f}/5")
                    if "bert_sentiment" in sample_topic.columns:
                        pos = (sample_topic["bert_sentiment"] == "positif").mean() * 100
                        neg = (sample_topic["bert_sentiment"] == "négatif").mean() * 100
                        c2.metric("% Positif", f"{pos:.1f}%")
                        c3.metric("% Négatif", f"{neg:.1f}%")

                cols_show = [c for c in ["hotel", "region", "rating_5", "bert_sentiment", "content_clean"] if c in sample_topic.columns]
                st.dataframe(sample_topic[cols_show].head(15), use_container_width=True, hide_index=True)

# ============================================================
# PIED DE PAGE
# ============================================================
st.markdown("---")
st.caption(
    "TouriSense.AI – Prototype d'aide à la décision | "
    "Module 1 : Prophet | Module 2 : BERT + BERTopic"
)