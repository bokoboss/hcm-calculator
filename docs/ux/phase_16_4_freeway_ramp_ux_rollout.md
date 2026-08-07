# Phase 16.4 Freeway and Ramp UX Rollout

Status: local qualification complete; **CONDITIONAL PASS pending PR/CI/merge**.

This phase rolls the validated Multilane task-oriented worksheet pattern into Basic Freeway, Merge, and Diverge. It is a presentation and workflow-clarity change. No HCM equations, lookup values, interpolation, method identifiers, normalized schemas, project contracts, result fields, or null semantics were changed.

## Baseline and isolation

- Worktree: `C:\Users\kittipat_t\Documents\hcm-calculator-phase-16-4`
- Branch: `codex/phase-16-4-freeway-ramp-ux-rollout`
- Baseline: `origin/main` at `54610233ee1ad5fadb34485b60b9fd9ce10b6e0c`
- Original checkout: `C:\Users\kittipat_t\Documents\hcm-calculator` was not modified.
- Evidence: `output/playwright/phase16_4_freeway_ramp_ux_rollout/` is temporary and uncommitted.

Weaving, Two-Lane Segment, and Two-Lane Facility are outside this phase. Their source files were not changed.

## Design decision

The chosen approach is progressive disclosure inside the existing single-page Streamlit worksheet. A copy-only pass would leave branch overload and stale/export hierarchy unresolved; a wizard would conflict with the repository direction. The rollout reuses only the proven presentation pattern and re-derives method copy from each workflow’s own contract.

## Implemented changes

### Basic Freeway Segment

- Added a clear Start section with method scope, units, starting values, and subordinate project load.
- Grouped roadway and demand fields as Traffic and segment basics.
- Kept Free-flow speed method as an active measured/estimated branch; inactive FFS variables remain hidden and neutralized before adapter submission.
- Reframed heavy-vehicle adjustment as three method choices that map to the existing engine paths:
  - General terrain lookup: level/rolling terrain.
  - Specific grade lookup: grade and supported SUT/TT composition.
  - External PCE: approved value and provenance.
- Kept advanced driver-population and calibration fields collapsed.
- Uses Calculate/Recalculate, result-first demand/capacity ordering, visible capacity-failure semantics, and a Result actions section before calculation details, audit, and full JSON.
- Existing project restore now reopens the measured/external presentation branches from the saved `ffs_source`, `pce_mode`, and `terrain_type` values.

### Merge and Diverge

- Added the same Start/unit/preset/project-load orientation while retaining Merge/Diverge-specific terminology.
- Reframed geometry and demand sections; derived downstream/continuing demand is explicitly calculated and not editable.
- Kept the existing method-specific FFS, traffic-composition, terrain, evidence, and diagram fields.
- Added active localized widget-state normalization for unit, FFS-source, and terrain controls.
- Replaced the old technical run label with Calculate/Recalculate while retaining the existing button keys and engine contract.
- Moved project state and report exports before calculation details/audit/full JSON.
- Put governing v/c immediately after the speed metrics without inventing any new method output.

## Compatibility evidence

The implementation diff contains only presentation/localization/test changes:

- `src/hcmcalc/ui/i18n.py`
- `src/hcmcalc/ui/streamlit_app.py`
- `tests/unit/test_streamlit_app.py`

The adapters, engines, project I/O, workflow-state fingerprinting, method identifiers, input contracts, result fields, and export builders are unchanged. The Basic Freeway branch test compares both submitted normalized inputs and the complete result dictionary against direct adapter/engine execution for general terrain, specific grade, and external PCE.

## Validation results

| Gate | Result |
|---|---:|
| Target Streamlit AppTest | 80 passed |
| Pure adapter/project/localization regression | 104 passed |
| Full repository suite | 1,055 passed in 188.59s |
| Catalog parity | `validate_catalogs() == []` |
| Compile check | `python -m compileall -q src tests` passed |
| Real-browser matrix | 43/43 passed |

Browser qualification used Python Playwright with system Chrome because Node/npm/npx were unavailable. The matrix covers 17 Basic Freeway, 13 Merge, and 13 Diverge rows across English/Thai, Metric/Imperial, 1280/768 CSS-pixel widths, blank/preset, measured/estimated FFS, valid results, stale/Recalculate, capacity failure where applicable, project load, and report export.

- 23 Metric rows; 20 Imperial rows.
- 29 rows at 1280 CSS-pixel width; 14 rows at 768 CSS-pixel width.
- 0 console-error rows.
- 0 horizontal-overflow rows.
- Screenshots, row records, downloads, and the summary are under `output/playwright/phase16_4_freeway_ramp_ux_rollout/` and are not committed.

## Accessibility and responsive findings

The qualified surface exposes visible labels and named controls, keeps the primary action reachable, renders status text in addition to color, and reports no page-level horizontal overflow at the target widths. Thai labels remained readable in the browser matrix. This is representative operator qualification, not formal WCAG, axe, screen-reader, or cross-browser certification.

Known follow-up boundaries:

- The 768 target is a narrow desktop/tablet width (`768 x 900` CSS pixels), not a small-phone qualification.
- Formal assistive-technology and cross-browser review remain follow-up work.
- The Export report control is intentionally subordinate/collapsed until requested; current-result-only download guards remain enforced.

## Rollout classification and recommendation

Classification: **CONDITIONAL PASS** for the isolated Phase 16.4 branch, pending PR review, CI, and merge checks. No Blocker or Major finding remains. The branch is ready for the requested PR/CI workflow.

Phase 16.5 should handle Weaving and the Two-Lane workflows separately because their geometry, handoff, curve, passing-lane, and facility semantics differ materially from this rollout.
