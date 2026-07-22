# Phase 16.1 UX Audit

Baseline: `fd5172ec3e4abdb161f268507c29c74b4848047c`
Version: `0.8.0`
Audit date: 2026-07-22
Evidence root: `output/playwright/phase16_1_ux_audit/`

## Executive Summary

The v0.8 UI is visually consistent, localized, and technically guarded, but the primary task flow still asks users to understand method structure before they can decide which fields matter. The most important UX issue is not styling. It is that calculation setup, project load/save, method scope, branch controls, stale-state messages, and audit/export surfaces all appear as peers in a compact two-column page.

The audit recommends **progressive disclosure within the current single-page Streamlit architecture** as the Phase 16.2 implementation strategy. It preserves the repository constraint against a multi-page wizard while materially reducing cognitive load. Multilane should be the pilot because it contains the broadest mix of branch logic: measured versus estimated FFS, Metric/Imperial, specific grade, Truck Mix, internal/external PCE, stale results, capacity failure, project files, and exports.

No production calculation engine, schema, fingerprint, localization catalog, or UI behavior was changed during this audit.

## User Profiles

**Profile A: HCM specialist.** Wants fast entry, explicit control, current/stale confidence, and immediate access to assumptions, lookup path, and intermediate values.

**Profile B: traffic engineer with limited HCM familiarity.** Understands traffic engineering data but needs the interface to explain which branch applies and why a field appears.

**Profile C: occasional internal professional user.** Has project data and needs a valid result without learning every HCM table boundary or internal implementation term.

The audit does not design for a public consumer. The tool remains a professional engineering worksheet.

## Audit Method

The browser audit used Python Playwright against the Streamlit app at `http://localhost:8516`. Evidence was captured in Chrome/Chromium at:

- Desktop viewport: approximately 1280 px.
- Narrow viewport: 768 px.
- English and Thai locale.
- Default Metric unit state for initial workflow captures; Multilane-specific states also covered calculated, stale, capacity failure, Truck Mix, and External PCE.

Structured evidence was written to `output/playwright/phase16_1_ux_audit/evidence_log.csv`. Temporary screenshots are in `output/playwright/phase16_1_ux_audit/screenshots/` and are intentionally ignored by Git.

Evidence totals:

| Workflow | Logged evidence rows |
| --- | ---: |
| Two-Lane Segment | 4 |
| Two-Lane Facility | 4 |
| Multilane Segment | 10 |
| Basic Freeway Segment | 4 |
| Weaving Segment | 4 |
| Merge Segment | 4 |
| Diverge Segment | 4 |
| Supported Workflows | 4 |

Browser limitation: the final optional Thai deep-state Multilane capture hit a localized Streamlit dropdown timeout. Thai evidence still exists for every workflow in desktop and 768 px initial states.

## Cross-Workflow Findings

| ID | Severity | Type | Finding | Evidence | Recommended action |
| --- | --- | --- | --- | --- | --- |
| UX-01 | High | Cross-workflow design-system issue | Project load appears before the core calculation setup. It is discoverable, but it makes a new blank calculation begin with file-management rather than the engineering task. | All calculator initial captures, for example `desktop_1280_en_multilane_blank_default.png`. | Keep project load available in Start, but visually subordinate it to Blank/Template and Unit. |
| UX-02 | High | Cross-workflow design-system issue | Result panes show Project output before any valid result. Save project is useful, but it competes with the first goal: calculate. | All calculator initial captures. | Show project save as secondary before calculation; after current result, group Save project and Export report together. |
| UX-03 | High | Cross-workflow design-system issue | Stale-result protection is technically strong, but stale recovery is not task-forward enough. Users see a warning and Save project while the intended next action is recalculate. | `desktop_1280_en_multilane_stale_after_input_change.png`; source state via `workflow_state`. | When stale, make Recalculate the primary action, hide result metrics and report exports, and show why the result is stale near the changed section when possible. |
| UX-04 | Medium | Cross-workflow design-system issue | Required and optional inputs are visually similar. Advanced, branch-specific, and core traffic fields use the same density and weight. | All calculator captures, especially Weaving and ramp modes at 768 px. | Use task sections: Start, Basics, Method branch, Calculate, Results, Audit/export. Keep advanced assumptions collapsed. |
| UX-05 | Medium | Documentation issue | Supported scope is accurate but often hidden in collapsed validation sections or phrased as method limitations rather than decision-point guidance. | Initial workflow screenshots and `Supported Workflows` page. | Keep the detailed validation section, but add short inline scope messages at branch choices that trigger limitations. |
| UX-06 | Medium | Cross-workflow design-system issue | Thai localization works, but acronyms and HCM branch terms remain untranslated or unexplained at the decision point. | `narrow_768_th_multilane_segment_initial.png`; Thai initial workflow screenshots. | Expand FFS, PCE, SUT, TT, PHF on first use in both English and Thai help/captions. |
| UX-07 | Medium | Cross-workflow design-system issue | Export discovery comes after several details sections. This reduces accidental stale export risk, but makes the successful task completion path harder to find. | Multilane calculated screenshot and result source flow. | After current result, provide a compact action row: Save project, Export report, and Details. Keep advanced formats inside Export report. |
| UX-08 | Medium | Accessibility and narrow layout | 768 px layout is usable but long. Users must scroll through many equally weighted controls and captions before the result and actions. | All `narrow_768_*` screenshots. | Keep single-page architecture, but collapse inactive branches and place a readiness/status summary before Calculate. |

## Workflow-By-Workflow Findings

### Two-Lane Segment

Visible tasks audited: blank calculation, unit change, required-field discovery, calculate path, invalid/unsupported recovery through existing guarded controls, stale state, project save/load affordances, export discovery, assumptions/evidence location.

Findings:

- **Medium, workflow-specific:** Segment type, terrain, and horizontal alignment are early and valid, but the user sees many method captions and inactive branch captions before calculating. This helps traceability but increases decision overhead for Profile C.
- **Medium, workflow-specific:** The horizontal-curve branch is correctly hidden until active. This pattern should be reused more aggressively in Multilane and freeway workflows.
- **Low, documentation issue:** The starting values expander has explanatory copy but no actual direct template action in the initial state, so it reads as a placeholder rather than a task.

### Two-Lane Facility

Visible tasks audited: blank/template-backed facility setup, unit change, segment table discovery, guarded invalid sequence, project load/reject, current result/export, assumptions/evidence.

Findings:

- **High, workflow-specific:** Facility table editing is inherently complex. The current UI exposes a professional table, but the first action and required sequence rules are not obvious without validation knowledge.
- **Medium, methodology/support-contract issue:** Guardrails around arbitrary segment sequences are method constraints, not UI defects. The UI should explain the supported facility template contract before table editing.
- **Medium, cross-workflow issue:** Recalculate/stale behavior should use the same status and action hierarchy as Multilane after the pilot proves the pattern.

### Multilane Segment

Visible tasks audited: blank calculation, optional defaults, Metric/Imperial, measured/estimated FFS, terrain, specific grade, Truck Mix, internal/external PCE, stable result, stale state, capacity failure, project save, export, assumptions/evidence.

Findings:

- **High, workflow-specific:** PCE Mode is presented as a separate technical control after grade has already been collected. For Profile B and C, this makes Heavy Vehicle %, Truck Mix, terrain, grade, and external PCE feel like peer inputs rather than mutually exclusive methods.
- **High, workflow-specific:** Truck Mix is labeled as a standalone traffic field. The UI does not state strongly enough that it means composition *within heavy vehicles*, while Heavy Vehicle % is share of total traffic.
- **High, methodology/support-contract issue:** The three Truck Mix choices are HCM table-domain constraints. The current help says only printed mixtures are supported, but the restriction should appear inline beside the choice and point users to External PCE.
- **High, cross-workflow issue:** Capacity failure reports LOS F correctly and hides predicted speed/density, but the cause is not tied to demand/capacity inputs near the result summary.
- **Medium, workflow-specific:** Measured/estimated FFS progressive disclosure works; left-side clearance appears only when divided median is selected. This is the strongest existing pattern for the pilot.
- **Medium, workflow-specific:** The Advanced section currently contains only a fixed driver-population note. It consumes hierarchy without offering an action.

### Basic Freeway Segment

Visible tasks audited: blank/preset, unit change, measured/estimated FFS, heavy-vehicle adjustment, advanced driver population, invalid/unsupported recovery, capacity failure, project/export, assumptions/evidence.

Findings:

- **High, cross-workflow issue:** Basic Freeway shares the Multilane PCE and Truck Mix ambiguity, though its advanced driver-population controls are better isolated.
- **Medium, workflow-specific:** Total ramp density is correctly explained as an FFS adjustment, not a ramp workflow. This is a useful inline limitation pattern.
- **Medium, methodology/support-contract issue:** Above-capacity behavior is an intended bounded method result, not a defect. It needs stronger result-level explanation.

### Weaving Segment

Visible tasks audited: blank/preset, unit change, geometry configuration, lane-change parameters, stable result, stale state, unsupported handoff, project/export, assumptions/evidence.

Findings:

- **High, workflow-specific:** Weaving requires many early geometry and lane-change decisions. HCM specialists can proceed, but Profile B users need a clearer geometry-first path with diagrams tied to the active configuration.
- **Medium, methodology/support-contract issue:** LS >= LMAX handoff and HCM 7.1 exclusions are method-support constraints. They should be explained as a scope decision, not only as post-run limitations.
- **Medium, accessibility/narrow layout:** At 768 px, the number of visible controls makes orientation and result discovery costly.

### Merge Segment

Visible tasks audited: blank/preset, unit change, geometry evidence, measured/estimated FFS, separate freeway/ramp demand and heavy vehicles, capacity warning/failure, project/export, assumptions/evidence.

Findings:

- **Medium, workflow-specific:** The diagram helps orientation. However, geometry evidence is hidden under an expander while the unsupported geometry contract is central to task success.
- **Medium, methodology/support-contract issue:** Isolated right-side one-lane scope is a method contract. The UI should keep that message closer to the geometry controls.
- **Low, workflow-specific:** Separate freeway and ramp PHF/heavy-vehicle inputs are accurate but visually dense.

### Diverge Segment

Visible tasks audited: blank/preset, unit change, geometry evidence, measured/estimated FFS, off-ramp demand validation, adjacent/wrong project rejection, capacity warning/failure, project/export, assumptions/evidence.

Findings:

- **Medium, workflow-specific:** Diverge has the same geometry-evidence and scope-disclosure issues as Merge.
- **Medium, validation/recovery:** Off-ramp demand cannot exceed upstream freeway demand. The validation is method-correct, but recovery would be easier if the affected field and relationship were shown inline.
- **Medium, methodology/support-contract issue:** Adjacent ramps and HCM 7.1 are correctly rejected as support constraints, not defects.

### Supported Workflows

Visible tasks audited: scope discovery, capabilities, limitations, English/Thai and narrow layout.

Findings:

- **Medium, documentation issue:** The page is accurate and useful as reference, but too much burden is placed on users finding it. Key limitations should also appear where users make branch decisions.
- **Low, cross-workflow issue:** The Supported Workflows page groups capabilities and limitations well; its concise supported/unsupported wording can seed inline copy in calculators.

## Severity Table

| Severity | Count | Primary themes |
| --- | ---: | --- |
| Critical | 1 | Default Two-Lane Facility AppTest calculation fails from inactive `NaN` opposing-volume values; documented as BUG-01 and left for a separate fix branch. |
| High | 8 | Stale-result recovery, Truck Mix/PCE mental model, project controls competing with calculation, capacity failure interpretation, complex Facility/Weaving entry. |
| Medium | 18 | Cognitive load, hidden method constraints, result/export discovery, Thai acronym explanation, narrow layout length, inline validation needs. |
| Low | 3 | Wording and consistency improvements. |

## Application Defects

One reproducible validation defect was confirmed during Phase 16.1 validation, outside the UX documentation changes:

| ID | Severity | Type | Reproducer | Expected | Actual | Recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| BUG-01 | Critical | Application defect / AppTest-visible Facility workflow | `python -m pytest tests/unit/test_streamlit_app.py::test_two_lane_facility_streamlit_stable_english_result_and_exports -q` | Default Two-Lane Facility template calculates and renders metrics/exports. | AppTest default Facility calculation stores `manual_facility_error = "Opposing-direction volume must be a finite numeric value."`; metrics and result dataframe do not render. | Fix in a separate hotfix branch before Phase 16.2 or before merging release-qualification work. Preserve the method contract by normalizing inactive opposing-volume cells to `None` or a method-valid default before engine submission. |

Minimal trace:

- Test helper opens `manual_facility`.
- `app.button[1].click().run()` clicks `Calculate`.
- Stored audit shows non-passing-zone rows carry `opposing_direction_volume_veh_h: nan`.
- Engine validation rejects the NaN value.

This branch does not fix BUG-01 because Phase 16.1 is documentation/evidence only and must not change production UI or calculation behavior.

Browser automation failures were separate test-tooling selector issues caused by Streamlit combobox implementation and localized labels; they were not classified as application defects.

Suspected but not defect-classified UX risks:

- Stale result save behavior is likely intentional because the saved project excludes stale results, but the visual hierarchy may still confuse users.
- Capacity failure output is method-correct, but its explanation is insufficiently close to the primary result.

## Methodology Constraints

The following are method/support-contract constraints, not UX defects:

- Multilane internal PCE lookup supports the implemented printed HCM table domain only.
- Multilane Truck Mix is bounded to 30% SUT / 70% TT, 50% SUT / 50% TT, and 70% SUT / 30% TT; other mixes require external PCE in the current bounded method.
- Multilane above-capacity cases report LOS F and do not predict speed or density.
- Basic Freeway, ramps, weaving, merge/diverge, managed lanes, work zones, reliability, and facility/corridor workflows are separate or unsupported in specific calculators.
- Weaving HCM 7.1, C-D roadways, and handoff conditions remain outside implemented scope.
- Merge/Diverge are isolated right-side one-lane HCM 7.0 workflows only.

## Recommended Priorities

1. Phase 16.2: implement the Multilane progressive-disclosure pilot without changing calculation logic.
2. Phase 16.3: qualify the pilot with regression tests and browser evidence before rollout.
3. Phase 16.4: apply proven patterns to Basic Freeway, Merge, and Diverge.
4. Phase 16.5: apply selected patterns to Weaving and Two-Lane Segment.
5. Phase 16.6: qualify Two-Lane Facility and app-wide release behavior.

Scrutinize verdict for Phase 16.1 recommendation: **fix-then-ship for production UX**, but **ship this audit/specification as the correct next step**. The problem is real, and a smaller copy-only pass would not resolve the main task-flow issue.
