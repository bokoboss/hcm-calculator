# Application Rebuild R0.9 — Technology Architecture Decision

Status: Proposed/accepted baseline for R0 planning
Date: 2026-08-24
Branch: `planning/application-rebuild-r0`

## 1. Decision summary

Use the following target architecture for the rebuilt HCM application:

```text
React + TypeScript SPA
built with Vite
        |
        | local HTTP / JSON
        v
FastAPI application/API boundary
        |
        v
Python application services
        |
        v
Existing HCM engines / models / validation
```

Production/local use should remain capable of operating entirely on the user's computer without cloud services or internet access.

During development, Vite and FastAPI may run as separate local development servers. In a release build, the preferred baseline is for the Python application to serve the compiled SPA assets and API from one localhost application endpoint so normal users do not operate two servers.

Do **not** use Next.js as the baseline frontend framework for R1.

Do **not** introduce Tauri/Electron in R1. Desktop-shell packaging remains a later decision after the browser-local application experience is qualified.

## 2. Why this architecture fits the project

The repository already has a Python 3.12+ engineering core with Pydantic, tests, project/reporting code, and UI-independent method adapters. The problem is not lack of a calculation backend; the problem is the current presentation/application composition.

The rebuild therefore needs:

- a component-oriented frontend capable of sophisticated forms, data grids, diagrams, scenario comparison, responsive states, and explicit result hierarchy;
- a stable application boundary around the Python engineering code;
- a way to test frontend/user journeys separately from numerical calculations;
- local/offline operation;
- a migration path that does not rewrite HCM equations.

React + TypeScript + Vite provides the frontend capability without requiring a server-rendering framework. FastAPI provides a thin typed Python API boundary while allowing the existing package and Pydantic contracts to remain authoritative.

## 3. Current ecosystem verification

Architecture was checked against current official documentation on 2026-08-24.

- React official documentation identifies React 19.2 as the latest major/minor documentation line and supports building component-based browser applications.
- Vite 8.1 was announced in June 2026 and remains suitable for modern SPA development/build tooling.
- FastAPI's current official tutorial supports modern Python and a straightforward typed API application model.
- Playwright's current documentation supports Chromium, Firefox, WebKit, branded Chromium browsers, and multi-project browser/device testing.

References:

- https://react.dev/versions
- https://react.dev/learn
- https://main.vite.dev/blog/announcing-vite8-1
- https://fastapi.tiangolo.com/tutorial/
- https://playwright.dev/docs/browsers

Exact dependency versions should be pinned/locked at implementation time rather than hard-coded into this architecture document.

## 4. Alternatives considered

### 4.1 Continue Streamlit

Decision: rejected as the target rebuild architecture.

Advantages:

- lowest immediate migration effort;
- existing application already works;
- Python-only runtime.

Disadvantages:

- product composition remains strongly tied to rerun/session-state semantics;
- complex data-grid/diagram/application-shell behavior is harder to control precisely;
- current ~5,000-line orchestration already demonstrates the scaling problem;
- difficult to achieve the intended Project/Analysis/Scenario workspace cleanly without repeating the same architectural coupling.

Streamlit may remain temporarily as the qualified legacy UI during migration.

### 4.2 React + TypeScript + Vite + FastAPI

Decision: selected.

Advantages:

- precise UI/component control;
- strong fit for forms, tables, diagrams, status states, and scenario comparison;
- clean separation from Python calculation code;
- static SPA build can be served locally by Python;
- no SSR requirement;
- straightforward Playwright browser testing;
- frontend and backend contracts can be independently tested.

Costs:

- introduces Node-based frontend development tooling;
- requires an API/application boundary;
- requires contract/version discipline between frontend and backend.

These costs are acceptable and directly address the current structural problem.

### 4.3 Next.js + FastAPI

Decision: not selected for R1.

Potential advantages:

- mature React framework conventions;
- routing/build ecosystem;
- server features if a public/cloud application becomes a goal.

Why not selected:

- HCM is primarily a local engineering application, not a content/SEO/SSR website;
- Python is already the authoritative backend;
- a second server-side framework adds deployment/runtime concepts without a clear current product benefit;
- React SPA routing and application state are sufficient for the planned workspace.

Next.js can be reconsidered if future requirements change materially, e.g. authenticated multi-user cloud deployment.

### 4.4 Tauri + React + Python sidecar

Decision: deferred.

Potential advantages:

- native desktop shell;
- filesystem integration;
- packaged application feel.

Reason to defer:

- adds packaging/process/security complexity before frontend/application architecture is proven;
- browser-local operation is sufficient for R1/R2 qualification;
- the SPA/API boundary should remain usable inside a future desktop shell if later required.

### 4.5 Electron + React + Python

Decision: not selected for initial rebuild.

The runtime/package footprint and multi-process complexity are not justified while browser-local deployment meets the current requirement.

## 5. Target repository structure

Conceptual migration target:

```text
hcm-calculator/

src/hcmcalc/
  core/
  methods/
  models/
  freeway/
  multilane/
  ramp_influence/
  two_lane/
  validation/
  weaving/

  application/
    analyses/
    projects/
    reporting/
    interpretation/
    registry/

  api/
    main.py
    routes/
    schemas/

  ui/                       # legacy Streamlit during migration

frontend/
  src/
    app/
    components/
    analyses/
      two_lane_segment/
      two_lane_facility/
      multilane_segment/
      basic_freeway_segment/
      weaving_segment/
      merge_segment/
      diverge_segment/
    project/
    compare/
    reference/
    i18n/
    api/
    styles/
  tests/

playwright/
  journeys/
  visual/
```

Exact directories may change during R1 implementation, but the boundaries should remain.

## 6. Python application layer

A new explicit `hcmcalc.application` layer should absorb framework-independent behavior that currently lives partly under `hcmcalc.ui`.

Candidate migrations include:

- `manual_multilane.py` adapter behavior;
- `manual_freeway.py`;
- `manual_facility.py`;
- `manual_weaving.py`;
- `manual_ramp_influence.py`;
- `manual_segment.py`;
- workflow-state/fingerprint behavior;
- project I/O orchestration;
- report orchestration;
- deterministic result interpretation;
- supported-method registry.

This is a refactor/move of application behavior, not an engine rewrite.

## 7. API layer responsibilities

FastAPI should be deliberately thin.

It owns:

- JSON request/response boundary;
- typed API schemas;
- routing;
- application-service invocation;
- error/status translation into stable application contracts;
- static SPA serving in release mode where selected;
- OpenAPI contract generation for development/testing.

It does not own:

- HCM formulas;
- duplicate validation methodology;
- frontend display formatting;
- direct persistence database logic in R1 unless later required.

## 8. Application service boundary

Frontend routes should not call HCM method classes directly through one-off endpoints.

Use services such as conceptually:

```text
AnalysisService
  validate(method_id, displayed_inputs, units)
  calculate(method_id, displayed_inputs, units)
  get_method_definition(method_id)

ProjectService
  import_legacy_project(...)
  load_project(...)
  save_project(...)

ReportService
  export_current_result(...)

ComparisonService
  compare_compatible_scenarios(...)
```

The application service normalizes UI-facing input through existing adapters before invoking the engine.

## 9. API contract principles

### Stable method identity

Requests use canonical method identifiers, not translated labels.

Example:

```text
multilane_segment
basic_freeway_segment
weaving_segment
merge_segment
diverge_segment
```

### Explicit method/input contract

Calculation identity includes:

- method identifier;
- method/input contract version;
- normalized inputs.

### No frontend formula replication

The frontend may perform lightweight field formatting/readiness checks for immediate UX, but backend/application validation remains authoritative before calculation.

### Structured states

API responses should expose canonical state codes, not only localized prose.

Examples:

```text
valid_current_result
capacity_failure
hcm_stopping_or_handoff
unsupported_scope
```

## 10. Initial API surface

The exact REST design should be finalized during R1, but the following is a sufficient starting concept.

### Method discovery

```text
GET /api/v1/methods
GET /api/v1/methods/{method_id}
```

Returns engineering availability/scope metadata and contract versions.

### Validation

```text
POST /api/v1/analyses/{method_id}/validate
```

Returns structured field/section/scope validation without performing a full accepted calculation where separable.

### Calculation

```text
POST /api/v1/analyses/{method_id}/calculate
```

Returns:

- normalized input identity;
- calculation fingerprint;
- engine result;
- presentation state;
- result presentation model / canonical interpretation codes;
- audit identity.

### Project import/export

Routes/services should support current JSON project compatibility while allowing user-driven browser file upload/download.

### Reporting

Generate from accepted current result/project state only; do not rerun the HCM engine.

## 11. Analysis Registry ownership

The engineering method registry should be backend/application authoritative.

It should expose method metadata such as:

- method ID;
- family;
- HCM edition/chapter;
- calculation contract;
- supported unit systems;
- capability flags;
- scope metadata;
- current availability.

The frontend owns the visual module registered for a supported method ID.

Conceptually:

```text
Backend registry
  determines what is calculable and authoritative

Frontend analysis module registry
  determines how a supported method is rendered
```

Adding a method should not require editing the AppShell/navigation dispatcher beyond registration.

## 12. Frontend architecture

Use React + TypeScript as a client-side application.

Conceptual layering:

```text
AppShell
  Routing / workspace
    Project screens
    Analysis screens
      shared workflow components
      method-specific composition
    Compare
    Reference

API client
Canonical frontend types
Localization
Design tokens/components
```

## 13. Routing

Use client-side routing.

Conceptual routes:

```text
/
/projects/:projectId
/projects/:projectId/analyses/:analysisId
/projects/:projectId/analyses/:analysisId/scenarios/:scenarioId
/quick/:analysisId
/compare/...
/reference/methods
/reference/methods/:methodId
```

Exact route structure may be simplified during implementation.

Routes represent application location; engineering calculation state remains in Project/Analysis/Scenario models.

## 14. Frontend state strategy

Avoid a large global state framework by default.

Use the smallest architecture that cleanly separates:

- server/application state;
- current editable form state;
- project/navigation state;
- accepted result identity;
- UI-only state.

A dedicated global state library should only be introduced if actual prototype complexity justifies it.

The critical requirement is not the library; it is preserving the current/stale fingerprint semantics.

## 15. Form state

Method forms should use typed canonical field definitions and method-specific view components.

Requirements:

- field-level errors;
- conditional branches;
- unit-aware values;
- dirty/stale detection;
- keyboard-efficient facility-grid editing;
- no calculation on every keystroke.

Exact form library is an implementation choice subject to R1 review.

## 16. Backend vs frontend validation

Use two layers deliberately.

### Frontend validation

For immediate UX:

- missing visible required field;
- parseable numeric input;
- simple branch-local constraints.

### Backend/application validation

Authoritative:

- normalized numeric/domain validation;
- cross-field engineering constraints;
- method support/scope;
- project compatibility;
- calculation readiness.

Frontend validation can improve speed but can never make an unsupported engine case calculable.

## 17. Localization architecture

Canonical IDs remain language-neutral.

Frontend should own most UI labels/help text using structured translation resources rather than one monolithic Python dictionary.

Backend returns:

- canonical codes;
- engineering values;
- source references;
- optionally fallback English diagnostic text for technical logging.

Frontend maps codes to Thai/English user presentation.

Migration should extract/reuse the valuable current translation content rather than rewrite all terminology from scratch.

## 18. Project file strategy

R1 should retain explicit file-based project workflows rather than introducing a database prematurely.

Current/legacy behavior:

- JSON project files;
- explicit Open/Save;
- user-controlled file location.

New multi-analysis project format can be introduced under a new schema version while retaining legacy import compatibility.

A database may be considered later for recent-project indexing or multi-user/cloud features, but it is not required for the core engineering application rebuild.

## 19. Browser file interaction

Normal web security prevents arbitrary silent filesystem access, which is desirable.

Use user-initiated operations:

- Open/import through file picker/upload;
- Save/export through browser download or a later desktop-shell save dialog;
- no background modification of arbitrary project files.

When/if a desktop shell is introduced, the ProjectService boundary should allow a native filesystem adapter without changing calculation code.

## 20. Local/offline release model

Preferred R1/R2 release concept:

```text
User starts HCM application
  -> Python launcher starts localhost FastAPI server
  -> server serves compiled React SPA
  -> browser opens local application URL
  -> all calculation occurs locally
```

Bind to loopback (`127.0.0.1`/equivalent) by default.

No cloud dependency is required.

## 21. Development model

During development:

```text
Terminal/process 1: Python/FastAPI
Terminal/process 2: Vite development server
```

Vite proxies `/api` requests to the Python server or uses configured local API origin.

This gives frontend hot reload while preserving the actual Python engine boundary.

## 22. Release static assets

For local production builds:

```text
frontend npm build
  -> static assets
  -> packaged/served by HCM Python application
```

The release user should not need Node/npm.

Node is a developer/build/test dependency only.

## 23. Dependency principle

The existing application has a small engineering dependency footprint.

The rebuild should avoid frontend dependency sprawl.

Prefer:

- React;
- TypeScript;
- Vite;
- routing;
- focused accessibility/form/table utilities only when justified;
- Playwright for E2E/visual testing.

Do not install a large design-system framework merely to avoid implementing the intentionally small HCM design system.

## 24. Styling implementation

R0.8 defines a custom restrained design system.

Implementation may use:

- CSS variables + CSS modules/structured CSS;
- a lightweight utility approach;
- another well-governed local styling strategy.

The architecture does not require Tailwind or a specific component library.

Whichever approach is selected must centralize tokens and avoid method-specific style drift.

## 25. Diagrams

Use browser-native SVG for initial engineering diagrams unless prototype evidence shows a need for a more complex graphics layer.

Why:

- crisp at different resolutions;
- accessible labels/text possible;
- easy to test geometry/DOM;
- sufficient for Merge/Diverge/initial Weaving diagrams;
- no WebGL dependency required.

## 26. Data grid strategy

Two-Lane Facility is the key grid stress test.

Do not select a heavy grid library solely from feature lists before prototype testing.

R1/R2 should test whether a focused accessible table/grid implementation can provide:

- editing;
- locked cells;
- row validation;
- sticky header/first column;
- keyboard navigation;
- local horizontal scroll.

If not sufficient, evaluate a dedicated data-grid package based on those concrete requirements.

## 27. API schema generation

FastAPI/OpenAPI can provide a machine-readable contract for the frontend.

Recommended direction:

- define request/response Pydantic models;
- generate or validate TypeScript API types from OpenAPI during development/CI;
- fail CI when frontend contract assumptions drift.

Exact generator/tool is an implementation choice.

## 28. Test architecture

### Python numerical tests

Continue existing pytest suite unchanged where possible.

### Python application/API tests

Add:

- adapter/application-service tests;
- interpretation-rule tests;
- API request/response contract tests;
- project compatibility tests.

### Frontend unit/component tests

Cover:

- conditional input behavior;
- readiness/error display;
- result-state rendering;
- localization keys;
- stale/current transitions at frontend boundary.

### Playwright E2E

Use real browser journeys:

- Quick Analysis -> calculate -> result;
- edit -> stale -> recalculate;
- Save/Open project;
- legacy project import;
- Multilane measured/estimated FFS;
- capacity failure;
- Two-Lane Facility grid validation;
- Weaving handoff;
- Merge/Diverge workflow;
- compare scenarios;
- export current result.

Playwright currently supports Chromium, Firefox, WebKit, and branded Chromium browsers, enabling both primary Chrome/Edge qualification and broader regression checks.

### Visual regression

Capture reference screenshots for key desktop/narrow states.

## 29. CI architecture

Target CI jobs conceptually:

```text
python-engine
  pytest numerical/domain

python-application-api
  application + contract + compatibility tests

frontend
  typecheck + unit/component tests + build

browser
  Playwright primary journeys

visual
  selected visual regression baselines
```

The exact split may be optimized later, but frontend qualification must no longer be accidental/optional because Streamlit is omitted from the base dev dependency.

## 30. Runtime error boundary

Frontend must distinguish:

- validation error;
- unsupported HCM scope;
- capacity/handoff engineering result;
- API transport failure;
- internal backend exception.

FastAPI/application responses should use structured error codes so the frontend does not infer engineering meaning from HTTP text.

## 31. Security/locality baseline

For local single-user R1:

- bind API to loopback by default;
- no public network listening without explicit future design;
- do not execute arbitrary code from project files;
- validate imported project schemas;
- escape/render audit strings safely;
- keep browser/backend dependency versions patched.

Authentication is not required for the loopback-only single-user baseline.

## 32. Migration sequence

### R1 — Application Foundation

Build alongside the existing Streamlit UI:

- React/Vite shell;
- FastAPI boundary;
- application registry;
- design-system components;
- project/result state contracts;
- test harness.

No method mass migration.

### R2 — Representative Prototypes

Implement:

- Multilane Segment;
- Two-Lane Facility.

Prove:

- form workflow;
- conditional inputs;
- grid workflow;
- result hierarchy;
- stale state;
- project compatibility;
- browser testing.

### R3 — Remaining current methods

Port:

- Two-Lane Segment;
- Basic Freeway;
- Weaving;
- Merge;
- Diverge.

### R4 — Default UI transition

After acceptance:

- new frontend becomes normal application entry;
- legacy Streamlit UI is deprecated/retained temporarily as rollback evidence as appropriate;
- documentation updated.

### R5 — Packaging / desktop-shell evaluation

Only after browser-local acceptance:

- evaluate packaged Python launcher;
- optionally Tauri/native shell if filesystem/distribution experience warrants it.

## 33. Legacy Streamlit treatment

Do not delete Streamlit at the beginning.

During R1/R2 it provides:

- behavior reference;
- project compatibility source;
- fallback qualified UI;
- regression comparison.

New application code must not call Streamlit modules.

When migration is complete, framework-independent logic should no longer remain under `ui/` merely because of historical location.

## 34. R0.9 architectural rules

The following are implementation invariants:

1. HCM formulas remain Python-authoritative.
2. React frontend never duplicates method mathematics.
3. FastAPI is an application boundary, not a second calculation engine.
4. Quick and Project analyses use the same backend services.
5. Method availability comes from canonical registry/contracts.
6. Frontend method modules compose shared application components.
7. Project/report export does not rerun calculations.
8. Node tooling is not required by normal release users.
9. Local/offline use remains supported.
10. Desktop shell is deferred until the web-local architecture is qualified.

## 35. R0.9 acceptance criteria

R0.9 is acceptable when:

- selected architecture directly addresses the monolithic Streamlit composition problem;
- frontend and engine responsibilities are unambiguous;
- local/offline operation is preserved;
- current Python engine/package can migrate incrementally;
- project compatibility has a clear service boundary;
- frontend type/API drift can be tested;
- browser journeys can be qualified with Playwright;
- no unnecessary SSR/cloud/database/desktop-shell dependency is introduced;
- the architecture can support future HCM methods through registries/modules;
- Streamlit can coexist temporarily during migration.

## 36. Next R0 gate

R0.10 should convert all accepted R0 specifications into an implementation-ready prototype plan, including:

- exact R1/R2 deliverables;
- file/module boundaries;
- API contract skeleton;
- Analysis Registry skeleton;
- Multilane prototype acceptance cases;
- Two-Lane Facility prototype acceptance cases;
- legacy project compatibility fixtures;
- Playwright journeys;
- visual-reference screens;
- migration sequencing and stop/go gates.
