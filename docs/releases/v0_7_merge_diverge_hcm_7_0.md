# v0.7 Merge and Diverge HCM 7.0 Workflows

## Summary

Version 0.7 adds qualified HCM 7.0 Freeway Merge Segment and Freeway Diverge
Segment product workflows. Both workflows use the public Phase 14.2 facades:

- `MergeSegmentMethod(version="hcm_7_0").calculate(inputs)`
- `DivergeSegmentMethod(version="hcm_7_0").calculate(inputs)`

No Streamlit, persistence, preset, report, or export path imports private
version-specific engine modules or duplicates Chapter 14 formulas.

## Qualified Scope

Merge supports isolated general-purpose freeway one-lane right-side on-ramp
operational analysis with 2-4 freeway lanes, explicit acceleration-lane length
`LA`, upstream freeway demand, on-ramp demand, separate freeway/ramp PHF and
heavy-vehicle percentages, measured or Chapter 12 estimated freeway FFS,
explicit ramp FFS, and level or rolling terrain.

Diverge supports the corresponding isolated one-lane right-side off-ramp
operational analysis with explicit deceleration-lane length `LD`, upstream
freeway demand, off-ramp demand, and derived continuing freeway demand.

HCM 7.1, adjacent-ramp contexts, left-side ramps, two-lane ramps, lane
additions/drops, option lanes, major merge/diverge areas, C-D roadways, managed
lanes, ramp metering, work zones, queues, delay, spillback, and
service-volume/design analysis remain unavailable.

## Product Workflows

Visible navigation labels:

- `Merge Segment`
- `Diverge Segment`

Both appear beside Basic Freeway Segment and Weaving Segment. Validation
presets are starting values, not separate product modes.

Project identities:

- `manual_freeway_merge_segment_v1`
- `manual_freeway_diverge_segment_v1`

Calculation contracts:

- `hcm7_v70_chapter_14_isolated_right_side_one_lane_merge_operational`
- `hcm7_v70_chapter_14_isolated_right_side_one_lane_diverge_operational`

## Diagrams

Original local SVG diagrams are packaged under:

- `src/hcmcalc/ui/assets/ramp_influence/merge_right_on_ramp.svg`
- `src/hcmcalc/ui/assets/ramp_influence/diverge_right_off_ramp.svg`

They are conceptual, not to scale, visible by default, and not a source of
calculation inputs.

## Units and Language

The engines remain US customary. Metric inputs are converted at the UI boundary
for acceleration/deceleration length, speeds, lateral clearances, ramp density,
and density outputs. Demand, PHF, heavy-vehicle percentages, lane count, LOS,
method identifiers, and flow rates remain canonical.

English and Thai labels cover navigation, setup, geometry, demands, PHF/HV,
FFS, diagrams, results, warnings, persistence, and exports.

## Persistence and Exports

Project files store schema version, project type, method family, method
version, calculation contract, unit system, displayed inputs, normalized engine
inputs, fingerprint, result where current, audit, assumptions, warnings, and
limitations.

Load rejects wrong project type, wrong method family, HCM 7.1, wrong contract,
malformed geometry, and cross-loading Merge into Diverge or Diverge into Merge.
Stored results are restored only when the fingerprint and normalized inputs
match.

Exports use the existing report subsystem for CSV, Excel, Markdown,
calculation JSON, and report JSON.

## Result Semantics

Capacity failure is a valid result: LOS F, governing capacity, v/c, and reason
are preserved; speed and density are `null`/Not predicted, never zero.

Maximum desirable influence-area flow exceedance is a warning-only condition
when roadway capacity has not failed. Stable speed, density, and LOS are
preserved.

## Validation

Reference presets:

- Merge Chapter 28 Example 1
- Merge Chapter 28 Example 3 merge component
- Diverge Chapter 28 Example 3 diverge component

Unsupported examples are documented only and are not exposed as calculable
presets.

Focused local qualification for this release included 13 new product tests and
129 focused regression tests covering adapters, projects, reporting,
localization, and Phase 14.2 ramp engines.
