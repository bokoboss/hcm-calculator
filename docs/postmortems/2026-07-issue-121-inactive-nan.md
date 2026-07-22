# Issue #121: Inactive UI Numeric Cells Submitted as NaN

Date: 2026-07-22

## Summary

The v0.8 Streamlit qualification suite exposed that blank optional numeric
cells from `st.data_editor` could arrive as `NaN`. The affected paths treated
those values as active inputs instead of inactive blanks.

## Impact

- Two-Lane Facility default AppTests failed because inactive
  `opposing_direction_volume_veh_h` cells were passed into Chapter 15 facility
  calculations.
- Two-Lane Segment horizontal-curve AppTests failed because tangent-row curve
  fields such as radius and superelevation were submitted as `NaN`.
- Project save/load and report exports could carry inactive facility `NaN`
  values unless the rows were normalized first.

## Root Cause

Streamlit represents blank optional numeric cells as non-finite floats. The UI
adapters checked only `None` or empty strings when deciding whether optional
fields were inactive. That allowed `NaN` to pass through calculation,
fingerprint, audit, project, and export boundaries.

## Fix

- Added canonical facility row normalization so inactive opposing-volume cells
  become `None`, passing-zone opposing volume remains finite and active, and
  project/audit/workflow paths use the same canonical row shape.
- Normalized optional horizontal-curve subsegment values during unit conversion
  so tangent-row blank fields become `None`.
- Added regression coverage for facility calculation, validation, fingerprint,
  project load/save, report exports, Streamlit AppTest, and the single-segment
  curve path.

## Validation

- `python -m pytest -q` passed with 1024 tests.
- Browser smoke evidence covered desktop English facility calculation, project
  save/reload, CSV and report JSON downloads, Thai calculated state, and narrow
  English calculated state.

## Prevention

Adapters that receive `st.data_editor` numeric columns should normalize
inactive optional values before calculation, fingerprinting, persistence, or
export. Regression tests should include non-finite blank-cell representations
for optional UI-only fields.
