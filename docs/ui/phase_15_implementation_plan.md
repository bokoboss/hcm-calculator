# Phase 15 implementation plan

## Phase 15.2 work packages

Phase 15.2 implementation is complete. The P1 migration work landed the shared
layout, localization, navigation, and result-state primitives and migrated all
eight visible modes: Two-Lane Segment, Two-Lane Facility, Multilane Segment,
Basic Freeway Segment, Weaving Segment, Merge Segment, Diverge Segment, and
Supported Workflows.

1. **Foundation (P1):** revise `layout.py`, `result_view.py`, `workflow_state.py`, `i18n.py`, and focused tests to add header/scope, section label, starting-values, primary action, stale banner, typed result panels, diagram container, project/export, audit, and limitations primitives. Keep helpers narrow; do not create a method-switching mega-helper.
2. **Localization (P1):** migrate visible strings in `streamlit_app.py`, `layout.py`, `supported_workflows.py`, `project_io.py`, `reporting.py`, and diagrams to the existing catalog. Add parity/hardcoded-visible-string tests and approved terminology.
3. **Workflow migration (P1 then P2):** Multilane, Basic Freeway, Merge, Diverge; then Two-Lane Segment, Facility, Weaving; finally Supported Workflows/navigation. Preserve each input, calculation contract, canonical unit conversion, current fingerprint semantics, and export field.
4. **Responsive/accessibility (P2):** native-first layout, named controls, diagram alternatives, contrast and keyboard review; no per-workflow CSS duplication or styling dependency.

## Risks and review gates

No numerical-engine formulas, method-version coverage, project schema (unless unavoidable and backward compatible), fingerprint semantics, qualified inputs, limitations, or export fields may change. Do not infer geometry from a diagram. Each package needs focused AppTests, localization parity, `git diff --check`, and review of Thai layout at narrow width before the next package.

## Phase 15.3 sequence

Implement the qualification matrix tests; run full pytest, UI/AppTest subset,
HTTP smoke, browser review in both locales/units, editable and wheel smoke,
compileall, and diff review. Block release on Critical/High result-state,
localization, navigation, or stale-export defects. Phase 15.3 starts from the
Phase 15.2 landed state with all seven calculators and Supported Workflows
migrated, no known unresolved P1 issue, and these remaining gates: clean
wheel-installed qualification, exhaustive app-wide browser matrix, release
qualification, and release notes.
