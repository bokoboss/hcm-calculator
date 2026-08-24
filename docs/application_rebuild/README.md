# HCM Calculator — Application Rebuild

Status: **R0 planning-complete and architecture-accepted; implementation not yet started**
Date: 2026-08-24
Planning branch: `planning/application-rebuild-r0`
Planning PR: #129 — Application Rebuild R0: Product & Architecture Reset
Implementation tracking: #130 — Application Rebuild R1/R2: Foundation and representative prototypes

## Purpose

This directory is the authoritative planning package for the engine-preserving HCM Calculator application rebuild.

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

R0.2 through R0.10 are documented and the cross-document architecture acceptance review is complete.

R0 is **architecture/specification only**. No production frontend, engine, dependency, test, or CI code is changed by PR #129.

The architecture review found no blocker requiring a change of product direction or technology architecture. It added binding clarifications for frontend-delivery availability, Project v2 state derivation, Recent Projects scope, release-like R1 integration, local API security, Project Overview hierarchy, context-aware toolbar behavior, and the Project v2 schema gate.

Implementation starts only after PR #129 is merged.

## Authority and conflict order

Implementation should resolve ambiguity in this order:

1. [`r0_architecture_acceptance_review.md`](r0_architecture_acceptance_review.md) — final cross-document clarifications and acceptance gates.
2. This README — current status, scope, and reading order.
3. [`r0_prototype_implementation_plan.md`](r0_prototype_implementation_plan.md) — implementation-ready R1/R2 sequence.
4. [`r0_technology_architecture.md`](r0_technology_architecture.md) — frontend/backend/runtime boundary.
5. Workflow/result/wireframe/design/product documents for their respective details.
6. Earlier sequential status prose only as planning history.

If any presentation specification conflicts with qualified engineering behavior on `main`, the qualified numerical/engineering contract wins until a separately reviewed engineering change says otherwise. Implementation must stop and record the conflict rather than silently changing the engine.

## Recommended reading order

1. [`r0_architecture_acceptance_review.md`](r0_architecture_acceptance_review.md)
   - final architecture review and disposition;
   - binding R1/R2 clarifications;
   - frontend-delivery vs engine-support availability;
   - Project v2 state/fingerprint authority;
   - release-like runtime and local security gates.

2. [`r0_product_architecture.md`](r0_product_architecture.md)
   - product definition;
   - Project / Analysis / Scenario / Result object model;
   - navigation and application-shell direction;
   - engine-preserving boundary;
   - future-method extensibility.

3. [`r0_decision_log.md`](r0_decision_log.md)
   - architectural rationale and accepted ADRs;
   - why the rebuild supersedes another Streamlit UX-polish phase;
   - compatibility and acceptance principles.

4. [`r0_workflow_architecture.md`](r0_workflow_architecture.md)
   - common workflow/state model;
   - target workflow for all seven currently supported analyses;
   - reusable workflow components;
   - validation and stale-result behavior.

5. [`r0_result_architecture.md`](r0_result_architecture.md)
   - Answer -> Engineering Performance -> Interpretation -> Evidence hierarchy;
   - per-method result priorities;
   - capacity failure, HCM handoff, warning, stale, and comparison semantics.

6. [`r0_wireframes.md`](r0_wireframes.md)
   - screen inventory and low-fidelity layouts;
   - Project Overview, New Analysis, Multilane, Facility grid, Weaving, Merge/Diverge, stale, compare, export, methodology, and audit states;
   - note that the acceptance review supersedes the early `Recent Projects` and flattened Project Overview examples where applicable.

7. [`r0_design_system.md`](r0_design_system.md)
   - professional engineering visual direction;
   - compact density;
   - shell geometry;
   - field/unit/validation/focus/table/result interaction rules;
   - accessibility and bilingual requirements.

8. [`r0_technology_architecture.md`](r0_technology_architecture.md)
   - React + TypeScript + Vite selection;
   - FastAPI / Python application boundary;
   - local/offline runtime model;
   - API, registry, project-file, localization, test, CI, and migration architecture.

9. [`r0_prototype_implementation_plan.md`](r0_prototype_implementation_plan.md)
   - R1/R2 sequence;
   - Multilane and Two-Lane Facility representative prototypes;
   - Project/Scenario/Compare closure;
   - Playwright, visual, compatibility, and numerical gates;
   - implementation stop conditions.

## Implementation sequence

```text
R1 — Application Foundation
  -> Gate R1

R2A — Multilane Segment representative prototype
  -> Gate R2A

R2B — Two-Lane Facility representative prototype
  -> Gate R2B

R2C — Project / Scenario / Compare closure
  -> Gate R2

R3 — Remaining current methods
```

Do not mass-port all seven methods before R2 acceptance.

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

## R1 additional acceptance clarifications

R1 must prove the selected runtime architecture, not only development servers:

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

Chosen to prove normal form workflow, conditional FFS and heavy-vehicle branches, units, capacity failure, result hierarchy, stale/recalculate lifecycle, localization, and legacy project import.

### Two-Lane Facility

Chosen to prove the multi-segment engineering grid, row/cell validation, locked vs editable context, facility aggregation, facility answer vs segment evidence, and complex browser/table interaction.

If the architecture works for both, broad migration has substantially stronger evidence than porting seven screens at once.

## Project v2 clarification

The Project v2 example in R0.10 is conceptual, not a release schema.

Before R2C treats Project v2 as durable persistence, create and accept a dedicated schema/compatibility specification covering IDs, Project/Analysis/Scenario relationships, method/input identity, displayed vs normalized inputs, stored result identity, fingerprint verification, result retain/discard rules, audit/warnings/assumptions, localization metadata boundaries, legacy 1.2 import, future-version rejection, and deterministic round-trip fixtures.

Serialized `presentation_state` is not authoritative. Current/stale/result presentation state is recomputed from verified method/input/fingerprint/result identity when loading.

## Home / Project Overview clarification

`Recent Projects` is not required in R1/R2 because the selected browser-local/file workflow does not yet define a reliable durable reopen permission/index. Do not add a database just to reproduce the early wireframe example.

Project Overview is analysis-first. Scenarios remain children of an Analysis and are expanded/opened within that Analysis rather than turning every scenario into a duplicate top-level Analysis row.

## Superseded Phase 17 plan

Issue #128 (`Phase 17: Release hardening and engineering acceptance`) is closed as superseded/not planned.

The branch `codex/phase-17-planning` is intentionally retained temporarily as historical reference. It must not be merged or treated as rebuild implementation authority because its single-page Streamlit premise conflicts with the accepted Application Rebuild direction.

Useful release-hardening ideas may still be carried forward individually when compatible with this R0 package.

## Next repository action

PR #129 is now eligible for final acceptance and merge.

After merge:

1. issue #130 becomes the R1/R2 implementation parent together with the merged R0 documents;
2. create an isolated implementation branch/worktree such as `codex/application-rebuild-r1-foundation`;
3. implement R1 Application Foundation only;
4. prove the strengthened Gate R1, including release-like single-origin local serving;
5. push a reviewable R1 PR;
6. do not begin Multilane R2A until R1 is accepted.
