# Validation Matrix

This matrix defines the validation work required before calculation outputs are considered correct and before UI expansion proceeds.

| ID | Facility Type | HCM Source | Example Problem | Inputs Fixture | Expected Outputs Fixture | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TLH-CH15-001 | Two-Lane Highway | HCM 7th Edition Chapter 26 | TBD | `references/example_inputs.yaml` | `references/expected_outputs.yaml` | Not started | Required before UI expansion |
| MLH-LOS-001 | Multilane Highway LOS | HCM 7th Edition Chapter 26 | TBD | TBD | TBD | Future | Future method target |

## Required Validation Gates

- Inputs must be mapped from published HCM Chapter 26 examples.
- Expected outputs must include tolerances and rounding rules.
- Validation tests must pass before output claims are shown in the UI.
- Reviewer sign-off should be recorded for production-ready methods.
