# v0.4 — Basic Freeway method completion

## Release summary

v0.4 integrates the bounded HCM7 Chapter 12 Basic Freeway Segment engine
across the single-page worksheet, freshness protection, project files, and
JSON/CSV/Excel/Markdown/report-JSON outputs. The engine result object remains
the single source of methodology values; no UI, persistence, or export adapter
implements HCM formulas.

## Completed scope

- Measured FFS accepts a field-study/user-supplied FFS and omits estimated-FFS
  geometry from the engine payload. Estimated FFS accepts base FFS, lane width,
  right-side clearance, and ramp density only. The audit distinguishes base
  FFS, individual reductions, pre-SAF FFS, SAF, and adjusted FFS.
- The worksheet supports internal HCM level, rolling, and printed
  specific-grade PCE lookup, plus an external positive PCE override with
  required provenance. Inactive lookup inputs are canonicalized away.
- Driver population uses the Chapter 26 category contract: a non-regular
  category supplies its paired SAF/CAF and provenance. Regular traffic may use
  explicitly sourced project-governed SAF and CAF values; neither is presented
  as an automatic universal calibration.
- Results, saved projects, reports, and exports retain FFS/PCE/SAF/CAF source
  and lookup information, capacity status, assumptions, warnings, references,
  and structured intermediates.
- At demand above adjusted capacity, the result is LOS F and explicit capacity
  failure. Speed and density remain null/“Not predicted”; no queue, delay,
  travel time, or congested-speed prediction is implied.

## Freshness, projects, and migration

Schema 1.2 persists the effective Phase 9 Basic Freeway normalized payload,
mode selectors, provenance, method identifier/version, and fingerprint.
Fingerprints use normalized engine inputs, so inactive measured/estimated FFS
and internal/external PCE values do not make a calculation stale. Mode changes
always change the normalized identity. Schema 1.0 and 1.1 projects load their
editable inputs safely, but legacy results are not reused unless they meet the
Phase 10 method/version/fingerprint/result contract. Legacy above-capacity
results containing speed or density are invalidated.

## Supported domain and limitations

The release covers one direction and one uninterrupted Basic Freeway Segment
with general-purpose lanes, adjusted FFS from 55 to 75 mph, bounded level or
rolling terrain and printed specific-grade PCE cells, or an explicit external
PCE. It excludes ramp influence areas, merge/diverge, weaving, ramp terminals,
managed lanes, work zones, reliability, bottlenecks/queues, freeway facilities
and corridors, mountainous or mixed-flow PCE domains, unprinted PCE mixes, and
oversaturated operational prediction. The known boundary is intentional:
the terminal `>25%` specific-grade PCE column is not interpolated; an external
PCE is required outside the printed numeric lookup domain.

## Qualification evidence

- Targeted Basic Freeway adapter, project, reporting, Streamlit-state, and
  engine tests cover mode switching, inactive-input identity, PCE provenance,
  driver population, SAF/CAF, migration, and above-capacity null outputs.
- Full repository suite: `860 passed`.
- Clean Python 3.12.10 environment: fresh editable installation with
  `.[dev,ui]`, then `860 passed`.
- Streamlit HTTP smoke: a clean-environment server returned HTTP 200.
- Streamlit interaction smoke: Basic Freeway estimated/internal PCE, measured
  FFS, external PCE with provenance, and internal specific-grade PCE paths all
  completed without an application exception.

The [acceptance matrix](../methodology/method_completion_acceptance_matrix.md)
maps AC-14 through AC-22 to the implementation and qualification evidence.
