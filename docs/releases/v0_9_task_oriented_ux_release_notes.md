# v0.9.0 Task-Oriented UX Release Notes

## What changed

The calculator app now presents each supported HCM workflow as a guided,
single-page engineering worksheet:

- calculator choices are grouped by roadway/freeway context;
- inputs are ordered by the operator's task, with advanced branches shown only
  when they apply;
- Calculate and Recalculate states are explicit, and stale results are harder
  to mistake for current results;
- result summaries lead with the operational outcome, followed by calculation
  details and audit/intermediate values;
- Save Project and Export / Report actions are separated and placed with the
  project/result workflow;
- English and Thai labels/help text are aligned across the supported workflows;
- Metric and Imperial presentation conversion is preserved at the UI boundary;
- the same patterns now cover Two-Lane Segment, Two-Lane Facility, Multilane
  Highway Segment, Basic Freeway Segment, Weaving Segment, Merge Segment, and
  Diverge Segment.

## Compatibility

This release is a presentation and workflow improvement. It does not change
HCM formulas, qualified methodology scope, project schema, method identifiers,
normalized engine inputs, fingerprints, result fields, or export fields.

Existing supported projects and current-result reports remain governed by the
same version and freshness rules. Stale results must be recalculated before
export.

## Qualification

- Source system-Chrome matrix: `126/126` passed.
- Installed `0.9.0` wheel system-Chrome matrix: `22/22` passed.
- Full automated suite: `1066 passed`.

The qualification is representative system-Chrome operator coverage. It is not
a formal WCAG/axe, screen-reader, or cross-browser certification. At 768 px,
the app targets narrow desktop/tablet layouts rather than small-phone layouts.
