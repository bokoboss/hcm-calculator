# Product Requirements Document

## Product Summary

The HCM Calculator is a local, auditable engineering calculator for Highway Capacity Manual analyses. It will initially focus on HCM 7th Edition Chapter 15 Two-Lane Highway motorized vehicle analysis, with a structure that can support multiple HCM facility types in the future.

## Users

- Transportation engineers
- Traffic operations analysts
- Engineering reviewers
- Agencies requiring transparent calculation records

## Initial Scope

The first implementation target is a single-page guided worksheet for HCM 7th Edition Chapter 15 Two-Lane Highway motorized vehicle analysis.

The initial scaffold does not include the full calculation engine. It establishes project structure, method boundaries, validation expectations, and UI requirements.

## Future Scope

Future calculation modules shall include Multilane Highway LOS and may include additional HCM facility types when validation data and methodology documentation are available.

## Functional Requirements

- Accept structured input data for facility analyses.
- Keep calculation methods independent from UI components.
- Produce auditable outputs, including assumptions and intermediate values.
- Support validation fixtures based on HCM Chapter 26 example problems.
- Allow future facility methods to register under a shared method interface.

## Non-Functional Requirements

- Python 3.12
- pytest for tests
- Streamlit may be used as an optional local UI dependency only.
- Deterministic calculations for identical inputs.
- Clear separation between domain models, calculation methods, validation fixtures, and UI.

## Explicit Non-Goals For Initial Scaffold

- No full calculation engine yet.
- No production UI yet.
- No multi-page wizard.
- No unvalidated HCM output claims.

## Acceptance Criteria

- Project installs locally.
- pytest runs successfully.
- Documentation states that validation against HCM Chapter 26 example problems is required before UI expansion.
