# AI Workflow Rules

This file covers two surfaces:

1. **Product ML rules** — how the predictive model and its lifecycle (training, registry, serving, drift) are expected to behave inside the platform.
2. **Dev AI rules** — how contributors should use AI coding assistants (Claude Code, Cursor, Copilot) when developing this repository.

The platform does not ship LLMs, agents, or RAG today. Sections about agentic loops, prompt injection, and retrieval are intentionally omitted; if those capabilities are added later, they belong here.

## Part 1 — Product ML rules

### Model selection and registration

The production model is a scikit-learn classifier loaded from MLflow as `models:/ProductionModel/latest` at API startup. There is no dynamic per-request model selection. New models reach `ProductionModel` only via an MLflow stage transition that happens at the end of a successful CI training run; the API picks them up on next start.

A new training run that does not register cleanly in MLflow does not reach production. There is no manual upload path.

### Training rules

- Training scripts live under `backend/src/models/`. They read DVC-tracked datasets, never raw filesystem paths.
- Every training run logs hyperparameters, metrics, and the trained artifact to MLflow. Runs that don't log are considered failed.
- Train / validation / test split logic is deterministic (seeded). The seed is logged.
- Evaluation metrics on the held-out test set must be present on the MLflow run before the model is considered for promotion.

### Inference rules

- Inputs are validated by `PredictPayload` (Pydantic). No coercion, no defaults that mask missing fields.
- Inference happens against the in-memory model loaded at startup; there is no per-request load.
- Every successful inference is persisted to `inference_logs` with `timestamp`, `model_version`, `input_payload`, `prediction`, `probability`, `latency_ms`. A failure to persist must be visible (HTTP 500 + log), not swallowed.
- Latency measurement wraps only the inference call, not request parsing or DB writes — the 150 ms P95 budget is the model itself.

### Drift detection rules

- Drift is computed off `inference_logs`, not off live request traffic. Inference is not blocked on drift detection.
- The `is_drift_detected` flag is written by the drift workflow, not by the API.
- Drift dashboards in Grafana are read-only over PostgreSQL.
- A drift signal triggers a retraining workflow in GitHub Actions; it does not auto-promote a new model. Promotion remains an MLflow stage transition.

### Observability rules for ML calls

- Trace the inference path with at least one structured `INFO` log per request: `model_version`, `latency_ms`, `prediction`. Never log `input_payload` at `INFO` (PII risk if the dataset later changes); rely on the DB row for audit.
- Errors during inference produce an `ERROR` log including the exception type and message — never the model artifact details, never the request payload at warning-or-above levels.

### Safety and content rules

- The model returns a class and a probability. The platform surfaces probability honestly; clients (the UI) decide how to present low-confidence results.
- The API does not add a confidence floor. If consumers need one, that's a UI concern documented in `ui-context.md`.
- Inputs that fail Pydantic validation never reach the model. There is no "best effort" path.

## Part 2 — Dev AI rules

### Authorship and accountability

The human committer owns the change, regardless of how much of it was generated. AI-generated code goes through the same review, the same tests, and the same standards as code typed by hand. "AI wrote it" is not a defense in code review.

### Context to give an AI assistant

When asking an assistant to work on this repo, point it at:

- The `context/` folder (this folder) so it inherits the project's conventions in one shot.
- `PRD.md` as the source of truth for *what* the system does.
- The specific phase in `progress-tracker.md` the change belongs to.
- The failing test or the type error, when fixing a bug.

Don't paste the whole PRD into a prompt when one section will do. Don't ask the assistant to "improve" code without a specific goal.

### What AI is good for here

- Drafting Pydantic schemas and matching TypeScript interfaces from a description of the payload.
- Writing test cases against an existing function — especially edge cases the human author didn't think of.
- Producing the SQLAlchemy model and a matching Alembic migration when the schema in `architecture-context.md` is the source of truth.
- Boilerplate Angular 22 standalone component scaffolding (template + Tailwind utility classes + Vitest spec) that the human then fills in. The assistant must default to Signals, Signal Forms, `input()`/`output()`, `inject()`, control flow (`@if`, `@for`), and OnPush — and must not generate `NgModule`, `*ngIf`, `@Input()`/`@Output()` decorators, or Karma/Jasmine specs.
- Translating a Pytest test into a Vitest test or vice versa.
- Reviewing a diff for naming, dead code, or missed edge cases.

### What AI must not do without human review

- Touch the inference path (`/api/predict`, model load, latency measurement) — performance and correctness here are load-bearing.
- Modify CORS configuration or any security-adjacent middleware.
- Change the `inference_logs` schema or the SQL that writes to it.
- Add dependencies to `requirements.txt` or `package.json` — every new dependency is a human decision.
- Modify the GitHub Actions workflows that gate releases or promote models.
- Edit prompts, eval cases, or any future AI-product surface (none today, but this is where the rule lands when it arrives).

### Verification before commit

- Run the relevant test suite locally. CI is a backstop, not a substitute.
- Read the diff line by line. AI assistants invent imports and APIs; the diff is the only ground truth.
- Type-check (`mypy` for Python, `tsc --noEmit` for TypeScript) and lint (`ruff`, ESLint) before pushing.
- For changes touching the schema or migrations, run the migration against a clean database before committing.

### Privacy when using AI assistants

- No production credentials in prompts, ever — including in pasted error messages.
- No real `inference_logs` rows in prompts. If you need a sample, hand-craft one.
- Be aware that pasted code may be retained by the assistant's provider; treat it as you would code on a public gist.

### Working with the codebase via AI assistants

- One concern per session. A session that drifts from "fix this test" to "refactor the service layer" produces low-quality output.
- Plan-before-edit: ask the assistant to outline the change first, agree on the plan, then have it implement. Skipping this step is the source of most rework.
- Anchor the assistant in `context/` whenever it suggests something that contradicts established conventions — those documents are the project's lived rules.

### Documentation generated by AI

Treat as a draft. Verify every claim against the current code. Match the project voice (direct, technical, no marketing words, no emojis except in `progress-tracker.md` snapshots).

## Part 3 — Cross-cutting

The product ships no LLMs today, so the prompt-injection and agent rules are deferred. If those features arrive, this file is the first thing to update; the deferral is intentional, not an oversight.

AI-generated code touching ML lifecycle code (training, registry, drift) requires the same human review as any other change, with extra attention to determinism, seed handling, and reproducibility. AI-on-AI shortcuts — using an assistant to "review" assistant-written code — are not a substitute for human review.

## Source

Derived from `PRD.md` v2.0.0. Cross-references `architecture-context.md` for the inference path and `code-standards.md` for the language-level conventions referenced above.
