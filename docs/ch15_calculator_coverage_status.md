# Chapter 15 Calculator Coverage Status

## Purpose

This document is a calculator-facing inventory of the current HCM 7th Edition
Chapter 15 Two-Lane Highway motorized vehicle implementation. It summarizes
what the engine, UI, fixtures, and tests support today so the next capability
PR can be selected without broadening methodology claims.

This is a status document only. It does not authorize new formulas, HCM table
values, calculation paths, or user-interface scope.

Multilane Highway analysis is planned as a separate calculator family and is
not part of this Chapter 15 Two-Lane Highway coverage inventory. See the
[Multilane Highway Implementation Plan](multilane_highway_implementation_plan.md)
for its scope boundary and phased validation plan.

Status terms used below:

- **Supported**: available in the stated workflow with tests and explicit scope.
- **Limited**: available only for a narrow subset of inputs or behavior.
- **Internal only**: available through validated fixtures, helpers, or QA
  workflows, but not as a general manual calculator workflow.
- **Guarded**: implemented behavior exists, but unsupported combinations are
  deliberately rejected.
- **Not implemented**: no current user workflow exists.

## Current Calculator Status

The current calculator is best described as:

- A **validated methodology engine** for the exact HCM Chapter 26 Example
  Problems 1 through 4 and their supporting Step 3 through Step 10 helpers.
- A **limited manual single-segment calculator** that exposes selected,
  explicitly guarded engine paths.
- A **strong level + straight baseline** for Passing Constrained, Passing Zone,
  and narrowly scoped Passing Lane segments.
- **Partial horizontal curve support**, strongest for the validated Example
  Problem 2 single-segment path and available internally in Example Problem 4.
- **Phase 1 Step 1-3 coverage** for all Exhibit 15-10 segment types and all
  Exhibit 15-11 vertical classes. This classifies and validates applicability;
  it does not authorize the downstream Step 4-10 calculation paths.
- **Guarded nonlevel downstream calculation support**, with one exact
  mountainous manual path and additional nonlevel paths retained only in
  validated facility examples.
- **Manual Facility Calculator v0.1 is limited and template-backed**. It exposes
  the existing Example 3/4 facility paths while keeping segment sequence,
  terrain/curve context, Passing Lane placement, and downstream context
  guarded. Facility Project Save/Load v0.1 preserves this template-backed
  boundary using `project_type = manual_facility_v0`. It is not a general
  facility calculator.

The presence of table-driven helpers or passing formula-level tests does not by
itself make arbitrary inputs supported. Public calculation claims remain
limited by the scope guardrails and validation fixtures.

## Methodology Step Coverage Matrix

| HCM Step | Methodology item | Equations / Exhibits | Engine status | UI status | Test status | Known limitation | Recommended next action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Step 2 | Demand flow, capacity, and demand-to-capacity context | Eq. 15-1; Chapter 15 Step 2 capacity rules | Supported for current segment paths; demand flow and capacity are audited. | Supported in Manual Single Segment and Validated Examples / QA; d/c is not presented as a primary manual result. | Unit, fixture, CLI, and level-straight regression coverage. | Capacity rules remain segment-type and validated-path scoped; no general facility input contract. | Expose consistent demand, capacity, and d/c context in a future facility worksheet without changing rules. |
| Step 1 | Segment length applicability | Exhibit 15-10 | Table-driven, auditable validation for Passing Constrained, Passing Zone, Passing Lane, and Classes 1-5. | Not separately exposed as a public calculator workflow. | Every table row, inclusive boundaries, invalid input, and outside-range tests. | Out-of-range actual lengths are rejected in Phase 1; no HCM restructuring/clamping has been implemented. | Add explicit HCM restructuring only when its scope is mapped and validated. |
| Step 3 | Vertical alignment classification | Exhibit 15-11 | Classification lookup is implemented and auditable for all table rows; downstream calculation use is separately guarded. | Limited terrain/grade entry; unsupported downstream calculations fail clearly. | Dedicated lookup, boundary, fixture infrastructure, and scope-guardrail tests. | Classification coverage is broader than validated calculation coverage; most nonlevel paths are not safe as standalone manual segments. | Keep downstream guards; expose additional calculation paths only through new independent fixtures. |
| Step 4 | Free-flow speed (FFS) | Eq. 15-2 through Eq. 15-6; Exhibit 15-12 | Centralized, auditable helper with class-indexed coefficients. | Supported where the selected manual or validated-example path is allowed. | Focused Step 4 tests plus Examples 1-4 and regression coverage. | Complete helper data does not authorize general nonlevel or curve combinations. | Reuse existing outputs in broader UI views; do not broaden methodology scope. |
| Step 5A | Tangent average speed | Eq. 15-7 through Eq. 15-11; Exhibits 15-13 through 15-20 | Centralized and auditable for supported segment types/classes. | Supported for allowed straight manual paths and validated examples. | Focused Step 5 tests plus Examples 1, 3, and 4. | Public execution remains constrained by validation and segment-type guardrails. | Surface existing intermediate values more clearly in facility and calculation-sheet views. |
| Step 5B | Horizontal curve speed adjustment | Eq. 15-12 through Eq. 15-16; Exhibit 15-22 | Implemented with auditable classification and subsegment calculations. | Limited to the guarded Example Problem 2-style level Passing Constrained manual workflow; validated examples also exercise curves internally. | Horizontal-class, curve-helper, manual adapter, and Examples 2/4 tests. | No general manual curves for Passing Zone, Passing Lane, or nonlevel segments. | Broaden UI exposure only after each additional curve interaction has validation evidence. |
| Step 6 | Percent followers | Eq. 15-17 through Eq. 15-23; Exhibits 15-24 through 15-29 | Centralized, table-driven, and auditable for supported paths. | Supported where the selected manual or validated-example path is allowed. | Focused Step 6 tests, input-domain tests, and Examples 1-4. | Helper coverage is broader than publicly validated combinations. | Reuse in facility templates; preserve current scope checks. |
| Step 7 | Passing Lane measures | Eq. 15-24 through Eq. 15-33 | Centralized and auditable for validated Passing Lane paths. | Limited manual Passing Lane result; no downstream or facility-wide effects in manual single segment. | Focused Step 7 tests and Examples 3/4. | Manual support remains Class 1 at exactly 8% heavy vehicles; no general Passing Lane workflow. | Make validated Passing Lane behavior visible in Manual Facility Calculator v0.1. |
| Step 8 | Follower density | Eq. 15-34 and Eq. 15-35 | Centralized and auditable for Passing Constrained, Passing Zone, and supported Passing Lane midpoint cases. | Supported for allowed manual paths and validated examples. | Focused Step 8 tests, level-straight regression, and Examples 1-4. | Passing Lane midpoint density must not be confused with endpoint or downstream facility density. | Label density basis explicitly in broader UI and exports. |
| Step 9 | Downstream Passing Lane adjustment | Eq. 15-36 through Eq. 15-38 | Centralized and auditable for explicitly identified downstream segments in validated facilities. | Visible only through the guarded Example 3/4 Manual Facility Calculator v0.1 templates and Validated Examples / QA; deliberately excluded from Manual Single Segment. | Focused Step 9 tests, Examples 3/4 facility tests, and manual facility guardrail tests. | No arbitrary downstream application or general manual facility context. | Preserve template-controlled downstream context until new validation evidence exists. |
| Step 10 | Motorized vehicle LOS | Exhibit 15-6 | Centralized, boundary-tested, and auditable for supported density bases. | Supported in manual results and validated examples. | Focused threshold/boundary tests plus Examples 1-4. | LOS validity depends on the upstream path and density basis being supported. | Preserve LOS guardrails and make basis/provenance clearer in facility and report views. |
| Step 11 | Facility analysis | Facility length-weighted results, including Eq. 15-39 pattern | Implemented through the existing Example 3 and Example 4 facility engine paths. | Limited template-backed Manual Facility Calculator v0.1 plus Validated Examples / QA. | Example 3/4 unit and integration fixture tests plus manual facility adapter tests. | Not a general facility calculator; arbitrary segment sequences and unsupported inputs are rejected. | Keep the workflow template-backed until additional methodology and fixtures authorize expansion. |

## Segment-Type Coverage Matrix

| Segment type | Level + straight | Level + horizontal curve | Nonlevel + straight | Nonlevel + horizontal curve | Downstream passing-lane affected segment | Manual single-segment UI | Facility/example engine support | Current guardrail status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Passing constrained | Supported baseline | Limited to validated Example Problem 2-style manual path | Guarded; exact `6% / 0.5 mi`, Class 4, 8% heavy-vehicle manual path supported | Internal only in exact Example Problem 4 facility paths | Internal only in exact Example 3/4 facility context | Supported with explicit limitations | Supported for exact Examples 1-4 | Rejects unsupported curves, nonlevel combinations, and missing facility context. |
| Passing zone | Supported; requires submitted opposing-direction volume | Not implemented manually | Guarded / not implemented manually | Not implemented | Internal only in exact Example 3 downstream context | Supported only for level + straight | Supported in exact Example 3 | Rejects missing opposing flow and unsupported geometry/nonlevel scope. |
| Passing lane | Limited to validated Class 1, 8% heavy-vehicle path | Not implemented manually | Internal only in exact Example 4 facility path | Not implemented | Passing Lane segment measures exist, but downstream effects apply to later facility segments only | Limited; explicitly excludes downstream and facility-wide effects | Supported in exact Examples 3/4 | Rejects unsupported heavy-vehicle, vertical, curve, and standalone downstream-effect claims. |

## User Workflow Coverage Matrix

| User workflow | Status | Current coverage and boundary |
| --- | --- | --- |
| Manual Single Segment | Limited | Single-page worksheet for supported Passing Constrained, Passing Zone, and Passing Lane paths; unsupported combinations are rejected. |
| Validated Examples / QA | Supported | Runs and displays exact Chapter 26 Examples 1-4, including facility examples. |
| CLI run from YAML/JSON | Limited | Loads YAML or JSON fixture files with a top-level `cases` list and runs a selected validated/example-scoped case. It is not a general ad hoc calculator CLI. |
| Save/Load Project JSON | Supported for Manual Single Segment and guarded Manual Facility v0.1 | `manual_single_segment` project JSON remains supported. `manual_facility_v0` project JSON preserves the selected Example 3/4 template, unit system, edited segment rows, normalized facility inputs, result, outputs, audit, warnings, assumptions, and unsupported-behavior notes. Facility Save/Load remains template-backed and does not imply general facility support. |
| Audit trail | Limited | Manual calculations and validated results expose assumptions, warnings, intermediate values, outputs, and selected provenance. Export/reporting v0.1 formats this existing context but is not a formal sealed calculation sheet. |
| Metric/Imperial UI | Supported | Manual UI accepts and displays Metric or Imperial values; engine-native calculation values remain Imperial. |
| Manual Facility Calculator | Limited | Manual Facility Calculator v0.1 is a guarded, template-backed workflow anchored to validated Examples 3 and 4. It is not a general Chapter 15 facility calculator. |
| Export/reporting | Limited | Export/reporting v0.1 provides CSV, lightweight Excel `.xlsx`, copy-ready Markdown, and report-friendly JSON for successful Manual Single Segment and guarded Manual Facility v0.1 calculations. Exports use selected display units with labels, include assumptions/warnings/limitations, and format only the existing calculated result. PDF/DOCX are not implemented, and export does not imply broader methodology support. |

## What Is Safe to Claim Now

- Level + straight single-segment motorized LOS is the strongest practical
  workflow.
- Horizontal curve support exists for validated/guarded single-segment
  workflows.
- Nonlevel support is still exact-path / guarded, not general.
- Passing Lane support remains limited and does not imply broad
  downstream/facility behavior in manual single segment.
- Facility behavior is exposed only through guarded Example 3/4-backed
  templates; arbitrary facility construction remains unsupported.

The calculator should not be described as a general HCM Chapter 15 calculator.
It is an auditable, validation-led implementation with deliberately narrow
public workflows.

## What Should Be Implemented Next

### 1. Harden Manual Facility Calculator Beyond v0.1

Manual Facility Calculator v0.1 now provides a template-backed, single-page
facility worksheet using the already validated Example 3 and Example 4
behavior. Any future expansion must add methodology evidence and validation
fixtures before unlocking additional segment sequences, nonlevel paths,
passing-lane arrangements, or downstream contexts.

This remains the correct guarded facility direction after Step 9 because:

- Step 7 and Step 9 are facility/downstream-related.
- Example 3 and Example 4 already validate facility behavior.
- Several vertical paths are facility-only, not safe standalone
  single-segment paths.
- A template-backed facility UI can expose capability without claiming general
  facility support.

This PR should preserve the single-page guided worksheet concept and should not
create an arbitrary segment-builder or claim general facility analysis.

### 2. Broader UI Exposure for Already-Supported Engine Paths

Expose more of the existing engine audit fields, density basis, scope
decisions, facility-only provenance, and Step 2 through Step 10 intermediate
values. This should improve clarity without enabling unsupported methodology
or relaxing guardrails.

### 3. Export / Reporting or Calculation-Sheet Output

After the manual single-segment and template-backed facility workflows are
clear, add a readable engineering calculation sheet or report export. It
should preserve submitted inputs, normalized inputs, assumptions, scope
decisions, intermediate values, outputs, sources, warnings, and validation
provenance. Existing JSON downloads can remain the machine-readable baseline.

## Decision Summary

The methodology engine is ahead of the general-purpose calculator workflows.
Manual Facility Calculator v0.1 exposes the existing Step 7, Step 9, Step 11,
and facility-only vertical capability through validated Example 3/4-backed
templates while keeping the project's validation-led guardrails intact. The
next facility expansion must remain evidence-led and should not claim general
Chapter 15 facility support.
