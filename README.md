# Intelligent Detection Platform

End-to-end MLOps reference platform that takes a predictive ML model from training to a production-grade inference surface. A scikit-learn classifier is registered in **MLflow**, served behind a typed **FastAPI** `/api/predict` endpoint, consumed by an **Angular 22** SPA (zoneless, Signals, Tailwind v4), and audited in **PostgreSQL** so a **Grafana** dashboard can surface data drift over time. **DVC** versions training datasets, and **GitHub Actions** orchestrates tests, image builds, drift-triggered retraining, and required-status-check gates on `main`.

Everything runs from one `docker-compose up`.

## Architecture at a glance

```
                 ┌────────────────┐
                 │  Browser (SPA) │
                 └───────┬────────┘
                         │ HTTPS · static + JSON
                 ┌───────▼────────┐
                 │     Nginx      │  serves Angular bundle, proxies /api
                 └───────┬────────┘
                         │ HTTP · JSON
                 ┌───────▼────────┐         ┌──────────────┐
                 │   FastAPI      │◀───────▶│   MLflow     │
                 │   /api/predict │ HTTP    │  (registry)  │
                 └───┬────────┬───┘         └──────────────┘
                     │        │ SQL
                     │        ▼
                     │   ┌─────────────┐         ┌──────────┐
                     │   │ PostgreSQL  │────────▶│  Grafana │
                     │   │ inference_  │  read   │  drift   │
                     │   │  logs       │         │  dash    │
                     │   └─────────────┘         └──────────┘
                     │
                     │ artifact pull at startup
                     ▼
                ┌──────────┐         ┌────────────────┐
                │  S3 / CS │◀────────│   DVC + GH     │
                │  (data)  │  track  │   Actions      │
                └──────────┘         └────────────────┘
```

Detail and trade-offs live in [`context/architecture-context.md`](context/architecture-context.md). The user-facing contract is `POST /api/predict` returning `{prediction, probability, latency_ms, model_version}` — and one row written to `inference_logs` per successful call.

## Prerequisites

- **Docker** 24+ and **docker-compose** v2 — the only hard requirement to run the stack.
- **Python** 3.11 and **Node** 20 — only if you want to run tests or develop without Docker.
- A POSIX shell (`bash` or `zsh`). The commands below assume you run them from the repo root.

## Quickstart (5 minutes)

This brings the full stack up and trains a model so you can call `/api/predict` end-to-end.

```bash
# 1. Clone and enter the repo
git clone https://github.com/juanjoseaosrivera/mlpipeline.git
cd mlpipeline

# 2. Boot the infrastructure (Postgres, MLflow, FastAPI, Angular, Grafana)
docker-compose up -d --build

# 3. Apply the database migration (creates `inference_logs`)
docker-compose exec backend_api alembic upgrade head

# 4. Train a baseline model and register it as ProductionModel
docker-compose exec backend_api python -m src.models.train --seed 42

# 5. Restart the API so it picks up the freshly registered model
docker-compose restart backend_api

# 6. Hit the API directly
curl -X POST http://localhost:8000/api/predict \
    -H "Content-Type: application/json" \
    -d '{"feature_1": 0.5, "feature_2": -0.3, "category": 2}'

# 7. Or use the UI — open the workbench in a browser
open http://localhost   # macOS;  use `xdg-open` on Linux
```

Once those steps complete, every UI prediction writes a row to PostgreSQL, MLflow tracks the model lineage, and Grafana renders the operational view.

| Service     | URL                          | Notes                              |
| ----------- | ---------------------------- | ---------------------------------- |
| Angular UI  | http://localhost             | Nginx serves the SPA + proxies /api |
| FastAPI     | http://localhost:8000        | `GET /health`, `POST /api/predict`  |
| MLflow      | http://localhost:5001        | Model registry + run tracking       |
| Grafana     | http://localhost:3000        | login `admin` / `admin`             |
| PostgreSQL  | localhost:5433               | `ai_user` / `securepassword` (dev)  |

## How to use it

### Make a prediction from the UI

1. Visit http://localhost in your browser.
2. Fill the three fields on the prediction workbench:
   - `feature_1` — any decimal (continuous feature)
   - `feature_2` — any decimal (continuous feature)
   - `category` — non-negative integer (e.g., `0`–`4`)
3. Click **Predict**. The submit button disables and a skeleton renders.
4. The result panel shows the predicted class, probability (3 sig figs), measured server-side inference latency, and the MLflow model version.
5. On a server error, the panel surfaces the status code and a **Retry** button that replays your last payload.

### Make a prediction from the CLI

```bash
curl -X POST http://localhost:8000/api/predict \
    -H "Content-Type: application/json" \
    -d '{"feature_1": 0.5, "feature_2": -0.3, "category": 2}'
```

Response:

```json
{
  "prediction": 1,
  "probability": 0.873,
  "latency_ms": 4,
  "model_version": "1"
}
```

### Inspect the audit trail

Every successful prediction lands in `inference_logs` with the input payload (`JSONB`), prediction, probability, latency, model version, timestamp, and a `is_drift_detected` flag.

```bash
docker-compose exec db psql -U ai_user -d mlops_db -c \
    "SELECT id, model_version, prediction, probability, latency_ms, timestamp FROM inference_logs ORDER BY timestamp DESC LIMIT 5;"
```

### View dashboards in Grafana

1. Open http://localhost:3000 and log in (`admin` / `admin`).
2. The dashboard **"MLPipeline — Inference & Drift"** is auto-provisioned from [`monitoring/grafana/dashboards/drift.json`](monitoring/grafana/dashboards/drift.json).
3. Panels: predictions/minute, drift-flag rate/minute, P95 inference latency (red-line at the 150 ms PRD budget), and class distribution over the last 24 hours.

### Run drift detection

The detector reads recent vs. reference windows of inference rows and runs a per-feature Kolmogorov–Smirnov test. If any feature crosses `ALPHA=0.01`, the recent window's rows are flagged `is_drift_detected = TRUE` and the script exits with status code 2 (so cron / CI callers can branch).

```bash
docker-compose exec backend_api python -m src.drift.detector --recent 500 --reference 500
```

Status codes: `0` = no drift, `1` = insufficient data (fewer than `recent + reference` rows), `2` = drift detected.

### Retrain the model

Three triggers, all defined in [`.github/workflows/retrain.yml`](.github/workflows/retrain.yml):

1. **Manual**: `gh workflow run Retrain` (with an optional `seed` input).
2. **Drift-driven**: a downstream script POSTs `repository_dispatch` event `drift_detected` to GitHub.
3. **Scheduled safety net**: Monday 06:00 UTC cron.

The workflow re-runs `src.models.train`, which registers a new MLflow version. Promotion to the `Production` stage is intentionally manual — see [`backend/src/models/README.md`](backend/src/models/README.md) for the runbook.

### Promote a model version to Production

In a Python REPL (or a notebook) against the MLflow tracking server:

```python
import mlflow
client = mlflow.MlflowClient(tracking_uri="http://localhost:5000")
client.transition_model_version_stage(
    name="ProductionModel",
    version="<new-version>",
    stage="Production",
    archive_existing_versions=True,
)
```

The FastAPI container loads `models:/ProductionModel/latest` on next restart. Set `MODEL_URI=models:/ProductionModel/Production` in the environment if you want stage-pinned loads.

## Local development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Lint, type-check, test
ruff check src tests
mypy src
pytest                    # enforces 80% coverage gate

# Run the API against a local Postgres + MLflow (or the compose stack)
export MLFLOW_TRACKING_URI=http://localhost:5001
export DATABASE_URL=postgresql://ai_user:securepassword@localhost:5433/mlops_db
uvicorn src.api.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm test -- --coverage    # Vitest, enforces 80% across lines/funcs/branches/stmts
npm run build             # production bundle into dist/
npm start                 # ng serve at http://localhost:4200
```

The dev server proxies nothing — set `apiBaseUrl` in `src/environments/environment.development.ts` if you point at a non-default backend.

## Data versioning with DVC

```bash
# Configure the remote (one-time; replace with your bucket)
dvc remote modify origin url s3://<your-bucket>/mlpipeline-data

# Materialize the DVC pipeline (prepare + train stages)
dvc repro

# Push tracked artifacts to the remote
dvc push
```

The pipeline graph lives in [`dvc.yaml`](dvc.yaml). The `prepare` stage writes `data/raw/dataset.csv`; the `train` stage depends on that CSV and the training scripts, so DVC re-runs training whenever the dataset or the training code changes.

## Repository layout

```
.
├── backend/                    FastAPI service + ML training + drift detector
│   ├── alembic/                Database migrations (0001_create_inference_logs.py)
│   ├── src/
│   │   ├── api/                FastAPI app, schemas, config, db session, ORM
│   │   ├── models/             Training, dataset prep, registry interaction
│   │   └── drift/              KS-test drift detector
│   └── tests/                  pytest with 80% coverage gate
├── frontend/                   Angular 22 SPA (zoneless, OnPush, Signals)
│   └── src/app/                models · services · components/{prediction-form,result-panel,prediction-workbench}
├── data/                       DVC-tracked datasets (pointers only in git)
├── monitoring/grafana/         Datasource + dashboard provisioning
├── .dvc/, dvc.yaml             DVC config and pipeline graph
├── .github/workflows/          ci.yml + retrain.yml
├── docker-compose.yml          db · mlflow · backend_api · frontend_ui · grafana
├── PRD.md                      Authoritative product spec (v2.0.0)
└── context/                    Project conventions and progress tracker
```

## Tests and CI

- **Backend**: `pytest` runs lint (ruff), type-check (mypy), unit tests, integration tests against a `file://` MLflow store, persistence tests against sqlite-in-memory, drift tests, and a 100-request P95 latency check (<150 ms). Coverage gate at 80%.
- **Frontend**: `npm test -- --coverage` runs Vitest specs for `MlService` (POST + 422/500/0 error mapping), `PredictionFormComponent` (validity, pending state, submit gating), and `ResultPanelComponent` (empty / loading / success / error). Coverage gate at 80% across lines/functions/branches/statements.
- **CI**: Every push and PR runs both suites, then builds the backend and frontend Docker images via `docker/build-push-action`. On merges to `main`, the images are pushed to `ghcr.io/juanjoseaosrivera/mlpipeline-{backend,frontend}:{latest,<sha>}`. Workflow lives in [`.github/workflows/ci.yml`](.github/workflows/ci.yml); pipeline budget is 10 minutes (`timeout-minutes: 10` per job, `concurrency.cancel-in-progress` for the run).

## Required-status-check gate on `main`

A GitHub ruleset on the default branch requires the four CI jobs (`Backend (Pytest)`, `Frontend (Vitest)`, `Backend image`, `Frontend image`) to pass before merge, plus a pull request and no force-push. Direct pushes to `main` are rejected by the platform.

## Configuration

All runtime config comes from environment variables, parsed by `src.api.config.Settings` (pydantic-settings). The defaults are dev-safe; production overrides should set:

| Variable                 | Default                                                            | Notes                                            |
| ------------------------ | ------------------------------------------------------------------ | ------------------------------------------------ |
| `MLFLOW_TRACKING_URI`    | `http://localhost:5000`                                            | `http://mlflow:5000` inside docker-compose       |
| `DATABASE_URL`           | `postgresql://ai_user:securepassword@localhost:5432/mlops_db`      | Replace creds for production                     |
| `MODEL_NAME`             | `ProductionModel`                                                  | MLflow registered model name                     |
| `MODEL_URI`              | `models:/ProductionModel/latest`                                   | Override to pin a stage (`/Production`)          |
| `ALLOWED_ORIGINS`        | `("http://localhost", "http://localhost:4200")`                    | CORS allowlist; comma-separated JSON for arrays  |
| `ENABLE_DOCS`            | `false`                                                            | Set `true` in dev to expose `/docs` and `/redoc` |

## Where to read next

- [`context/project-overview.md`](context/project-overview.md) — vision, stack, user stories.
- [`context/architecture-context.md`](context/architecture-context.md) — components, boundaries, trade-offs.
- [`context/code-standards.md`](context/code-standards.md) — language, tooling, naming, testing.
- [`context/ui-context.md`](context/ui-context.md) — UI principles, flows, design tokens.
- [`context/ai-workflow-rules.md`](context/ai-workflow-rules.md) — ML lifecycle and AI-assistant rules.
- [`context/progress-tracker.md`](context/progress-tracker.md) — phase-by-phase status, ADR index, blocker log.
- [`PRD.md`](PRD.md) — authoritative product spec.
