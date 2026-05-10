# UI Context

This document is the design context for the Angular 22.0.0 frontend. It complements `architecture-context.md` (the technical shape of the frontend) and `code-standards.md` (the coding rules). The audience is a contributor who is about to touch the UI and needs to know what conventions are already in force.

The stack is Angular 22.0.0 + TypeScript 5.9, zoneless, Signals-first, Signal Forms, standalone components with OnPush as the default, and Tailwind CSS v4 for styling. Tests run on Vitest. If a piece of guidance below conflicts with the Angular 22 idioms, the v22 idiom wins.

## 1. Audience and tone

The product is internal-enterprise: data scientists, ML engineers, and the operators who depend on their models. Users read latency numbers and probabilities natively; they do not need explanatory copy or animated reassurance. They do need to trust what they see — values must be exact, error states must be honest, and the system should not pretend to know things it doesn't.

Tone rules: direct, technical, sober. Plain numerals. No marketing words. No emojis. No "Loading..." with an ellipsis where a skeleton or a real progress indicator would do.

## 2. Design principles

- **Predictions are the protagonist.** Every screen is in service of a prediction the user requests, sees, and trusts. Decoration that distracts from the prediction is removed in review.
- **Show your work.** When the system has a probability, surface it. When it has measured latency, surface it. The user is technical; concealment of detail is the wrong default.
- **Stable layout.** The form does not jump when results render. Panels reserve space; the result panel is laid out before the response arrives.
- **Disable, don't hide.** Submit is disabled while a prediction is in flight, not removed. The user always knows where the action is.
- **Validate close to input.** Errors appear next to the field that caused them, the moment the field is touched and invalid — not after submit. Use Signal Forms' per-field signals so validation state is reactive without an RxJS detour.
- **One source of truth per value.** A field's value lives in the Signal Form's state. Components do not maintain parallel `signal()` copies of form values.

## 3. Information architecture

The MVP has a single primary surface — the prediction workbench — with auxiliary surfaces for history and (later) drift dashboards.

```
+--------------------------------------------------------------+
|  Header: product name · model_version pill · environment     |
+--------------------------------------------------------------+
|                                                              |
|  +------------------+    +------------------------------+    |
|  | Prediction form  |    | Result panel                 |    |
|  | (reactive form)  |    | prediction · probability ·   |    |
|  | submit button    |    | latency_ms                   |    |
|  +------------------+    +------------------------------+    |
|                                                              |
|  Recent predictions (read-only table from inference_logs)    |
|                                                              |
+--------------------------------------------------------------+
```

Secondary surfaces deferred past v2.0: drift dashboard (lives in Grafana, not the SPA), authentication / user management, model promotion controls (MLflow's UI handles these for now).

Explicit non-surfaces: no marketing pages, no in-app onboarding tour, no settings panel beyond environment switching, no embedded MLflow or Grafana iframes (they have their own URLs).

## 4. Core user flows

### 4.1 Submit a prediction (the hot loop)

1. User lands on the workbench. The Signal Form renders empty; the result panel renders an empty state with a hint ("Submit to see a prediction").
2. User fills `feature_1`, `feature_2`, `category`. Per-field validation runs on blur via Signal Forms' field validators.
3. Submit becomes enabled when the form's `valid` signal is `true`.
4. User clicks Submit. The `isPending` signal flips, submit disables, the result panel shows a skeleton.
5. The `MlService` posts to `/api/predict`. The response is bridged into a signal with `toSignal()`. On success, the result panel renders prediction (class label), probability (formatted to 3 significant figures), and latency_ms (integer, with unit).
6. The form remains populated for the user to tweak and re-submit. Submit re-enables.
7. On HTTP error, the result panel renders an error state with the correlation ID (when available) and a Retry button. The form is not cleared.

### 4.2 Inspect recent predictions

1. The "Recent predictions" table renders the last N rows of `inference_logs` (read via a future read endpoint or paginated query — out of scope for v2.0 if a backend route is not yet wired).
2. Rows show timestamp, model_version, prediction, probability, latency_ms.
3. Clicking a row reveals the input payload (the `JSONB` field) in a side panel — read-only.

### 4.3 Detect a degraded backend

1. If `/api/predict` returns 500 or fails to connect, the result panel renders a clear error: "Inference unavailable" with the correlation ID and a Retry button.
2. If three consecutive submissions fail, a banner appears at the top of the page recommending the user check the platform status (link to Grafana / MLflow).

## 5. Component conventions

- Standalone components only. `NgModule` is not used.
- `ChangeDetectionStrategy.OnPush` everywhere (the v22 default for new components — do not opt out).
- Zoneless: do not import `Zone.js`; reactivity flows through Signals.
- Use control flow (`@if`, `@for`, `@switch`) — no `*ngIf` / `*ngFor`.
- Selectors are kebab-case with the project prefix (`app-prediction-form`, `app-result-panel`). Where selectorless usage improves readability, use it.
- File set per component: `name.component.ts`, `name.component.html`, `name.component.css`, `name.component.spec.ts`. Templates lean on Tailwind utilities; the component CSS file is reserved for `@apply` clusters and rare custom rules. No mega-components.
- Inputs and outputs use the signal-based APIs: `input<T>()` and `output<T>()`. No `@Input()` / `@Output()` decorators. No `any`. No `unknown` without a narrowing step.
- Services are injected with `inject()` and provided via `providedIn: 'root'` unless they are scoped to a component subtree.

## 6. Streaming UX

The platform does not stream inference responses. Predictions are single-shot JSON. The submit-disabled-with-skeleton pattern (Section 4.1) is the entire async UX surface today. Do not add fake streaming or simulated typing — the user is technical and will resent the artifice.

If a future feature streams (e.g., live drift readings), it gets its own subsection here and uses Server-Sent Events with a documented reconnect strategy.

## 7. Empty, loading, and error states

- **Empty.** Every panel renders a deliberate empty state, never blank. The result panel's empty state names the action ("Submit to see a prediction").
- **Loading.** Skeletons that match the final content's layout (rows of the right height, panels of the right width). No spinners over already-rendered content.
- **Error.** Plain language, no apology theatre. Show the correlation ID when the API supplies one. Always offer a Retry where retry is safe.

## 8. Styling and design tokens (Tailwind CSS v4)

Tailwind CSS v4 is the styling system. It is wired in via the `@tailwindcss/postcss` plugin and a `.postcssrc.json` at the repo root; `src/styles.css` starts with `@import "tailwindcss";`. SCSS is not used (Tailwind v4 does not officially support it).

Tokens cover color (neutral grays, one accent, one error red, one warn amber), spacing (4 / 8 / 12 / 16 / 24 / 32), typography (sans for UI, monospace for numerals and identifiers), radius (small + medium only), and elevation (flat + one card shadow). Tokens live in `tailwind.config` and are consumed exclusively through utility classes. No inline `style="..."` attributes for values that map to a token.

Theme strategy: dark-mode-first via the `dark:` variant. Light mode is a secondary theme generated from the same tokens. Class-based dark mode (`darkMode: 'class'`) so the user's preference can be persisted.

Numeric values (probability, latency, timestamps) render in the monospace family so they line up across rows. Use `font-mono tabular-nums` together to keep digit widths consistent.

## 9. Accessibility

WCAG 2.1 AA. Color contrast at AA across both themes. Every input has a programmatic label. Focus rings are visible (don't strip them). Errors are announced via `aria-live="polite"` regions when they appear after async operations. Reduced-motion preferences are respected — the skeleton's shimmer is disabled when `prefers-reduced-motion: reduce`.

Keyboard parity: every action reachable by mouse is reachable by keyboard, including Submit, Retry, and the row-expansion in the recent-predictions table.

## 10. Responsiveness

Two breakpoints: small (< 768px) and large (≥ 768px). Below small, the form and the result panel stack vertically; the recent-predictions table collapses into a card list. The platform is usable on a phone but not optimized for it — power users are on laptops.

## 11. Internationalization

i18n is not built in for v2.0. Strings live in component templates. When i18n is required, they move to Angular's i18n catalog and this section is rewritten. File paths, identifiers, and code never get localized.

## 12. Performance budgets

Initial bundle under 300 KB gzipped (Angular 22's zoneless build shrinks the runtime vs. v18; Tailwind v4's content-aware pruning keeps CSS small). First Contentful Paint under 1 second on a fast connection (the PRD's success metric). Time to Interactive under 2 seconds. CI runs the Angular CLI bundle-budget check on every PR; budgets are enforced, not advisory.

## 13. Frontend observability

Errors caught by the global error handler are reported to the (future) telemetry endpoint with a correlation ID. No PII, no input payloads, no model output values leave the browser by way of telemetry — the database is the audit surface, not telemetry.

## 14. What this product is not

- Not a notebook or experimentation tool. Use Jupyter or MLflow's UI for that.
- Not an admin console for MLflow or DVC. Those tools have their own UIs.
- Not a chat interface. The model is a classifier, not an LLM.
- Not a dashboarding product. Drift dashboards live in Grafana.
- Not a multi-tenant tool. There is one model and one user persona at this scale.

## Source

Derived from `PRD.md` v2.0.0 (Sections 4.2 and 6.2) and aligned with `architecture-context.md`. Frontend stack pinned to Angular 22.0.0 (May 2026 release) and Tailwind CSS v4 — these supersede the PRD's "Angular 18+" line.
