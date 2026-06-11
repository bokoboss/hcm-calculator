# Chapter 15 Vertical Fixture Inventory

## A. Purpose

This document inventories the validation data currently available for future
Chapter 15 vertical-class and grade-length expansion. It separates standalone
manual evidence from facility-context evidence, records which expected outputs
exist, and identifies the verified fixtures and methodology data still needed.

This Phase 4 inventory adds no methodology support. It does not add formulas,
table values, coefficients, calculation paths, or authorization to broaden the
current supported scope.

### Phase 4B data and fixture preparation

Phase 4B adds non-runtime data and fixture manifests, a future-fixture
template, a structural validation helper, and
[vertical data ingestion guidelines](ch15_vertical_data_ingestion_guidelines.md).
No actual HCM values or coefficients are populated, and no runtime support is
enabled. Future verified data must include source attribution, expected
outputs, tolerances, and explicit validation status. Placeholder data must not
be used for calculation.

## B. Existing Validated Fixtures

In the table below, a grade length shown as the segment length means the source
fixture does not carry a separate `grade_length_mi`; the current validated
engine path treats the full segment length as the grade length. "Facility-only"
means the published expected outputs validate the path in its exact facility
context, not as an independent manual single segment.

| Fixture ID / test name | Source example | Calculation type | Terrain type | Segment type | Horizontal alignment | Grade percent | Grade length | Vertical class | Heavy vehicle percent | Expected outputs available | Current status | Notes |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `TLH-CH15-001`; `test_example_problem_1_matches_hcm_chapter_26_expected_values` | Chapter 26 Example Problem 1 | Single segment / CLI | Level | Passing Constrained | Straight | `0%` | `0.75 mi` segment length | 1 | `5%` | Demand, capacity, class, free-flow-speed components, average-speed components, percent-followers components, follower density, LOS | Supported | Exact standalone Chapter 26 manual path. |
| `TLH-CH15-002`; `test_example_problem_2_matches_hcm_chapter_26_expected_values` | Chapter 26 Example Problem 2 | Single segment | Level | Passing Constrained | 11 tangent/curve subsegments | `0%` | `0.75 mi` segment length | 1 | `5%` | Tangent speeds, curve-subsegment speeds and coefficients, adjusted average speed | Supported | Exact standalone manual horizontal-curve path; fixture does not publish final percent followers, follower density, or LOS. |
| `TLH-CH15-003`; `test_example_problem_3_matches_hcm_chapter_26_expected_values` | Chapter 26 Example Problem 3 | Facility / CLI | Level | Passing Constrained, Passing Lane, Passing Zone | Straight | `0%` | Segment lengths `0.5-1.75 mi` | 1 | `7.5%` or `8%` | Per-segment demand, capacity, free-flow speed, average speed, percent followers, density, LOS; Passing Lane lane-level outputs; facility density and LOS | Facility-only | Validates the exact five-segment workflow, Passing Lane, Passing Zone, and downstream adjustments in facility context. |
| `TLH-CH15-004` segment 1; Example Problem 4 fixture/integration tests | Chapter 26 Example Problem 4 | Facility | Mountainous | Passing Constrained | Horizontal curves | `4%` | `1.3 mi` segment length | 4 | `8%` | Segment class, demand, capacity, free-flow speed, average speed, percent followers, follower density, LOS | Facility-only | Shares its grade/length metadata with segment 4; no straight standalone fixture. |
| `TLH-CH15-004` segment 2; Example Problem 4 fixture/integration tests | Chapter 26 Example Problem 4 | Facility | Mountainous | Passing Constrained | Horizontal curves | `6%` | `1.0 mi` segment length | 5 | `8%` | Segment class, demand, capacity, free-flow speed, average speed, percent followers, follower density, LOS | Facility-only | No straight standalone fixture. |
| `TLH-CH15-004` segment 3; `test_manual_mountainous_supported_grade_length_returns_result` | Chapter 26 Example Problem 4 | Facility and manual single segment | Mountainous | Passing Constrained | Straight | `6%` | `0.5 mi` segment length | 4 | `8%` | Segment class, demand, capacity, free-flow speed, average speed, percent followers, follower density, LOS; manual audit provenance | Supported | Only independently validated nonlevel manual single-segment path. |
| `TLH-CH15-004` segment 4; Example Problem 4 fixture/integration tests | Chapter 26 Example Problem 4 | Facility | Mountainous | Passing Constrained | Horizontal curves | `4%` | `1.3 mi` segment length | 4 | `8%` | Segment class, demand, capacity, free-flow speed, average speed, percent followers, follower density, LOS | Facility-only | Curve-combined output differs from segment 1; no straight standalone fixture. |
| `TLH-CH15-004` segment 5; Example Problem 4 fixture/integration tests | Chapter 26 Example Problem 4 | Facility | Mountainous | Passing Lane | Straight | `-3%` | `0.5 mi` segment length | 1 | `8%` | Segment class, demand, capacity, free-flow speed, average speed, percent followers, midpoint follower density, LOS; downstream effective length is tested | Facility-only | Standalone Passing Lane and downstream effects are not independently validated. |
| `TLH-CH15-004` segment 6; Example Problem 4 fixture/integration tests | Chapter 26 Example Problem 4 | Facility | Mountainous | Passing Constrained | Straight | `-3%` | `0.5 mi` segment length | 1 | `8%` | Segment class, demand, capacity, free-flow speed, average speed, percent followers, adjusted follower density, LOS; downstream improvement values are tested | Facility-only | Published final density includes an upstream Passing Lane adjustment. |
| `test_vertical_lookup.py` lookup cases | Repository metadata derived from Example Problem 4 | QA | Mountainous | Passing Constrained / Passing Lane | As limited above | Exact mapped pairs only | Exact mapped lengths only | 1, 4, 5 | `8%` | Lookup status, class, source, validation basis, manual/facility-only marker | Guarded | Metadata only; contains no HCM table values or coefficients. |
| `test_vertical_scope_guardrails.py` scope cases | Repository scope contract | QA | Level / mountainous | Passing Constrained / Passing Zone / Passing Lane | Straight / curves | Supported and adjacent unsupported cases | Full segment only; missing/mismatched cases tested | Derived or submitted | Primarily `8%` for nonlevel | Scope status/reason, derived class where known, failed-audit context with no outputs | Guarded | Confirms unsupported combinations fail before formulas run. |
| `test_run_example_4_returns_expected_facility_results`; `test_unsupported_vertical_scope_returns_clear_cli_error` | Example Problem 4 and repository scope contract | CLI / QA | Mountainous | Facility / Passing Constrained | Mixed / straight | Fixture and unsupported case | Fixture or unsupported length | Fixture classes | `8%` | Facility LOS/density or clear CLI error | Facility-only / guarded | Confirms CLI behavior; does not create a new calculation path. |

The canonical inputs and published expected targets are
`references/example_inputs.yaml` and `references/expected_outputs.yaml`.
`references/VALIDATION_MATRIX.md` records their implemented-example-only
status. The unit tests additionally check formula-level intermediates, lookup
metadata, scope decisions, audit behavior, and CLI behavior.

## C. Existing Validated Manual Single-Segment Paths

Only these exact Chapter 26 paths have standalone expected-output evidence that
is safe for manual single-segment use:

| Path | Validation basis | Limitations |
| --- | --- | --- |
| Level, straight Passing Constrained, `0% / 0.75 mi`, Class 1, `5%` heavy vehicles | `TLH-CH15-001` | Exact Example Problem 1 inputs and outputs. |
| Level Passing Constrained with the exact Example Problem 2 curve structure, `0% / 0.75 mi`, Class 1, `5%` heavy vehicles | `TLH-CH15-002` | Expected outputs cover curve/tangent and adjusted average speeds, not final density or LOS. |
| Mountainous, straight Passing Constrained, `6% / 0.5 mi`, Class 4, `8%` heavy vehicles | `TLH-CH15-004` segment 3 and manual-path tests | Only validated nonlevel manual path; grade length must equal segment length. |

The level reliability matrix tests broader currently supported manual behavior,
including level Passing Zone and Passing Lane cases. Those regression tests
improve confidence in the implementation but are not additional published
Chapter 26 standalone validation fixtures.

## D. Facility-Only Validated Paths

- `TLH-CH15-003` validates the exact level five-segment facility workflow.
  Its Passing Zone, Passing Lane, and downstream-adjusted segments should not be
  treated as independent Chapter 26 single-segment fixtures.
- `TLH-CH15-004` segments 1 and 4 validate Class 4 `4% / 1.3 mi` Passing
  Constrained segments only with their exact horizontal-curve structures.
- `TLH-CH15-004` segment 2 validates the Class 5 `6% / 1.0 mi` Passing
  Constrained segment only with its exact horizontal-curve structure.
- `TLH-CH15-004` segment 5 validates a Class 1 `-3% / 0.5 mi` Passing Lane
  within the facility and its downstream-effect workflow.
- `TLH-CH15-004` segment 6 validates a Class 1 `-3% / 0.5 mi` Passing
  Constrained final result that includes upstream Passing Lane adjustment.

These paths must not be promoted to manual single-segment support without an
independent expected-output fixture that isolates the intended calculation.

## E. Unsupported but Important Future Paths

- Additional vertical classes and complete applicability coverage for each
  supported class.
- Other upgrade and downgrade grade percentages.
- Other grade lengths, including values near classification boundaries.
- Heavy-vehicle percentages other than exactly `8%` on nonlevel segments.
- Nonlevel Passing Zone segments with verified opposing-flow treatment.
- Nonlevel Passing Lane segments, including class-specific capacity and
  lane-level behavior.
- Horizontal-curve plus nonlevel combinations outside the exact facility
  examples.
- Grades whose length differs from the segment length, vertical profiles with
  grade transitions, and multiple grades within one segment.
- Facility-level workflows outside the exact Example Problems 3 and 4 segment
  sequences.
- Metric inputs that normalize to verified values at grade-length boundaries.

## F. Required Validation Fixtures

Every new fixture must identify its source, inputs, units, expected outputs,
tolerances, rounding convention, calculation context, and reviewer/checker.

| Future path category | Required fixture evidence before support |
| --- | --- |
| One additional straight Passing Constrained vertical path | Expected vertical class, demand flow and capacity where applicable, free-flow speed, average speed, percent followers, follower density, LOS, material intermediates, and supported audit/scope result. |
| Additional grade percentages, lengths, and vertical classes | Boundary-focused fixtures immediately below, at, and above each claimed classification boundary; expected class plus complete segment outputs and clear unsupported behavior outside the claimed range. |
| Non-`8%` heavy vehicles | At least one independently checked case per claimed class/path/percentage range with expected heavy-vehicle adjustment, demand/capacity where applicable, average speed, percent followers, follower density, LOS, and audit provenance. |
| Nonlevel Passing Zone | Standalone expected segment outputs including opposing demand flow, demand/capacity, speed, percent followers, follower density, LOS, and explicit scope/audit behavior. |
| Nonlevel Passing Lane | Standalone and facility-context fixtures with class-specific capacity, lane allocation, lane heavy-vehicle percentages, lane speeds, lane percent followers, midpoint/endpoint density basis, LOS, downstream effective length where applicable, and audit behavior. |
| Horizontal curve plus nonlevel | Expected tangent and curve-subsegment values, length-weighted segment average speed, final segment percent followers, follower density, LOS, and evidence that vertical/horizontal interaction order is correct. |
| Grade transitions | Structured vertical-profile inputs, classification/applicability decisions for each grade portion, segment-level outputs, transition handling, and explicit rejection fixtures for incomplete profiles. |
| Facility workflow | Expected output for every segment before and after facility adjustments, facility average speed if claimed, facility follower density, facility LOS, passing-lane/downstream effects, and full audit provenance. |
| Guardrail and audit QA | Expected supported/unsupported status, reason, normalized inputs, derived class when available, validation source, warnings/assumptions, and confirmation that rejected cases emit no calculation outputs. |

## G. Data Requirements

Verified, source-attributed data is required before implementation for:

- HCM grade-length classification boundaries, including units, sign handling,
  inclusivity, applicability limits, and upgrade/downgrade distinctions.
- Heavy-vehicle adjustment data for every proposed class, grade/length range,
  opposing-flow condition, and heavy-vehicle percentage range.
- Vertical-class lookup data sufficient to classify the claimed input domain.
- Segment-type-specific adjustment data for Passing Constrained, Passing Zone,
  and Passing Lane paths.
- Passing Lane class-specific capacity, lane allocation, midpoint/endpoint
  density, and downstream-effect behavior.
- Facility adjustment rules, sequencing, distance basis, rounding, and
  aggregation rules.
- Horizontal and vertical interaction rules, including calculation order and
  applicability.
- Grade-transition and partial-grade-length rules when grade length differs
  from segment length.
- Independent validation examples or checked calculations with documented
  tolerances and reviewer sign-off.

No copyrighted HCM table contents should be copied into this repository unless
they are already present and their use has been reviewed. Placeholders must not
be populated with invented values or inferred coefficients.

## H. Recommended Implementation Sequence

1. Add a reusable, source-attributed fixture harness for vertical cases that
   distinguishes standalone segment, facility segment, facility output, and
   guardrail/audit expectations.
2. Add reviewed data-source placeholders and provenance fields for required
   vertical tables without adding coefficients or broadening support.
3. Implement one additional straight Passing Constrained vertical path only
   after a complete independent fixture is available; add lookup, scope,
   formula/intermediate, audit, and regression tests first.
4. Add nonlevel Passing Zone support only after a standalone fixture verifies
   opposing-flow treatment and complete segment outputs.
5. Add facility workflow support only after facility fixture boundaries,
   adjustment rules, intermediate expectations, and aggregation rules are
   documented.
6. Expand the single-page UI only after the corresponding engine paths are
   validated and unsupported adjacent inputs remain explicitly guarded.

Each PR should enable at most one narrowly defined path or one supporting
fixture/data capability, and must prove that Examples 1 through 4, audit,
project save/load, UI, and CLI behavior remain unchanged.

## I. Open Questions

- What reviewed source will supply the grade-length classification boundaries,
  and how will source/version provenance be recorded without copying protected
  table content?
- Which standalone checked case should be the next vertical path after
  `TLH-CH15-004` segment 3?
- Are upgrade and downgrade paths governed by distinct classification or
  adjustment data in every proposed class?
- What heavy-vehicle percentage domain can be claimed for each nonlevel
  segment type, and which fixtures establish its boundaries?
- Can any Example Problem 4 curve-combined result be decomposed into a valid
  standalone straight or curve fixture, or is a new checked calculation
  required?
- What is the correct expected-output basis for a standalone downgrade segment
  when the published facility result includes Passing Lane adjustment?
- Which Passing Lane outputs define standalone LOS versus facility/downstream
  performance for nonlevel classes?
- How should grade transitions be modeled when grade length and segment length
  differ?
- Which facility adjustments and rounding rules are method requirements versus
  example-specific presentation conventions?
- What independent review and sign-off process is required before a fixture
  can change a guardrail from unsupported to supported?
