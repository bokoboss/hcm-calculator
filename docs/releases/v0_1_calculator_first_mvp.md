# v0.1 Calculator-First MVP Release Notes

## Milestone Summary

v0.1 closes the current calculator-first UI and workflow-generalization
milestone. The product now presents supported engineering calculators as the
primary experience, with auditable results, details, assumptions, intermediate
values, and export/report actions kept close to the calculation workflow.
Validation examples remain important regression and QA evidence, but they are
not product navigation or a claim of broader methodology support.

## Supported Calculator Workflows

- Two-Lane Segment
- Two-Lane Facility
- Basic Freeway Segment
- Multilane Segment

All supported workflows retain calculation logic independent of Streamlit and
provide bounded, auditable inputs and results. Save/Load and available
export/report actions apply only within each workflow's implemented scope.

## Current Scope by Workflow

### Two-Lane Segment

The HCM 7th Edition Chapter 15 motorized-vehicle LOS worksheet supports one
segment at a time for implemented Passing Constrained, Passing Zone, and
Passing Lane paths. Level-terrain straight paths are user-input driven within
the implemented envelope. Mountainous and horizontal-curve combinations are
limited to the validation-backed scope guards; unsupported combinations are
explicitly rejected.

### Two-Lane Facility

The facility worksheet is a guarded, template-backed Chapter 15 workflow with
facility and segment results. It supports the implemented Example 3 and Example
4 facility contexts, selected editable values, Save/Load, and exports. It is
not yet a general facility editor: segment sequence, geometry, passing-lane
placement, and downstream context remain controlled by the selected template.

### Basic Freeway Segment

The HCM 7th Edition Chapter 12 worksheet supports one-direction, one-segment,
uninterrupted-flow, general-purpose Basic Freeway Segment analysis. It supports
measured or estimated free-flow speed, level or rolling general terrain, and
the implemented speed and capacity adjustment inputs. Chapter 26 Example 1 is
an optional preset and regression reference, not the supported-scope boundary.

### Multilane Segment

The HCM 7th Edition Chapter 12 worksheet supports bounded one-direction
Multilane Highway basic-segment analysis within the implemented input envelope.
Chapter 26 Example 4 eastbound and westbound remain optional defaults and
regression evidence. Metric/Imperial conversion occurs at the UI boundary;
engine calculations remain Imperial-native.

## What Changed in This Milestone

- Established a calculator-first UI, with the engineering worksheet as the
  primary product workflow.
- Hid Validation Examples from product navigation while preserving them as
  regression and QA evidence.
- Added a shared result summary panel across calculator workflows.
- Generalized Basic Freeway Segment wording and supported handling beyond an
  Example 1-only framing, without changing formulas or unsupported-scope
  guardrails.
- Generalized Multilane Segment wording and supported handling beyond an
  Example 4-only framing, without changing formulas or unsupported-scope
  guardrails.
- Hardened non-example coverage for the generalized Basic Freeway and
  Multilane input envelopes.

## Known Limitations

- Two-Lane Segment remains bounded by implemented and validation-backed
  vertical, horizontal-curve, and passing-lane combinations.
- Two-Lane Facility remains template-backed rather than a general facility
  analysis workflow.
- Basic Freeway Segment excludes ramps, weaving, merge/diverge, managed lanes,
  work zones, reliability, facility/corridor analysis, driver-population input,
  and specific-grade or mountainous-terrain PCE tables.
- Multilane Segment excludes facility/corridor, ramp, weaving, merge/diverge,
  managed-lane, work-zone, and reliability workflows; unsupported methodology
  branches remain guarded.
- PDF and DOCX report export are not implemented.

## Intentionally Out of Scope

This milestone does not change calculation formulas, test fixtures, project
JSON schemas, reports, exports, UI controls, or methodology contracts. It does
not claim a full HCM Chapter 15 or Chapter 12 engine, general freeway/facility
analysis, or production validation coverage.

## Running Tests

From the repository root:

```powershell
python -m pip install -e .[dev]
py -m pytest
```

## Running Streamlit

Install the optional UI dependency, then start the single-page calculator:

```powershell
python -m pip install -e .[dev,ui]
streamlit run src/hcmcalc/ui/streamlit_app.py
```

## Recommended Next Roadmap

1. Two-Lane Segment generalization audit.
2. Two-Lane Facility generalization after segment-level scope is stable.
3. Report/export hardening.
4. Additional validation cases.
