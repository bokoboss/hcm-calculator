# Chapter 15 Vertical Data Ingestion Guidelines

## Purpose

These guidelines define how verified Chapter 15 vertical-class, grade-length,
adjustment, and validation-fixture data may be proposed in future PRs. The
Phase 4B manifests and fixture template are preparation artifacts only and are
not runtime calculation inputs.

## Adding Verified Data

Each future data or fixture PR must:

1. Add one narrowly scoped data category or validation path.
2. Identify the source and exact source reference without copying protected
   table contents into the repository unless permission and review allow it.
3. Record units, lookup keys, applicability, boundaries, inclusivity,
   assumptions, and exclusions.
4. Provide independently checked expected outputs, material intermediate
   values, tolerances, rounding rules, and validation status.
5. Record the checker/reviewer evidence and explain why the fixture is
   independent of facility effects when claiming standalone support.
6. Keep all new data marked `not_runtime_enabled` until the methodology,
   fixture, implementation, audit, and regression review is complete.

## Required Review Evidence

- Source attribution and source-version confirmation.
- Manual verification of every proposed value and unit.
- Evidence that the data is applicable to the exact segment type, vertical
  class, grade/length domain, heavy-vehicle domain, and calculation context.
- Independent checked calculation or accepted published example.
- Review of copyright and repository-use status.
- Explicit reviewer sign-off before runtime enablement.

OCR-extracted, transcribed, or inferred values must not be used without manual
verification against the authoritative source. Missing values must never be
interpolated, approximated, or invented merely to complete a dataset.

## Tests Before Runtime Enablement

- Manifest/schema validation for source, status, required keys, and required
  outputs.
- Boundary tests immediately below, at, and above every claimed lookup
  boundary.
- Method-level tests for all material intermediates.
- Complete expected-output fixture tests with documented tolerances.
- Unsupported adjacent-case and failed-audit tests.
- Regression tests for Example Problems 1 through 4, level-straight behavior,
  horizontal curves, vertical lookup/guardrails, audit, project save/load, UI,
  and CLI behavior.

Placeholder manifests and fixtures must not be imported by production
calculation modules or treated as validation evidence.
