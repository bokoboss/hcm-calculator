# Two-Lane Highway Method Completion — Phase 1 Specification

Related issue: #82

> **Final annotation:** Phase 5 release qualification supersedes this phase specification's provisional scope statements; see `two_lane_phase_5_release_qualification.md`.

## Purpose

Phase 1 establishes the HCM 7th Edition Chapter 15 Step 1–3 foundation required before the calculator can safely accept broader non-example Two-Lane Highway inputs.

This phase is methodology and engine work. It must not broaden UI claims until the engine, tests, audit output, and documentation agree on the supported envelope.

## Authoritative references

Use the read-only references already available to the project:

- HCM7 Chapter 15, Two-Lane Highways — Motorized Vehicle Methodology
- HCM7 Chapter 26, Two-Lane Highway Example Problems
- NCHRP Research Report 1102, Chapter 7 equation/exhibit summary

Primary Phase 1 source items:

- Exhibit 15-9 — core methodology sequence
- Exhibit 15-10 — minimum and maximum segment lengths
- Equation 15-1 — analysis-direction demand flow rate
- Exhibit 15-11 — vertical alignment classification

## Current implementation problem

The repository already contains:

- a complete Exhibit 15-11 upgrade/downgrade classification table;
- coefficient rows for vertical Classes 1–5 used by later Chapter 15 steps; and
- validated Examples 1–4.

However, production scope remains coupled to exact Example Problem 4 metadata, selected heavy-vehicle percentages, and manually validated paths. The current `grade_length_mi` contract also needs to be reconciled with Exhibit 15-11, which classifies by analysis **segment length** and grade magnitude/direction.

Phase 1 must separate:

1. HCM classification and applicability rules;
2. validation evidence; and
3. temporary product-scope decisions.

Validation metadata may describe confidence and regression evidence, but it must not be the data source for vertical classification.

## Required implementation

### 1. Add a table-driven Exhibit 15-10 segment-length validator

Implement a pure engine helper that returns an auditable result containing:

- segment type;
- vertical class;
- submitted segment length;
- minimum permitted length;
- maximum permitted length;
- compliance status; and
- source reference.

Required ranges in miles:

| Vertical class | Passing constrained | Passing zone | Passing lane |
| --- | --- | --- | --- |
| 1 | 0.25–3.0 | 0.25–2.0 | 0.5–3.0 |
| 2 | 0.25–3.0 | 0.25–2.0 | 0.5–3.0 |
| 3 | 0.25–1.1 | 0.25–1.1 | 0.5–1.1 |
| 4 | 0.5–3.0 | 0.5–2.0 | 0.5–3.0 |
| 5 | 0.5–3.0 | 0.5–2.0 | 0.5–3.0 |

Boundary values are inclusive. Invalid segment types, invalid vertical classes, non-finite values, and non-positive lengths must fail explicitly.

Do not silently clamp a submitted segment length. If a future workflow needs HCM-defined segment restructuring, implement that as a separate, explicit preprocessing operation.

### 2. Make Exhibit 15-11 the production vertical classifier

Use `classify_vertical_alignment()` as the sole production source of the vertical class for general Chapter 15 input.

Requirements:

- signed positive grade defaults to upgrade;
- signed negative grade defaults to downgrade;
- explicit `direction_context` remains available for unsigned grade magnitude input;
- grade magnitude uses the correct Exhibit 15-11 column;
- analysis segment length uses the correct Exhibit 15-11 row;
- submitted `vertical_class`, when accepted for audit/import compatibility, must match the derived class;
- classification output must retain lookup row, lookup column, direction, and source reference.

Example Problem 4 metadata must not be used to derive a class.

### 3. Reconcile `grade_length_mi` with the HCM input model

Before changing the public schema, inspect every use of `grade_length_mi`.

Phase 1 decision rule:

- Exhibit 15-11 uses analysis segment length, not a separate grade-length lookup input.
- Do not introduce an independent grade-length input unless another Chapter 15 equation or source item explicitly requires it.
- Where `grade_length_mi` is only an alias for segment length, deprecate, rename, or normalize it deliberately rather than maintaining a false methodology distinction.
- Preserve backward compatibility for existing saved projects and fixtures through an explicit migration/normalization layer if the field changes.

The implementation and documentation must state the final decision and source basis.

### 4. Decouple HCM support from validation metadata

Refactor `two_lane_highway_scope.py` and `vertical_lookup.py` so that:

- Exhibit 15-11 classification is method data;
- Exhibit 15-10 length applicability is method data;
- Chapter 26 records remain validation/provenance data;
- missing a Chapter 26 example-path record does not by itself mean that HCM table data is missing;
- unsupported status identifies the actual missing methodology branch, applicability failure, or validation gap.

Do not remove validation metadata. Reclassify its role.

### 5. Define the Phase 1 calculation envelope

Phase 1 does not automatically authorize every downstream calculation combination.

At completion, the engine must at least be able to classify and validate Step 1–3 inputs for:

- Passing Constrained, Passing Zone, and Passing Lane;
- vertical Classes 1–5;
- upgrade and downgrade grades;
- all Exhibit 15-10 boundary ranges; and
- level grade where applicable.

Downstream Steps 4–10 may remain guarded until Phase 2 tests establish non-example positive paths.

The error must distinguish:

- invalid input;
- outside Exhibit 15-10 applicability;
- unsupported downstream methodology combination; and
- insufficient validation evidence.

## Tests

Add focused tests for:

1. every Exhibit 15-10 table row and segment type;
2. inclusive minimum and maximum boundaries;
3. just-below-minimum and just-above-maximum rejection;
4. non-finite and non-positive segment lengths;
5. Exhibit 15-11 representative upgrade/downgrade cells;
6. every row and grade-column boundary;
7. signed-grade direction inference;
8. explicit direction-context behavior;
9. submitted vertical-class mismatch;
10. decoupling classification from Chapter 26 metadata;
11. existing Examples 1–4 regression; and
12. saved-project compatibility if the grade-length field changes.

Tests must assert audit/source fields, not only the final class number.

## Audit output

Phase 1 must expose these intermediate values for supported calculations or scope inspection:

- `vertical_class`;
- `vertical_direction`;
- `vertical_lookup_row_range`;
- `vertical_lookup_column_range`;
- `vertical_class_source_reference`;
- `segment_length_min_mi`;
- `segment_length_max_mi`;
- `segment_length_applicability_status`; and
- `segment_length_source_reference`.

Names may be adjusted to match repository conventions, but the information must be retained.

## Documentation updates

Update at least:

- `docs/ch15_calculator_coverage_status.md`;
- `docs/methodology/generalization_audit.md`;
- relevant vertical methodology/scope documents;
- README limitations if public behavior changes; and
- project schema notes if the grade-length contract changes.

Do not describe the calculator as complete Chapter 15 support after Phase 1.

## Verification and PR requirements

Before opening the PR:

- run the full pytest suite;
- run focused Step 1–3 and Examples 1–4 tests;
- run `git diff --check`;
- inspect calculation/audit JSON for representative Class 1–5 inputs;
- verify existing project JSON still loads or has a tested migration path; and
- confirm no Streamlit formula logic was introduced.

The Phase 1 PR must include:

- source mapping;
- files changed;
- behavior added;
- behavior deliberately still guarded;
- tests and results;
- compatibility impact; and
- follow-up items for Phase 2.

After CI passes, self-review the diff, address findings, and squash-merge.
