# App-wide UI audit (Phase 15.1)

## Evidence and severity

Baseline: `1c8fdebd72393c5ff5912918c99c8fc4120408db`; clean worktree: `C:\Users\kittipat_t\Documents\hcm-calculator-phase-15-1`. Source, assets, AppTest, HTTP smoke, and rendered AppTest paths were inspected. The visible application inventory is seven calculator modes plus one information mode; validation examples are query-route-only and not public navigation.

| Mode (English / Thai target) | Status, sections and assets | Findings / Phase 15.2 priority |
|---|---|---|
| Two-Lane Segment / ช่วงถนนสองช่องจราจร | Calculator; defaults, geometry, traffic, FFS, HV/curves, schematic, result/audit/project/export. Metric/Imperial. | Medium: English setup labels/constants and long sidebar/intro copy bypass i18n; section order and shell differ from freeway views. Preserve useful schematic. P2. |
| Two-Lane Facility / สิ่งอำนวยความสะดวกถนนสองช่องจราจร | Calculator; template, editable segment table, result/audit/project/export. Metric/Imperial. | High: table workflow needs explicit required/optional and result-current cues; a facility-specific table is justified but needs the shared action/state areas. P1. |
| Multilane Segment / ช่วงถนนหลายช่องจราจร | Calculator; template, geometry, demand, FFS, HV/PCE, results, audit/project/export. Metric/Imperial. | High: capacity failure has LOS F and Not predicted correctly, but state styling needs shared capacity panel; `Adjusted capacity` hotfix is correctly absent. P1. |
| Basic Freeway Segment / ช่วงทางด่วนพื้นฐาน | Calculator; preset, geometry, demand, FFS, HV/PCE, results, audit/project/export. Metric/Imperial. | High: ramp-density help correctly says it is not a ramp workflow; make conditional FFS controls and capacity failure visibly distinct. P1. |
| Weaving Segment / ช่วงสานการจราจร | Calculator; preset, geometry/evidence, traffic, FFS/HV, one/two-sided PNG diagrams, results/audit/project/export. Metric/Imperial. | Medium: dense geometry evidence and diagram need a shared placement/caption/alt pattern; stopping/handoff needs taxonomy panel. P2. |
| Merge Segment / ช่วงรวมกระแส | Calculator; preset, geometry, demand, FFS/HV/evidence, merge SVG, results/audit/project/export. Metric/Imperial. | High: Thai navigation/title keys fall back to English in the catalog; diagram and derived demand are good local patterns to retain. P1. |
| Diverge Segment / ช่วงแยกกระแส | Calculator; same structure with deceleration SVG. Metric/Imperial. | High: same Thai fallback and capacity/warning distinction requirement; primary action wording must align with other methods. P1. |
| Supported Workflows / ขั้นตอนการทำงานที่รองรับ | Information; support, limitations, save/load/export summaries. | Medium: English-only hardcoded body and flat, long section list; should be localized and separated below calculators. P2. |

## Cross-workflow findings

| Severity | Finding | Recommended action |
|---|---|---|
| High | Navigation is a flat radio list that mixes all calculator families and information; it will not scale and separates related freeway modes only by list order. | Implement the grouped sidebar selector in the UI-system standard and update route AppTests. |
| High | Thai catalog intentionally assigns English values for `nav.merge_segment`, `nav.diverge_segment`, `ramp.merge.title`, and `ramp.diverge.title`; broad legacy surfaces still use English constants. | Complete catalog keys and remove visible hardcoded English through the existing `translate()` mechanism. |
| High | Result renderer has only freshness strings (`Ready`, `Calculated`, stale); it lacks an app-wide typed treatment for capacity, stopping, unsupported scope, and errors. | Implement the nine-state taxonomy and current-result export gate. |
| High | Required browser qualification is not presently demonstrable through the in-app browser although HTTP and AppTest run. | Add deterministic browser smoke routes/fixtures and make browser review a release gate. |
| Medium | Setup/load/defaults/action/exports have shared helper names but their placement and labels are not consistently localized. | Strengthen small shared primitives; migrate in the order in the implementation plan. |
| Medium | Custom unsafe HTML LOS panel uses color and compact uppercase styling; it needs textual state, contrast check, and Thai wrapping review. | Keep a native-first hero with accessible text and no color-only meaning. |
| Medium | Exports and reports contain English method prose. | Declare them intentionally language-neutral until localized templates are defined; do not create a second i18n system. |
| Low | Title case, `Run`/`Calculate` vocabulary, and captions vary. | Adopt sentence case and one localized Calculate/Recalculate vocabulary. |

No Critical calculation/display defect was reproduced by AppTest. The browser initially exposed an import failure because the server used the original dirty checkout’s editable package; restarting it with the audit worktree source removed that environment artifact. It is not a tracked baseline defect.
