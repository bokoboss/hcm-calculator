# Thai/English localization architecture

## Scope

Release v0.5 supports `en` and `th`. Localization is a presentation concern in
`hcmcalc.ui.i18n`; HCM method engines do not import catalogs or Streamlit.
English is the deterministic default and fallback. The implementation uses
semantic identifiers such as `result.capacity` and `status.result_stale`, never
English display text as a key. Named `str.format` placeholders are required.

## Catalog and QA contract

`src/hcmcalc/ui/i18n.py` contains one authoritative mapping per locale. The
`validate_catalogs()` test contract checks exact key parity, blank values, and
placeholder parity. Missing presentation keys fall back to human-readable
English rather than exposing an internal ID. New UI text must add an English and
Thai semantic entry and a focused test where it carries engineering meaning.

Canonical method IDs, result keys, enum values, input payloads, provenance
codes, units, and numeric types are never translated. `field_label()` and
`enum_label()` only create display text from those canonical values.

## State, projects, and freshness

The selected locale is session state named `ui_locale`; it defaults to `en` and
is globally visible before method-specific forms. It does not clear widgets,
change a selected canonical option, or participate in a fingerprint.

Projects retain schema **1.2**. They may include optional
`presentation.locale` metadata, which is backward-compatible and outside
normalized inputs, result identity, and `calculation_fingerprint`. On load, an
explicit saved locale is restored; a legacy project without it retains the
current application locale. Invalid supplied locale metadata is rejected.

## Exports

The export control offers same-as-UI, English, or Thai. JSON retains canonical
machine keys, enum values, numeric types, nulls, method metadata, and
fingerprints. Its `presentation` object records the selected export locale.
CSV retains its portable structure while headings and display labels are
localized. Excel, Markdown, and report JSON localize presentation labels; Excel
sheet titles are safely constrained to its character and length rules. Units,
equation symbols, official HCM titles, citations, user-entered provenance, and
machine identifiers remain unchanged.

## Message contract

New presentation messages use stable codes with named parameters. If an engine
must expose a new user-facing status, its compatible audit structure is:

```json
{"code":"capacity.demand_exceeds_capacity","params":{"capacity_pcphpl":2300.0},"message_en":"Demand flow exceeds capacity."}
```

The engine may keep `message_en` for audit compatibility. Presentation code
translates by `code` and never requires engines to import a catalog.
