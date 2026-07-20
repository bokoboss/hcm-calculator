# App-wide UI system (Phase 15.1)

## Decision and principles

This is a calculator-first, single-page worksheet application. The calculator, not explanatory prose, is the primary surface. Every qualified method must preserve auditable inputs, method scope, intermediate values, and exports; UI convenience must never infer geometry or alter canonical calculation inputs.

Use one clear action, one current-result identity, visible units, and equivalent English/Thai engineering meaning. Keep the numerical engine, project schema, input fingerprint, qualified input set, and export fields unchanged in Phase 15.2 unless a backward-compatible defect fix is separately approved.

## Navigation

Phase 15.2 replaces the flat eight-option radio with a sidebar grouped selector
using stable internal workflow identifiers, not localized labels. The groups are:

1. Roadways: **Two-Lane Segment / ช่วงถนนสองช่องจราจร**, **Two-Lane Facility / สิ่งอำนวยความสะดวกถนนสองช่องจราจร**, **Multilane Segment / ช่วงถนนหลายช่องจราจร**.
2. Freeways: **Basic Freeway Segment / ช่วงทางด่วนพื้นฐาน**, **Weaving Segment / ช่วงสานการจราจร**, **Merge Segment / ช่วงรวมกระแส**, **Diverge Segment / ช่วงแยกกระแส**.
3. Reference: **Supported Workflows / ขอบเขตงานที่รองรับ**.

Use a short category heading plus selectbox, not tabs: the choices are growing
and labels are long in Thai. Keep the selected workflow in a namespaced session
key. Internal validation examples remain query-parameter-only and do not appear
in public navigation. Navigation changes do not affect method contracts.

## Mandatory worksheet sequence

1. Header: title, HCM version/qualification badge, one-sentence scope.
2. Starting values: optional preset/template and display-unit selector.
3. Geometry/roadway configuration.
4. Traffic demand.
5. Free-flow speed and adjustment inputs.
6. Heavy vehicles and other adjustment factors.
7. Advanced/optional evidence.
8. Configuration diagram, immediately after the geometry it explains.
9. Primary Calculate/Recalculate action.
10. Result summary.
11. Engineering warnings and interpretation.
12. Calculation details and audit trail.
13. Save project.
14. Export/report.
15. Validation basis and limitations.

Allowed deviations: facility segment table replaces the single geometry/traffic sequence; weaving has geometry evidence before traffic; merge/diverge place their diagram after geometry; unsupported/stopping results interrupt at 10 but retain inputs and limitations. Required inputs may not be collapsed.

## Compactness and layout

No more than two short captions before the first input. Use two columns only for independent short fields with compatible units; use one column for long Thai labels, conditional fields, text evidence, tables, and any control narrower than 240 px. Use a single section header followed by 8--16 px before the first control and 20--28 px between sections. Group related numbers horizontally only when the group is understandable without scanning across rows.

Diagrams have a minimum readable width of 480 px (otherwise stack below inputs), an alt/caption, a legend where movement codes appear, and the statement that they are conceptual references rather than survey/CAD geometry. Show at most four secondary metrics above the fold and at most one secondary expander open by default. Do not nest containers merely for spacing.

## Controls and actions

| Decision | Standard |
|---|---|
| Radio | 2--4 consequential choices needing visible comparison; horizontal only for short labels. |
| Segmented control | 2--4 short mutually exclusive display modes only after verifying installed Streamlit/AppTest accessibility; do not require an upgrade. |
| Selectbox | More than four choices, presets, long Thai labels, or space-sensitive choice. |
| Tabs | Results versus audit only; never sequential required inputs, and never save/export formats. |
| Toggle | Immediate binary mode/state. |
| Checkbox | Optional inclusion, acknowledgement, or evidence; fixed unsupported values are text, not a disabled-looking control. |
| Number input | Unit in label, documented precision/step, explicit min/max and help; disabled only when the selected method mode makes it inapplicable. No silent clipping. |
| Expander | Advanced optional inputs, audit, methodology, limitations, or secondary exports only. |

Use one full-width primary `Calculate` before a result and `Recalculate` while stale. Place Load and Reset as secondary actions at starting values; group Save and downloads after a current result. A disabled action states why it is disabled. Use sentence case and localized action text. Reset must not compete with Calculate.

## Result-state system

| State | Hero and status | Metrics/audit/save/export | Primary action |
|---|---|---|---|
| `prerun` | Neutral "Calculation required / ต้องคำนวณ" | No result metrics; no audit; save inputs only if valid; no result export | Calculate |
| `valid_current_result` | Result hero (LOS where assigned) | Primary + up to four secondary metrics; audit/save/export enabled | Recalculate |
| `valid_current_result_with_warning` | Normal hero plus amber engineering warning | Same as valid; warning remains above details | Recalculate |
| `capacity_failure` | LOS F, amber/red capacity message; distinguish from app error | Capacity/v-c shown; speed/density show "Not predicted / ไม่ทำนาย"; audit/save/export enabled | Recalculate |
| `hcm_stopping_or_handoff` | Neutral/amber handoff panel | Only entered/check metrics; audit and input save enabled; result export disabled unless it is an explicit handoff record | Revise geometry |
| `stale_result` | Amber "Input changed — recalculate required / ข้อมูลเปลี่ยน ต้องคำนวณใหม่" | Hide result metrics, audit and result exports; save current inputs allowed | Recalculate |
| `invalid_input` | Red field-oriented validation summary | No nulls/zeros masquerading as results; audit/export disabled | Correct inputs |
| `unsupported_scope` | Neutral/amber scope panel, never a calculated LOS | No calculated metrics; input save permitted; result export disabled | Choose supported case |
| `internal_error` | Red application-error panel with safe reference ID | No metrics/audit/export; retain entered inputs | Try again |

Never use a generic red error for LOS F or a stopping condition, and never display an absent value as zero.

## Shared secondary areas

Project load belongs directly below starting values; save belongs after current
results; downloads are a collapsed Export/report section below save. Calculation
details precede audit/intermediate values, which precede validation/limitations.
Report presentation can follow the selected UI/export language, but filenames,
JSON keys, project schemas, fingerprints, method identifiers, HCM references,
equations, conventional units, and engine provenance strings remain
language-neutral and stable.

## Accessibility, responsiveness, and state

Every control has a unique programmatic label, required/optional indication, keyboard-reachable order matching visual order, and contextual help that does not rely on color. Headings follow the worksheet sequence; custom result HTML must meet contrast and have text status. Diagrams need concise text alternatives. Captions must remain at least 12 px equivalent and Thai must wrap rather than clip.

Use workflow-scoped keys: `workflow.<id>.<area>.<field>`. Store `ui.locale` and
display unit separately from canonical inputs. Unit-system switches reload the
visible worksheet values for the selected workflow and clear that workflow's
stored result, audit, and fingerprint before a new current result can be
exported; localized display labels must never enter calculation state. Prefix
result, preset, load, diagram, and fingerprint state by workflow, clear only
that workflow on preset/load change, and never reuse generic widget keys.
