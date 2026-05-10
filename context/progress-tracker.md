# Progress Tracker

- **Last updated:** 2026-05-10
- **Current phase:** Phase 4 — UI
- **Overall status:** Phases 0–3 complete. PostgreSQL persistence on the critical path of `/api/predict`; row shape mirrors PRD Section 5.2; row-write and DB-unavailable paths both tested. US-03 closed. Ready for Phase 4 (UI).

## 1. Snapshot

| Phase | Name                       | Status        | Progress | Target  |
| ----- | -------------------------- | ------------- | -------- | ------- |
| P0    | Scaffolding                | 🟢 Done       | 100%     | 2026-05-10 |
| P1    | Model + Registry           | 🟢 Done       | 100%     | 2026-05-10 |
| P2    | Inference API              | 🟢 Done       | 100%     | 2026-05-10 |
| P3    | Persistence                | 🟢 Done       | 100%     | 2026-05-10 |
| P4    | UI                         | ⚪ Not started | 0%       | TBD     |
| P5    | CI/CD                      | ⚪ Not started | 0%       | TBD     |
| P6    | Data ops + drift           | ⚪ Not started | 0%       | TBD     |

Status icons: 🟢 Done · 🟡 In progress · 🔵 Blocked · ⚪ Not started · 🔴 At risk.

## 2. Phase 0 — Scaffolding

> Goal: Stand up the repository, the empty service skeletons, and a docker-compose stack that boots without errors.

### Repository scaffolding
- [x] PRD authored and approved (`PRD.md` v2.0.0)
- [x] Context folder generated (`context/`)
- [x] Initialize Git repository and `.gitignore` for Python + Node
- [x] Top-level directory layout per PRD Section 5.1
- [x] `README.md` at repo root pointing at `context/` for newcomers

### Backend skeleton
- [x] `backend/` package layout (`src/api/`, `src/models/`, `tests/`)
- [x] `backend/requirements.txt` pinned (FastAPI, Uvicorn, Pydantic, MLflow, SQLAlchemy, psycopg2-binary)
- [x] `backend/Dockerfile` (Uvicorn entrypoint)
- [x] `backend/src/api/main.py` — minimal `FastAPI()` with health endpoint

### Frontend skeleton
- [x] `frontend/` Angular 22.0.0 project initialized (`ng new` with `--standalone --style=css --ssr=false`)
- [x] `frontend/package.json` pins `@angular/core@22.0.0` and TypeScript 5.9
- [x] Tailwind CSS v4 installed (`tailwindcss`, `@tailwindcss/postcss`, `postcss`) with `.postcssrc.json` and `@import "tailwindcss";` in `src/styles.css`
- [x] Vitest configured as the test runner (the v22 default)
- [x] Zoneless bootstrap in `main.ts` (no `Zone.js` import)
- [x] `frontend/Dockerfile` multi-stage (Node build → Nginx serve)
- [x] Routing configured for the prediction workbench placeholder

### Infrastructure baseline
- [x] `docker-compose.yml` with `db`, `mlflow`, `backend_api`, `frontend_ui`
- [x] PostgreSQL volume + healthcheck
- [x] MLflow service reachable on `:5000`
- [x] Stack boots cleanly from `docker-compose up`

### CI baseline
- [x] `.github/workflows/ci.yml` skeleton with Python and Node matrix
- [x] No-op test step on each language to prove wiring

**Exit criteria:** `docker-compose up` brings the four services online, the FastAPI health endpoint responds 200, the Angular placeholder renders, and CI runs to green on a no-op test.

## 3. Phase 1 — Model + Registry

> Goal: Train a baseline classifier and register it in MLflow as `ProductionModel`.

### Training
- [x] Training script under `backend/src/models/train.py`
- [x] Deterministic train/val/test split with logged seed
- [x] Logs hyperparameters and metrics to MLflow
- [x] Held-out test metrics meet a documented baseline

### Registry
- [x] MLflow tracking URI parameterized via env
- [x] Trained model registered as `ProductionModel`
- [x] Stage transition (Staging → Production) documented

### Tests
- [x] Unit tests for any data-prep functions
- [x] Smoke test that loads the registered model and predicts on a fixture row

**Exit criteria:** A fresh MLflow registry contains `ProductionModel/latest`, loadable from Python with the same artifact URI the API will use.

## 4. Phase 2 — Inference API

> Goal: Implement `POST /api/predict` end-to-end with the model singleton, CORS, and the latency budget.

### Schemas
- [x] `PredictPayload` Pydantic model in `backend/src/api/schemas.py`
- [x] `PredictResponse` Pydantic model

### Endpoint
- [x] Model loaded once on FastAPI startup (singleton)
- [x] `POST /api/predict` validates, infers, and returns prediction + probability + latency
- [x] Latency measured around the inference call only
- [x] Errors return HTTP 500 with a generic detail; specifics logged

### Security
- [x] CORS allowlist configured to the Angular origin
- [x] No introspection or admin endpoints exposed

### Tests
- [x] Unit tests for the endpoint with a fake model
- [x] Integration test against MLflow + a registered fixture model
- [x] P95 latency check under 150 ms with fixture model

**Exit criteria:** `curl` against `/api/predict` from the Angular origin returns a typed JSON response within budget; same call from a disallowed origin is rejected by CORS.

## 5. Phase 3 — Persistence

> Goal: Persist every successful inference to PostgreSQL and verify the schema supports drift queries.

### Schema
- [x] Alembic initialized
- [x] Migration creates `inference_logs` per PRD Section 5.2
- [x] `idx_timestamp` index in place

### Write path
- [x] SQLAlchemy session dependency wired into FastAPI
- [x] Inference handler inserts a row on success
- [x] Insertion failure returns HTTP 500 (no silent swallowing)

### Tests
- [x] Integration test asserts the row shape matches the PRD schema
- [x] Test for the "DB unavailable" error path

**Exit criteria:** Every successful prediction in dev produces exactly one `inference_logs` row with correct values for all required columns.

## 6. Phase 4 — UI

> Goal: Ship the prediction workbench: reactive form, typed service, result panel, error states.

### Models and services
- [ ] `PredictPayload` and `PredictResponse` interfaces in `frontend/src/app/models/`
- [ ] `MlService` posts to `/api/predict` and returns a typed Observable (bridged into Signals at the component boundary with `toSignal()`)

### Components
- [ ] `PredictionFormComponent` — Signal Form, per-field validators, OnPush, disabled-while-pending submit
- [ ] `ResultPanelComponent` — empty / loading skeleton / success / error states (Tailwind v4 utilities for layout and skeleton shimmer)
- [ ] `RecentPredictionsTableComponent` (read-only, deferred to a later sub-phase if no read endpoint)

### Styling
- [ ] Tailwind v4 design tokens (color, spacing, typography, radius, elevation) defined in `tailwind.config`
- [ ] Dark-mode-first theme wired via `darkMode: 'class'`
- [ ] Bundle stays within the budget defined in `ui-context.md`

### Tests (Vitest)
- [ ] Component specs cover disabled-during-pending, success, and error paths
- [ ] Service spec covers HTTP success and HTTP error mapping

**Exit criteria:** A user can fill the form, submit, see a prediction with probability and latency, and see a clear error state when the API is down.

## 7. Phase 5 — CI/CD

> Goal: One pipeline runs both test suites, builds both images, and gates merges on green.

### Tests
- [ ] Pytest job in CI with coverage reporting
- [ ] Vitest job in CI with coverage reporting (Angular 22 default runner)
- [ ] Coverage threshold of 80% enforced for both languages

### Build
- [ ] Backend Docker image built on every PR
- [ ] Frontend Docker image built on every PR
- [ ] Images pushed to a registry on merges to `main`

### Gates
- [ ] Branch protection on `main`: tests required, image build required
- [ ] Pipeline duration tracked; target under 10 minutes

**Exit criteria:** A PR cannot merge into `main` without green tests and successful image builds for both services, and the full pipeline completes in under 10 minutes.

## 8. Phase 6 — Data ops + drift

> Goal: Add data versioning and a drift signal that can trigger retraining.

### DVC
- [ ] DVC initialized with a remote backend (S3 or equivalent)
- [ ] `dvc.yaml` defines train data → model pipeline
- [ ] `.dvc` files committed; raw data excluded from Git

### Drift
- [ ] Drift detection script reads `inference_logs` and computes a signal
- [ ] Writes `is_drift_detected = TRUE` on triggering rows
- [ ] Grafana dashboard renders the drift signal over time

### Retraining trigger
- [ ] GitHub Actions workflow listens for the drift signal
- [ ] Workflow checks out DVC data, runs training, registers a new MLflow version
- [ ] Promotion to `ProductionModel` remains a manual stage transition

**Exit criteria:** A simulated drift event populates Grafana, triggers the retraining workflow, and produces a new candidate model in MLflow without auto-promoting it.

## 9. User story tracking

| ID    | User              | Requirement                                                                            | Priority | Phase | Status         |
| ----- | ----------------- | -------------------------------------------------------------------------------------- | -------- | ----- | -------------- |
| US-01 | End user          | Submit a validated form and receive a prediction with probability and latency.         | P0       | P2/P4 | ⚪ Not started |
| US-02 | ML engineer       | Every successful training is automatically registered in MLflow.                       | P0       | P1    | 🟢 Done       |
| US-03 | SRE / ML engineer | Every successful prediction is auditable in PostgreSQL with timestamp and latency.     | P0       | P3    | 🟢 Done       |
| US-04 | Data scientist    | Monitor data drift via Grafana and trigger retraining when thresholds are breached.    | P1       | P6    | ⚪ Not started |

## 10. Evaluation metrics (latest run)

| Metric                       | Baseline | Target  | Latest | Δ |
| ---------------------------- | -------- | ------- | ------ | - |
| Backend P95 inference latency| —        | < 150ms | —      | — |
| CI pipeline duration         | —        | < 10min | —      | — |
| Backend test coverage        | —        | ≥ 80%   | —      | — |
| Frontend test coverage       | —        | ≥ 80%   | —      | — |
| Angular FCP                  | —        | < 1s    | —      | — |

This table is regenerated by CI once the eval harness exists. Do not hand-edit `Latest` or `Δ`.

## 11. Decision log (ADRs)

| #     | Title                                                            | Status   | Date       |
| ----- | ---------------------------------------------------------------- | -------- | ---------- |
| 0001  | Decoupled Angular + FastAPI microservices over a monolith         | Accepted | 2026-05    |
| 0002  | MLflow as the model registry                                      | Accepted | 2026-05    |
| 0003  | DVC for dataset versioning                                        | Accepted | 2026-05    |
| 0004  | PostgreSQL `inference_logs` as the drift substrate                | Accepted | 2026-05    |
| 0005  | Model loaded as a process-local singleton on API startup          | Accepted | 2026-05    |
| 0006  | CORS allowlist over a same-origin proxy in dev                    | Accepted | 2026-05    |
| 0007  | Pin Angular 22.0.0 (May 2026) over the PRD's "Angular 18+" floor  | Accepted | 2026-05-10 |
| 0008  | Tailwind CSS v4 as the frontend styling system                    | Accepted | 2026-05-10 |
| 0009  | Vitest as the frontend test runner (Angular 22 default), not Karma| Accepted | 2026-05-10 |

ADR full text lives in `docs/adr/NNNN-*.md` (to be added).

## 12. Open questions

- Production deployment target (cloud provider, orchestrator) — deferred past v2.0.
- Authentication/authorization model — none in v2.0; revisit before any non-trivial multi-user use.
- Drift detection algorithm and thresholds — to be defined during Phase 6 with the data science owner.
- Whether the SPA should expose a read endpoint over `inference_logs` for the recent-predictions table, or rely on Grafana for history.

## 13. Blockers and risks

| ID  | Item | Impact | Owner | Status |
| --- | ---- | ------ | ----- | ------ |
| —   | —    | —      | —     | —      |

## 14. Recent updates

- **2026-05-10** — Phase 3 (Persistence) complete: Alembic initialized with `alembic.ini` + `env.py` reading `DATABASE_URL` from `Settings`; migration `0001_create_inference_logs.py` creates the table per PRD Section 5.2 (`SERIAL` PK, `TIMESTAMPTZ DEFAULT NOW()`, `VARCHAR(50)`, `JSONB`, `INT`, `FLOAT`, `INT`, `BOOLEAN DEFAULT FALSE`) plus `idx_timestamp`; ORM `InferenceLog` uses `JSONB().with_variant(JSON(), "sqlite")` for portable tests; `create_app` factory now also accepts a `session_factory`, builds one from `Settings.database_url` by default, and disposes the engine on shutdown; `/api/predict` inserts the row on the inference path and returns HTTP 500 ("Persistence Error") with full traceback in logs on `SQLAlchemyError` — never silently swallowed; tests: shared `conftest.py` fixture with sqlite-in-memory + `StaticPool` (schema persists across the request), `test_predict_persistence` asserts every PRD column on a read-back row and a `BrokenSession` factory exercises the DB-down 500 path. US-03 closed.
- **2026-05-10** — Phase 2 (Inference API) complete: `PredictPayload`/`PredictResponse` Pydantic schemas with `extra="forbid"` and bounded `category`/`probability` fields; `create_app()` factory wires a lifespan singleton that resolves `ProductionModel`'s latest version via `MlflowClient.get_latest_versions` and loads it once with `mlflow.sklearn.load_model`; `POST /api/predict` measures latency strictly around `predict`/`predict_proba` (PRD 150ms budget), returns `HTTPException(500, "Inference Error")` on any inference failure (full traceback logged), Swagger/Redoc/openapi disabled by default (`enable_docs=False`), CORS allowlist sourced from `Settings.allowed_origins`. Three test tiers: unit (fake model — success, schema validation, exploding model 500, CORS allow/deny, docs disabled), integration (`file://` MLflow + train_and_register fixture), P95 latency (100 reqs, asserts `latency_ms` P95 < 150).
- **2026-05-10** — Phase 1 (Model + Registry) complete: `Settings` reads `MLFLOW_TRACKING_URI` from env via `pydantic-settings`; `src.models.data` generates a 3-feature synthetic dataset and splits deterministically (seed=42, 60/20/20) — shape mirrors `PredictPayload`; `src.models.train` fits `RandomForestClassifier`, logs params + val/test metrics to MLflow, refuses to register below `BASELINE_TEST_ACCURACY=0.70`, registers as `ProductionModel`; stage-transition runbook documented in `backend/src/models/README.md`; `tests/test_data.py` covers shape/determinism/partitioning; `tests/test_train_smoke.py` runs train → register → `models:/ProductionModel/latest` load → predict against a `file://` tracking store. US-02 closed.
- **2026-05-10** — Phase 0 scaffolding complete: git repo initialized; PRD layout (`backend/`, `frontend/`, `data/`, `.github/workflows/`, `docker-compose.yml`) in place; backend FastAPI skeleton with `/health` and Pytest fixture; Angular 22.0.0 frontend with zoneless bootstrap, Signals-ready, Tailwind v4 (`@tailwindcss/postcss`, CSS-first `@theme`), Vitest via `@angular/build:unit-test`; multi-stage Nginx image with `/api/` reverse proxy; docker-compose with healthchecks for `db`, `mlflow`, `backend_api`; CI workflow runs Pytest + Vitest + builds.
- **2026-05-10** — Frontend stack pinned to Angular 22.0.0 + Tailwind CSS v4 + Vitest across context docs (ADRs 0007–0009). Supersedes the PRD's "Angular 18+" and "Karma/Jasmine" lines.
- **2026-05-10** — Context folder bootstrapped (`project-overview.md`, `architecture-context.md`, `code-standards.md`, `ai-workflow-rules.md`, `ui-context.md`, `progress-tracker.md`) from `PRD.md` v2.0.0.

## 15. How to update this document

- Flip a checkbox in the same PR that ships the work; do not batch checkbox flips.
- When a phase's checked-item ratio crosses a 5% bucket, update the snapshot table.
- When a phase moves to 🟢 Done, update the `Current phase` header to the next phase and add an entry to "Recent updates."
- When an open question is resolved, write an ADR under `docs/adr/`, add a row to the decision log, and remove the question from Section 12.
- When a new requirement is added, append a checkbox in the appropriate phase. Do not silently delete existing checkboxes — strike them through with a one-line note if they are obsolete.
- Append "Recent updates" entries newest-first with a date stamp. One line per update.
- Do not hand-edit the `Latest` and `Δ` columns of the evaluation metrics table; CI owns them.
- Do not wipe completed checkboxes or the recent-updates log when refreshing this document.

## Source

Initialized from `PRD.md` v2.0.0 (Section 7 KPIs, Section 4 requirements, Section 5 schema). Cross-references `project-overview.md` (roadmap, user stories) and `architecture-context.md` (component-to-phase map).
