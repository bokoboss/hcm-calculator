# Issue #184 — Thailand/LHT worksheet release qualification

Implementation candidate, **not independently accepted or merged**. Starting
remote main: `089af22f9b8e1dfd3fb5c35153574f26ebbaae26` (accepted PR #183).
Branch: `codex/ch18-th-lht-production-ui-issue184`. Worktree:
`D:/R&D/hcm-calculator/.worktrees/issue184`.

## Scope and protected contracts

LHT is the eighth delivered React workflow in the existing AnalysisWorkflow
shell. The exact handshake is
`hcm7_ch18_bounded_signalized_15min_th_lht_semantic_v1`; the method ID and route
are `urban_street_segment_th_lht` and `/analysis/urban_street_segment_th_lht`.
RHT has no frontend registry entry and remains disabled/reference-only;
its direct/restored route containment and backend regressions remain tested.

Python remains the calculation authority. Only LHT form grouping,
conditional metadata, and its obsolete reference-only scope key change in
the application layer. Backend validation code is unchanged. No engine,
equation, coefficient, identity, normalization, Project `2.0` schema,
fingerprint or export/comparison implementation changes are included.

The accepted-main and working-tree Git blob hashes of
`src/hcmcalc/urban_street_ch18.py` both equal
`d9d7b40dc6478832e6faf3700e485ca0aec6eb2e`.
The accepted-main metric starter snapshot is preserved in
[`urban_street_lht_application_baseline.json`](../../tests/fixtures/urban_street_lht_application_baseline.json).
The regression compares displayed and normalized inputs, serialized result,
both fingerprints and all accepted method identities. Metric fixture LOS is
**C**, travel speed `38.090654968232464 km/h`, running speed
`58.88324211886915 km/h`, through v/c `0.5238095238095238`, total travel time
`51.85271824932475 s`, and running time `33.54271824932475 s`.

Calculation fingerprint:
`3ad2c549d5697e0a3ed35e4f21e1b387f1e58772ae630f15d33de5cc94e4d36c`.
Input snapshot fingerprint:
`4923e8d8d74cd8efcaa0a4169f187917bdcba662de811539fa50befde68c4379`.

## Genuine RED / GREEN

Tests were written before the corresponding implementation. Corrected control
tests were also rerun against accepted-main production files and metadata;
the harness restored all current implementation bytes in `finally`.

| Gate | Actual RED evidence | GREEN evidence |
|---|---|---|
| Number list | No accessible Access-point delays group; scalar renderer cannot edit an ordered list | Numeric ordered JSON values, fractional values, s/veh item units, keyboard add/remove, explicit blank null and backend error recovery |
| Boolean | Actual Demand is balanced group has no No radio | Yes/No EN/TH, real true/false payloads, no preselection in blank starter, backend prerequisite/spillback rejection |
| Field option localization | Actual calibration field lacks the localized reference option | Field-specific calibration labels; signalized labels; legacy option lookup regression |
| Delivery/routing | Missing LHT module, direct/restored worksheet and Handbook action/spec | Exact handshake, actionable eight, direct/history and restored scenario worksheet, RHT containment |
| Metrics | New metric labels returned raw localization keys | Every Chapter 18 label EN/TH; LOS hero and fixed five-metric order |
| Form metadata | 1 failed / 27 passed: old two groups fail expected six groups | Six groups, conditional source metadata; accepted snapshot unchanged |
| CSV | 1 failed / 8 filtered: no Export CSV menuitem | All four LHT exports, legacy export menu preserved |
| Packaged SPA | 1 failed / 3 passed: old bundle lacks LHT contract | Current bundled worksheet/Handbook and byte-exact dist/static equality |

The focused accepted-main control RED run was **3 failed / 6 filtered**.
The initial frontend RED run was **11 failed / 40 passed**; two initial
control selectors needed correction, so the focused run above is the
authoritative control evidence. Final full frontend GREEN is **54 passed**.
Raw local logs are under `.tmp/evidence/` (ignored, not shipped); concise
extracted results and final qualification logs are in `issue184-evidence/`.

## Product and engineering journeys

Six production groups: Roadway / segment geometry; Traffic and access;
Analysis conditions; Downstream through performance; External source /
provenance; Calibration. The last two use advanced disclosures. Required
errors reveal their sections; error-summary links open and focus the field.
Calibration source is visible for user local calibration. Status switches
retain the source and speed adjustment; reference use with nonzero S_calib
still fails, and local use still requires nonblank text, as before.

The list is a reusable numeric control with explicit empty-state behavior;
no HCM logic or engineering default is implemented in TypeScript. All
readiness booleans start unselected in blank custom. Backend errors remain
authoritative, including invalid list items, prerequisites, spillback,
direction/movement/period mismatch, provenance, and calibration.

Chromium covers the accepted starter (LOS C), full manual blank completion,
validation recovery, current → stale → recalculate, Project save (schema
2.0), exact-payload restore without calculation, edit/duplicate/save and
scenario comparison. JSON, Markdown, CSV and XLSX download journeys assert
`recalculated: false`. Existing backend no-rerun export/comparison tests
remain unchanged. Locale switching retains values and current results.

The EN/TH Handbook has six preparation items, six glossary items, seven
steps, five outputs, five interpretation items and six limits. It explains
direction-relative physical-left kerbside roles, v_m versus v_th, qualified
external final downstream delay consumed once, HCM-reference coefficients,
calibration provenance, unsupported spillback/control types, deferred
Chapter 18/30 methodology, and the fixture's semantic-verification status.
It does not claim a published Thai example or empirical Thai calibration.

Keyboard/browser checks cover list focus, radio choices, disclosure errors,
error-summary focus and Enter activation, and exports. Semantic fieldsets,
labels, units and linked error descriptions are present. This is bounded
accessibility evidence; no claim of exhaustive screen-reader certification.
Both locales pass viewport/form-control containment at 1920, 1366, 1024
and 390 px. The existing section-navigation strip remains scrollable.

| Width | English | Thai |
|---|---|---|
| 1920 | [Worksheet](issue184-evidence/lht-en-1920.png) | [Worksheet](issue184-evidence/lht-th-1920.png) |
| 1366 | [Worksheet](issue184-evidence/lht-en-1366.png) | [Worksheet](issue184-evidence/lht-th-1366.png) |
| 1024 | [Worksheet](issue184-evidence/lht-en-1024.png) | [Worksheet](issue184-evidence/lht-th-1024.png) |
| 390 | [Worksheet](issue184-evidence/lht-en-390.png) | [Worksheet](issue184-evidence/lht-th-390.png) |

Screenshots intentionally show retained stale results following the list
edit/remove journey; recalculation is verified separately. Handbook routes
and overflow are checked at every listed locale/width.

## Final local qualification — 2026-10-05

| Check | Result |
|---|---|
| Full Python 3.12 suite | **1369 passed / 0 skipped / 0 failed / 1369 total**, 282.83 s |
| compileall src tests | Pass |
| OpenAPI snapshot | Matches FastAPI; regenerated TypeScript API types have no diff |
| Frontend typecheck | Pass |
| Full Vitest | **54 passed**, 9 files |
| Production SPA build | Pass; existing 500 kB chunk advisory remains nonblocking |
| Full Chromium source/release-like server | **53 passed / 0 skipped / 0 failed**, serial workers |
| Installed-wheel packaged Chromium LHT journeys | **15 passed / 0 skipped / 0 failed** |
| Packaged/static + Vercel adapter tests | **9 passed / 0 skipped / 0 failed** |
| SPA freshness | Established `_sync_frontend_dist` helper; dist/static byte equality; current hashes referenced; old generated assets removed |
| Wheel | Build/install succeeds; import resolves isolated venv site-packages; default server has no explicit static-dir and serves packaged SPA |
| Engine/seven-workflow/RHT regressions | Pass in full Python and Chromium suites; engine source unchanged |
| Actual diff | Reviewed; engine absent, no frontend HCM formulas, no unrelated screenshot updates |

Commands use the repository's pinned pnpm 11.19.0, invoked via Node to avoid
Windows `.cmd` parsing of the `R&D` path. Final Python tests use worktree-local
TEMP/TMP and `--basetemp`; process/temp restrictions in sandbox-only trial
runs are not counted as successful qualification. Two screenshot write
errors in an earlier parallel browser run recovered serially; the final
entire suite passed. A disclosure mounting regression affecting Weaving
was found by full browser tests and fixed before final qualification.

The SPA is generated normally, never hand-edited. Current JS is
`index-CC7S3KTf.js` and CSS is `index-BGjgfhsd.css`.
The current R1 workflow has Python, application/API, frontend and browser
jobs; local checks reproduce those gates and additionally verify the wheel.

## External closeout gate

The implementation commit must reach a stable head with current-head R1
qualification and Vercel green before requesting exactly one code review
and one security review. External results and the exact head/PR links are
recorded in the PR discussion and final 64-item handoff report, without
altering the reviewed head merely to update this record.

No known implementation BLOCKER or REQUIRED finding remains from local
qualification. Automated reviews may add findings; tooling failure without
a concrete security finding must be reported honestly, without code churn.
Fresh-context UX/engineering acceptance is still required. Issue #184 and
parent #172 stay open until authorized acceptance/merge. Do not merge or
self-approve this candidate.
