# Architecture Context

This document is the technical companion to `project-overview.md`. It describes the components, the boundaries between them, and the reasoning that drove each non-obvious choice.

## 1. Architectural principles

- **Decoupled microservices over a monolith.** The frontend, the inference API, the model registry, and the database are separate services. They share no in-process state. A failure in one (say, MLflow being unreachable on cold start) is contained, and each can be scaled independently.
- **Typed contracts at every hop.** Pydantic on the API boundary, TypeScript interfaces on the client. The same shape is asserted twice; mismatches surface at request time or at compile time, never silently in production.
- **Stateless containers.** Containers carry no local mutable state. State lives in PostgreSQL, MLflow, or DVC-tracked storage. This is a scalability prerequisite, not a future-proofing flourish: replicas must be safe to add and remove.
- **Inference logs are first-class data.** PostgreSQL is not a side-effect; it is the substrate for drift detection, retraining triggers, and audit. The inference write path is on the critical path of the platform's value proposition.
- **One pipeline ties the lifecycle together.** GitHub Actions is the single orchestrator for tests, image builds, and retraining. There is no parallel CI system or hand-run training environment.

## 2. System topology

```
                        ┌────────────────┐
                        │  Browser (SPA) │
                        └───────┬────────┘
                                │ HTTPS · static + JSON
                        ┌───────▼────────┐
                        │     Nginx      │  (serves Angular bundle, proxies /api)
                        └───────┬────────┘
                                │ HTTP · JSON
                        ┌───────▼────────┐         ┌──────────────┐
                        │   FastAPI      │◀───────▶│   MLflow     │
                        │   /api/predict │ HTTP    │  (registry)  │
                        └───┬────────┬───┘         └──────────────┘
                            │        │
                            │        │ SQL
                            │        ▼
                            │   ┌─────────────┐         ┌──────────┐
                            │   │ PostgreSQL  │────────▶│  Grafana │
                            │   └─────────────┘  read   └──────────┘
                            │
                            │ (artifact pull at startup)
                            ▼
                       ┌──────────┐         ┌────────────────┐
                       │  S3 / CS │◀────────│   DVC + GH     │
                       │ (data)   │ track   │   Actions      │
                       └──────────┘         └────────────────┘
```

External anchors: MLflow anchors model lineage and versioning, PostgreSQL anchors operational and drift data, DVC anchors dataset lineage, GitHub Actions anchors all automation.

## 3. Layered architecture

### 3.1 Frontend (Angular 22.0.0)

- **Responsibility:** Render the form, validate inputs, post to `/api/predict`, render the prediction with probability and latency.
- **Key choices:** Standalone components everywhere (modules are out); `ChangeDetectionStrategy.OnPush` (the v22 default for new components); zoneless change detection (Zone.js is no longer included by default in v22); Signals as the primary reactive primitive, with Signal Forms (stable in v22) used in place of the legacy Reactive Forms `FormGroup`; typed `MlService` injected via DI; submit button disabled while the inference request is in flight to prevent duplicate fires; Tailwind CSS v4 (PostCSS plugin via `@tailwindcss/postcss`) for styling.
- **Boundary:** Sends a `PredictPayload` JSON, receives a `PredictResponse` JSON. No direct database or MLflow access.

### 3.2 Edge / gateway (Nginx)

- **Responsibility:** Serve the Angular bundle and reverse-proxy `/api/*` to the FastAPI container.
- **Key choices:** Multi-stage Dockerfile (Node build, Nginx serve) keeps the runtime image small; the proxy keeps the browser on a single origin so the only CORS concern is local development.
- **Boundary:** Public HTTP(S) in, HTTP to internal services out.

### 3.3 Inference API (FastAPI)

- **Responsibility:** Validate inbound payloads, run inference against the in-memory model, persist the result, return prediction + probability + measured latency.
- **Key choices:** Async endpoints under Uvicorn for I/O concurrency; the model is loaded once on startup as a process-local singleton (no per-request load); CORS allowlist is explicit (Angular origin only); failures degrade to HTTP 500 with a generic message — no model-internal detail leaks to clients.
- **Boundary:** JSON in, JSON out, side effect to PostgreSQL.

### 3.4 Model registry (MLflow)

- **Responsibility:** Authoritative store for trained model artifacts, their metrics, and their version history. Loaded by the API as `models:/ProductionModel/latest`.
- **Key choices:** Managed lifecycle through MLflow's stage tags so promotion is explicit; no model artifacts shipped inside the API image.
- **Boundary:** API reads on startup; CI writes after a successful training run.

### 3.5 Storage — PostgreSQL

- **Responsibility:** Persist every successful inference (`inference_logs`).
- **Schema (verbatim from the PRD):**

  ```sql
  CREATE TABLE inference_logs (
      id SERIAL PRIMARY KEY,
      timestamp TIMESTAMPTZ DEFAULT NOW(),
      model_version VARCHAR(50) NOT NULL,
      input_payload JSONB NOT NULL,
      prediction INT NOT NULL,
      probability FLOAT NOT NULL,
      latency_ms INT NOT NULL,
      is_drift_detected BOOLEAN DEFAULT FALSE
  );
  CREATE INDEX idx_timestamp ON inference_logs(timestamp);
  ```

- **Key choices:** `JSONB` for the input payload keeps the schema stable across feature changes; the timestamp index supports the time-bucketed queries Grafana issues for drift dashboards.
- **Boundary:** Written by the API on the inference path; read by Grafana and by the drift-detection workflow.

### 3.6 Data versioning (DVC)

- **Responsibility:** Track dataset versions in S3 / cloud storage, keep `.dvc` pointers in Git so the repo stays small.
- **Key choices:** `dvc.yaml` defines the pipeline graph; CI checks out data deterministically before training.
- **Boundary:** Reads dataset blobs from cloud storage; writes new dataset versions when retraining is triggered.

### 3.7 CI/CD (GitHub Actions)

- **Responsibility:** Run tests, build images, optionally trigger retraining when drift fires.
- **Key choices:** Same workflow file owns both test gates and image build; triggers and matrices are explicit, not implicit.
- **Boundary:** Reads the repo and DVC remote; writes Docker images and (on retraining) MLflow versions.

## 4. Cross-cutting concerns

**Observability.** Latency is measured at the API call site and persisted in `latency_ms` so the same source of truth feeds both audit and dashboards. Grafana reads PostgreSQL directly. Application-level structured logs are out of scope for v2.0; the `inference_logs` table is the v2 observability surface.

**Evaluation.** Training in CI emits standard classification metrics into MLflow. The platform's success metric is operational — P95 inference latency under 150 ms — and is verified at the API layer, not inside the model.

**Security.** CORS is allowlisted to the Angular origin (`http://localhost`, `http://localhost:4200` in dev; production origin in prod via env). Database credentials and model URIs are injected via environment variables. The API surface is `POST /api/predict` only — no introspection endpoints — and exception detail is sanitized before being returned. Containers are stateless and rebuilt from source; secrets never bake in.

**Deployment.** Local orchestration uses `docker-compose.yml` with four services: `db`, `mlflow`, `backend_api`, `frontend_ui`. The frontend image is multi-stage (Node build → Nginx serve). The backend image runs Uvicorn. Production deployment target is left to the host environment but inherits the same compose contract.

## 5. Phased build-out (architecture view)

- **Phase 0 — Scaffolding:** `db`, `mlflow`, `backend_api`, `frontend_ui` placeholders in compose; CI skeleton.
- **Phase 1 — Model + Registry:** Training script and MLflow integration arrive; API still stubbed.
- **Phase 2 — Inference API:** FastAPI implements `/api/predict`, loads the model on startup, returns prediction + probability + latency.
- **Phase 3 — Persistence:** `inference_logs` table created; SQLAlchemy writes wired into the inference path.
- **Phase 4 — UI:** Angular reactive form and typed `MlService` arrive; Nginx multi-stage image finalized.
- **Phase 5 — CI/CD:** Pytest + Karma matrix, image build and push, deploy gate.
- **Phase 6 — Data ops + drift:** DVC pipeline (`dvc.yaml`) wired in; Grafana dashboards over `inference_logs`; retraining workflow gated on drift signal.

## 6. Key trade-offs

- **PostgreSQL for drift over a dedicated time-series store.** One database is enough at this scale and keeps ops surface small. Revisit if `inference_logs` exceeds tens of millions of rows or if Grafana queries hot-spot the OLTP workload.
- **Model loaded as a process-local singleton.** Trades cold-start time for per-request speed; necessary for the 150 ms P95 budget. Revisit if the artifact grows large enough that container memory becomes the binding constraint.
- **MLflow over a custom registry.** Industry standard, cheap to run for the project's scale. Revisit only if multi-tenant governance becomes a requirement.
- **DVC over Git LFS or a custom data layer.** Keeps the Git repo lightweight while allowing pipeline-graph-aware retraining. Cost: contributors must learn DVC. Worth it for the lifecycle discipline.
- **Angular 22 + Nginx vs. an SSR or full-stack framework.** Strict typing, mature DI, Signals + Signal Forms, and the zoneless default of v22 are the deciding factors. The trade-off is a heavier toolchain than a vanilla React app — accepted because the platform is enterprise-targeted. Revisit if SSR becomes a requirement (Angular's SSR story would then be evaluated against alternatives).
- **Angular 22.0.0 pinned over the PRD's "Angular 18+" floor.** v22 is the May 2026 release and the first to ship Signal Forms as stable, Vitest as the default test runner, and zoneless by default. Pinning to the latest LTS-track release avoids a forced migration mid-build. Cost: contributors must use the v22 idioms (Signals, standalone components, OnPush) from day one.
- **Tailwind CSS v4 over a hand-rolled SCSS system or Angular Material.** Utility-first styling keeps the design tokens close to the markup and removes the need to maintain a parallel theme file. The trade-off is template verbosity; mitigated by component composition. Revisit if a design system handoff requires Material-style theming.
- **Same docker-compose for dev and reference deploy.** Contributors get a one-command local stack at the cost of dev-vs-prod parity guarantees. Revisit when a real production target is chosen — at that point the compose file becomes a reference, not the deploy artifact.
- **CORS allowlist over a same-origin proxy in dev.** Deliberate: the API enforces its own origin policy regardless of how the SPA is served. Revisit only if a third trusted origin is added.

## 7. Component-to-phase map

| Component        | P0       | P1       | P2       | P3       | P4       | P5       | P6       |
| ---------------- | -------- | -------- | -------- | -------- | -------- | -------- | -------- |
| Repo scaffolding | core     | —        | —        | —        | —        | —        | —        |
| Training script  | scaffold | core     | —        | —        | —        | —        | tuned    |
| MLflow           | scaffold | core     | tuned    | —        | —        | —        | —        |
| FastAPI          | scaffold | —        | core     | tuned    | —        | tuned    | —        |
| PostgreSQL       | scaffold | —        | —        | core     | —        | —        | tuned    |
| Angular SPA      | scaffold | —        | —        | —        | core     | —        | —        |
| docker-compose   | core     | tuned    | tuned    | tuned    | tuned    | —        | —        |
| GitHub Actions   | scaffold | —        | —        | —        | —        | core     | tuned    |
| DVC              | —        | scaffold | —        | —        | —        | —        | core     |
| Grafana          | —        | —        | —        | —        | —        | —        | core     |

## 8. Source

Distilled from `PRD.md` v2.0.0 and cross-referenced with `project-overview.md`. The PRD is authoritative for any disagreement.
