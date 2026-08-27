# HCM Calculator — Application Rebuild

Status: **Phase 1 — Application Foundation accepted and merged; Phase 2 — Prototype & Architecture Validation authorized**
Date: 2026-08-27
Accepted R0 commit: `6482808c06fd4bfc3f6d6ef246bd6efdc58c4e65`
Accepted Phase 1 commit: `cfcfe7af14d821dadc04c4f067322ef5d3760c1c`
Accepted Phase 1 PR / CI: #133 / R1 qualification run #249
Implementation tracking: #130 — historical R1/R2 parent; use the current three-phase roadmap below for management

## Purpose

This directory is the authoritative architecture/specification package for the engine-preserving HCM Calculator application rebuild.

The rebuild changes the product/application/frontend architecture while preserving the qualified Python HCM calculation engine, numerical contracts, auditability, project compatibility safeguards, and reporting behavior unless a separately reviewed engineering change explicitly says otherwise.

Core product direction:

```text
Project
  -> Analysis
      -> Scenario
          -> Engineering Inputs
              -> HCM Calculation
                  -> Result + Interpretation
                      -> Compare / Review / Report / Audit
```

Target technology direction:

```text
React + TypeScript + Vite SPA
        |
        | local HTTP / JSON
        v
FastAPI application/API boundary
        |
        v
Python application services
        |
        v
Existing qualified HCM engines
```

## Current status

R0.2 through R0.10 and the final cross-document Architecture Acceptance Review are complete and merged to `main` through PR #129.

R0 was documentation/architecture only. It did not change production frontend code, engine formulas, dependencies, tests, or CI behavior.

The final review found no blocker requiring a change of product direction or technology architecture. Binding clarifications were added for:

- backend engineering availability vs rebuilt-frontend delivery availability;
- fingerprint-derived current/stale state;
- Project v2 persistence authority;
- Recent Projects scope;
- release-like R1 local serving;
- local API security;
- Analysis/Scenario hierarchy;
- context-aware application actions;
- the Project v2 schema gate.

R1 Application Foundation has been accepted and merged through PR #133. The next authorized implementation step is Phase 2 — Prototype & Architecture Validation.

## Authority and conflict order

Implementation should resolve ambiguity in this order:

1. [`r0_architecture_acceptance_review.md`](r0_architecture_acceptance_review.md) — final cross-document clarifications and acceptance gates.
2. This README — current status, scope, and reading order.
3. [`r0_prototype_implementation_plan.md`](r0_prototype_implementation_plan.md) — implementation-ready R1/R2 sequence.
4. [`r0_technology_architecture.md`](r0_technology_architecture.md) — frontend/backend/runtime boundary.
5. Workflow/result/wireframe/design/product documents for their respective details.
6. Earlier sequential status prose only as planning history.

If a presentation specification conflicts with qualified engineering behavior on `main`, the qualified numerical/engineering contract wins until a separately reviewed engineering change says otherwise. Implementation must stop and record the conflict rather than silently changing the engine.

## Recommended reading order

1. [`r0_architecture_acceptance_review.md`](r0_architecture_acceptance_review.md)
2. [`r0_product_architecture.md`](r0_product_architecture.md)
3. [`r0_decision_log.md`](r0_decision_log.md)
4. [`r0_workflow_architecture.md`](r0_workflow_architecture.md)
5. [`r0_result_architecture.md`](r0_result_architecture.md)
6. [`r0_wireframes.md`](r0_wireframes.md)
7. [`r0_design_system.md`](r0_design_system.md)
8. [`r0_technology_architecture.md`](r0_technology_architecture.md)
9. [`r0_prototype_implementation_plan.md`](r0_prototype_implementation_plan.md)

The acceptance review supersedes early wireframe examples where it explicitly clarifies behavior, including Recent Projects and flattened Analysis/Scenario rows.

## Implementation sequence

The user-facing development roadmap is intentionally kept to three main phases. Older R1/R2A/R2B/R2C labels remain useful as internal engineering checkpoints, not separate management/approval phases.

```text
Pre-development — R0 Product & Architecture Reset
  -> accepted

Phase 1 — Application Foundation
  -> maps to former R1
  -> accepted at cfcfe7af14d821dadc04c4f067322ef5d3760c1c

Phase 2 — Prototype & Architecture Validation
  -> internal checkpoint 2.1: Multilane Segment
  -> internal checkpoint 2.2: Two-Lane Facility
  -> internal checkpoint 2.3: Project / Scenario / Compare
  -> internal checkpoint 2.4: Architecture Acceptance

Phase 3 — Full Migration & Release
  -> remaining five current workflows
  -> parity / regression / runtime / packaging / default-UI transition
```

Phase 2 should normally run as one bounded implementation cycle with internal self-gates. Stop for external re-planning only when a genuine architecture, engineering-contract, compatibility, or distribution stop condition is reached.

Do not mass-port all seven methods before Phase 2 acceptance.

## Non-negotiable invariants

1. Python remains the HCM calculation authority.
2. Frontend TypeScript must not duplicate HCM formulas.
3. Numerical equivalence is preserved unless a separately reviewed engineering bug fix explicitly changes it.
4. Current/stale state is fingerprint-driven and derived, not trusted from serialized presentation state.
5. v0.9 / project schema 1.2 compatibility remains a migration requirement.
6. Reports/exports represent accepted current results and must not silently rerun calculations.
7. Capacity-failure and HCM-handoff states must not fabricate unavailable performance measures.
8. Quick Analysis and Project Analysis reuse the same engineering services.
9. The qualified Streamlit UI remains runnable through representative-prototype migration.
10. New HCM methods integrate through common registry/contracts rather than another monolithic dispatcher.
11. A method is actionable in the rebuilt normal UI only when both engineering support and a compatible delivered frontend module exist.
12. Project v2 cannot become release-stable before its dedicated schema/compatibility gate passes.

## Strengthened Gate R1

R1 must prove the selected runtime architecture, not only separate development servers:

```text
frontend production build
-> compiled SPA served by Python/FastAPI
-> API and SPA share one loopback origin
-> browser smoke succeeds
-> Node/Vite runtime is not required for that smoke
```

The local API is deny-by-default for cross-origin access: no wildcard CORS, loopback binding by default, and only explicit development origins when development CORS is required.

The rebuilt New Analysis workflow must not expose dead-end method cards. Backend engineering support and frontend delivery status are separate concerns; normal user actions require both.

## Representative prototypes

### Multilane Segment

Proves normal form workflow, conditional FFS and heavy-vehicle branches, units, capacity failure, result hierarchy, stale/recalculate lifecycle, localization, and legacy project import.

### Two-Lane Facility

Proves the multi-segment engineering grid, row/cell validation, locked vs editable context, facility aggregation, facility answer vs segment evidence, and complex browser/table interaction.

## Project v2 clarification

The Project v2 example in R0.10 is conceptual, not a release schema.

Before R2C treats Project v2 as durable persistence, create and accept a dedicated schema/compatibility specification covering IDs, Project/Analysis/Scenario relationships, method/input identity, displayed vs normalized inputs, stored result identity, fingerprint verification, result retain/discard rules, audit/warnings/assumptions, localization metadata boundaries, legacy 1.2 import, future-version rejection, and deterministic round-trip fixtures.

Serialized `presentation_state` is not authoritative. Current/stale/result presentation state is recomputed from verified method/input/fingerprint/result identity when loading.

## Home / Project Overview clarification

`Recent Projects` is not required in R1/R2 because the selected browser-local/file workflow does not yet define a reliable durable reopen permission/index. Do not add a database merely to reproduce the early wireframe example.

Project Overview is analysis-first. Scenarios remain children of an Analysis and are expanded/opened within that Analysis rather than turning every Scenario into a duplicate top-level Analysis row.

## Superseded Phase 17 plan

Issue #128 (`Phase 17: Release hardening and engineering acceptance`) is closed as superseded/not planned.

The branch `codex/phase-17-planning` is retained as historical reference only. It must not be merged or treated as rebuild implementation authority because its single-page Streamlit premise conflicts with the accepted Application Rebuild direction.

## Next action — Phase 2 Prototype & Architecture Validation

Phase 1 / R1 is complete and accepted at `cfcfe7af14d821dadc04c4f067322ef5d3760c1c`.

The next implementation work must:

1. start from current clean `main` containing the accepted Phase 1 foundation and Engineering Development Workflow v1.4.1;
2. use one isolated Phase 2 implementation branch/worktree;
3. implement the representative Multilane Segment and Two-Lane Facility workflows on the accepted application foundation;
4. complete Project / Analysis / Scenario / Compare behavior and the required persistence/compatibility work without weakening legacy schema 1.2 safeguards;
5. preserve numerical equivalence, Python calculation authority, current/stale fingerprints, Streamlit compatibility, and contract-safe frontend delivery;
6. run the internal Phase 2 checkpoints autonomously when no architecture stop condition is triggered;
7. push one reviewable Phase 2 PR with engineering, API, frontend, browser, project-compatibility, and regression evidence;
8. return to ChatGPT/GitHub acceptance before Phase 3 full migration.
