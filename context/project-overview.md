# Project Overview — Intelligent Detection Platform

- **Project:** Intelligent Detection Platform (E2E MLOps with Angular & FastAPI)
- **Version:** 2.0.0
- **Status:** Approved for development
- **Owner:** AI / Full-stack Engineer

## What it is

A production-grade MLOps reference platform that wraps a predictive ML model in an asynchronous REST API and exposes it through a strictly typed enterprise web UI. The whole system — model training, registry, inference, persistence, UI, drift monitoring, retraining — runs under one repository, one docker-compose stack, and one CI/CD pipeline. The distinctive property is end-to-end coverage: nothing about the journey from a Jupyter prototype to a monitored production model is left as "out of scope."

## The problem

ML models routinely fail the jump from notebook to production. Common failure modes include monolithic services that conflate training and serving, untyped HTTP boundaries that silently drift between teams, no versioning for datasets or models, and no observability once the model is live — so model degradation (data drift, concept drift) is detected only when business metrics fall. The result is a wall between data scientists and end users that this project is built to remove.

## Strategic objectives

- Demonstrate full ownership of the ML lifecycle: data versioning, training, registry, serving, UI, monitoring, retraining.
- Keep the frontend and backend independently deployable and independently scalable through a decoupled microservices boundary.
- Enforce typed contracts at every hop (Pydantic on the wire, TypeScript interfaces in the client) so contract drift is caught at compile or request time.
- Hold inference latency under 150 ms at P95 and keep CI/CD under 10 minutes end-to-end.
- Detect model drift early using logged inference inputs, not downstream business signals.

## How it works

A user fills a reactive form in the Angular SPA. Nginx serves the bundled SPA and reverse-proxies inference requests to FastAPI. The API validates the payload against a Pydantic schema, calls the in-memory model that was loaded at startup from MLflow's Model Registry, and returns a prediction with its probability and measured latency.

Each successful prediction is persisted to PostgreSQL — input payload as `JSONB`, prediction, probability, model version, latency, and timestamp — so the inference log itself becomes the substrate for drift analysis. Grafana reads the same table to surface drift signals; once thresholds are crossed, a GitHub Actions workflow triggers retraining against DVC-versioned data, registers the new artifact in MLflow, and the API picks up the latest registered model on next start.

The end-to-end shape is therefore: Angular ↔ Nginx ↔ FastAPI ↔ (MLflow Model Registry, PostgreSQL) — with DVC, GitHub Actions, and Grafana wrapping the lifecycle around that runtime path.

## Technology stack at a glance

- **Frontend:** Angular 22.0.0 (TypeScript 5.9), zoneless by default, Signals + Signal Forms, standalone components with OnPush as default, Tailwind CSS v4 for styling, served by Nginx. Tests run on Vitest (the default in Angular 22).
- **Backend:** FastAPI on Python 3.10+, Pydantic, Uvicorn, MLflow client, SQLAlchemy.
- **ML / data:** MLflow (registry + tracking), DVC (dataset versioning, S3/cloud storage backend).
- **Storage:** PostgreSQL 15 for inference logs and drift inputs.
- **Platform:** Docker + docker-compose for local orchestration; GitHub Actions for CI/CD; Grafana for drift dashboards.

## Primary user stories

- **US-01 (P0)** — As an end user, I submit a validated form and receive a class prediction with its probability and measured latency.
- **US-02 (P0)** — As an ML engineer, every successful training run is automatically registered as a new version in MLflow.
- **US-03 (P0)** — As an SRE / ML engineer, every successful prediction is auditable in PostgreSQL with timestamp, model version, and latency.
- **US-04 (P1)** — As a data scientist, I can monitor data drift from logged inference inputs in Grafana and trigger a retraining pipeline when thresholds are breached.

## Evaluation framework

- Unit-test coverage at 80%+ on both Python (Pytest) and TypeScript (Vitest, Angular 22 default).
- Backend pure-inference latency under 150 ms at P95.
- CI/CD pipeline (build + test + image push) under 10 minutes.

## Roadmap

- **Phase 0 — Scaffolding:** repository skeleton, base Dockerfiles, docker-compose, CI baseline.
- **Phase 1 — Model + Registry:** training script, evaluation, MLflow registration of `ProductionModel`.
- **Phase 2 — Inference API:** FastAPI `/api/predict`, Pydantic schemas, model load on startup, CORS hardening.
- **Phase 3 — Persistence:** PostgreSQL schema, SQLAlchemy writes from the inference path.
- **Phase 4 — UI:** Angular 22 standalone components, Signal Forms, typed `MlService`, Tailwind v4 styling, submit-disable while pending, result rendering.
- **Phase 5 — CI/CD:** Pytest + Vitest in GitHub Actions, image build/push, deploy gate.
- **Phase 6 — Data ops + drift:** DVC pipeline, Grafana dashboards over `inference_logs`, retraining trigger workflow.

## Security posture

CORS is locked to the Angular origin in FastAPI (no wildcard). Database credentials and model URIs are injected through environment variables, never hard-coded. Containers are stateless so credentials never persist on disk inside an image. Inference logs store the input payload as `JSONB`; no PII is in scope for the seed dataset, but logging policy in `code-standards.md` still applies. Detail on AI-specific guardrails lives in `ai-workflow-rules.md`; detail on the operational rules lives in `code-standards.md`.

## Source

Distilled from `PRD.md` v2.0.0 (May 2026). The PRD is the authoritative specification; this overview is a reading aid. The frontend stack is pinned to Angular 22.0.0 (released May 2026) with Tailwind CSS v4, superseding the PRD's "Angular 18+" line — see `architecture-context.md` for the rationale.
