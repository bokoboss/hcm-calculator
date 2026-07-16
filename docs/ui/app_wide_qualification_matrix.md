# App-wide qualification matrix (Phase 15.1)

Legend: **C** covered, **P** partially covered, **M** missing, **NA** not applicable. Existing evidence is primarily unit/AppTest; current AppTest has a real Multilane render/stale/recalculate/capacity path and Weaving diagram route coverage. HTTP smoke passed. Browser document rendering did not become inspectable in the in-app browser and is therefore M, not inferred as passed.

| Workflow | Open/preset/valid/result/stale/recalc | Capacity/warning/stopping/unsupported | Project/CSV/XLSX/MD/report JSON/calc JSON | EN/TH/Metric/Imperial | Navigation/isolation/HTTP/wheel/browser |
|---|---|---|---|---|---|
| Two-Lane Segment | P/P/P/P/P/P | P/P/NA/P | P/P/P/P/P/P | P/P/P/P | P/P/C/M/M |
| Two-Lane Facility | P/P/P/P/P/P | NA/P/NA/P | P/P/P/P/P/P | P/P/P/P | P/P/C/M/M |
| Multilane | C/P/C/C/C/C | C/P/NA/P | P/P/P/P/P/P | P/P/P/P | P/P/C/M/M |
| Basic Freeway | P/P/P/P/P/P | P/P/NA/P | P/P/P/P/P/P | P/P/P/P | P/P/C/M/M |
| Weaving | C/P/P/P/P/P | P/P/P/C | P/P/P/P/P/P | P/P/P/P | P/P/C/M/M |
| Merge | P/P/P/P/P/P | P/P/NA/P | P/P/P/P/P/P | P/P/P/P | P/P/C/M/M |
| Diverge | P/P/P/P/P/P | P/P/NA/P | P/P/P/P/P/P | P/P/P/P | P/P/C/M/M |
| Supported Workflows | P/NA/NA/NA/NA/NA | NA | NA | P/P/NA/NA | P/NA/C/M/M |

## Phase 15.3 acceptance criteria

For every calculator, add one `AppTest` that opens the route, applies a qualified preset, calculates, asserts the hero and principal metrics, changes a calculation input, asserts stale/export blocking, recalculates, and asserts no exception. Add method fixtures for capacity/LOS F, warning, weaving handoff, unsupported scope, invalid input, project roundtrip, every declared download, English/Thai, Metric/Imperial round trip, and workflow navigation/state isolation. Add browser smoke for the same route list at desktop and 768 px width, HTTP smoke, editable-install and wheel-installed Streamlit smoke. A release passes only with zero current-result leakage, zero English fallback in Thai routes, and explicit NA justification per matrix cell.
