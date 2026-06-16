# Compact UI Refactor Plan

## 1. UI Objective and Design Principles

Refactor the existing Streamlit app toward the compact calculator-first UI direction shown in `mockups/ui_consistency_review/`. The app should read as an engineering calculator, not an example-template viewer. Users should choose a calculator mode, optionally load a project, enter or review inputs, run the calculation, inspect results and audit details, then save or export.

Design principles:

- Keep calculation workflows compact, structured, and auditable.
- Use consistent page rhythm across calculator pages.
- Make examples and presets secondary starting-value aids.
- Keep validation basis, limitations, calculation details, and audit records available but visually secondary.
- Preserve a single-page guided worksheet concept; do not introduce a multi-page wizard.
- Keep calculation modules independent from Streamlit and any UI framework.
- Prefer shared Streamlit helpers for repeated layout, headings, expanders, project controls, and export controls.
- Avoid decorative gradients, large hero sections, large warning blocks for normal scope limits, and dashboard-style visual noise.

## 2. Page-by-Page Target Layout

### Supported Workflows

Target layout:

- Page header:
  - Title: `Supported Workflows`
  - Caption: concise scope and workflow summary.
- Persistent mode selector remains available.
- Show compact workflow summaries for:
  - Two-Lane Highway
  - Two-Lane Facility
  - Multilane Highway
  - Basic Freeway
  - Examples / Validation
- Each workflow summary must show:
  - Supported
  - Current limitations
  - Save/Load and Export availability
- Do not present this page as marketing content.
- Keep limitation content clear, but avoid visually dominant warnings.

### Two-Lane Highway Manual Segment Calculator

Target layout:

- Page header:
  - Title: `Two-Lane Highway Manual Segment Calculator`
  - Caption: short current status and method scope.
- Top workflow area:
  - Compact `Load Project` control before detailed inputs.
  - Unit system selection near setup, not as a dominant global mode control.
- Left input column:
  - `Setup`
  - Existing road concept schematic for selected segment type.
  - `Roadway / Geometry`
  - `Traffic`
  - `Advanced / Optional`
  - `Run Calculation`
  - Collapsed `Validation basis and limitations`
- Right output column:
  - `Results`
  - Collapsed `Calculation details`
  - Collapsed `Audit / intermediate values`
  - `Project output` with compact `Save Project`
  - `Export / Report` with compact downloads

The selected segment type must continue to render the correct schematic via the existing schematic asset mapping.

### Two-Lane Facility Calculator

Target layout:

- Page header:
  - Title: `Two-Lane Facility Calculator`
  - Caption: multi-segment facility worksheet status.
- Top workflow area:
  - Compact `Load Project` before starting values and segment inputs.
  - Optional secondary `Starting values` section using current facility example-backed options.
- Left input column:
  - `Starting values` if needed, with caption:
    `Starting values only prefill supported inputs. You may edit values before running the calculation.`
  - `Setup`
  - `Roadway / Geometry` with segment table/editor
  - `Traffic`
  - `Advanced / Optional`
  - `Run Calculation`
  - Collapsed `Validation basis and limitations`
- Right output column:
  - Facility result summary
  - Segment result table
  - Collapsed `Calculation details`
  - Collapsed `Audit / intermediate values`
  - `Project output`
  - `Export / Report`

Starting values must not be framed as the main workflow.

### Multilane Highway Calculator

Target layout:

- Page header:
  - Title: `Multilane Highway Calculator`
  - Caption must make clear this is a Multilane Highway Segment workflow.
- Top workflow area:
  - Compact `Load Project`.
  - Secondary `Starting values`.
  - Use wording:
    - `Starting values`
    - `Eastbound starting values`
    - `Westbound starting values`
- Left input column:
  - `Setup`
  - `Roadway / Geometry`
  - `Traffic`
  - `Advanced / Optional`
  - `Run Calculation`
  - Collapsed `Validation basis and limitations`
- Right output column:
  - LOS, speed, density, demand flow, adjusted FFS, capacity
  - Collapsed details and audit
  - Save and export sections

Scope text must distinguish Multilane Highway Segment from Basic Freeway and from ramp, weaving, merge/diverge, and facility workflows.

### Basic Freeway Segment Calculator

Target layout:

- Page header:
  - Title: `Basic Freeway Segment Calculator`
  - Caption must make clear this is a Basic Freeway Segment workflow, not a freeway facility workflow.
- Top workflow area:
  - Compact `Load Project`.
  - Secondary `Starting values` using Chapter 26 Example 1.
- Left input column:
  - `Setup`
  - `Roadway / Geometry`
  - `Traffic`
  - `Advanced / Optional`
  - `Run Calculation`
  - Collapsed `Validation basis and limitations`
- Right output column:
  - LOS, speed, density, demand flow, capacity/check outputs
  - Collapsed details and audit
  - Save and export sections

Scope text must make clear that ramps, weaving, merge/diverge, managed lanes, work zones, reliability, and facility/corridor workflows are unsupported.

### Examples / Validation

Target layout:

- Page header:
  - Title: `Examples / Validation`
  - Caption: reference-backed validation and regression checks.
- Frame this page as validation/audit reference only.
- Use wording:
  - `Validation examples`
  - `Reference-backed checks`
  - `Example-backed regression cases`
- Keep the selected-case run behavior available.
- Results should emphasize comparison and audit outputs rather than calculator data entry.
- Keep export/report behavior available where currently supported.

## 3. Shared Component/Layout Grammar

Introduce reusable Streamlit UI helpers, likely in a new module such as `src/hcmcalc/ui/layout.py` or in a tightly scoped section of `streamlit_app.py` during the first phase.

Recommended helpers:

- `render_page_header(title: str, caption: str, status: str | None = None)`.
- `render_calculator_shell(...)` or a lighter helper that returns `input_column, result_column` with shared proportions.
- `render_project_load_section(...)`.
- `render_starting_values_section(...)`.
- `render_validation_basis_and_limitations(...)` using the existing exact label.
- `render_run_actions(...)`.
- `render_project_output_section(...)`.
- `render_export_report_section(...)` around the existing export/report implementation.
- `render_collapsed_calculation_details(...)`.
- `render_collapsed_audit(...)`.
- `render_result_summary_metrics(...)` for LOS/speed/density/demand/capacity summary cards.

Shared labels:

- `Validation basis and limitations`
- `Calculation details`
- `Audit / intermediate values`
- `Starting values`
- `Project file / Load`
- `Project output`
- `Export / Report`

Shared layout rules:

- Calculator pages use two primary columns after the page header.
- Left column contains project load and input workflow.
- Right column contains results, details, audit, save, and export.
- `Load Project` appears before detailed inputs.
- `Save Project` appears in `Project output` after inputs or near result context.
- Validation scope is collapsed by default.
- Normal unsupported scope information belongs in collapsed limitations, not top-level warnings.
- Top-level `st.error` remains appropriate for actual runtime or validation errors.

## 4. Mapping From Current UI Structure to Compact Mockup Structure

### Current Main Navigation

Current structure:

- `main()` renders a top header and horizontal radio mode selector.
- Labels are defined in `src/hcmcalc/ui/supported_workflows.py`.

Target mapping:

- Preserve the same mode choices and routing semantics.
- Prefer a sidebar mode selector to match the mockups if feasible in Streamlit without disrupting tests.
- If keeping a top selector in the first implementation phase, still apply the shared page grammar inside each page.
- Keep `APP_MODE_LABELS` and `APP_MODE_TO_VIEW` stable unless label changes are explicitly approved and tests are updated.

### Supported Workflows

Current structure:

- `render_supported_workflows_page()` loops through `SUPPORTED_WORKFLOW_SECTIONS`.
- Limitations are shown in per-section expanders.
- Examples / Validation are summarized separately.

Target mapping:

- Expand `SUPPORTED_WORKFLOW_SECTIONS` or add UI-only presentation rows so the page explicitly shows Two-Lane Highway, Two-Lane Facility, Multilane Highway, Basic Freeway, and Examples / Validation.
- Present each workflow with the same three fields: Supported, Current limitations, Save/Load and Export availability.
- Preserve documentation-oriented tests that validate current scope content.

### Two-Lane Manual Segment

Current structure:

- `render_manual_single_segment_calculator()` uses two columns.
- `_render_manual_project_load_controls()` currently places `Load Project` in a collapsed expander.
- `render_manual_project_file_controls()` places save under a collapsed `Project` expander.
- `render_manual_result()` includes metrics, details, audit, export/report, and JSON.
- `get_segment_schematic_path()` supplies the selected segment schematic.

Target mapping:

- Move load controls to a compact top section before the form inputs.
- Keep the schematic in the input column and preserve the existing selected segment mapping.
- Rename or visually frame save as `Project output`; keep existing project JSON generation.
- Keep result details and audit collapsed with the standardized labels.
- Keep export/report after visible results.

### Two-Lane Facility

Current structure:

- Facility behavior is adapter-backed by `manual_facility.py`.
- Starting values are based on Chapter 26 Example 3 and 4 facility definitions.
- Segment table/editor and result rows are already separate from engine code.

Target mapping:

- Reframe current template controls as secondary `Starting values`.
- Keep segment table/editor in `Roadway / Geometry`.
- Place facility result summary and segment result table in the right column.
- Move load/save to shared project sections.
- Preserve current guarded template validation and locked-field behavior.

### Multilane Highway

Current structure:

- `render_manual_multilane_calculator()` presents unit system, `Starting values` selectbox, load controls, inputs, validation expander, results, audit, save, and export.
- Adapter functions in `manual_multilane.py` use `TEMPLATE_LABELS`, `load_multilane_template()`, conversion helpers, and `run_manual_multilane()`.

Target mapping:

- Change the visual treatment of EB/WB choices from prominent template selection to secondary starting-value buttons or a compact selector.
- Use labels `Eastbound starting values` and `Westbound starting values` where possible.
- Keep `STARTING_VALUES_CAPTION`.
- Keep all adapter conversions, validation, and audit records unchanged.
- Consolidate load/save/export placement with other calculators.

### Basic Freeway Segment

Current structure:

- `render_manual_freeway_calculator()` uses Basic Freeway Example 1 preset inputs and adapter functions from `manual_freeway.py`.
- Preset wording exists in `PRESET_LABELS`.
- Limitations are available through `MANUAL_FREEWAY_LIMITATIONS`.

Target mapping:

- Reframe Chapter 26 Example 1 as secondary starting values.
- Keep Basic Freeway Segment scope text in collapsed limitations and concise page caption.
- Keep ramp density label/help behavior unchanged, because it clarifies FFS adjustment rather than ramp analysis.
- Consolidate load/save/export placement with other calculators.

### Examples / Validation

Current structure:

- `render_validated_case_viewer()` uses sidebar controls for fixture and selected case.
- It can run selected implemented cases and render results with `render_result()`.

Target mapping:

- Reframe page copy around validation examples, reference-backed checks, and example-backed regression cases.
- Avoid making this page look like the primary product workflow.
- Keep run-selected-case behavior and result rendering.
- Keep validation basis and limitations collapsed.

## 5. Files Likely to Be Changed

Likely UI implementation files:

- `src/hcmcalc/ui/streamlit_app.py`
- `src/hcmcalc/ui/supported_workflows.py`
- `src/hcmcalc/ui/result_view.py`
- `src/hcmcalc/ui/project_io.py` only if helper signatures require presentation adjustments; avoid semantic changes.
- New optional helper module: `src/hcmcalc/ui/layout.py`

Likely test files:

- `tests/unit/test_streamlit_app.py`
- Potentially new focused tests for shared constants/helper output if helper functions are pure enough to test without Streamlit.

Files that should not be changed for this UI-only refactor unless separately approved:

- `src/hcmcalc/methods/**`
- `src/hcmcalc/freeway/**`
- `src/hcmcalc/multilane/**`
- `src/hcmcalc/core/**`
- `references/**`
- `tests/unit/test_*example*`
- `tests/integration/test_validation_fixtures.py`
- `assets/schematics/two_lane/**`

## 6. Non-Goals and Strict Guardrails

Non-goals:

- Do not implement new HCM methodology.
- Do not broaden supported facility types.
- Do not create a multi-page wizard.
- Do not redesign exports or project schemas.
- Do not make Examples / Validation the main calculator workflow.
- Do not replace existing validation fixtures or tolerances.
- Do not add new dependencies solely for UI layout.

Strict guardrails:

- Do not change calculation engines, formulas, fixtures, expected outputs, tolerances, or validation logic.
- Do not change project JSON semantics unless explicitly required and documented.
- Do not remove save/load/export/report behavior.
- Do not delete, move, or break existing two-lane schematic assets.
- The Two-Lane Highway Manual Segment page must continue to render the correct road concept schematic for the selected segment type.
- Keep validation/audit content available, but visually secondary and collapsible where appropriate.
- Prefer reusable Streamlit UI helper functions.
- Avoid brittle source-code inspection tests.

## 7. Preservation Requirements

Functional preservation:

- Existing calculator results must remain unchanged for all current validated examples and manual workflows.
- Existing project load/save behavior must continue to accept and produce the same project JSON semantics.
- Existing export/report formats must remain available where currently supported.
- Existing unit conversion boundaries must remain unchanged.
- Existing unsupported-scope guardrails must remain enforced by adapters and engines.
- Existing validation example execution must remain available.

UI preservation:

- The app remains a single Streamlit app.
- The guided worksheet remains single-page per mode.
- Two-Lane segment schematics remain visible and correct for:
  - `passing_constrained`
  - `passing_zone`
  - `passing_lane`
- Error states continue to use visible error rendering.
- Collapsed expanders remain usable for limitations, details, and audit.

Test preservation:

- Existing unit and integration tests should continue to pass.
- Tests should validate behavior and stable labels, not fragile exact Streamlit DOM structure.

## 8. Implementation Phases

### Phase 0: Baseline and Screenshot Capture

- Run the current test suite.
- Capture screenshots of the current six modes for comparison.
- Confirm the mockup gallery at `mockups/ui_consistency_review/index.html` remains the visual reference.

### Phase 1: Shared UI Grammar Helpers

- Add shared helper functions for page headers, two-column shells, validation expanders, project load/save sections, starting values, and export/report sections.
- Keep helper APIs presentation-focused and independent from calculation adapters.
- Update existing label constants only if preserving current test expectations or explicitly updating tests.

### Phase 2: Two-Lane Manual Segment Baseline

- Refactor `render_manual_single_segment_calculator()` to the compact grammar first.
- Preserve schematic rendering through `get_segment_schematic_path()`.
- Preserve current manual input keys where feasible to avoid breaking session restore behavior.
- Keep result rendering behavior and export downloads intact.

### Phase 3: Two-Lane Facility Alignment

- Refactor facility layout to match the manual segment grammar.
- Reframe templates as secondary starting values.
- Keep guarded facility template behavior and locked-field validation unchanged.
- Preserve project IO and export/report behavior.

### Phase 4: Multilane and Basic Freeway Alignment

- Refactor Multilane and Basic Freeway calculators to use the shared compact shell.
- Reframe EB/WB and Chapter 26 Example 1 as starting values.
- Keep adapter conversion functions, audit records, and run functions unchanged.
- Preserve existing limitations content, but place it in the standard collapsed expander.

### Phase 5: Supported Workflows and Examples / Validation

- Update Supported Workflows to match the summary-page mockup structure.
- Reframe Examples / Validation as reference-backed checks, not calculator entry.
- Preserve selected-case execution and result rendering.

### Phase 6: Verification, Cleanup, and Documentation Notes

- Run full test suite.
- Manually inspect all six modes.
- Compare against mockups for hierarchy, placement, and wording.
- Add concise developer notes only if needed to explain reusable helper patterns.

## 9. Test Plan

Automated tests:

- Run `pytest`.
- Keep existing validation fixture tests unchanged.
- Keep existing example-output tests unchanged.
- Keep existing project IO tests unchanged.
- Keep schematic asset tests:
  - supported segment types map to existing schematic files;
  - unknown segment type has no schematic.
- Keep shared grammar label tests:
  - `Validation basis and limitations`
  - `Calculation details`
  - `Audit / intermediate values`
  - `Starting values` caption.
- Add pure helper tests only where helpers return simple data structures or stable label content.

Avoid:

- Do not add tests that inspect large source strings.
- Do not add tests coupled to Streamlit-generated DOM internals.
- Do not add screenshot tests unless a stable local browser test harness is explicitly approved.

Manual verification:

- Launch the Streamlit app locally.
- Visit all six modes.
- Confirm `Load Project` appears near the top of calculator workflows.
- Confirm starting values are secondary and use approved wording.
- Confirm `Validation basis and limitations` is collapsed by default and in a consistent location.
- Confirm results, details, audit, save, and export are visible after calculation.
- Confirm two-lane schematics change correctly with selected segment type.
- Confirm existing save/load/export/report actions still work for each supported workflow.

Regression checks:

- Run representative calculations before and after refactor and compare outputs for:
  - Two-Lane Manual Segment
  - Two-Lane Facility
  - Multilane Highway EB and WB
  - Basic Freeway Segment
  - Examples / Validation selected cases
- Confirm project JSON generated before the refactor can still be loaded after the refactor.
- Confirm project JSON generated after the refactor can be loaded by the same code path.

## 10. Acceptance Criteria

UI acceptance:

- All calculator pages follow the shared compact section order:
  - Page header
  - Project file / Load
  - Inputs
  - Run Calculation
  - Validation basis and limitations
  - Results
  - Calculation details
  - Audit / intermediate values
  - Project output
  - Export / Report
- `Load Project` is not hidden inside Advanced.
- Save Project remains available and visually secondary.
- Starting values are not presented as the primary workflow.
- The required starting-values caption appears wherever starting values exist.
- The limitations expander is named exactly `Validation basis and limitations`.
- Normal scope limitations are collapsed by default and not shown as large warnings.
- Examples / Validation is framed as a reference and audit workflow.

Behavioral acceptance:

- Full test suite passes.
- Validated expected outputs, tolerances, and fixture comparisons are unchanged.
- Project load/save semantics are unchanged.
- Export/report behavior remains available and produces the same supported formats.
- No calculation engine, formula, fixture, validation, or tolerance files are changed.
- Existing two-lane schematic assets remain in place and render correctly by segment type.

Review acceptance before coding:

- Product owner accepts the page-by-page target layout.
- Engineering accepts the helper/module split.
- Engineering accepts that the first implementation pass is UI-only and must not broaden methodology support.
- Any desired navigation label changes are explicitly approved before code changes begin.
