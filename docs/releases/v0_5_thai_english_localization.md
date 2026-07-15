# v0.5 — Thai/English localization

## Summary

v0.5 adds presentation-only English (`en`) and Thai (`th`) localization to the
qualified HCM Calculator. The global selector is session-stable and preserves
inputs, method selection, current results, and freshness. English remains the
default; locale is not inferred from the operating system.

## Contract

- Semantic catalogs, fallback, placeholder validation, and terminology are
  documented in `docs/localization/`.
- Saved projects remain schema 1.2; optional `presentation.locale` is
  backward-compatible metadata. An explicit saved locale restores on load;
  legacy projects retain the active UI locale.
- Export language may be same-as-UI, English, or Thai. JSON retains canonical
  keys, numeric types, enum values, schema/method identifiers, and nulls, with
  presentation metadata. CSV remains portable; Excel and Markdown localize
  presentation text.
- Official titles, citations, method identifiers, units, equations, and
  user-entered provenance remain unmodified.

## Regression and limits

No HCM equations, exhibits, coefficients, PCE/SAF/CAF methodology, LOS
thresholds, or supported domains changed. Two-Lane Segment, Two-Lane Facility,
Multilane Segment, and Basic Freeway Segment retain their established bounded
scope; ramps, merge/diverge, weaving, facilities/corridors, oversaturation, and
other documented exclusions remain excluded. Qualification results and known
exceptions are recorded with the implementation PR; untranslated exceptions are
limited to official citations, file names, units, abbreviations, formulas,
machine identifiers, and user-entered provenance.
