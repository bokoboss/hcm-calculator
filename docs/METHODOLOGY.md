# Methodology

## Scope

This document will map implemented calculations to HCM source methodology. The initial target is HCM 7th Edition Chapter 15 Two-Lane Highway motorized vehicle analysis.

## Current Status

The full calculation engine is not implemented in this scaffold. Methodology mapping, formulas, units, assumptions, intermediate values, and validation fixtures must be completed before production use.

## Initial Method Target

- HCM 7th Edition Chapter 15: Two-Lane Highway motorized vehicle analysis

## Future Method Target

- Multilane Highway LOS

## Method Documentation Requirements

For each implemented method, document:

- HCM edition and chapter reference
- Facility type
- Applicability limits
- Required inputs and units
- Optional inputs and defaults
- Formula sequence
- Adjustment factors
- Intermediate values
- Output measures
- LOS thresholds where applicable
- Rounding rules
- Known exclusions and assumptions

## Validation Requirement

Correctness must be validated against HCM Chapter 26 example problems before UI expansion. Each validation case should include:

- Example problem identifier
- Source chapter and edition
- Input mapping notes
- Expected outputs
- Tolerances
- Differences from published example assumptions, if any
- Reviewer notes

## Implementation Rule

Calculation code should return auditable result objects containing final outputs and intermediate values. It should not directly render UI elements.

## Implemented Validation Scope

HCM Chapter 26 Two-Lane Highway Example Problem 4 is implemented for its exact
six-segment mountainous facility. The validated vertical alignment scope is
limited to level or 3% downgrade Class 1 segments, 4%/1.3-mi and 6%/0.5-mi
Class 4 segments, and a 6%/1.0-mi Class 5 segment. Other nonlevel grade and
length combinations raise `MethodNotImplementedError`.

The implementation applies HCM Chapter 15 Equations 15-1 through 15-39 as
needed by the example, including horizontal-curve speed adjustment, passing
lane midpoint follower density, downstream adjustment, and facility
length-weighted follower density. The facility summary follows the Chapter 26
example's displayed one-decimal segment-density convention.

Known limitation: the macroscopic method may not fully represent interactions
across the example's long upgrade. Detailed design evaluation may require
microsimulation.
