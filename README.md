# Intelligent Detection Platform

End-to-end MLOps reference platform: a predictive ML model wrapped in a FastAPI inference service, exposed through an Angular 22 SPA, with MLflow for the model registry, DVC for dataset versioning, PostgreSQL for inference logs, and Grafana for drift dashboards. Local orchestration via docker-compose; CI/CD via GitHub Actions.

## Where to start

New contributor? Read [`context/`](context/) before touching code:

- [`context/project-overview.md`](context/project-overview.md) — what the project is and how it fits together.
- [`context/architecture-context.md`](context/architecture-context.md) — components, boundaries, trade-offs.
- [`context/code-standards.md`](context/code-standards.md) — language, tooling, naming, testing.
- [`context/ai-workflow-rules.md`](context/ai-workflow-rules.md) — ML lifecycle rules and AI-assistant rules.
- [`context/ui-context.md`](context/ui-context.md) — UI principles, flows, design tokens.
- [`context/progress-tracker.md`](context/progress-tracker.md) — phase-by-phase status and ADR index.

The PRD ([`PRD.md`](PRD.md)) is the authoritative specification.

## Layout

```
.
├── backend/            # FastAPI inference service + ML training
├── frontend/           # Angular 22 SPA, served by Nginx
├── data/               # DVC-tracked datasets (pointers only in git)
├── docker-compose.yml  # db · mlflow · backend_api · frontend_ui
├── .github/workflows/  # CI/CD
└── context/            # Project conventions and roadmap
```

## Run locally

```
docker-compose up
```

- Frontend: `http://localhost`
- Backend API: `http://localhost:8000`
- MLflow: `http://localhost:5000`
- PostgreSQL: `localhost:5432`
