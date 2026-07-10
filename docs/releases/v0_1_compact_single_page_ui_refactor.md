# Compact Single-Page UI Refactor release note

## What changed

The calculator now uses a consistent compact, single-page worksheet workflow
for Two-Lane Segment, Two-Lane Facility, Multilane Segment, and Basic Freeway
Segment analysis. Each worksheet follows the same structure: setup, guided
inputs, results, calculation details, audit/intermediate values, project
save/load, and export/report controls. The visible mode chooser contains only
supported calculator workflows; validation examples remain internal regression
evidence.

## What did not change

This refactor does not change calculation engines, methodology, validation
fixtures, tolerances, expected outputs, project schemas, or export formats.
It does not add any supported HCM scope.

## Release validation — 2026-07-10

| Check | Result | Evidence |
| --- | --- | --- |
| Required editable install | Pass | ` .\\.venv\\Scripts\\python.exe -m pip install -e ".[dev,ui]"` completed. |
| Full regression suite | Pass | ` .\\.venv\\Scripts\\python.exe -m pytest`: 779 passed. |
| Representative calculation and I/O regression set | Pass | Fixture, project I/O, reporting, freshness, and all worksheet tests: 167 passed. This covers Two-Lane Segment/Facility, Multilane Example 4 eastbound and westbound, and Basic Freeway Example 1. |
| Clean setup | Pass | New temporary Python 3.12 virtual environment installed `.[dev,ui]`; `hcmcalc` and Streamlit 1.59.1 imported successfully. |
| Streamlit smoke | Pass | Local application launched successfully; Two-Lane Segment, Two-Lane Facility, Multilane Segment, Basic Freeway Segment, and Supported Workflows rendered without errors. Each calculator ran successfully. |
| Project and export workflow | Pass | Guarded project JSON round trips and CSV, Excel, Markdown, and report JSON export tests passed. Browser verification confirmed the current-result export controls after recalculation. |
| Stale-result protection | Pass | Browser verification changed the Two-Lane unit system after a calculation: status changed to `Input changed — recalculate required` and export was withheld. Recalculation restored CSV, Excel, Markdown, and report JSON actions. |
| Release self-review | Pass | No engine, fixture, tolerance, expected-output, project-schema, or export-format changes. `mockups/` remains untracked and excluded. |
