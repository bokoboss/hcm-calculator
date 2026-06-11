# Chapter 15 Vertical Class and Grade-Length Methodology Map

## A. Purpose

This document prepares the Chapter 15 Two-Lane Highway method for broader
vertical class and grade-length support. It audits the current implementation,
separates implemented behavior from validated behavior, identifies missing
methodology data, and recommends a safe implementation sequence.

This document does not add methodology support, authorize new calculation
paths, or establish that any combination beyond the existing validation
fixtures is correct.

### Phase 1 unsupported-scope guardrails

Explicit vertical-scope guardrails are now applied before calculation. The
scope decision classifies a combination as `supported`, `unsupported`,
`unsupported_needs_hcm_table_data`, or
`unsupported_needs_validation_fixture`. Unsupported combinations are rejected
instead of being approximated or allowed to fall back to level assumptions.

These guardrails do not add broader vertical-class or grade-length support.
Future expansion still requires reviewed HCM grade-length table/coefficient
data and independent validation fixtures before a new calculation path can be
enabled.

### Phase 2 lookup structure

Typed, source-attributed lookup structures and pure lookup helpers now exist
for future table-driven vertical-class support. The placeholder records contain
metadata only for existing validated Example Problem 4 paths.

No HCM table values or coefficients have been added, and no new vertical-class
support has been enabled. The production scope checker and calculation formulas
remain unchanged. Future PRs should populate the structure only with verified
HCM data and validation fixtures before connecting any new path to production
calculations.

## B. Current Implementation Summary

### Level terrain

- The manual worksheet's `terrain_type="level"` selection normalizes
  `grade_percent` to `0.0`. The engine model now parses `terrain_type`,
  `grade_length_mi`, and an optional submitted `vertical_class` for explicit
  scope classification and guardrails. These fields are not used directly in
  calculation formulas.
- `vertical_alignment_class()` returns vertical Class 1 for a `0%` grade when
  the segment length is from `0.25` through `3.0 mi`.
- Level, straight Passing Constrained, Passing Zone, and Passing Lane paths
  exist. The level reliability matrix broadens regression coverage, but the HCM
  Chapter 26 validation basis remains Example Problems 1 through 3.
- Manual Passing Lane remains limited to Class 1 and exactly `8%` heavy
  vehicles.
- The only manual horizontal-curve path is the level Passing Constrained,
  11-subsegment Example Problem 2 structure.

### Current mountainous and example-problem paths

The grade-length-to-vertical-class decision is a hard-coded subset of HCM
Exhibit 15-11:

| Grade and length | Derived vertical class | Validation basis |
| --- | ---: | --- |
| `4% / 1.3 mi` | 4 | Chapter 26 Example Problem 4 |
| `6% / 0.5 mi` | 4 | Chapter 26 Example Problem 4 |
| `6% / 1.0 mi` | 5 | Chapter 26 Example Problem 4 |

The Example Problem 4 facility path validates these combinations at `8%` heavy
vehicles in its exact six-segment facility context. Some combinations include
horizontal curves and downstream Passing Lane effects. Nonlevel manual
single-segment support is explicitly guarded: Passing Constrained is limited to
the exact mapped grade-length pairs at `8%` heavy vehicles, and nonlevel Passing
Zone is rejected pending an independent validation fixture. Exact grade-length
pairs do not establish broad methodology validation or authorize other
nonlevel inputs.

### Downgrade Class 1 path

- `-3% / 0.5 mi` maps to vertical Class 1.
- Chapter 26 Example Problem 4 validates that downgrade for one Passing Lane
  segment and one Passing Constrained segment, both straight and at `8%` heavy
  vehicles.
- The manual single-segment path permits the exact downgrade for Passing
  Constrained and Passing Lane only at `8%` heavy vehicles. Nonlevel Passing
  Zone is rejected pending an independent validation fixture.
- No other downgrade grade-length pair is supported.

### Other current vertical class behavior

- Class-indexed coefficient dictionaries exist for Classes 1, 4, and 5 for
  heavy-vehicle free-flow-speed adjustment, average speed, and percent
  followers.
- Passing Lane coefficient dictionaries and Passing Lane lane-level capacity
  are implemented only for Class 1.
- No complete grade-length classification table is present. A metadata-only
  boundary lookup structure now exists but is not connected to production
  scope classification or calculations.
- No generic `terrain_type`-to-class calculation exists. Terrain type is parsed
  into the engine model and used by scope guardrails, but vertical class is
  still derived from normalized grade and grade length for formulas.

## C. Current Input Fields Related to Vertical Alignment

| Field | Current meaning and use |
| --- | --- |
| `terrain_type` | Manual UI/adapter field with values `level` or `mountainous`. `level` forces normalized `grade_percent` to `0.0`; `mountainous` requires a submitted grade. It is parsed into the method-owned engine segment model for scope classification and guardrails, but is not used directly in formulas. |
| `grade_percent` | Signed engine input used with `segment_length_mi` to derive `vertical_class`. Positive values represent the implemented upgrade examples; `-3.0` is the only implemented downgrade. Manual level terrain overwrites a submitted grade with `0.0`. |
| `grade_length_mi` | Parsed engine-model scope input. The currently supported contract requires it to equal the full `segment_length_mi`; a different or missing nonlevel grade length is rejected because grade-transition methodology is not implemented. |
| `vertical_class` | Normally a derived intermediate value and output. An optional submitted value may be parsed for scope validation and must match the guarded grade-length mapping. The derived class selects class-indexed coefficients for formulas. |
| `heavy_vehicle_percent` | Engine input used in free-flow speed, average speed, percent followers, and Passing Lane lane-allocation calculations. Level Passing Constrained and Passing Zone accept `0%` through `100%`. Guarded nonlevel manual paths and all manual Passing Lane paths are limited to exactly `8%`; other nonlevel percentages require validation fixtures. |
| `segment_type` | Selects Passing Constrained, Passing Zone, or Passing Lane calculation paths. Passing Lane has Class 1-only coefficient/capacity limitations and an `8%` manual guard. |
| `horizontal_alignment` | Selects `straight` or `horizontal_curves`. Manual curves are restricted to the level Passing Constrained Example Problem 2 structure. The Example Problem 4 facility fixture includes Class 4 and Class 5 curve interactions, but this is not a general manual curve path. |
| `segment_length_mi` | Serves both as segment length and current grade length. It is also used directly by class-specific speed and percent-followers equations. Vertical classification currently accepts level lengths only from `0.25` through `3.0 mi` and exact nonlevel pairs. |
| `opposing_direction_volume_veh_h` | Required only for a manual Passing Zone segment. Passing Constrained uses the fixed `1,500 veh/h` assumption. Opposing flow is used by heavy-vehicle and speed/percent-followers calculations, so its treatment affects grade-specific results. |
| `posted_speed_mph` | Converted to base free-flow speed, then used by class-specific heavy-vehicle and speed calculations. |
| `horizontal_alignment_subsegments` | Structured tangent/curve data used by narrowly scoped horizontal-curve paths. It can interact with mountainous vertical classes in Example Problem 4 facility calculations. |
| `unit_system` | UI/adapter field. Metric lengths and speeds are converted to the engine's Imperial-native inputs before vertical classification and calculation. Grade percent is dimensionless and is not converted. |
| `case_id` | Facility fixture discriminator. It restricts facility analysis to exact Example Problem 3 or 4 shapes, but it is not used by the public single-segment calculation contract. |
| `upstream_passing_lane` | Facility-context input used to restrict the validated examples and support downstream effects. It does not change vertical classification directly. |

## D. Supported Combinations

"Implemented, narrowly validated" means the combination has Chapter 26 fixture
coverage only in the stated example context. "Implemented, not independently
validated" means current guards and coefficient maps allow the path, but the
repository does not contain a validation fixture establishing broader
methodology correctness.

| Terrain type | Segment type | Grade percent | Grade length | Vertical class | Heavy vehicle percent | Source / validation basis | Status | Notes |
| --- | --- | ---: | --- | ---: | --- | --- | --- | --- |
| Level | Passing Constrained | `0%` | `0.25-3.0 mi` | 1 | Manual accepts `0-100%` | Chapter 26 Examples 1-3; level reliability matrix | Implemented; validated baseline is example-scoped | Straight supported; manual curves only through exact Example Problem 2 structure. |
| Level | Passing Zone | `0%` | `0.25-3.0 mi` | 1 | Manual accepts `0-100%` | Chapter 26 Example 3; level reliability matrix | Implemented; validated baseline is example-scoped | Requires actual opposing-direction volume. |
| Level | Passing Lane | `0%` | `0.25-3.0 mi` | 1 | Exactly `8%` manually | Chapter 26 Example 3; level reliability matrix | Implemented, narrowly validated | Manual result excludes downstream/facility effects. |
| Mountainous | Passing Constrained | `4%` | `1.3 mi` | 4 | Exactly `8%` on guarded nonlevel manual path | Chapter 26 Example 4 | Implemented, narrowly validated at fixture inputs | Facility fixture includes horizontal-curve variants; manual mountainous curves are rejected. |
| Mountainous | Passing Constrained | `6%` | `0.5 mi` | 4 | Exactly `8%` on guarded nonlevel manual path | Chapter 26 Example 4 | Implemented, narrowly validated at fixture inputs | Fixture path is straight. |
| Mountainous | Passing Constrained | `6%` | `1.0 mi` | 5 | Exactly `8%` on guarded nonlevel manual path | Chapter 26 Example 4 | Implemented, narrowly validated at fixture inputs | Facility fixture includes a horizontal curve; manual mountainous curves are rejected. |
| Mountainous | Passing Constrained | `-3%` | `0.5 mi` | 1 | Exactly `8%` on guarded nonlevel manual path | Chapter 26 Example 4 | Implemented, narrowly validated at fixture inputs | Only implemented downgrade pair. |
| Mountainous | Passing Zone | Any nonlevel pair | Any | Any | Any | No direct Chapter 26 fixture for a nonlevel Passing Zone | Explicitly unsupported pending validation fixture | Phase 1 guardrails reject this path before calculation. |
| Mountainous | Passing Lane | `-3%` | `0.5 mi` | 1 | Exactly `8%` | Chapter 26 Example 4 | Implemented, narrowly validated | Only nonlevel Passing Lane pair; manual result excludes downstream/facility effects. |

## E. Unsupported Combinations

These combinations should remain rejected or explicitly unsupported until the
required HCM data and validation fixtures are available.

| Combination | Current reason to remain unsupported |
| --- | --- |
| Any nonlevel grade-length pair other than `-3% / 0.5 mi`, `4% / 1.3 mi`, `6% / 0.5 mi`, or `6% / 1.0 mi` | The complete grade-length-to-vertical-class mapping is absent and no validation fixtures exist. |
| Any vertical class not represented by the current class-indexed dictionaries | Required coefficients and validated calculation behavior are absent. |
| Any nonlevel manual path at a heavy-vehicle percentage other than exactly `8%` | Current nonlevel validation fixtures use `8%`; other percentages require independent validation fixtures before calculation. |
| Any nonlevel manual Passing Zone path | No independent nonlevel Passing Zone validation fixture exists, so the scope guardrail rejects it before calculation. |
| Passing Lane in vertical Class 4 or 5, or any other non-Class-1 path | Passing Lane speed, percent-followers, and lane-level capacity data are Class 1 only. |
| Manual Passing Lane at a heavy-vehicle percentage other than exactly `8%` | Current path is restricted to the validated example percentage. |
| Any downgrade other than `-3% / 0.5 mi` | No classification mapping or validation fixture exists. |
| General mountainous horizontal-curve single segments | Manual curve support is explicitly limited to level Passing Constrained Example Problem 2. |
| Grade transitions or a grade length different from the full segment length | `grade_length_mi` is parsed for scope validation, but the current calculation contract requires it to equal the full segment length because grade-transition methodology is not implemented. |
| Segment lengths outside `0.25-3.0 mi` for vertical classification | Current classifier rejects them; broader applicability has not been mapped. |
| Arbitrary mountainous Passing Constrained inputs claimed as validated | Exact mapped grade-length pairs execute only through guarded `8%` paths; only the Example Problem 4 inputs establish fixture validation. |
| Arbitrary mountainous multi-segment facilities or segment sequences | Facility calculations are restricted to the exact Example Problem 4 shape and context. |
| General passing-lane upstream/downstream interactions with new vertical classes | Downstream behavior is validated only through the existing facility example paths. |

## F. HCM Table / Coefficient Data Needed

Do not infer or interpolate missing values from the existing example paths.
Before broader support is implemented, the project needs an independently
reviewed methodology source for:

- The complete HCM Exhibit 15-11 grade-length-to-vertical-class decision data,
  including exact boundaries, inclusivity rules, upgrade/downgrade treatment,
  and applicability limits.
- Coefficient rows for every vertical class intended to be supported for the
  heavy-vehicle free-flow-speed adjustment. The repository currently contains
  Exhibit 15-12 rows only for Classes 1, 4, and 5.
- Coefficient rows for every intended vertical class for Passing Constrained
  and Passing Zone average-speed calculations. The repository currently
  contains relevant Exhibit 15-13 and 15-19 rows only for Classes 1, 4, and 5.
- Coefficient rows for every intended vertical class for percent followers at
  capacity and at 25% capacity. The repository currently contains relevant
  Exhibit 15-24 and 15-26 rows only for Classes 1, 4, and 5.
- Any class-specific auxiliary coefficients, minimum values, applicability
  ranges, and rounding rules needed by those equations.
- Passing Lane class-specific speed, percent-followers, and lane-capacity data
  beyond Class 1. Current Passing Lane maps reference Exhibits 15-14, 15-16,
  15-18, 15-20, 15-25, and 15-27 only for Class 1.
- Methodology for grade changes within a segment, if Chapter 15 requires grade
  length to differ from segment length or requires segmentation rules.
- Methodology and validation data for interactions among vertical class,
  horizontal curves, Passing Lane segments, and downstream facility effects.
- Source-backed valid domains for grade, grade length, heavy-vehicle
  percentage, speed, flow, and any interpolation or boundary behavior.

The exact names or numbers of additional HCM tables needed beyond those already
identified in current code comments are not established by repository files.
They must be confirmed from an authorized HCM source. HCM table contents should
not be copied into the repository unless licensing and project policy permit it.

## G. Implementation Risks

- Accidentally over-generalizing from the four Example Problem 4 grade-length
  pairs or treating a passing regression test as methodology validation.
- Mixing level-terrain assumptions with grade-specific behavior, especially
  because `terrain_type="level"` silently normalizes grade to zero.
- Applying heavy-vehicle adjustments outside a validated vertical class or
  input domain merely because a coefficient dictionary lookup succeeds.
- Confusing terrain type with vertical class. Terrain type is currently a UI
  interpretation field; vertical class is a derived engine decision.
- Extending Passing Lane calculations without the required class-specific
  coefficients, lane-capacity rules, and downstream/facility validation.
- Introducing unsupported Passing Lane downstream effects when expanding a
  single-segment path.
- Metric/Imperial conversion mistakes at grade-length boundaries. The engine
  uses Imperial miles and current nonlevel classification relies on exact
  floating-point grade-length pairs.
- Misrepresenting segment length as grade length when a future vertical profile
  contains grade transitions.
- Weak validation fixtures that confirm only final LOS while missing
  classification, heavy-vehicle adjustment, speed, percent followers, and
  audit-decision errors.
- Silent dictionary-key failures or accidental fallbacks when a derived class
  lacks coefficients for a downstream calculation step.
- Changing audit, project JSON, UI, or CLI contracts before the engine
  methodology and fixtures are stable.

## H. Recommended Phased Implementation

### Phase 1: Explicit unsupported-scope guardrails and documentation

- Make supported versus validated scope explicit at the engine boundary.
- Define terminology for terrain type, signed grade, grade length, segment
  length, vertical class, and vertical profile.
- Preserve clear rejection for every unmapped or unvalidated combination.
- Add no new formula behavior.

### Phase 2: Table data structure and lookup helpers

- A reviewed, source-attributed metadata structure now represents existing
  validated example paths without copying HCM table data or coefficients.
- Pure lookup helpers define explicit units, inclusivity rules, source metadata,
  input validation, and structured missing-data results.
- Lookup tests remain separate from production calculations and enable no new
  classes or calculation paths.

### Phase 3: One narrowly validated vertical class path

- Select one missing or incomplete grade-length/class path with an authoritative
  example or independently checked fixture.
- Add the classification data, required coefficient data, method-level tests,
  fixture test, and regression coverage for only that path.
- Keep Passing Lane and horizontal-curve interactions out unless the selected
  fixture specifically validates them.

### Phase 4: Expanded grade-length matrix

- Add additional classes and grade-length ranges incrementally.
- Cover every boundary, supported heavy-vehicle range, and unsupported gap.
- Add interaction tests only after each underlying path is independently
  validated.

### Phase 5: UI exposure after engine validation

- Expose only combinations that the engine can classify and calculate with
  validated methodology.
- Clearly distinguish terrain selection from derived vertical class and show
  grade-length applicability feedback.
- Preserve the single-page guided worksheet concept.

### Phase 6: Documentation and audit/reporting polish

- Record classification source, boundary decision, normalized units,
  assumptions, coefficient-set provenance, and unsupported-scope decisions.
- Update methodology, validation matrix, reports, and user-facing limitations
  after engine validation is complete.

## I. Validation Fixture Needs

Before broader support is implemented, add:

- At least one HCM example or independently checked case per vertical class and
  calculation path claimed as supported.
- Cases immediately below, at, and immediately above every grade-length
  boundary, including inclusive/exclusive boundary behavior.
- Upgrade and downgrade cases where their classification or coefficients
  differ.
- Multiple heavy-vehicle percentage cases per supported class, including
  boundaries and values that materially exercise the heavy-vehicle formulas.
- Metric and Imperial input cases that normalize to the same engine values,
  especially at grade-length boundaries.
- Unsupported-scope rejection cases for missing classes, missing coefficient
  sets, Passing Lane limitations, curve interactions, and facility context.
- Audit-trail cases that verify normalized inputs, signed grade, grade length,
  derived vertical class, classification source, selected coefficient set,
  assumptions, intermediate values, outputs, and warnings.
- Regression cases that verify new lookup data does not change existing Example
  Problems 1 through 4 or the level reliability matrix.

## J. Recommended Next PR

The next implementation PR should be narrow and test-first: add explicit
vertical-class lookup boundary data and pure lookup tests for one independently
validated, currently unsupported grade-length path, while leaving production
calculation routing disabled for that path.

That PR should include source attribution, unit and boundary rules, unsupported
lookup behavior, and validation fixtures before a later PR connects the new
class path to calculation formulas.
