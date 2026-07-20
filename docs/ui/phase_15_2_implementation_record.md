# Phase 15.2 implementation record

## Baseline and environment

- Worktree: `C:\Users\kittipat_t\Documents\hcm-calculator-phase-15-2`
- Starting SHA: `1729cfda9c1874f475d3207dd943d59ff7131241`
- Python: 3.12.10
- Streamlit: 1.59.2

## Delivered shared foundation

- Replaced the flat public workflow picker with compact grouped navigation:
  Roadways, Freeways, and Reference.
- Kept navigation state workflow-scoped and retained the existing internal
  query-parameter validation route.
- Added a Streamlit-independent `ResultPresentationState` taxonomy and resolver
  for pre-run, current, warning, capacity, handoff, stale, invalid, unsupported,
  and internal-error presentation.
- Added a native Streamlit state-panel renderer so capacity, stale, unsupported,
  and invalid states have typed presentation instead of raw tracebacks or generic
  application errors.
- Added localized navigation and shared result-state labels in English and Thai.
- Extended the shared project-output and export-section layout helpers so
  migrated workflows can provide localized section labels without changing older
  workflow behavior.

## Workflow migration status

### Multilane Segment — migrated and verified

- Migrated the visible Multilane route, setup controls, defaults, geometry,
  demand, heavy-vehicle/PCE, advanced, validation, result, audit, project-load,
  project-save, and report-export surfaces to English/Thai localization.
- Preserved canonical internal widget and adapter values for unit system, FFS
  source, PCE mode, median type, terrain type, truck mix, template IDs, and
  normalized engine inputs.
- Kept the canonical result output metric as `display["capacity"]` with visible
  label `Capacity`; capacity status remains a separate presentation field.
- Distinguished unsupported scope, invalid input, stale result, capacity failure,
  current result with warnings, and pre-run states with typed
  `ResultPresentationState` handling.
- Hid current-result metrics and report export when inputs become stale.
- Ensured unit-system or starting-value changes clear stored Multilane results,
  audit state, and the calculation fingerprint before displaying reset inputs.
- Preserved project-save compatibility. A result and audit are included only
  when the stored result still matches the visible worksheet inputs.
- Preserved project-load compatibility for current-result and malformed-project
  cases, including stored presentation-locale restoration for Multilane projects.
- Kept report exports available only for current results, including calculated
  capacity-failure results.

### Basic Freeway Segment — migrated and verified

- Migrated the visible Basic Freeway route, setup controls, starting values,
  roadway geometry, traffic demand, FFS, heavy-vehicle/PCE, advanced SAF/CAF,
  validation, result, audit, project-load, project-save, and report-export
  surfaces to English/Thai localization.
- Kept technical identifiers, serialized keys, method names, HCM references,
  units, and engine provenance values language-neutral.
- Applied the shared section order: header/scope, project load and starting
  values, geometry, demand, FFS, heavy vehicles/adjustments, advanced optional
  controls, Calculate, typed result summary, warnings/capacity interpretation,
  details/audit, project save, export/report, validation/limitations.
- Reworked FFS controls so measured mode shows only measured FFS and estimated
  mode shows base FFS, lane width, right-side lateral clearance, and total ramp
  density. The ramp-density help states that it is a Chapter 12 estimated FFS
  variable, not a ramp-junction analysis.
- Integrated `ResultPresentationState` for pre-run, valid current result,
  warning result, capacity failure, stale result, invalid input, unsupported
  scope, and internal-error presentation. Stale results hide metrics and report
  downloads; capacity failure remains a calculated current result with exports.
- Preserved project schema, project type, method identifier, method version,
  normalized engine input fingerprints, stored `null` values, and stale stored
  result rejection.
- Preserved CSV, Excel, Markdown, report JSON, and project JSON export behavior
  for current results, including above-capacity results with null speed/density.
- Added canonicalization around Basic Freeway segmented controls so English/Thai
  locale switches cannot pass localized labels into the calculation adapter.
- Unit or preset changes now clear stored Basic Freeway results, audit records,
  and workflow fingerprints to match the shared Multilane policy.

### Merge Segment - migrated and verified

- Migrated the visible Merge route, setup controls, project load, freeway/ramp
  geometry, traffic demand, freeway FFS, ramp FFS, component PHF/HV, geometry
  evidence, diagram, result, audit, project-save, and report-export surfaces to
  English/Thai localization.
- Updated the Thai navigation/title to the reviewed terminology for
  `ช่วงรวมกระแส`; HCM, LOS, FFS, PHF, LA, units, method identifiers, schema
  keys, and exported technical fields remain language-neutral.
- Applied the shared section order: header and qualified scope, project/load and
  starting values, freeway/ramp geometry, demand, FFS, PHF/HV, evidence,
  diagram, Calculate, typed result summary, warning/capacity interpretation,
  details/audit, project save, export/report, validation/limitations.
- Separated freeway and ramp component inputs. Fixed qualified geometry is now
  presented as read-only scope text: isolated context, right-side ramp, one ramp
  lane. No normal UI path exposes left-side ramps, two-lane ramps, adjacent
  context, lane additions, or major merge.
- Kept LA visible with unit-aware Metric/Imperial conversion and tied it to the
  diagram summary. The SVG remains a conceptual reference and does not derive
  geometry.
- Replaced legacy result rendering with `ResultPresentationState` handling for
  pre-run, valid current result, warning-only, capacity failure, stale result,
  invalid input, unsupported scope, and internal-error paths. Stale Merge results
  hide metrics and report downloads; current capacity failures keep project and
  report exports available.
- Preserved the maximum-desirable influence-flow exceedance as a valid warning
  state. LOS, density, speeds, actual influence flow, desirable maximum, capacity
  status, project save, and report exports remain visible when roadway capacity
  has not failed.
- Preserved capacity-failure semantics: LOS F, governing capacity, v/c,
  governing reason, and Not predicted speed/density are shown without zero-fill.
- Preserved project type `manual_freeway_merge_segment_v1`, method version,
  calculation contract, normalized inputs, fingerprints, result identity, stored
  nulls, and report/export field names.

### Diverge Segment - migrated and verified

- Migrated the visible Diverge route, setup controls, project load, separated
  freeway/off-ramp geometry, traffic demand, freeway FFS, ramp FFS, component
  PHF/HV, geometry evidence, diagram, result, audit, project-save, and
  report-export surfaces to English/Thai localization.
- Updated the Thai navigation/title to the approved terminology
  `ช่วงแยกกระแส`; HCM, LOS, FFS, PHF, LD, units, method identifiers, schema
  keys, and exported technical fields remain language-neutral.
- Applied the shared section order used by the other migrated freeway
  workflows. The isolated HCM 7.0 support envelope remains visible near setup
  and is not hidden in the validation expander.
- Separated freeway and off-ramp component inputs. Fixed qualified geometry is
  presented as read-only scope text: isolated context, right-side off-ramp, one
  ramp lane. No normal UI path exposes left-side ramps, two-lane ramps,
  adjacent context, lane drops, option lanes, or major diverges.
- Kept LD visible with unit-aware Metric/Imperial conversion and tied it to the
  diagram summary. The SVG remains a conceptual reference and does not derive
  geometry.
- Shows continuing freeway demand as read-only raw arithmetic before
  calculation, distinct from the engine's normalized pc/h result output.
  Off-ramp demand greater than upstream freeway demand is classified as invalid
  input with a localized explanation and no fabricated result.
- Uses `ResultPresentationState` for pre-run, valid current result,
  warning-only, capacity failure, stale result, invalid input, unsupported
  scope, and internal-error paths. Stale Diverge results hide metrics and report
  downloads; current capacity failures keep project and report exports
  available.
- Preserves the maximum-desirable influence-flow exceedance as a valid warning
  state. LOS, density, speeds, actual influence flow, desirable maximum,
  capacity status, project save, and report exports remain visible when roadway
  capacity has not failed.
- Preserves capacity-failure semantics: LOS F, governing capacity, v/c,
  governing reason, and Not predicted speed/density are shown without zero-fill.
- Preserved project type `manual_freeway_diverge_segment_v1`, method version,
  calculation contract, normalized inputs, fingerprints, result identity, stored
  nulls, and report/export field names. Project loading now rejects unsupported
  saved normalized ramp geometry before restoring a result.

### Two-Lane Segment - migrated and verified

- Migrated the visible Two-Lane Segment route, setup controls, starting values,
  segment type, terrain, alignment, geometry, traffic demand, FFS/roadway
  adjustment explanation, advanced grade/curve/passing-lane controls,
  schematic, validation, result, audit, project-load, project-save, and
  report-export surfaces to English/Thai localization.
- Kept canonical internal values for unit system, segment type, terrain,
  horizontal alignment, method identifier, calculation contract, normalized
  engine inputs, project schema keys, report field names, HCM references, and
  engineering units.
- Applied the shared worksheet order used by the migrated workflows: header and
  scope, project load, setup/starting values, roadway geometry, traffic demand,
  FFS/roadway adjustment explanation, advanced grade/curve/passing controls,
  schematic, Calculate, typed result summary, details/audit, project save,
  export/report, and validation/limitations.
- Replaced the legacy form submit path with immediate controls and a Calculate
  button so edited inputs update the workflow fingerprint before result-state
  resolution. This prevents stale current-result leakage after field edits.
- Integrated `ResultPresentationState` for pre-run, valid current result,
  warning result, stale result, invalid input, unsupported scope, and
  internal-error presentation. The bounded Two-Lane Segment method does not use
  the shared capacity-failure contract.
- Hid result metrics and report exports when the current worksheet inputs no
  longer match the calculated fingerprint. Project files include a result only
  when the stored audit inputs match the visible worksheet inputs.
- Preserved project-load compatibility for current-result, wrong-type, and
  malformed-project paths, including stored presentation-locale restoration.
- Retained the existing Two-Lane schematic asset as a localized shared-style
  conceptual reference. The schematic now summarizes active segment type,
  length, alignment, and grade context and is explicitly not a calculation
  input.
- Kept horizontal-curve generation and data-editor controls visible only on the
  curve branch; kept the passing-lane branch explicit without inferring
  downstream facility effects.

### Two-Lane Facility - migrated and verified

- Migrated the visible Two-Lane Facility route to the shared Phase 15.2
  worksheet pattern while preserving the facility-specific table-first workflow.
- Added localized English/Thai keys for header, scope, project load, template,
  unit selection, segment-table headings, table guidance, validation summary,
  Calculate/Recalculate, typed result states, facility summary, segment-result
  table, audit/details, project save, export/report, validation basis, and
  limitations.
- Kept canonical row values, template IDs, project schema keys, method
  identifiers, calculation contract, fingerprints, HCM references, and units
  unchanged for compatibility.
- Replaced the collapsed defaults pattern with a visible compact facility
  template selectbox. Template or unit changes reload the displayed rows and
  clear stored result/audit/fingerprint state before presentation.
- Canonicalized the Facility unit segmented-control state before calculation so
  inherited localized labels from an English/Thai browser session cannot reach
  the calculation template loader.
- Added a non-calculating table validation summary that identifies valid tables,
  missing required fields, invalid numeric fields, and unsupported table
  combinations with affected row/field detail.
- Preserved the editable table workflow with ordered columns for ID/name/type,
  passing-lane role, length/speed, traffic, PHF/HV, terrain/grade/alignment,
  lane/shoulder width, and access density. Helper columns for legacy
  passing/downstream booleans and curve subsegments are hidden from the editor.
- Integrated `ResultPresentationState` for pre-run, current result,
  warning-result, stale result, invalid input, unsupported scope, and internal
  error presentation. Stale Facility results hide facility/segment metrics and
  block report exports.
- Added a compact facility result hierarchy: LOS hero with follower density,
  weighted average speed, facility length, segment count, governing segment, and
  a secondary localized segment-result table. Facility weighting remains engine
  output only and is not recomputed in Streamlit.
- Preserved project compatibility for current-result load, wrong-type rejection,
  malformed-project rejection, presentation-locale metadata, segment order, and
  stale-result withholding. Project save includes result/audit only when the
  stored audit rows match the visible table rows.
- Preserved CSV, Excel, Markdown, report JSON, result JSON, and project JSON
  behavior for current results. Stale, invalid, and unsupported states do not
  fabricate exportable report results.

## Weaving Segment completion

- Migrated the Weaving Segment worksheet to the shared Phase 15.2 single-page
  pattern: localized starting values, project load, configuration/geometry,
  movement demand, FFS/heavy-vehicle controls, required geometry evidence,
  packaged one-sided/two-sided PNG references, typed result states, project
  output, and current-result-only report exports.
- Preserved Weaving engine inputs, method version, calculation contract,
  project schema, report type, result dictionaries, fingerprints, and packaged
  diagram assets.
- Browser review found and corrected two UI-only defects:
  - over-capacity Weaving results were visually classified as handoff because
    the facade treated every `stopping_handoff_reason` as a handoff signal;
    the UI now uses the canonical `support_status`/`scope_status` handoff
    markers so capacity failure remains distinct and exportable.
  - long-segment handoff rendered a raw `TypeError` when formatting a null
    capacity metric; the UI now displays the localized Not predicted value.
- Direct browser evidence was captured with Chrome/Selenium against the local
  Streamlit server at `http://localhost:8512` under
  `output/playwright/phase15_2_weaving_gate/`. Screenshots and generated
  project fixtures are temporary, untracked artifacts and were not staged.

Reviewed Weaving browser states:

| State | Locale | Viewport | Result |
|---|---|---|---|
| Current one-sided result with report export controls opened | English | 1280x900 | Pass: LOS/current metrics visible, report CSV/XLSX/Markdown/JSON controls available, no overflow or traceback. |
| Stale result after segment length edit | English | 1280x900 | Pass: stale warning visible; result metrics and download controls hidden. |
| Invalid missing case name | English | 1280x900 | Pass: invalid panel identifies `case_name is required`; no exports. |
| Unsupported two-sided zero RR movement | English | 1280x900 | Pass: unsupported panel identifies the positive RR movement requirement; visually distinct from invalid. |
| Capacity failure | English | 1280x900 | Pass: above-capacity warning, Not predicted speed/density, and current-result report exports visible. |
| Exact capacity boundary | English | 1280x900 | Pass: current LOS F result with displayed v/c of 1.000, no capacity-failure panel. |
| Long-segment handoff | English | 1280x900 | Pass: handoff/stopping panel and entered LS/computed LMAX visible; no traceback. |
| Valid two-sided result | English | 1280x900 | Pass: two-sided diagram and current result visible. |
| Current one-sided result | Thai | 1280x900 | Pass: Thai labels are readable in screenshot and current result renders without overflow or traceback. |
| Stale result after segment length edit | English | 768x900 | Pass: no horizontal document overflow; stale exports hidden. |
| Invalid missing case name | English | 768x900 | Pass: no horizontal document overflow; invalid field detail visible. |
| Valid project load with restored current result | English | 1280x900 | Pass: project load message and restored current LOS result visible. |
| Wrong project type load | Thai | 1280x900 | Pass: localized project-load error visible; no raw Python exception. |
| Malformed project load | Thai | 1280x900 | Pass: localized project-load error visible; no raw Python exception. |

Remaining Phase 15.3-only gaps:

- Full app-wide browser/wheel qualification for every workflow remains Phase
  15.3.
- Broader hardcoded-string elimination for non-migrated workflows remains open.
- Final app-wide browser/wheel qualification for all migrated workflows remains
  Phase 15.3.

## Direct visual verification

Browser verification used a local Streamlit server at `http://localhost:8501`.
Terminal Playwright CLI was unavailable because `npx` was not installed, so the
Codex in-app browser was used instead.

- Desktop English/Metric, 1280px wide: Multilane worksheet loaded, calculated,
  displayed LOS, density, canonical Capacity, capacity status, project save, and
  report export controls without horizontal overflow.
- Narrow English/Metric, 768px wide: setup and input labels followed the intended
  worksheet order with no horizontal overflow.
- Desktop Thai/Metric, 1280px wide: Multilane title, setup, unit controls,
  geometry, demand, heavy/PCE, result metrics, capacity status, and project
  labels localized with no horizontal overflow.
- Thai/Imperial and 768px narrow: input units switched to mph/ft/per mi with no
  horizontal overflow.
- Regression found and fixed during visual review: switching unit systems after a
  calculation previously left the old Metric result visible. The fix now clears
  the stored result/audit/fingerprint on unit or template changes.
- Basic Freeway desktop English/Metric, 1280px wide: required first inputs were
  visible in the approved order; estimated FFS showed base FFS, lane width,
  right-side clearance, and total ramp density; stable result showed LOS,
  density, speed, capacity, capacity status, project, and export sections with
  no horizontal overflow.
- Basic Freeway English/Metric, 768px wide: narrow layout retained section
  order, usable controls, no horizontal document overflow, and no result/export
  leakage when stale.
- Basic Freeway Thai/Metric desktop: localized header, setup, geometry, demand,
  FFS/ramp-density wording, result labels, project labels, and export section
  rendered without traceback or horizontal overflow. Browser automation required
  a unit-toggle event after locale switching; AppTest covers the normal Thai
  calculated route.
- Basic Freeway Thai/Imperial desktop and 768px: units switched to mph/mi/ft and
  Thai result labels wrapped without horizontal overflow.
- Basic Freeway capacity failure: LOS F, governing capacity, demand/capacity,
  and Not predicted speed/density rendered as a calculated state with current
  result exports still available.
- Basic Freeway stale state: changing demand after calculation hid all metrics
  and withheld report downloads until recalculation.
- Merge desktop English/Metric: first inputs remained visible, freeway/ramp
  grouping was clear, LA appeared in the worksheet and diagram summary, derived
  downstream demand was read-only, and stable result exports were available.
- Merge English/Metric 768px: grouped controls, diagram, Calculate placement,
  result hierarchy, project save, and export/report sections rendered without
  horizontal overflow in AppTest-backed layout review.
- Merge Thai/Metric and Thai/Imperial: title, section labels, action labels,
  result labels, project controls, and export controls localized; HCM/LOS/FFS/
  PHF/LA/units remained language-neutral.
- Merge warning-only state: maximum desirable influence-flow exceedance rendered
  as a non-capacity valid result with LOS/density/speed still visible and report
  exports available.
- Merge capacity-failure state: LOS F, v/c, governing reason, and Not predicted
  speed/density rendered as a calculated state with current exports available.
- Merge stale state: changing on-ramp demand after calculation hid all metrics
  and report downloads until recalculation.
- Diverge desktop English/Metric: first inputs remained visible, freeway and
  off-ramp grouping was clear, LD appeared in the worksheet and diagram
  summary, derived continuing demand was read-only, and stable result exports
  were available by AppTest.
- Diverge English/Metric 768px: grouped controls, diagram, Calculate placement,
  project save, and validation sections rendered without horizontal overflow.
- Diverge Thai/Metric and Thai/Imperial: approved title, section labels, action
  labels, result labels, project controls, and export controls localized; HCM,
  LOS, FFS, PHF, LD, and units remained language-neutral.
- Diverge warning-only state: maximum desirable influence-flow exceedance
  rendered as a non-capacity valid result with LOS/density/speed still visible
  and report exports available.
- Diverge capacity-failure state: LOS F, v/c, governing reason, and Not
  predicted speed/density rendered as a calculated state with current exports
  available.
- Diverge invalid continuing demand: off-ramp demand greater than upstream
  demand rendered as invalid input with no metrics, no traceback, and localized
  relationship guidance.
- Diverge stale state: changing off-ramp demand after calculation hid all
  metrics and report downloads until recalculation.
- Browser screenshots for Diverge were captured with system Chrome at
  `output/playwright/`; no horizontal overflow was detected at 1280px or 768px.
- Two-Lane Segment desktop English/Metric, 1280px wide: default worksheet
  loaded, calculated, displayed LOS D, follower density, speed, percent
  followers, demand flow, capacity, FFS, project save, and report export
  controls without horizontal overflow.
- Two-Lane Segment English/Metric, 768px wide: setup, geometry, demand,
  advanced controls, schematic, result hierarchy, project output, and export
  sections rendered without horizontal document overflow.
- Two-Lane Segment Thai/Metric and Thai/Imperial: title, setup, action labels,
  result labels, project controls, and export controls localized; HCM, LOS,
  FFS, PHF, units, method identifiers, and serialized keys remained
  language-neutral.
- Two-Lane Segment stale state: changing analysis-direction demand after
  calculation changed the workflow status to recalculate required, hid current
  metrics, and withheld report export controls until recalculation.
- Two-Lane Segment advanced branches: passing-lane and horizontal-curve controls
  rendered in the live browser with localized schematic context; AppTest covers
  grade, generated-curve, and passing-lane calculation/render paths.
- Browser screenshots for Two-Lane Segment were captured at
  `output/playwright/`, including English/Metric desktop and 768px, Thai/Metric
  desktop, Thai/Imperial desktop and 768px, and stale states.
- Final Two-Lane Facility gate used a temporary Streamlit server at
  `http://localhost:8517` with system Chrome/Playwright. Confirmation
  screenshots were written only under `output/playwright/phase15_2_facility_gate/`
  and remain temporary/untracked.
- Two-Lane Facility current result/export controls, English desktop 1280px:
  calculated current result showed Facility summary, segment-result table, CSV,
  Markdown, Excel, and report JSON downloads; no horizontal document overflow,
  no traceback, and exports appeared only for the current result.
- Two-Lane Facility stale after direct segment-table edit, English desktop
  1280px, Thai desktop 1280px, and English 768px: editing a rendered data-editor
  segment-name cell after calculation changed the workflow to stale/recalculate,
  hid Facility metrics and the segment-result table, removed report downloads,
  and kept the table usable with no horizontal document overflow. Thai stale
  warning text was readable and localized.
- Two-Lane Facility invalid row, English desktop 1280px, Thai desktop 1280px,
  and English 768px: direct data-editor edit duplicated `segment_id`, producing
  invalid input with affected row/field detail (`Segment 1: duplicate
  segment_id.` / Thai localized equivalent), no Facility metrics, no
  segment-result table, no report downloads, no traceback, and no horizontal
  document overflow.
- Two-Lane Facility unsupported segment combination, English desktop 1280px and
  Thai desktop 1280px: direct data-editor edit changed the Passing Lane row's
  `passing_lane_role` to `none`, producing a visually distinct unsupported-scope
  warning with affected segment detail, no Facility metrics, no segment-result
  table, no report downloads, no traceback, readable Thai text, and no
  horizontal document overflow.
- Two-Lane Facility valid project load, English desktop 1280px and Thai desktop
  1280px: loading a current-result project restored the segment table, current
  Facility result, localized project-loaded message, and report-export section.
  The restored result stayed current and no traceback or raw Python exception
  appeared.
- Two-Lane Facility wrong project type and malformed project load, Thai desktop
  1280px: both project-load errors rendered localized error panels, retained the
  editable table/pre-run state without fabricated current results, and showed no
  traceback or raw Python exception.
- Issue found and corrected during the final visual gate: switching an inherited
  browser session into Thai could leave `facility_unit_label` as a localized
  label, causing `unit_system must be metric or imperial` instead of the
  Facility table. The route now canonicalizes the segmented-control state before
  loading templates; an AppTest regression covers the Thai locale-switch case.

## Supported Workflows cleanup

- Migrated the public Supported Workflows information page from hardcoded
  English section content to semantic English/Thai catalog keys.
- Replaced the visible workflow selector values with stable internal workflow
  identifiers while preserving the legacy English `selected_calculator_mode`
  session value for compatibility.
- Added localized grouped navigation coverage that opens every public workflow
  in English and Thai, including the Supported Workflows route.
- Preserved the internal validation examples route as query-parameter-only; it
  remains absent from public navigation.
- Issue found and corrected during the localized route sweep: the Weaving preset
  selectbox could carry an English formatted label into Thai-rendered options in
  AppTest/browser-like state transitions. The control now normalizes invalid
  preset state to the canonical `blank_custom` ID and supplies an explicit
  option index.

## Hardcoded-string review

- Multilane route strings in `streamlit_app.py` now route through the i18n catalog
  except for technical identifiers, method IDs, file names, units, and raw audit
  or engine provenance values.
- Basic Freeway route strings in `streamlit_app.py` now route through the i18n
  catalog except for technical identifiers, method IDs, file names, units, and
  raw audit or engine provenance values.
- Merge and Diverge route strings in `streamlit_app.py` now route through the i18n catalog
  except for technical identifiers, method IDs, file names, units, and raw audit
  or engine provenance values.
- Two-Lane Segment route strings in `streamlit_app.py` now route through the
  i18n catalog except for technical identifiers, method IDs, file names, units,
  and raw audit or engine provenance values.
- Two-Lane Facility route strings in `streamlit_app.py` now route through the
  i18n catalog except for technical identifiers, method IDs, file names, units,
  canonical data-editor cell values, and raw audit or engine provenance values.
- Phase 15.2 visible routes now cover Two-Lane Segment, Two-Lane Facility,
  Multilane, Basic Freeway, Weaving, Merge, Diverge, and Supported Workflows.
  Clean wheel-installed qualification and the exhaustive app-wide browser matrix
  remain Phase 15.3.
- Existing report payload field names and engineering provenance strings remain
  canonical for export/project compatibility.
- Supported Workflows page strings now route through the i18n catalog except
  for HCM references, file-format names, method versions, and intentionally
  language-neutral technical terms.

## Compatibility

No numerical engine, public engine API, project schema, normalized engine input
contract, export field contract, qualified preset, or diagram calculation
semantic was changed. The Two-Lane Segment migration continues to use the
existing Chapter 15 adapter, result fields, audit record, curve-generation
helpers, and schematic asset path. The Multilane and Basic Freeway displays
continue to use `display["capacity"]`; Merge and Diverge continue to use the
existing ramp-influence display adapter and SVG asset paths.

The Two-Lane Facility migration continues to use project type
`manual_two_lane_facility_v1`, method identifier
`hcm7_two_lane_highway_facility`, method version
`phase_5_product_integration`, the existing normalized segment list,
fingerprint contract, Chapter 26 Example 3/4 templates, and report/export
contracts.

## Verification

- Focused Multilane/AppTest regression suite passes.
- Basic Freeway AppTests cover stable English, Thai result, measured FFS,
  estimated FFS/ramp density, stale/recalculate, capacity failure, invalid input,
  unsupported scope, project load/malformed project, and navigation isolation.
- Merge AppTests cover stable English, Thai result, maximum-desirable warning
  only, capacity failure, stale/recalculate, measured/estimated FFS, invalid
  input, current/HCM 7.1/malformed project load, and navigation isolation.
- Diverge AppTests cover stable English, Thai result, maximum-desirable warning
  only, capacity failure, invalid continuing demand, stale/recalculate,
  measured/estimated FFS, current/HCM 7.1/adjacent/wrong-type/malformed project
  load, and navigation isolation.
- Two-Lane Segment AppTests cover stable English result and exports, Thai
  localized result surfaces, stale result/export blocking, grade/curve/passing
  branch rendering, invalid and unsupported states with no metrics, current
  project load, wrong-type and malformed project load, and navigation isolation.
- Two-Lane Facility AppTests cover stable English result and exports, Thai
  localized result surfaces, table-edit stale/export blocking/recalculate,
  template-change reset/recalculate, invalid row with row/field detail,
  unsupported combination with no metrics, current/wrong-type/malformed project
  load, and navigation isolation.
- Merge/Diverge adapter/export tests protect warning-only export status,
  null-preserving capacity-failure exports, Metric/Imperial equivalent
  fingerprints, project stale-result rejection, HCM 7.1/unsupported geometry
  rejection, and diagram asset packaging.
- Focused Two-Lane Segment, Basic Freeway, Multilane, Merge, Diverge,
  localization, workflow-state, project I/O, reporting, and diagram checks pass.
  The full test-suite result is recorded in the final task handoff for this work
  item.
