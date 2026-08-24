# Application Rebuild R0.5 — Workflow Architecture

Status: Draft baseline for R0 planning
Date: 2026-08-24
Branch: `planning/application-rebuild-r0`
Base engineering behavior: qualified `main` at `8dc1481163d9864df71e2091ce23f0963b702e92`

## 1. Purpose

This document defines the target user-workflow architecture for the seven currently supported HCM analysis workflows before any frontend implementation begins.

It translates the existing qualified engine/adaptor contracts into engineering-task-oriented workflows while preserving current scope limitations and calculation authority.

The seven current analyses are:

1. Two-Lane Segment
2. Two-Lane Facility
3. Multilane Segment
4. Basic Freeway Segment
5. Weaving Segment
6. Merge Segment
7. Diverge Segment

This is not a screen-design document. Exact wireframes, spacing, visual design, and framework implementation belong to later R0 gates.

## 2. Workflow design principles

### 2.1 Engineering task first

The user should see engineering concepts such as Traffic, Geometry, Free-Flow Speed, Heavy Vehicles, and Weaving Geometry rather than internal software variable groups.

### 2.2 Explicit calculation

Changing an input must never silently replace an accepted result.

The calculation lifecycle remains explicit:

```text
Edit inputs
  -> validate readiness
  -> Calculate
  -> review result
  -> edit input
  -> previous result becomes stale
  -> Recalculate
```

### 2.3 Progressive disclosure

Conditional/advanced inputs should only appear when relevant.

Examples:

- measured FFS -> show measured FFS only;
- estimated FFS -> show geometry/adjustment inputs;
- specific-grade heavy-vehicle treatment -> show grade and truck-mix inputs;
- external PCE -> show PCE and provenance where required;
- passing-zone Two-Lane Segment -> show opposing volume;
- divided Multilane facility -> show left-side lateral clearance;
- one-sided Weaving -> show `lc_rf` and `lc_fr` rather than two-sided `lc_rr`.

### 2.4 Scope guardrails before engine failure

Known unsupported combinations should be explained at the point of selection where practical, not only after a failed calculation.

### 2.5 Results-first after calculation

After a successful calculation, the primary result becomes the dominant content. Input sections remain accessible for review/editing but no longer dominate the page.

### 2.6 Presets/examples are secondary

Validated examples and optional defaults remain useful for regression evidence and starting values, but they are not the primary product mental model.

The user workflow is:

```text
choose analysis -> enter/review inputs -> calculate -> review -> audit/export
```

not:

```text
choose example -> alter a worksheet
```

### 2.7 Preserve method truth

The new workflow must not imply capabilities absent from the current engine.

Current bounded limitations must remain visible and enforceable until separately implemented and qualified.

## 3. Common analysis lifecycle

Every Analysis/Scenario follows the same high-level lifecycle.

```text
1. Analysis Context
2. Required Engineering Inputs
3. Conditional / Method-Specific Inputs
4. Readiness Validation
5. Calculate
6. Result Review
7. Details / Methodology / Audit
8. Scenario / Compare / Export actions
```

The exact engineering input sections differ by method.

## 4. Common application states

The rebuilt application should preserve the semantics already represented by the existing result-state taxonomy.

### 4.1 Prerun

No accepted result exists yet.

Presentation:

- input workflow active;
- readiness status visible;
- Calculate enabled only when blocking validation passes;
- result area contains a restrained placeholder.

### 4.2 Invalid input

Inputs are incomplete or numerically invalid.

Presentation:

- Calculate blocked;
- errors attached to fields/sections;
- readiness summary identifies the minimum recovery actions.

### 4.3 Unsupported scope

Inputs describe a combination outside the qualified method boundary.

Presentation:

- Calculate blocked where the unsupported state is known before execution;
- explain why the method does not apply;
- show method handoff/reference guidance when supported by HCM behavior.

### 4.4 Valid current result

The accepted result matches the current input fingerprint.

Presentation:

- result becomes primary;
- export/report available;
- audit/details available;
- scenario actions available.

### 4.5 Valid current result with warning

Calculation is current but warnings require review.

Presentation:

- result remains usable;
- warning appears near engineering interpretation;
- audit/details preserve full warning text.

### 4.6 Capacity failure

Demand/capacity behavior reaches the qualified capacity-failure state.

Presentation:

- LOS/status shown according to the method contract;
- explicitly state when speed/density are not predicted;
- do not manufacture congested speed, delay, queue, or travel time.

### 4.7 HCM stopping / handoff

The active method stops and requires a different HCM analysis path.

Presentation:

- make the handoff the primary answer;
- do not show a fabricated LOS;
- offer a relevant supported analysis entry only when a valid mapping is known.

### 4.8 Stale result

Inputs changed after the last accepted result.

Presentation:

- prior result may remain visible for context but must be visually marked stale;
- export/report of the stale result must not be presented as current;
- primary action becomes Recalculate.

### 4.9 Internal error

Unexpected application/engine error.

Presentation:

- distinguish from engineering invalid/unsupported states;
- preserve diagnostic evidence;
- never reinterpret it as an HCM result.

## 5. Common workflow components

The following should be reusable application components/contracts rather than duplicated per method.

### 5.1 AnalysisHeader

Displays:

- analysis name;
- scenario name;
- method/facility name;
- HCM edition/chapter metadata;
- units;
- current/stale status.

### 5.2 StartingValuesControl

Optional action to load blank/default/reference starting values.

Rules:

- secondary to normal workflow;
- loading values invalidates/replaces current editable inputs intentionally;
- reference examples must remain labeled as examples/starting values, not as methods.

### 5.3 EngineeringSection

Common section container for Traffic, Geometry, Speed, Heavy Vehicles, etc.

Must support:

- required/optional/advanced distinction;
- inline help;
- section validity state;
- collapsed detail only for genuinely secondary content.

### 5.4 FFSSelector

Shared conceptual component for methods supporting measured or estimated FFS.

Modes:

```text
Free-Flow Speed
  - Use measured FFS
  - Estimate from roadway characteristics
```

The internal engine-specific fields differ by method but the interaction grammar stays consistent.

### 5.5 HeavyVehicleAdjustment

Shared conceptual component where applicable.

Possible supported modes by method include:

- general terrain;
- specific grade;
- external PCE.

Only modes supported by the active method should be exposed.

### 5.6 ScopeGuard

Evaluates known method limitations at the workflow boundary and produces:

- valid;
- warning;
- blocking unsupported scope;
- method handoff where known.

### 5.7 ReadinessPanel

Compact summary immediately before Calculate.

Examples:

```text
Ready to calculate
```

or

```text
2 items required
- Enter opposing-direction volume
- Select horizontal alignment
```

### 5.8 CalculateBar

Contains the explicit Calculate/Recalculate action and current readiness/status.

Calculation must not be triggered simply by editing a field.

### 5.9 ResultShell

Common result hierarchy defined further in R0.6.

### 5.10 SegmentGrid

Specialized reusable grid for facility/multi-segment workflows.

Must support:

- row-level validation;
- locked/read-only cells;
- conditional columns;
- row identity;
- result linkage to source segment;
- keyboard-efficient editing where practical.

### 5.11 GeometryDiagram

Reusable container for method geometry explanation where the spatial configuration matters.

Initial candidates:

- Weaving;
- Merge;
- Diverge.

It is explanatory/confirmatory unless a later design explicitly qualifies interactive geometry derivation.

## 6. Workflow 1 — Two-Lane Segment

### 6.1 Product intent

Analyze one supported Two-Lane Highway segment under the implemented Chapter 15 method boundary.

### 6.2 Proposed workflow

```text
Analysis Context
  -> Segment Type
  -> Traffic
  -> Roadway Geometry
  -> Terrain / Alignment
  -> Readiness
  -> Calculate
  -> Results
```

### 6.3 Analysis Context

Fields/actions:

- Analysis name
- Scenario
- Units
- Optional starting values where available

### 6.4 Segment Type

Engineering choice:

- passing-constrained / supported segment type;
- passing-zone;
- passing-lane where supported by the single-segment contract.

The UI should present user-facing labels and map them to stable internal identifiers.

### 6.5 Traffic

Required:

- analysis-direction volume;
- PHF;
- heavy-vehicle percentage.

Conditional:

- opposing-direction volume only when segment type requires it, notably passing-zone behavior.

### 6.6 Roadway Geometry

Required:

- segment length;
- posted/base speed;
- lane width;
- shoulder width;
- access-point density.

### 6.7 Terrain / Alignment

Terrain:

- level;
- mountainous within qualified scope.

Conditional:

- grade input for non-level terrain.

Horizontal alignment:

- straight;
- horizontal curves.

Conditional:

- horizontal-curve subsegment data when curves are selected.

Vertical-class behavior should remain consistent with the existing method contract; do not expose a user override unless the existing workflow actually supports and validates it.

### 6.8 Readiness rules

Block calculation for:

- missing required traffic or geometry fields;
- invalid PHF/numeric domains;
- missing opposing volume when the chosen segment type requires it;
- unsupported terrain/alignment combination.

### 6.9 Result transition

After calculation show the method's primary LOS/performance outputs first, followed by assumptions/warnings and audit evidence.

Any material input edit marks the result stale.

## 7. Workflow 2 — Two-Lane Facility

### 7.1 Product intent

Analyze an ordered Two-Lane facility composed of multiple segments while preserving the currently qualified facility/template boundaries.

This workflow is deliberately different from a normal stacked form.

### 7.2 Current scope reality

The current qualified workflow is not unrestricted general Chapter 15 facility creation.

It uses validated Example 3 / Example 4 facility-backed contexts with guarded edits. Some fields are editable and some context remains locked depending on the selected template.

The new application must not disguise this limitation.

### 7.3 Proposed workflow

```text
Analysis Context
  -> Facility Basis / Starting Context
  -> Segment Table
  -> Facility Validation
  -> Calculate
  -> Facility Summary
  -> Segment Results
```

### 7.4 Facility Basis / Starting Context

Present available validated contexts clearly, for example:

- Example 3-backed level facility context;
- Example 4-backed mountainous facility context.

For each, explain:

- what may be edited;
- what is locked;
- why the context is bounded.

Do not imply the selected example is merely cosmetic if it controls qualified context.

### 7.5 Segment Table

Core columns conceptually include:

- segment ID/name;
- segment type;
- length;
- posted speed;
- analysis-direction volume;
- opposing-direction volume when applicable;
- PHF;
- heavy vehicles;
- terrain / grade;
- horizontal alignment;
- lane width;
- shoulder width;
- access-point density;
- passing-lane role/context.

The exact editable set depends on the qualified facility basis.

### 7.6 Grid behavior

The grid must distinguish:

- editable cells;
- locked cells inherited from the selected qualified context;
- conditionally active cells;
- invalid cells;
- row-level warnings.

For example, opposing-direction volume is only active for a passing-zone segment.

### 7.7 Facility validation

Validation runs before Calculate and should aggregate:

- missing fields;
- invalid numeric values;
- duplicate/invalid segment IDs;
- invalid segment type/role combinations;
- invalid downstream-affected placement;
- missing opposing volume for passing-zone segments;
- unsupported edits to locked context.

The user should be able to jump from a validation message to the relevant row/cell.

### 7.8 Results

Two result levels are both important:

1. facility-level answer/performance;
2. segment-level result table.

Segment result rows should remain traceable to the original segment IDs/names.

### 7.9 Future general facility support

The UI architecture should allow later replacement of template-bounded setup with a general facility builder, but R0 must not promise that capability before engineering implementation/qualification.

## 8. Workflow 3 — Multilane Segment

### 8.1 Product intent

Analyze one bounded one-direction Multilane Highway Segment using the existing qualified method.

### 8.2 Proposed workflow

```text
Analysis Context
  -> Traffic
  -> Segment Geometry
  -> Free-Flow Speed
  -> Heavy-Vehicle Adjustment
  -> Readiness
  -> Calculate
  -> Results
```

### 8.3 Traffic

Required:

- demand volume;
- PHF;
- heavy-vehicle percentage.

### 8.4 Segment Geometry

Required:

- number of lanes;
- segment length.

Additional geometry appears under estimated FFS rather than being duplicated here.

### 8.5 Free-Flow Speed

Choice:

```text
Free-Flow Speed
  - Measured
  - Estimate from roadway characteristics
```

Measured mode:

- free-flow speed.

Estimated mode:

- posted speed limit;
- lane width;
- roadside lateral clearance;
- median type;
- access-point density;
- left-side lateral clearance when median type is divided.

Scope guard:

- estimated FFS currently supported only for two or three lanes in the analysis direction.

### 8.6 Heavy-Vehicle Adjustment

Engineering choice:

- General terrain
- Specific grade
- External PCE

General terrain:

- terrain type within supported domain.

Specific grade:

- grade percent;
- truck mix.

External PCE:

- passenger-car equivalent.

The UI should explain when an external PCE is required because the internal lookup is outside the printed qualified domain.

### 8.7 Results

Primary output hierarchy should include LOS/status followed by core measures such as density, speed, demand flow, capacity, and relevant adjusted quantities.

Capacity-failure state must not show invented speed/density.

## 9. Workflow 4 — Basic Freeway Segment

### 9.1 Product intent

Analyze one bounded one-direction, one-segment, uninterrupted-flow Basic Freeway Segment within the current qualified Chapter 12 implementation.

### 9.2 Proposed workflow

```text
Analysis Context
  -> Traffic
  -> Segment Geometry
  -> Free-Flow Speed
  -> Heavy Vehicles
  -> Driver Population / Adjustment Factors
  -> Readiness
  -> Calculate
  -> Results
```

### 9.3 Traffic

Required:

- demand volume;
- PHF;
- heavy-vehicle percentage.

### 9.4 Segment Geometry

Required:

- number of lanes;
- segment length.

### 9.5 Free-Flow Speed

Measured mode:

- measured FFS.

Estimated mode:

- base FFS;
- lane width;
- right-side lateral clearance;
- total ramp density used for FFS adjustment.

The UI must make clear that ramp density here is an FFS adjustment input, not a ramp-analysis workflow.

### 9.6 Heavy Vehicles

Current contract supports internal or external PCE behavior.

Internal behavior may involve:

- terrain type;
- truck mix for specific-grade conditions;
- grade percent where applicable.

External PCE:

- PCE value;
- provenance/source.

Unsupported PCE domains must remain guarded.

### 9.7 Driver Population / Adjustment Factors

This section is important but visually secondary to core traffic/geometry.

Expose a user-facing decision such as:

```text
Driver population / governing adjustment
  - Regular drivers / HCM base conditions
  - Supported Chapter 26 driver category
  - Explicit governed SAF/CAF values [only if current contract permits]
```

Preserve source/provenance fields for non-default factors.

### 9.8 Results

Primary measures include:

- LOS/status;
- density;
- speed used for density;
- adjusted FFS;
- demand flow rate;
- capacity / adjusted capacity.

Above-capacity behavior reports the qualified capacity-failure result without fabricating congested speed/density, queues, delay, or travel time.

## 10. Workflow 5 — Weaving Segment

### 10.1 Product intent

Analyze a qualified isolated HCM 7.0 freeway weaving segment with one-sided or two-sided geometry within the implemented lane envelope.

### 10.2 Proposed workflow

```text
Analysis Context
  -> Weaving Configuration
  -> Geometry / Lane Relationships
  -> Movement Flows
  -> Traffic Conditions
  -> Free-Flow Speed
  -> Readiness / Handoff Check
  -> Calculate
  -> Results
```

### 10.3 Analysis Context

- analysis/case name;
- units;
- optional reference preset.

### 10.4 Weaving Configuration

Choice:

- one-sided;
- two-sided.

Required:

- segment length;
- total lanes;
- weaving lanes;
- entry side;
- exit side.

A geometry diagram should update to reflect the selected configuration where practical, but R0 does not authorize automatic geometry derivation.

### 10.5 Geometry / Lane Relationships

Current engine contract includes explicit evidence/inputs for:

- reachable O-D lanes FF/FR/RF/RR;
- option-lane status FR/RF/RR;
- NWL basis;
- lane-change basis.

These should not be presented as an unexplained matrix of internal variables.

Recommended UX:

- diagram first;
- grouped O-D lane relationship controls second;
- technical basis fields under an Engineering Details subsection with clear help.

Conditional lane-change inputs:

- one-sided: `LC_RF`, `LC_FR`;
- two-sided: `LC_RR`.

### 10.6 Movement Flows

Group the four movement demands together:

- FF;
- FR;
- RF;
- RR.

Use a compact movement-flow grid/diagram rather than four unrelated form fields if the wireframe study confirms usability.

### 10.7 Traffic Conditions

- PHF;
- heavy-vehicle percentage;
- terrain type;
- interchange density.

### 10.8 Free-Flow Speed

Shared FFSSelector:

Measured:

- free-flow speed.

Estimated:

- base free-flow speed;
- lane width;
- right-side lateral clearance;
- total ramp density.

### 10.9 Readiness / Handoff

Known method limits must be evaluated before result presentation.

If `LS >= LMAX` according to the qualified method behavior, present an HCM method handoff rather than a weaving LOS.

Above-capacity behavior must preserve the current rule that speed/density are not predicted.

### 10.10 Results

Core measures include:

- LOS/status or handoff;
- mean speed;
- weaving speed;
- nonweaving speed;
- density;
- demand;
- adjusted prevailing capacity;
- warnings/limitations.

## 11. Workflow 6 — Merge Segment

### 11.1 Product intent

Analyze the qualified HCM 7.0 isolated, one-lane, right-side freeway merge operational case within the implemented scope.

### 11.2 Proposed workflow

```text
Analysis Context
  -> Ramp / Freeway Geometry
  -> Freeway + Ramp Traffic
  -> Freeway FFS
  -> Ramp Speed / Conditions
  -> Scope Confirmation
  -> Calculate
  -> Results
```

### 11.3 Geometry

The geometry diagram should be shown early because it explains the method boundary.

Current supported geometry includes:

- right-side on-ramp;
- one ramp lane;
- 2-4 freeway lanes;
- acceleration lane length;
- isolated ramp context.

User-editable core geometry:

- freeway lane count;
- acceleration lane length.

Geometry source/notes are evidence fields and should be available without competing visually with core geometry.

### 11.4 Freeway + Ramp Traffic

Present as paired freeway/ramp inputs:

- freeway demand;
- ramp demand;
- freeway PHF;
- ramp PHF;
- freeway heavy-vehicle percentage;
- ramp heavy-vehicle percentage.

The paired layout reinforces that these are two streams entering the analysis.

### 11.5 Freeway FFS

Measured:

- freeway FFS.

Estimated:

- base FFS;
- lane width;
- right-side lateral clearance;
- total ramp density.

### 11.6 Ramp / Terrain Conditions

- explicit ramp FFS;
- terrain: level or rolling within current qualified scope.

### 11.7 Scope Confirmation

The UI should make the fixed assumptions conspicuous but concise:

- isolated ramp;
- right-side;
- one ramp lane;
- no lane addition;
- no major merge;
- no adjacent-ramp interaction.

Unsupported combinations should not be offered as if calculable.

### 11.8 Results

Core measures include:

- LOS/status;
- ramp-influence density;
- ramp-influence speed;
- all-lanes speed;
- governing capacity;
- governing v/c;
- maximum-desirable influence-flow warning where applicable.

Capacity failure must not invent speed/density.

## 12. Workflow 7 — Diverge Segment

### 12.1 Product intent

Analyze the qualified HCM 7.0 isolated, one-lane, right-side freeway diverge operational case within the implemented scope.

### 12.2 Proposed workflow

The workflow mirrors Merge to maximize transfer learning:

```text
Analysis Context
  -> Ramp / Freeway Geometry
  -> Freeway + Ramp Traffic
  -> Freeway FFS
  -> Ramp Speed / Conditions
  -> Scope Confirmation
  -> Calculate
  -> Results
```

### 12.3 Geometry

Current supported geometry includes:

- right-side off-ramp;
- one ramp lane;
- 2-4 freeway lanes;
- deceleration lane length;
- isolated context.

### 12.4 Traffic

Paired freeway/off-ramp inputs:

- upstream freeway demand;
- off-ramp demand;
- freeway PHF;
- ramp PHF;
- freeway heavy vehicles;
- ramp heavy vehicles.

Blocking validation:

- off-ramp demand cannot exceed upstream freeway demand.

### 12.5 Freeway FFS

Same FFSSelector grammar as Merge.

### 12.6 Ramp / Terrain Conditions

- ramp FFS;
- terrain: level or rolling.

### 12.7 Scope Confirmation

Fixed qualified assumptions include:

- isolated ramp;
- right-side;
- one ramp lane;
- no lane drop;
- no option lane;
- no major diverge;
- no adjacent-ramp interaction.

### 12.8 Results

Use the same Merge/Diverge result grammar so users can compare related analyses easily.

Core measures include:

- LOS/status;
- influence density/speed;
- all-lanes speed;
- governing capacity;
- governing v/c;
- warnings.

## 13. Cross-method reusable workflow matrix

| Capability | 2L Segment | 2L Facility | Multilane | Basic Freeway | Weaving | Merge | Diverge |
|---|---:|---:|---:|---:|---:|---:|---:|
| AnalysisHeader | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| StartingValuesControl | Optional | Important bounded context | Optional | Optional | Optional | Optional | Optional |
| Traffic section | Yes | Grid | Yes | Yes | Yes | Paired | Paired |
| Segment geometry | Yes | Grid | Yes | Yes | Specialized | Specialized | Specialized |
| FFSSelector | No/posted-speed method | No | Yes | Yes | Yes | Yes | Yes |
| HeavyVehicleAdjustment | Method-specific | Grid/context | Yes | Yes | Simplified | Separate streams | Separate streams |
| SegmentGrid | No | Yes | No | No | No | No | No |
| MovementFlowGrid | No | No | No | No | Yes | No | No |
| GeometryDiagram | Optional | Optional | Optional | Optional | Strongly recommended | Strongly recommended | Strongly recommended |
| ScopeGuard | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| HCM handoff state | Possible | Possible | Possible | Possible | Explicit | Possible | Possible |
| Capacity-failure state | Method-dependent | Method-dependent | Yes | Yes | Yes | Yes | Yes |
| Audit/evidence | Yes | Yes | Yes | Yes | Yes | Yes | Yes |

## 14. Common edit/recalculation behavior

### 14.1 Before first calculation

- input edits update readiness immediately;
- no engine result is implied;
- optional derived presentation values may update only if they are clearly not HCM result outputs.

### 14.2 After accepted calculation

Any material input change:

1. preserves the previous result as historical/stale context if desired;
2. marks it `stale_result` immediately;
3. disables current-result export/report actions;
4. changes primary action to Recalculate.

### 14.3 Reverting an input

If the exact calculation fingerprint returns to the accepted result fingerprint, the application may restore current-result status only if the existing fingerprint contract verifies identity deterministically.

### 14.4 Changing units

Changing Metric/Imperial is a presentation-boundary operation where supported. It should not change engineering identity when canonical engine inputs are equivalent.

### 14.5 Loading starting values

Loading a preset/default is an explicit destructive edit of displayed inputs and must invalidate any incompatible current result.

## 15. Validation architecture

Validation should be layered.

### Layer 1 — Field validity

Examples:

- numeric parsing;
- required fields;
- basic ranges.

### Layer 2 — Section validity

Examples:

- measured FFS requires measured speed;
- estimated FFS requires active geometry;
- external PCE requires PCE/provenance where defined;
- passing zone requires opposing volume.

### Layer 3 — Method scope

Examples:

- supported lane counts;
- supported terrain;
- supported weaving configuration;
- isolated right-side one-lane ramp only;
- valid facility context.

### Layer 4 — Engine/result state

Examples:

- capacity failure;
- HCM stopping/handoff;
- warning-only domain conditions.

The UI must not collapse all four layers into a generic red error box.

## 16. Method selection workflow

The user should not select methods from a single long calculator dropdown.

Recommended entry:

```text
New Analysis

Highways
  Two-Lane Segment
  Two-Lane Facility
  Multilane Segment

Freeways
  Basic Freeway Segment
  Weaving Segment
  Merge Segment
  Diverge Segment
```

Each option should show a short scope description before creation.

Example:

```text
Merge Segment
Isolated one-lane right-side freeway on-ramp operational analysis.
HCM 7.0 · qualified current scope
```

This is especially important because several methods are deliberately bounded.

## 17. Analysis creation behavior

Creating an Analysis should establish:

- stable analysis ID;
- user-facing analysis name;
- method identifier/version;
- default Base Scenario;
- unit system;
- initial input state;
- no current result.

The method cannot silently change after calculations exist. If the user needs a different method, create a new Analysis or perform an explicit supported handoff/duplicate operation.

## 18. Quick Analysis workflow

Quick Analysis should reuse the exact same Analysis component architecture but without requiring a persistent Project.

```text
Home
  -> New Analysis
  -> choose method
  -> Base Scenario created internally
  -> enter inputs
  -> calculate
  -> review
  -> Save to Project [optional]
```

There must not be separate engineering calculation code for Quick Analysis and Project Analysis.

## 19. Project Analysis workflow

```text
Project Overview
  -> Add Analysis
  -> choose method
  -> name/location/context
  -> Base Scenario
  -> calculate/review
  -> duplicate scenario if needed
  -> compare/report
```

The Project layer organizes analyses but does not alter numerical calculation contracts.

## 20. R0.5 acceptance criteria

R0.5 is acceptable when the following are true:

1. All seven current methods have an explicit target workflow.
2. Current bounded scope/limitations are represented rather than hidden.
3. Common components are identified without forcing all methods into the same form.
4. Calculation remains explicit and fingerprint/state-driven.
5. Stale-result behavior is defined.
6. Validation is separated into field, section, scope, and result-state layers.
7. FFS interaction is consistent across the five methods that use measured/estimated FFS.
8. Merge and Diverge share one interaction grammar while preserving distinct engine contracts.
9. Two-Lane Facility is treated as a grid/facility workflow rather than a standard form.
10. Weaving receives a geometry/movement-oriented workflow rather than an unexplained list of technical fields.
11. Quick Analysis and Project Analysis reuse the same engineering workflow components.
12. No requirement in this document requires HCM calculations to be implemented in the frontend.

## 21. Next R0 gate

R0.6 should define the result architecture in detail, including:

- primary answer by method;
- secondary metric priority;
- deterministic interpretation rules;
- warning vs blocking vs handoff presentation;
- capacity-failure presentation;
- facility/segment result hierarchy;
- comparison-ready result contracts;
- audit/evidence disclosure levels.
