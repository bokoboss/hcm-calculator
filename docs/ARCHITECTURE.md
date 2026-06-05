# Architecture

## Design Principles

- Calculation logic is independent from UI.
- HCM facility types are modeled as separate method modules behind shared contracts.
- Inputs and outputs are structured and serializable for validation and audit records.
- Intermediate values are first-class outputs, not hidden implementation details.

## Package Structure

```text
src/hcmcalc/
  __init__.py
  core/           Shared contracts, exceptions, audit result structures
  models/         Typed input and output models
  methods/        Facility-specific calculation methods
  validation/     Validation fixture loading and comparison helpers
  ui/             Optional UI entry points; no calculation logic
```

## Planned Method Organization

```text
methods/
  two_lane_highway_ch15.py
  multilane_highway_los.py
```

The initial scaffold includes placeholders only. Future method files should implement shared interfaces from `hcmcalc.core`.

## Data Flow

1. UI or API gathers engineering inputs.
2. Inputs are normalized into typed domain models.
3. A facility-specific method computes outputs and intermediate values.
4. Results are returned as an auditable calculation record.
5. Validation tests compare calculated values against reference examples and tolerances.

## UI Boundary

The UI layer may import method interfaces and domain models, but method modules must not import UI code or Streamlit.

## Validation Boundary

Validation fixtures live under `references/` until they become test fixtures. HCM Chapter 26 example problems are the required benchmark source before calculation outputs can be treated as correct.

## Extension Strategy

New facility types should add:

- A method module under `src/hcmcalc/methods/`
- Domain input/output models as needed
- Validation fixtures and expected outputs
- Unit and validation tests
- Documentation updates in `docs/METHODOLOGY.md`
