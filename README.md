# TouriSense.AI

Plateforme nationale d'intelligence artificielle pour l'analyse prédictive et l'aide à la décision dans le secteur touristique tunisien.

## 🎯 Contexte et objectif

Les solutions existantes en IA appliquée au tourisme se concentrent généralement sur un seul problème (prévision de la demande, analyse de sentiments, recommandation...) sans proposer de plateforme intégrée pour les décideurs publics.

**TouriSense.AI** vise à combler ce manque en proposant un prototype de plateforme intégrant plusieurs modules d'intelligence artificielle pour aider les décideurs institutionnels (ex: Fédération Tunisienne du Tourisme) à anticiper les évolutions du secteur.

## 🧩 Modules prévus

| Module | Statut | Description |
|---|---|---|
| **1. Prévision des flux touristiques** | ✅ En cours / réalisé | Prévision par région, mois et pays d'origine (Prophet, LSTM, XGBoost) |
| **2. Analyse des tendances (NLP)** | 🔜 À venir | Analyse des réseaux sociaux, Google Trends, avis clients (BERT, BERTopic) |
| **3. Système d'alerte précoce** | 🔜 Extension | Détection d'anomalies et baisses de réservations (Isolation Forest, VAE) |
| **4. Cartographie intelligente** | 🔜 Extension | Clustering et visualisation géospatiale des régions |

## ✅ Avancement — Module 1 : Forecasting

Le Module 1 (prévision des flux touristiques) est opérationnel à deux niveaux de granularité :

- **Version annuelle** : basée sur des données réelles (Banque Mondiale, indicateurs officiels), modélisée avec **Prophet**.
- **Version mensuelle** : basée sur des données synthétiques réalistes (saisonnalité + répartition par nationalité), faute de données publiques structurées à cette granularité.

Un dashboard interactif **Streamlit** permet de visualiser l'historique, les prévisions, les intervalles de confiance et les métriques du modèle.

📄 Le rapport détaillé du Module 1 est disponible dans `/docs` *(ou indique le vrai chemin si tu l'ajoutes au repo)*.

### Livrables du Module 1

| Fichier | Description |
|---|---|
| `02_forecasting_prophet.ipynb` | Notebook annuel (données réelles) |
| `01_generate_monthly_synthetic_data.py` | Génération des données mensuelles synthétiques |
| `02_forecasting_prophet_monthly.py` | Prévision mensuelle avec Prophet |
| `prophet_*.joblib` | Modèles sérialisés (annuels + mensuel) |
| `forecast_summary_2025_2029.csv` | Prévisions annuelles exportées |
| `forecast_monthly_2026_2027.csv` | Prévisions mensuelles exportées |
| `dashboard.py` | Interface Streamlit (vue annuelle + mensuelle) |

## 🛠️ Stack technique

| Domaine | Technologies |
|---|---|
| Frontend | React.js, Next.js, TypeScript, Tailwind CSS |
| Backend | NestJS |
| Service IA | Python, FastAPI |
| Machine Learning | Scikit-learn, XGBoost, Prophet |
| Deep Learning | TensorFlow/Keras, PyTorch |
| NLP | Hugging Face Transformers, BERT, BERTopic |
| Base de données | PostgreSQL + PostGIS |
| Déploiement | Docker, Docker Compose |
| Suivi des modèles | MLflow |

## 🚀 Lancer le projet en local

```bash
# Cloner le repo
git clone https://github.com/salmaachour2/tourisense-ai.git
cd tourisense-ai

# Installer les dépendances (exemple Python)
pip install -r requirements.txt

# Lancer le dashboard
streamlit run dashboard.py
```
*(adapte cette section selon la structure réelle de ton projet)*




## 📌 Branches

- `main` : version stable
- `branch-salma` : développement Module 1
