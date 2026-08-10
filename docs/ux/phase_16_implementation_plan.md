# Phase 16 Implementation Plan

Baseline: `72d9de8841db8e158077372bf60df93a9f5bcdab`
Phase 16.1 status: completed and merged in PR #120
Phase 16.2 status: implementation and local qualification complete; PR/CI/merge pending
Phase 16.3 status: Conditional Pass for the Multilane pilot; targeted copy and contrast remediation complete; PR/CI/rollout tracking pending
Phase 16.4 status: Conditional Pass after local qualification; PR/CI/merge pending
Phase 16.5 status: local implementation, full tests, and qualification complete; final review, PR/CI, and merge gates pending

## Simpler-Alternative Review

### Option 1: Copy And Guidance Only

Scope:

- Improve labels, help text, warnings, and validation messages.
- Keep layout and field ordering mostly unchanged.
- Add clearer Truck Mix and PCE copy.

Pros:

- Lowest implementation cost.
- Low Streamlit state risk.
- Minimal test impact.
- Preserves project compatibility.

Cons:

- Does not materially reduce the number of visible decisions.
- Does not fix project/load/result hierarchy.
- Leaves PCE Mode as a technical control rather than a task choice.
- Stale-state recovery remains visually similar.

Verdict: useful but insufficient for Phase 16.2. Use selected copy improvements inside the pilot, not as the whole strategy.

### Option 2: Progressive Disclosure Within Current Streamlit Architecture

Scope:

- Reorder Multilane into task-oriented sections.
- Use conditional display for FFS and heavy-vehicle adjustment branches.
- Replace separate PCE Mode and terrain controls with a clearer three-way heavy-vehicle adjustment method.
- Keep one page and existing project/export contracts.

Pros:

- Directly reduces cognitive load and irrelevant fields.
- Preserves the single-page guided worksheet requirement.
- Keeps calculation modules independent from Streamlit.
- Limits state changes to one workflow in Phase 16.2.
- Compatible with existing project schema if normalized input mapping remains unchanged.
- Browser tests can focus on visible branch matrix and stale/export behavior.

Cons:

- Requires careful session-state migration for renamed/reordered controls.
- Needs focused tests for every conditional branch.
- May require localized copy updates in a later implementation phase.

Verdict: recommended strategy.

### Option 3: Guided Step-Based Workflow

Scope:

- Use tabs, staged sections, or a wizard-like flow.
- Require users to complete Start, Inputs, Method Branch, Calculate, Results, and Export stages.

Pros:

- Strong orientation for Profile C.
- Can reduce visible controls per step.
- Makes readiness checks explicit.

Cons:

- Conflicts with the repository direction to avoid a multi-page wizard.
- Higher Streamlit state complexity.
- Greater stale-state and back-navigation risk.
- More browser accessibility and regression surface.
- Slower for HCM specialists who want direct entry.

Verdict: do not use for Phase 16.2. Borrow only the idea of ordered task sections inside one page.

## Recommended Strategy

Use **Option 2: Progressive disclosure within the current Streamlit architecture**.

Rationale:

- The problem is real and affects task completion effort, not just wording.
- Copy-only changes do not solve visible-field overload or branch hierarchy.
- A wizard is heavier than needed and conflicts with the single-page worksheet concept.
- Multilane has enough branch complexity to prove the pattern before app-wide rollout.
- Calculation contracts can remain unchanged.

## Phase 16.2: Multilane UX Pilot Implementation

Goal: implement the Multilane task-oriented pilot without numerical-method changes.

Scope:

- Reorder Multilane into Start, Traffic and segment basics, Free-flow speed, Heavy-vehicle adjustment, Calculate, Result summary, Details, Project/export.
- Replace PCE Mode + terrain presentation with a three-way heavy-vehicle adjustment method:
  - General terrain lookup.
  - Specific grade lookup.
  - External PCE.
- Rename Truck Mix to Heavy-vehicle composition (SUT/TT).
- Add inline English and Thai copy for Heavy Vehicle %, SUT, TT, PCE, FFS, and HCM table-domain limits.
- Hide inactive branch fields.
- Improve stale result hierarchy.
- Keep project schema and calculation engine inputs compatible.
- Keep details/audit/export records intact.

Validation:

- Unit tests for branch field-to-engine mapping.
- Streamlit AppTest coverage for measured/estimated FFS and each heavy-vehicle adjustment method.
- Regression tests for current/stale export visibility.
- Browser evidence at desktop and 768 px in English and Thai.
- Full `python -m compileall -q src tests` and `python -m pytest -q`.

Exit criteria:

- Multilane default calculation still matches existing expected outputs.
- External PCE bypasses internal lookup exactly as before.
- Unsupported Truck Mix behavior remains external-PCE only.
- Project load/save remains compatible.
- No other workflow behavior changes.

Phase 16.2 local qualification result:

- Full suite: 1048 tests passed.
- System Chrome browser matrix: 25/25 rows passed, including English/Thai at 1280 px, compact 768 px, capacity failure/correction, project restore, report export, and no horizontal overflow.
- One cross-locale segmented-control state defect was found in real-browser testing, fixed with canonical pre-widget normalization, and covered by AppTest.
- No engine, schema, fingerprint, result-contract, preset, or export-field changes were required.

## Phase 16.3: Pilot Usability And Regression Qualification

Goal: complete human-centered qualification of the now-implemented Multilane pilot before any cross-workflow rollout.

Scope:

- Browser matrix for Profile A/B/C tasks.
- Manual review of English and Thai copy fit at 768 px.
- Verify stale input, capacity failure, project load, malformed project rejection, current result export, and audit detail access.
- Review screenshots against Phase 16.1 acceptance criteria.
- Run moderated or representative traffic-engineer review of Heavy Vehicle % versus SUT/TT terminology.
- Perform a focused accessibility audit of the progressive-disclosure and result-action hierarchy.
- Decide which patterns generalize to Basic Freeway, Merge, and Diverge without copying unsupported methodology assumptions.

Exit criteria:

- No critical or high UX regression remains in Multilane.
- Existing test suite passes.
- Documentation and release notes identify no numerical-method change.
- A separate rollout proposal identifies the patterns that generalize and the patterns that remain Multilane-specific.

Phase 16.3 qualification result:

- Decision: **CONDITIONAL PASS** for controlled Multilane pilot rollout. No unresolved Blocker or Major finding remains.
- Final system-Chrome qualification: 27/27 Metric rows and 27/27 Imperial rows passed across English/Thai, 1280/768 px, branch, stale, capacity, project/report, and keyboard scenarios; no console/page errors or horizontal overflow.
- Targeted remediation: visible bilingual SUT/TT scope clarification and Multilane-only primary-button contrast treatment. No HCM engine, schema, fingerprint, result, export, or other workflow changes.
- Remaining Minor limitations: narrow post-action scroll position can leave result metrics above the current viewport; long Median type values can ellipsize in the narrow two-column grid. Record both for Phase 16.4.
- Formal screen-reader/assistive-technology, automated axe/WCAG, cross-browser, and moderated participant work remains follow-up; this phase is a representative operator qualification, not a conformance claim.
- Detailed evidence: `docs/ux/phase_16_3_multilane_usability_accessibility_qualification.md`.

## Phase 16.4: Basic Freeway, Merge, And Diverge Rollout

Goal: apply proven task-section and stale/export hierarchy patterns to workflows closest to Multilane.

Phase 16.4 boundary from Phase 16.3:

- Start with a Basic Freeway presentation pilot; qualify Merge and Diverge as separate follow-on workflow slices rather than broad app-wide restyling.
- Reuse only presentation patterns proven here: ordered single-page sections, active-branch disclosure, stale/Recalculate hierarchy, current-result-only exports, project/report separation, native labelled controls, bilingual scope copy, and scoped contrast treatment.
- Re-derive every method label, support boundary, lookup explanation, and failure message from that workflow’s own HCM contract and Chapter 26 evidence.
- Do not copy Multilane SUT/TT choices, External PCE rules, lookup-domain assumptions, equations, or engine contracts.
- Require each workflow to pass its own compatibility gate, method-level tests, EN/TH system-Chrome matrix at 1280/768 px, keyboard review, and formal accessibility follow-up before rollout.

Scope:

- Basic Freeway:
  - Align FFS and heavy-vehicle adjustment structure with Multilane where method-compatible.
  - Keep driver-population controls collapsed under a clear advanced section.
- Merge and Diverge:
  - Move geometry evidence and support scope closer to geometry controls.
  - Improve capacity warning/failure result hierarchy.
  - Preserve isolated right-side one-lane HCM 7.0 contract.

Exit criteria:

- No schema or engine changes unless separately scrutinized and validated.
- Browser evidence confirms desktop/narrow and English/Thai usability.

Phase 16.4 local qualification result:

- Decision: **CONDITIONAL PASS** for the isolated Basic Freeway, Merge, and Diverge rollout. No Blocker or Major finding remains; PR review, CI, and merge are pending.
- Working baseline: `origin/main` at `54610233ee1ad5fadb34485b60b9fd9ce10b6e0c`; branch `codex/phase-16-4-freeway-ramp-ux-rollout`.
- Target AppTest: 80 passed. Pure adapter/project/localization regression: 104 passed. Full repository suite: 1,055 passed. `compileall` and localization catalog parity passed.
- Browser qualification: 43/43 system-Chrome rows passed across 17 Basic Freeway, 13 Merge, and 13 Diverge rows; English/Thai; Metric/Imperial; 1280/768 CSS-pixel widths; branch, result, stale, capacity, project, and export scenarios. No console-error or horizontal-overflow rows.
- Compatibility: no engine, adapter, normalized schema, method identifier, project contract, result field, export, or workflow-state changes. Weaving, Two-Lane Segment, and Two-Lane Facility remain out of scope and untouched.
- Remaining limitations: representative system-Chrome qualification is not formal WCAG, axe, screen-reader, or cross-browser certification; 768 px coverage is narrow desktop/tablet width rather than small-phone coverage.
- Detailed evidence: `docs/ux/phase_16_4_freeway_ramp_ux_rollout.md` and temporary `output/playwright/phase16_4_freeway_ramp_ux_rollout/`.

## Phase 16.5: Weaving And Two-Lane Rollout

Goal: adapt the pattern to the more specialized geometry-heavy workflows.

Scope:

- Weaving:
  - Tie diagrams directly to geometry branch selection.
  - Keep lane-change parameters visible only when configuration requires them.
  - Clarify capacity failure versus HCM stopping/handoff at geometry decision points.
  - Preserve one/two-sided semantics, FFS source behavior, and advanced evidence inputs.
- Two-Lane Segment:
  - Preserve effective current curve and passing-lane disclosure.
  - Use Start, basics, directional traffic, geometry, and method-branch task order.
- Two-Lane Facility:
  - Keep the editor table central.
  - Clarify segment sequence, directional grouping, Passing Zone applicability, and row validation.
  - Preserve inactive opposing-value canonicalization and Issue #121 protection.

Exit criteria:

- Weaving handoff, capacity failure, and unsupported scope remain method-contract explanations.
- Two-Lane Segment remains fast for HCM specialists and clearer for occasional users.
- Facility editing remains table-first and guarded by row validation.
- Project, fingerprint, result, export, localization, unit, and stale-state contracts remain compatible.

Phase 16.5 local qualification result:

- Implementation and local browser qualification: **PASS**.
- System-Chrome matrix: `58/58` rows passed: Weaving `19/19`, Two-Lane Segment `17/17`, Two-Lane Facility `19/19`, plus `3/3` shared Start/project-load smokes.
- Coverage included English/Thai, 1280/768 px, Metric/Imperial, method branches, stale/Recalculate, capacity/handoff, project restore, and report/export controls.
- No console/page errors or horizontal overflow were recorded.
- No HCM formula, method, lookup, schema, fingerprint, result-field, or export-field changes were made.
- Detailed evidence: `docs/ux/phase_16_5_weaving_two_lane_ux_rollout.md` and temporary `output/playwright/phase16_5_weaving_two_lane_ux_rollout/`.
- Full repository suite: `1066 passed in 209.47s`.
- Release classification: **CONDITIONAL PASS** pending final review, PR/CI, and merge gates.

## Phase 16.6: App-Wide Release Qualification

Goal: complete app-wide consistency and release qualification after the specialized Weaving and Two-Lane rollout.

Scope:

- Review navigation, Supported Workflows, result hierarchy, stale states, project/export placement, localization, and accessibility at 768 px across all implemented workflows.
- Add formal keyboard-only, assistive-technology, and cross-browser qualification where available.
- Update release notes and the app-wide qualification matrix.
- Keep methodology, scope, and workflow-specific assumptions under separate scrutinize review before any implementation expansion.

Validation:

- Full test suite and release packaging checks.
- App-wide browser qualification matrix.
- Documentation review that no method scope was implied beyond implemented support.

## Risk Register

| Risk | Phase | Mitigation |
| --- | --- | --- |
| Session-state key churn causes stale or lost inputs | 16.2 | Keep explicit migration/default handling and add AppTest coverage. |
| Copy implies unsupported HCM interpolation | 16.2 | Use scrutinize review for Truck Mix and PCE language before merge. |
| Project files load but branch UI does not restore correctly | 16.2 | Add project load tests for each FFS and heavy-vehicle adjustment branch. |
| Export availability regresses for current/stale states | 16.2-16.6 | Keep current-result-only tests per workflow. |
| Narrow Thai labels overflow | 16.2-16.6 | Browser screenshot review at 768 px for Thai. |
| Rollout broadens scope accidentally | all | Treat methodology changes as separate phases with source verification and validation fixtures. |

## Issue And PR Guidance

Parent issue: `Phase 16: Improve task-oriented calculator UX`.

Phase 16.1 PR should include only:

- `docs/ux/phase_16_1_ux_audit.md`
- `docs/ux/multilane_ux_pilot_spec.md`
- `docs/ux/phase_16_implementation_plan.md`

Do not commit temporary screenshots, Playwright output, source changes, localization catalog changes, schema changes, or calculation changes in Phase 16.1.
