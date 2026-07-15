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

## Validation Evidence

Validation examples are regression and reference evidence for implemented
fixture cases. They are not user-facing workflows or product modes, and they do
not broaden supported methodology scope.

