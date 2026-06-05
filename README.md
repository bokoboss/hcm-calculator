# HCM Calculator

Auditable Python scaffold for Highway Capacity Manual (HCM) calculations.

This project is intentionally in an early scaffold state. It does **not** yet implement the full calculation engine. The first supported analysis target is HCM 7th Edition Chapter 15 Two-Lane Highway motorized vehicle analysis. The architecture is prepared to support additional HCM facility types later, including Multilane Highway LOS.

## Goals

- Keep calculation logic independent from the user interface.
- Support auditable engineering workflows with transparent inputs, assumptions, intermediate values, and outputs.
- Validate methodology against HCM Chapter 26 example problems before expanding the UI or adding production workflows.
- Provide a single-page guided worksheet concept for engineering data entry rather than a multi-page wizard.

## Current Status

Implemented:

- Project package scaffold
- Documentation scaffold
- Placeholder methodology and validation references
- Placeholder tests

Not implemented yet:

- Full HCM Chapter 15 calculation engine
- Streamlit worksheet UI
- Multilane Highway LOS calculations
- Production validation dataset

## Local Setup

Requires Python 3.12.

```powershell
python -m pip install -e .[dev]
pytest
```

Streamlit is listed as an optional UI dependency only. Calculation logic must remain usable without Streamlit installed.

## Repository Layout

```text
docs/                       Product, architecture, UI, and methodology docs
references/                 Validation fixtures and example data
src/hcmcalc/                Python package
tests/                      Placeholder test structure
```

## Validation Requirement

Before UI expansion or any production use, calculation correctness must be validated against relevant HCM 7th Edition Chapter 26 example problems. Validation artifacts should document source examples, input mappings, expected outputs, tolerances, and reviewer sign-off.
