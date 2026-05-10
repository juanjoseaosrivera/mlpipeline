# Code Standards

The rulebook for this repository. The goal is consistency: the codebase should read like one engineer wrote it, not like a committee assembled it. Every rule below has a rationale; if you find a rule you can't justify, raise it in review and amend the standards rather than working around it in a PR.

## 1. General principles

- **Optimize for the next reader.** Code is read far more often than it is written. Choose names, structure, and comments that the next contributor (possibly you in three months) can pick up cold.
- **Explicit over implicit.** Typed payloads, named parameters, declared return shapes. Magical conventions get unlearned the first time a contributor leaves the project.
- **Fail loudly.** Validation errors, missing config, and inference exceptions surface immediately. Silent fallbacks hide drift; we want drift visible.
- **Stateless by default.** Server-side handlers and containers carry no local mutable state across requests or restarts. State lives in PostgreSQL, MLflow, or DVC.
- **No dead code.** Unused imports, commented-out blocks, and "we might need it" helpers get deleted. Git history is the archive.
- **Tests describe behavior.** A new test file should read like a specification of the unit, not like a transcript of how the code happens to work today.

## 2. Python (backend, training, scripts)

- **Language and tooling.** Python 3.10+. Format with `black` (line length 100). Lint with `ruff`. Type-check with `mypy --strict` on `backend/src`. Imports sorted by `ruff`'s isort rules. No `# type: ignore` without a one-line reason.
- **Project layout.**
  - `backend/src/api/` — FastAPI entrypoint (`main.py`), routers, dependencies, Pydantic `schemas.py`.
  - `backend/src/models/` — training, evaluation, and any model-loading helpers.
  - `backend/tests/` — Pytest, mirroring the source layout.
- **Naming.** `snake_case` for modules, functions, variables. `PascalCase` for classes and Pydantic models. Boolean predicates are `is_*` / `has_*` / `should_*`. Pydantic schemas are suffixed with their role: `PredictPayload`, `PredictResponse`.
- **Type / shape rules.** Every public function has type annotations. API shapes are Pydantic models in `schemas.py`. Domain shapes (dataclasses) live next to the logic that uses them. Storage shapes (SQLAlchemy models) live in `backend/src/api/db/`. Never import a SQLAlchemy model into a Pydantic schema or vice versa — translate at the boundary.
- **Async.** Endpoints are `async def` unless they have a hard-blocking reason not to be. Don't block the event loop with synchronous I/O; if a library is sync-only, run it in a threadpool.
- **Errors and exceptions.** Validation failures are raised by Pydantic and become HTTP 422 automatically. Inference failures raise `HTTPException(status_code=500, detail="Inference Error")` — the detail is intentionally generic; specifics go to logs, not to the client. Database errors propagate as 500 unless a more specific status applies.
- **Logging.** Standard `logging` with structured key-value pairs. Levels: `DEBUG` for development noise, `INFO` for the inference-path summary (timestamp, model_version, latency_ms), `WARNING` for retried operations, `ERROR` for failed requests. Never log the full payload or model output at `INFO`. Never log secrets, env values, or DB credentials at any level.
- **Configuration.** All settings come from environment variables, parsed once via `pydantic-settings` at startup. Hard-coded URLs (including `http://localhost:8000`) appear only in tests. Secrets must never be in source.
- **Testing.** `pytest` with `pytest-asyncio`. Three tiers: unit tests (no I/O, in-memory model fakes), integration tests (real Postgres + MLflow via test compose), end-to-end tests (full stack). Coverage target: 80%+ on `backend/src`. Mock at boundaries — never mock what you own.

## 3. TypeScript (frontend, Angular 22.0.0)

- **Language and tooling.** TypeScript 5.9 with `strict: true`, `noImplicitAny: true`, `strictNullChecks: true`. Angular 22.0.0, pinned exactly in `package.json` (`"@angular/core": "22.0.0"`). Format with Prettier (line length 100). Lint with ESLint using `angular-eslint`. Imports sorted by ESLint.
- **Project layout.**
  - `frontend/src/app/components/` — standalone UI components, one folder per component.
  - `frontend/src/app/models/` — TypeScript interfaces shared across the app.
  - `frontend/src/app/services/` — HTTP clients and stateful services injected by DI.
- **Framework idioms (Angular 22).** All components are standalone (no `NgModule`). `changeDetection: ChangeDetectionStrategy.OnPush` everywhere — this is the v22 default for new components, do not opt out. The app is zoneless (no `Zone.js` import in `main.ts`); reactivity flows through Signals. Use `inject()` over constructor injection. Prefer selectorless component usage where it improves readability. Use control flow (`@if`, `@for`, `@switch`) — no `*ngIf` / `*ngFor`.
- **State and forms.** Component state lives in `signal()` / `computed()` / `linkedSignal()`. Forms use **Signal Forms** (stable in v22) — `form()` and field-level signals — not the legacy `FormGroup` / `FormControl`. Use the native `debounced()` signal for debounced fields (search boxes, dependent validation) rather than reaching for RxJS.
- **Naming.** Files use `kebab-case` (`ml.service.ts`, `prediction-form.component.ts`). Classes use `PascalCase` with the suffix matching their role: `MlService`, `PredictionFormComponent`. Interfaces are `PascalCase` without an `I` prefix. Booleans are `isFoo`, `hasFoo`, `shouldFoo`. Signal accessors are nouns (`prediction`, `isPending`), not getters (`getPrediction`).
- **Type / shape rules.** Every component and service has explicit input, output, and method signatures. Use `input()` / `output()` signal-based APIs, not `@Input()` / `@Output()` decorators. The shapes traded with the API (`PredictPayload`, `PredictResponse`) live in `frontend/src/app/models/` and mirror the Pydantic schemas exactly — when one moves, the other moves in the same PR.
- **Async.** HTTP returns Observables via `HttpClient`, bridged into Signals at the component boundary with `toSignal()`. Don't subscribe inside components. Where a subscription is unavoidable, use `takeUntilDestroyed()` — no manual `Subscription.unsubscribe` boilerplate.
- **Errors.** HTTP errors are caught at the service layer with `catchError`, mapped to a typed error union, and surfaced to the component as signal state. Components render error states; they do not throw or `console.error`.
- **Styling (Tailwind CSS v4).** Tailwind v4 is the styling system. Setup uses the `@tailwindcss/postcss` plugin with a `.postcssrc.json`, and `src/styles.css` starts with `@import "tailwindcss";` (do not use `@use`; SCSS is not supported by Tailwind v4). Use utility classes in templates; reach for `@apply` in component stylesheets only when a utility cluster repeats three or more times. Design tokens (color, spacing, typography, radius, elevation) are defined in `tailwind.config` and consumed exclusively through utilities. No inline `style="..."` attributes for values that map to a token.
- **Logging.** No `console.log` in committed code. Use a wrapper that can be silenced in production builds.
- **Configuration.** Environment-specific values live in `frontend/src/environments/`. The API base URL must come from environment, never hard-coded in services beyond the dev default.
- **Testing.** Vitest is the test runner (default in Angular 22). Component tests use the Angular Testing Library patterns (render the component, assert from a user's perspective). Coverage target: 80%+ on `frontend/src/app`. Do not introduce Karma/Jasmine — the v22 default is Vitest and we follow it.

## 4. Database conventions (PostgreSQL)

- **Naming.** Tables `snake_case` plural-or-singular consistently per project — this project uses singular-of-domain ↔ plural-of-record (`inference_logs`). Columns `snake_case`. Foreign keys `<referenced_table>_id`. Indexes `idx_<table>_<columns>`.
- **Primary keys.** `SERIAL PRIMARY KEY` is acceptable for `inference_logs` (already established in the PRD). For new tables, prefer `BIGSERIAL` or UUID.
- **Timestamps.** `timestamp TIMESTAMPTZ DEFAULT NOW()` on every row, even when not used today.
- **JSON columns.** Use `JSONB`, not `JSON`. Index commonly-queried keys explicitly.
- **Migrations.** Schema changes go through Alembic migrations; never apply ad hoc DDL to a running database.

## 5. Git and commit hygiene

- **Branches.** `feat/<short-name>`, `fix/<short-name>`, `chore/<short-name>`. No personal-name branches.
- **Commits.** Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`. Subject under 72 characters; body explains *why* when the diff doesn't. One concern per commit.
- **PRs.** Under ~400 lines of substantive diff when possible. Every PR links the user story or phase from `progress-tracker.md` and updates a checkbox in the same PR. No direct pushes to `main`. Rebase, don't merge-commit, into `main`.
- **Reviews.** At least one human reviewer on every PR. Reviewers approve substance — design, correctness, security, test coverage. Style is the formatter's job.

## 6. Documentation

- **Docstrings.** Google style for Python, TSDoc for TypeScript. Public functions get a one-line summary plus parameter and return descriptions. Private helpers get a one-liner only when the *why* isn't obvious.
- **Comments.** Explain *why*, not *what*. A comment that paraphrases the next line is a deletion candidate.
- **READMEs.** `backend/` and `frontend/` each carry a README with: how to run, how to test, how to add a feature. Keep them short; deeper material lives in `context/`.
- **ADRs.** When an architectural decision is made (or reversed), add an ADR under `docs/adr/NNNN-title.md` and index it in `progress-tracker.md`.

## 7. Security and privacy

- **Never log secrets** — DB credentials, MLflow URIs with auth, S3 keys. Treat env values as opaque outside config loading.
- **Treat external content as untrusted.** Inputs to the model are validated by Pydantic; nothing else is parsed from untrusted sources at runtime.
- **CORS.** The allowlist is exhaustive. No `allow_origins=["*"]`, ever. Add new origins via env, not by editing the allowlist in code.
- **Rate limiting.** Out of scope for v2.0; documented here so a contributor doesn't bolt one on without an ADR.
- **Dependencies.** Pin versions (`requirements.txt`, `package-lock.json` committed). Security updates flow through Dependabot PRs with a human reviewer.

## 8. Performance

- **Measure first.** Don't optimize without a P95 number. The 150 ms inference budget is at the API boundary; if you're under it, leave it.
- **N+1 queries.** Forbidden in the inference path. Inference writes are a single insert per request.
- **Batching.** Training and evaluation may batch freely; inference is per-request.
- **Caching.** The model is cached in process by being loaded once at startup. There is no response cache — predictions on identical payloads must still be logged for drift analysis.

## 9. Code review

Reviewers check: correctness, security, test coverage, alignment with `architecture-context.md`, and whether the PR updates the right checkbox in `progress-tracker.md`. Reviewers do not gatekeep on: naming bikesheds the formatter doesn't catch, personal style preferences, or speculative refactors.

When reviewer and author disagree on a rule, the resolution is to amend `code-standards.md` in a follow-up PR — not to relitigate the same conversation in the next review.

## Source

Derived from `PRD.md` v2.0.0 (technology stack, Section 3) and constraints in Sections 4 and 6. The frontend section pins Angular 22.0.0, TypeScript 5.9, Vitest, and Tailwind CSS v4 — these supersede the PRD's "Angular 18+" and "Karma/Jasmine" lines and reflect the May 2026 Angular release. Cross-references `architecture-context.md` for boundaries and `ai-workflow-rules.md` for AI-specific rules.
