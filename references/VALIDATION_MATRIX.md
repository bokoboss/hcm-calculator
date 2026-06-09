# Validation Matrix

This matrix defines the validation work required before calculation outputs are considered correct and before UI expansion proceeds.

| ID | Facility Type | HCM Source | Example Problem | Inputs Fixture | Expected Outputs Fixture | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TLH-CH15-001 | Two-Lane Highway | HCM 7th Edition Chapter 26 | Example Problem 1 | `references/example_inputs.yaml` | `references/expected_outputs.yaml` | Implemented example only | Level, straight Passing Constrained segment only |
| TLH-CH15-002 | Two-Lane Highway | HCM 7th Edition Chapter 26 | Example Problem 2 | `references/example_inputs.yaml` | `references/expected_outputs.yaml` | Implemented example only | Passing Constrained segment with horizontal curve speed adjustment only |
| TLH-CH15-003 | Two-Lane Highway | HCM 7th Edition Chapter 26 | Example Problem 3 | `references/example_inputs.yaml` | `references/expected_outputs.yaml` | Implemented example only | Level, straight five-segment facility with Passing Constrained, Passing Lane, and Passing Zone segments |
| TLH-CH15-004 | Two-Lane Highway | HCM 7th Edition Chapter 26 | Example Problem 4 | `references/example_inputs.yaml` | `references/expected_outputs.yaml` | Implemented example only | Mountainous six-segment facility with upgrades, downgrades, horizontal curves, a Passing Lane, and downstream adjustment |
| MLH-LOS-001 | Multilane Highway LOS | HCM 7th Edition Chapter 26 | TBD | TBD | TBD | Future | Future method target |

## Required Validation Gates

- Inputs must be mapped from published HCM Chapter 26 examples.
- Expected outputs must include tolerances and rounding rules.
- Validation tests must pass before output claims are shown in the UI.
- Reviewer sign-off should be recorded for production-ready methods.
