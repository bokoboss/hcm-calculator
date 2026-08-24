# HCM Calculator — Application Rebuild

Status: **R0 planning-complete; implementation not yet started**
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

R0.2 through R0.10 are now documented.

R0 is **architecture/specification only**. No production frontend, engine, dependency, test, or CI code is changed by the R0 planning PR.

The earlier R0 documents were written sequentially. Some early sections intentionally use future tense such as `R0 remaining work` or list decisions that were unresolved at that moment. For current status, this README and `r0_prototype_implementation_plan.md` take precedence: the later R0 gates have now been completed as planning specifications.

Implementation must still wait for review/acceptance of PR #129.

## Recommended reading order

1. [`r0_product_architecture.md`](r0_product_architecture.md)
   - product definition;
   - Project / Analysis / Scenario / Result object model;
   - navigation and application-shell direction;
   - engine-preserving boundary;
   - future-method extensibility.

2. [`r0_decision_log.md`](r0_decision_log.md)
   - architectural rationale and accepted ADRs;
   - why the rebuild supersedes another Streamlit UX-polish phase;
   - compatibility and acceptance principles.

3. [`r0_workflow_architecture.md`](r0_workflow_architecture.md)
   - common workflow/state model;
   - target workflow for all seven currently supported HCM analyses;
   - reusable workflow components;
   - validation and stale-result behavior.

4. [`r0_result_architecture.md`](r0_result_architecture.md)
   - Answer -> Engineering Performance -> Interpretation -> Evidence hierarchy;
   - per-method result priorities;
   - capacity failure, HCM handoff, warning, stale, and comparison semantics.

5. [`r0_wireframes.md`](r0_wireframes.md)
   - screen inventory;
   - low-fidelity desktop-first wireframes;
   - Project Overview, New Analysis, Multilane, Facility grid, Weaving, Merge/Diverge, stale, compare, export, methodology, and audit screens.

6. [`r0_design_system.md`](r0_design_system.md)
   - conventional professional engineering visual direction;
   - compact density;
   - shell geometry;
   - field/unit/validation/focus/table/result interaction rules;
   - accessibility and bilingual requirements.

7. [`r0_technology_architecture.md`](r0_technology_architecture.md)
   - React + TypeScript + Vite selection;
   - FastAPI / Python application boundary;
   - local/offline runtime model;
   - API, registry, project-file, localization, test, CI, and migration architecture.

8. [`r0_prototype_implementation_plan.md`](r0_prototype_implementation_plan.md)
   - implementation-ready R1/R2 sequence;
   - Multilane and Two-Lane Facility representative prototypes;
   - Project/Scenario/Compare closure;
   - Playwright, visual, project-compatibility, and numerical gates;
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
3. The rebuild must preserve numerical equivalence unless a separately reviewed engineering bug fix explicitly changes it.
4. Existing fingerprint/stale-result semantics must be retained or deliberately migrated with compatibility tests.
5. v0.9 / project schema 1.2 compatibility remains a migration requirement.
6. Reports/exports represent accepted current results and must not silently rerun calculations.
7. Capacity-failure and HCM-handoff states must not fabricate unavailable performance measures.
8. Quick Analysis and Project Analysis reuse the same engineering services.
9. The qualified Streamlit UI remains runnable through the representative-prototype migration.
10. New HCM methods should integrate through common registry/contracts rather than another monolithic dispatcher.

## Representative prototypes

### Multilane Segment

Chosen to prove:

- normal form workflow;
- conditional FFS branches;
- heavy-vehicle treatment branches;
- units;
- capacity failure;
- result hierarchy;
- stale/recalculate lifecycle;
- legacy project import/export.

### Two-Lane Facility

Chosen to prove:

- multi-segment engineering grid;
- row/cell validation;
- locked vs editable context;
- facility aggregation;
- facility answer vs segment evidence;
- complex browser/table interaction.

If the architecture works for both, broad migration has much stronger evidence than porting seven screens at once.

## Superseded Phase 17 plan

Issue #128 (`Phase 17: Release hardening and engineering acceptance`) is closed as superseded/not planned.

The branch `codex/phase-17-planning` is intentionally retained temporarily as historical reference. It must not be merged or treated as rebuild implementation authority because its single-page Streamlit premise conflicts with the accepted Application Rebuild direction.

Useful release-hardening ideas from that plan may still be carried forward individually when compatible with this R0 package.

## Next gate

The next repository decision is **R0 acceptance**, not production coding.

After PR #129 is reviewed and accepted:

1. merge the planning-only R0 PR;
2. use issue #130 as the implementation parent;
3. create an isolated implementation branch/worktree, suggested:
   `codex/application-rebuild-r1-foundation`;
4. implement R1 Application Foundation only;
5. push a reviewable PR and qualify it before starting Multilane R2A.

If implementation discovers a conflict between this R0 package and the qualified engineering behavior on `main`, stop and record the conflict rather than changing the engine or inventing methodology to make the UI fit.
