# Application Rebuild R0 — Decision Log

Status: Active
Date opened: 2026-08-24
Branch: `planning/application-rebuild-r0`

This log records product and architecture decisions made during the HCM Calculator application rebuild. The goal is to keep the rationale visible so later implementation does not accidentally revert to assumptions from the previous Streamlit worksheet architecture.

Decision status values:

- **Accepted** — current authoritative direction.
- **Provisional** — preferred direction but still requires a later R0 gate.
- **Superseded** — retained for history but no longer authoritative.
- **Rejected** — explicitly not selected.

---

## ADR-001 — Stop treating the next phase as another Streamlit UX-polish phase

**Status:** Accepted

### Context

Phase 16 substantially improved consistency, localization, hierarchy, validation disclosure, and browser qualification, but the product still behaves primarily as a single-page calculator/worksheet application. The remaining usability issue is structural rather than cosmetic.

### Decision

The next product track is an **engine-preserving application rebuild**, not another broad Streamlit styling/polish phase.

### Consequences

- Production implementation must wait for Product/IA/Workflow/Result/Wireframe/Technology gates.
- Existing Streamlit presentation code is not a compatibility requirement.
- Existing engineering calculations and contracts remain protected.

---

## ADR-002 — Preserve the validated HCM engine as calculation authority

**Status:** Accepted

### Context

The repository already contains implemented method modules, structured models, validation fixtures, unit conversions, deterministic tests, audit behavior, project persistence, and reporting logic.

### Decision

The rebuild will not duplicate or reimplement HCM calculations in the frontend. Python remains the single engineering calculation authority.

### Consequences

- Frontend code owns presentation/workflow, not HCM equations.
- Numerical equivalence can be regression-tested against the existing qualified baseline.
- Application changes can be evaluated separately from engineering-method changes.

---

## ADR-003 — Adopt `Project -> Analysis -> Scenario -> Result` as the core product model

**Status:** Accepted

### Context

Real engineering work commonly contains multiple analytical locations and multiple alternatives. A single-calculator mental model does not represent this work well.

### Decision

Use the following object hierarchy:

```text
Project
  -> Analysis
      -> Scenario
          -> Calculation Result
```

Reports/exports present existing results rather than becoming calculation objects.

### Consequences

- A Project can contain many different HCM methods.
- One Analysis can contain Existing/No-Build/Option scenarios.
- Result identity remains tied to method, normalized inputs, fingerprint, and state.

---

## ADR-004 — Scenario functionality must not burden one-off calculations

**Status:** Accepted

### Context

A full project/scenario workflow would be excessive for users who only need one calculation.

### Decision

Every new Analysis receives a default Base Scenario automatically. The scenario concept may remain visually quiet until the user duplicates or compares alternatives. Quick Analysis does not require a persistent Project.

### Consequences

- The architecture supports professional scenario work without making simple calculations harder.
- A Quick Analysis can later be saved into a Project.

---

## ADR-005 — Navigation is facility/task-based; HCM chapter is metadata

**Status:** Accepted

### Context

Engineers generally approach the tool by facility/analysis type rather than chapter number, and HCM chapter numbering can change between editions.

### Decision

Top-level navigation is organized around engineering facility/task families such as Highways, Freeways, Intersections, Urban Streets, Pedestrian, Bicycle, and Transit.

HCM edition/chapter/method identifiers are displayed as analysis methodology metadata.

### Consequences

- Adding or revising HCM editions does not require conceptual navigation redesign.
- Method names remain stable and user-oriented.

---

## ADR-006 — Use a Curbside-inspired application shell

**Status:** Accepted

### Context

The Airport Curbside Analysis Tool v1.1 uses a conventional but effective application grammar: header toolbar, left navigation, main workspace, and persistent status. It cleanly separates application actions from calculation content.

### Decision

Use the same broad grammar for the rebuilt HCM application:

```text
Header Toolbar
Left Navigation | Main Workspace
Persistent Status
```

This is a pattern reference, not a requirement to visually clone the Curbside Tool.

### Consequences

- New/Open/Save/Export/Help live at application level.
- Project actions no longer compete visually with engineering inputs.
- The user has a stable location model across analyses.

---

## ADR-007 — Shared design grammar, method-specific internal controls

**Status:** Accepted

### Context

HCM methods differ materially. Some are compact forms; Two-Lane Facility is tabular/multi-segment; Weaving benefits from geometry visualization; future intersection analyses may require phase/lane diagrams.

### Decision

Every method shares the high-level grammar:

```text
Analysis Header
Setup / Context
Traffic
Geometry
Method-specific Conditions
Readiness / Validation
Calculate
Results
Engineering Interpretation
Details / Methodology / Audit
```

Within this grammar, each method may use specialized grids, controls, diagrams, and result components.

### Consequences

- Users learn one application structure.
- The architecture does not force every HCM method into the same simplistic form layout.

---

## ADR-008 — Add future HCM methods through a lightweight Analysis Registry

**Status:** Accepted

### Context

The current Streamlit application has a large central dispatcher. Repeating that pattern would make future chapter expansion increasingly expensive.

### Decision

Define lightweight registration/contracts for each analysis type, including conceptually:

- id;
- family/name;
- HCM edition/chapter/method identifier;
- unit support;
- workflow/input definition;
- result definition;
- engine adapter;
- project adapter;
- report adapter;
- localization/help/scope metadata.

Do not build a speculative general-purpose plugin SDK in R0.

### Consequences

- New methods should primarily be added as registered analysis modules.
- The central application shell should not require a new large `if/elif` branch for every method.

---

## ADR-009 — Present results in four levels of hierarchy

**Status:** Accepted

### Context

The current result presentation gives useful metrics but does not sufficiently separate the engineering answer from detailed evidence.

### Decision

Use four result levels:

1. **Answer** — LOS / primary status / capacity or handoff state.
2. **Engineering Performance** — method-specific metrics.
3. **Interpretation** — deterministic explanation, limitations, governing condition, freshness/status.
4. **Evidence** — normalized inputs, factors, intermediate values, assumptions, references, audit data.

### Consequences

- Primary engineering meaning is visible immediately.
- Auditability remains available without overwhelming normal users.
- Interpretation must not invent unsupported methodology or design recommendations.

---

## ADR-010 — Maintain v0.9 project compatibility during migration

**Status:** Accepted

### Context

Qualified v0.9 projects already contain stable method identifiers, displayed and normalized inputs, fingerprints, result information, audit data, warnings, assumptions, and presentation metadata.

### Decision

The rebuilt application must import qualified legacy project files and map a legacy single-analysis project into the new Analysis/Base Scenario model when compatibility checks succeed.

### Consequences

- Existing user work is not abandoned.
- Stored results must only be retained when method/fingerprint/result compatibility is verifiable.
- Existing stale/unverifiable-result protections must not be weakened.

---

## ADR-011 — Reports and exports do not rerun calculations

**Status:** Accepted

### Context

The existing reporting layer is deliberately generated from stored current results rather than rerunning the engine.

### Decision

Retain this behavior in the rebuilt application.

### Consequences

- Export is presentation, not a hidden engineering-state transition.
- Printed/exported outputs remain tied to the result the user actually reviewed.

---

## ADR-012 — Use Multilane Segment and Two-Lane Facility as representative rebuild prototypes

**Status:** Accepted

### Context

Porting all supported analyses simultaneously would make it difficult to prove that the new architecture works before committing to it.

### Decision

Use two contrasting prototypes:

1. **Multilane Highway Segment** — conditional branches, FFS, heavy vehicles, units, capacity/status behavior.
2. **Two-Lane Facility** — multi-segment grid, row validation, aggregation, richer result structure.

Weaving may be used later as a diagram-heavy third prototype.

### Consequences

- The common application contracts must prove themselves against both simple/conditional and complex/tabular workflows before mass migration.

---

## ADR-013 — Separate numerical acceptance from application acceptance

**Status:** Accepted

### Context

A green numerical test suite can coexist with an application that remains difficult to use.

### Decision

The rebuild requires separate acceptance layers:

1. numerical regression;
2. application/API contract tests;
3. legacy project compatibility;
4. browser user journeys;
5. visual regression.

### Consequences

- Numerical correctness remains necessary but is not sufficient for release acceptance.
- User workflow and presentation regressions become explicit release criteria.

---

## ADR-014 — Do not merge `codex/phase-17-planning` as the rebuild authority

**Status:** Accepted

### Context

The existing Phase 17 planning branch was created under the assumption that a broad architecture rewrite was not justified and that the current single-page worksheet structure should remain compatible. That premise conflicts with the newly accepted rebuild direction.

### Decision

Do not merge `codex/phase-17-planning` into the rebuild planning branch or treat it as implementation authority.

Retain it temporarily as historical reference until the replacement R0 plan is mature enough to supersede it formally.

### Consequences

- Useful prior release-hardening ideas may still be referenced individually.
- The old architectural premise will not constrain the new product design.

---

## ADR-015 — Do not select the final frontend technology before IA/workflow/wireframe gates

**Status:** Accepted

### Context

Repository structure makes a separate modern frontend plus Python application/API layer feasible, but selecting a framework before the workflow and screen architecture are defined risks technology-led product design.

### Decision

Technology selection is deferred to R0.9.

A React/Next.js-style frontend plus Python API/application layer is a leading candidate, not an approved implementation decision yet.

### Consequences

- R0.5–R0.8 remain framework-neutral where practical.
- Tauri/Electron packaging is also deferred until the local web experience is proven.

---

## ADR-016 — R0 is documentation/architecture only

**Status:** Accepted

### Context

Implementation before the product model, workflow architecture, result architecture, wireframes, design system, migration boundary, and acceptance gates are settled would recreate the current iteration problem.

### Decision

No production frontend rewrite is authorized during R0.

R0 completes:

- product definition;
- information architecture;
- workflow architecture;
- result architecture;
- wireframes/screen inventory;
- design system/interaction rules;
- technology decision;
- prototype specification;
- migration/compatibility requirements;
- acceptance harness specification.

### Consequences

Codex should not begin implementation until the R0 package is accepted.

---

# Open decisions for later R0 gates

The following remain intentionally unresolved:

- exact Project/Quick Analysis home-screen behavior;
- detailed workflow steps for all seven current methods;
- exact comparison semantics across scenario types;
- which deterministic engineering interpretations are safe per method;
- screen-level wireframes and responsive behavior;
- final visual design system;
- frontend framework and Python application/API boundary;
- local packaging/distribution strategy;
- exact Analysis Registry schema/API;
- final migration schema for new multi-analysis projects;
- release/versioning strategy for the rebuilt application.

These items should be resolved through R0.5–R0.10 rather than during implementation.
