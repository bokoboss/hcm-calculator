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
- HCM7 Multilane Basic Segment engine v0.1, limited to the eastbound and
  westbound Chapter 26 Multilane Highway Example Problem 4 validation path,
  with ML-2 validation, audit, boundary, and unsupported-scope hardening
- Chapter 26 second-case inventory documenting that no additional compatible
  Multilane Highway motorized-vehicle validation case is available in the
  supplied example-problem reference
- Streamlit Manual Single Segment Calculator, Manual Facility Calculator v0.1,
  Manual Multilane Highway Segment v0.1, and Validated examples / QA viewer
- Manual Multilane Save/Load and CSV, Excel, Markdown, and Report JSON export
  integration using `project_type = manual_multilane_v0`
- Unit and validation fixture tests

Not implemented yet:

- Full HCM Chapter 15 calculation engine
- General facility manual input
- General Multilane Highway LOS calculations beyond Chapter 26 Example Problem 4
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

The single-page app provides four modes:

- **Manual Single Segment Calculator** accepts one straight or horizontal-curve
  Two-Lane Highway segment using Metric inputs by default or optional Imperial
  inputs. Horizontal-curve support uses the currently validated Example Problem
  2 structured-subsegment calculation path. Horizontal curve mode includes a
  compact curve setup section that generates evenly distributed editable
  subsegments; users may still review and edit every subsegment manually. Unit
  conversion occurs only in the UI/manual adapter; the calculation engine keeps
  its existing imperial-native contract. The result view displays selected
  metrics in the chosen unit system and preserves the full imperial-native
  engine result in the downloadable JSON. After a successful calculation, an
  **Export / Report** section provides CSV, Excel `.xlsx`, Markdown, and
  report-friendly JSON downloads.
- **Validated examples / QA** loads `references/example_inputs.yaml` and preserves
  Example Problems 1 through 4 validation behavior.
- **Manual Facility Calculator v0.1** is a limited template-backed facility
  workflow anchored to validated Example Problems 3 and 4. It provides a
  guarded segment table, facility and segment results, warnings, assumptions,
  audit details, CSV/Excel/Markdown/report JSON exports, downloadable result
  JSON, and guarded Facility Project
  Save/Load JSON using `project_type = manual_facility_v0`. Segment sequence, type,
  terrain/curve context, passing-lane placement, and downstream adjustment
  context remain controlled by the selected template.
- **Manual Multilane Highway Segment v0.1** is a limited validated-path
  worksheet anchored only to Chapter 26 Example Problem 4 EB and WB. It
  prefills the supported fixture inputs in Metric or Imperial units, converts
  Metric inputs to engine-native Imperial values at the UI boundary, and
  converts speed and density back to Metric for display. Changing unit system
  or template resets the worksheet to the selected validated template. Engine
  formulas and engine-native outputs remain unchanged. Any edit outside the
  exact validated EB/WB path is rejected by the existing engine guardrails.
  After a successful calculation, this mode supports guarded Project JSON
  Save/Load using `project_type = manual_multilane_v0` and CSV, Excel `.xlsx`,
  Markdown, and Report JSON exports. Saved projects preserve displayed values
  in the selected unit system and normalized engine-native Imperial inputs.
  Reports display the selected unit system and label engine-native Imperial
  values explicitly where included.

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
- Straight alignment, plus horizontal curves for a level Passing Constrained
  segment using the validated Example Problem 2 11-subsegment structure

Limitations:

- Manual Facility Calculator v0.1 is not a general facility calculator.
- Arbitrary segment sequences, nonlevel facilities, horizontal/nonlevel
  combinations, passing-lane placement, and downstream adjustments remain
  unsupported.
- Facility Project Save/Load v0.1 is supported only for the guarded Example 3/4
  templates using `project_type = manual_facility_v0`. It does not imply
  general facility support; unsupported combinations remain guarded.
- Existing Manual Single Segment Save/Load using
  `project_type = manual_single_segment` remains supported.
- Export/reporting v0.1 supports Manual Single Segment, guarded Manual Facility
  v0.1, and guarded Manual Multilane v0.1 results. Exports use the selected UI
  display unit system, label units explicitly, include workflow limitations,
  and format the existing calculated result without changing calculation
  behavior.
- No general mountainous grade table; unsupported grade/length combinations are rejected
- No downstream corridor effects for single passing-lane mode
- Passing Lane calculation remains limited to the engine's validated Class 1, 8% heavy-vehicle path
- Horizontal curves remain limited to the validated Example Problem 2 path; other
  segment types, terrain combinations, and subsegment structures are rejected.
  Curve setup generation does not expand this single-segment validated scope
- Manual Multilane Highway Segment v0.1 provides only the Chapter 26 Example
  Problem 4 EB/WB validated-path UI. It is not a general Multilane Highway
  calculator. Save/Load and reporting are supported only for
  `project_type = manual_multilane_v0` and the exact validated templates.
  Metric/Imperial selection changes only UI inputs and displayed/report values;
  calculations remain engine-native Imperial.
- Multilane Highway v0.1 remains implemented-example-only. Example Problem 4
  eastbound and westbound are the only validated paths; boundary-tested helper
  behavior does not imply general Multilane Highway support. The remaining
  Chapter 26 examples are Basic Freeway, mixed-flow freeway, adverse-weather
  Basic Freeway, or managed-lane cases and cannot safely serve as a second
  Multilane validation case.
- Basic Freeway, ramps, weaving, merge/diverge, managed lanes, work zones,
  reliability analysis, and facility/corridor workflows remain unsupported.
- User-supplied base/adjusted free-flow speed and driver-population adjustment
  inputs remain unsupported.
- PDF and DOCX report export are not implemented.
- Export availability does not imply broader Chapter 15 methodology support.

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

See the
[Chapter 15 Calculator Coverage Status](docs/ch15_calculator_coverage_status.md)
for a calculator-facing inventory of current engine, UI, test, segment-type,
and workflow coverage and the recommended next capability PR.

See the
[Multilane Highway Implementation Plan](docs/multilane_highway_implementation_plan.md)
for the separately scoped reference inventory, architecture proposal, and
validation-led implementation phases for a future Multilane Highway calculator.
