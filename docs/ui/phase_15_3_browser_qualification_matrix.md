# Phase 15.3 Browser Qualification Matrix

Status: incomplete, with partial real-browser evidence added on 2026-07-20.

This matrix records Phase 15.3 installed-package route, AppTest, and partial
real-browser evidence collected from the isolated worktree. Browser automation
used Python Playwright with installed system Chrome; Node/npm/npx were not used.
The matrix is still incomplete because project upload/download qualification,
full export content qualification, launcher execution, and several explicit
state probes are not complete.

Evidence environment:

- Worktree: `C:\Users\kittipat_t\Documents\hcm-calculator-phase-15-3`
- Branch: `codex/phase-15-3-release-qualification`
- Baseline SHA: `f16485329b451cf69cc61f9b59adb07ae3ed80d9`
- Installed wheel environment:
  `C:\Users\kittipat_t\AppData\Local\Temp\hcmcalc-phase15-3-wheel-browser`
- Installed app path:
  `C:\Users\kittipat_t\AppData\Local\Temp\hcmcalc-phase15-3-wheel-browser\Lib\site-packages\hcmcalc\ui\streamlit_app.py`
- Temporary evidence location:
  `output/playwright/phase15_3_release_qualification/` with screenshots,
  downloads, and JSONL evidence kept uncommitted.
- Browser: `C:\Program Files\Google\Chrome\Application\chrome.exe`,
  ProductVersion `150.0.7871.125`.
- Evidence log: `output/playwright/phase15_3_release_qualification/browser_evidence.jsonl`.

Real-browser evidence summary:

- Rows recorded: 44.
- Passing rows: 37.
- Failed/incomplete rows: 7.
- 1280 px rows: 36.
- 768 px rows: 8.
- English rows: 36.
- Thai rows: 8.
- Imperial calculator rows: 7.
- Horizontal overflow findings: 0 recorded rows.
- Console status: 43 clean, 1 severe during an export sequence.
- Browser downloads captured and inspected: Facility CSV, Excel, Markdown, and
  report JSON only.

| Workflow | Locale | Unit system | Viewport | Preset/case | Result state | Project operation | Export operation | Diagram/table status | Overflow status | Console status | Result | Evidence reference | Notes |
|---|---|---:|---:|---|---|---|---|---|---|---|---|---|---|
| Two-Lane Segment | EN | Metric | 1280 px real browser | Default | Stable | AppTest current/wrong/malformed | Export attempted, download not captured | Packaged schematic visible | Pass | Clean | Pass | `manual_single_segment_en_metric_1280px_stable.png` | Direct calculation row passed |
| Two-Lane Segment | EN | Metric | AppTest only | Default edited | Stale | N/A | Report exports hidden | Packaged schematic resolver passes | Not browser-reviewed | Not browser-reviewed | AppTest pass | `test_two_lane_segment_stale_state_hides_metrics_and_blocks_report_exports` | Real browser pending |
| Two-Lane Segment | TH | Metric | AppTest only | Project load | Current/wrong/malformed | Current restore and rejection | N/A | Packaged schematic resolver passes | Not browser-reviewed | Not browser-reviewed | AppTest pass | `test_two_lane_segment_project_load_current_wrong_type_and_malformed_smoke` | Real browser pending |
| Two-Lane Facility | EN | Metric | 1280 px real browser | Facility template | Stable | Current/wrong/malformed in AppTest | CSV/XLSX/MD/report JSON downloaded and inspected | Segment table renders | Pass | Clean | Pass | `manual_facility_en_metric_1280px_stable.png`; downloads directory | Facility is the only fully captured browser export set |
| Two-Lane Facility | EN | AppTest only | Table edit | Stale/invalid | N/A | Report exports hidden | Facility table editable | Not browser-reviewed | Not browser-reviewed | AppTest pass | `test_two_lane_facility_table_edit_stale_hides_metrics_and_blocks_exports` | Real browser pending |
| Multilane Segment | EN | Metric/Imperial | 1280 px real browser | Example 4 | Stable and Imperial | Project restore/malformed in AppTest | Export attempted, download not captured | Capacity display uses `capacity` in AppTest | Pass | Clean | Pass for route/calculation; export incomplete | `manual_multilane_en_metric_1280px_stable.png` | Browser export failed to capture |
| Basic Freeway Segment | EN | Metric/Imperial | 1280 px real browser | BF-CH26-001 | Stable and Imperial | Project restore/malformed in AppTest | Export attempted, download not captured | Ramp-density text visible in AppTest | Pass | Clean | Pass for route/calculation; export incomplete | `manual_basic_freeway_en_metric_1280px_stable.png` | Browser export failed to capture |
| Weaving Segment | EN | Metric/Imperial | 1280 px real browser | WVG default | Stable and Imperial | Project tests pass in suite | Export attempted, download not captured | Packaged diagrams visible | Pass | Clean | Pass for EN; TH row failed to find calculate button | `manual_weaving_en_metric_1280px_stable.png` | Needs TH/browser state recheck |
| Merge Segment | EN/TH | Metric/Imperial | 1280 px real browser | Chapter 28 preset | Stable and Imperial | Current/HCM 7.1/malformed in AppTest | Export attempted, download not captured | Packaged SVG visible | Pass | Clean | Pass for route/calculation; export incomplete | `manual_merge_en_metric_1280px_stable.png` | Warning/capacity states still AppTest-only |
| Diverge Segment | EN/TH | Metric/Imperial | 1280 px real browser | Chapter 28 preset | Stable and Imperial | Current/wrong/HCM 7.1/adjacent/malformed in AppTest | Export attempted, download not captured | Packaged SVG visible | Pass | One severe export-row console classification | Pass for route/calculation; export/console incomplete | `manual_diverge_en_metric_1280px_stable.png` | Needs console follow-up |
| Supported Workflows | EN/TH | N/A | 1280 px and 768 px real browser | Reference page | Stable reference | N/A | N/A | Grouped sections render | Pass | Clean | Pass | `supported_workflows_en_n_a_1280px_stable.png`; `supported_workflows_th_n_a_1280px_stable.png` | Scope wording visually sampled |

Required unqualified browser cells and states:

- Direct project upload/download qualification from the installed browser app.
- Direct successful browser report exports for every calculator.
- Direct content inspection for every calculator export set, not only Facility.
- Explicit stale, invalid, unsupported, warning-only, capacity-failure, and
  handoff state probes in the real browser.
- Thai Weaving calculation row recheck.
- Diverge export console follow-up.
- Launcher execution qualification.
- Focused real-browser accessibility review.
- Complete screenshot/evidence log coverage for every required release gate
  under `output/playwright/phase15_3_release_qualification/`.
