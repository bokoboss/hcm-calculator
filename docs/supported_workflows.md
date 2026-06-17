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
- Chapter 26 Example 4 EB/WB-compatible validated path
- Metric/Imperial UI-boundary conversion
- Save/Load
- Export/reporting

Limitations:

- not a Basic Freeway calculator
- not ramp/weaving/merge/diverge/facility workflow
- unsupported combinations remain guarded

## Basic Freeway

Supported:

- Manual Basic Freeway Segment Calculator
- bounded Chapter 12 one-direction, one-segment uninterrupted-flow analysis
- Chapter 26 Example 1 optional defaults and regression evidence
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
- no specific-grade or mountainous-terrain PCE tables

## Validation Evidence

Validation examples are regression and reference evidence for implemented
fixture cases. They are not user-facing workflows or product modes, and they do
not broaden supported methodology scope.

