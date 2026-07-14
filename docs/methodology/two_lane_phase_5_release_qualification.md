# Two-Lane Highway Phase 5 — release qualification

Related issue: #82

## Release decision and authority

This specification qualifies the implemented HCM 7th Edition Chapter 15 motorized-vehicle method; it does not add methodology. Authority is, in order: the local `HCM7 CH15 Two-Lane HW Motorized.pdf`; the local Chapter 26 example PDF; NCHRP Research Report 1102 Chapter 7 where already cited by the method; then repository fixtures and tests. Production calculation output is never independent validation evidence.

Supported single segments are Passing Constrained, Passing Zone, and Passing Lane midpoint analysis, Classes 1–5, level/nonlevel upgrade/downgrade, straight/supported horizontal curves, valid Exhibit 15-10 lengths, and valid implemented input domains. Supported facilities are explicitly ordered Passing Constrained, Passing Zone, and Passing Lane segments with explicit Passing Lane roles, supported Step 9 downstream effects, and Step 11 aggregation. Example 3/4 are optional starting values and published reference cases, not scope gates.

Reliability, automatic segmentation, Passing Lane warrant/design, pedestrian or bicycle LOS, overlapping Passing Lane interactions, unsupported physical or geometry domains, and every other HCM method remain explicitly unsupported.

## Evidence, tolerances, and release blockers

Evidence is classified as `published_reference_case`, `method_conformance_case`, `regression_case`, `boundary_case`, or `negative_guardrail_case`. Reference display values use their published display precision; internal calculations use `pytest.approx` tolerances stated by the individual test (normally 1e-6 relative). Inclusive exhibit boundaries are tested at the represented value, with adjacent values on each side.

A release is blocked by an equation/table/reference discrepancy, an unguarded unsupported combination, stale result/export reuse, input/unit mismatch, project migration loss, cross-format load-bearing disagreement, an unexpected skip/xfail, failing CI, or an unclean clean-environment run. Issue #82 may be closed only after those conditions are absent, all matrix rows below are qualified, CI passes, and the PR/release note accurately state this envelope.

## Trace audit matrix

| Step | Source | Engine helper/path | Inputs | Audit fields | Positive tests | Boundary tests | Negative tests | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Exhibit 15-10 | `two_lane_highway_applicability` | type, length | applicability, source | `test_exhibit_15_10_applicability` | all table edges | invalid/outside length | qualified |
| 2 | Eq. 15-1, capacity text | `demand_flow_rate`, `resolve_segment_capacity` | volume, PHF, type, HV | demand, capacity, d/c | phase 2/example tests | exact capacity | negative flow/zero PHF | qualified |
| 3 | Exhibit 15-11 | `vertical_alignment_class` | length, signed grade | class, direction, lookup | `test_vertical_lookup` | all cells/edges | invalid grades/lengths | qualified |
| 4 | Eq. 15-2–15-6, Ex. 15-12 | `estimate_free_flow_speed` | BFFS, widths, access, HV, class | BFFS/adjustments/FFS | `test_step4_free_flow_speed` | coefficient edges | invalid domains | qualified |
| 5 | Eq. 15-7–15-16, exhibits | `estimate_average_speed`, curve helpers | FFS, demand, opposing, geometry | tangent/curve/weighted speed | `test_step5_average_speed`, Ex. 2 | curve/table edges | log/power/curve domains | qualified |
| 6 | Eq. 15-17–15-23, exhibits | `estimate_percent_followers` | demand, opposing, class/type | coefficients, PF | `test_step6_percent_followers` | exhibit edges | invalid ranges | qualified |
| 7 | Eq. 15-24–15-33 | Passing Lane Step 7 helpers | lane, demand, HV, class | lane flow/HV/speed/PF | `test_step7_passing_lane_measures` | capacity/class edges | conservation/domain guards | qualified |
| 8 | Eq. 15-34–15-35 | `estimate_follower_density` | speed, flow, PF, type | formula, density basis | `test_step8_follower_density` | zero/exact capacity | negative/zero-speed guards | qualified |
| 9 | Eq. 15-36–15-38 | `_apply_downstream_adjustment` | ordered roles/distance | upstream ID, effective length, adjusted basis | `test_step9_downstream_passing_lane_adjustment` | effective-length edge | invalid/overlapping contexts | qualified |
| 10 | Exhibit 15-6 | `determine_motorized_los` | final density | threshold group, LOS source | `test_step10_motorized_los` | every inclusive threshold | negative density | qualified |
| 11 | Eq. 15-39 | `calculate_facility` | ordered final results/length | numerators, denominator, critical segment | facility/Ex. 3/4 tests | capacity/length edges | invalid sequence/length | qualified |

## Independent review inventory

The review inventory is represented by published Examples 1–4 plus method-conformance and boundary tests for level Passing Constrained/Zone, upgrade, downgrade, nonlevel/curve, Passing Lane Classes 1–5, exact/over-capacity, and facilities with downstream adjustment/context reset. Expected published values are transcribed from Chapter 26; non-published expected values are explicit constants in focused tests, derived from the cited equation/table rather than generated by the method under test. Review checks normalization, demand, class, capacity, FFS, speed, PF, lane split, density, Step 9, Step 11, and LOS.

## Trace, UI, project, and export requirements

Successful results retain submitted and normalized inputs, units, type, applicability, vertical provenance, demand/PHF/capacity/dc, FFS and speed intermediates, curve details, PF, Passing Lane values, density basis/formula, LOS provenance, assumptions, warnings, unsupported notes, evidence class, and equation/exhibit references. Facilities additionally retain ordered IDs/roles, Step 9 context, each final density basis, length shares, Step 11 terms, capacity-failure/critical segment, and source references.

Manual worksheets fingerprint complete normalized calculation inputs. Any change (including units, type, geometry, curve rows, role, ID, order, or preset) makes a result stale; exports remain unavailable until recalculation. Projects round-trip as create → serialize → load → normalize → calculate → compare. `manual_two_lane_facility_v1` is current; `manual_facility_v0` loads for compatibility. A missing or mismatched fingerprint discards stored result, audit, and output data while retaining validated inputs. Unknown type/schema or malformed data is rejected.

CSV, Excel, Markdown, and report JSON are rendered from the same report structure and preserve normalized/display inputs, units, segment order, outputs/LOS/density basis, Passing Lane context, Step 9/11 values, assumptions, warnings, sources, and evidence class. Workbook tests load the generated file and verify valid sheets/cells; CSV and Markdown section complex facility values deterministically.

## Verification record

Baseline run: `.venv\Scripts\python.exe -m pytest -ra` — 824 passed. Final clean result: Python 3.12.10 in `C:\Users\kittipat_t\AppData\Local\Temp\hcmcalc-phase5-py312`, `python -m pip install -e .[dev,ui]`, then `python -m pytest -ra` — **826 passed**, no skips or xfails. A headless Streamlit launch accepted a connection on port 8515. `git diff --check`, CI, and PR merge remain release gates and must be recorded in the Phase 5 PR before Issue #82 is closed. The clean procedure does not use repository `.venv`, global packages, fixtures as runtime dependencies, or `mockups/`.
