# Basic Freeway Segment Implementation Plan

## Purpose

HCM 7th Edition Chapter 12 Basic Freeway Segment support should be added as a
separate calculator family. It must not be implemented as part of the
Multilane Highway Segment family, and it must not be presented as a general
freeway facility calculator.

The v0.1 engine is a reference-backed, auditable Basic Freeway Segment
calculator for one uninterrupted-flow segment in one direction. It reuses
neutral project patterns where they fit, such as typed inputs, auditable
intermediate values, guardrail errors, and UI adapter separation. It must not
share facility-specific formulas, coefficients, or
validation assumptions with Multilane Highway code merely because Chapter 12
presents a common motorized vehicle core methodology.

This document began as the planning artifact for PR #59. Basic Freeway Segment
engine v0.1 is now implemented as an engine-only package under
`src/hcmcalc/freeway/`. It does not implement UI, Save/Load, export behavior,
ramps, weaving, merge/diverge, managed lanes, work zones, reliability, or
facility/corridor workflows.

No Chapter 26 Basic Freeway validation fixture files are added yet. The local
Chapter 12 methodology reference provides the formulas and tables needed for
formula-level implementation, but this repository does not currently contain a
published Chapter 26 Basic Freeway example with complete mapped expected
outputs suitable for `references/freeway_example_inputs.yaml` and
`references/freeway_expected_outputs.yaml`.

## Scope Separation

Chapter 12 covers Basic Freeway and Multilane Highway Segments, but the
calculator should keep the facility families explicit:

- **Basic Freeway Segment**: uninterrupted-flow freeway segment methodology.
  This is the only facility family targeted by Basic Freeway v0.1.
- **Multilane Highway Segment**: a separate Chapter 12 calculator family with
  its own facility-specific inputs, adjustments, validation fixtures, UI, and
  project type. Basic Freeway work must not be mixed into the existing
  Multilane package or workflow.
- **Ramps / merge / diverge**: separate influence-area methodologies and out of
  scope for Basic Freeway v0.1.
- **Weaving**: a separate methodology and out of scope for Basic Freeway v0.1.
- **Managed lanes**: a separate Chapter 12 extension and out of scope for Basic
  Freeway v0.1.
- **Work zones**: out of scope for Basic Freeway v0.1.
- **Reliability**: out of scope for Basic Freeway v0.1.
- **Facility/corridor workflow**: multi-segment freeway facility or corridor
  analysis is out of scope for Basic Freeway v0.1.

Basic Freeway v0.1 targets Basic Freeway Segment only. It must not imply
support for ramps, merge/diverge, weaving, managed lanes, work zones,
reliability analysis, or facility/corridor workflows.

## Product/UI Direction

Future Basic Freeway UI work should follow the current Two-Lane calculator UX:
calculator-first, engineering-data-entry oriented, and single-page. It should
not be designed as a template selector page or example viewer.

The future user-facing workflow should be input-driven, not template-driven.
Validated presets may exist, but they should be optional starting values that
help users begin from a known reference case. The validation basis,
limitations, source notes, and unsupported-scope details should remain
available in audit/details/limitations sections without dominating the form.

Unsupported combinations must remain guarded. If a user selects or enters
conditions outside the implemented Basic Freeway scope, the UI and engine
should reject those conditions clearly instead of producing misleading outputs.

Recommended future page structure:

- Setup
- Roadway / Geometry
- Traffic
- Advanced / Optional
- Results
- Calculation details / Audit
- Save / Load / Export

Recommended wording for optional examples:

- Input preset
- Starting values
- Validated example preset

Avoid wording or interaction patterns that make the page feel like:

- Select template and view example
- Example viewer
- Template-only workflow

## Module Structure

Basic Freeway has its own package. Validation assets should be added when a
published Basic Freeway example mapping is available:

```text
src/hcmcalc/freeway/
  __init__.py
  models.py
  method.py
  validation.py
  coefficients.py

references/
  freeway_example_inputs.yaml
  freeway_expected_outputs.yaml

tests/unit/
  test_freeway_models.py
  test_freeway_method.py
  test_freeway_validation.py
  test_freeway_coefficients.py

tests/integration/
  test_freeway_example_fixtures.py
```

Implemented responsibilities:

- `models.py`: typed Basic Freeway input contract.
- `method.py`: Basic Freeway calculation orchestration and intermediate-value
  assembly.
- `validation.py`: physical input validation and unsupported-scope guardrails.
- `coefficients.py`: reference-backed Chapter 12 constants used by Basic
  Freeway v0.1.
- `references/`: no Basic Freeway fixtures yet because no complete published
  Chapter 26 Basic Freeway expected-output mapping is available in this repo.
- `tests/`: formula, boundary, invalid input, guardrail, and audit coverage.

The current Multilane code may inform neutral helper patterns, such as explicit
facility type fields, dataclass-style input contracts, auditable outputs, and
clear unsupported-scope exceptions. Basic Freeway should not depend on
Multilane method code or reuse Multilane-specific formulas, tables, or
coefficients.

## Supported Scope

Basic Freeway v0.1 supports:

- Basic Freeway Segment only
- one direction
- one segment
- uninterrupted flow
- no ramps
- no weaving
- no merge/diverge
- no managed lanes
- no work zones
- no reliability analysis
- no facility workflow
- Chapter 12 measured FFS or estimated FFS paths for Basic Freeway Segments
- Chapter 12 general-terrain heavy-vehicle PCEs for level and rolling terrain

The engine contract should be validation-led. Inputs, assumptions,
intermediate values, and outputs are traceable to the selected Basic Freeway
methodology path. Published Chapter 26 fixture validation remains pending.

Implemented input groups:

- analysis setup and facility type;
- directional lane count and segment length;
- measured FFS or estimated FFS basis;
- lane width, right-side lateral clearance, and total ramp density for the
  estimated FFS path;
- demand volume, peak-hour factor, heavy-vehicle percentage, and default truck
  mix; and
- level/rolling general terrain plus speed and capacity adjustment factors.

Implemented outputs:

- support and scope status;
- adjusted free-flow speed and capacity-related values;
- demand flow rate under the implemented methodology basis;
- speed, density, demand-capacity status, and level of service;
- assumptions, warnings, unsupported-scope notes, source references, and
  intermediate values;
- formula source references.

These outputs are engine-only. They do not imply UI, Save/Load, export,
facility, ramp, weaving, or managed-lane support.

## Guardrails

Unsupported conditions must reject clearly before calculation. Guardrail errors
should identify:

- the unsupported condition;
- the currently supported Basic Freeway v0.1 boundary;
- the validation basis for that boundary; and
- the likely future calculator family when the requested condition belongs
  elsewhere.

The Basic Freeway family must reject attempts to route Multilane Highway,
ramps, merge/diverge, weaving, managed lanes, work zones, reliability, or
facility/corridor analyses through the Basic Freeway Segment method.

## Implementation Phases

### BF-0: Scope + Architecture

- Define Basic Freeway Segment boundaries and non-goals.
- Record product/UI direction for a future calculator-first worksheet.
- Propose package, fixture, validation, and guardrail structure.
- Add no formulas, tables, coefficients, expected outputs, UI behavior,
  Save/Load behavior, or exports.

### BF-1: Reference-Backed Basic Freeway Segment Engine

- Implemented typed one-direction, one-segment input and result contracts.
- Implemented Chapter 12 Basic Freeway Segment formula helpers and lookup
  constants for Eq. 12-1, Eq. 12-2, Eq. 12-5, Eq. 12-6, Eq. 12-8,
  Eq. 12-9, Eq. 12-10, Eq. 12-11, and Exhibits 12-4, 12-6, 12-15,
  12-18, 12-20, 12-21, and 12-25.
- Exposes auditable inputs, assumptions, intermediate values, outputs, warnings,
  source references, and unsupported-scope notes.
- Does not add Chapter 26 validation fixtures because no complete Basic
  Freeway example expected-output mapping is available in this repo yet.

### BF-2: Validation, Boundary, and Guardrail Hardening

- Add formula-level unit tests for implemented steps.
- Add table lookup and boundary tests for implemented reference ranges.
- Add invalid input and unsupported-condition tests.
- Add validated HCM example tests with documented tolerances.
- Add regression checks ensuring Two-Lane and Multilane behavior remain
  unchanged.
- Harden errors so unsupported Basic Freeway, adjacent freeway, or facility
  cases fail clearly.

### BF-3: Manual Basic Freeway UI v0.1

- Add a single-page Manual Basic Freeway Segment Calculator only after the
  engine is stable and validated.
- Follow the Two-Lane calculator structure: Setup, Roadway / Geometry, Traffic,
  Advanced / Optional, Results, Calculation details / Audit, and Save / Load /
  Export.
- Treat validated example presets as optional starting values.
- Keep the workflow input-driven rather than template-driven.
- Display validation basis and limitations in audit/details/limitations areas.
- Preserve engine guardrails for unsupported combinations.

### BF-4: Save/Load + Export Integration

- Add a distinct Basic Freeway project type after UI and engine contracts are
  stable.
- Persist displayed inputs, normalized engine inputs, results, audit details,
  assumptions, warnings, limitations, and unsupported-scope notes.
- Add CSV, Excel, Markdown, and report JSON exports using the shared reporting
  pattern.
- Avoid changing existing Two-Lane and Multilane Save/Load or export behavior.

### BF-5: Broader Freeway Features Only After Validated References Exist

- Consider broader freeway features only after methodology mappings and
  independent validation fixtures exist.
- Treat ramps, merge/diverge, weaving, managed lanes, work zones, reliability,
  and facility/corridor workflows as separate future work.

## Testing Strategy

Testing should grow with the implementation phases:

- formula-level unit tests for each implemented calculation step;
- table lookup and boundary tests, including exact boundaries and rejection
  outside supported ranges;
- invalid input tests for missing, non-finite, physically invalid, and
  unsupported-scope values;
- validated HCM example tests with documented input mappings, expected outputs,
  tolerances, and provenance;
- regression tests ensuring Two-Lane and Multilane behavior remain unchanged;
  and
- UI tests only after the Basic Freeway engine is stable and validated.

Passing a selected validation example must not be treated as authorization for
general Basic Freeway, freeway facility, or adjacent-methodology support.

## Non-Goals

Basic Freeway Segment engine v0.1 does not implement:

- UI workflow;
- Save/Load;
- export/reporting;
- ramps;
- weaving;
- merge/diverge;
- managed lanes;
- work zones;
- reliability;
- facility/corridor workflow;
- expected-output fixtures; or
- changes to existing Two-Lane or Multilane behavior.
