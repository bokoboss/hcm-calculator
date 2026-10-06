# AGENTS.md

## Project Direction

This repository is an auditable HCM calculator and the accepted Application
Rebuild R0 baseline is the authority for the target application architecture.
Treat engineering correctness, traceability, and validation as primary product
requirements.

The current normal application architecture is React + TypeScript + Vite -> FastAPI -> a
framework-independent Python application layer -> the existing qualified HCM
engines. Python remains the calculation authority. TypeScript must not
duplicate HCM formulas. The qualified Streamlit UI remains available as a compatibility path.

The accepted R0 authority is under `docs/application_rebuild/`, in this order:

1. `r0_architecture_acceptance_review.md`
2. `README.md`
3. `r0_prototype_implementation_plan.md`
4. `r0_technology_architecture.md`
5. remaining R0 specification documents

R0 and the application rebuild through Phase 3 / PR #141 are merged.
Chapter 18 engine, RHT application integration, Thailand/LHT semantic
qualification, LHT backend adapter, and production worksheet/Handbook are
accepted through PRs #175, #177, #180, #183 and #185. The LHT worksheet requires
a signalized downstream boundary; the immediate upstream boundary may be
signalized or non-signalized. Downstream unsignalized control types remain
deferred.

## Current Scope

- Python 3.12 package
- pytest test suite
- Calculation logic independent from UI
- Accepted workflows currently cover Two-Lane Segment, Two-Lane Facility,
  Multilane Segment, Basic Freeway Segment, Weaving Segment, Merge Segment,
  Diverge Segment, and the bounded Thailand/LHT Urban Street Segment.
  Eight production React workflows are accepted. Preserve
  their existing calculation contracts and validation evidence.
- React/FastAPI is the normal installed-use architecture; Streamlit remains
  the qualified compatibility UI.
- HCM RHT Urban Street Segment remains backend-qualified/reference-only,
  with no delivered/actionable React worksheet.
- The Chapter 18 LHT adapter uses HCM-reference coefficients and is not
  Thai-calibrated by default. Its accepted 15-minute scope has a signalized
  downstream boundary; the immediate upstream boundary may be non-signalized.
  Downstream unsignalized controls and internal intersection methods remain
  deferred. Project v2 schema remains `2.0`.

## Constraints

- Do not rewrite or change qualified HCM engine behavior unless methodology,
  validation fixtures, and acceptance criteria are explicitly defined.
- Do not treat the legacy single-page Streamlit worksheet as the target
  architecture. Follow the accepted Application Rebuild workflow and result
  contracts; preserve compatibility during migration.
- Keep method implementations facility-type aware so future HCM modules can be added without rewriting core contracts.
- Do not couple calculation modules to Streamlit or any UI framework.
- Preserve project schema compatibility and fingerprint-derived current/stale
  result semantics. Reports and exports must not silently rerun calculations.

## Quality Bar

- Every calculation method must expose auditable inputs, assumptions, intermediate values, and outputs.
- New or changed calculation behavior must be validated against HCM Chapter 26
  example problems or other explicitly accepted reference evidence before it
  is treated as qualified. Application-layer work must preserve existing engine
  outputs and validation evidence.
- Tests should grow from placeholder smoke tests into method-level unit tests, validation fixture tests, and regression tests.

## Development Commands

```powershell
python -m pip install -e .[dev]
pytest
```
