# Application Rebuild R0.10 — Prototype Implementation Plan

Status: Implementation-ready R0 baseline
Date: 2026-08-24
Branch: `planning/application-rebuild-r0`

## 1. Purpose

This document converts the R0 product, workflow, result, wireframe, design-system, and technology decisions into an implementation-ready plan for Codex or another implementation agent.

R0 itself remains documentation/architecture only. Production implementation starts in R1 after this planning branch is reviewed/accepted.

The rebuild principle remains:

> Rebuild the application layer and frontend. Preserve the qualified engineering engine.

## 2. R0 authority set

Implementation must read these documents together:

```text
docs/application_rebuild/
  r0_product_architecture.md
  r0_decision_log.md
  r0_workflow_architecture.md
  r0_result_architecture.md
  r0_wireframes.md
  r0_design_system.md
  r0_technology_architecture.md
  r0_prototype_implementation_plan.md
```

If implementation discovers a conflict between these documents and the qualified engineering behavior on `main`, do not silently change the engine to fit the spec. Record the conflict and resolve it as an architecture/engineering decision.

## 3. Implementation constraints

The first implementation branch must not:

- rewrite HCM equations;
- change qualified numerical outputs merely to simplify frontend integration;
- duplicate calculation formulas in TypeScript;
- remove the Streamlit application before replacement qualification;
- break v0.9 project compatibility;
- introduce a cloud dependency;
- introduce a database as a prerequisite;
- introduce Tauri/Electron as a prerequisite;
- port all seven methods simultaneously;
- make design recommendations beyond current qualified methodology.

## 4. Target implementation sequence

```text
R1 Application Foundation
  -> Gate R1

R2A Multilane Representative Prototype
  -> Gate R2A

R2B Two-Lane Facility Representative Prototype
  -> Gate R2B

R2C Project/Scenario/Compare Prototype Closure
  -> Gate R2

R3 Remaining Current Methods
```

Do not begin R3 before the R2 architecture is accepted in real browser workflows.

# R1 — Application Foundation

## 5. R1 objective

Create the new frontend/backend/application architecture beside the existing qualified Streamlit UI, with no requirement for complete method parity.

At R1 completion:

- existing Python numerical tests still pass;
- new application layer exists;
- FastAPI starts locally;
- React/Vite shell starts locally;
- API/frontend contract tests run;
- application shell/design-system components render;
- method registry can describe current methods;
- no engineering calculation is implemented in TypeScript.

## 6. R1.1 — Repository/application-layer foundation

Create explicit framework-independent application packages.

Target concept:

```text
src/hcmcalc/application/
  __init__.py
  registry.py
  contracts.py
  workflow_state.py
  interpretation.py
  analyses/
  projects/
  reporting/
```

Initial work:

- establish application contracts without changing engine outputs;
- move or wrap existing framework-independent UI adapters gradually;
- preserve legacy import paths temporarily where required for tests/compatibility;
- avoid a large all-at-once file move.

Acceptance:

- Python engine modules do not import FastAPI/React/Streamlit;
- application modules do not require Streamlit;
- existing tests remain green.

## 7. R1.2 — Analysis Registry

Create a backend-authoritative registry for current analysis methods.

Minimum canonical entries:

```text
two_lane_segment
two_lane_facility
multilane_segment
basic_freeway_segment
weaving_segment
merge_segment
diverge_segment
```

Each entry should provide at minimum:

```text
method_id
family
name_key
description_key
method_identifier
method_version / engineering version metadata
input_contract
HCM edition
chapter/reference metadata
supported unit systems
availability
capabilities
scope summary keys
```

Do not encode all form controls in one giant backend JSON schema merely to make the frontend generic. Method-specific frontend composition remains allowed/expected.

Acceptance:

- registry has unit tests;
- IDs are stable/language-neutral;
- frontend can discover supported analyses without hard-coded top-level navigation labels.

## 8. R1.3 — Application result/state contracts

Implement framework-independent contracts based on R0.6.

Minimum canonical states:

```text
prerun
valid_current_result
valid_current_result_with_warning
capacity_failure
hcm_stopping_or_handoff
stale_result
invalid_input
unsupported_scope
internal_error
```

Preserve/reuse existing fingerprint semantics.

Implement canonical interpretation codes, not only prose.

Example:

```text
capacity_below_limit
capacity_exceeded
result_stale
facility_length_weighted
facility_critical_segment
weaving_handoff
```

Acceptance:

- rules unit-tested independent of frontend;
- existing result contracts are not modified unnecessarily;
- localization is not embedded in engineering identity.

## 9. R1.4 — FastAPI boundary

Create:

```text
src/hcmcalc/api/
  main.py
  schemas.py
  routes/
```

Initial endpoints:

```text
GET  /api/v1/health
GET  /api/v1/methods
GET  /api/v1/methods/{method_id}
```

Calculation endpoints may be introduced first for Multilane in R2A, unless a generic service boundary is useful earlier.

Requirements:

- localhost-safe default;
- typed Pydantic schemas;
- structured error codes;
- OpenAPI available in development;
- no HCM formulas in route handlers.

Acceptance:

- API tests run under pytest;
- starting API does not require Streamlit;
- current package remains installable.

## 10. R1.5 — Frontend foundation

Create:

```text
frontend/
  package.json
  tsconfig...
  vite...
  src/
    app/
    components/
    analyses/
    project/
    compare/
    reference/
    api/
    i18n/
    styles/
```

Use React + TypeScript + Vite.

Do not use Next.js in R1.

Acceptance:

- development server starts;
- production build succeeds;
- no external CDN/runtime internet dependency;
- TypeScript strictness is enabled to a practical production standard.

## 11. R1.6 — AppShell and design-system primitives

Implement initial shared components from R0.8:

```text
AppShell
AppHeader
SidebarNavigation
StatusBar
PageHeader
AnalysisHeader
EngineeringSection
Field
InputWithUnit
ChoiceGroup
ScopeNotice
ErrorSummary
ReadinessBar
ResultHero
MetricCard
EngineeringAssessment
StatusBadge
DetailsDisclosure/Tabs
StaleResultBanner
CapacityFailurePanel
HandoffPanel
```

Do not implement method-specific calculation pages yet beyond visual fixtures/stories/test routes where useful.

Acceptance:

- desktop shell matches R0.7 hierarchy;
- narrow layout does not page-overflow because of shell geometry;
- focus states and keyboard access pass initial QA;
- Thai placeholder strings do not clip common controls.

## 12. R1.7 — Localization foundation

Create structured frontend Thai/English resources.

Migration strategy:

- reuse existing terminology from `ui/i18n.py`;
- do not manually retranslate established technical terms without reason;
- canonical backend codes map to frontend translation keys.

Acceptance:

- language switch does not call calculation engine;
- navigation and shared result states available in Thai/English;
- no canonical method ID changes by locale.

## 13. R1.8 — API type/contract discipline

Use FastAPI OpenAPI as a machine-readable API contract.

Implement one of:

- generated TypeScript API types; or
- CI validation that frontend request/response types match OpenAPI.

Tool selection can be made during implementation, but contract drift must fail tests/CI.

## 14. R1.9 — Test harness foundation

### Python

- existing pytest suite;
- application-state tests;
- registry tests;
- API tests.

### Frontend

- typecheck;
- unit/component test harness;
- accessibility-focused component checks where practical.

### Playwright

Initial journey:

```text
launch app
-> Home visible
-> open New Analysis
-> supported method cards visible
-> switch Thai/English
-> navigate reference page
```

### Visual

Initial baselines:

- Home desktop;
- Project shell desktop;
- New Analysis desktop;
- narrow shell.

## 15. R1.10 — CI foundation

Add independent CI jobs or clearly separated steps:

```text
python-engine
python-application-api
frontend
browser
```

Do not make frontend tests silently skip because optional UI dependencies are not installed.

## 16. Gate R1

R1 may proceed to Multilane implementation only if:

- existing numerical suite passes unchanged or changes are explicitly justified;
- React production build passes;
- API tests pass;
- AppShell browser journey passes;
- no engine imports frontend/API code;
- no TypeScript HCM formulas exist;
- method registry is authoritative and stable;
- local/offline launch path is demonstrated in development form.

# R2A — Multilane Representative Prototype

## 17. R2A objective

Prove the form-based workflow, conditional inputs, backend normalization, result hierarchy, stale state, current-result export boundary, localization, and browser QA using Multilane Segment.

## 18. R2A.1 — Move/wrap Multilane application adapter

Use existing `manual_multilane.py` behavior as the migration seam.

Create application service functions conceptually:

```text
get_multilane_starting_values(...)
validate_multilane(...)
calculate_multilane(...)
build_multilane_presentation(...)
```

Preserve:

- UI-to-engine unit conversion;
- FFS branches;
- heavy-vehicle treatment mapping;
- external PCE behavior;
- engine result conversion;
- audit behavior;
- fingerprint identity.

## 19. R2A.2 — Multilane API

Add typed endpoints/service operations.

Conceptual request:

```json
{
  "unit_system": "metric",
  "displayed_inputs": {
    "number_of_lanes": 2,
    "segment_length": 1.2,
    "demand_volume_veh_h": 1690,
    "peak_hour_factor": 0.92,
    "heavy_vehicle_percent": 8,
    "ffs_source": "estimated",
    "posted_speed_limit": 90,
    "lane_width": 3.5,
    "roadside_lateral_clearance": 1.8,
    "median_type": "divided",
    "left_side_lateral_clearance": 0.6,
    "access_point_density": 4,
    "heavy_vehicle_adjustment_method": "general_terrain",
    "terrain_type": "rolling"
  }
}
```

Conceptual response:

```json
{
  "method_id": "multilane_segment",
  "input_contract": "...",
  "calculation_fingerprint": "...",
  "presentation_state": "valid_current_result",
  "normalized_inputs": {},
  "engine_result": {},
  "presentation": {
    "answer": {},
    "metrics": [],
    "interpretation_codes": []
  },
  "audit": {}
}
```

Exact field names should reuse existing contracts where possible rather than invent duplicate vocabulary.

## 20. R2A.3 — Multilane frontend

Implement sections from R0.7:

```text
Traffic
Segment
Free-Flow Speed
Heavy-Vehicle Adjustment
Readiness / Calculate
Result
Details
```

Conditional branches:

- measured vs estimated FFS;
- divided median left clearance;
- general terrain / specific grade / external PCE.

## 21. R2A.4 — Multilane result

Implement:

- LOS/status hero;
- density supporting measure when available;
- key metrics;
- deterministic Engineering Assessment;
- capacity-failure panel;
- method/scope details;
- audit evidence.

## 22. R2A.5 — Multilane stale behavior

Browser behavior:

```text
calculate
-> result current
-> edit PHF
-> result immediately stale
-> export current disabled
-> Recalculate
-> new result current
```

If exact normalized inputs/fingerprint return to the accepted calculation, current status may restore only according to the canonical fingerprint rules.

## 23. R2A.6 — Multilane project compatibility

Use at least one qualified v0.9 Multilane project fixture.

Test:

```text
legacy project
-> import
-> create new Analysis/Base Scenario representation
-> verify normalized inputs
-> verify method/input identity
-> retain stored result only if fingerprint compatibility verifies
-> recalculation equals qualified baseline
```

## 24. R2A Playwright journeys

Minimum:

1. Blank Metric Multilane -> valid calculation.
2. Estimated FFS -> measured FFS branch switch.
3. Divided median -> left clearance appears.
4. General terrain -> specific grade -> external PCE branches.
5. Missing required field -> Calculate blocked and focusable error.
6. Valid result -> edit -> stale -> recalculate.
7. Capacity-failure example -> correct result state, no fake speed/density.
8. Thai/English switch preserving calculation identity.
9. Legacy project import.
10. Export from current result only.

## 25. Gate R2A

Do not start Two-Lane Facility until:

- numerical outputs match baseline fixtures;
- Multilane API contract is stable enough for the prototype;
- all required Playwright journeys pass;
- visual review approves input/result hierarchy;
- capacity and stale states are unambiguous;
- no usability regression forces users to understand internal PCE mode terminology.

# R2B — Two-Lane Facility Representative Prototype

## 26. R2B objective

Prove the grid-heavy, multi-segment workflow and facility/segment result hierarchy.

## 27. R2B.1 — Facility application service

Migrate/wrap current `manual_facility.py` behavior.

Preserve:

- qualified Example 3/4-backed contexts;
- editable/locked field rules;
- canonical row normalization;
- segment validation;
- facility calculation;
- segment result mapping;
- audit record;
- facility aggregation semantics.

Do not imply arbitrary general Chapter 15 facility construction is now supported.

## 28. R2B.2 — Facility grid

Implement:

- stable row identity;
- editable vs locked cells;
- conditionally active opposing-volume cells;
- sticky header;
- local horizontal scroll;
- keyboard-efficient field editing;
- row/cell validation;
- error summary navigation;
- readable locked values.

Avoid a spreadsheet library if a focused accessible grid meets requirements. If it does not, select a dedicated grid library based on prototype evidence.

## 29. R2B.3 — Facility result

Implement:

### Facility answer

- facility LOS;
- facility follower density;
- facility average speed;
- facility percent followers;
- capacity-failure state;
- critical segment.

### Interpretation

- length weighting under Eq. 15-39;
- facility LOS based on final facility follower density;
- segment LOS letters are not averaged;
- critical segment meaning.

### Segment result table

- ID/name;
- type;
- average speed;
- percent followers;
- final follower density;
- LOS;
- warnings/context.

Selecting a segment opens segment evidence without losing facility context.

## 30. R2B project compatibility

Use qualified facility project fixtures from both current bounded contexts where available.

Verify:

- rows preserved;
- locked-context evidence preserved;
- normalized segment inputs match;
- facility/segment outputs match baseline;
- stale behavior works after row edit.

## 31. R2B Playwright journeys

Minimum:

1. Load level facility context -> calculate.
2. Load mountainous facility context -> calculate.
3. Edit valid allowed cell -> stale -> recalculate.
4. Invalid PHF cell -> row/cell + summary error.
5. Passing-zone missing opposing volume -> blocking error.
6. Locked context visibly read-only.
7. Facility result -> select segment evidence.
8. Capacity-failed segment -> facility warning/state.
9. Thai/English grid labels.
10. Narrow viewport local table scroll without whole-page overflow.

## 32. Gate R2B

R2B passes when:

- facility baseline results remain numerically equivalent;
- grid editing is practical in a real browser;
- locked context is understandable;
- facility answer is visually distinct from segment evidence;
- critical segment and capacity warnings are correct;
- browser/table accessibility is acceptable for the intended engineering workflow.

# R2C — Project / Scenario / Compare Prototype Closure

## 33. R2C objective

Prove the product object model with the two representative methods.

## 34. Project schema v2 draft

Introduce a new multi-analysis schema without modifying legacy files in place.

Conceptual shape:

```text
schema_version: "2.0"
project_id
project_name
created_at
updated_at
presentation_metadata

analyses[]
  analysis_id
  name
  method_id
  method_version
  input_contract

  scenarios[]
    scenario_id
    name
    displayed_inputs
    normalized_inputs
    calculation_fingerprint
    result
    presentation_state
    audit
    warnings
    assumptions
```

Exact serialization details must be specified/tested before release.

Legacy schema 1.2 import remains supported.

## 35. Scenario operations

Prototype:

- Base Scenario automatic;
- Duplicate Scenario;
- Rename Scenario;
- edit independently;
- current/stale state independent per scenario;
- no cross-scenario hidden recalculation.

## 36. Compare prototype

Initially compare scenarios within the same Analysis only.

Eligibility:

- same method;
- compatible method/input contract;
- current results.

Compare canonical metrics.

Do not calculate percentage improvement for LOS letters.

## 37. Project Overview

Implement basic work-list view:

- Analysis name;
- method;
- scenario count;
- result/status;
- stale/warning state;
- open action.

Avoid decorative KPI dashboards in the prototype.

## 38. Quick Analysis -> Project

Test:

```text
create Quick Multilane analysis
-> calculate
-> Save to Project
-> Analysis/Base Scenario appears in Project
-> fingerprint/result identity preserved
```

## 39. R2 end-to-end journeys

At least:

1. Create Project -> Multilane Analysis -> calculate.
2. Duplicate Base Scenario -> change geometry -> calculate.
3. Compare Existing vs Option A.
4. Add Two-Lane Facility to same Project.
5. Save Project v2 -> reopen -> results/current states preserved and verified.
6. Import legacy v0.9 single-analysis project -> save as new v2 project copy.
7. Quick Analysis -> Save to Project.
8. Stale scenario excluded/flagged in Compare.

# R2 Visual Reference Set

## 40. Required visual baselines

Capture at least:

```text
home-desktop
project-overview-desktop
new-analysis-desktop
multilane-input-desktop
multilane-result-desktop
multilane-capacity-failure-desktop
multilane-stale-desktop
facility-grid-desktop
facility-validation-desktop
facility-result-desktop
compare-desktop
narrow-analysis-shell
narrow-facility-grid
thai-multilane-input
thai-facility-result
```

Use stable deterministic fixture data.

# Engineering regression harness

## 41. Numerical equivalence rule

New frontend/API architecture must not change accepted numerical results.

For representative fixtures compare:

```text
legacy adapter -> engine result
new application service -> same engine result
API response engine payload -> same values
frontend display conversion -> expected units/format only
```

Differences require explicit classification:

- presentation-only;
- unit-format-only;
- known bug fix with engineering review;
- unintended regression.

## 42. Contract fixtures

Create durable JSON fixtures for:

- Multilane valid estimated FFS;
- Multilane measured FFS;
- Multilane capacity failure;
- Multilane invalid/scope cases;
- Facility level context;
- Facility mountainous context;
- Facility invalid row;
- legacy project import.

Fixtures should test application contracts, not only screenshots.

# Migration safety

## 43. Keep Streamlit runnable through R2

R1/R2 must not remove the current Streamlit entry path.

Use it for:

- behavioral comparison;
- regression investigation;
- fallback during prototype qualification.

Do not add new product features to Streamlit merely to keep both UIs at parity unless required for engineering correctness.

## 44. Refactor strategy for `manual_*`

Prefer incremental extraction:

```text
existing ui/manual_multilane.py
  -> application/multilane.py owns framework-independent behavior
  -> ui/manual_multilane.py temporarily re-exports/wraps application behavior
```

Repeat method-by-method after tests prove compatibility.

This avoids a destructive namespace migration before the new app is qualified.

# Codex implementation rules

## 45. Worktree/branch discipline

Implementation should occur on isolated branches/worktrees.

Suggested first branch:

```text
codex/application-rebuild-r1-foundation
```

Do not develop directly on `main`.

## 46. Commit discipline

Prefer reviewable slices:

```text
R1.1 application contracts
R1.2 registry
R1.3 API skeleton
R1.4 frontend shell
R1.5 design components
R1.6 tests/CI
```

Avoid one giant frontend/backend migration commit.

## 47. Stop conditions

Implementation should stop and report rather than improvise when:

- a proposed UI field cannot be mapped to the existing engine contract;
- a required result cannot be derived without a new engineering formula;
- legacy project identity cannot be verified;
- moving an adapter changes numerical behavior;
- a new dependency materially changes offline/distribution assumptions;
- current HCM scope conflicts with the R0 wireframe wording.

## 48. Review loop

Preferred implementation review cycle:

```text
ChatGPT/R0 spec
  -> Codex implementation
  -> push branch/PR
  -> GitHub review in ChatGPT
  -> Codex fixes specific findings only
  -> browser/CI qualification
  -> acceptance
```

# R0 completion gate

## 49. R0 is complete when

The planning set provides enough information to answer before coding:

- what product is being built;
- how Project/Analysis/Scenario work;
- how users navigate;
- how all seven existing methods should flow;
- how results are prioritized/interpreted;
- what key screens look like structurally;
- what visual/interaction system is used;
- which frontend/backend architecture is selected;
- how current engines/projects remain compatible;
- which two methods prove the architecture first;
- how browser/numerical/visual acceptance is measured;
- when implementation must stop rather than invent behavior.

With this document, the Application Rebuild R0 package is considered planning-complete subject to review/acceptance of the planning branch.

## 50. Recommended next repository actions

After review of the R0 branch:

1. Open a planning-only pull request from `planning/application-rebuild-r0` to `main`.
2. Create a new parent issue for `Application Rebuild — R1/R2` referencing the R0 documents.
3. Mark the existing Phase 17 release-hardening issue/plan as superseded by the accepted application rebuild direction, retaining history.
4. Merge the R0 documentation PR only after the architecture is accepted.
5. Start Codex on `R1 Application Foundation`, not on visual mass migration.
