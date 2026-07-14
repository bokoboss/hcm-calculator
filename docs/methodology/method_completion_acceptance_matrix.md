# Method Completion Acceptance Matrix

Status: Phase 6 scope lock  
Sequence: Multilane completion first, Basic Freeway completion second

## 1. Milestone boundaries

| Milestone | Included | Excluded |
|---|---|---|
| Multilane Highway Method Completion | One-direction, one-segment uninterrupted-flow Multilane Highway analysis | Basic Freeway, ramps, weaving, merge/diverge, facility/corridor, managed lanes, work zones, reliability |
| Basic Freeway Method Completion | One-direction, one-segment uninterrupted-flow Basic Freeway Segment analysis | Ramp influence areas, weaving, merge/diverge, facility/corridor, managed lanes, work zones, reliability |
| Cross-method UX Hardening | Shared workflow, freshness, save/load, export/report parity, terminology and usability | New HCM methodologies, cloud collaboration, simulation, CAD functions |

## 2. Acceptance matrix

Legend: M = Multilane; F = Basic Freeway.

| ID | Acceptance requirement | M | F | Evidence required |
|---|---|:---:|:---:|---|
| AC-01 | Production calculations contain no validation-example identity dependency | Required | Required | Code review plus non-example tests |
| AC-02 | Canonical typed input model and normalized payload exist | Required | Required | Unit tests and serialized input snapshot |
| AC-03 | Physical invalidity is distinguished from unsupported methodology | Required | Required | Error-type and message tests |
| AC-04 | Measured and estimated FFS workflows are explicit and independently tested | Required | Required | Branch tests and UI tests |
| AC-05 | All declared FFS adjustment branches and interpolation boundaries are verified | Required | Required | Table/equation boundary tests |
| AC-06 | Heavy-vehicle PCE source, lookup path, and adjustment factor are auditable | Required | Required | Intermediate-value assertions |
| AC-07 | Declared terrain/grade/truck-mix domain is either implemented or rejected before calculation | Required | Required | Supported/unsupported matrix tests |
| AC-08 | Demand flow calculation includes all declared adjustment factors exactly once | Required | Required | Equation tests and result trace |
| AC-09 | Speed-flow branch is verified below breakpoint, at breakpoint, between breakpoint and capacity, and at capacity | Required | Required | Boundary and non-example tests |
| AC-10 | Above-capacity output is an explicit status and cannot imply an unverified oversaturated prediction | Required | Required | Warning/LOS/output contract tests |
| AC-11 | Density and LOS thresholds are deterministic at exact boundaries | Required | Required | Parametrized threshold tests |
| AC-12 | Sensitivity and monotonicity are checked where physically applicable | Required | Required | Property/parametrized tests |
| AC-13 | Calculation result contains input summary, intermediate values, assumptions, warnings, references, and scope notes | Required | Required | Result-schema tests |
| AC-14 | UI contains no independent formula implementation | Required | Required | Code review and UI integration tests |
| AC-15 | Changing a material input marks stored results stale and blocks export until recalculation | Required | Required | State/fingerprint tests |
| AC-16 | Save/load preserves method version, normalized inputs, result freshness, and supported warnings | Required | Required | Round-trip tests |
| AC-17 | UI, JSON, CSV/Excel/Markdown, and report outputs agree for key values | Required | Required | Cross-surface parity tests |
| AC-18 | Existing Two-Lane calculations remain unchanged except for verified shared-infrastructure defects | Required | Required | Full regression suite |
| AC-19 | Clean Python 3.12 installation and full test suite pass | Required | Required | Release qualification log |
| AC-20 | Streamlit starts and all visible modes complete a smoke calculation | Required | Required | Smoke-test log |
| AC-21 | User and methodology documentation state supported and unsupported domains without overclaiming | Required | Required | Documentation review |
| AC-22 | Release note records scope, limitations, test evidence, and migration impact | Required | Required | Release note |

## 3. Phase gates

### Phase 7 — Multilane calculation engine completion

Must satisfy AC-01 through AC-13 and AC-18 for Multilane before product labels may stop describing the method as v0.1.

### Phase 8 — Multilane product integration and release

Must satisfy AC-14 through AC-22 for Multilane. Target release: `v0.3`.

### Phase 9 — Basic Freeway calculation engine completion

Must satisfy AC-01 through AC-13 and AC-18 for Basic Freeway before product labels may stop describing the method as v0.1.

### Phase 10 — Basic Freeway product integration and release

Must satisfy AC-14 through AC-22 for Basic Freeway. Target release: `v0.4`.

### Phase 11 — Cross-method UX hardening

Requires both method-completion releases. Changes must not alter qualified calculation outputs unless accompanied by a verified defect report and regression tests. Target release: `v0.5`.

## 3. Phase 8 v0.3 evidence map

| ID | Evidence in this release |
|---|---|
| AC-14 | `manual_multilane.py` constructs normalized engine inputs only; `MultilaneHighwayLOSMethod` calculates; result, report, and export adapters consume the result object. |
| AC-15 | Measured/estimated mode normalization and `workflow_state` fingerprint tests prove active values go stale and inactive values do not; exports are rendered only for current calculations. |
| AC-16 | Project schema 1.1 persists the effective input fingerprint, method identifier, and method contract. Version 1.0 projects migrate inputs but do not reuse unchecked results. |
| AC-17 | Manual Multilane and Basic Freeway display adapters preserve `None` speed/density; report JSON, CSV, Excel, and Markdown originate from the same result dictionary. |
| AC-18 | Full-suite qualification includes the qualified Two-Lane segment and facility tests. |
| AC-19 | Release note records the Python 3.12 clean-environment full-suite command and result. |
| AC-20 | Release note records Streamlit launch and each visible workflow smoke result. |
| AC-21 | `supported_workflows.md`, the Multilane gap analysis, and the v0.3 release note state lane, PCE, driver-population, and above-capacity limits. |
| AC-22 | `docs/releases/v0_3_multilane_method_completion.md` records scope, migration, validation, and retained limitations. |

## 4. Required test classes

- Official/reference example regression.
- Independent non-example normal cases.
- Equation and lookup-table boundary cases.
- Interpolation cases.
- Invalid physical inputs.
- Explicit unsupported-domain inputs.
- Breakpoint, capacity, and LOS threshold cases.
- Sensitivity and monotonicity cases.
- Deterministic repeatability.
- Save/load and calculation-freshness round trips.
- Cross-surface export/report parity.
- Full repository regression and application smoke tests.

## 5. Change-control rule

Two-Lane Highway methods remain in maintenance mode. A change to a qualified Two-Lane calculation requires a reproducible defect, a documented engineering rationale, targeted regression tests, and confirmation that historical validation examples remain correct.
