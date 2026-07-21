# v0.8 Phase 15.3 Release Qualification

Status: release-qualified locally for PR review, CI, merge, and Issue #115 closure.

## Executive Result

Phase 15.3 qualifies the v0.8 unified UI package from the isolated release
worktree. The release fixed three installed/browser blockers:

- Two-Lane schematic assets were not packaged in the wheel.
- Runtime UI presets for Facility, Multilane, Basic Freeway, Weaving, Merge,
  Diverge, and the internal validation view depended on repository-relative
  `references/*.yaml` files.
- Multilane browser edits stayed hidden inside a Streamlit form, leaving stale
  report exports available after visible input changes.

The qualified source tree preserves numerical engines, project schemas,
fingerprints, calculation contracts, report fields, presets, and support scope.

## Baseline And Branch

- Required baseline SHA: `f16485329b451cf69cc61f9b59adb07ae3ed80d9`
- Continuation HEAD before final work: `230e3c015c97534077a56be3a6b349d2a0476232`
- Qualification branch: `codex/phase-15-3-release-qualification`
- Worktree: `C:\Users\kittipat_t\Documents\hcm-calculator-phase-15-3`
- Original dirty checkout: left untouched.

## Environment

- OS: Microsoft Windows 11 Pro 10.0.26200, 64-bit
- Python: 3.12.10
- Streamlit: 1.59.2
- Browser automation: Python Playwright 1.61.0 with installed system Chrome
- Browser executable:
  `C:\Program Files\Google\Chrome\Application\chrome.exe`
- Browser version: `150.0.7871.125`

## Wheel Evidence

Final candidate wheel:

- Version: `0.8.0`
- Wheel filename: `hcm_calculator-0.8.0-py3-none-any.whl`
- SHA-256:
  `4bf6a3bc2f60c890070d1e681843ef112864cd2b3fa3a542e3b5f6d274549989`
- Installed environment:
  `C:\Users\kittipat_t\AppData\Local\Temp\hcmcalc-phase15-3-final-wheel-0-8-0`

Installed-package provenance from outside the repository confirmed:

- `hcmcalc.__version__ == "0.8.0"`
- `hcmcalc.__file__` and `hcmcalc.ui.streamlit_app.__file__` resolved from
  `site-packages`.
- Packaged Two-Lane schematic, Weaving diagram, Merge/Diverge SVG assets, and
  Multilane, Basic Freeway, Weaving, and Merge preset YAML resources loaded
  from the installed package.

## Automated Results

- Compile check: `python -m compileall -q src tests` passed.
- Focused release qualification tests:
  `python -m pytest tests\unit\test_scaffold.py tests\unit\test_streamlit_app.py tests\unit\test_package_assets.py tests\unit\test_project_io.py tests\unit\test_reporting.py -q`
  passed with `159 passed`.
- Full repository suite: `python -m pytest -q` passed with `1016 passed`.
- Final wheel build: `python -m build --wheel` passed.
- Final installed Streamlit HTTP startup on port `8768` returned HTTP `200`.

## Browser Evidence

The browser matrix is closed in
`docs/ui/phase_15_3_browser_qualification_matrix.md`. Evidence is retained
under `output/playwright/phase15_3_release_qualification/` and remains
uncommitted.

Closed browser gates:

- Thai Weaving two-sided, capacity-failure, and long-segment handoff rows
  passed at 1280 px and 768 px.
- Project upload/load/error rows passed for all seven calculators: valid
  current-result project, stale-result project, wrong-type project, and
  malformed JSON project.
- Current-result report downloads with content inspection passed for all seven
  calculators. Weaving was recaptured on 2026-07-21 from the installed wheel at
  `continuation/downloads/weaving_recapture_hcm_ch13_weaving_segment_report_20260721_032755.json`.
- Stale export blocking passed in the real browser for Two-Lane Segment,
  Weaving, Merge, Diverge, Basic Freeway, and Multilane. Facility stale export
  blocking remains covered by AppTest because Streamlit's canvas-backed data
  editor is not safely mutable at cell level through the browser harness.
- Diverge report-export console follow-up passed three repeated report JSON
  downloads with no severe console entries; the earlier severe observation was
  not reproduced.
- `run_app.bat` and `run_app.ps1` returned HTTP `200` from the release
  worktree and terminated cleanly. A copied launcher in a path containing
  spaces produced the documented missing-`.venv` failure message.
- Final wheel route-open browser smoke passed for all eight visible modes with
  no horizontal overflow in recorded rows.

## Accessibility Review

Focused browser accessibility sampling passed for Two-Lane Segment, Weaving,
Merge, Diverge, Supported Workflows, and Facility at 768 px where applicable:
navigation and primary controls were keyboard reachable, no focus trap was
observed, state panels used text rather than color-only signaling, and page
horizontal overflow was not observed.

Facility limitation: the Streamlit data editor is canvas-backed. Browser
automation verified keyboard traversal into the grid and meaningful surrounding
table/section text, but cell-level semantics and mutation remain framework
provided. This is not a WCAG certification.

## Compatibility Statement

No numerical engine formulas, project schemas, fingerprints, result contracts,
export fields, presets, or support scope were intentionally changed. The code
changes only package runtime resources and make Multilane browser input edits
participate in the same freshness model as the other calculator worksheets.

## Release Recommendation

Proceed with PR #118 review/ready-for-review, CI, merge, and Issue #115 closure
after the pushed branch receives a passing GitHub Actions run.
