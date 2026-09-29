# OasisInsight

AI-driven Ecological Diagnosis and Governance Support for Dryland Oasis Cities

**Institution:** Xinjiang University

**Team:** Chunhui Li · Chao Guo · Xiaxuan Zhang

Precomputed Urumqi ecological research demonstration. Four tabs: Overview, Trajectory Diagnosis, Trustworthy AI, Governance.

## Run
Use Python 3.12 and install `pip install -r requirements.txt`, then `streamlit run app.py`.

## Directory structure
`app.py` is the entrypoint; `utils/` contains data and UI helpers; `assets/` contains the supplied university logo, CSS and evidence figures; `data/` contains precomputed display grids and formal summary tables; `.streamlit/config.toml` defines the theme.

## Main functions
- Overview: four source layers and formal trajectory areas.
- Trajectory Diagnosis: three trajectory maps and vegetation response composition.
- Trustworthy AI: model benchmarks, validation sensitivity, global SHAP and selected feature responses.
- Governance: formal five-zone map and deterministic diagnosis rules.

## Scientific limitations
RF spatial OOF R² is approximately 0.252, not high-accuracy prediction. SHAP is associative, not causal. Event-time contrasts are observational evidence. A scenario selection is not a point-specific diagnosis. Display resampling does not change reported full-resolution areas.

## Streamlit Community Cloud
Upload this directory as the repository root. Select `app.py` as entrypoint and Python 3.12 in Advanced settings. Do not upload the parent research workspace. Confirm the available Python version before deploying; if 3.12 is unavailable, test another supported version before release.

All runtime data is included. No API keys, live training, external GIS service, or Rasterio dependency is needed. Maps are reduced display grids; statistics retain full-resolution source values. Data layer metadata records original source names for provenance, not runtime dependencies.

Contents include research maps, evidence figures, summary metrics and governance rules. A public app exposes these displayed results and downloadable governance statistics. No raw training samples or model objects are included.

This package has not yet been verified on Cloud/Linux. Local tests are not a substitute for public URL tests. Check all four tabs, selectors, images and CSV download after deployment. Keep the local demo as a backup.

Sources: formal project trajectory/governance analyses, benchmark_models and trustworthy_ai results. SHAP describes predictive associations, not causality. Spatial blocks have no buffer; spatial independence is not guaranteed.

Deployment guidance: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
