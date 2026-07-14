# Basic Freeway Segment Implementation Plan

> Phase 7.1 corrected above-capacity behavior and supporting source audit are recorded in [the Phase 7.1 reference audit](methodology/phase_7_1_reference_audit.md).

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
`src/hcmcalc/freeway/`. A Manual Basic Freeway Segment Calculator v0.1 now
exposes that existing engine path in Streamlit for bounded one-direction,
one-segment uninterrupted-flow Basic Freeway Segment analysis within the
implemented Chapter 12 scope. BF-CH26-001 remains optional defaults and
regression evidence. Save/Load and export/reporting integration now exists
for that same bounded worksheet through `project_type =
manual_basic_freeway_v0`. This does not add ramps, weaving, merge/diverge,
managed lanes, work zones, reliability, or facility/corridor workflows.

BF-2 adds Chapter 26 Basic Freeway Segment validation fixtures for Example
Problem 1. The local Chapter 12 methodology reference provides the formulas and
tables used by the engine, while the local Chapter 26 example reference provides
the published example inputs and rounded expected outputs used for validation.
The PDF references remain local read-only sources and are not copied into the
repository.

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

Basic Freeway UI work should follow the current Two-Lane calculator UX:
calculator-first, engineering-data-entry oriented, and single-page. It should
not be designed as a template selector page or example viewer.

The user-facing workflow should be input-driven, not template-driven.
Validated presets may exist, but they should be optional starting values that
help users begin from a known reference case. The validation basis,
limitations, source notes, and unsupported-scope details should remain
available in audit/details/limitations sections without dominating the form.

Unsupported combinations must remain guarded. If a user selects or enters
conditions outside the implemented Basic Freeway scope, the UI and engine
should reject those conditions clearly instead of producing misleading outputs.

Implemented v0.1 page structure:

- Setup
- Roadway / Geometry
- Traffic
- Advanced / Optional
- compact Save/Load controls
- Results
- Calculation details / Audit
- Export / Report after successful results

Save / Load / Export remains calculator-scoped and does not convert the page
into an example-template viewer. Loading restores unit system, preset, displayed
inputs, engine-native inputs, and matching result context when present. Exports
format the existing calculated result in CSV, Excel `.xlsx`, Markdown, and
report JSON.

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
- `references/`: Basic Freeway Example Problem 1 validation fixtures for the
  selected Chapter 26 operational segment case.
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
- input summary for audit traceability;
- adjusted free-flow speed and capacity-related values;
- demand flow rate under the implemented methodology basis;
- speed, density, demand-capacity status, and level of service;
- assumptions, warnings, unsupported-scope notes, source references, and
  intermediate values;
- formula source references.

These outputs are displayed by the bounded Manual Basic Freeway Segment UI.
They are also available in bounded project files and reports. They do not imply
facility, ramp, weaving, merge/diverge, managed-lane, work-zone, reliability, or
facility/corridor support.

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

## Chapter 26 Basic Freeway Candidate Inventory

The supplied Chapter 26 freeway/multilane example reference was inspected for
Basic Freeway Segment candidates. The selected validation case is:

- **BF-CH26-001: Example Problem 1, Four-Lane Freeway LOS**. Selected for v0.1
  validation because it is a one-direction, one-segment, uninterrupted-flow
  Basic Freeway Segment operational analysis. It uses the implemented estimated
  FFS path, level-terrain general PCE, regular-user driver population, base
  SAF/CAF values, and publishes/checks adjusted FFS, capacity, demand flow
  rate, breakpoint, speed, density, and LOS.

Rejected or deferred candidates:

- **Example Problem 2, Number of Lanes Required for Target LOS**. Basic Freeway
  design analysis, but v0.1 is an operational engine and does not determine
  required lane count.
- **Example Problem 3, Six-Lane Freeway LOS and Capacity**. Basic Freeway
  operational/planning candidate with present/future conditions. Deferred
  because Example Problem 1 is simpler and sufficient for the first validation
  fixture.
- **Example Problem 4, LOS on a Five-Lane Highway with a Two-Way Left-Turn
  Lane**. Multilane Highway Segment, already separate from Basic Freeway.
- **Example Problem 5, Mixed-Flow Operational Performance**. Freeway mixed-flow
  analysis requiring branches outside Basic Freeway v0.1.
- **Example Problem 6, Severe Weather Effects on a Basic Freeway Segment**.
  Basic Freeway operational analysis with adverse-weather SAF/CAF inputs.
  Deferred because v0.1 validation starts with the base-condition operational
  case; weather effects are not a broader supported workflow.
- **Example Problem 7, Basic Managed Lane Segment**. Managed-lane analysis and
  out of scope for Basic Freeway Segment v0.1.

Basic Freeway Segment remains separate from Multilane Highway Segment. Passing
the BF-CH26-001 fixture does not imply support for Multilane Highway, ramps,
merge/diverge, weaving, managed lanes, work zones, reliability, adverse-weather
workflow, or freeway facility/corridor analysis.

### BF-2: Validation, Boundary, and Guardrail Hardening

- Added Chapter 26 Example Problem 1 fixtures:
  `references/freeway_example_inputs.yaml` and
  `references/freeway_expected_outputs.yaml`.
- Added validation tests with documented tolerances for demand flow rate,
  adjusted FFS, capacity, breakpoint, speed, density, and LOS.
- Added boundary tests for PHF = 1.0, zero heavy vehicles, minimum positive
  volume, LOS thresholds, capacity threshold behavior, non-finite values, and
  FFS range endpoints.
- Added guardrail tests for Multilane Highway, ramp, weaving, merge/diverge,
  managed lanes, work zones, reliability, facility/corridor, driver-population
  adjustment inputs, adjacent-methodology inputs, and arbitrary out-of-scope
  inputs.
- Hardened audit outputs with a normalized input summary, validation status,
  driver-population factor, Chapter 26 source reference, and computed speed and
  density sanity checks.
- Corrected the Basic Freeway adjusted breakpoint helper to use the Chapter 12
  `CAF^2` relationship.
- No UI, Save/Load, export/reporting, ramps, weaving, merge/diverge, managed
  lane, work-zone, reliability, or facility/corridor support was added.

### BF-3: Manual Basic Freeway UI v0.1

- Added a single-page Manual Basic Freeway Segment Calculator after the engine
  was stable and validated.
- Added a Streamlit Freeway mode without changing Two-Lane or Multilane modes.
- Followed the calculator-first structure: Setup, Roadway / Geometry, Traffic,
  Advanced / Optional, Results, Calculation details, Audit / intermediate
  values, and Full JSON.
- Added the Chapter 26 Example Problem 1 input preset as starting values from
  `references/freeway_example_inputs.yaml`.
- Kept the workflow input-driven rather than template-driven.
- Displayed validation basis and limitations in collapsed details areas.
- Added Metric/Imperial UI conversion at the UI boundary while keeping the
  engine-native Imperial calculation contract.
- Preserved engine guardrails for unsupported combinations.
- Added no Save/Load controls and no export/reporting buttons.
- Added no ramp, weaving, merge/diverge, managed-lane, work-zone,
  reliability, or facility/corridor support.
- Changed no Basic Freeway formulas or outputs.

### BF-4: Save/Load + Export Integration

- Added distinct Basic Freeway project type
  `manual_basic_freeway_v0` under the existing project schema version `1.0`.
- Persisted displayed inputs, normalized engine-native Imperial inputs, matching
  results, audit details, assumptions, warnings, limitations, and
  unsupported-scope notes.
- Added CSV, Excel `.xlsx`, Markdown, and report JSON exports using the shared
  reporting pattern.
- Placed Load Project near the input preset controls, Save Project below the
  worksheet inputs, and Export / Report after successful results so the
  calculator remains the primary workflow.
- Preserved Metric/Imperial UI-boundary conversion; calculations remain
  engine-native Imperial.
- Avoided changing existing Two-Lane and Multilane Save/Load or export behavior.
- Added no Basic Freeway formulas, coefficients, tables, ramps, weaving,
  merge/diverge, managed-lane, work-zone, reliability, or facility/corridor
  support.

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

Basic Freeway Segment v0.1 does not implement:

- ramps;
- weaving;
- merge/diverge;
- managed lanes;
- work zones;
- reliability;
- facility/corridor workflow;
- additional expected-output fixtures beyond BF-CH26-001; or
- changes to existing Two-Lane or Multilane behavior.

Save/Load and export/reporting are implemented only for the bounded Manual Basic
Freeway Segment v0.1 worksheet using `manual_basic_freeway_v0`; they do not add
broader freeway facility or adjacent-methodology scope.
