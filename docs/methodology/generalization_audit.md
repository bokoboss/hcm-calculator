# Methodology Generalization Audit

This audit identifies where the current HCM calculator is still tied to
validated example paths and proposes a safe staged path toward broader manual
inputs. It is documentation-only: no calculation behavior is broadened here.

## Executive Summary

The product presents four calculator workflows, but their generality differs by
facility type.

- **Two-Lane Segment** is the most user-input driven today. It exposes segment
  type, geometry, traffic, terrain, and optional horizontal-curve inputs, but
  Chapter 15 vertical and horizontal behavior is still guarded by validated
  combinations and fixture-backed scope decisions.
- **Two-Lane Facility** remains template-backed. It is explicitly anchored to
  Chapter 26 Example Problems 3 and 4, with selected editable traffic and speed
  values merged into fixed facility contexts.
- **Multilane Segment** exposes worksheet fields but the engine rejects any
  deviation from Chapter 26 Example Problem 4 eastbound/westbound inputs. The
  helper formulas are partially general, but validation enforces exact fixtures.
- **Basic Freeway Segment** has the broadest engine implementation among the
  non-two-lane methods. The engine supports measured and estimated FFS, general
  level/rolling terrain PCEs, speed and capacity adjustment factors, and a range
  of freeway geometry inputs. The UI still labels the workflow as Example 1
  anchored, and validation coverage is centered on one Chapter 26 case plus
  guardrail/unit tests.

Recommended first calculator to generalize: **Basic Freeway Segment**, because
its engine already supports more than the single validation fixture and has
explicit physical-value and unsupported-scope validation. The safest immediate
work is still wording cleanup first, followed by non-example tests before any
public scope expansion.

## Workflow Audits

### Two-Lane Segment

**Current supported calculation scope**

- One segment, HCM7 Chapter 15 motorized vehicle LOS, independent of Streamlit.
- Segment types: Passing Constrained, Passing Zone, and Passing Lane.
- Level terrain for general straight paths within currently implemented length
  bounds.
- Mountainous terrain only where vertical scope classification returns
  supported.
- Horizontal-curve support is available only through the currently validated
  Example Problem 2-shaped path.
- Passing Lane single-segment output excludes downstream and facility-wide
  effects.

**Current inputs exposed in UI**

- Unit system.
- Segment type.
- Terrain type.
- Horizontal alignment.
- Segment length.
- Posted speed / base speed.
- Lane width.
- Shoulder width.
- Access point density.
- Grade percent when mountainous terrain is selected.
- Analysis-direction volume.
- Peak hour factor.
- Heavy-vehicle percent.
- Opposing-direction volume for Passing Zone.
- Optional horizontal-curve setup and subsegment table when horizontal curves
  are selected.
- Project load/save and export/report controls.

**Inputs hidden or constrained because of example-backed paths**

- Upstream passing-lane context is not exposed.
- Downstream/facility passing-lane effects are not exposed in the single-segment
  workflow.
- Grade length is not independently exposed; the adapter maps grade length to
  segment length.
- Vertical class is not a free manual input; it is derived and guarded.
- Non-level Passing Zone and most non-level Passing Lane paths are not exposed
  as supported manual inputs.
- General horizontal-curve combinations outside validated paths are accepted by
  UI controls but rejected by scope guards.
- General Chapter 15 grade-length table coverage is not exposed.

**Adapter-level guards**

- `build_manual_segment_inputs()` requires numeric geometry, traffic, and
  grade inputs, normalizes unit-system values, restricts terrain to level or
  mountainous, and restricts horizontal alignment to straight or
  horizontal_curves.
- Passing Zone requires opposing-direction volume.
- The adapter delegates scope enforcement to the Chapter 15 method rather than
  duplicating formulas.

**Engine-level limitations**

- `calculate_single_segment()` parses one facility-style segment and calls
  `_validate_single_segment_scope()` / `require_supported_vertical_scope()`.
- Non-level support depends on vertical lookup records and validation metadata.
- Grade length must equal segment length in current supported scope.
- Non-level behavior is validated only at 8% heavy vehicles unless a
  manual-single-segment validation fixture exists.
- Passing Lane is limited to Class 1 at 8% heavy vehicles.
- General non-level horizontal-curve behavior is outside validated manual scope.
- Full arbitrary Chapter 15 coverage, upstream passing lanes, and downstream
  facility effects are not implemented in this workflow.

**Validation fixture coverage**

- Chapter 26 Two-Lane Example Problems 1 and 2 cover level Passing Constrained
  straight and horizontal-curve paths.
- Example Problems 3 and 4 provide facility-backed behavior, including selected
  Passing Lane, Passing Zone, downstream, and mountainous segments.
- Vertical fixture infrastructure includes at least one runtime-validated
  backfill path for a manual single-segment mountainous combination, plus
  placeholder/template infrastructure for future cases.

**Can safely become general manual input now**

- Wording can describe the workflow as a calculator with validation-backed
  guardrails instead of an example viewer.
- Existing exposed level-terrain fields can remain manual, as long as
  unsupported combinations continue to fail with auditable messages.
- Project/export/report behavior can continue unchanged for currently accepted
  manual inputs.

**Requires new methodology implementation**

- Independent grade length and grade transition handling.
- Broader vertical class lookup coverage from HCM tables.
- Upstream passing-lane context in single-segment analysis.
- Downstream passing-lane effects outside facility analysis.
- General non-level horizontal-curve behavior.

**Requires new validation cases before exposing**

- Non-level heavy-vehicle percentages other than the current validated 8% paths.
- Non-level Passing Zone single-segment paths.
- Passing Lane vertical classes other than Class 1 and heavy-vehicle
  percentages other than 8%.
- Horizontal-curve inputs outside the Example Problem 2-shaped path.
- Any newly implemented grade-length or upstream/downstream context paths.

### Two-Lane Facility

**Current supported calculation scope**

- Template-backed HCM7 Chapter 15 facility workflow.
- Chapter 26 Example Problem 3: five-segment level facility context.
- Chapter 26 Example Problem 4: six-segment mountainous facility context.
- Facility-level and segment-level outputs, project save/load, and
  export/reporting for the guarded templates.

**Current inputs exposed in UI**

- Unit system.
- Defaults selector for Example 3 or Example 4 starting values.
- Fixed-row segment table.
- Editable fields differ by template:
  - Example 3: segment names, lengths, posted speeds, directional volumes, PHF,
    and heavy-vehicle percentages.
  - Example 4: segment names, posted speeds, analysis-direction volumes, and
    PHF.
- Read-only table fields include segment type, terrain, grade, alignment,
  passing-lane placement, downstream context, and other locked context.

**Inputs hidden or constrained because of example-backed paths**

- Number of segments is fixed by selected template.
- Segment sequence is fixed by selected template.
- Passing-lane placement and downstream context are locked.
- Upstream passing lane is forced false.
- Arbitrary facility length is derived from locked/edited segment lengths.
- Arbitrary curves, grades, vertical classes, and grade lengths are locked.
- Arbitrary facility layouts and arbitrary nonlevel combinations are not
  exposed.

**Adapter-level guards**

- `build_manual_facility_inputs()` loads the selected fixture, validates the row
  count, and merges only whitelisted editable fields.
- `_validate_locked_context()` rejects edits to locked fields and rejects manual
  downstream adjustment.
- Unknown template IDs are rejected.
- Facility project load rejects unknown templates and malformed or unsupported
  segment rows.

**Engine-level limitations**

- `calculate()` accepts only case IDs `TLH-CH15-003` and `TLH-CH15-004` for
  facility analysis.
- `_validate_facility_example_scope()` enforces exact segment count, sequential
  IDs, fixed segment-type sequence, no upstream passing lane, and segment
  lengths summing to facility length.
- Example 3 is level and straight only.
- Opposing flow is accepted only for Passing Zone segments.
- Horizontal subsegments must match segment lengths and valid curve rows.
- Vertical scope is allowed in facility context only through existing validated
  example paths.

**Validation fixture coverage**

- `references/example_inputs.yaml` contains `TLH-CH15-003` and
  `TLH-CH15-004`.
- Unit tests cover manual facility adapter behavior, project round trips,
  reporting, downstream passing-lane adjustment, and guarded scope.
- The fixture coverage validates the current templates, not arbitrary facility
  design.

**Can safely become general manual input now**

- No facility methodology broadening should be claimed yet.
- Wording can be cleaned to say the facility worksheet is a guarded calculator
  mode with fixture-backed defaults.
- Segment name and already-whitelisted edits can remain manual.

**Requires new methodology implementation**

- Arbitrary segment sequences and segment counts.
- Manual upstream passing-lane context.
- Manual downstream passing-lane context.
- General facility aggregation rules beyond the fixed examples.
- General nonlevel facility behavior and mixed curve/grade handling.

**Requires new validation cases before exposing**

- Additional level facility sequences.
- Passing-lane placement variations.
- Downstream adjustment cases at different locations/distances.
- Nonlevel facility cases with grades, curves, and heavy-vehicle percentages
  outside Example 4.
- Facility save/load/report regression tests for any broadened schema.

### Multilane Segment

**Current supported calculation scope**

- HCM7 Chapter 12 Multilane Highway basic segment path.
- Chapter 26 Example Problem 4 eastbound and westbound only.
- One direction, one segment, basic segment analysis.
- Engine-native Imperial calculations with Metric display conversions.

**Current inputs exposed in UI**

- Unit system.
- Defaults selector for Example 4 eastbound/westbound starting values.
- Number of lanes.
- Segment length.
- Posted speed limit.
- Lane width.
- Roadside lateral clearance.
- Access point density.
- Demand volume.
- Peak hour factor.
- Heavy-vehicle percent.
- Grade percent.
- Project load/save and export/report controls.

**Inputs hidden or constrained because of example-backed paths**

- Facility type and analysis type are fixed to multilane basic segment.
- Direction is tied to template.
- Truck mix is fixed to the default 30% SUT / 70% TT mix.
- Median type is fixed to TWLTL.
- Base/free-flow speed inputs and driver population factors are rejected.
- Facility/corridor, ramp, weaving, merge/diverge, managed lanes, work zones,
  and reliability inputs are rejected.
- Although the UI fields are editable, any deviation from the exact Example 4
  EB/WB values is rejected by validation.

**Adapter-level guards**

- Template ID must be `MLH-CH26-004-EB` or `MLH-CH26-004-WB`.
- Unit system is restricted to Metric or Imperial.
- UI inputs are converted to engine-native Imperial and merged over the selected
  template.
- Project load/save is guarded by template IDs and normalized engine inputs.

**Engine-level limitations**

- `validate_inputs()` enforces exact Example Problem 4 values for direction,
  lanes, length, demand, PHF, heavy vehicles, truck mix, grade, speed, lane
  width, roadside clearance, median type, and access points.
- `estimate_base_free_flow_speed()` supports only the posted-speed-below-50
  branch.
- `total_lateral_clearance()` supports only the TWLTL clearance rule.
- PCE lookup supports only Example 4 grade length, heavy-vehicle percentage,
  truck mix, upgrade, and downgrade.
- `mean_speed_below_breakpoint()` supports only the flow-below-breakpoint
  branch.
- Access point density is limited to the implemented Exhibit 12-24 range.

**Validation fixture coverage**

- `references/multilane_example_inputs.yaml` contains only Example 4 EB and WB.
- Tests cover the two examples, exact-scope rejection, unsupported workflow keys,
  physical value validation, helper formulas, project I/O, reporting, and UI
  grammar.
- There are no non-example positive validation cases.

**Can safely become general manual input now**

- Nothing should be publicly broadened yet because exact-scope validation
  rejects all non-example combinations.
- Wording can be cleaned up to avoid presenting editable controls as generally
  supported.
- Internal helper tests can be expanded around already implemented formula
  helpers before removing exact-example guards.

**Requires new methodology implementation**

- General PCE lookup/interpolation for Exhibit 12-26 across grade, length,
  heavy-vehicle percentage, and truck mix.
- Posted-speed-at-or-above-50 base-FFS branch or measured/base FFS support if
  required by the chosen UI model.
- Median/left-clearance behavior beyond TWLTL.
- Speed-flow branch above the 1,400 pc/h/ln breakpoint.
- Capacity and LOS behavior for broader FFS and demand ranges if not already
  fully covered by helper functions.

**Requires new validation cases before exposing**

- At least one non-Example-4 basic segment with different access density,
  demand, PHF, heavy vehicles, and lane/clearance values.
- Posted-speed branch coverage at and above 50 mi/h.
- PCE table/interpolation cases for upgrade, downgrade, and level grades.
- Flow above the breakpoint and near capacity.
- Guardrail cases for unsupported facility/corridor and interchange workflows.

### Basic Freeway Segment

**Current supported calculation scope**

- HCM7 Chapter 12 Basic Freeway Segment, one direction, one segment,
  uninterrupted flow, general-purpose lanes.
- Measured FFS and estimated FFS branches are implemented.
- Estimated FFS includes lane width, right-side lateral clearance, and total
  ramp density terms.
- General-terrain level and rolling PCEs are implemented.
- Speed adjustment factor and capacity adjustment factor are implemented.
- LOS, capacity checks, speed-flow relationship, and audit outputs are
  implemented.

**Current inputs exposed in UI**

- Unit system.
- Preset selector for `BF-CH26-001` starting values.
- Number of lanes.
- Segment length.
- FFS source: measured or estimated from geometry.
- Measured free-flow speed, when measured FFS is selected.
- Base free-flow speed, lane width, right-side lateral clearance, and ramp
  density when estimated FFS is selected.
- Demand volume.
- Peak hour factor.
- Heavy-vehicle percent.
- Terrain type.
- Speed adjustment factor.
- Capacity adjustment factor.
- Project load/save and export/report controls.

**Inputs hidden or constrained because of example-backed paths**

- Facility type is fixed to Basic Freeway.
- Analysis type is fixed to basic segment.
- Truck mix is fixed to the default 30% SUT / 70% TT mix.
- Driver population factor is fixed to 1.0 and user-supplied driver population
  inputs are rejected.
- Specific-grade and mountainous PCE inputs are rejected.
- Multilane access-point density, median, and left/total lateral clearance
  fields are rejected.
- Ramp influence is represented only by total ramp density for FFS estimation;
  ramp, merge, diverge, weaving, managed-lane, work-zone, reliability, and
  facility/corridor workflows are rejected.

**Adapter-level guards**

- Preset ID must be `BF-CH26-001`.
- Unit system is restricted to Metric or Imperial.
- UI conversion branches depend on measured versus estimated FFS.
- Project load/save is guarded by preset ID and normalized engine inputs.
- The adapter merges worksheet values over the fixture preset, so hidden fields
  remain fixture-derived unless explicitly replaced by exposed controls.

**Engine-level limitations**

- `reject_unsupported_scope_keys()` rejects out-of-scope workflow keys,
  unsupported input keys, and unrecognized inputs.
- `validate_inputs()` allows at least two lanes, positive segment length and
  volume, PHF in `(0, 1]`, heavy vehicles in `[0, 100]`, SAF/CAF in `(0, 1]`,
  Basic Freeway facility type, basic segment analysis type, default truck mix,
  level/rolling terrain, and measured/estimated FFS.
- Estimated FFS requires base FFS, lane width, right-side lateral clearance, and
  total ramp density.
- Lane width below 10 ft, right-side clearance above 10 ft, total ramp density
  outside 0 to 6 ramps/mi, adjusted FFS outside 55 to 75 mi/h, specific grades,
  and mountainous terrain are unsupported.
- Driver population factor is hard-coded to 1.0.

**Validation fixture coverage**

- `references/freeway_example_inputs.yaml` contains only `BF-CH26-001`.
- Unit tests cover Example 1, model validation, method helpers, guardrails,
  project I/O, reporting, manual adapter behavior, and export behavior.
- Positive published validation coverage is still one Chapter 26 case.

**Can safely become general manual input now**

- Basic Freeway can be the first candidate for broader manual-input tests
  because the engine already accepts more than the exact fixture in its
  validation layer.
- Wording can stop implying only the Example 1 values are supported, after
  adding non-example tests for measured FFS, estimated FFS, level and rolling
  terrain, SAF/CAF changes, and capacity-exceeding conditions.
- The existing project/export/report schema can remain stable while documenting
  the broader accepted input envelope.

**Requires new methodology implementation**

- Driver population factor input and related adjustments.
- Specific-grade and mountainous freeway PCE tables.
- Freeway facility/corridor analysis.
- Ramp, merge/diverge, weaving, managed lanes, work zones, and reliability.
- Any methodology beyond Basic Freeway Segment one-direction, one-segment
  uninterrupted flow.

**Requires new validation cases before exposing**

- Non-example measured FFS case.
- Non-example estimated FFS case with varied lane width, clearance, and ramp
  density.
- Rolling terrain PCE case.
- SAF/CAF cases below 1.0.
- Near-capacity and demand-exceeds-capacity cases.
- Published or independently reviewed expected outputs for each newly claimed
  public scope.

## User-Facing Wording Inventory

The following wording still frames the product or workflows as example-tied,
validated-path-only, or constrained to preserve examples. These should be
cleaned up before broader generalization is claimed.

### README.md

- Mentions validation against HCM Chapter 26 example problems before expanding
  UI or production workflows.
- Lists Two-Lane Example Problems 1 through 4, Multilane Example Problem 4, and
  Basic Freeway Example Problem 1 as current validation evidence.
- Says general Multilane Highway LOS beyond Chapter 26 Example Problem 4 is not
  in scope.
- Says the CLI currently supports validated example fixtures only.
- Describes the Streamlit app as a validated-case viewer in one launch section.
- Describes Manual Facility as anchored to validated Example Problems 3 and 4.
- Describes Manual Multilane as a limited validated-path worksheet anchored only
  to Example Problem 4 EB/WB.
- Describes Manual Basic Freeway as bounded to the implemented Chapter 12 Basic
  Freeway Segment envelope; BF-CH26-001 remains optional defaults and
  regression evidence.
- Uses phrases such as "validated path", "validated template",
  "example-backed", "guarded Example 3/4", "implemented-example-only", and
  "exact validated templates".

### docs/supported_workflows.md

- Two-Lane Highway lists "validated Chapter 26 example-backed paths where
  available".
- Multilane lists "Chapter 26 Example 4 EB/WB-compatible validated path".
- Basic Freeway lists bounded Chapter 12 one-direction, one-segment
  uninterrupted-flow analysis and Chapter 26 Example 1 optional defaults.
- Validation evidence is correctly positioned as regression/reference evidence,
  but this still needs to remain separate from user-facing workflow claims.

### src/hcmcalc/ui/supported_workflows.py

- Supported Workflow sections include "validated Chapter 26 example-backed
  paths", "Example 3 and 4 facility-backed starting values", "Example 4
  EB/WB-compatible validated path"; Basic Freeway now lists bounded Chapter 12
  segment analysis and Example 1 optional defaults.

### src/hcmcalc/ui/manual_facility.py

- Template labels are "Chapter 26 Example 3 starting values" and "Chapter 26
  Example 4 starting values".
- Supported context and locked summaries explicitly refer to selected validated
  templates and Example Problem 4 context.
- Unsupported notes say arbitrary segment sequences and arbitrary nonlevel
  facilities are unsupported.

### src/hcmcalc/ui/manual_multilane.py

- Template labels are "Chapter 26 Example 4 - Eastbound/Westbound starting
  values".
- Limitations say the worksheet is limited to Example Problem 4 EB/WB-compatible
  validated paths and is not a general Multilane Highway calculator.

### src/hcmcalc/ui/manual_freeway.py

- Preset label is "Chapter 26 Example 1 starting values".
- Limitations say the workflow is bounded to the implemented Basic Freeway
  Segment v0.1 envelope and preserves only that bounded workflow.
- Audit support status is `supported_basic_freeway_segment_v0_1`.

### src/hcmcalc/ui/streamlit_app.py

- Facility copy says Example 3/4 references back defaults and that projects
  remain guarded to the selected validation basis.
- Single Segment validation basis says "HCM7 Chapter 26 Two-Lane Highway
  example-backed checks for implemented Chapter 15 paths."
- Facility validation basis says "HCM Chapter 26 Two-Lane Highway Example
  Problem 3/4" and "Guarded Example 3/4 facility paths".
- Multilane and Basic Freeway result panels carry validation basis copy tied to
  Chapter 26 example-backed checks and guarded paths.

### Engine and Audit Output Wording

- `src/hcmcalc/multilane/method.py` warnings, support status, scope status, and
  unsupported notes say Example Problem 4 only.
- `src/hcmcalc/multilane/validation.py` rejects all non-exact Example 4 inputs.
- `src/hcmcalc/freeway/method.py` warning describes the bounded Chapter 12
  Basic Freeway Segment scope and treats Example Problem 1 as regression
  evidence.
- `src/hcmcalc/methods/two_lane_highway_ch15.py` assumptions and warnings
  reference Example Problems 1 through 4 and validated vertical paths.

## Staged Methodology Roadmap

### Phase 1: Wording Cleanup Only

Goal: present the app as a calculator with validation-backed scope, not an
example viewer, while preserving all current guards.

Work:

- Update user-facing copy in README, Supported Workflows, Streamlit validation
  basis sections, and UI adapter limitation strings.
- Replace "Example-compatible validated path" wording with "currently supported
  input envelope" where the engine actually supports more than one fixture.
- Keep explicit "validation evidence" language for fixtures and tests.
- Do not change formulas, inputs accepted by engines, project JSON semantics,
  export/report behavior, or fixtures.

Acceptance criteria:

- Formulas unchanged unless explicitly implementing a documented method: no
  calculation-code changes in this phase.
- Tests for non-example input combinations: not required for wording-only
  changes, but existing guardrail tests must remain green.
- Validation/error handling for unsupported combinations: unchanged.
- Audit output remains clear: no audit fields removed.
- Report/export remains stable: no schema or output format changes.

### Phase 2: Multilane Segment Generalization

Goal: turn Multilane from exact Example 4 validation into a documented basic
segment input envelope.

Work:

- Decide the first general Multilane input envelope: likely basic segment,
  one direction, no ramps/weaving/facility, default truck mix, documented
  median/clearance assumptions.
- Implement or document the missing HCM Chapter 12 branches before relaxing
  exact-scope validation.
- Add PCE table/interpolation coverage beyond the two Example 4 values.
- Add speed-flow branch coverage above the breakpoint if exposed.
- Add non-example positive tests before any UI copy says general manual input.

Acceptance criteria:

- Formulas unchanged unless explicitly implementing documented HCM Chapter 12
  branches with source references.
- Tests for non-example input combinations include at least one positive case
  outside Example 4 EB/WB and boundary/error tests for unsupported fields.
- Validation/error handling clearly rejects ramps, weaving, merge/diverge,
  managed lanes, reliability, and facility/corridor workflows.
- Audit output identifies assumptions, table branches, intermediate values, and
  source references for the generalized path.
- Report/export remains stable for existing `manual_multilane_v0` project and
  report payloads, or a schema migration is documented and tested.

### Phase 3: Basic Freeway Segment Generalization

Goal: publicly align Basic Freeway wording and tests with the broader v0.1
engine envelope that already exists.

Status: Phase 3 wording and positive non-example smoke coverage began in
`basic-freeway-generalization-phase-1`. The branch keeps formulas, input
contracts, fixtures, project JSON type, and unsupported-scope guardrails
unchanged.

Work:

- Add non-example positive tests for measured FFS, estimated FFS, rolling
  terrain, SAF/CAF below 1.0, and near-capacity/demand-exceeds-capacity cases.
- Decide whether the preset remains optional starting values or becomes a
  simple "Reset to example defaults" control.
- Reword UI limitations from "Example 1-compatible path" to the documented
  Basic Freeway Segment v0.1 input envelope.
- Keep specific-grade, mountainous, driver-population, ramp, weaving,
  merge/diverge, managed-lane, work-zone, reliability, and facility/corridor
  paths guarded.

Acceptance criteria:

- Formulas unchanged unless adding documented missing Basic Freeway Segment
  methods.
- Tests for non-example input combinations cover both measured and estimated
  FFS branches and at least one non-level general terrain value that is already
  supported.
- Validation/error handling rejects unsupported specific-grade, driver
  population, and non-basic-segment inputs with clear messages.
- Audit output remains clear about FFS source, SAF, CAF, PCE, demand/capacity,
  and unsupported scope notes.
- Report/export remains stable for saved projects and generated reports.

### Phase 4: Two-Lane Facility Generalization

Goal: move from fixed Example 3/4 facility templates toward documented general
facility editing only after methodology and validation catch up.

Work:

- Define the smallest general facility envelope, such as level straight
  facilities with configurable segment count and segment sequence, before
  mountainous or curve support.
- Separate "facility template defaults" from "facility schema" so project JSON
  can represent arbitrary supported segment rows without pretending all
  examples are supported.
- Implement method support for arbitrary segment sequences and passing-lane
  downstream context only when HCM methodology is mapped and tested.
- Add validation fixtures for every newly claimed facility behavior.

Acceptance criteria:

- Formulas unchanged unless implementing a documented Chapter 15 facility
  method branch.
- Tests for non-example input combinations include positive level-facility
  cases and negative unsupported facility layouts.
- Validation/error handling rejects unsupported passing-lane placement,
  downstream context, nonlevel/curve combinations, and malformed segment
  sequences.
- Audit output remains clear at both segment and facility levels.
- Report/export remains stable, including segment table outputs and project
  round trips.

### Phase 5: Additional Validation Cases and QA References

Goal: expand confidence and traceability before broad public scope claims.

Work:

- Inventory published HCM Chapter 26 cases and any additional reviewed
  engineering examples by facility type.
- Convert candidate examples into fixture files with input mappings, expected
  outputs, tolerances, source references, and reviewer notes.
- Add regression tests that compare engine outputs and intermediate values
  against fixtures.
- Keep validation evidence accessible as internal QA/reference material rather
  than primary product navigation.

Acceptance criteria:

- Formulas unchanged unless tied to a documented method implementation.
- Tests include positive fixtures, regression tests, and negative unsupported
  combinations for each broadened path.
- Validation/error handling explains whether a failure is invalid input,
  unsupported methodology, missing HCM table data, or missing validation
  fixture.
- Audit output links assumptions and intermediate values to source references.
- Report/export remains stable and continues to include enough context for
  independent review.

## Cross-Cutting Guardrails

- Do not broaden UI claims before engine validation and tests prove the broader
  input envelope.
- Keep calculation modules independent from Streamlit and all UI frameworks.
- Preserve fixtures as regression/reference evidence even when UI wording is
  cleaned up.
- Preserve project JSON semantics unless a deliberate schema migration is
  documented and tested.
- Preserve report/export behavior unless a deliberate versioned change is
  documented and tested.
- Prefer adding new validation fixtures and method-level tests before removing
  any exact-example guard.
- Keep unsupported-scope errors explicit enough to distinguish invalid input,
  missing HCM table data, missing implementation, and missing validation.
