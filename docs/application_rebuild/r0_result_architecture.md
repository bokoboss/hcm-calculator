# Application Rebuild R0.6 — Result Architecture

Status: Draft baseline for R0 planning
Date: 2026-08-24
Branch: `planning/application-rebuild-r0`
Base engineering behavior: qualified `main` at `8dc1481163d9864df71e2091ce23f0963b702e92`

## 1. Purpose

This document defines how the rebuilt HCM application should present, interpret, compare, and expose evidence for calculation results without changing the underlying engineering calculation contracts.

The central rule is:

> The result screen must answer the engineering question first, then show the key performance measures, then explain the result, and only then expose full calculation evidence.

The existing engine remains the calculation authority. The application layer may organize and explain engine results deterministically, but it must not invent HCM methodology, values, or design recommendations.

## 2. Result hierarchy

Every method should use four levels.

### Level 1 — Answer

The primary engineering outcome.

Examples:

- LOS C;
- LOS F — capacity exceeded;
- HCM method handoff — no weaving LOS assigned;
- invalid / unsupported scope;
- stale result — recalculate required.

### Level 2 — Engineering performance

The small set of method-relevant measures needed to understand the answer.

Examples:

- follower density;
- density;
- average/mean speed;
- percent followers;
- v/c;
- capacity;
- facility metrics.

### Level 3 — Engineering interpretation

Deterministic explanation of what the current engine result means.

Examples:

- motorized LOS is governed by follower density;
- demand exceeds applicable capacity;
- facility LOS is calculated from final facility follower density and is not an average of segment LOS letters;
- a warning applies but the calculation remains current;
- the weaving method stops and requires an HCM handoff;
- the result is stale because an input changed.

Interpretation is explanatory, not advisory. It must not become an unsupported recommendation engine.

### Level 4 — Evidence

Full traceability and audit content.

Examples:

- method and calculation contract;
- normalized engine inputs;
- intermediate values;
- assumptions;
- warnings;
- source references;
- calculation fingerprint;
- raw audit record;
- stored project/result identity.

Level 4 must be readily accessible but must not compete visually with Level 1.

## 3. Result presentation contract

The rebuilt application should derive a framework-independent result presentation model from the existing engine result and application state.

Conceptual contract:

```text
ResultPresentation
  identity
    project_id? 
    analysis_id
    scenario_id
    method_identifier
    method_version
    input_contract
    calculation_fingerprint

  state
    presentation_state
    current/stale
    calculated_at

  answer
    kind
    label
    value
    supporting_measure?

  metrics[]
    key
    label
    value
    unit
    priority

  interpretation[]
    code
    severity
    text
    source_basis

  warnings[]
  assumptions[]

  evidence
    displayed_inputs
    normalized_inputs
    intermediate_values
    source_references
    audit_record
```

This is an application presentation contract. It does not replace the existing engine `CalculationResult` or project schema by itself.

## 4. Result screen grammar

Conceptual post-calculation layout:

```text
Analysis / Scenario header
Method metadata / Current status

PRIMARY ANSWER
  LOS / capacity / handoff hero
  one supporting governing measure

KEY PERFORMANCE
  3-6 method-specific measures

ENGINEERING ASSESSMENT
  deterministic interpretation
  warnings / limitations that materially affect use

ACTIONS
  Recalculate [when stale]
  Duplicate Scenario
  Compare
  Export / Report

DETAILS
  Calculation Details
  Methodology & Assumptions
  Inputs
  Audit / Intermediate Values
```

The exact visual arrangement is deferred to R0.7/R0.8.

## 5. Result state behavior

The existing `ResultPresentationState` taxonomy should be preserved as the canonical application-state vocabulary unless a later compatibility decision deliberately changes it.

### 5.1 `prerun`

Primary message:

- no result yet;
- calculation has not been run.

Do not show a fake zero/blank result card.

### 5.2 `valid_current_result`

Primary message:

- current engineering answer and metrics.

Actions:

- export/report enabled;
- scenario actions enabled;
- evidence available.

### 5.3 `valid_current_result_with_warning`

Primary answer remains visible.

Warnings appear in Level 3, not as an application failure.

### 5.4 `capacity_failure`

The capacity condition becomes part of the primary answer.

Rules:

- show LOS/status exactly as supported by the method contract;
- explicitly say when predicted speed/density are not available;
- never fill unavailable values with zero;
- never derive congested speed, queue, delay, or travel time unless the qualified engine actually supplies them.

### 5.5 `hcm_stopping_or_handoff`

Primary answer is the method stopping/handoff state.

Rules:

- do not assign LOS if the active HCM method does not assign one;
- explain the stopping condition;
- suggest a supported method transition only when the mapping is known and valid;
- preserve all calculated evidence leading to the handoff.

### 5.6 `stale_result`

Primary state:

```text
Input changed — recalculation required
```

The previous result may remain visible for context but:

- must be visibly stale;
- must not appear current in exports/reports;
- primary action becomes Recalculate.

### 5.7 `invalid_input`

Do not show result interpretation.

Show blocking validation recovery steps.

### 5.8 `unsupported_scope`

Do not present an HCM answer.

Explain the unsupported combination and relevant qualified boundary.

### 5.9 `internal_error`

Do not present the exception as an engineering state.

Show a clear application error and preserve diagnostic evidence.

## 6. Common status language

Engineering state and software state must not be mixed.

Recommended distinction:

```text
Calculation status: Current
Engineering result: LOS C
```

or

```text
Calculation status: Current
Engineering result: Capacity exceeded — LOS F
```

or

```text
Calculation status: Stale
Engineering result: Previous LOS C (not current)
```

This avoids ambiguous labels such as simply `Calculated` when the engineering result has important warnings or failure conditions.

## 7. LOS hero rules

LOS is an effective primary answer for methods that validly assign LOS.

The LOS hero should contain:

- `LOS X`;
- one governing/supporting metric where helpful;
- compact engineering-state wording.

Example:

```text
LOS C
Follower density: 12.4 followers/mi/ln
Current result
```

or

```text
LOS F
Capacity exceeded
Speed and density are not predicted in this state
```

LOS colors may support recognition but must not be the only way the grade/state is conveyed.

## 8. Interpretation rule architecture

Interpretations should be code-driven and deterministic.

Conceptual form:

```text
InterpretationRule
  rule_id
  applicable_method
  condition based on engine outputs/state
  severity
  localized message
  source/basis
```

Rules must be testable without a browser.

### 8.1 Allowed interpretation categories

- governing measure;
- capacity condition;
- method stopping/handoff;
- scope warning;
- active calculation treatment/method choice;
- facility aggregation basis;
- critical segment identification;
- stale/current identity;
- unavailable-result explanation.

### 8.2 Not allowed without separate engineering implementation

- recommended lane additions;
- recommended design speed;
- recommended mitigation;
- prediction of operational measures outside the method;
- causal explanations not encoded/supported by the calculation method;
- statements that a design is acceptable/unacceptable beyond the method's supported criteria.

## 9. Method result architecture — Two-Lane Segment

### 9.1 Level 1 — Answer

Primary:

- Motorized Vehicle LOS.

Supporting governing measure:

- follower density.

The implemented Chapter 15 method explicitly bases Motorized Vehicle LOS on follower density.

### 9.2 Level 2 — Engineering performance

Recommended priority:

1. follower density;
2. average speed;
3. percent followers;
4. demand/capacity ratio;
5. free-flow speed;
6. demand flow / capacity as secondary detail.

Not all measures need to be displayed as equal cards.

### 9.3 Level 3 — Interpretation

Safe deterministic messages include:

- `Motorized Vehicle LOS is based on follower density.`
- selected segment type behavior/assumption;
- passing-zone opposing-flow treatment where applicable;
- single passing-lane segment limitation where applicable;
- horizontal-curve adjustment warning where emitted by the engine;
- capacity state when explicitly returned.

### 9.4 Level 4 — Evidence

Expose:

- vertical class and applicability evidence;
- FFS adjustments;
- average-speed coefficients;
- percent-followers coefficients;
- follower-density formula/reference;
- LOS thresholds/reference;
- assumptions/warnings;
- intermediate values.

## 10. Method result architecture — Two-Lane Facility

### 10.1 Level 1 — Answer

Primary:

- facility LOS.

Supporting governing measure:

- facility follower density.

### 10.2 Level 2 — Facility performance

Recommended priority:

1. facility follower density;
2. facility average speed;
3. facility percent followers;
4. facility length / segment count as context;
5. critical segment identity;
6. facility capacity-failure state.

### 10.3 Level 3 — Facility interpretation

The engine contract supports the following deterministic explanation:

- facility metrics are length weighted under HCM Eq. 15-39;
- facility LOS is determined from final facility follower density;
- segment LOS letters are not averaged;
- identify the critical segment using the engine's controlling/critical segment result;
- if any segment exceeds applicable capacity, surface facility capacity-failure status and the affected segment warnings.

### 10.4 Segment Results

Facility results require a first-class segment table beneath the facility answer.

Recommended columns:

- segment ID/name;
- segment type;
- length;
- average speed;
- percent followers;
- final follower density;
- LOS;
- capacity/warning marker;
- passing-lane/downstream context where relevant.

The table should support selecting a row to inspect segment evidence.

### 10.5 Critical segment treatment

The critical segment should be visually identifiable but must not replace the facility-level answer.

Example:

```text
Facility LOS C
Follower density: ...

Critical segment by demand/capacity ratio: Segment 4
```

### 10.6 Level 4 — Evidence

Include:

- facility Eq. 15-39 weighting components;
- segment-level intermediate calculations;
- final-density basis for each segment;
- passing-lane downstream adjustments;
- assumptions/warnings;
- template/context evidence where the workflow is bounded.

## 11. Method result architecture — Multilane Segment

### 11.1 Level 1 — Answer

Primary:

- LOS/status.

Supporting measure:

- density when available.

### 11.2 Level 2 — Engineering performance

Recommended order:

1. density;
2. speed used for density;
3. demand flow rate;
4. capacity;
5. adjusted FFS;
6. base FFS as secondary/detail.

### 11.3 Level 3 — Interpretation

Safe rules include:

- current demand is below/at/above applicable capacity based on engine state;
- identify active FFS source: measured or estimated;
- identify active heavy-vehicle treatment: general terrain / specific grade / external PCE;
- if internal PCE domain is unsupported, present the existing scope guard rather than extrapolating;
- if capacity failure occurs, state that speed and density are not predicted where the engine returns them unavailable.

### 11.4 Capacity failure

Primary presentation:

```text
LOS F — capacity exceeded
Demand exceeds applicable segment capacity
Speed/density not predicted by the qualified method in this state
```

Only show values actually returned by the engine.

## 12. Method result architecture — Basic Freeway Segment

### 12.1 Level 1 — Answer

Primary:

- LOS/status.

Supporting measure:

- density when available.

### 12.2 Level 2 — Engineering performance

Recommended order:

1. density;
2. speed used for density;
3. demand flow rate;
4. adjusted capacity;
5. base/applicable capacity;
6. adjusted FFS;
7. FFS before SAF as secondary evidence.

### 12.3 Level 3 — Interpretation

Safe deterministic messages include:

- capacity condition;
- measured vs estimated FFS treatment;
- driver-population/SAF/CAF treatment and source;
- internal vs external PCE treatment and provenance;
- no queue/delay/travel-time prediction in above-capacity state.

### 12.4 Capacity failure

Use the same visual grammar as Multilane while preserving Basic Freeway-specific capacity values and factor evidence.

## 13. Method result architecture — Weaving Segment

### 13.1 Normal Level 1 — Answer

Primary:

- weaving LOS/status.

Supporting measure:

- weaving-segment density when available.

### 13.2 Level 2 — Engineering performance

Recommended order:

1. density;
2. mean speed;
3. weaving speed;
4. nonweaving speed;
5. demand;
6. adjusted prevailing capacity / v/c if available in engine result.

### 13.3 Level 3 — Interpretation

Safe rules include:

- active one-sided/two-sided geometry context;
- capacity condition;
- warning/limitation from the engine;
- FFS source;
- HCM stopping/handoff state.

### 13.4 HCM handoff

The existing qualified scope specifies `LS >= LMAX` as a Chapter 12/14 handoff condition with no weaving LOS assigned.

Presentation priority:

```text
Weaving method handoff
No weaving LOS assigned for this condition
Review the applicable Basic Freeway / Merge-Diverge analysis path
```

The exact destination action must only be enabled when the application's method mapping can preserve the required engineering context.

### 13.5 Capacity failure

For unrounded v/c above the method boundary:

- capacity failure is primary;
- unavailable speed/density remain unavailable;
- do not calculate substitute values in the presentation layer.

## 14. Method result architecture — Merge Segment

### 14.1 Level 1 — Answer

Primary:

- LOS/status.

Supporting measure:

- ramp-influence density when available.

### 14.2 Level 2 — Engineering performance

Recommended order:

1. ramp-influence density;
2. governing v/c;
3. governing capacity;
4. ramp-influence speed;
5. all-lanes speed;
6. other method-specific flow measures in Details.

### 14.3 Level 3 — Interpretation

Safe rules include:

- qualified geometry summary: isolated one-lane right-side on-ramp;
- capacity condition;
- maximum desirable influence-area flow warning when emitted;
- freeway FFS source;
- ramp FFS context;
- explicit reminder that warning-only desirable-flow exceedance is not a capacity failure unless the engine also reports capacity failure.

### 14.4 Capacity failure

Primary:

- LOS F/capacity failure according to engine contract;
- speed/density unavailable where not predicted.

## 15. Method result architecture — Diverge Segment

Use the same interaction and result grammar as Merge so users transfer knowledge directly.

### 15.1 Level 1

- LOS/status;
- influence density supporting measure when available.

### 15.2 Level 2

1. influence density;
2. governing v/c;
3. governing capacity;
4. influence speed;
5. all-lanes speed.

### 15.3 Level 3

Safe rules include:

- qualified geometry summary: isolated one-lane right-side off-ramp;
- capacity condition;
- warning-only desirable-flow behavior;
- freeway/ramp FFS context;
- no queue/delay/spillback prediction outside the current method.

## 16. Missing / unavailable metric behavior

Use three distinct concepts:

### Not applicable

The method does not use the metric in the active branch.

Display `Not applicable` only when useful; otherwise omit it.

### Not available

The method conceptually has the metric but does not predict it in the current state, e.g. speed/density after certain capacity failures.

Display:

```text
Not predicted in this state
```

Do not display `0`.

### Not calculated

Calculation has not been run/current.

Do not imply engineering meaning.

## 17. Warning hierarchy

Warnings should be classified by effect on use.

### Informational

Example:

- active calculation assumption;
- reference/preset provenance.

### Engineering warning

Calculation remains valid/current, but a condition warrants review.

Example:

- maximum desirable influence flow exceeded while roadway capacity is not failed.

### Scope limitation

Valid result is bounded and must be interpreted within a documented scope.

### Blocking unsupported condition

No calculable result should be presented.

### Capacity failure / handoff

These are primary engineering states, not generic warnings.

## 18. Assumption presentation

Do not place all assumptions in the primary result card.

Show only assumptions that materially affect interpretation at Level 3.

Full assumptions belong in Methodology & Assumptions / Evidence.

Examples that may deserve Level 3 visibility:

- Two-Lane single passing-lane result excludes downstream facility effects;
- Merge/Diverge assumes isolated one-lane right-side geometry;
- facility result is length-weighted;
- external PCE is user-supplied and has recorded provenance.

## 19. Comparison-ready result model

Scenario comparison should be built on canonical result metric keys, not formatted labels.

Example:

```text
metric key              Existing       Option A
level_of_service        D              C
follower_density        18.2           12.4
average_speed           46.1           51.8
```

### 19.1 Comparison eligibility

Default comparison should require:

- same Analysis;
- same method family;
- compatible method version/input contract;
- current results for all compared scenarios.

A stale scenario should be clearly excluded or marked as requiring recalculation.

### 19.2 LOS comparison

Display grade transition:

```text
D -> C
```

Do not treat LOS letters as continuous numeric data for percentage calculations.

### 19.3 Numeric metrics

Show:

- absolute values;
- absolute delta where meaningful;
- percentage delta only for metrics where percentage comparison is technically meaningful and not misleading.

Exact comparison semantics are finalized in a later Compare specification.

### 19.4 Missing values

If one scenario is in capacity failure or handoff state and a metric is unavailable, show the state rather than forcing a numeric comparison.

## 20. Facility comparison

Two-Lane Facility comparison should operate at two levels:

1. facility-level scenario comparison;
2. segment-level comparison only where segment identity can be matched reliably.

Do not match segments merely by display row number if stable segment IDs differ.

## 21. Evidence architecture

Recommended evidence sections:

### 21.1 Method & Scope

- HCM edition/chapter;
- method identifier/version;
- calculation contract;
- supported-scope statement;
- source references.

### 21.2 Inputs

- user-displayed inputs;
- canonical/normalized engine inputs;
- units;
- provenance for governed/external inputs.

### 21.3 Calculation Details

- intermediate values;
- factors;
- method step/equation/source where available.

### 21.4 Assumptions & Warnings

- full lists;
- severity/classification.

### 21.5 Audit

- fingerprint;
- project/result identity;
- raw structured audit record;
- app/method version.

Raw JSON is an evidence view, not the default result experience.

## 22. Export relationship

Exports/reports must use the same current ResultPresentation identity but must not rerun the engine.

Export eligibility:

- current result: allowed;
- current result with warning: allowed with warning retained;
- capacity failure: allowed as an engineering result if the existing reporting contract supports it, with unavailable metrics clearly represented;
- handoff: exportable only as a stopping/handoff result where reporting contract supports it;
- stale result: not exportable as current;
- invalid/unsupported/internal error: no normal engineering result export.

Existing machine-readable project/audit exports remain separate from presentation reports where appropriate.

## 23. Localization

Result semantics must use language-neutral canonical keys and localized labels/messages.

Do not store Thai/English formatted strings as engineering identity.

Examples:

```text
state = capacity_failure
metric_key = follower_density
interpretation_code = facility_length_weighted
```

Localization maps these to English/Thai presentation.

## 24. Accessibility

Result meaning must not depend only on color.

Requirements for later design system:

- LOS letters/status written as text;
- warning icons accompanied by labels;
- tables usable with keyboard/screen-reader semantics where practical;
- stale/current state explicit in text;
- chart/diagram information duplicated in accessible text where necessary.

## 25. R0.6 acceptance criteria

R0.6 is acceptable when:

1. All result states have explicit presentation behavior.
2. Four-level hierarchy is method-independent.
3. Each of the seven methods has a defined primary answer and metric priority.
4. Capacity-failure behavior never invents unavailable measures.
5. Weaving handoff is treated as an answer/state rather than generic warning.
6. Two-Lane Facility separates facility answer from segment evidence.
7. Deterministic interpretation is explicitly separated from unsupported recommendations.
8. Comparison is based on canonical metric keys and current compatible results.
9. Evidence remains fully auditable without dominating normal use.
10. Export/report does not rerun calculation.
11. Localization does not alter engineering identity.
12. Result semantics can be unit-tested independently of the final frontend framework.

## 26. Next R0 gate

R0.7 should convert the approved Product + Workflow + Result architecture into a screen inventory and low-fidelity wireframes covering at minimum:

- Home / Quick Analysis / Projects;
- Project Overview;
- New Analysis selection;
- Multilane Segment input and result states;
- Two-Lane Facility grid and result states;
- Weaving geometry workflow;
- Merge/Diverge workflow;
- stale/result recovery;
- scenario comparison;
- methodology/evidence views;
- responsive behavior.
