# Multilane Highway Implementation Plan

## Purpose

HCM 7th Edition Multilane Highway analysis will be added as a separate
calculator family, not as an extension of the existing Chapter 15 Two-Lane
Highway calculator. It will have its own inputs, models, methodology
implementation, validation fixtures, guardrails, and future UI adapter while
continuing to use neutral shared contracts where appropriate.

This plan defines the scope and validation sequence before any Multilane
Highway formulas, tables, coefficients, or expected outputs are implemented.

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

### Candidate First Validation Example

Chapter 26 Example Problem 4 is the proposed first validation anchor because it
is the available example explicitly identified as a Multilane Highway
operational analysis. The example evaluates the two travel directions
separately. For an initial one-direction, one-segment engine contract, each
direction should be represented and validated as an independent case derived
from the same source example.

This candidate still requires a deliberate fixture-definition review before
implementation. Its grade, directional, and access-point conditions must not
be generalized beyond what the reference validates.

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

### Phase ML-1: Reference-Backed Basic Segment Engine

- Define typed one-direction, one-segment input and result contracts.
- Implement only the methodology required by the selected validation example.
- Expose assumptions, intermediate values, outputs, sources, and guardrail
  decisions as auditable data.
- Add formulas and lookup data only with traceable reference mappings.

### Phase ML-2: Validated Chapter 26 Example Problem

- Create reviewed input and expected-output fixtures for the selected example.
- Validate each supported directional segment independently.
- Document tolerances, rounding, provenance, and reviewer sign-off.
- Add regression fixtures before broadening the engine contract.

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

## Non-Goals

This planning PR does not:

- implement Multilane Highway formulas, HCM tables, coefficients, or expected
  outputs;
- add a Multilane Highway UI workflow;
- add Multilane Highway Save/Load support;
- add Multilane Highway export or reporting support;
- implement Basic Freeway, ramp, merge/diverge, weaving, managed-lane,
  reliability, or facility/corridor analysis; or
- change existing Chapter 15 Two-Lane Highway calculation or UI behavior.
