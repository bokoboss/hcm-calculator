# v0.9.0 Phase 16 UX Release Qualification

Date: 2026-08-10
Decision: **PASS — release ready**
Baseline: `origin/main` at `210a460b2dbc13ec6cbd42bd757376aafa58bf6c`
Qualification branch: `codex/phase-16-6-app-wide-ux-release-qualification`
Package version: `0.8.0` before qualification; `0.9.0` after qualification

## Scope and release decision

Phase 16 is closed as an application-wide, task-oriented UX release. The
qualification covered the seven implemented calculator workflows and the
public Supported Workflows reference surface:

| Group | Qualified workflows |
| --- | --- |
| Roadways | Two-Lane Segment, Two-Lane Facility, Multilane Highway Segment |
| Freeways | Basic Freeway Segment, Weaving Segment, Merge Segment, Diverge Segment |
| Reference | Supported Workflows |

The release decision is based on the combined source-checkout matrix, the clean
installed-wheel matrix, automated tests, packaging/resource checks, and a
documentation audit. No blocker or major product defect remains. The release
does not expand HCM methodology scope and does not change calculation formulas,
method identifiers, normalized inputs, project schema, fingerprints, result
fields, or export fields.

## Phase 16 closure summary

- Phase 16.1 established the UX audit, task-oriented worksheet direction, and
  compatibility boundaries.
- Phase 16.2 implemented and qualified the Multilane pilot.
- Phase 16.3 completed Multilane usability, regression, and responsive
  qualification with the documented representative-accessibility limits.
- Phase 16.4 rolled the proven presentation patterns through Basic Freeway,
  Merge, and Diverge.
- Phase 16.5 rolled the patterns through the geometry-heavy Weaving and
  Two-Lane workflows.
- Phase 16.6 performed the app-wide consistency review, source/wheel release
  qualification, packaging check, release documentation, and closure gate.

## App-wide UX audit

The audit found a consistent shared grammar across the seven calculators:

- navigation is grouped by roadway/freeway context, with Supported Workflows
  available as a reference page;
- each calculator remains a single-page guided worksheet with ordered task
  sections rather than a multi-page wizard;
- shared labels and help text cover validation basis and limitations,
  calculation details, audit/intermediate values, optional defaults, project
  loading, project output, export/report actions, and the post-calculation
  result state;
- results use a shared current/stale hierarchy, with `Calculate`/`Recalculate`
  and current-result-only export visibility;
- English/Thai and Metric/Imperial are handled at the UI boundary while the
  calculation contracts remain stable;
- native labelled controls, branch-specific disclosure, and the same project
  versus report action grouping are used throughout the app.

The remaining differences are intentional engineering distinctions, not UX
drift: the Two-Lane Facility table editor and facility summary, Weaving
configuration diagrams and HCM stopping/handoff state, Two-Lane grade/curve/
passing-zone controls, Merge/Diverge geometry and derived demand, and the
different capacity semantics of Multilane and Basic Freeway results.

The Supported Workflows page was checked against the actual navigation and
method contracts. It names all seven implemented workflows, documents the
current support boundaries and exports, and does not imply support for
unqualified facilities, HCM 7.1, queues, delay, or other unsupported domains.

## Browser qualification

### Source checkout

System Chrome was driven with Python Playwright against the isolated source
checkout, with the worktree `src` directory explicitly selected to prevent
unrelated user-site editable installs from shadowing the package.

| Matrix | Result | Coverage |
| --- | ---: | --- |
| Weaving + Two-Lane | 58/58 | Weaving, Two-Lane Segment, Two-Lane Facility; branches, stale/recalculate, capacity/handoff, projects, export, diagrams, EN/TH, Metric/Imperial, 1280/768 |
| Basic Freeway + Merge + Diverge | 43/43 | Route, branch, capacity, stale, project, export, EN/TH, Metric/Imperial, 1280/768 |
| Multilane | 25/25 | Default, terrain/grade/PCE/FFS branches, capacity, stale, project, report, EN/TH, Metric/Imperial, 1280/768 |
| **Source total** | **126/126** | All rows passed |

All source rows recorded zero browser console/page errors and zero horizontal
overflow. Evidence is retained in the local, ignored qualification output
root `output/playwright/phase16_6_app_wide_ux_release_qualification/`.

### Installed wheel

The final `hcm_calculator-0.9.0-py3-none-any.whl` was installed with its UI
dependencies into a fresh Python 3.12 environment whose working directory was
outside the repository and whose imports resolved from `site-packages`.

Wheel SHA-256:

`008AC51FCDF5891A0C21159EE0FBB6E8EA09AA7CCE1E14820D7E1055C28CFA99`

The wheel contains the required Weaving diagrams, Two-Lane Passing Zone image,
example YAML resources, and localization module. The installed-wheel browser
matrix used system Chrome and passed `22/22` rows:

- all eight routes, including Supported Workflows;
- all seven default calculator calculations;
- deep resource checks for Weaving and Two-Lane;
- Two-Lane Facility and Weaving project save/load round trips;
- the Multilane Specific Grade branch;
- current-result CSV export for Multilane and Diverge.

The wheel matrix recorded zero browser console/page errors and zero horizontal
overflow. Evidence is retained in the local, ignored directory
`output/playwright/phase16_6_app_wide_ux_release_qualification/installed_wheel_v0_9/`.

## Persistence, wrong-project rejection, and exports

Project compatibility was checked through the project I/O contract tests,
Streamlit AppTest coverage, and the browser matrix. The combined coverage
exercised save/load for all seven calculator types, including facility
multi-segment editing, inactive facility values, Weaving one/two-sided state,
Multilane branch inputs, and Merge/Diverge measured or estimated FFS paths.
Loaded projects restore the method-specific inputs and current/stale result
state without recomputing a different methodology.

Wrong-project and unsupported-version files are rejected through the existing
typed project loader and UI error path. No raw traceback, `ImportError`, or
missing-resource page was observed in source or wheel browser runs.

JSON, CSV, Excel, and Markdown reporting contracts remain compatible. Current
results export successfully; stale results remain blocked until recalculation.
The validation suite checked field names and metadata, current-result gating,
and the absence of `NaN` field values. The CSV browser check matches complete
field tokens so legitimate words such as `provenance` are not treated as a
numeric NaN value.

## Localization, units, responsive behavior, and accessibility boundary

English and Thai were exercised across the source matrices, including route
navigation, method branches, stale/result states, project/report actions, and
768 px narrow layouts. Metric and Imperial UI conversions were exercised on
each calculator family and in the installed-wheel smoke cases. The 1280 px and
768 px layouts remained readable without horizontal document overflow.

This is representative operator qualification in system Chrome, not a formal
conformance claim. It does not certify WCAG/axe, screen readers or other
assistive technologies, Safari/Firefox, or a moderated user study. The 768 px
case represents a narrow desktop/tablet width, not a small-phone target. The
known minor follow-ups from earlier phases remain: after calculation the result
can sit above the current viewport, and long Median type values can ellipsize
in a narrow result grid.

## Automated and packaging gates

- `python -m compileall -q src tests` — passed.
- `python -m pytest tests/unit/test_streamlit_app.py -q` — `86 passed`.
- `python -m pytest -q` — `1066 passed`.
- Focused project/report/unit/workflow/localization/contract/package suite —
  `128 passed`.
- `python -m build` — built the 0.9.0 sdist and wheel successfully.
- Wheel contents — 90 entries; required images, YAML resources, and
  localization module present.
- `git diff --check` — clean.

The qualification environment also exposed an inherited user-site editable
install for an unrelated worktree. That environment issue was resolved by
explicit source import isolation and a clean wheel environment; no user-owned
editable-install files were modified.

Streamlit emitted the same internal Arrow fallback/widget-policy warnings in
source and wheel server logs. They did not surface as browser console errors,
raw tracebacks, broken resources, or visible workflow failures, so they are
recorded as framework runtime observations rather than release defects.

## Defects and compatibility disposition

The only findings were qualification-harness or environment issues:

1. An unrelated editable install shadowed the source package; the launcher
   environment was isolated and import origins were verified.
2. A Diverge browser row re-selected an already-selected option and timed out;
   the retry asserted the current branch instead and passed.
3. The installed-wheel harness used two stale method labels and a raw
   substring `nan` check; the temporary harness was corrected and the final
   0.9.0 matrix passed.

No production code change was needed to address these findings. No HCM
methodology, schema, fingerprint, result, export, or persistence contract
change was introduced for Phase 16.6.

## Version recommendation and next phase

The qualified version is **0.9.0**. This is a minor release because the
app-wide task-oriented UX is a user-visible, cross-workflow improvement while
the public engineering calculation contracts remain compatible. No tag,
package-index publication, or next feature phase is started by this record.

The roadmap recommendation is to use the next major effort for maintenance and
distribution hardening plus real engineering user acceptance: improve local
packaging, provenance display, export ergonomics, accessibility follow-up, and
performance/regression coverage. After that evidence is complete, a separate
audited methodology phase may address Freeway facilities. Any such expansion
must again define authoritative references, validation fixtures, audit fields,
persistence, exports, and release gates before implementation.

## Final classification

**PASS — Phase 16 closed; v0.9.0 release ready.**

The remaining steps are repository delivery gates only: commit, non-draft PR,
CI, merge, and closure of Issue #119.
