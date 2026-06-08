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
- Methodology and validation references
- HCM Chapter 26 Example Problems 1, 2, and 3
- Unit and validation fixture tests

Not implemented yet:

- Full HCM Chapter 15 calculation engine
- HCM Chapter 26 Example Problem 4
- Streamlit worksheet UI
- Multilane Highway LOS calculations
- Production validation dataset

## Local Setup

Requires Python 3.12.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
```

Streamlit is listed as an optional UI dependency only. Calculation logic must remain usable without Streamlit installed.

## Running Tests

Run the full test suite from the repository root:

```powershell
py -m pytest
```

## Repository Layout

```text
docs/                       Product, architecture, UI, and methodology docs
references/                 Validation fixtures and example data
src/hcmcalc/                Python package
tests/                      Unit and validation fixture tests
```

## Validation Requirement

HCM 7th Edition Chapter 26 Example Problems 1, 2, and 3 are implemented as the current validation baseline. Additional example problems, including Example Problem 4, are not yet implemented.

Before UI expansion or any production use, calculation correctness must continue to be validated against relevant HCM Chapter 26 example problems. Validation artifacts should document source examples, input mappings, expected outputs, tolerances, and reviewer sign-off.
