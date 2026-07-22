# Phase 16 Implementation Plan

Baseline: `fd5172ec3e4abdb161f268507c29c74b4848047c`
Phase 16.1 status: audit and specification only

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

## Phase 16.3: Pilot Usability And Regression Qualification

Goal: qualify the Multilane pilot before rollout.

Scope:

- Browser matrix for Profile A/B/C tasks.
- Manual review of English and Thai copy fit at 768 px.
- Verify stale input, capacity failure, project load, malformed project rejection, current result export, and audit detail access.
- Review screenshots against Phase 16.1 acceptance criteria.

Exit criteria:

- No critical or high UX regression remains in Multilane.
- Existing test suite passes.
- Documentation and release notes identify no numerical-method change.

## Phase 16.4: Basic Freeway, Merge, And Diverge Rollout

Goal: apply proven task-section and stale/export hierarchy patterns to workflows closest to Multilane.

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

## Phase 16.5: Weaving And Two-Lane Rollout

Goal: adapt the pattern to the more specialized geometry-heavy workflows.

Scope:

- Weaving:
  - Tie diagrams directly to geometry branch selection.
  - Keep lane-change parameters visible only when configuration requires them.
  - Clarify handoff conditions at geometry decision points.
- Two-Lane Segment:
  - Preserve effective current curve and passing-lane disclosure.
  - Reduce inactive captions where a collapsed branch label is enough.

Exit criteria:

- Weaving handoff and unsupported scope remain method-contract explanations.
- Two-Lane Segment remains fast for HCM specialists and clearer for occasional users.

## Phase 16.6: Facility And App-Wide Release Qualification

Goal: complete app-wide consistency and release qualification.

Scope:

- Two-Lane Facility:
  - Improve template-first orientation.
  - Clarify segment sequence rules before table editing.
  - Preserve guarded facility support boundaries.
- App-wide:
  - Review navigation, Supported Workflows, result hierarchy, stale states, project/export placement, localization, and accessibility at 768 px.
  - Update release notes and qualification matrix.

Validation:

- Full test suite.
- Browser qualification matrix.
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
