TouriSense.AI — Website Roadmap

Summary of proposal
- Vision: Make TouriSense.AI the national reference tool for anticipating the future of Tunisian tourism by turning dispersed data into unified strategic intelligence for public decision-makers.
- Core missions: centralize multi-source tourism data; provide interpretable predictive analytics; detect early crisis signals; support national/regional strategic decisions.
- Key modules: Forecasting (LSTM/Prophet/XGBoost), Trend detection (NLP: BERT/BERTopic), Early alerting (Anomaly detection / Isolation Forest / time-series), Geospatial mapping & clustering.

High-level website objectives
- Present the platform purpose and modules to public and institutional users.
- Expose dashboards and interactive visualizations (maps, trends, forecasts).
- Provide a backoffice for data ingestion, model management and alerts configuration.
- Reserve clear integration points for ML/DL models and for future APIs.

Milestones (iterative)
1. Discovery & content (this document): extract goals and required pages.
2. Scaffolding: routes, layout components (`frontoffice`, `backoffice`, `shared`), placeholders for dashboards and model APIs.
3. Core pages: `home`, `public`, `institutionnel`, and a basic `backoffice` shell with sample widgets.
4. Data & models placeholders: implement `ModelIntegrationService` + mock endpoints and UI hooks for forecasts, NLP, alerts.
5. Visual polish & theme: finalize Sahara & Méditerranée palette across pages and components.
6. Integrate real models: swap mock endpoints for real model endpoints or microservices; add auth and quotas.
7. Testing & deployment: CI, automated builds, basic e2e or smoke tests.

Routes & page map (initial)
- `/` → Home landing (overview + signal map)
- `/public` → Public-facing summaries & visualization widgets
- `/institutionnel` → Institutional dashboards with richer filters and export
- `/backoffice` → Admin: data sources, model config, alerts

Model integration placeholders (what to reserve now)
- A central `ModelIntegrationService` that exposes typed methods:
  - `getTouristForecast(region, period)` → forecast results
  - `detectTrends(textQuery)` → NLP topic/trend outputs
  - `getAlerts()` / `configureAlert()` → alert rules and triggers
- HTTP API contract (placeholder): JSON request/response shapes documented in-code and mocked by the backoffice during development.

Next steps I can take now
- Scaffold the `ModelIntegrationService` placeholder and document the minimal API (done if you approve).
- Generate route & component stubs for the pages above.
- Add a short developer README describing how to replace mock endpoints with real model services.

Notes
- Keep models decoupled behind a service layer so we can replace implementations (local ML, remote microservice, or third-party APIs) without touching UI components.
- Data privacy and access control should be considered when integrating real datasets and models (auth, logging, rate-limits, data retention).
