# v0.6 — HCM 7.0 Freeway Weaving Segment

## Release summary

v0.6 integrates the qualified HCM 7.0 Chapter 13 isolated freeway weaving
engine into the calculator-first Streamlit product. The worksheet calls only
`WeavingSegmentMethod(version="hcm_7_0").calculate(inputs)`; no equations are
duplicated in UI, persistence, presets, or reporting.

## User workflow

Choose **Weaving Segment**, select a reference preset or enter a custom case,
provide configuration, movement, FFS/heavy-vehicle, and explicit geometry
evidence, review the conceptual weaving schematic, then run the calculation.
The worksheet displays auditable outcomes, supports English/Thai navigation and
Metric/Imperial display, and saves a version-pinned
`manual_freeway_weaving_segment_v1` project. Current results can be exported as
CSV, Excel, Markdown, calculation JSON, and report JSON.

## Qualified scope and behavior

- HCM 7.0 only; HCM 7.1 remains known but unqualified, unavailable, and
  rejected as a calculable project.
- Freeway-only isolated operational analysis, qualified one-sided/two-sided
  geometry, `N = 3/4`, and the documented `NWL` envelope.
- Reference presets are Chapter 27 Examples 1–3 numeric fixtures, not extra
  method modes.
- Above capacity returns LOS F, capacity and `v/c`, with speed/density null and
  visibly **Not predicted**.
- `LS >= LMAX` is an explicit Chapter 12/14 handoff with no LOS or fabricated
  performance prediction.

## Limitations

C-D/multilane weaving, Design/Sensitivity, overlapping segments, managed or
cross-weave configurations, signal/ramp control, queues, specific-grade/truck
mix paths, and automatic lane-change or `NWL` derivation are excluded.

See [Phase 13.3 qualification](../methodology/weaving_phase_3_release_qualification.md)
for validation and release evidence.
