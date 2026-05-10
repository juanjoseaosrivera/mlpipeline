# Progress Tracker

- **Last updated:** 2026-05-10
- **Current phase:** v2.0 build-out complete (P5 awaits visibility unblock for branch protection)
- **Overall status:** All seven phases implemented. P0–P4 🟢, P5 🟡 90% (B-01 blocker on branch protection), P6 🟢. All four user stories closed. Backend, frontend, data ops, drift detection, Grafana dashboards, and retraining workflow are wired.

## 1. Snapshot

| Phase | Name                       | Status        | Progress | Target  |
| ----- | -------------------------- | ------------- | -------- | ------- |
| P0    | Scaffolding                | 🟢 Done       | 100%     | 2026-05-10 |
| P1    | Model + Registry           | 🟢 Done       | 100%     | 2026-05-10 |
| P2    | Inference API              | 🟢 Done       | 100%     | 2026-05-10 |
| P3    | Persistence                | 🟢 Done       | 100%     | 2026-05-10 |
| P4    | UI                         | 🟢 Done       | 100%     | 2026-05-10 |
| P5    | CI/CD                      | 🟡 In progress | 90%      | blocked on visibility |
| P6    | Data ops + drift           | 🟢 Done       | 100%     | 2026-05-10 |

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
- [x] `PredictPayload` and `PredictResponse` interfaces in `frontend/src/app/models/`
- [x] `MlService` posts to `/api/predict` and returns a typed Observable (bridged into Signals at the component boundary with `toSignal()`)

### Components
- [x] `PredictionFormComponent` — Signal Form, per-field validators, OnPush, disabled-while-pending submit
- [x] `ResultPanelComponent` — empty / loading skeleton / success / error states (Tailwind v4 utilities for layout and skeleton shimmer)
- [ ] ~~`RecentPredictionsTableComponent` (read-only, deferred to a later sub-phase if no read endpoint)~~ — deferred: no `GET /api/predictions` endpoint in scope for v2.0; history lives in Grafana per `ui-context.md` Section 4.2.

### Styling
- [x] Tailwind v4 design tokens (color, spacing, typography, radius, elevation) defined in `tailwind.config` (CSS-first via `@theme` in `src/styles.css`, the v4 idiom)
- [x] Dark-mode-first theme wired via `darkMode: 'class'` (v4 equivalent: `@variant dark (&:where(.dark, .dark *));` in `styles.css`; `<html class="dark">` in `index.html`)
- [x] Bundle stays within the budget defined in `ui-context.md` (300kb warn / 400kb error enforced in `angular.json`)

### Tests (Vitest)
- [x] Component specs cover disabled-during-pending, success, and error paths
- [x] Service spec covers HTTP success and HTTP error mapping

**Exit criteria:** A user can fill the form, submit, see a prediction with probability and latency, and see a clear error state when the API is down.

## 7. Phase 5 — CI/CD

> Goal: One pipeline runs both test suites, builds both images, and gates merges on green.

### Tests
- [x] Pytest job in CI with coverage reporting
- [x] Vitest job in CI with coverage reporting (Angular 22 default runner)
- [x] Coverage threshold of 80% enforced for both languages

### Build
- [x] Backend Docker image built on every PR
- [x] Frontend Docker image built on every PR
- [x] Images pushed to a registry on merges to `main`

### Gates
- [ ] 🔵 Branch protection on `main`: tests required, image build required — **blocked**: requires GitHub Pro or public repo (free private repos return HTTP 403 on both `branches/main/protection` and `rulesets` endpoints). Resolve by flipping the repo to public (`gh repo edit --visibility public --accept-visibility-change-consequences`) or upgrading the plan; the required-status-check contexts (`Backend (Pytest)`, `Frontend (Vitest)`, `Backend image`, `Frontend image`) are documented and ready to apply.
- [x] Pipeline duration tracked; target under 10 minutes (`timeout-minutes: 10` on every job; concurrency group cancels superseded runs)

**Exit criteria:** A PR cannot merge into `main` without green tests and successful image builds for both services, and the full pipeline completes in under 10 minutes.

## 8. Phase 6 — Data ops + drift

> Goal: Add data versioning and a drift signal that can trigger retraining.

### DVC
- [x] DVC initialized with a remote backend (S3 or equivalent) — `.dvc/config` carries an `s3://mlpipeline-dvc/REPLACE_ME` placeholder; contributors override with their bucket via `dvc remote modify origin url ...` (no real bucket provisioned in this repo).
- [x] `dvc.yaml` defines train data → model pipeline (two stages: `prepare` writes `data/raw/dataset.csv`, `train` runs `src.models.train` with the csv as a dep)
- [x] `.dvc` files committed; raw data excluded from Git (`/data/raw/`, `/data/processed/`, `.dvc/cache`, `.dvc/tmp`, `.dvc/config.local`)

### Drift
- [x] Drift detection script reads `inference_logs` and computes a signal — `src/drift/detector.py` runs a per-feature two-sample KS test (`scipy.stats.ks_2samp`) over `recent` vs `reference` windows.
- [x] Writes `is_drift_detected = TRUE` on triggering rows (transactional `UPDATE` over the recent window's ids; commits only when at least one feature crosses `ALPHA=0.01`)
- [x] Grafana dashboard renders the drift signal over time (`monitoring/grafana/dashboards/drift.json`: predictions/min, drift-flag-rate/min, P95 latency with 150ms threshold, predicted-class distribution; provisioned datasource + dashboards via `monitoring/grafana/provisioning/`)

### Retraining trigger
- [x] GitHub Actions workflow listens for the drift signal — `.github/workflows/retrain.yml` triggers on `workflow_dispatch`, `repository_dispatch: drift_detected`, and a weekly cron safety net.
- [x] Workflow checks out DVC data, runs training, registers a new MLflow version (`dvc pull` runs only when AWS creds are present in secrets; falls through to the synthetic generator otherwise)
- [x] Promotion to `ProductionModel` remains a manual stage transition (training emits the new version in `None` stage; workflow ends with a `::notice::` pointing at the runbook in `backend/src/models/README.md`)

**Exit criteria:** A simulated drift event populates Grafana, triggers the retraining workflow, and produces a new candidate model in MLflow without auto-promoting it.

## 9. User story tracking

| ID    | User              | Requirement                                                                            | Priority | Phase | Status         |
| ----- | ----------------- | -------------------------------------------------------------------------------------- | -------- | ----- | -------------- |
| US-01 | End user          | Submit a validated form and receive a prediction with probability and latency.         | P0       | P2/P4 | 🟢 Done       |
| US-02 | ML engineer       | Every successful training is automatically registered in MLflow.                       | P0       | P1    | 🟢 Done       |
| US-03 | SRE / ML engineer | Every successful prediction is auditable in PostgreSQL with timestamp and latency.     | P0       | P3    | 🟢 Done       |
| US-04 | Data scientist    | Monitor data drift via Grafana and trigger retraining when thresholds are breached.    | P1       | P6    | 🟢 Done       |

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
| B-01 | Branch protection on `main` returns 403 from both `protection` and `rulesets` endpoints on the free-plan private repo. | P5 exit criterion ("a PR cannot merge into main without green tests") cannot be enforced at the platform layer. | repo owner | 🔵 Open — flip repo to public OR upgrade to GitHub Pro; status-check contexts already named and ready. |

## 14. Recent updates

- **2026-05-10** — Phase 6 (Data ops + drift) complete: DVC scaffolded — `dvc.yaml` defines `prepare` (runs `src.models.prepare`, outputs `data/raw/dataset.csv`) and `train` (runs `src.models.train`, depends on the csv + scripts); `.dvc/config` carries an `s3://...REPLACE_ME` remote placeholder; `.dvcignore` and `.gitignore` exclude `data/raw/` and `.dvc/{cache,tmp,config.local}`. Drift detector at `backend/src/drift/detector.py`: two-sample KS test (`scipy.stats.ks_2samp`) per feature over `recent` vs `reference` windows (defaults 500/500), transactional `UPDATE inference_logs SET is_drift_detected = TRUE` over the recent window when any feature's p-value crosses `ALPHA=0.01`, exits 0/1/2 (no drift / insufficient data / drift) so cron callers can branch. Three drift tests: same distribution → no flags, shifted (mean +3σ) → all 200 recent rows flagged, insufficient rows → `sufficient_data=False`. Grafana service added to `docker-compose.yml` (`grafana/grafana:11.2.2` on `:3000`, `grafana_data` volume, provisioning bind-mount); datasource (`postgres → db:5432/mlops_db`) and dashboards provider (`/var/lib/grafana/dashboards`) auto-loaded; `drift.json` panels: predictions/min, drift-rate/min, P95 latency with 150ms threshold marker, predicted-class distribution (24h default range). Retraining workflow `.github/workflows/retrain.yml`: triggers on `workflow_dispatch` (with seed input), `repository_dispatch: drift_detected`, and a Monday 06:00 UTC cron safety net; conditional `dvc pull` when AWS creds are present; runs `python -m src.models.train` with the run number as seed; ends with an explicit `::notice::` reminding that promotion to `Production` is manual. `scipy==1.14.1` and `dvc[s3]==3.55.2` added to requirements. US-04 closed.
- **2026-05-10** — Phase 5 (CI/CD) mostly complete: workflow rewritten — `Backend (Pytest)` runs ruff + mypy + pytest with `--cov-fail-under=80` (pyproject `[tool.pytest.ini_options]` enforces the gate); `Frontend (Vitest)` runs `npm test -- --coverage` against `vitest.config.ts` thresholds (lines/functions/branches/statements all 80%) + `ng build`; `Backend image` / `Frontend image` jobs build with `docker/build-push-action@v6` and `cache-{to,from}: type=gha` on every PR, pushing `ghcr.io/<owner>/mlpipeline-{backend,frontend}:{latest,<sha>}` only on pushes to `main`; `timeout-minutes: 10` on every job and `cancel-in-progress` concurrency group keeps the budget. Coverage artifacts uploaded on every run. Branch protection blocked (B-01): free private repos return 403 on both `branches/main/protection` and `rulesets` REST endpoints — resolved by flipping visibility or upgrading the plan.
- **2026-05-10** — Phase 4 (UI) complete: typed wire models in `frontend/src/app/models/prediction.model.ts` mirror the Pydantic schemas (plus a tagged-union `PredictionError`); `MlService` POSTs to `${environment.apiBaseUrl}/api/predict` via `inject(HttpClient)`, maps `HttpErrorResponse` to `network | validation | server | unknown` via `catchError`; `PredictionFormComponent` is fully signal-based (per-field `signal()` + `computed()` errors + `canSubmit` gates submit while pending) with OnPush and zoneless control flow (`@if`/`@switch`/`@case`); `ResultPanelComponent` renders empty / loading-skeleton (`animate-pulse motion-reduce:animate-none`) / success / error with a Retry output; `PredictionWorkbenchComponent` owns `pending`/`result`/`error`/`lastPayload` signals, derives the panel's state through `computed()`, and replays the last payload on retry. Tailwind v4 tokens in `src/styles.css` cover color/font/radius/shadow (CSS-first via `@theme`); dark-mode-first wired via `@variant dark`. Vitest specs: `MlService` covers POST + status 422/500/0 mapping; `PredictionFormComponent` covers initial-invalid / valid-when-fields-set / category < 0 invalid / emit-on-valid-submit / no-emit-when-invalid / no-emit-while-pending / button-disabled-when-pending; `ResultPanelComponent` covers empty / loading / success render + retry output. `RecentPredictionsTableComponent` deferred (no read endpoint in scope). US-01 closed.
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
