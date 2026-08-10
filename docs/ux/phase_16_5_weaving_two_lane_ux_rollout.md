# Phase 16.5: Weaving And Two-Lane UX Rollout

Status: **Local qualification PASS; release classification CONDITIONAL PASS pending final repository tests, review, PR, and CI gates**

Baseline: `origin/main` at `f22dbc527c0b2304058d13b5fe6275f2b23f3786`
Package baseline: `0.8.0`
Parent issue: `#119`
Worktree: `C:\Users\kittipat_t\Documents\hcm-calculator-phase-16-5`
Branch: `codex/phase-16-5-weaving-two-lane-ux-rollout`

## Purpose and boundary

Phase 16.5 rolls the validated single-page, task-oriented worksheet pattern into:

- Weaving Segment.
- Two-Lane Segment.
- Two-Lane Facility.

The rollout preserves method-specific engineering semantics, the existing facility editor, and the one-page worksheet concept. It does not introduce a wizard, new calculation methodology, formula or lookup changes, public engine schema changes, project-schema changes, fingerprint-contract changes, method identifiers, result fields, or export fields.

## Implemented UX changes

### Weaving Segment

- Start now leads with units and validated starting values; project load remains available as a secondary action.
- One-sided and two-sided geometry remain separate, with the diagram and lane-change controls following the active configuration.
- Traffic, FFS source, and advanced geometry evidence are grouped in task order.
- Advanced geometry evidence is collapsed until needed while retaining the same audit inputs and active-branch null semantics.
- The primary action is `Calculate` before a result and `Recalculate` after a result.
- Capacity failure is presented separately from HCM stopping/handoff. Capacity failure reports LOS F while speed and density remain not predicted. When `LS >= LMAX`, the result is an explicit Chapter 13 handoff state without a normal LOS result.
- Stale results take precedence over old handoff/capacity taxonomy: metrics and report exports are withheld until recalculation.

### Two-Lane Segment

- The worksheet follows Start, segment basics, directional traffic, geometry, and method-specific adjustment branches.
- Grade, curve, and passing-lane controls retain their existing conditional behavior and engine mapping.
- Method-specific branches remain visible when active and are summarized when inactive.
- The primary action changes from `Calculate` to `Recalculate` after a current result.
- Result summary and project/report actions precede subordinate calculation details.

### Two-Lane Facility

- Template and units lead the page; the project loader remains secondary.
- The editable table remains the central task surface.
- Columns are ordered into identity/type, directional traffic, and geometry groups.
- Passing Zone-only opposing volume applicability is stated before validation, including inactive-row canonicalization behavior.
- Add/remove guidance and row validation are visible near the editor; row order remains the engineered facility sequence and reordering is not implied.
- Current result order is facility summary, segment results, project/report actions, then details/audit/JSON.
- `canonicalize_manual_facility_rows()` remains the seam for inactive opposing values, including the Issue #121 NaN regression path.

## Contract and numerical safeguards

- Weaving UI adapter outputs match the public `WeavingSegmentMethod` for current and handoff cases.
- Two-Lane Segment UI adapter outputs match the public `TwoLaneHighwayChapter15Method`.
- Metric and Imperial Weaving display paths normalize to equivalent engine inputs.
- Facility inactive opposing values preserve normalized inputs and calculation fingerprints, produce JSON without `NaN`, and restore as canonical rows after project load.
- The only shared state change is stale-result precedence: stale freshness is evaluated before capacity and HCM handoff presentation states.

## Validation evidence

### Automated tests

Already run during the implementation and qualification cycle:

- Baseline non-AppTest target suites: `174 passed in 3.52s`.
- Streamlit AppTest suite: `80 passed in 211.08s` after the rollout edits.
- Focused new UX AppTests: `6 passed`.
- Focused manual facility/workflow/project/reporting suites: `121 passed`.
- Phase 16.5 contract tests: `5 passed`.
- `python -m compileall -q src tests`: passed.
- Localization catalog validation: `[]`.

Final full repository suite: `1066 passed in 209.47s`.

### Real-browser qualification

The mandated Python Playwright route used system Chrome at `C:\Program Files\Google\Chrome\Application\chrome.exe` against the isolated Streamlit server.

- Complete matrix: `58/58 passed`.
- Workflow rows: Weaving `19/19`, Two-Lane Segment `17/17`, Two-Lane Facility `19/19`.
- Cross-workflow Start/project-load consistency smokes: `3/3`.
- Viewports: 1280px and 768px.
- Locales: English and Thai.
- Coverage includes one/two-sided Weaving, capacity failure, HCM handoff, grade/curve/passing branches, Facility row validation, Add row, stale/Recalculate, project load, save/export, and current-result hierarchy.
- Recorded console/page errors: none.
- Recorded horizontal overflow: none.

Temporary evidence is in:

`C:\Users\kittipat_t\Documents\hcm-calculator-phase-16-5\output\playwright\phase16_5_weaving_two_lane_ux_rollout`

The authoritative final artifacts are `matrix.json`, `matrix.csv`, the 58 row screenshots, and project fixtures. These temporary outputs remain uncommitted.

## Defects found and disposition

### EXP-001 — stale Weaving result precedence

An old handoff or capacity result could be classified as current after input edits. The resolver now gives stale freshness precedence, with a regression assertion in `tests/unit/test_workflow_state.py`. Focused tests and browser stale scenarios pass.

### EXP-002 — Weaving Metric segmented-control transient state

System Chrome could send a transient `None` when clicking the already-selected Metric option. The localized unit state is now canonicalized before rendering. The real-browser Weaving matrix is green after the fix.

### EXP-003 — Facility browser editor harness interaction

The Glide canvas overlapped the Add row pointer hit target, and a newly added blank row did not reliably submit through the browser path used by the harness. This was isolated as a harness interaction issue, not a product calculation defect. The harness now uses keyboard activation for Add row, uses a submitted existing-row type change for blocking validation/stale coverage, and adapts the type-cell target to the clipped 768px editor. Facility and full-matrix evidence are green.

## Accessibility and responsive review

- Native labelled controls, visible section captions, and localized task labels remain in use.
- The editor, current-result actions, and stale/recalculation state remain reachable at 768px.
- No horizontal overflow was observed in the matrix.
- The qualification is representative system-Chrome evidence, not formal WCAG conformance, axe certification, screen-reader certification, or cross-browser certification.
- Follow-up should include keyboard-only and assistive-technology review across all workflows, plus a broader browser matrix.

## Intentional cross-workflow differences

The shared grammar is Start, active inputs, Calculate/Recalculate, current-result summary, project/report actions, and subordinate details. The content remains method-specific:

- Weaving keeps geometry diagrams and distinguishes capacity from Chapter 13 handoff.
- Two-Lane Segment keeps grade, curve, and passing-lane branches.
- Two-Lane Facility keeps the table editor, row sequence, applicability rules, and segment-result table.

These differences are deliberate and preserve engineering meaning rather than forcing a generic form architecture.

## Phase classification and next phase

Local qualification is a **PASS** for implementation, browser evidence, and the full repository suite. The release decision remains **CONDITIONAL PASS** until final diff review, Issue #119 status update, PR checks, and merge gates complete.

Phase 16.6 should focus on app-wide release qualification: shared navigation and localization consistency, current/stale/result/export behavior across all implemented workflows, formal accessibility follow-up, cross-browser coverage, and release notes. No Phase 16.6 implementation is included here.
