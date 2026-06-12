# Chapter 15 Vertical Class and Grade-Length Methodology Map

## A. Purpose

This document prepares the Chapter 15 Two-Lane Highway method for broader
vertical class and grade-length support. It audits the current implementation,
separates implemented behavior from validated behavior, identifies missing
methodology data, and recommends a safe implementation sequence.

This document does not authorize new calculation paths or establish that any
combination beyond the existing validation fixtures is correct. HCM7 Chapter
15 Step 3 vertical alignment classification is now implemented independently
from downstream calculations.

### Step 4 free-flow speed estimation

HCM7 Chapter 15 Step 4 free-flow speed estimation is implemented as a
calculation-first helper using Eq. 15-2 through Eq. 15-6 and the complete
Exhibit 15-12 coefficient table for vertical Classes 1 through 5. The helper
validates its Step 4 inputs and exposes BFFS, the heavy-vehicle speed adjustment
coefficient, lane/shoulder adjustment, access-point adjustment, FFS, and source
references. Class 1 retains the Eq. 15-4 minimum coefficient behavior.

### Step 5 tangent average-speed estimation

HCM7 Chapter 15 Step 5 tangent/base average-speed estimation is implemented as
an auditable calculation helper using Eq. 15-7 through Eq. 15-11. The
coefficient tables in Exhibits 15-13 through 15-20 are table-driven for
vertical Classes 1 through 5 and separately select Passing Constrained/Passing
Zone or Passing Lane coefficients. The helper exposes the segment-length
coefficient `b3`, heavy-vehicle coefficient `b4`, slope coefficient `m`, power
coefficient `p`, tangent average speed, and source references.

This formula hardening does not expand horizontal-curve support, implement Step
6 percent followers, or broaden guarded public nonlevel, Passing Lane, or
facility calculation paths. Existing validated outputs and unsupported-scope
decisions remain in force.

### Step 8 follower-density estimation

HCM7 Chapter 15 Step 8 follower-density estimation is implemented through
validated, auditable helpers. Passing Constrained and Passing Zone segments use
Eq. 15-35. Supported Passing Lane cases reuse the existing Step 7 faster-lane
and slower-lane midpoint values and use Eq. 15-34, including separately
reported lane components.

The Step 8 helpers validate segment type, percent followers, demand flow,
average speed, and required Passing Lane midpoint values. They expose the
selected equation reference and formula while preserving existing follower
density output names. This hardening does not implement or change Step 9
downstream Passing Lane adjustment, change LOS thresholds, or broaden any
guarded nonlevel, horizontal-curve, Passing Lane, or facility path.

### Exhibit 15-11 classification lookup

The verified table from the supplied NCHRP/NAP Chapter 7 methodology document,
Step 3, Exhibit 15-11, is implemented as a table-driven lookup. The lookup:

- accepts segment length in miles and grade percent;
- infers upgrade or downgrade from signed grade, or accepts an explicit
  direction context for unsigned grade magnitude;
- applies lower-exclusive and upper-inclusive bins, including `<=0.1 mi`,
  `>0.1 to <=0.2 mi`, `<=1%`, and `>1% to <=2%`;
- returns the vertical class, matched length row, matched grade column,
  direction, and source reference.

Classification support is separate from calculation support. The existing
scope guardrails still reject unvalidated nonlevel FFS, speed, percent
followers, follower density, Passing Lane, downstream-adjustment, and facility
calculation paths. No downstream formulas or validated expected outputs changed.

The Phase 4
[Chapter 15 Vertical Fixture Inventory](ch15_vertical_fixture_inventory.md)
records the existing standalone and facility-only validation evidence, missing
fixtures, required verified data, and recommended test-first expansion order.
It does not add methodology support.

### Phase 4B data and fixture preparation

Non-runtime manifests, a fixture template, structural fixture validation, and
[vertical data ingestion guidelines](ch15_vertical_data_ingestion_guidelines.md)
now provide a controlled path for adding verified data later. No actual HCM
values or coefficients are populated, no placeholder is runtime enabled, and
placeholder data must not be used for calculation. Any future data must include
source attribution, expected outputs, tolerances, and explicit validation
status before implementation review.

The first validated schema backfill now represents the exact existing
`TLH-CH15-004` segment 3 manual path. It uses only existing repository inputs,
expected outputs, and tolerances, and serves as a fixture/provenance pattern.
It adds no HCM table values or coefficients and enables no new calculation
path.

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
for table-driven vertical-class support. Exhibit 15-11 classification is
implemented as a pure lookup. Separate validation-path records contain metadata
only for existing validated Example Problem 4 calculation paths.

No downstream coefficient tables were added. Phase 3 connects validation-path
metadata to production scope classification for one exact validated path;
calculation formulas remain unchanged.

### Phase 3 selected validated vertical path

Production manual single-segment support now uses the lookup metadata for
exactly one nonlevel path: mountainous, straight Passing Constrained,
`6% / 0.5 mi`, vertical Class 4, and exactly `8%` heavy vehicles.

The validation basis is Chapter 26 Example Problem 4 fixture `TLH-CH15-004`,
segment 3. This path is safe because the fixture segment is straight Passing
Constrained, has published expected outputs, and does not depend on Passing
Lane or downstream facility effects. No formulas, coefficients, or HCM table
values changed.

Adjacent combinations remain unsupported for manual calculation, including a
different grade length, a different heavy-vehicle percentage, a mismatched
submitted vertical class, any nonlevel Passing Zone or Passing Lane, missing
grade length, and any other mapped Example Problem 4 path outside its validated
facility context. No general mountainous, vertical-class, or grade-length
support is claimed.

### Phase 3B remaining validated-path assessment

No additional manual single-segment vertical paths were formalized. Inspection
of every remaining `TLH-CH15-004` segment found no additional path with a
standalone validation basis:

| Segment(s) | Exact path | Existing expected-output basis | Manual decision |
| --- | --- | --- | --- |
| 1 and 4 | Passing Constrained, `4% / 1.3 mi`, Class 4, `8%`, horizontal curves | Facility fixture validates the curve-combined segment outputs | Remains facility-only; no new nonlevel horizontal-curve support |
| 2 | Passing Constrained, `6% / 1.0 mi`, Class 5, `8%`, horizontal curves | Facility fixture validates the curve-combined segment output | Remains facility-only; no new nonlevel horizontal-curve support |
| 5 | Passing Lane, `-3% / 0.5 mi`, Class 1, `8%`, straight | Facility fixture validates the Passing Lane segment and downstream context | Remains facility-only; no nonlevel manual Passing Lane promotion |
| 6 | Passing Constrained, `-3% / 0.5 mi`, Class 1, `8%`, straight | Published final follower density includes upstream Passing Lane adjustment | Remains facility-only; standalone final output is not validated |

Lookup metadata now records the exact fixture segment basis, facility-only
limitation, and whether a record is independently validated for manual
single-segment use. Only segment 3 is marked manual-single-segment validated.
No formulas, coefficients, or HCM table values changed.

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

The lookup-backed grade-length-to-vertical-class decision represents a narrow
subset of HCM Exhibit 15-11:

| Grade and length | Derived vertical class | Validation basis |
| --- | ---: | --- |
| `4% / 1.3 mi` | 4 | Chapter 26 Example Problem 4 |
| `6% / 0.5 mi` | 4 | Chapter 26 Example Problem 4 |
| `6% / 1.0 mi` | 5 | Chapter 26 Example Problem 4 |

The Example Problem 4 facility path validates these combinations at `8%` heavy
vehicles in its exact six-segment facility context. Some combinations include
horizontal curves and downstream Passing Lane effects. Nonlevel manual
single-segment support is explicitly guarded and limited to the exact straight
Passing Constrained `6% / 0.5 mi` segment-3 path at `8%` heavy vehicles. Other
mapped pairs remain facility-fixture-only. Exact grade-length pairs do not
establish broad methodology validation or authorize other nonlevel inputs.

### Downgrade Class 1 path

- `-3% / 0.5 mi` maps to vertical Class 1.
- Chapter 26 Example Problem 4 validates that downgrade for one Passing Lane
  segment and one Passing Constrained segment, both straight and at `8%` heavy
  vehicles.
- The manual single-segment path rejects this downgrade because Phase 3
  promotes only the exact Example Problem 4 segment-3 upgrade path.
- No other downgrade grade-length pair is supported.

### Other current vertical class behavior

- The complete Exhibit 15-12 heavy-vehicle free-flow-speed coefficient table,
  Step 5 Exhibits 15-13 through 15-20 average-speed coefficient tables, and
  Step 6 Exhibits 15-24 through 15-29 percent-followers coefficient tables are
  implemented for vertical Classes 1 through 5.
- Passing Lane Step 5 and Step 6 coefficient tables cover Classes 1 through 5.
  Passing Lane lane-level capacity remains Class 1 only, and independent
  validation fixtures do not authorize new nonlevel paths, so public
  calculation guardrails are unchanged.
- The complete Exhibit 15-11 grade-length classification table is available
  through a pure lookup that reports matched row and column ranges.
- Classification does not authorize downstream calculation. Validation-path
  metadata remains connected to production scope classification only for the
  selected exact manual path and validated facility examples.
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
| Mountainous | Passing Constrained | `6%` | `0.5 mi` | 4 | Exactly `8%` | Chapter 26 Example 4, `TLH-CH15-004` segment 3 | Implemented as the one Phase 3 validated manual vertical path | Straight only; published fixture outputs are preserved. |
| Mountainous | Passing Constrained | Other Example Problem 4 mapped pairs | Exact fixture lengths | 1, 4, or 5 | Exactly `8%` in fixture | Chapter 26 Example 4 facility only | Explicitly unsupported manually | Remain available only in the exact validated facility fixture. |
| Mountainous | Passing Zone | Any nonlevel pair | Any | Any | Any | No direct Chapter 26 fixture for a nonlevel Passing Zone | Explicitly unsupported pending validation fixture | Phase 1 guardrails reject this path before calculation. |
| Mountainous | Passing Lane | Any nonlevel pair | Any | Any | Any | No independent standalone fixture | Explicitly unsupported manually | Facility Example Problem 4 behavior is preserved. |

## E. Unsupported Combinations

These combinations should remain rejected or explicitly unsupported until the
required HCM data and validation fixtures are available.

| Combination | Current reason to remain unsupported |
| --- | --- |
| Any nonlevel calculation pair other than `-3% / 0.5 mi`, `4% / 1.3 mi`, `6% / 0.5 mi`, or `6% / 1.0 mi` | Exhibit 15-11 can classify the pair, but downstream coefficients and validation fixtures do not yet authorize calculation. |
| Any vertical class not represented by the current class-indexed dictionaries | Required coefficients and validated calculation behavior are absent. |
| Any nonlevel manual path at a heavy-vehicle percentage other than exactly `8%` | Current nonlevel validation fixtures use `8%`; other percentages require independent validation fixtures before calculation. |
| Any nonlevel manual Passing Zone path | No independent nonlevel Passing Zone validation fixture exists, so the scope guardrail rejects it before calculation. |
| Passing Lane in vertical Class 4 or 5, or any other non-Class-1 path | Passing Lane lane-level capacity data and independent validation fixtures do not authorize these paths, even though Step 5 and Step 6 coefficient tables are complete. |
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

- Independent validation fixtures for any new nonlevel Step 4 input
  combinations before they are promoted through guarded public calculation
  paths. The complete Exhibit 15-12 heavy-vehicle coefficient table is present,
  but table availability alone does not authorize downstream support.
- Independent validation fixtures for additional vertical-class Step 6 paths.
  Exhibits 15-24 through 15-29 are table-driven for Classes 1 through 5, but
  table availability alone does not authorize broader calculation support.
- Any class-specific auxiliary coefficients, minimum values, applicability
  ranges, and rounding rules needed beyond the implemented Step 6 equations.
- Passing Lane lane-capacity data and validation beyond Class 1. Step 5 and
  Step 6 coefficient tables are complete, but the lane-level capacity path
  remains intentionally guarded.
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
- Lookup tests remain separate from calculation formulas. Phase 3 uses the
  metadata to enable one exact production scope path.

### Phase 3: One narrowly validated vertical class path

- Completed for the exact straight Passing Constrained `6% / 0.5 mi`, Class 4,
  `8%` heavy-vehicle path from `TLH-CH15-004` segment 3.
- The lookup scaffold is integrated with the scope guardrail; no formulas,
  coefficients, or new HCM table values were added.
- All adjacent manual nonlevel combinations remain rejected.

### Phase 3B: Remaining Example Problem 4 paths

- Completed as an assessment and guardrail-hardening phase.
- No additional path was formalized because every remaining candidate depends
  on horizontal curves, Passing Lane behavior, or facility adjustment context.
- Metadata and tests now make those facility-only limitations explicit.

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

Any next vertical expansion must add independently verified methodology data
and a standalone validation fixture for one additional path before production
scope is broadened. The Phase 3B assessment confirms that the remaining
Example Problem 4 paths are facility-only and must not be promoted as general
single-segment support without that evidence.
