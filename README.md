# HCM Calculator

Auditable Python calculator for bounded Highway Capacity Manual (HCM) workflows.

The current v0.1 calculator-first MVP provides single-page, auditable
worksheets for supported Two-Lane Highway, Basic Freeway Segment, and
Multilane Segment workflows. It does **not** implement general HCM facility
analysis. Validation examples remain regression and reference evidence, and
are intentionally hidden from product navigation.

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
- HCM Chapter 26 Two-Lane Highway Example Problems 1 through 4
  (`TLH-CH15-001` through `TLH-CH15-004`) as validation evidence
- HCM7 Multilane Basic Segment engine v0.1 for bounded one-direction
  Multilane Highway Segment analysis within the implemented HCM scope. Chapter
  26 Multilane Highway Example Problem 4 remains regression evidence and
  optional defaults.
- HCM7 Chapter 12 Basic Freeway Segment engine v0.1 under
  `src/hcmcalc/freeway/`, limited to one-direction, one-segment,
  uninterrupted-flow Basic Freeway Segment calculations with measured or
  estimated FFS, general-terrain level/rolling heavy-vehicle PCEs, audit
  outputs, unsupported-scope guardrails, and Chapter 26 Example Problem 1
  validation fixtures
- Chapter 26 second-case inventory documenting that no additional compatible
  Multilane Highway motorized-vehicle validation case is available in the
  supplied example-problem reference
- Streamlit Manual Single Segment Calculator, Manual Facility Calculator v0.1,
  Manual Multilane Highway Segment v0.1, and Manual Basic Freeway Segment
  Calculator v0.1 with a shared result summary panel
- Manual Multilane Save/Load and CSV, Excel, Markdown, and Report JSON export
  integration using `project_type = manual_multilane_v0`
- Manual Basic Freeway Segment Save/Load and CSV, Excel, Markdown, and Report
  JSON export integration using `project_type = manual_basic_freeway_v0`
- Unit and validation fixture tests

Not implemented yet:

- Full HCM Chapter 15 calculation engine
- General facility manual input
- Multilane Highway facility, ramp, weaving, merge/diverge, managed lane, work
  zone, reliability, and unsupported PCE table expansion workflows
- Basic Freeway ramps, weaving, merge/diverge, managed lanes, work zones,
  reliability, facility/corridor workflows, and specific-grade PCE tables
- Production validation dataset

## Supported Workflows

The app is an engineering calculator, not an example-template viewer. Presets
and examples provide starting values and validation references only. The primary
workflow is: choose calculator, enter inputs, run calculation, review results,
inspect calculation details and audit / intermediate values, then Save Project
or Export / Report.

Currently supported:

- **Two-Lane Highway:** Manual Single Segment Calculator, Manual Facility
  Calculator, validated Chapter 26 example-backed paths where available,
  Save/Load, and Export/reporting. Only implemented HCM7 Chapter 15 paths are
  supported; unsupported combinations remain guarded.
- **Multilane Highway:** Manual Multilane Segment Calculator for bounded
  one-direction Multilane Highway Segment analysis, Chapter 26 Example 4
  optional defaults and regression evidence, Metric/Imperial UI-boundary
  conversion, Save/Load, and Export/reporting. It is not a Basic Freeway
  calculator and does not support ramp, weaving, merge/diverge, facility,
  managed lane, work zone, or reliability workflows.
- **Basic Freeway:** Manual Basic Freeway Segment Calculator for bounded
  Chapter 12 one-direction, one-segment uninterrupted-flow analysis,
  Chapter 26 Example 1 optional defaults and regression evidence,
  Metric/Imperial UI-boundary conversion, Save/Load, and Export/reporting. It
  is not a general freeway facility calculator and does not support ramps,
  weaving, merge/diverge, managed lanes, work zones, reliability,
  facility/corridor workflows, specific-grade PCE tables, or mountainous-terrain
  PCE tables.

See [Supported Workflows](docs/supported_workflows.md) for the concise app-wide
scope summary.

## Run Locally

Use this exact two-step Windows workflow from the repository root:

1. Run `setup_app.bat` once for first-time setup, and again whenever you need
   to refresh dependencies.
2. Run `run_app.bat` for every normal launch.

`run_app.bat` never installs or upgrades packages. It opens the calculator in
your browser using `src\hcmcalc\ui\streamlit_app.py` and tells you to run
setup if Python 3.12 or `.venv` is unavailable. See the [local quick-start
guide](docs/user_quick_start.md) for the matching PowerShell commands and
troubleshooting.

## Local Setup

Requires Python 3.12.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
```

Streamlit is listed as an optional UI dependency only. Install it with the development
dependencies to run the calculator:

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

Run the single-page calculator from the repository root:

```powershell
streamlit run src/hcmcalc/ui/streamlit_app.py
```

The single-page app provides six modes:

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
- **Validation Examples** remain fixture-backed regression and QA evidence;
  they are intentionally not a product-navigation workflow.
- **Manual Facility Calculator v0.1** is a limited template-backed facility
  workflow anchored to validated Example Problems 3 and 4. It provides a
  guarded segment table, facility and segment results, warnings, assumptions,
  audit details, CSV/Excel/Markdown/report JSON exports, downloadable result
  JSON, and guarded Facility Project
  Save/Load JSON using `project_type = manual_facility_v0`. Segment sequence, type,
  terrain/curve context, passing-lane placement, and downstream adjustment
  context remain controlled by the selected template.
- **Manual Multilane Highway Segment v0.1** is a bounded worksheet for
  one-direction Multilane Highway Segment analysis within the implemented HCM
  scope. Chapter 26 Example Problem 4 EB and WB remain optional defaults and
  regression evidence. It converts Metric inputs to engine-native Imperial
  values at the UI boundary, and converts speed and density back to Metric for
  display. Engine formulas and engine-native outputs remain unchanged.
  Unsupported methodology branches are rejected by the existing engine
  guardrails.
  After a successful calculation, this mode supports guarded Project JSON
  Save/Load using `project_type = manual_multilane_v0` and CSV, Excel `.xlsx`,
  Markdown, and Report JSON exports. Saved projects preserve displayed values
  in the selected unit system and normalized engine-native Imperial inputs.
  Reports display the selected unit system and label engine-native Imperial
  values explicitly where included.
- **Manual Basic Freeway Segment Calculator** is a calculator-first v0.1
  worksheet for one-direction, one-segment uninterrupted-flow Basic Freeway
  Segment analysis within the implemented HCM7 Chapter 12 scope. It exposes
  Setup, Roadway / Geometry, Traffic, Advanced / Optional, Results, Details,
  Audit, and Full JSON sections for general-purpose lanes only. The Chapter 26
  Example 1 input preset supplies optional starting values from
  `references/freeway_example_inputs.yaml`; it remains regression evidence, not
  the supported methodology boundary. Metric inputs are converted to
  engine-native Imperial values at the UI boundary and speed/density outputs are
  converted back for display. The page calls only the existing
  `src/hcmcalc/freeway` engine and does not add or change formulas. Save/Load
  controls are compactly placed around the calculator inputs: load sits near
  the optional defaults controls and save sits below the worksheet inputs.
  After a successful calculation, an **Export / Report** section provides CSV,
  Excel `.xlsx`, Markdown, and report-friendly JSON downloads. Project JSON uses
  `project_type = manual_basic_freeway_v0`, preserves displayed UI values,
  engine-native Imperial inputs, limitations, warnings, assumptions, and any
  matching current result. Export/reporting preserves the same bounded Basic
  Freeway Segment v0.1 scope only.
- **Supported Workflows** summarizes current Two-Lane Highway, Multilane
  Highway, Basic Freeway, Save/Load, Export / Report, and validation-reference
  scope in the app. Limitations are visible but kept secondary to the calculator
  workflow.

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
  v0.1, guarded Manual Multilane v0.1, and bounded Manual Basic Freeway
  Segment v0.1 results. Exports use the selected UI display unit system, label
  units explicitly, include workflow limitations, and format the existing
  calculated result without changing calculation behavior.
- No general mountainous grade table; unsupported grade/length combinations are rejected
- No downstream corridor effects for single passing-lane mode
- Passing Lane calculation remains limited to the engine's validated Class 1, 8% heavy-vehicle path
- Horizontal curves remain limited to the validated Example Problem 2 path; other
  segment types, terrain combinations, and subsegment structures are rejected.
  Curve setup generation does not expand this single-segment validated scope
- Manual Multilane Highway Segment v0.1 is bounded to one-direction segment
  analysis within the implemented HCM scope. Save/Load and reporting use
  `project_type = manual_multilane_v0`; Metric/Imperial selection changes only
  UI inputs and displayed/report values; calculations remain engine-native
  Imperial.
- Multilane Highway v0.1 is not facility, ramp, weaving, merge/diverge,
  managed-lane, work-zone, or reliability support. Chapter 26 Example Problem
  4 eastbound and westbound remain regression evidence; the remaining Chapter
  26 examples are Basic Freeway, mixed-flow freeway, adverse-weather Basic
  Freeway, or managed-lane cases and cannot safely serve as a second Multilane
  validation case.
- Manual Basic Freeway Segment Save/Load and reporting are supported only for
  `project_type = manual_basic_freeway_v0` and the bounded implemented Chapter
  12 Basic Freeway Segment envelope. Basic Freeway ramps, weaving,
  merge/diverge, managed lanes, work zones, reliability analysis,
  facility/corridor workflows, specific-grade Basic Freeway PCE tables, and
  mountainous-terrain PCE tables remain unsupported. The Manual Basic Freeway
  Segment Calculator v0.1 is not a general freeway facility calculator;
  BF-CH26-001 remains optional defaults and Chapter 26 regression evidence.
- User-supplied Multilane adjusted free-flow speed and driver-population
  adjustment inputs remain unsupported.
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

See the
[Basic Freeway Segment Implementation Plan](docs/basic_freeway_implementation_plan.md)
for the separately scoped architecture, implemented engine v0.1 scope, product
direction, and validation-led future phases for HCM7 Chapter 12 Basic Freeway
Segment support.
