# Phase 15.3 Browser Qualification Matrix

Status: incomplete.

This matrix records the Phase 15.3 installed-package route and AppTest evidence
collected from the isolated worktree. The required real-browser Playwright CLI
matrix could not be completed in this environment because Node/npm/npx were not
installed. No row below is claimed as a real-browser pass.

Evidence environment:

- Worktree: `C:\Users\kittipat_t\Documents\hcm-calculator-phase-15-3`
- Branch: `codex/phase-15-3-release-qualification`
- Baseline SHA: `f16485329b451cf69cc61f9b59adb07ae3ed80d9`
- Installed wheel environment:
  `C:\Users\kittipat_t\AppData\Local\Temp\hcmcalc-phase15-3-wheel-current`
- Installed app path:
  `C:\Users\kittipat_t\AppData\Local\Temp\hcmcalc-phase15-3-wheel-current\Lib\site-packages\hcmcalc\ui\streamlit_app.py`
- Temporary evidence location:
  `output/playwright/phase15_3_release_qualification/` reserved, no committed
  screenshots.

| Workflow | Locale | Unit system | Viewport | Preset/case | Result state | Project operation | Export operation | Diagram/table status | Overflow status | Console status | Result | Evidence reference | Notes |
|---|---|---:|---:|---|---|---|---|---|---|---|---|---|---|
| Two-Lane Segment | EN | Metric | AppTest only | Default | Stable | AppTest current/wrong/malformed | CSV/XLSX/MD/report JSON AppTest | Packaged schematic resolver passes | Not browser-reviewed | Not browser-reviewed | AppTest pass | `tests/unit/test_streamlit_app.py`, `test_package_assets.py` | Real browser pending |
| Two-Lane Segment | EN | Metric | AppTest only | Default edited | Stale | N/A | Report exports hidden | Packaged schematic resolver passes | Not browser-reviewed | Not browser-reviewed | AppTest pass | `test_two_lane_segment_stale_state_hides_metrics_and_blocks_report_exports` | Real browser pending |
| Two-Lane Segment | TH | Metric | AppTest only | Project load | Current/wrong/malformed | Current restore and rejection | N/A | Packaged schematic resolver passes | Not browser-reviewed | Not browser-reviewed | AppTest pass | `test_two_lane_segment_project_load_current_wrong_type_and_malformed_smoke` | Real browser pending |
| Two-Lane Facility | EN | Imperial/Metric | AppTest only | Facility templates | Stable | Current/wrong/malformed | CSV/XLSX/MD/report JSON AppTest | Segment table renders | Not browser-reviewed | Not browser-reviewed | AppTest pass | `tests/unit/test_streamlit_app.py` | Real browser pending |
| Two-Lane Facility | EN | AppTest only | Table edit | Stale/invalid | N/A | Report exports hidden | Facility table editable | Not browser-reviewed | Not browser-reviewed | AppTest pass | `test_two_lane_facility_table_edit_stale_hides_metrics_and_blocks_exports` | Real browser pending |
| Multilane Segment | EN | Metric/Imperial | AppTest only | Example 4 | Stable/stale/capacity failure | Project restore/malformed | CSV/XLSX/MD/report JSON AppTest | Capacity display uses `capacity` | Not browser-reviewed | Not browser-reviewed | AppTest pass | `test_multilane_*` | Real browser pending |
| Basic Freeway Segment | EN | Metric/Imperial | AppTest only | BF-CH26-001 | Stable/stale/capacity failure | Project restore/malformed | CSV/XLSX/MD/report JSON AppTest | Ramp-density explanation present | Not browser-reviewed | Not browser-reviewed | AppTest pass | `test_freeway_*` | Real browser pending |
| Weaving Segment | EN | Metric/Imperial | Installed AppTest | WVG presets | Route opens after packaged-fixture fix | Project tests pass in suite | Export tests pass in suite | Packaged diagrams pass | Not browser-reviewed | Not browser-reviewed | Installed route pass after fix | Installed route smoke, `test_weaving_diagrams.py` | Real browser pending |
| Merge Segment | EN | Metric/Imperial | Installed AppTest | Chapter 28 presets | Stable/warning/capacity/stale/invalid | Current/HCM 7.1/malformed | CSV/XLSX/MD/report JSON AppTest | Packaged SVG pass | Not browser-reviewed | Not browser-reviewed | Installed route pass after fix | `test_merge_*`, installed route smoke | Real browser pending |
| Diverge Segment | EN | Metric/Imperial | Installed AppTest | Chapter 28 presets | Stable/warning/capacity/stale/invalid | Current/wrong/HCM 7.1/adjacent/malformed | CSV/XLSX/MD/report JSON AppTest | Packaged SVG pass | Not browser-reviewed | Not browser-reviewed | Installed route pass after fix | `test_diverge_*`, installed route smoke | Real browser pending |
| Supported Workflows | EN/TH | N/A | AppTest only | Reference page | Stable reference | N/A | N/A | Grouped sections render | Not browser-reviewed | Not browser-reviewed | AppTest pass | `test_supported_workflows_page_renders_english_and_thai` | Real browser pending |

Required unqualified browser cells:

- Direct desktop approximately 1280 px review for all workflows/locales/unit
  systems.
- Direct 768 px review for all workflows/locales/unit systems.
- Browser console review.
- Horizontal overflow review.
- Screenshot/evidence log production under
  `output/playwright/phase15_3_release_qualification/`.
