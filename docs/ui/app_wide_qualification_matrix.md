# App-wide qualification matrix (Phase 15.1)

Legend: **C** covered, **P** partially covered, **M** missing, **NA** not applicable. Existing evidence is primarily unit/AppTest; current AppTest has real Two-Lane Segment, Two-Lane Facility, Multilane, Basic Freeway, Weaving, Merge, and Diverge render/stale/recalculate/state paths. HTTP smoke passed. Browser document rendering is recorded where direct evidence exists; full app-wide browser/wheel qualification remains Phase 15.3.

| Workflow | Open/preset/valid/result/stale/recalc | Capacity/warning/stopping/unsupported | Project/CSV/XLSX/MD/report JSON/calc JSON | EN/TH/Metric/Imperial | Navigation/isolation/HTTP/wheel/browser |
|---|---|---|---|---|---|
| Two-Lane Segment | C/P/C/C/C/C | NA/C/NA/C | C/C/C/C/C/P | C/C/C/C | C/C/C/M/C |
| Two-Lane Facility | C/C/C/C/C/C | NA/C/NA/C | C/C/C/C/C/P | C/C/C/C | C/C/C/M/C |
| Multilane | C/P/C/C/C/C | C/P/NA/P | P/P/P/P/P/P | P/P/P/P | P/P/C/M/M |
| Basic Freeway | C/C/C/C/C/C | C/P/NA/C | C/C/C/C/C/P | C/C/C/C | C/C/C/M/C |
| Weaving | C/C/C/C/C/C | C/C/C/C | C/C/C/C/C/P | C/C/C/P | C/P/C/M/C |
| Merge | C/C/C/C/C/C | C/C/NA/C | C/C/C/C/C/P | C/C/C/C | C/C/C/M/C |
| Diverge | C/C/C/C/C/C | C/C/NA/C | C/C/C/C/C/P | C/C/C/C | C/C/C/M/C |
| Supported Workflows | C/NA/NA/NA/NA/NA | NA | NA | C/C/NA/NA | C/NA/C/M/M |

## Phase 15.3 acceptance criteria

For every calculator, add one `AppTest` that opens the route, applies a qualified preset, calculates, asserts the hero and principal metrics, changes a calculation input, asserts stale/export blocking, recalculates, and asserts no exception. Add method fixtures for capacity/LOS F, warning, weaving handoff, unsupported scope, invalid input, project roundtrip, every declared download, English/Thai, Metric/Imperial round trip, and workflow navigation/state isolation. Add browser smoke for the same route list at desktop and 768 px width, HTTP smoke, editable-install and wheel-installed Streamlit smoke. A release passes only with zero current-result leakage, zero English fallback in Thai routes, and explicit NA justification per matrix cell.
