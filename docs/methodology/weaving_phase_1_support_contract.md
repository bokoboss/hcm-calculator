# Phase 13.1 Weaving Segment Support Contract

## Status and method identity

This is a proposed, evidence-bounded contract for a future engine.  **No
Weaving Segment engine, UI, persistence type, export, navigation entry, or
numerical design/sensitivity tool exists in this phase.**  The only locally
governing material available for this contract is HCM **Version 7.0**.  HCM 7.1
material substantially changes the procedure; a decision to target 7.1 blocks
Phase 2 until it is separately audited and this contract is revised.

Proposed stable identifiers for a Version 7.0 implementation:

| Item | Proposed identifier |
| --- | --- |
| Method name | `hcm7_v70_freeway_weaving_segment` |
| Facility type | `freeway_weaving_segment` |
| Calculation type | `operational_analysis` |
| Future project type (not implemented) | `manual_freeway_weaving_segment_v1` |
| Engine-native units | US customary: ft, mi, mi/h, veh/h, pc/h, pc/h/ln, pc/mi/ln |

## Proposed qualified release envelope

Subject to Phase 2 equation tests and the independent Chapter 27
transcription gate below, the first release is a single, isolated **freeway**
weaving segment during the peak 15-min period of an analysis hour, expressed as
equivalent hourly rates.  It supports HCM 7.0 one-sided and two-sided
configurations directly described by Chapter 13.  The initial numeric lane
domain is `N = 3 or 4`, the independently reviewed core-example coverage;
`NWL` is 2/3 one-sided and 0 two-sided.  Wider/narrower domains are deferred
until a Chapter-13 table/equation-domain review and non-example validation
prove them; no value is silently substituted.  `LS` must be positive and
strictly less than computed `LMAX`; no long-segment approximation is allowed.

It supports measured FFS within the weave or estimated freeway FFS only in the
Chapter 12 Eq. 12-2 model range (55--75 mi/h) with its required lane-width,
right-clearance, and total-ramp-density inputs.  General-terrain level (`ET=2`)
and rolling (`ET=3`) Chapter 12 PCE paths are the proposed initial terrain
paths.  Specific-grade, mountainous, unprinted truck-mix, and external-PCE
paths are deferred even where another current package supports them: weaving
must obtain independent evidence and tests first.  The common HV mix therefore
uses one segment-level `fHV`; Chapter 13 provides no authoritative aggregation
rule for movement-specific capacity factors.  CAF/SAF and driver-population
adjustments are fixed at their HCM default unless the Phase 2 crosswalk maps an
authorized, source-provenanced adjustment route; no numeric factor may be
user-invented.

The release is freeway-only.  `multilane_cd`, C-D roadway, multilane access,
managed-lane/cross-weave, and signal-influenced branches are excluded.  HCM
7.0 calls the C-D/multilane application approximate, requires measured C-D
FFS, and warns of limitations.  That is insufficient evidence for a first
qualified product branch.

## Canonical movement terminology

`FF` is freeway-to-freeway, `FR` is freeway-to-ramp, `RF` is ramp-to-freeway,
and `RR` is ramp-to-ramp.  Labels name origin and destination, not lane
position, and their meanings do not change between configurations.  What
changes is the weaving classification: one-sided configurations use the
applicable FR/RF crossing movements in the Chapter 13 minimum-lane-change
relationship; two-sided configurations have RR as the weaving movement and
`NWL = 0`.  Phase 2 must display a newly created, non-copyrighted schematic or
an accessible text mapping; legacy PNGs are not approved for reuse.

## Input contract draft

| Field | Meaning/type | Native/display unit | Required | Validity/dependency | Zero meaningful? |
| --- | --- | --- | --- | --- | --- |
| `configuration` | enum: `one_sided`/`two_sided` | — | yes | must match movement geometry | no |
| `analysis_period_minutes`, `peak_hour_factor` | period and PHF | min, ratio | yes | qualified peak-period convention | no |
| `segment_length_ft` | `LS` | ft / m | yes | positive and `< LMAX` | no |
| `number_of_lanes` | directional freeway lanes | count | yes | initial `N` is 3 or 4 only | no |
| `number_of_weaving_lanes` | `NWL` | count | derived/validated | 2/3 one-sided, 0 two-sided | no |
| `movement_volumes_veh_h` | FF/FR/RF/RR observed demand | veh/h | yes | each explicitly provided; configuration validates inactive movement | only documented absent movement |
| `ffs_mode`, `free_flow_speed_mph` | measured/estimated FFS inputs | mi/h / km/h | yes | measured in weave or qualified Ch. 12 route | no |
| `geometry_adjustments` | lane/clearance/ramp-density evidence | ft, ramps/mi | conditional | selected FFS path only | never silently |
| `heavy_vehicle_path` | common mix/PCE provenance | %, PCE | yes | level/rolling Ch. 12 general-terrain path only | no |
| `terrain_grade_truck_mix` | PCE route inputs | %/grade/mi/mix | conditional | grade/truck-mix path is deferred in first release | no |
| `driver_population`, `saf`, `caf` | authoritative adjustment inputs | ratio | conditional | only allowed source-backed pair/default | no |

All inputs need source provenance or an explicit user-measured designation.
Unknown/inapplicable fields are rejected even when zero.  UI metric conversion,
if later added, belongs at the boundary and must not alter normalized inputs.

## Result contract draft

Return the existing `CalculationResult` contract with a method/facility
identifier, normalized-input audit, source-tagged `IntermediateValue`s,
assumptions, warnings, and limitations.  The outputs must distinguish demand
volume, ideal passenger-car flow, density-governed capacity, weaving-flow
capacity when applicable, base/CAF-adjusted governing capacity, v/c, capacity
status, weaving/nonweaving/mean speed, density, LOS, and governing reason.
The audit trail must include movement map, VR, LCMIN, LS/LMAX, capacity
candidates, fHV/PCE and FFS provenance, lane-change branch and values, and
equation/exhibit location.  Ideal lane/weaving-flow capacities are pc/h/ln or
pc/h as explicitly named; prevailing unadjusted and CAF-adjusted segment
capacities are veh/h after `fHV`/CAF.  The result must never mix those units.

At capacity/above-capacity behavior is deliberately explicit: exactly unrounded
`v/c = 1.00` continues to the HCM speed/density/LOS calculation; only `v/c >
1.00` is the segment capacity failure.  A failure is a calculated engineering
status, not a malformed-input error: report LOS F, the governing reason, and
`mean_speed_mph = None` and `density_pc_mi_ln = None` (rendered Not predicted).
`LS >= LMAX` is an HCM stopping/handoff
condition, not an input error: return an explicit unsupported/handoff status
with no weaving predictions.  Invalid physical inputs remain `HCMCalcError`;
an excluded but well-formed method case is `UnsupportedScopeError`.

## Explicit exclusions

The first release excludes multiple/interacting or overlapping weaves,
upstream/downstream facility or corridor analysis, merge/diverge computation,
reliability, ramp metering, managed lanes, work zones, queues/delay/travel-time
prediction, urban streets, oversaturated operational prediction, Design mode,
Sensitivity charts, unsupported truck mixes/grades/geometries, C-D and
multilane branches, and any input requiring table extrapolation or silent
clipping.  It also does not implement a Chapter 14 handoff calculation; it
identifies the handoff only.

## Decision register

| ID | Question/evidence | Decision and rationale | Implementation consequence / revisit condition |
| --- | --- | --- | --- |
| WEAVE-DEC-001 | Ch. 13 is an operational procedure; legacy Design/Sensitivity are numerical wrappers | Operational analysis only | no solver/chart; revisit after operational qualification |
| WEAVE-DEC-002 | Local governing source is HCM 7.0; official 7.1 materially changes method | Canonical method identifies v7.0 | retarget to 7.1 only after a full new audit |
| WEAVE-DEC-003 | Ch. 13 directly defines both configuration types | Support one-sided and two-sided core cases | independent equation/example coverage for each |
| WEAVE-DEC-004 | Ch. 13 p. 13-30 calls C-D/multilane approximate | Freeway-only | revisit with measured-FFS and validation evidence |
| WEAVE-DEC-005 | singular Ch. 13 capacity `fHV`; no aggregation rule | common segment HV mix | differing movement factors rejected/deferred |
| WEAVE-DEC-006 | Ch. 13 p. 13-29/Ch. 12 define FFS routes | measured-in-weave or qualified freeway estimate | source/provenance required |
| WEAVE-DEC-007 | current Ch. 12 logic is qualified but package-coupled | reuse core contracts; refactor only pure evidence-identical helpers | no code duplication or cross-package extension without tests |
| WEAVE-DEC-008 | Eq. 13-4 and p. 13-21 | `LS >= LMAX` stops weaving analysis | explicit Chapter 12/14 handoff result |
| WEAVE-DEC-009 | Ch. 13 p. 13-24 | only unrounded `v/c > 1.00` is capacity failure/LOS F; equality continues | preserve v/c and null speed/density only after failure |
| WEAVE-DEC-010 | product convention and method stopping language | speed/density are Not predicted after a capacity failure | no capacity-point proxy |
| WEAVE-DEC-011 | legacy wrappers lack HCM method authority | defer Design/Sensitivity | future tool clearly numerical wrapper |
| WEAVE-DEC-012 | legacy assets lack license/provenance | do not reuse diagrams | redraw or obtain documented permission |

## Chapter 27 validation evidence and gate

Candidate core operational examples are local HCM 7.0 Chapter 27 Example 1
(major weave, pp. 27-2--7), Example 2 (ramp weave, pp. 27-7--11), and Example
3 (two-sided weave, pp. 27-12--16).  Their visually checked published final
evidence is respectively: `D=26.3`, `S=53.1`, `LOS C`, capacity `8,038 veh/h`;
`D=20.2`, `S=61.9`, `LOS C`, capacity `8,580 veh/h`; and `D=39.2`, `S=45.8`,
`LOS E`, capacity `4,593 veh/h`.  Published display rounding requires
tolerances derived from each displayed precision, not artificial exactness.

Example 3's printed nonweaving-flow chain is internally inconsistent (defined
4,995 pc/h; later lane-change use 5,015 pc/h).  Its implementation must follow
the equation-defined flow and document the printed intermediate difference;
final values are validation evidence with a reviewed tolerance, never a hidden
branch.  Examples 4--5 (design/service-volume) and Examples 6--7
(managed-lane/access extension) are outside the first release.

The independent transcription ledger below records the complete practical
input/intermediate inventory needed to recreate the examples without copying
their narrative. `V` is raw veh/h and `v` is pc/h unless stated otherwise.

| Example | Configuration / inputs | FFS/HV/capacity path | Published intermediate and result evidence | Precision/tolerance |
| --- | --- | --- | --- | --- |
| 1, major weave, pp. 27-2--7 | one-sided; LS 1,500 ft; N 4; PHF .91; level; ID .8; V(FF,FR,RF,RR)=(1,815,692,1,037,1,297) | FFS 65 mi/h; PT 5%, ET 2, fHV .952; cIFL 2,350 pc/h/ln; CAF/SAF source values await second transcription | v=5,586; vW=1,995; VR=.357; LCRF=0, LCFR=1, NWL=3; LCMIN=798; LMAX=4,639 ft; density capacity 8,038 veh/h governs vs weaving 9,333; LCW=1,144; LCNW=782; LCALL=1,926; W=.275; Sw=54.2, Snw=52.5, S=53.1 mi/h; D=26.3 pc/mi/ln; LOS C | speed/density ±0.05; integer capacities/lane changes ±0.5; LOS exact |
| 2, ramp weave, pp. 27-7--11 | one-sided; LS 1,000 ft; N 4; PHF/fHV 1; v(FF,FR,RF,RR)=(4,000,300,600,100) | flows already pc/h; capacity path published; CAF/SAF source values await second transcription | v=5,000; vW=900; VR=.18; LCRF=1, LCFR=1, NWL=2; LCMIN=900; LMAX=4,333 ft; density capacity 8,580 veh/h governs; LCW=1,187; LCNW=616; LCALL=1,803; W=.360; Sw=59.1, Snw=62.5, S=61.9 mi/h; D=20.2 pc/mi/ln; LOS C | speed/density ±0.05; integer capacities/lane changes ±0.5; LOS exact |
| 3, two-sided weave, pp. 27-12--16 | two-sided; LS 750 ft; N 3; PHF .94; rolling; ID 2; V(FF,FR,RF,RR)=(3,500,250,100,300) | FFS 60 mi/h; PT 11%, ET 3, fHV .82; cIFL 2,300 pc/h/ln; CAF/SAF source values await second transcription | ideal v=(4,541,324,130,389); v=5,384; vW=389; defined vNW=4,995; VR=.072; LCRR=2, NWL=0; LCMIN=778; LMAX=6,405 ft; density capacity 4,593 veh/h vs demand 4,150; LCW=960; printed LCNW=861/LCALL=1,821; W=.455; Sw=45.9, Snw=45.8, S=45.8 mi/h; D=39.2 pc/mi/ln; LOS E | speed/density ±0.05; capacity ±0.5; LOS exact; do not assert LCNW/LCALL until ambiguity resolution |

No `references/weaving_example_inputs.yaml` is created: before Phase 2 it
would imply a runtime-ready fixture despite the Example 3 ambiguity and absent
engine.  The evidence above is the Phase 1 inventory.

## Phase 2 implementation blueprint and entry conditions

Create `src/hcmcalc/weaving/{__init__,models,validation,coefficients,method}.py`
only after the entry gate passes.  Add a focused helper module only for
configuration/movement mapping or lane-change branching.  First implement
frozen typed models and strict whitelist validation, then source-tagged
coefficients/tables, movement-flow/LMAX/capacity calculations, then
lane-changing and speed/density/LOS.  Add equation, units, boundary,
configuration, unknown-input, capacity-null, and no-extrapolation tests before
each next layer.  Finally add independently reviewed Example 1--3 input and
expected-output fixtures and regressions.

Reuse `core/audit.py` and `core/exceptions.py` unchanged.  Phase 2 may extract
a neutral Chapter 12 PCE/FFS helper only after proving equation/table identity
and retaining existing freeway/multilane regressions; it must not reuse their
capacity, speed, density, or LOS helpers.  It must not add UI, registry,
project, exports, or fixtures that claim an engine before calculation
qualification.

Entry gate: select HCM version explicitly; independently transcribe/visual
review Example 1--3 inputs/intermediates; resolve/document Example 3 tolerance;
map selected Chapter 12 FFS/PCE/SAF/CAF domains; and approve common-fHV scope.
