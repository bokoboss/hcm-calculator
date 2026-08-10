# Phase 17 — Release Hardening and Engineering Acceptance Execution Plan

Date prepared: 2026-08-10
Planning baseline: `origin/main` at `8dc1481163d9864df71e2091ce23f0963b702e92`
Planning branch: `codex/phase-17-planning`

## Evidence language

This plan uses three evidence labels throughout:

- **Verified fact** — observed in the fetched repository, a local read-only check, or the GitHub API on 2026-08-10.
- **Recommendation** — the execution approach selected from that evidence.
- **Execution assumption** — a condition Luna-Max must revalidate before relying on it because dependencies, GitHub state, or workstation state can change.

## 1. Executive decision

**Recommendation:** execute one cohesive Phase 17 focused on release hardening and real engineering acceptance before beginning any new HCM methodology. The phase should harden the existing seven calculators, make their engineering provenance and exported records easier to audit, turn the current release evidence into repeatable qualification, and obtain recorded engineering UAT. It must not implement Freeway Facility calculations.

The problem is real and load-bearing. Phase 16 explicitly recommends maintenance/distribution hardening, provenance, export ergonomics, accessibility follow-up, performance/regression coverage, and real engineering acceptance before Freeway Facility work. Repository inspection also found stale authoritative documentation, an orphaned GitHub issue, source-folder-only launch assumptions, minimal CI, and no committed browser qualification harness. Doing nothing would leave a locally qualified release whose most extensive browser/wheel evidence is difficult to reproduce.

The smaller alternative—documentation cleanup alone—would resolve roadmap drift but not first-time setup, repeatable package/browser qualification, professional report usability, accessibility follow-up, performance evidence, or real engineering acceptance. A new installer, EXE, MSI, bundled Python runtime, or broad architecture rewrite is not justified by current evidence and is excluded unless a separate approved decision is made later.

**Execution verdict:** proceed with Phase 17 as planned, then issue exactly one Freeway Facility readiness decision. A GO authorizes only a new methodology-audit phase.

## 2. Verified baseline

| Item | Verified fact | Evidence |
| --- | --- | --- |
| Remote baseline | Fresh `git fetch origin --prune` left `origin/main` at `8dc1481163d9864df71e2091ce23f0963b702e92`. | Local Git, 2026-08-10 |
| Version | `pyproject.toml` and `src/hcmcalc/__init__.py` both declare `0.9.0`. | Repository files |
| Phase 16 | Phase 16 is documented as PASS/release ready. Issue #119 is closed as completed and PR #127 merged to the baseline SHA. | `docs/releases/v0_9_phase_16_ux_release_qualification.md`; [#119](https://github.com/bokoboss/hcm-calculator/issues/119); [#127](https://github.com/bokoboss/hcm-calculator/pull/127) |
| Phase 16 recorded qualification | Full suite `1066 passed`; source system-Chrome matrix `126/126`; installed-wheel matrix `22/22`; wheel build and resource inspection passed. | Phase 16 qualification and release notes |
| Current test inventory | `python -m pytest --collect-only -q` collected exactly 1066 tests. A representative package/project/report/freshness run passed `103/103`. The full suite was not rerun for this planning-only task. | Local read-only validation |
| Current CI | The merge-commit `pytest` check completed successfully. The sole committed workflow installs `.[dev]` on Ubuntu/Python 3.12 and runs pytest. Streamlit is in the separate `ui` extra, and AppTest acquisition uses `pytest.importorskip`, so the current CI job does not exercise Streamlit runtime/AppTest paths. | `.github/workflows/test.yml`, `pyproject.toml`, `test_streamlit_app.py`; GitHub check run `31357228826` |
| Workflows | Seven calculators are implemented: Two-Lane Segment, Two-Lane Facility, Multilane Segment, Basic Freeway Segment, Weaving Segment, Merge Segment, and Diverge Segment. Supported Workflows is the eighth visible route. | README, supported-workflow docs, UI navigation, tests |
| Persistence | Project schema is `1.2`, with explicitly supported legacy schemas `1.0` and `1.1`; each workflow has a stable project type and method/input fingerprint checks. | `src/hcmcalc/ui/project_io.py` |
| Reporting | Report schema is `0.1`; current formats are CSV, XLSX, Markdown, and report JSON, in addition to project/calculation JSON surfaces. | `src/hcmcalc/ui/reporting.py` and tests |
| Package resources | UI YAML, PNG, and SVG resources live under `src/hcmcalc/ui` and are resolved with `importlib.resources`; package-resource tests cover the required set. | `runtime_resources.py`, `test_package_assets.py` |
| Browser infrastructure | Phase 16 records strong browser evidence, but no browser/Playwright harness is committed; qualification scripts and evidence were local/ignored. | Tracked file search and Phase 16 records |
| Releases | There are no Git tags and no GitHub Releases. Release history is maintained as versioned Markdown documents. | Local tags and GitHub releases API |
| GitHub workload | No open PRs. The only open issue is #114. | GitHub API, 2026-08-10 |
| Planning isolation | The planning worktree is clean and based on `origin/main`. The original checkout remains on local `main` at `1729cfda...` with pre-existing edits to `AGENTS.md` and two localization docs plus untracked `.agent/` and `mockups/`. | Local Git status |

**Execution assumption:** `origin/main`, open issue/PR state, dependency resolution, and CI status remain unchanged. Luna-Max must fetch and recheck all four at execution start. If new commits merely add compatible maintenance changes, rebase the evidence and continue. If they materially invalidate scope or contracts, use the stop condition in section 16.

## 3. Repository and GitHub findings

### Repository and roadmap

- **Verified fact:** `README.md` accurately names the seven calculators and the single-page workflow, but still calls v0.6 the current maintenance release and describes localization as “Version 0.5.”
- **Verified fact:** `docs/methodology/supported_methods_matrix.md` calls itself the authoritative matrix for v0.6 even though it contains v0.7 methods and the package is v0.9.0.
- **Verified fact:** `docs/roadmap.md` still lists ramp influence, Merge/Diverge, and Weaving as future methodology candidates although those isolated workflows are implemented and qualified.
- **Verified fact:** `docs/ARCHITECTURE.md` still describes placeholders and a future method layout; actual code contains separate Freeway, Multilane, Weaving, ramp-influence, Two-Lane, UI, persistence, reporting, localization, and resource boundaries.
- **Verified fact:** the header of `docs/ux/phase_16_implementation_plan.md` retains several “pending” PR/CI/merge statuses even though the work is merged and Phase 16 is closed.
- **Recommendation:** correct these documents in Workstream A and add a current release/qualification index. Historical release records should remain historical; do not rewrite their contemporaneous baselines or results.

### Runtime and distribution

- **Verified fact:** `setup_app.bat`/`.ps1` require the Windows `py` launcher and exact Python 3.12, create `.venv`, upgrade pip, and install an editable `.[dev,ui]` environment. `run_app.bat`/`.ps1` never install but launch Streamlit from `src/hcmcalc/ui/streamlit_app.py`.
- **Verified fact:** `pyproject.toml` says Python `>=3.12`, while the supported launcher, README, and CI qualify 3.12 only. Dependencies have lower bounds and no lock/constraints file.
- **Verified fact:** the wheel is qualified from outside the source checkout, but the project has no installed console/UI entry point; normal launch is explicitly a source-folder workflow.
- **Verified fact:** Phase 16 encountered an unrelated user-site editable install that shadowed source imports. Qualification worked around it with explicit source isolation and a clean wheel environment.
- **Recommendation:** define the supported distribution contract as “Windows source-folder local app on qualified Python 3.12” unless user evidence justifies something broader. Harden that contract and retain installed-wheel qualification as an independent packaging gate. Do not infer a need for EXE/MSI/portable Python.

### Architecture and contracts

- **Verified fact:** engines are independent of Streamlit. UI adapters normalize display inputs into engine-native values, keep locale/unit handling at the boundary, and use public version-pinned facades for Weaving, Merge, and Diverge.
- **Verified fact:** freshness incorporates method identity, calculation contract, and normalized inputs. Loaders reject wrong project types/unsupported versions and discard stale or unverifiable stored results.
- **Verified fact:** reports are built from stored current engine results rather than recalculating methodology. Tests cover schema, export fields, null/NaN handling, localization, project compatibility, and package assets.
- **Recommendation:** hardening should remain in launch/package, UI presentation, reporting format, documentation, test/qualification, and CI layers. Engine directories are out of the expected change set.

### Provenance, UX, accessibility, and performance

- **Verified fact:** all workflows expose validation/limitations text, result state, details/audit records, warnings, and current-result-only exports, but method-specific presentation is assembled across large workflow modules and is not covered by one cross-workflow provenance acceptance matrix.
- **Verified fact:** Phase 16 qualified English/Thai, Metric/Imperial, 1280/768 px, stale/recalculate, capacity/handoff, projects, exports, and zero horizontal overflow in system Chrome.
- **Verified fact:** Phase 16 explicitly did not claim WCAG/axe, screen-reader, cross-browser, or moderated-user certification. Known minor follow-ups are post-calculation result position and narrow-result ellipsis; broader keyboard/assistive-technology review remains recommended.
- **Verified fact:** there is no committed performance suite, engineering UAT protocol, or UAT record.
- **Recommendation:** close these evidence gaps without making a formal conformance claim and without turning microbenchmarks into brittle release gates.

### GitHub and release process

- **Verified fact:** PRs #116–#118 implemented and qualified Phase 15 under parent #115; PRs #120 and #123–#127 implemented and qualified Phase 16 under parent #119. The final baseline check is green.
- **Verified fact:** browser, installed-wheel, Windows launcher, and package-build gates are not in current CI. Because CI installs `.[dev]` rather than `.[dev,ui]` and AppTest imports are skippable, a green current check is not evidence that Streamlit AppTest paths ran.
- **Recommendation:** use one Phase 17 parent issue and one cohesive PR, make UI dependency installation and unexpected skip reporting explicit in CI, add practical repeatable package gates, and keep workstation/browser/UAT evidence in a durable qualification record even where CI cannot reproduce it.

## 4. Issue #114 disposition recommendation

**Classification: C — completed but accidentally left open; its tracking role was also superseded by the completed #115 and #119 sequences.**

Evidence:

1. #114 was opened on 2026-07-15 and has no subsequent update, comment, or closure.
2. #115, opened as the operative Phase 15 parent, contains essentially the same app-wide UI, localization, result-state, project/export, AppTest/browser, clean-wheel, and release-hardening requirements.
3. #115 was closed by merged PR #118 after PRs #116 and #117; its qualification record reports the unified UI, localization, wheel, browser, AppTest, export, and accessibility gates.
4. Phase 16 then broadened task-oriented usability and app-wide qualification. #119 is closed; PR #127 and the v0.9 record report all seven workflows, `126/126` source browser rows, `22/22` installed-wheel rows, and `1066` automated tests.
5. Remaining accessibility and engineering-UAT improvements are explicitly later hardening work. They do not make #114’s completed Phase 15 objective an unfinished methodology phase.

**Recommended execution action:** at Phase 17 startup, post a concise evidence comment on #114 and close it as completed/superseded, linking #115, #118, #119, #127, and `docs/releases/v0_9_phase_16_ux_release_qualification.md`. Then create the new Phase 17 parent issue. Do not silently repurpose #114 for Phase 17.

## 5. Phase 17 objective

Make v0.9’s seven supported calculators acceptable for repeatable local engineering use by hardening setup/launch/package behavior, improving visible methodology provenance and professional report usability, closing material accessibility/UX gaps, establishing stable regression/performance qualification, and recording real engineering UAT—while preserving every qualified numerical and data contract.

The phase is complete only when the gates in section 17 pass and the readiness gate in section 19 produces a documented GO or NO-GO.

## 6. In scope

- Repository, issue, roadmap, release, architecture, quick-start, and supported-scope hygiene.
- Supported Windows/Python 3.12 source-folder setup and launch hardening.
- Clean build, sdist/wheel inspection, installed-wheel execution/resource qualification outside the checkout.
- Evidence-driven dependency/environment isolation improvements.
- Consistent visible methodology/version/scope/provenance, assumptions, limitations, warnings, units, freshness, capacity/handoff, and Not predicted presentation across all seven calculators.
- Additive presentation/formatting improvements to JSON, CSV, Excel, Markdown, and report JSON usability that preserve machine contracts.
- Keyboard, focus, label, status, error, responsive/truncation, and non-color communication follow-up.
- Repeatable browser, package, contract, regression, and performance harnesses.
- A recorded engineering UAT protocol and execution across all seven workflows.
- CI and final release qualification appropriate to the changes.
- Version decision and a Freeway Facility methodology-audit readiness decision.

## 7. Explicit non-goals

Phase 17 must not include:

- Freeway Facility engine, facility flow propagation, aggregation, or facility outputs.
- New or broadened HCM methodology, HCM 7.1 implementation, reliability, managed lanes, work zones, ramp metering, oversaturated facility prediction, or unsupported table interpolation/extrapolation.
- Invented formulas, undocumented engineering assumptions, or synthetic “authoritative” examples.
- EXE, MSI, portable Python, bundled runtime, hosted service, or auto-update architecture without separate evidence and approval.
- A multi-page wizard or UI-engine coupling.
- Formal WCAG conformance, screen-reader certification, or cross-browser support claims without matching evidence.
- Silent changes to project schemas/types/identifiers, method identifiers/versions, normalized inputs, fingerprints, result fields, report/export fields, calculation contracts, units, or null/Not predicted semantics.
- Rewriting historical qualification records to make them appear current.

## 8. Contracts and architecture to preserve

The following are compatibility gates, not suggestions:

1. Calculation engines remain independent of `hcmcalc.ui` and Streamlit.
2. Qualified numerical results, boundaries, lookup behavior, tolerances, and unsupported-scope guardrails remain unchanged unless the numerical defect policy below is satisfied.
3. Project schema `1.2`, legacy-load support for `1.0`/`1.1`, project types, method identities, project identity, normalized inputs, and load-status semantics remain compatible.
4. Fingerprints continue to include effective normalized inputs, method, and calculation contract; inactive/hidden inputs remain non-operative; stale results are not shown or exported as current.
5. Locale and Metric/Imperial conversion stay at the UI/report boundary; engine inputs remain canonical and language-neutral.
6. Reports are generated from a stored current result and never rerun the engine implicitly.
7. Existing report schema `0.1`, canonical JSON keys, export field names, calculation JSON, and null semantics remain stable. `None`/Not predicted must never become zero, an empty numeric, `NaN`, or an invented value.
8. Capacity failure, warning-only state, HCM handoff/stopping state, unsupported scope, invalid input, internal error, and stale state remain distinct.
9. Version-pinned Weaving/Merge/Diverge public facades continue to reject known-unqualified HCM 7.1.
10. Packaged YAML/images/SVGs continue to resolve through package resources outside the source tree.
11. The UI remains a single-page guided worksheet per calculator.

### Numerical defect policy

If a probable numerical defect is discovered, Luna-Max must isolate it from normal Phase 17 work and require all of the following before correction:

1. a minimal reproducible case;
2. authoritative HCM/source evidence;
3. affected-method and user-impact analysis;
4. backward-compatibility and stored/exported-result analysis;
5. the smallest isolated correction;
6. a numerical regression fixture/test with explicit tolerance and provenance;
7. focused and affected browser/project/export qualification, then the full suite.

Use the repository `scrutinize` skill before broadening any method/formula/table/domain and `systematic-debug` for the reproducer. If authoritative evidence is unavailable, do not guess: record the method work as blocked, exclude the suspected output from any GO decision, and continue independent Phase 17 hardening only where safe. A meaningful escaped numerical defect warrants `engineering-postmortem`; ordinary UI/harness failures do not.

## 9. Ordered workstreams

Workstreams are checkpoints inside one autonomous phase, not approval-dependent mini-phases. B through F may use separate internal commits and may overlap after A establishes the live baseline, but G, H, and I are ordered release gates.

### Workstream A — Repository and roadmap hygiene

- **Objective:** make repository/GitHub state describe the actual v0.9 baseline and Phase 17 direction.
- **Evidence/current finding:** #114 is orphaned; README, roadmap, supported-method matrix, architecture, and Phase 16 header status contain stale release/scope statements; no release index, tag, or GitHub Release exists.
- **Expected changes:** close #114 with evidence; create one Phase 17 parent issue; update current-state docs, roadmap, architecture, support matrix, quick-start/release links, and Phase 16 closure status; add/update a Phase 17 qualification/release record as work progresses. Preserve historical documents.
- **Likely areas:** `README.md`, `docs/roadmap.md`, `docs/ARCHITECTURE.md`, `docs/supported_workflows.md`, `docs/methodology/supported_methods_matrix.md`, `docs/ux/phase_16_implementation_plan.md`, `docs/releases/`, GitHub issues.
- **Preserved contracts:** all numerical, persistence, fingerprint, export, and support-envelope contracts.
- **Validation:** link/path check, terminology/scope comparison against navigation and public facades, version-string consistency, `git diff --check`.
- **Risks:** accidentally converting historical statements into current claims or implying unqualified Freeway Facility support.
- **Completion condition:** current docs consistently identify v0.9/Phase 16 as baseline, seven supported calculators, Phase 17 as hardening, and Freeway Facility as audit-gated future work; #114 has an evidence-backed disposition; Phase 17 tracking exists.
- **Dependencies:** starts after execution baseline revalidation; final release fields finish in H.

### Workstream B — Local runtime and distribution hardening

- **Objective:** make the supported local Windows workflow predictable for first setup, repeat launch, updates, and failures without broadening distribution architecture.
- **Evidence/current finding:** source-folder launch works and was documented/qualified, but setup installs editable dev dependencies, upgrades from unbounded lower constraints, assumes `py -3.12`, and has no committed clean-workstation matrix; installed wheel has no supported app entry point; prior editable-install contamination occurred.
- **Expected changes:** first write an explicit runtime support contract. Exercise clean temp copies/VMs for `.bat` and PowerShell paths; improve actionable error messages and environment/provenance checks where evidence shows failure; make setup idempotent; verify run never installs; decide whether production setup should omit dev dependencies; align Python support wording/enforcement; record resolved dependency versions. Add constraints only if reproducibility evidence justifies them and document their update process. Add an installed-package launch/smoke mechanism only if needed for qualification, without declaring wheel installation the end-user workflow by accident.
- **Likely areas:** `setup_app.bat`, `setup_app.ps1`, `run_app.bat`, `run_app.ps1`, `pyproject.toml`, optional new launcher/diagnostic module under `src/hcmcalc`, `runtime_resources.py`, `docs/user_quick_start.md`, README, runtime/package tests, CI.
- **Preserved contracts:** calculation/UI separation, supported Python 3.12 baseline, no implicit package install on normal launch, package resource paths, no user-site or user-owned environment deletion.
- **Validation:** clean Windows/source-copy first setup; second/idempotent setup; repeat launch; paths containing spaces; missing `py`; missing/wrong-version `.venv`; missing Streamlit/dependency; nonzero-exit and readable-message checks; user-site contamination probe; fresh sdist/wheel build and content inspection; installed-wheel import/resource/UI smoke from a directory outside the repository.
- **Risks:** dependency drift, network-dependent setup instability, accidental Python support broadening/narrowing, launcher behavior that only works in a checkout, or destructive `.venv` repair.
- **Completion condition:** the declared local workflow succeeds from a clean supported workstation and after update, common failures tell the user exactly what to do, launch is isolated from unrelated editable installs, and wheel/package resources qualify outside the checkout. No installer architecture is added without evidence.
- **Dependencies:** A defines current documentation; findings may feed F/H CI and qualification.

### Workstream C — Engineering provenance and auditability

- **Objective:** let an engineer identify the governing method and interpret the result without opening raw source code.
- **Evidence/current finding:** engines/audit records already carry many method, intermediate, assumption, warning, and provenance values, and each UI has validation/limitations/details sections; presentation is method-specific and lacks one cross-workflow acceptance matrix.
- **Expected changes:** inventory each workflow’s existing data before changing UI. Define a shared presentation checklist containing calculator/method identity, HCM version/chapter, analysis unit/direction, validation basis versus optional preset, supported scope/limitations, active assumptions and branch provenance, warnings, capacity/handoff status, key intermediate/audit values, units, result freshness, app/report version, and explicit null/Not predicted meaning. Reuse existing authoritative engine/audit constants; make only presentation-layer additions. Do not fabricate page/exhibit citations where the repository lacks authoritative evidence.
- **Likely areas:** `src/hcmcalc/ui/layout.py`, `result_view.py`, `audit.py`, `streamlit_app.py`, `manual_*.py`, `supported_workflows.py`, `i18n.py`, reporting presentation, docs, UI/report tests.
- **Preserved contracts:** engine outputs and identifiers, normalized inputs/fingerprints, project/report schemas and field names, bilingual meaning, null/capacity/handoff distinctions.
- **Validation:** a seven-workflow provenance matrix in EN/TH and Metric/Imperial representative cases; assertions against actual engine/audit data; current/stale/capacity/handoff/null states; report/UI consistency; no claim beyond source evidence.
- **Risks:** mistaking validation examples for scope authority, duplicating inconsistent methodology text, exposing internal-only implementation details, or changing canonical schemas to solve a display problem.
- **Completion condition:** every calculator and every professional report satisfies the shared checklist with correct method-specific distinctions and no unsupported claim.
- **Dependencies:** A supplies authoritative current scope; D consumes the presentation contract.

### Workstream D — Export and report ergonomics

- **Objective:** make exported records practical for engineering review while retaining exact machine compatibility.
- **Evidence/current finding:** CSV/XLSX/Markdown/report JSON exist and are contract-tested; they include assumptions, warnings, limitations, audit context, and null handling. Phase 16 primarily verified successful/current export and stable fields, not print/readability or handoff usability.
- **Expected changes:** evaluate each format using actual reports from all seven workflows. Improve ordering, labels, column widths, wrapping, freeze panes, print/view layout, filenames, localized Unicode rendering, unit visibility, and prominent method/case/freshness/provenance/status context where these can be changed without data-contract changes. Prefer formatting or existing fields. Any proposed report-schema/key change requires an explicit version/migration design and is a stop condition unless already approved; do not silently add/remove/rename canonical fields.
- **Likely areas:** `src/hcmcalc/ui/reporting.py`, export layout helpers, `i18n.py`, `tests/unit/test_reporting.py`, cross-method contract tests, docs/UAT fixtures.
- **Preserved contracts:** report schema `0.1` unless explicitly approved, supported formats, field names/order where contractual, JSON types, `None` semantics, current-result gate, no implicit recalculation.
- **Validation:** golden structural assertions rather than fragile binary snapshots; parse every CSV/JSON/XLSX; openpyxl checks for cells/formatting; Markdown review; EN/TH Unicode; Metric/Imperial units; capacity/handoff/warning/Not predicted; stale export withheld; round-trip result identity.
- **Risks:** cosmetic changes breaking downstream consumers, spreadsheet coercion of identifiers/nulls, translated machine keys, or reports implying unsupported predictions.
- **Completion condition:** representative engineering reviewers can identify case, method, scope, result, status, units, provenance, warnings, and null meaning in every format, while compatibility tests prove canonical data unchanged.
- **Dependencies:** C defines provenance content; G evaluates practical usability; H qualifies final artifacts.

### Workstream E — Accessibility and residual UX hardening

- **Objective:** resolve verified interaction and interpretation risks left after Phase 16 without overstating conformance.
- **Evidence/current finding:** system-Chrome keyboard sampling, named controls, text statuses, contrast sampling, and 768 px overflow passed; formal axe/screen-reader/cross-browser review did not occur. Known minor issues are result visibility after calculation and narrow median-value ellipsis; the Facility data editor relies on framework-provided grid semantics.
- **Expected changes:** reproduce known issues first. Audit keyboard-only order/activation, visible focus, native labels/help, status communication, error association/recovery, post-calculate result discoverability, non-color status, diagrams/text alternatives, zoom/narrow wrapping, truncation, downloads/uploads, and Facility editor operation. Use native Streamlit behavior where possible; add scoped fixes and automated checks for reproduced defects. Axe or assistive-technology probes may be used as diagnostics, but claims remain evidence-limited.
- **Likely areas:** `layout.py`, `result_view.py`, `streamlit_app.py`, `i18n.py`, workflow modules, diagrams/assets descriptions, AppTest/browser tests, UX qualification docs.
- **Preserved contracts:** single-page worksheet, calculation semantics, project/export/fingerprint behavior, meaningful EN/TH parity.
- **Validation:** keyboard-only tasks across all seven workflows; focus/order evidence; labels/status/error text; 1280 and 768 px plus zoom/wrapping probes; EN/TH; current/stale/capacity/handoff; automated accessibility scan if tooling is stable; no critical browser console/page error or page-level horizontal overflow.
- **Risks:** CSS fixes that break Streamlit upgrades, focus manipulation that conflicts with reruns, false WCAG claims, or optimizing for phone layouts outside scope.
- **Completion condition:** no accessibility Blocker/Major remains for supported engineering tasks; known minors are fixed or explicitly documented with low engineering risk; the release record states exactly what was and was not tested.
- **Dependencies:** C clarifies status/provenance communication; feeds G/H.

### Workstream F — Performance and regression robustness

- **Objective:** make regressions reproducible and detect material responsiveness/resource failures without brittle microbenchmarks.
- **Evidence/current finding:** 1066 tests and extensive Phase 16 browser matrices exist, but browser harnesses are untracked, CI only runs pytest, and there is no repeatable performance baseline.
- **Expected changes:** commit a maintainable qualification runner/matrix or equivalent reusable test infrastructure; isolate source and installed-wheel imports; capture dependency/browser/Python/OS provenance; add deterministic output checks. Reconstruct the Phase 16 source/wheel scenarios from the release and workstream records, assign durable row IDs, and record a coverage mapping because the original scripts are untracked; preserve every recoverable row and all recorded coverage categories rather than pretending the exact ephemeral harness is available. Make CI install the dependencies needed for AppTest, report skips, and fail if mandatory UI tests are skipped; add an explicit package-build/resource job. Establish a pre-change and final timing protocol on the same host: warm up, then at least 10 trials for one representative calculation per workflow plus project load and each export family. Record median and p95 with raw data. Track cold app readiness separately. Gate only material regressions: investigate when both median worsens by more than 25% and 100 ms, or p95 worsens by more than 50% and 250 ms; justify any accepted regression in the release record. Network-dependent setup time is reported, not used as a hard performance gate.
- **Likely areas:** new tracked `tests/qualification/` or `scripts/qualification/`, pytest tests, `.github/workflows/test.yml` or additional workflow, docs qualification matrix, package/browser helpers.
- **Preserved contracts:** deterministic numerical outputs, no timing-driven formula approximation, no reliance on source checkout for wheel tests, no unstable sleep-based browser assertions.
- **Validation:** focused harness self-tests; deterministic repeated results; targeted browser matrix after each UI/runtime change; full successor to all Phase 16 source rows at final qualification; installed-wheel successor matrix; repeat performance protocol with environment manifest.
- **Risks:** flaky browser timing, excessive CI duration, platform differences, test code coupled to translated copy, or committing generated evidence/binaries.
- **Completion condition:** a fresh agent can run documented qualification commands, reproduce matrices, distinguish source from wheel imports, and compare stable timing evidence without the original Phase 16 local scripts.
- **Dependencies:** B supplies runtime matrix; C–E add rows; H executes the final matrix.

### Workstream G — Real engineering user acceptance

- **Objective:** demonstrate that actual engineers can complete and interpret supported work, not merely activate widgets.
- **Evidence/current finding:** Phase 16 performed representative operator automation but explicitly was not a moderated user study; no committed engineering UAT protocol or signed result exists.
- **Expected changes:** create a versioned UAT protocol, case sheets using supported non-invented inputs/presets, observation log, severity/disposition register, and final acceptance record. Use at least one reviewer competent in HCM operational analysis and at least one Thai-capable reviewer for Thai tasks; one person may satisfy both roles. Record role/qualification, date, build SHA/version, environment, scenarios, observed outputs, findings, and sign-off. Automation may preflight cases but must not be represented as human UAT.
- **Likely areas:** `docs/uat/` or `docs/qualification/`, approved fixture references, issue tracker, and focused fixes/tests arising from findings.
- **Preserved contracts:** supported-scope boundaries, no participant-driven invented formula, privacy-minimal reviewer metadata, existing projects/exports.
- **Validation:** protocol completeness; all seven scenario records; evidence for save/reload/stale/export; reviewer confirms principal result, warning/unsupported state, audit trail, units, and provenance are understandable.
- **Risks:** unavailable qualified reviewer, feedback broadening methodology, undocumented workaround, or “pass” inferred from automation.
- **Completion condition:** 100% of mandatory scenarios executed; zero unresolved Blocker; zero unresolved Major; any Minor has a documented low-risk disposition and regression coverage where fixed; Enhancements are deferred explicitly. If a qualified reviewer is unavailable, independent work continues but final acceptance and GO remain blocked.
- **Dependencies:** B–F substantially complete; findings loop back through the autonomous fix cycle before H.

### Workstream H — Final release qualification

- **Objective:** produce one auditable release decision on the exact deliverable SHA/artifacts.
- **Evidence/current finding:** Phase 16 provides a strong model but its browser harness is not tracked and CI omits Windows/package/browser gates.
- **Expected changes:** freeze the candidate SHA; run the layered matrix in section 12; build fresh artifacts; verify import/resource provenance; execute full source and wheel browser matrices; complete UAT; audit docs/version/GitHub state; write Phase 17 qualification and release notes; strengthen CI where stable and proportionate. Do not tag/publish unless the parent issue explicitly authorizes it.
- **Likely areas:** tests/qualification, CI, package metadata, release docs, UAT record, GitHub issue/PR.
- **Preserved contracts:** all section 8 gates and exact artifact/result correspondence.
- **Validation:** all section 12 rows and section 17 gates on the final SHA; `git diff --check`; clean worktree; CI green.
- **Risks:** qualifying a different artifact than the PR head, environment shadowing, stale local browser evidence, or version/docs mismatch.
- **Completion condition:** all mandatory gates pass on the same candidate, evidence is durable, PR review findings are resolved, and the release record has no hidden limitation.
- **Dependencies:** A–G complete.

### Workstream I — Freeway Facility readiness gate

- **Objective:** decide whether the existing platform is stable enough to begin a separate Freeway Facility methodology audit.
- **Evidence/current finding:** current engines cover isolated Basic Freeway, Weaving, Merge, and Diverge segments, but no facility composition/flow-propagation contract exists; Phase 16 recommends maintenance/UAT first.
- **Expected changes:** no Freeway Facility formulas or design. Apply section 19 criteria to Phase 17 evidence and record exactly one GO/NO-GO decision with unresolved risks.
- **Likely areas:** Phase 17 qualification/release record, roadmap, next-phase issue only if GO and separately authorized.
- **Preserved contracts:** all current isolated-method boundaries; GO is not implementation authorization.
- **Validation:** evidence links for every gate; independent `scrutinize` self-review; no contaminated baseline defect.
- **Risks:** interpreting strong isolated-method coverage as facility-method evidence, or starting design before authoritative chapter/examples are audited.
- **Completion condition:** one explicit decision using the exact wording in section 19, with reasons and next allowed action.
- **Dependencies:** H complete; NO-GO is mandatory if any gate lacks evidence.

## 10. Expected repository areas affected

| Area | Expected level | Notes |
| --- | --- | --- |
| `README.md`, current docs, release/qualification/UAT docs | High | Correct drift and add durable evidence. Historical release facts remain unchanged. |
| Setup/run scripts and `docs/user_quick_start.md` | Medium | Evidence-driven source-folder runtime hardening. |
| `pyproject.toml`, package entry/resource helpers | Low–medium | Only if runtime/package tests justify changes; no distribution redesign. |
| `src/hcmcalc/ui/layout.py`, `result_view.py`, `i18n.py`, `reporting.py` | Medium | Shared provenance, ergonomics, accessibility. |
| `streamlit_app.py` and `manual_*.py` | Low–medium | Scoped presentation fixes; avoid method adapters unless necessary. |
| `project_io.py`, `workflow_state.py` | Tests expected; production changes exceptional | Contracts are preservation targets, not refactor opportunities. |
| Engine modules under Freeway/Multilane/Two-Lane/Weaving/ramp influence | None expected | Touch only under the numerical defect policy. |
| Tests and new qualification tooling | High | Contract, package, browser, performance, and UAT preflight coverage. |
| `.github/workflows/` | Medium | Add stable build/package gates; browser/Windows gates only where maintainable. |
| GitHub issues/PR | Medium | Close #114, create parent issue, one implementation PR. |

## 11. Autonomous implement-review-test-fix loop

Use repository `long-task-guard` for the entire phase. Maintain ignored `.agent-work/` task plan, progress ledger, decisions, blockers, debug notes, and handoff. Before and after each substantial workstream, use `scrutinize` for intent, end-to-end seams, contract claims, findings, and a `ship`/`fix-then-ship`/`rework`/`reject` verdict. Use `systematic-debug` only for reproducible failures; use `engineering-postmortem` only for a meaningful escaped defect/release blocker/repeated failure; use `technical-status-translation` for the final stakeholder-facing completion report.

For every coherent change:

1. inspect current behavior and authoritative evidence;
2. choose the smallest coherent change;
3. implement it without mixing unrelated cleanup;
4. inspect the complete diff and integration seams;
5. run focused tests;
6. diagnose any failure to root cause;
7. fix the root cause;
8. rerun focused tests;
9. run the applicable contract/regression layer;
10. self-review for methodology, schema, localization, null, accessibility, packaging, and stale-state risk;
11. fix meaningful review findings and retest;
12. record evidence/decision and continue.

Then run broader regression at workstream boundaries. Do not rerun an unchanged failing command more than twice without changed code, environment, input, or hypothesis. Pytest, browser, build, CI, localization, export, persistence, resource, or recoverable contamination failures are routine engineering work—not user stop conditions.

## 12. Validation and qualification matrix

| Layer | When | Mandatory scope and gate |
| --- | --- | --- |
| Static/focused | Every change | Compile/import checks as relevant, focused unit/AppTest tests, localization catalog parity, link/resource checks, `git diff --check`. |
| Numerical contracts | Any shared/UI/report/adapter change; always final | Chapter-backed fixtures and method regression suites unchanged; exact result dictionaries where existing tests use equality; tolerances only where already authoritative. |
| Persistence/freshness | Any UI/project/report change; always final | All project types, schema 1.2 and supported legacy loads, wrong-project/version rejection, normalized inputs, fingerprints, inactive inputs, current/stale/recalculate, no stale export. |
| Cross-method presentation | C–E and final | Seven methods; EN/TH; Metric/Imperial; assumptions/warnings/limitations/provenance/units; capacity, warning, handoff, unsupported, invalid, stale, and Not predicted states. |
| Export/report | D and final | Parse JSON/CSV/XLSX; render Markdown; all seven; Unicode; canonical fields/types; null/no-NaN; current-only; provenance and professional formatting. |
| Full automated suite | Each substantial workstream boundary when risk warrants; mandatory final | Entire pytest suite with UI dependencies installed. Baseline inventory is 1066; final count may legitimately increase and must be recorded. No failure, unexpected skip, or xpass surprise; CI must prove mandatory AppTest paths executed rather than being skipped. |
| Source browser qualification | Targeted rows during B–F; mandatory full final | A committed, coverage-mapped successor preserving every recoverable Phase 16 row and all categories represented by the recorded `126/126`, plus Phase 17 provenance/accessibility/runtime regressions. Any row that cannot be reconstructed from durable Phase 16 records must be called out and replaced by an equal-or-stronger named scenario. System Chrome remains authoritative unless support is explicitly broadened. Zero failed rows, console/page errors, raw tracebacks, or page-level horizontal overflow. |
| Build/package | B and final | Clean `python -m build`; inspect sdist/wheel contents; version/metadata; required YAML/images/SVG/localization; artifact hashes; install without source checkout leakage. |
| Installed wheel | Targeted during B/F; mandatory full final | Fresh Python 3.12 venv outside repository; imports from `site-packages`; all eight routes; all seven default calculations; deep resources; representative branches; project round trips; every report family; provenance/null/stale checks. Retain all Phase 16 22 rows and add changed-feature rows. |
| Windows launcher | B and final | Clean copy, paths with spaces, `.bat` and PowerShell, first/idempotent setup, normal launch/no install, missing/wrong prerequisites, readable exit behavior, environment contamination. |
| Performance/determinism | Baseline before B–F and final | Same host/environment, warmup plus 10 trials, raw median/p95, deterministic results, material-regression thresholds from F. No microbenchmark-only optimization. |
| Engineering UAT | After B–F; repeat affected scenarios after fixes | Section 13 protocol, all seven workflows, qualified reviewers, zero Blocker/Major. |
| Repository/delivery | Final | Candidate SHA equals built/tested SHA; clean execution worktree; docs/version/release consistency; original dirty checkout unchanged; PR checks green. |

The final browser matrix must be full because Phase 17 can change app-wide runtime, provenance, reports, and accessibility. Intermediate loops should run only targeted matrices plus relevant contract suites.

## 13. Engineering UAT protocol

### Participants and evidence

- At least one reviewer competent to interpret HCM operational results and support boundaries.
- At least one Thai-capable reviewer for Thai-language tasks; this may be the same reviewer.
- Record role/qualification (not unnecessary personal data), date, build SHA/version, OS/Python/browser, source or installed distribution, case ID/input source, unit/locale, observations, severity, disposition, retest, and sign-off.
- Preflight all cases with automation. Human execution and interpretation remain mandatory and must not be fabricated.

### Common task sequence for every calculator

Every scenario must require the reviewer to:

1. select the correct method/workflow;
2. enter or adapt supported engineering inputs;
3. distinguish required, optional, and branch-specific inputs;
4. calculate;
5. interpret the principal result and units;
6. identify a warning, capacity, handoff, unsupported, or other guarded state relevant to that method;
7. inspect key intermediate/audit values, assumptions, limitations, and provenance;
8. modify an active input, recognize stale state, and recalculate;
9. save and reload the project, confirming identity/freshness;
10. export at least one human-readable format and verify the corresponding machine-readable record.

### Representative scenario matrix

| Calculator | Mandatory representative tasks/branches |
| --- | --- |
| Two-Lane Segment | Supported straight/grade or curve case plus a passing-context case; inspect ATS, percent followers, follower density, vertical/curve/passing evidence, capacity/guardrail behavior. |
| Two-Lane Facility | Build/edit an ordered multi-segment facility including a passing-lane/downstream or Passing Zone context; validate row errors/inactive opposing values; interpret facility aggregation separately from segment results. |
| Multilane Segment | Measured FFS/general terrain and estimated FFS with Specific grade or External PCE; distinguish Heavy Vehicle % from SUT/TT mix; exercise above-capacity Not predicted. |
| Basic Freeway Segment | Measured and estimated FFS representative paths; general versus supported specific-grade/external PCE branch; inspect SAF/CAF/driver-population provenance and above-capacity nulls. |
| Weaving Segment | One-sided and two-sided geometry evidence; review NWL/lane-change provenance; exercise either long-segment handoff and above-capacity behavior as separate states. |
| Merge Segment | Right-side one-lane on-ramp with measured or estimated freeway FFS; interpret freeway/ramp demands, influence-flow warning versus roadway capacity failure, and Not predicted values. |
| Diverge Segment | Right-side one-lane off-ramp with the complementary FFS branch; verify derived continuing flow, warning/capacity distinction, and invalid off-ramp-demand recovery. |

Across the matrix, cover EN and TH, Metric and Imperial, measured and estimated FFS, terrain/specific grade, supported PCE override, both Weaving geometries, Merge/Diverge warning/capacity states, Two-Lane curve/grade/passing contexts, and multi-segment editing. Not every permutation is required, but every listed branch family must have an identified scenario.

### Severity and acceptance

- **Blocker:** prevents a correct supported engineering task or creates credible material interpretation/data-loss risk.
- **Major:** task is possible only with significant confusion/workaround or has meaningful auditability/accessibility risk.
- **Minor:** low engineering-risk clarity/usability defect with a straightforward workaround.
- **Enhancement:** useful future improvement with no current supported-task or interpretation failure.

Acceptance requires all mandatory scenarios complete, **0 unresolved Blockers, 0 unresolved Majors**, and all fixed findings retested. Minors may remain only when the record explains why engineering risk is low, documents the workaround/owner or deferral, and does not contradict a release claim. Enhancements do not block release and go to explicit backlog items.

## 14. Git, worktree, branch, issue, and PR strategy

1. Fetch `origin` and verify the live baseline, version, open PRs/issues, and original dirty-checkout status.
2. Create execution worktree `C:\Users\kittipat_t\Documents\hcm-calculator-phase-17` from current `origin/main` on `codex/phase-17-release-hardening`.
3. Never reset, clean, stash, reformat, or overwrite the original checkout. Record its HEAD/status and compare at completion.
4. Close #114 with the evidence comment from section 4; create one Phase 17 parent issue containing this scope and completion gates.
5. Use one cohesive implementation PR where practical. Internal commits should align to coherent workstreams or cross-cutting contract gates; avoid a PR per workstream.
6. Permit an isolated hotfix PR only for a confirmed numerical defect or a technically necessary release blocker that cannot safely wait, with explicit issue linkage and compatibility evidence.
7. Keep generated browser output, virtual environments, builds, and `.agent-work` ignored. Commit reusable harnesses, matrices, protocols, and concise qualification records—not bulky transient evidence.
8. Before PR: update from `origin/main` without destructive operations, run final qualification on the resolved head, inspect the entire diff, and obtain `scrutinize` verdict `ship`.
9. Use a non-draft PR after local gates pass, require CI green, resolve review comments through the same loop, rerun affected and final gates, then squash merge. Do not merge the planning branch.
10. Tag or GitHub Release publication is out of scope unless explicitly authorized in the Phase 17 issue; Markdown release qualification remains mandatory.

## 15. Risk register

| Risk | Likelihood / impact | Mitigation and trigger |
| --- | --- | --- |
| Numerical contract drift from presentation work | Low / Critical | Exact engine/result regressions; engine files excluded. Trigger numerical defect policy on any difference. |
| Project/fingerprint/export compatibility break | Medium / Critical | Contract tests before/after; no silent schema/key changes; stop for breaking migration. |
| Unsupported methodology implied by provenance copy | Medium / High | Source-backed wording and scrutinize matrix; distinguish example evidence from scope authority. |
| Dependency resolution changes clean setup | Medium / High | Record resolver manifest, clean/idempotent setup matrix, evidence-based constraints decision. |
| Source import shadows installed wheel | Medium / High | Outside-checkout venv, import-origin assertions, isolated environment variables. |
| Browser qualification remains non-repeatable | Medium / High | Commit maintainable runner/matrix and self-tests; avoid copy-sensitive selectors where stable identifiers/state are available. |
| Browser/performance flakiness | Medium / Medium | Fixed environment, readiness conditions instead of sleeps, warmups/repetitions, material thresholds, raw evidence. |
| Accessibility claim exceeds evidence | Medium / High | State exact tools/browsers/assistive tech and retain non-conformance wording. |
| UAT is simulated or reviewer unavailable | Medium / High | Named role/qualification and sign-off; automation only preflight; no GO without real UAT. |
| Report formatting breaks downstream consumers | Medium / High | Preserve schema/keys/types; structural parsers and cross-version fixtures; presentation-only default. |
| Worktree contamination or user-file damage | Low / Critical | Isolated worktree, status/hash checkpoints, no reset/clean/stash/destructive repair. |
| Phase expands into Freeway Facility design | Medium / Critical | Explicit non-goals and readiness wording; stop on formula/support-domain requests. |
| One large PR becomes hard to review | Medium / Medium | Coherent internal commits, workstream evidence ledger, focused diffs/tests, full final review. |

## 16. Stop conditions

Luna-Max should stop the affected path and report only for a genuine condition:

- authoritative HCM evidence is required but unavailable;
- the required fix would invent or interpolate/extrapolate unsupported methodology;
- a necessary change requires an unapproved breaking project/report/result/fingerprint migration;
- user-owned dirty files would need destructive modification;
- newly fetched `origin/main` materially invalidates the approved plan;
- a materially irreversible architecture/distribution decision cannot be resolved from repository evidence and established principles;
- a qualified engineering UAT reviewer remains unavailable after the protocol, preflight, and all independent work are complete;
- repository delivery becomes impossible after reasonable retries with available Git/GitHub mechanisms.

On a method-specific evidence block, continue independent runtime, documentation, accessibility, regression, and UAT preparation only where it cannot contaminate the affected result. Routine test/browser/build/CI/localization/export/persistence/resource/environment failures are not stop conditions.

## 17. Completion gates

Phase 17 is complete only when all are true on the final candidate SHA:

- Workstreams A–H meet their completion conditions and I records a decision.
- No production methodology scope was added and every section 8 contract is demonstrably stable.
- Any numerical defect followed the full evidence/correction/regression policy.
- Full pytest suite, focused contract suites, compile/import checks, localization parity, and `git diff --check` pass.
- Full source browser successor matrix passes with zero failed rows, console/page errors, raw tracebacks, and horizontal overflow.
- Fresh build, artifact inspection/hash, and installed-wheel successor matrix pass outside the checkout with verified import/resource origins.
- Windows source-folder setup/run matrix passes for supported Python 3.12 and common failure cases.
- Performance/determinism protocol has no unexplained material regression.
- Engineering UAT has 0 unresolved Blocker and 0 unresolved Major; all mandatory scenarios and retests are recorded.
- Documentation, version, README, supported-scope matrix, roadmap, release notes, qualification record, GitHub issue, and PR agree.
- CI is green on the final PR head and again after any post-review change.
- Execution worktree is clean after commit; the original dirty checkout’s HEAD, tracked diff, and untracked path set are unchanged.
- Final report states limitations, artifact SHA/version, test/matrix counts, UAT disposition, issue/PR/merge state, and the exact readiness phrase.

## 18. Release/version recommendation

Repository history uses minor versions for coherent user-visible cross-workflow capability releases (`0.8.0` unified UI, `0.9.0` task-oriented UX) while preserving engineering contracts.

**Working recommendation: `0.10.0`** if Phase 17 delivers the planned user-visible runtime, provenance, report, accessibility, and qualification improvements across the application. This is the likely outcome and should be the issue/PR target, but the version bump should occur only after implementation scope is known and before final artifact qualification.

Use **`0.9.1`** instead if execution ultimately produces only backward-compatible defect fixes, documentation/CI/harness work, and no material user-visible cross-workflow improvement. Do not choose `1.0.0`: the repository still labels production validation data as not implemented and Phase 17 is an acceptance/hardening phase, not a claim of complete HCM coverage. Keep `pyproject.toml`, `hcmcalc.__version__`, tests, artifact filenames, release docs, and UI/report version metadata synchronized.

## 19. Freeway Facility GO/NO-GO criteria

The final Phase 17 record must contain exactly one of:

`GO FOR FREEWAY FACILITY METHODOLOGY AUDIT`

or

`NO-GO FOR FREEWAY FACILITY METHODOLOGY AUDIT`

GO requires all of the following:

1. zero unresolved UAT Blocker and Major findings;
2. acceptable, documented Python 3.12 local setup/launch/update/failure behavior;
3. green full automated suite and final CI;
4. stable full source-browser and installed-wheel qualification;
5. stable project schema/types, normalized inputs, identities, fingerprints, stale-state, and legacy-load behavior;
6. professional UI/report provenance, units, warnings, limitations, capacity/handoff, and null semantics across all seven workflows;
7. no unexplained material performance regression;
8. no known baseline numerical, persistence, export, or state defect likely to contaminate facility integration;
9. coherent README/architecture/roadmap/supported-scope/release/GitHub tracking;
10. exact candidate SHA/artifacts/UAT evidence recorded and clean delivery complete.

Any unmet or unverified criterion produces NO-GO with the failed criteria and remediation owner/path. GO authorizes only a separately scoped **Freeway Facility methodology audit**. That future phase must independently verify the applicable HCM chapter/version, supported facility composition, interactions among Basic Freeway/Weaving/Merge/Diverge, flow propagation, capacity/oversaturation/handoff boundaries, aggregation/facility outputs, authoritative examples/evidence, discrepancy handling, and reuse versus new facility logic. It must not assume isolated-method outputs compose automatically.

## 20. Final execution checklist

### Start

- [ ] Fetch origin; record live baseline SHA/version/open issues/open PRs/CI.
- [ ] Record original checkout HEAD/status/diff/untracked set without changing it.
- [ ] Create clean execution worktree and `codex/phase-17-release-hardening`.
- [ ] Initialize ignored long-task ledgers and revalidate this plan’s assumptions.
- [ ] Close #114 with evidence and create the Phase 17 parent issue.

### Implement and validate

- [ ] Establish pre-change runtime, contract, browser, and performance baselines.
- [ ] Complete A through F using the autonomous loop and focused/broader tests.
- [ ] Keep numerical engines and all schemas/identities/fields stable.
- [ ] Commit reusable qualification infrastructure and concise evidence records.
- [ ] Execute real engineering UAT; fix/retest all Blocker/Major findings.

### Qualify and deliver

- [ ] Freeze candidate SHA and decide `0.10.0` versus `0.9.1` by section 18.
- [ ] Run all section 12 final layers on the same candidate/artifacts.
- [ ] Write Phase 17 release notes and qualification record with exact limitations.
- [ ] Run final scrutinize review; fix findings and rerun affected/full gates.
- [ ] Verify diff hygiene, clean worktree, original checkout unchanged.
- [ ] Open one non-draft PR; obtain green CI; resolve feedback and requalify.
- [ ] Squash merge when authorized by the Phase 17 issue and all gates pass.
- [ ] Record one GO/NO-GO readiness decision; do not start Freeway Facility implementation.

# Luna-Max Execution Handoff

```yaml
verified_starting_sha: 8dc1481163d9864df71e2091ce23f0963b702e92
starting_version: 0.9.0
revalidate_at_start: [origin_main, version, open_issues, open_prs, ci, original_dirty_checkout]
approved_scope: "Release hardening and engineering acceptance for the seven existing calculators; no new HCM methodology"
execution_worktree: "C:\\Users\\kittipat_t\\Documents\\hcm-calculator-phase-17"
execution_branch: codex/phase-17-release-hardening
issue_strategy:
  - "Close #114 as completed/accidentally left open and superseded, with links to #115/#118/#119/#127"
  - "Create one Phase 17 parent issue"
  - "Use one cohesive implementation PR; isolated hotfix only if technically necessary"
ordered_workstreams:
  - A_repository_and_roadmap_hygiene
  - B_local_runtime_and_distribution
  - C_engineering_provenance_and_auditability
  - D_export_and_report_ergonomics
  - E_accessibility_and_residual_ux
  - F_performance_and_regression_robustness
  - G_real_engineering_uat
  - H_final_release_qualification
  - I_freeway_facility_readiness_gate
mandatory_loop: "Inspect -> smallest coherent implementation -> diff review -> focused test -> diagnose/fix -> retest -> broader regression -> scrutinize -> fix/retest -> continue"
mandatory_final_qualification:
  - full_pytest
  - source_browser_successor_to_126_rows
  - installed_wheel_successor_to_22_rows_outside_checkout
  - fresh_build_and_resource_inspection
  - windows_setup_and_launch_matrix
  - persistence_fingerprint_localization_units_export_null_contracts
  - performance_and_determinism_protocol
  - real_engineering_uat_all_seven_workflows
  - git_diff_check_clean_worktree_ci_green_original_checkout_unchanged
version_rule: "Target 0.10.0 for material cross-workflow user-visible hardening; otherwise 0.9.1"
stop_conditions:
  - authoritative_HCM_evidence_unavailable
  - unsupported_methodology_would_be_invented
  - unapproved_breaking_migration_required
  - destructive_change_to_user_owned_files_required
  - origin_main_materially_invalidates_plan
  - irreversible_architecture_decision_unresolved
  - qualified_UAT_reviewer_unavailable_after_independent_work
  - repository_delivery_impossible_after_reasonable_attempts
required_final_status_wording:
  success_go: "PHASE 17 COMPLETE — GO FOR FREEWAY FACILITY METHODOLOGY AUDIT"
  success_no_go: "PHASE 17 COMPLETE — NO-GO FOR FREEWAY FACILITY METHODOLOGY AUDIT"
  stopped: "PHASE 17 STOPPED — NO-GO FOR FREEWAY FACILITY METHODOLOGY AUDIT"
```

Luna-Max should begin without requesting routine clarification. Revalidate facts, execute normal engineering failures autonomously, preserve evidence and contracts, and ask the user only when a section 16 stop condition genuinely occurs.
