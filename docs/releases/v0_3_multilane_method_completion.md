# v0.3 — Multilane method completion

## Release summary

v0.3 integrates the qualified HCM7 Multilane Highway Segment method across the
single-page worksheet, save/load, result presentation, JSON/CSV/Excel/Markdown
exports, and report JSON. The calculation engine remains the sole source of
methodology results.

## Completed product scope

- Explicit measured versus estimated FFS workflow. Measured mode submits only
  measured FFS; estimated-only geometry is non-operative and does not affect
  fingerprints, freshness, saved-project identity, or exports.
- Estimated FFS supports two or three lanes per analysis direction. Divided
  medians require explicit left- and right-side clearance; TWLTL and undivided
  medians use the documented left-side treatment.
- Internal PCE lookup reports exhibit/path provenance. A positive external PCE
  override bypasses internal lookup and is reported as external.
- PCE lookup remains bounded to printed truck mixes and numeric table cells.
  Unprinted mixes, table extrapolation, and the ambiguous terminal `>25%`
  category require an external PCE.
- Result, saved project, and every export retain `None` speed and density for
  above-capacity cases. They explicitly report LOS F and capacity failure;
  they never synthesize an oversaturated prediction.

## Freshness and migration

Project schema 1.1 adds a method identifier, method contract, and effective
input fingerprint. Legacy 1.0 projects load their editable inputs safely but
do not restore a result unless it is validated under the current contract.
The FFS source is authoritative when a legacy payload contains both measured
and estimated fields. Basic Freeway projects also reject stored above-capacity
results that retain the pre-correction synthesized speed or density.

## Retained limitations and ambiguity

This is a one-direction, one-segment uninterrupted-flow Multilane method. It
does not add Basic Freeway completion, ramps, weaving, merge/diverge, managed
lanes, work zones, reliability, or corridor analysis. It does not infer a
Multilane driver-population adjustment: the factor remains fixed at 1.0 due to
the documented HCM ambiguity.

## Qualification evidence

- Targeted Multilane adapter, project, reporting, Streamlit, and validation
  tests cover FFS switching, inactive input identity, divided median, PCE
  provenance, stale-result gating, and save/load migration.
- Targeted Basic Freeway checks cover the corrected above-capacity null
  speed/density contract across UI adapters and reports.
- Full repository suite: `845 passed` on Python 3.12.10.
- Clean Python 3.12.10 environment: fresh `pip install -e .[dev,ui]`, then
  `845 passed`.
- Streamlit smoke: HTTP launch returned 200; Streamlit AppTest completed
  Multilane estimated FFS, Multilane measured FFS, and Basic Freeway workflows.

See the [acceptance matrix](../methodology/method_completion_acceptance_matrix.md)
for AC-14 through AC-22 evidence.
