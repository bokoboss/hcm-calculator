# Phase 14.2 Engine Qualification: Versioned Merge and Diverge Segments

## Scope

- Starting `main` SHA: `5a30b2495ab224d5144d92907b3c67b15342b4f2`.
- Qualified method versions: `hcm_7_0` isolated-only Merge Segment and Diverge Segment.
- Known but unqualified method version: `hcm_7_1`.
- Public APIs:
  - `MergeSegmentMethod(version="hcm_7_0").calculate(inputs)`
  - `DivergeSegmentMethod(version="hcm_7_0").calculate(inputs)`

The implemented Phase 14.2 scope is isolated, general-purpose freeway, one-lane
right-side ramp junction operational analysis for 2-4 freeway lanes per
direction. Merge requires explicit upstream freeway demand, on-ramp demand,
acceleration-lane length, freeway FFS, ramp FFS, PHF, heavy vehicles, SAF/CAF,
and geometry evidence. Diverge requires the corresponding off-ramp demand and
deceleration-lane length.

Excluded and guarded: adjacent-ramp branches, left-side ramps, two-lane ramps,
lane additions, lane drops, option lanes, major merge/diverge areas, managed
lanes, C-D roads, multilane highway approximate use, service-volume analysis,
ramp metering, work zones, queues, delay, spillback, product UI, persistence,
exports, navigation, localization, and assets.

## Sources

The governing source was the local licensed HCM 7.0 PDF: Chapter 14 printed
pp. 14-5 through 14-28 and Chapter 28 printed pp. 28-2 through 28-14. No
licensed PDF, extracted source text, page images, screenshots, OCR output, or
copied source tables are committed.

Existing Chapter 12 helpers are reused only for source-identical foundations:
freeway FFS estimation, basic freeway capacity, level/rolling general-terrain
PCE, and heavy-vehicle adjustment factor.

## Implementation Mapping

| Area | Merge | Diverge |
| --- | --- | --- |
| Demand conversion | Eq. 14-1 with separate freeway/ramp PHF and fHV | Eq. 14-1 with separate freeway/ramp PHF and fHV |
| Lane distribution | Eq. 14-2 and isolated branches from Exhibit 14-8 | Eq. 14-8 and isolated branches from Exhibit 14-9 |
| Reasonableness | Eqs. 14-14 through 14-19 | Eqs. 14-14 through 14-19 after diverge-specific v12 |
| Capacity | Exhibit 14-10, Exhibit 14-12, Eq. 14-21 | Exhibit 14-10, Exhibit 14-12, Eq. 14-21 |
| Density/LOS | Eq. 14-22 and Exhibit 14-3 | Eq. 14-23 and Exhibit 14-3 |
| Speed | Exhibits 14-13 and 14-15 for stable cases | Exhibits 14-14 and 14-15 for stable cases |

## Official Example Results

`references/merge_diverge_example_inputs.yaml` contains compatible runtime
fixtures:

| Example | Compatibility | Expected |
| --- | --- | --- |
| Chapter 28 Example 1 | isolated merge runtime fixture | vF 2,918 pc/h; vR 625 pc/h; density 28.2 pc/mi/ln; LOS D; SR 53.0 mi/h |
| Chapter 28 Example 3 merge component | eight-lane merge component; adjacent ignored by HCM lane distribution | adjusted v12 2,570 pc/h; density 27.2; LOS C; SR 56.2; all-lane speed 58.8 |
| Chapter 28 Example 3 diverge component | eight-lane diverge component; adjacent ignored by HCM lane distribution | adjusted v12 3,397 pc/h; density 31.1; LOS D; SR 50.7; all-lane speed 58.3 |

Examples 2 and 3's overlap interpretation and adjacent six-lane branches remain
documented but not exposed as general adjacent-ramp execution. Example 4 is
left-side and rejected. Example 5 is service-volume evidence and not a runtime
operational fixture.

## Independent Validation

Unit tests cover low/moderate isolated cases, each lane-count branch, six- and
eight-lane reasonableness adjustment, measured and estimated FFS, level/rolling
PCE path through Chapter 12 helpers, exact v/c continuation, v/c greater than
1.00 null speed/density behavior, maximum-desirable-flow warning without
automatic LOS F, malformed input, unknown keys, boolean/nonfinite rejection,
unsupported geometry, adjacent-ramp guards, and version isolation.

## Capacity and Null Semantics

Freeway and ramp roadway capacity failures produce LOS F with `None` speed and
density. Unrounded v/c equality at 1.00 continues to stable speed and density.
Maximum desirable influence-area flow exceedance is a warning only; the stable
prediction is preserved with interpretation limitations unless a roadway
capacity check also fails.

## Adjacent-Ramp Status

Adjacent-ramp branches are not qualified in this first isolated engine. Any
`adjacent_ramp_context` other than `isolated` raises `UnsupportedScopeError`.
This prevents silently treating adjacent ramps as isolated.

## HCM 7.1 Status

`hcm_7_1` is registered as known but unqualified for both method families.
Dispatch raises `UnsupportedScopeError`; there are no HCM 7.1 coefficients,
imports, placeholder results, or fallback to HCM 7.0.

## Defects and Corrections

No Phase 14.1 assumption was broadened. The only scope reduction is explicit:
adjacent-ramp branches are deferred until independent branch examples and
boundary tests are completed.

Chapter 28 Example 3's merge all-lane speed appears internally inconsistent:
applying Exhibit 14-15 to the printed intermediate values gives approximately
58.2 mi/h, while the example reports 58.8 mi/h. The engine follows the equation
chain with unrounded values and the fixture uses a wider tolerance for this
single display value. No example-specific runtime branch was added.

## Phase 14.3 Entry Gate

Phase 14.3 may build product UI only on the version-pinned APIs above. The UI
must preserve explicit method/version identity, structured geometry fields,
component PHF/HV provenance, capacity/null semantics, and the isolated-only
adjacent-ramp guard unless a later engine qualification broadens scope.
