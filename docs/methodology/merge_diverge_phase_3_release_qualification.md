# Phase 14.3 Release Qualification

## Baseline

- Starting remote `main` SHA: `985f2104b55906bec9970f608c5e51b5b152c10b`
- Branch: `codex/merge-diverge-phase-3-product-integration`
- Product release: `v0.7.0`

The starting SHA includes the Phase 14.2 Merge/Diverge engine merge and the
Multilane capacity-display hotfix.

## Architecture

The product integration adds `src/hcmcalc/ui/manual_ramp_influence.py` as a
Streamlit-independent adapter. It converts display units, loads maintained
fixtures, builds typed public-engine input dictionaries, runs only the public
facades, and assembles audit records.

Streamlit rendering is in `src/hcmcalc/ui/streamlit_app.py`. Persistence is in
`src/hcmcalc/ui/project_io.py`. Exports use the existing
`src/hcmcalc/ui/reporting.py` subsystem.

No UI, project, preset, or export path imports private
`ramp_influence.merge.v7_0` or `ramp_influence.diverge.v7_0` implementations.
No numerical formulas are reimplemented outside the qualified engines.

## UI Routes

Visible app labels:

- `Merge Segment`
- `Diverge Segment`

Thai labels:

- `ช่วงทางรวม`
- `ช่วงทางแยก`

## Project Types and Fingerprints

Project identities:

- `manual_freeway_merge_segment_v1`
- `manual_freeway_diverge_segment_v1`

Calculation contracts:

- `hcm7_v70_chapter_14_isolated_right_side_one_lane_merge_operational`
- `hcm7_v70_chapter_14_isolated_right_side_one_lane_diverge_operational`

Fingerprints include method family, calculation contract, method version,
geometry, auxiliary-lane length, component demands, PHF, heavy vehicles,
terrain, FFS mode and fields, ramp FFS, SAF/CAF provenance, geometry evidence,
and isolated adjacent-ramp context. Locale and display-only state are excluded.

Stored results are withheld when normalized inputs or fingerprints do not
match the current worksheet.

## Diagrams and Packaging

Original local diagrams:

- `src/hcmcalc/ui/assets/ramp_influence/merge_right_on_ramp.svg`
- `src/hcmcalc/ui/assets/ramp_influence/diverge_right_off_ramp.svg`

The diagrams are conceptual, not to scale, visible by default, and packaged
inside the `hcmcalc.ui` package tree. They contain no HCM/HCS copied figures,
screenshots, OCR, or proprietary source material.

## Presets

Maintained fixture-backed presets:

- Merge blank/custom from Chapter 28 Example 1 starting values
- Merge Chapter 28 Example 1
- Merge Chapter 28 Example 3 merge component
- Diverge blank/custom from Chapter 28 Example 3 diverge component
- Diverge Chapter 28 Example 3 diverge component

Example 2, Example 4, and Example 5 are not exposed as calculable presets.

## Exports

Current-result-only export formats:

- CSV
- Excel
- Markdown
- report JSON
- calculation JSON through existing result/project payloads

Capacity failure preserves LOS F, governing capacity, v/c, and null speed and
density in JSON. Warning-only maximum desirable influence-flow exceedance is
exported as a warning without being reclassified as roadway capacity failure.

## Locale and Unit Matrix

English and Thai presentation keys are registered for navigation, setup,
geometry, demand, PHF/HV, FFS, diagrams, results, warnings, null predictions,
project loading, and exports.

Metric and Imperial conversions are performed at the UI boundary. Engine inputs
remain US customary.

## Tests

Focused tests added:

- `tests/unit/test_manual_ramp_influence.py`

Local focused result:

- `python -m pytest tests\unit\test_manual_ramp_influence.py tests\unit\test_localization.py tests\unit\test_project_io.py tests\unit\test_reporting.py tests\unit\ramp_influence\test_ramp_influence.py -q`
- Result: 129 passed

Compile result:

- `python -m compileall -q src tests`
- Result: passed

## Known Limitations

The integration qualifies the isolated product workflows only. HCM 7.1,
adjacent-ramp influence, non-right-side ramps, two-lane ramps, lane additions,
lane drops, option lanes, major merge/diverge areas, C-D roadways, managed
lanes, queues, delay, spillback, and design/service-volume analysis remain
guarded.

## Release Decision

The local implementation is qualified for a focused v0.7 product integration
PR once the full suite, Streamlit AppTest/browser/HTTP smoke, wheel build and
asset inclusion check, GitHub CI, and final diff review pass.
