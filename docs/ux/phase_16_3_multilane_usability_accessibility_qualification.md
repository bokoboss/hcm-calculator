# Phase 16.3: Multilane Usability and Accessibility Qualification

Date: 2026-08-07
Scope: Multilane Highway Segment pilot only
Decision: **CONDITIONAL PASS — accepted for the Multilane pilot; not an app-wide rollout approval**

## Qualification summary

The Phase 16.2 one-page progressive-disclosure pilot was exercised from the perspective of an HCM engineer/operator across blank entry, validated starting values, free-flow-speed branches, heavy-vehicle adjustment branches, stale recovery, capacity failure, project load/save, report export, localization, keyboard navigation, and narrow layouts.

The qualification found and fixed two material risks before the final gate:

1. The visible SUT/TT guidance did not explicitly repeat that composition is within the heavy-vehicle portion of total traffic. This could be confused with Heavy Vehicle % of total traffic.
2. The default red/white primary-button treatment sampled at approximately 4.00:1 contrast. The Multilane Calculate/Recalculate control now uses a scoped blue treatment at approximately 7.20:1.

No calculation engine, HCM formula, lookup domain, normalized input, project schema, fingerprint, result contract, or other workflow was changed.

Remaining limitations are Minor: at 768 px Streamlit can preserve the Calculate control’s scroll position, leaving result metrics above the current viewport after calculation; long Median type values can ellipsize in the narrow two-column input grid. Both controls remain native, labelled, and usable. These are recorded for Phase 16.4 rather than treated as rollout blockers.

This is a representative operator qualification, not a moderated participant study or a formal WCAG conformance audit. Screen-reader, browser-compatibility, and automated axe scans remain follow-up work.

## Baseline and evidence

- Qualification branch: `codex/phase-16-3-multilane-usability-accessibility`.
- Baseline tree: `63de783` (`Phase 16.2: Implement Multilane UX pilot`); the Phase 16.2 comparison worktree at `7a6199b` has the same source tree.
- Original dirty checkout was not used for edits.
- Browser: Python Playwright driving installed system Chrome at `C:\Program Files\Google\Chrome\Application\chrome.exe`.
- Streamlit was launched with the isolated worktree `src` path explicitly selected.
- Metric evidence: `output/playwright/phase16_3_multilane_usability_accessibility_metric/`.
- Imperial evidence: `output/playwright/phase16_3_multilane_usability_accessibility_imperial/`.
- The screenshot, accessibility JSON, matrix, and compatibility outputs are temporary, ignored evidence and are intentionally not committed.

## Profiles and task matrix

| Profile | Locale | Units | Viewport | Representative tasks | Result |
| --- | --- | --- | --- | --- | --- |
| A — HCM engineer/operator | English | Metric and Imperial | 1280 px | Blank case, measured/estimated FFS, General terrain, Specific grade, supported SUT/TT, External PCE, stale/Recalculate, capacity failure, project/report, keyboard | Passed |
| B — localized operator | Thai | Metric and Imperial | 1280 px | Same branch and recovery tasks plus EN↔TH branch-preservation checks | Passed |
| C — constrained/narrow operator | English | Metric and Imperial | 768 px | Blank/branch paths, stale, result summary, capacity failure, project/report, keyboard spot check | Passed with Minor follow-ups |

Each unit system used the same 27-row scenario set:

- Rows 1–10: English at 1280 px — blank basic case, estimated/general, Specific grade, unsupported-mix discovery, External PCE, stale/Recalculate, capacity failure, project load, save/export, keyboard navigation.
- Rows 11–18: Thai at 1280 px — blank, Specific grade, External PCE, stale, capacity failure, project/export, EN→TH, and TH→EN branch preservation.
- Rows 19–27: English at 768 px — blank, estimated, Specific grade, External PCE, stale, result summary, capacity failure, project/export, keyboard spot check.

Final browser results:

| Unit system | Passed | Console/page errors | Horizontal overflow |
| --- | ---: | ---: | ---: |
| Metric | 27/27 | 0 | 0 |
| Imperial | 27/27 | 0 | 0 |
| Total | **54/54** | **0** | **0** |

## Representative review findings

### Heavy Vehicle % versus SUT/TT

The primary input is labelled `Heavy Vehicle % of total traffic`. The Specific grade branch is labelled `Heavy-vehicle composition (SUT/TT)` and now places this visible sentence immediately below the control:

> SUT/TT is the mix within the heavy-vehicle portion of total traffic; it is not another percentage of total traffic. The internal HCM lookup supports these three table compositions. For other observed truck compositions, use External PCE. No Truck Mix interpolation is applied.

The Thai catalog carries the same distinction. The browser checks opened the composition control and confirmed only the three supported table choices: 30/70, 50/50, and 70/30. A 40/60 observed mix is not offered or interpolated; the visible guidance points to External PCE.

### External PCE escape path

External PCE is a first-class method choice. Selecting it removes the internal terrain and SUT/TT controls, exposes the engineer-entered PCE field, and states that the internal lookup is bypassed and the external value must be traceable to an approved source. Results report the external override source.

### Stale state and recovery

Changing a calculated input removes stale metrics and report downloads, exposes the localized stale message, and changes the primary action to Recalculate. The recovery action remains visible and unambiguous in English and Thai at both tested unit systems.

### Result hierarchy and capacity failure

At the result surface, LOS and density are the hero finding, followed by demand/capacity, mean speed, capacity, capacity status, demand flow, adjusted FFS, PCE, and the heavy-vehicle factor. Capacity failure retains LOS F and demand/capacity/status, while speed and density show Not predicted and the warning explains why. The 768 px DOM checks confirmed the result metrics remain present and labelled; the remaining narrow-layout limitation is scroll position after the Calculate control receives focus.

### Project, report, and details actions

Project JSON is presented as editable/reloadable calculation state. Save is unavailable until inputs are valid, stale saves contain inputs only, and a current project round-trip restores the branch and result. Report formats remain subordinate under the Export report expander. Calculation details and audit information remain behind the Details / engineering record expander. Project load feedback is visibly distinct from report export.

### Copy fit and localization

The English and Thai branch labels, help text, stale/recovery messages, capacity warning, project/export labels, and SUT/TT clarification were reviewed at 1280 px and 768 px. Thai rows 11–18 were rerun after correcting the temporary harness so they select the Thai application locale before each action; final screenshots contain Thai headings, labels, unit strings, and branch copy. EN↔TH switching preserved the selected branch and current result.

## Accessibility qualification

The checks were deliberately limited to evidence supported by the running application:

- Native Streamlit inputs, segmented controls, comboboxes, buttons, alerts, and expanders were inspected through the browser DOM.
- Controls exposed accessible labels for the main fields, including Heavy Vehicle %, FFS source, active branch fields, PCE, project actions, and locale controls.
- The matrix captured 59–75 controls per state depending on active branch and result/export surfaces, plus status regions and headings.
- A 45-tab probe in each keyboard scenario reached Calculate/Recalculate, visited 35 unique labelled controls, and observed no keyboard trap.
- No horizontal overflow was found at either viewport or unit system.
- The Multilane primary button now samples as RGB `(36, 91, 134)` with white text, approximately 7.20:1 contrast. The style is scoped to the Multilane Calculate/Recalculate container.

Not assessed as formal conformance claims:

- Screen-reader announcements and interaction with a real assistive technology.
- Automated axe/WCAG scanning.
- Safari/Firefox behavior, browser zoom, reduced-motion settings, and high-contrast OS modes.
- Moderated participant completion time, error rate, or satisfaction.

## Remediation record

| Finding | Severity before fix | Remediation | Final disposition |
| --- | --- | --- | --- |
| SUT/TT scope was only implicit in visible guidance | Major qualification risk | Added explicit bilingual visible scope sentence and localization assertions | Fixed; final matrix passed |
| Primary Calculate/Recalculate contrast sampled about 4.00:1 | Major accessibility risk | Added Multilane-only scoped blue primary-button style; verified about 7.20:1 in system Chrome | Fixed; final matrix passed |
| Result can be above viewport after narrow Calculate action | Minor | No behavior change in this phase; recorded for responsive follow-up | Accepted for pilot; Phase 16.4 |
| Median type value can ellipsize in narrow two-column grid | Minor | No behavior change in this phase; native labelled select remains complete when opened | Accepted for pilot; Phase 16.4 |

## Phase 16.1 acceptance comparison

| Phase 16.1 concern | Phase 16.3 result |
| --- | --- |
| Method-structured UI and peer-control clutter | Improved: one-page task order and one active heavy-vehicle method at a time |
| Heavy Vehicle % versus Truck Mix/SUT/TT ambiguity | Fixed: explicit visible scope copy now distinguishes the two percentages |
| Internal lookup domain and unsupported mix behavior | Improved: three supported table compositions are visible; unsupported observed mixes point to External PCE with no interpolation |
| PCE Mode presented as a technical peer control | Improved: General terrain, Specific grade, and External PCE are task choices |
| Stale result recovery | Improved: stale results and unavailable exports are removed; Recalculate is primary |
| Capacity failure explanation | Improved: LOS F, v/c/status, and Not predicted speed/density semantics remain together |
| Result hierarchy | Improved at desktop and present in the narrow DOM; Minor narrow scroll-position follow-up remains |
| Project and export placement | Improved: project state is separated from subordinate report formats |
| Narrow layout | Improved: 1280/768 Metric and Imperial runs had no horizontal overflow; Minor truncation/scroll follow-ups remain |
| Calculation and project/report contracts | Unchanged and verified by exact compatibility comparison |

## Automated validation and compatibility

- Focused Multilane/UI/localization/project/workflow/reporting suites: **217 passed**.
- Final focused Streamlit AppTest file: **73 passed**.
- Final full repository suite: **1048 passed**.
- `python -m compileall -q src tests`: passed.
- `git diff --check`: passed.
- Exact compatibility comparison: **7/7 representative paths equal** after normalizing only nondeterministic project `created_at` timestamps. Cases covered measured/general, estimated/general, Specific grade with 30/70, 50/50, and 70/30, External PCE, and capacity failure.
- Persisted project contract remained `schema_version` 1.2, `project_type` `manual_multilane_v0`, method `hcm7_multilane_los`, contract `phase_8`, with unchanged calculation fingerprints, result payloads, and field structure.
- Report structure remained `manual_multilane_v0` with unchanged summary, intermediate-value, audit, limitation, and presentation fields.

## Decision and rollout readiness

**CONDITIONAL PASS.** The Multilane pilot is acceptable for controlled pilot rollout. No Blocker or unresolved Major finding remains, and all requested Metric/Imperial, English/Thai, 1280/768, stale, capacity, project/report, keyboard, and compatibility gates passed.

The condition is that this result does not authorize copying Multilane methodology assumptions into other workflows. Phase 16.4 should generalize only the presentation patterns below, with each workflow independently scrutinized and qualified:

1. Reuse ordered single-page task sections: Start, inputs, active method branch, Calculate, result summary, result actions, details.
2. Reuse active-branch disclosure, stale/Recalculate hierarchy, current-result-only export behavior, project/report separation, native accessible controls, bilingual scope copy, and scoped contrast treatment.
3. Start with a Basic Freeway pilot, then qualify Merge and Diverge separately. Each workflow needs its own HCM Chapter 26 fixtures, support-domain wording, project/fingerprint compatibility checks, EN/TH browser matrix, 1280/768 visual review, and keyboard/assistive-technology follow-up.
4. Do not copy Multilane-specific SUT/TT choices, External PCE rules, lookup-domain language, equations, or engine contracts into Basic Freeway, Merge, or Diverge.

Issue #119 should remain open for rollout tracking until the Phase 16.4 scope and the remaining formal accessibility/human-review work are accepted.
