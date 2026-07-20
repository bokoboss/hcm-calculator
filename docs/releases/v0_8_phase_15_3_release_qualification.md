# v0.8 Phase 15.3 Release Qualification

Status: incomplete release qualification.

## Executive Result

Phase 15.3 found and fixed two installed-wheel release blockers:

- Two-Lane schematic assets were not packaged in the wheel.
- Runtime UI presets for Facility, Multilane, Basic Freeway, Weaving, Merge,
  Diverge, and the internal validation view depended on repository-relative
  `references/*.yaml` files.

The fixed source tree passes the full local repository suite, installed package
provenance checks, installed Streamlit HTTP startup, and installed route-open
smoke coverage. The release is not qualified for merge/Issue #115 closure
because the required exhaustive real-browser matrix, CI, PR review, and merge
gates are not complete.

## Baseline

- Required baseline SHA: `f16485329b451cf69cc61f9b59adb07ae3ed80d9`
- Effective baseline SHA: `f16485329b451cf69cc61f9b59adb07ae3ed80d9`
- Qualification branch: `codex/phase-15-3-release-qualification`
- Worktree: `C:\Users\kittipat_t\Documents\hcm-calculator-phase-15-3`
- Original dirty checkout: left untouched.

## Environment

- OS: Microsoft Windows 11 Pro 10.0.26200, 64-bit
- Python: 3.12.10
- Initial pip: 25.0.1
- Qualification venv pip after upgrade: 26.1.2
- Streamlit: 1.59.2
- Browser automation: blocked; Node/npm/npx not installed.

## Wheel Evidence

Candidate wheel after asset/resource fixes:

- Wheel filename: `hcm_calculator-0.7.0-py3-none-any.whl`
- Build location:
  `C:\Users\kittipat_t\AppData\Local\Temp\hcmcalc-phase15-3-build-current`
- SHA-256:
  `8d10866486ead2033c3092249cf4011f539ddd3fd7991865b8337ce54aa4d06d`

Package-content inspection confirmed inclusion of:

- Python package modules.
- Streamlit UI modules.
- English/Thai i18n data in package modules.
- Packaged runtime YAML presets under `hcmcalc/ui/data/`.
- Weaving PNG diagrams.
- Merge/Diverge SVG diagrams.
- Two-Lane PNG schematics.
- Package metadata.

Package-content inspection confirmed exclusion of:

- `tests/`
- `mockups/`
- `output/`
- root `assets/schematics`

## Installed Package Provenance

Installed environment:
`C:\Users\kittipat_t\AppData\Local\Temp\hcmcalc-phase15-3-wheel-current`

Provenance from working directory `C:\Users\kittipat_t`:

- `hcmcalc.__file__`:
  `C:\Users\kittipat_t\AppData\Local\Temp\hcmcalc-phase15-3-wheel-current\Lib\site-packages\hcmcalc\__init__.py`
- Streamlit app module:
  `C:\Users\kittipat_t\AppData\Local\Temp\hcmcalc-phase15-3-wheel-current\Lib\site-packages\hcmcalc\ui\streamlit_app.py`
- Two-Lane schematic:
  `...\site-packages\hcmcalc\ui\assets\two_lane\passing_constrained.png`
- Weaving diagram:
  `...\site-packages\hcmcalc\ui\assets\weaving\one_sided_weave.png`
- Merge diagram:
  `...\site-packages\hcmcalc\ui\assets\ramp_influence\merge_right_on_ramp.svg`

## Automated Results

- Focused package/asset/route tests after fixes: `16 passed`
- Streamlit AppTest suite: `68 passed`
- Full repository suite: `1016 passed`
- Compile check: `python -m compileall -q src tests` passed.
- Installed AppTest route-open smoke: 8 of 8 visible routes opened from the
  installed `site-packages` app path.

## Installed Streamlit Launch

Command:

```powershell
python -m streamlit run <site-packages>\hcmcalc\ui\streamlit_app.py --server.headless=true --server.port=8523 --server.address=127.0.0.1
```

Run from `C:\Users\kittipat_t`.

Result:

- HTTP: `200`
- Startup log: Uvicorn server started on `127.0.0.1:8523`
- No startup traceback observed.
- Temporary server stopped after the check.

## Browser Matrix

The matrix file is
`docs/ui/phase_15_3_browser_qualification_matrix.md`.

Result: incomplete. AppTest and installed route-open smoke evidence exists, but
desktop/768 px real-browser review, overflow review, console review, and
screenshot/evidence logs are not complete because Node/npm/npx is unavailable
for the required Playwright CLI workflow.

## Project Qualification

Automated project I/O and AppTest coverage passed for current-result restore,
wrong-type rejection, malformed project handling, stale-result protection, and
locale restoration across the implemented visible calculators. Full release
project compatibility remains incomplete until direct installed-browser project
load/save checks are completed.

## Export Qualification

Automated export/report tests and AppTests passed for CSV, Excel, Markdown, and
report JSON exposure on current results, plus stale-result export blocking.
Full release export qualification remains incomplete until representative
generated artifact content is inspected from the installed browser workflow.

## Launcher Qualification

`setup_app.bat`, `setup_app.ps1`, `run_app.bat`, and `run_app.ps1` were
reviewed. They preserve the documented source-checkout local workflow and do
not create an executable installer. Automated launcher execution was not
completed in this pass.

## Accessibility Review

Automated and code-level review confirmed typed textual result states,
diagram captions/alternatives in the implemented UI paths, specific button
labels, and table headings in AppTest-covered surfaces. Full release-level
keyboard, focus, narrow viewport, and color-only review remains incomplete
until real-browser testing is available.

## Defects Found And Fixed

- Blocker fixed: Two-Lane schematic assets were source-tree-only and absent
  from the wheel.
- Blocker fixed: UI preset YAML files were source-tree-only and caused raw
  tracebacks when installed Weaving/Merge/Diverge routes opened outside the
  repository.

Regression tests added:

- `tests/unit/test_package_assets.py`

## Unresolved Findings

- Real-browser matrix blocked by missing Node/npm/npx.
- CI not run/monitored in this local pass.
- PR not opened in this pass.
- Merge and Issue #115 closure are blocked.

## Compatibility Statement

No numerical engine formulas, project schemas, fingerprints, result contracts,
export fields, presets, or support scope were intentionally changed. The code
changes only move runtime assets and preset data into packaged resources and
resolve them from the installed package.

## Release Recommendation

Do not merge or close Issue #115 yet. Continue Phase 15.3 after browser
automation is available, complete the exhaustive real-browser matrix, rerun the
clean wheel-installed gate, open the PR with `Refs #115`, and only use
`Closes #115` after all gates pass.
