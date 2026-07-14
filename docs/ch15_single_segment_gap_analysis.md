# Chapter 15 Single-Segment Gap Analysis

## Purpose

This document identifies the work needed to make the HCM 7th Edition Chapter
15 Two-Lane Highway Motorized Vehicle LOS manual single-segment calculator more
complete. It is a planning document only. It does not authorize formula changes
or expansion beyond independently validated methodology and fixtures.

The target remains an auditable, facility-type-aware calculation method whose
inputs, assumptions, intermediate values, and outputs can be reviewed without
depending on the UI.

For a calculator-facing inventory of current engine, UI, test, segment-type,
and workflow coverage, see the
[Chapter 15 Calculator Coverage Status](ch15_calculator_coverage_status.md).

## Current Repository Capability

### Validated baseline

- HCM Chapter 26 Two-Lane Highway Example Problems 1 through 4
  (`TLH-CH15-001` through `TLH-CH15-004`) are implemented as the validation
  baseline.
- Examples 1 and 2 validate single Passing Constrained segment paths, including
  the Example 2 horizontal-curve path.
- Examples 3 and 4 validate narrowly scoped multi-segment facility paths,
  including Passing Constrained, Passing Zone, Passing Lane, mountainous
  segments, downstream passing-lane adjustment, and facility follower density.
- The validated examples are not evidence that arbitrary Chapter 15 inputs are
  supported.
- Manual Facility Calculator v0.1 exposes those Example 3/4 paths through a
  guarded template-backed workflow. It does not broaden the methodology or
  authorize arbitrary facilities.

### Manual single-segment calculator

The Streamlit worksheet and its UI adapter call the calculation method's public
`calculate_single_segment` boundary. Calculation logic remains independent from
Streamlit.

Current manual support:

- One straight segment.
- Passing Constrained, Passing Zone, and Passing Lane segment types.
- Level terrain.
- One narrowly validated mountainous path: straight Passing Constrained,
  `6% / 0.5 mi`, Class 4, exactly `8%` heavy vehicles, based on
  `TLH-CH15-004` segment 3.
- Passing Zone actual opposing-direction volume.
- Passing Constrained fixed `1,500 veh/h` opposing-flow assumption.
- Passing Lane only for the validated Class 1, `8%` heavy-vehicle path.
- Engineer-readable validation for positive length and speed, supported lane and
  shoulder widths, PHF, heavy-vehicle percentage, and directional volumes.
- Manual horizontal curves for the narrowly validated Example Problem 2 path.
- Metric and Imperial UI entry and result display. The UI adapter converts
  Metric inputs to the engine's Imperial-native contract, and downloadable JSON
  preserves the Imperial-native engine result.
- Auditable result objects containing outputs, selected named intermediate
  values with HCM references, assumptions, and warnings.
- A hardened HCM7 Chapter 15 Step 4 helper that exposes BFFS, the
  heavy-vehicle speed adjustment coefficient, lane/shoulder adjustment,
  access-point adjustment, and FFS using Eq. 15-2 through Eq. 15-6 and the
  complete Exhibit 15-12 coefficient table for vertical Classes 1 through 5.
- A hardened HCM7 Chapter 15 Step 5 tangent average-speed helper that exposes
  `b3`, `b4`, `m`, `p`, tangent average speed, and source references using Eq.
  15-7 through Eq. 15-11 and table-driven Exhibits 15-13 through 15-20 for
  vertical Classes 1 through 5.
- The guarded Step 5 horizontal-curve speed adjustment uses a table-driven
  Exhibit 15-22 classification lookup and centralized, auditable Eq. 15-12
  through Eq. 15-16 helpers. It reports matched radius/superelevation bins,
  curve BFFS/FFS, slope coefficient, subsegment speed, tangent comparison
  speed, and the length-weighted segment speed.
- Hardened HCM7 Chapter 15 Step 8 follower-density helpers that use Eq. 15-35
  for Passing Constrained and Passing Zone segments and Eq. 15-34 for supported
  Passing Lane midpoint cases. The helpers expose the equation/formula and,
  for Passing Lane, the faster-lane and slower-lane density components.

Known unsupported or incomplete manual cases:

- Horizontal curves outside the narrowly validated Example Problem 2 manual
  path.
- General nonlevel calculations for arbitrary grade-length combinations.
  HCM7 Chapter 15 Step 3 vertical alignment classification is implemented from
  Exhibit 15-11, including auditable matched length and grade bins, but the
  classification result does not enable downstream formulas. This calculation
  gap is tracked through the dedicated
  [Chapter 15 Vertical Class and Grade-Length Methodology Map](ch15_vertical_class_methodology_map.md),
  which audits current scope, missing coefficient data, validation needs, and a
  phased implementation plan.
- Passing Lane cases outside Class 1 and `8%` heavy vehicles.
- Upstream or downstream passing-lane effects and other corridor context.
- General follower-density adjustment for a manual single segment.
- General facility manual input and report export. Facility LOS is exposed only
  through the guarded Manual Facility Calculator v0.1 Example 3/4 templates.
- A complete audit record that preserves normalized inputs and all
  decision-relevant intermediate values alongside the result.

### Explicit unsupported-scope guardrails

The manual and engine boundaries now reject unsupported terrain, grade-length,
vertical-class, and Passing Lane combinations before formulas run. Failed
manual calculations preserve the selected scope inputs, normalized engine
inputs when available, a classified scope status, and an engineer-readable
unsupported reason without emitting misleading LOS or output values.

This change does not add general mountainous, grade-length, or vertical-class
calculation support. Exhibit 15-11 can classify general vertical alignment, but
unsupported calculation combinations are still rejected rather than
approximated. Broader calculation support still requires reviewed downstream
coefficient data and independent validation fixtures.

The Phase 3 vertical implementation integrates the metadata lookup with the
scope guardrail and promotes exactly one Example Problem 4 segment path. It
adds validation provenance to successful audit records and assumptions. It
does not change formulas or claim general vertical-class, grade-length,
mountainous, Passing Zone, or Passing Lane support.

Phase 3B assessed every remaining Example Problem 4 nonlevel path and
formalized no additional manual paths. Segments 1, 2, and 4 include horizontal
curves; segment 5 is a Passing Lane facility path; and segment 6's published
final density includes upstream Passing Lane adjustment. Lookup metadata and
guardrail tests now preserve these paths as facility-only. The exact straight
Passing Constrained `6% / 0.5 mi`, Class 4, `8%` path from segment 3 remains
the only validated mountainous manual single-segment path.

Manual Facility Calculator v0.1 now exposes the facility-only Example 3/4
paths without promoting them to standalone or general support. Segment
sequence, nonlevel/curve context, Passing Lane placement, and downstream
adjustment context remain template-controlled. Facility Save/Load is not
general-purpose: Facility Project Save/Load v0.1 supports only
`project_type = manual_facility_v0` for the guarded Example 3/4 templates.
It restores the selected template, unit system, editable segment rows, and
saved calculation/audit context without changing the calculation path.
Unsupported combinations remain guarded. Manual Single Segment Save/Load using
`project_type = manual_single_segment` remains supported.

Export/reporting v0.1 adds CSV, lightweight Excel `.xlsx`, copy-ready Markdown,
and report-friendly JSON for successful Manual Single Segment and guarded
Manual Facility v0.1 calculations. Reports use the currently selected UI unit
system with explicit unit labels and include assumptions, warnings,
limitations, segment rows where applicable, and an audit/source-reference
summary. The export layer formats the existing result and does not re-run or
change calculation formulas, Step 3-10 behavior, guardrails, or supported
methodology. PDF and DOCX export are not implemented.

The Phase 4
[Chapter 15 Vertical Fixture Inventory](ch15_vertical_fixture_inventory.md)
now records the available standalone and facility-only evidence and the
required future fixtures. Nonlevel calculation expansion remains blocked by
missing verified fixtures and applicable downstream HCM coefficient data.

### Phase 4B data and fixture preparation

Non-runtime manifest files, a vertical fixture template, structural validation,
and [vertical data ingestion guidelines](ch15_vertical_data_ingestion_guidelines.md)
now exist for future verified additions. They contain no actual HCM values or
coefficients and enable no calculation support. Future fixtures must include
source attribution, expected outputs, tolerances, and explicit validation
status; placeholders must never be used for calculation.

### Level + straight baseline status

Level terrain with straight horizontal alignment is treated as the practical
baseline assumption because it excludes unvalidated grade, horizontal-curve,
and facility interactions while retaining the supported Chapter 15 motorized
vehicle LOS workflow. It is the appropriate default case when those effects are
intentionally not modeled.

The baseline currently supports one Passing Constrained, Passing Zone, or
Passing Lane segment. Passing Constrained uses the required `1,500 veh/h`
opposing-flow assumption, Passing Zone requires a positive submitted opposing
flow, and Passing Lane remains limited to the validated Class 1, `8%`
heavy-vehicle path. Passing Lane results explicitly exclude downstream and
facility-wide effects.

The reliability matrix covers low, medium, and near-capacity demand; multiple
supported heavy-vehicle percentages; low, normal, and high opposing flows;
Metric and Imperial entry; supported Passing Lane behavior and warnings;
engineer-readable boundary and non-finite input validation; output sanity;
successful audit completeness; and runnable project JSON round trips for all
three supported segment types. These regression tests improve confidence in the
existing baseline but do not expand the validated HCM methodology or support
mountainous terrain, general horizontal curves, or facility analysis.

## Comparison Reference

The public
[`crosstraffic/highway-capacity-manual-mcp`](https://github.com/crosstraffic/highway-capacity-manual-mcp)
repository was reviewed as a comparison reference, especially:

- [`hcm_mcp_server/functions/chapter15.py`](https://github.com/crosstraffic/highway-capacity-manual-mcp/blob/main/hcm_mcp_server/functions/chapter15.py)
- [`hcm_mcp_server/core/models.py`](https://github.com/crosstraffic/highway-capacity-manual-mcp/blob/main/hcm_mcp_server/core/models.py)
- [`README.md`](https://github.com/crosstraffic/highway-capacity-manual-mcp/blob/main/README.md)

Its useful design references are:

- Chapter 15 is decomposed into named workflow steps rather than exposed only
  as one complete analysis operation.
- Its schema separates highway-level, segment-level, and horizontal-subsegment
  data.
- Segment inputs include passing type, length, grade, speed limit, directional
  volumes and flows, capacity, free-flow speed, average speed, vertical class,
  heavy vehicles, percent followers, follower density, and horizontal class.
- Horizontal subsegments include length, average speed, horizontal class,
  radius, central angle, and superelevation.

The comparison repository must not be treated as an authoritative calculation
source. Its Chapter 15 function layer constructs objects from and delegates core
calculations to `transportations_library`. Its README describes the project as
beta/research-oriented and states that tests are still to be added. Any workflow,
schema, or calculation behavior inferred from it requires independent mapping
to the HCM and validation against accepted fixtures before use here. No
calculation logic should be copied from it, and it should not become a
dependency.

## Full Single-Segment Workflow Gap Matrix

| Workflow step | Current capability | Gap to a more complete single-segment workflow |
| --- | --- | --- |
| Identify vertical class | Uses the table-driven Exhibit 15-11 lookup to return Classes 1-5 plus the matched length row, grade column, direction, and source. | Integrate the classification decision into broader workflows only after downstream coefficients and validation fixtures are available. |
| Demand flow / capacity | Calculates analysis-direction demand flow. Passing Zone uses actual opposing demand flow; Passing Constrained assumes `1,500 veh/h`; Passing Lane uses its validated capacity path. | Clarify directional-flow requirements and capacity rules by segment type, validate all input domains and capacity exceedance behavior, and expose assumptions consistently. |
| Vertical alignment | Vertical class is calculated directly from grade and length; there is no separately reported vertical-alignment workflow decision. | Separate input interpretation, applicability checks, and vertical-class result in the audit trail without duplicating formulas. |
| Free-flow speed | Calculates and audits base free-flow speed, lane/shoulder adjustment, access-point adjustment, heavy-vehicle coefficient, and free-flow speed through a validated Step 4 helper. Exhibit 15-12 is table-driven for Classes 1-5. | Add independent validation fixtures before promoting additional nonlevel public calculation paths. |
| Average speed | Calculates and audits Step 5 tangent average speed for supported straight segment types with table-driven Exhibits 15-13 through 15-20. The guarded horizontal-curve path uses table-driven Exhibit 15-22 and centralized Eq. 15-12 through Eq. 15-16 helpers. | Add independent validation before broadening beyond the existing level Example Problem 2 manual path and validated facility examples. |
| Percent followers | Calculates and audits Step 6 percent followers through Eq. 15-17 to Eq. 15-23. Exhibits 15-24 through 15-29 are table-driven for vertical Classes 1-5, with explicit input and logarithm-domain validation. | Add independent validation fixtures before broadening guarded nonlevel or Passing Lane calculation support. |
| Passing Lane midpoint measures | Calculates and audits Step 7 Passing Lane lane flow, heavy-vehicle split, speed differential, and midpoint speeds through Eq. 15-24 to Eq. 15-33. The HCM-defined faster-lane heavy-vehicle proportion multiplier remains `0.4`. | Preserve the validated Class 1, `8%` heavy-vehicle guardrails until independent fixtures authorize broader Passing Lane support. |
| Follower density | Calculates and audits Passing Constrained/Passing Zone density with Eq. 15-35 and supported Passing Lane midpoint density with Eq. 15-34, including lane components. | Preserve the explicit endpoint-versus-midpoint basis as future Passing Lane and facility support expands. |
| Follower-density adjustment, where applicable | Downstream adjustment exists in validated facility examples, but manual single-segment analysis explicitly excludes upstream/downstream effects. | Define when a standalone segment may validly receive an adjustment, what context is required, and when the UI must warn that facility context is missing. |
| Segment LOS | Step 10 determines Motorized Vehicle LOS from follower density with centralized, boundary-tested HCM7 Exhibit 15-6 thresholds. Outputs audit the threshold group, thresholds used, density basis, posted speed, and source reference. | Document capacity-related LOS F behavior before expanding beyond the currently supported calculation paths. |

## Input Schema Gaps

The existing repository already has facility-aware models and should evolve
those contracts rather than adopting the comparison repository's schema.
Useful schema improvements for a complete single-segment workflow are:

- A public, method-owned single-segment input model instead of relying on the
  facility fixture model plus a UI-built dictionary.
- Explicit analysis context: segment type, terrain/vertical inputs, horizontal
  alignment, directional volumes, and whether upstream/downstream facility
  effects are intentionally excluded.
- Structured horizontal subsegments for manual curve input.
- Field-level units, valid ranges, required/conditional rules, and normalized
  engine-native values.
- A structured audit result that records normalized inputs, assumptions,
  applicability decisions, all material intermediate values, outputs, warnings,
  and validation provenance.
- Stable terminology for Passing Constrained, Passing Zone, and Passing Lane
  across models, UI labels, output fields, and documentation.

## Prioritized Implementation Roadmap

Every phase requires methodology mapping, new validation fixtures, method-level
tests, regression tests, and reviewer sign-off before its capability is claimed
as supported.

The Step 4 through Step 6 formula hardening does not implement general nonlevel
workflow support. Step 6 now exposes auditable PFcap, PF25cap, slope, power, and
final percent-followers values using table-driven Exhibits 15-24 through 15-29.
Step 8 follower density is hardened separately with Eq. 15-34 and Eq. 15-35.
Step 10 Motorized Vehicle LOS determination is hardened with centralized HCM7
Exhibit 15-6 thresholds, explicit upper-inclusive boundaries, input validation,
and audit fields. Step 7 Passing Lane midpoint measures are centralized and
auditable through Eq. 15-24 to Eq. 15-33. Step 9 downstream Passing Lane
adjustment is centralized and auditable through Eq. 15-36 to Eq. 15-38 for the
existing validated facility paths. It explicitly distinguishes the percent
followers entering the Passing Lane from the subject segment's unadjusted
percent followers used in adjusted follower density. This does not add general
facility UI, broaden Passing Lane support, or enable downstream adjustment for
manual single-segment calculations; existing guardrails remain in force.

### Phase 1: Complete the level-terrain single-segment foundation

1. Broaden validated level-terrain single-segment coverage.
2. Cleanly define Passing Constrained, Passing Zone, and Passing Lane input
   requirements, assumptions, capacity behavior, density basis, and warnings.
3. Improve input validation, including conditional fields and supported ranges.
4. Improve the output audit trail so normalized inputs, assumptions,
   intermediate values, outputs, sources, and warnings can be reviewed together.
5. Add validation fixtures covering the expanded level-terrain matrix before
   exposing additional UI choices.

This is the recommended next implementation phase because it strengthens the
single-segment contract and auditability before adding geometric and facility
complexity.

### Phase 2: Expand geometric and adjustment coverage

1. Add horizontal-curve manual input using structured subsegments.
2. Add general nonlevel calculation support only as downstream coefficient
   tables and validation fixtures become available. Exhibit 15-11
   classification alone does not authorize those calculations.
3. Expand follower-density adjustment coverage with explicit applicability and
   required context.
4. Add focused regression coverage for interactions among segment type,
   vertical class, horizontal alignment, and adjustment behavior.

### Phase 3: Add facility and reporting workflows

1. Expand beyond the template-backed multi-segment facility workflow only
   after additional methodology and validation fixtures authorize it.
2. Broaden facility LOS exposure only with new validation, while clearly
   distinguishing segment results from facility effects.
3. Add export/report workflows that preserve the full audit record and
   validation provenance.

## Do Not Do Yet

- Do not replace the validated engine with an external library.
- Do not add full mountainous tables without independent methodology mapping
  and validation.
- Do not mix facility effects into the single-segment UI without clear warnings
  and explicit required context.
- Do not copy calculation logic from the comparison repository or add it as a
  dependency.
- Do not claim general Chapter 15 support from the current Example Problems 1
  through 4 validation baseline.

## Completion Criteria for a More Complete Single-Segment Calculator

A capability should be called supported only when:

- Applicability and exclusions are documented.
- Inputs and units have explicit validation rules.
- Formula sequence and assumptions are mapped to the HCM.
- Material intermediate values and decision points are auditable.
- Independent validation fixtures and tolerances exist.
- Method-level, fixture, and regression tests pass.
- Unsupported combinations fail clearly instead of silently defaulting.
# Phase 2 update

Passing Constrained and Passing Zone homogeneous single segments are now
available across the Exhibit 15-10/15-11 applicable Class 1--5 envelope.
This includes level/nonlevel, upgrade/downgrade, actual Passing Zone opposing
flow, and valid Step 5d horizontal-curve subsegments. Passing Lane and
upstream/downstream/facility interactions remain guarded for Phase 3.
