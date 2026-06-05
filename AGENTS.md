# AGENTS.md

## Project Direction

This repository is an auditable HCM calculator scaffold. Treat engineering correctness, traceability, and validation as primary product requirements.

## Current Scope

- Python 3.12 package
- pytest test suite
- Calculation logic independent from UI
- Planned optional Streamlit local UI
- Initial method target: HCM 7th Edition Chapter 15 Two-Lane Highway motorized vehicle analysis
- Future method target: Multilane Highway LOS

## Constraints

- Do not implement the full calculation engine until methodology and validation fixtures are defined.
- Do not create a multi-page wizard.
- Preserve a single-page guided worksheet UI concept for engineering data entry.
- Keep method implementations facility-type aware so future HCM modules can be added without rewriting core contracts.
- Do not couple calculation modules to Streamlit or any UI framework.

## Quality Bar

- Every calculation method must expose auditable inputs, assumptions, intermediate values, and outputs.
- Method correctness must be validated against HCM Chapter 26 example problems before UI expansion.
- Tests should grow from placeholder smoke tests into method-level unit tests, validation fixture tests, and regression tests.

## Development Commands

```powershell
python -m pip install -e .[dev]
pytest
```
