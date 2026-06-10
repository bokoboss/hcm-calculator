# HCM Calculator

Auditable Python scaffold for Highway Capacity Manual (HCM) calculations.

This project is intentionally in an early, example-scoped state. It does **not** yet implement a general HCM Chapter 15 calculation engine. The first supported analysis target is HCM 7th Edition Chapter 15 Two-Lane Highway motorized vehicle analysis. The architecture is prepared to support additional HCM facility types later, including Multilane Highway LOS.

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
- HCM Chapter 26 Two-Lane Highway Example Problems 1 through 4 (`TLH-CH15-001` through `TLH-CH15-004`)
- Streamlit Manual Single Segment Calculator and Validated examples / QA viewer
- Unit and validation fixture tests

Not implemented yet:

- Full HCM Chapter 15 calculation engine
- Full facility manual input
- Multilane Highway LOS calculations
- Production validation dataset

## Local Setup

Requires Python 3.12.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
```

Streamlit is listed as an optional UI dependency only. Install it with the development
dependencies to run the validated-case viewer:

```powershell
python -m pip install -e .[dev,ui]
```

Calculation logic and the CLI remain usable without Streamlit installed.

## Running Tests

Run the full test suite from the repository root:

```powershell
py -m pytest
```

## CLI Usage

Run a validated fixture case and print its auditable result as JSON:

```powershell
py -m hcmcalc run references/example_inputs.yaml --case TLH-CH15-001
py -m hcmcalc run references/example_inputs.yaml --case TLH-CH15-004
```

The CLI currently supports validated example fixtures only.

## Streamlit Calculator

Run the single-page validated-case viewer from the repository root:

```powershell
streamlit run src/hcmcalc/ui/streamlit_app.py
```

The single-page app provides two modes:

- **Manual Single Segment Calculator** accepts one straight Two-Lane Highway
  segment using Metric inputs by default or optional Imperial inputs. Unit
  conversion occurs only in the UI/manual adapter; the calculation engine keeps
  its existing imperial-native contract. The result view displays selected
  metrics in the chosen unit system and preserves the full imperial-native
  engine result in the downloadable JSON.
- **Validated examples / QA** loads `references/example_inputs.yaml` and preserves
  Example Problems 1 through 4 validation behavior.

The engine and CLI validation behavior remains based on the existing validated
fixtures. CLI inputs, outputs, and JSON schema are unchanged.

Manual v0.1 scope:

- HCM 7th Edition Chapter 15 Two-Lane Highway
- Motorized Vehicle LOS
- One segment only
- Passing Constrained, Passing Zone, and Passing Lane segment types
- Level terrain and narrowly validated mountainous terrain combinations
- Passing Zone requires opposing-direction volume
- Passing Constrained uses the implemented HCM 1,500 veh/h opposing-flow assumption

Limitations:

- No full facility manual input yet
- No general mountainous grade table; unsupported grade/length combinations are rejected
- No downstream corridor effects for single passing-lane mode
- Passing Lane calculation remains limited to the engine's validated Class 1, 8% heavy-vehicle path
- No Multilane Highway yet
- No report export yet; full result JSON download is available

## Repository Layout

```text
docs/                       Product, architecture, UI, and methodology docs
references/                 Validation fixtures and example data
src/hcmcalc/                Python package
tests/                      Unit and validation fixture tests
```

## Validation Requirement

HCM 7th Edition Chapter 26 Two-Lane Highway Example Problems 1 through 4 (`TLH-CH15-001` through `TLH-CH15-004`) are implemented and validated as the current baseline. Manual single-segment mode reuses those formula paths and coefficient tables, but only the listed v0.1 combinations are supported and unsupported scope is rejected.

Before UI expansion or any production use, calculation correctness must continue to be validated against relevant HCM Chapter 26 example problems. Validation artifacts should document source examples, input mappings, expected outputs, tolerances, and reviewer sign-off.

See the [Chapter 15 Single-Segment Gap Analysis](docs/ch15_single_segment_gap_analysis.md)
for the prioritized roadmap toward a more complete manual single-segment
workflow.
