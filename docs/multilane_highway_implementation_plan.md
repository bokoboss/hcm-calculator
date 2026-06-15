# Multilane Highway Implementation Plan

## Purpose

HCM 7th Edition Multilane Highway analysis will be added as a separate
calculator family, not as an extension of the existing Chapter 15 Two-Lane
Highway calculator. It will have its own inputs, models, methodology
implementation, validation fixtures, guardrails, and future UI adapter while
continuing to use neutral shared contracts where appropriate.

This plan defines the scope and validation sequence for Multilane Highway
development. Phase ML-1 and the first Example Problem 4 validation path are
implemented as Multilane Basic Segment engine v0.1. Phase ML-2 hardens that
implemented-example-only path with validation, audit, table/equation boundary,
guardrail, fixture, and documentation coverage. It does not broaden the
calculation methodology.

A second-case review of the available Chapter 26 examples found no additional
Multilane Highway motorized-vehicle example or unused Example Problem 4 subcase
that can safely broaden the current validation evidence. The engine therefore
remains limited to Example Problem 4 EB/WB.

## Scope Separation

The initial calculator family must distinguish the following analysis types:

- **Multilane Highway Segment**: an uninterrupted-flow highway segment outside
  the influence of signalized intersections, ramps, merge/diverge areas, and
  weaving areas. This is the only analysis type targeted by v0.1.
- **Basic Freeway Segment**: covered by the shared Chapter 12 reference but
  operationally distinct from a Multilane Highway Segment. It is outside the
  v0.1 scope.
- **Ramp / merge / diverge**: separate influence-area methodologies and outside
  the v0.1 scope.
- **Weaving**: a separate methodology and outside the v0.1 scope.
- **Managed lanes**: a separate Chapter 12 extension and outside the v0.1 scope.
- **Facility/corridor workflow**: a multi-segment or system-level workflow,
  including broader freeway-facility interactions, and outside the v0.1 scope.

The Chapter 12 reference presents a shared motorized vehicle core methodology
for Basic Freeway and Multilane Highway Segments beginning in Section 3. Within
that shared sequence, facility-type-specific inputs and adjustments must remain
explicit. Multilane Highway v0.1 must not accidentally expose Basic Freeway
Segment behavior or imply support for adjacent facility methodologies.

## Available References

The following read-only local references were inventoried for planning. They
must remain under `local_references/` and must not be copied into the
repository.

| Filename | Brief purpose |
| --- | --- |
| `HCM7 CH12 Basic Freeway and Mulilane Highway Segments.pdf` | Primary methodology-scope reference. It identifies the shared Chapter 12 motorized vehicle core methodology, the Multilane-specific portions of that methodology, and separate Basic Freeway and managed-lane concerns. |
| `HCM7 CH26 Multilane HW EX Problems.pdf` | Validation-example inventory. It lists the available Freeway and Multilane Highway examples and identifies Example Problem 4, "LOS on a five-lane highway with a two-way left-turn lane," as the explicit Multilane Highway example. |

No HCM tables, equations, coefficients, or expected numerical outputs are
reproduced in this plan.

### Validated Example Problem 4 Cases

Chapter 26 Example Problem 4 is the validation anchor because it
is the available example explicitly identified as a Multilane Highway
operational analysis. The example evaluates the two travel directions
separately. For an initial one-direction, one-segment engine contract, each
direction should be represented and validated as an independent case derived
from the same source example.

The two directions are implemented as independent cases:

- `MLH-CH26-004-EB`: 3.5% downgrade, 10 access points/mi;
- `MLH-CH26-004-WB`: 3.5% upgrade, 0 access points/mi.

Both cases remain locked to the published example inputs. Their grade,
directional, access-point, lane, median, truck, and demand conditions must not
be generalized beyond what the reference validates.

Valid equation or table boundaries tested during ML-2, such as PHF 1.0, zero
heavy vehicles, and LOS density thresholds, are helper-level verification only.
They do not authorize arbitrary full-engine input combinations.

### Second Validation Case Review

No safe second validation case was added. The Chapter 26 example inventory was
reviewed against the requirement for a one-direction, one-segment,
uninterrupted-flow Multilane Highway motorized-vehicle case close to the
implemented v0.1 path and with published density and LOS results.

| Chapter 26 candidate | Classification | Decision |
| --- | --- | --- |
| Example Problem 1 | Basic Freeway Segment operational analysis | Rejected: Basic Freeway methodology is outside scope. |
| Example Problem 2 | Basic Freeway Segment design analysis | Rejected: Basic Freeway methodology and lane-design workflow are outside scope. |
| Example Problem 3 | Basic Freeway Segment operational and planning analysis | Rejected: Basic Freeway methodology and planning workflow are outside scope. |
| Example Problem 4 EB/WB | Multilane Highway Segment operational analysis | Already validated as `MLH-CH26-004-EB` and `MLH-CH26-004-WB`; no additional direction or subcase is published. |
| Example Problem 5 | Mixed-flow freeway operational analysis | Rejected: freeway and mixed-flow methodology are outside scope. |
| Example Problem 6 | Basic Freeway Segment with severe-weather adjustments | Rejected: Basic Freeway and adverse-weather adjustment methodology are outside scope. |
| Example Problem 7 | Basic managed lane segment operational analysis | Rejected: managed-lane methodology is outside scope. |

The review used the Chapter 26 example inventory and Example Problem 4 result
pages, together with the Chapter 12 scope distinctions between Multilane
Highway, Basic Freeway, and managed-lane methods. No formula/table branch,
fixture, expected output, or engine guardrail was changed because none can be
validated by an additional compatible example in the available reference.

## Implemented v0.1 Methodology

The engine implements only the Chapter 12 path exercised by Chapter 26
Multilane Highway Example Problem 4:

- Equation 12-3 and Exhibits 12-20, 12-22, 12-23, and 12-24 for Multilane
  Highway FFS;
- Equation 12-4 for total lateral clearance;
- Equation 12-7 for Multilane Highway capacity;
- Equation 12-9 and Equation 12-10 with the two required Exhibit 12-26 PCEs;
- Equation 12-1's flow-below-breakpoint branch;
- Equation 12-11 for density; and
- Exhibit 12-15 for LOS.

Published Example Problem 4 validation targets are:

| Direction | FFS (mi/h) | Capacity (pc/h/ln) | PCE | fHV | Flow (pc/h/ln) | Density (pc/mi/ln) | LOS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Eastbound | 49.5 | 1,990 | 2.24 | 0.93 | 896 | 18.1 | C |
| Westbound | 52.0 | 2,040 | 3.97 | 0.85 | 980 | 18.8 | C |

## Proposed Module Structure

The implementation should keep the Multilane family independent from
`hcmcalc.two_lane` and from Streamlit:

```text
src/hcmcalc/multilane/
  __init__.py
  method.py
  models.py
  coefficients.py
  validation.py

tests/unit/
  test_multilane_method.py
  test_multilane_models.py
  test_multilane_coefficients.py
  test_multilane_validation.py

tests/integration/
  test_multilane_example_fixtures.py

references/
  multilane_example_inputs.yaml
  multilane_expected_outputs.yaml
```

Responsibilities should remain explicit:

- `models.py`: typed, serializable inputs and auditable result structures.
- `method.py`: calculation orchestration and intermediate-value assembly.
- `coefficients.py`: reference-backed table and coefficient access, added only
  when validation evidence is ready.
- `validation.py`: fixture loading, comparison, tolerances, and provenance.
- `tests/`: formula, boundary, guardrail, fixture, and regression coverage.
- `references/`: reviewed input mappings and expected outputs, added only after
  they are defined and independently checked.

## Initial Supported Scope Proposal

Multilane Basic Segment v0.1 should be intentionally limited to:

- one direction;
- one segment;
- uninterrupted flow;
- no ramps;
- no weaving;
- no merge/diverge;
- no managed lanes;
- no work zones;
- no reliability analysis;
- no corridor or facility workflow; and
- input fields limited to those required by the selected Chapter 26 example
  problem.

The v0.1 contract should be reference-backed and example-scoped. It should not
claim general Multilane Highway coverage merely because a helper, equation, or
lookup has been implemented.

## Guardrails

Unsupported conditions must be rejected clearly before calculation rather than
producing misleading outputs. Guardrail errors should identify the unsupported
condition, the currently supported boundary, and the validation basis for that
boundary.

The engine must keep facility type explicit and reject attempts to route Basic
Freeway, ramp, merge/diverge, weaving, managed-lane, work-zone, reliability, or
facility/corridor analyses through the Multilane Highway v0.1 method.

## Implementation Phases

### Phase ML-0: Scope + Reference Inventory + Architecture

- Define facility-family boundaries and non-goals.
- Inventory the available Chapter 12 methodology and Chapter 26 examples.
- Propose module, fixture, validation, and guardrail structure.
- Add no formulas, coefficient values, or working UI behavior.

### Phase ML-1: Reference-Backed Basic Segment Engine - Implemented v0.1

- Define typed one-direction, one-segment input and result contracts.
- Implement only the methodology required by the selected validation example.
- Expose assumptions, intermediate values, outputs, sources, and guardrail
  decisions as auditable data.
- Add formulas and lookup data only with traceable reference mappings.

### Phase ML-2: Example Problem 4 Engine Hardening - Implemented

- Create reviewed input and expected-output fixtures for the selected example.
- Validate each supported directional segment independently.
- Document tolerances, rounding, provenance, and reviewer sign-off.
- Add regression fixtures before broadening the engine contract.
- Reject missing, non-finite, physically invalid, and unsupported-scope inputs
  with clear errors.
- Verify implemented table/equation boundaries without exposing unvalidated
  general Multilane cases.
- Expose calculation type, support/scope status, capacity check, density speed,
  source references, warnings, assumptions, and unsupported-scope notes.

### Phase ML-2A: Second Validation Case Review - Completed, No Case Added

- Inventory the remaining Chapter 26 examples against the current Multilane
  Highway basic segment scope.
- Record why each non-Example-4 candidate is outside scope.
- Preserve Example Problem 4 EB/WB fixtures, outputs, guardrails, and engine
  behavior because no compatible additional validation case is available.

### Phase ML-3: Manual Streamlit UI

- Add a single-page guided worksheet only after the engine is stable.
- Keep UI normalization and display concerns outside calculation modules.
- Expose only validated inputs and reject unsupported conditions clearly.

### Phase ML-4: Save/Load + Export Integration

- Add a distinct Multilane project type and schema.
- Integrate reporting without changing calculation behavior.
- Preserve inputs, assumptions, intermediates, outputs, warnings, and
  validation provenance.

### Phase ML-5: Broader HCM Features Only After Validated References Exist

- Consider broader Multilane conditions, additional examples, and workflows
  only after methodology mappings and independent validation fixtures exist.
- Treat Basic Freeway, ramps, merge/diverge, weaving, managed lanes,
  reliability, and facility/corridor workflows as separately scoped work.

## Testing Strategy

Testing should grow with the implementation phases:

- formula-level unit tests for each implemented calculation step;
- table lookup boundary tests, including exact boundaries and rejection outside
  supported ranges;
- invalid input and unsupported-condition tests;
- validated Chapter 26 example tests with documented tolerances;
- regression tests ensuring existing `two_lane` behavior remains unchanged; and
- UI tests only after the Multilane engine is stable and validated.

Tests must distinguish exact example validation from general methodology
coverage. Passing a selected Chapter 26 example does not authorize unsupported
inputs or workflows.

## Current Non-Goals

Multilane Basic Segment v0.1 does not:

- implement a general Multilane Highway calculator beyond Example Problem 4;
- add a Multilane Highway UI workflow;
- add Multilane Highway Save/Load support;
- add Multilane Highway export or reporting support;
- accept user-supplied base/adjusted free-flow speed or driver-population
  adjustment inputs;
- implement Basic Freeway, ramp, merge/diverge, weaving, managed-lane,
  reliability, or facility/corridor analysis; or
- change existing Chapter 15 Two-Lane Highway calculation or UI behavior.
