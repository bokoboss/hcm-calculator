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
