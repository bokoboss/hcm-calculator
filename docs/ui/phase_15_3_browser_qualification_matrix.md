# Phase 15.3 Browser Qualification Matrix

Status: closed for local release qualification.

Browser automation used Python Playwright with installed system Chrome. Evidence
artifacts are stored under
`output/playwright/phase15_3_release_qualification/` and are intentionally
uncommitted.

Environment:

- Worktree: `C:\Users\kittipat_t\Documents\hcm-calculator-phase-15-3`
- Branch: `codex/phase-15-3-release-qualification`
- Browser: `C:\Program Files\Google\Chrome\Application\chrome.exe`
- Browser version: `150.0.7871.125`
- Final installed wheel environment:
  `C:\Users\kittipat_t\AppData\Local\Temp\hcmcalc-phase15-3-final-wheel-0-8-0`
- Final wheel smoke:
  `output/playwright/phase15_3_release_qualification/final_wheel/final_wheel_smoke_pass.jsonl`

## Gate Summary

| Gate | Result | Evidence |
|---|---|---|
| Installed wheel route-open smoke | Pass | All eight visible modes opened from installed `site-packages`; final route screenshots under `final_wheel/screenshots/`. |
| Project upload/load/error | Pass | All seven calculators covered valid current-result, stale-result, wrong-type, and malformed JSON projects in continuation evidence. |
| Current-result report exports | Pass | All seven calculators had report downloads inspected; Weaving was recaptured on 2026-07-21 from the installed wheel. |
| Stale export blocking | Pass with Facility automation limitation | Real-browser pass for Two-Lane Segment, Multilane, Basic Freeway, Weaving, Merge, and Diverge; Facility covered by AppTest because the Streamlit data editor is canvas-backed. |
| Thai Weaving | Pass | Two-sided, capacity-failure, and handoff rows passed at 1280 px and 768 px. |
| Diverge export console follow-up | Pass | Three repeated report JSON downloads produced no severe console entries. |
| Launcher checks | Pass | `run_app.bat` and `run_app.ps1` returned HTTP `200`; copied path-with-spaces failure message was documented. |
| Focused accessibility | Pass with Facility limitation | Representative keyboard/focus/overflow/state-text checks passed; Facility cell-level grid semantics remain framework-provided. |
| Final wheel version/startup | Pass | `hcmcalc.__version__ == "0.8.0"`; HTTP `200` on port `8768`. |

## Workflow Matrix

| Workflow | Browser result | Project load/error | Current-result exports | Stale export blocking | Accessibility/overflow | Notes |
|---|---|---|---|---|---|---|
| Two-Lane Segment | Pass | Pass | Pass | Pass | Pass | Packaged schematic visible; current/stale behavior covered by AppTest and browser evidence. |
| Two-Lane Facility | Pass | Pass | Pass | AppTest pass | Pass with limitation | Browser verified grid reachability; data-editor cell mutation is not reliable through Playwright. |
| Multilane Segment | Pass | Pass | Pass | Pass | Pass | Release blocker fixed by removing the stale-hiding Streamlit form boundary. |
| Basic Freeway Segment | Pass | Pass | Pass | Pass | Pass | Estimated FFS and stale export-blocking reruns closed. |
| Weaving Segment | Pass | Pass | Pass | Pass | Pass | Thai two-sided, capacity, and handoff evidence closed; report JSON recaptured. |
| Merge Segment | Pass | Pass | Pass | Pass | Pass | Warning-only and capacity-failure state evidence retained. |
| Diverge Segment | Pass | Pass | Pass | Pass | Pass | Invalid continuing-demand and repeated export console follow-up closed. |
| Supported Workflows | Pass | N/A | N/A | N/A | Pass | English/Thai reference navigation sampled; no calculate action by design. |

## Remaining Limitations

- Browser evidence does not certify WCAG conformance.
- Facility cell-level data-editor semantics and mutation are owned by
  Streamlit's canvas-backed grid implementation; AppTest remains the stable
  regression mechanism for Facility stale-result export blocking.
- Earlier failed harness attempts and partial JSONL files remain in the
  uncommitted evidence folder for traceability; this matrix treats the
  superseding pass files as authoritative.
