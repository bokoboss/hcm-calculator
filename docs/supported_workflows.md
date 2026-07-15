# Supported Workflows

The app is an engineering calculator, not an example-template viewer. Examples
and presets provide starting values and validation references only.

The main workflow is:

1. Choose calculator.
2. Enter inputs.
3. Run calculation.
4. Review results.
5. Inspect calculation details and audit / intermediate values.
6. Save Project or Export / Report.

For the authoritative cross-method comparison of analysis unit, FFS/PCE modes,
capacity behavior, units, exports, and exclusions, see the
[supported methods matrix](methodology/supported_methods_matrix.md).

## Two-Lane Highway

Supported:

- Manual Single Segment Calculator
- Manual Facility Calculator
- validated Chapter 26 example-backed paths where available
- Save/Load
- Export/reporting

Limitations:

- only implemented HCM7 Chapter 15 paths
- unsupported combinations remain guarded

## Multilane Highway

Supported:

- Manual Multilane Segment Calculator
- bounded HCM Multilane Highway Segment one-direction analysis
- Chapter 26 Example 4 optional defaults and regression evidence
- measured FFS, or estimated FFS from posted speed and active roadway geometry
- two- and three-lane estimated FFS, including divided-median left-side clearance
- internal HCM PCE lookup or auditable external PCE override
- Metric/Imperial UI-boundary conversion
- Save/Load
- Export/reporting

Limitations:

- not a Basic Freeway calculator
- not ramp/weaving/merge/diverge/facility workflow
- internal PCE lookup is limited to printed truck mixtures and numeric table boundaries; use an external PCE otherwise
- estimated FFS is limited to two or three lanes per analysis direction
- above-capacity results are LOS F/capacity failure only; speed and density are not predicted
- unsupported combinations remain guarded

## Basic Freeway

Supported:

- Manual Basic Freeway Segment Calculator
- bounded Chapter 12 one-direction, one-segment uninterrupted-flow analysis
- Chapter 26 Example 1 optional defaults and regression evidence
- measured FFS or estimated FFS with active geometry inputs only
- internal level, rolling, and printed specific-grade PCE lookup, or an external PCE override with provenance
- Chapter 26 driver-population category with paired SAF/CAF, or explicitly governed SAF/CAF factors
- above-capacity LOS F/capacity failure without predicted speed or density
- Metric/Imperial UI-boundary conversion
- Save/Load
- Export/reporting

Limitations:

- not a general freeway facility calculator
- no ramps
- no weaving
- no merge/diverge
- no managed lanes
- no work zones
- no reliability
- no facility/corridor workflow
- no mountainous or mixed-flow PCE domains, unprinted truck mixes, or PCE extrapolation
- no oversaturated speed, density, queue, delay, or travel-time prediction

## Freeway Weaving Segment

Supported:

- HCM 7.0 qualified isolated freeway weaving operational analysis
- one-sided and two-sided configurations within the documented `N`/`NWL` envelope
- explicit movement volumes, option-lane status, lane-change values, and geometry provenance
- measured FFS or qualified estimated freeway FFS; level/rolling common heavy-vehicle path
- Metric/Imperial display conversion; English/Thai presentation; version-pinned project save/load
- CSV, Excel, Markdown, calculation JSON, and report JSON exports from current results

Limitations:

- HCM 7.1 is known but unqualified, unavailable in navigation, and rejected on project load
- C-D roadway, multilane weaving, Design/Sensitivity, multiple/overlapping weaves, queue/volume-served prediction, managed-lane/cross-weave, signal influence, ramp metering, and automatic movement geometry are unsupported
- `LS >= LMAX` is a stopping/handoff condition: no LOS is assigned; use applicable separate merge/diverge/basic-segment analysis
- above capacity is LOS F with capacity and `v/c`; speed and density are **Not predicted**, never zero

## Freeway Merge Segment

Supported:

- HCM 7.0 qualified isolated one-lane right-side on-ramp operational analysis
- 2-4 freeway lanes per analysis direction
- explicit acceleration-lane length `LA`
- upstream freeway and on-ramp demand in `veh/h`
- separate freeway and on-ramp PHF and heavy-vehicle percentages
- measured freeway FFS or Chapter 12 estimated freeway FFS; explicit ramp FFS
- level or rolling terrain
- original local configuration diagram visible by default
- Chapter 28 Example 1 and Example 3 merge-component validation/reference presets
- Metric/Imperial display conversion, English/Thai labels, project save/load, and CSV, Excel, Markdown, calculation JSON, and report JSON exports

Limitations:

- HCM 7.1 is known but unqualified and rejected on project load
- adjacent ramps, left-side ramps, two-lane ramps, lane additions, major merges, managed lanes, C-D roads, ramp metering, work zones, queues, delay, spillback, and service-volume/design analysis are unsupported
- capacity failure is LOS F with capacity and `v/c`; speed and density are **Not predicted**, never zero
- maximum desirable influence-area flow exceedance is warning-only unless a roadway capacity check also fails

## Freeway Diverge Segment

Supported:

- HCM 7.0 qualified isolated one-lane right-side off-ramp operational analysis
- 2-4 freeway lanes per analysis direction
- explicit deceleration-lane length `LD`
- upstream freeway and off-ramp demand in `veh/h`, with continuing freeway demand derived and checked
- separate freeway and off-ramp PHF and heavy-vehicle percentages
- measured freeway FFS or Chapter 12 estimated freeway FFS; explicit ramp FFS
- level or rolling terrain
- original local configuration diagram visible by default
- Chapter 28 Example 3 diverge-component validation/reference preset
- Metric/Imperial display conversion, English/Thai labels, project save/load, and CSV, Excel, Markdown, calculation JSON, and report JSON exports

Limitations:

- HCM 7.1 is known but unqualified and rejected on project load
- adjacent ramps, left-side ramps, two-lane ramps, lane drops, option lanes, major diverges, managed lanes, C-D roads, ramp metering, work zones, queues, delay, spillback, and service-volume/design analysis are unsupported
- capacity failure is LOS F with capacity and `v/c`; speed and density are **Not predicted**, never zero
- maximum desirable influence-area flow exceedance is warning-only unless a roadway capacity check also fails

## Validation Evidence

Validation examples are regression and reference evidence for implemented
fixture cases. They are not user-facing workflows or product modes, and they do
not broaden supported methodology scope.

## Cross-method result and persistence rules

- Use the same labels for genuinely shared concepts, but do not treat Two-Lane
  follower density as Multilane/Freeway density or facility outputs as segment
  outputs.
- Above-capacity Multilane and Basic Freeway results are LOS F/capacity-failure
  results; speed and density are **Not predicted**, not zero.
- Exports are available only for current results and use the stored engine
  result rather than recomputing methodology.
- A project loader reports whether a result is current, the project was
  migrated, or recalculation is required. See the
  [v0.4.1 release note](releases/v0_4_1_cross_method_consolidation.md) for the
  detailed contract.

