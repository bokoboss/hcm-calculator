# Multilane Highway Method Completion Gap Analysis

Status: Phase 6 scope lock  
Target: HCM7 one-direction, one-segment Multilane Highway analysis  
Current implementation: `multilane_basic_segment_v0_1`

## Phase 7 implemented engine scope

The engine supports one-direction, one-segment, uninterrupted-flow Multilane
Highway analysis with measured FFS from 45 through 70 mi/h, or estimated FFS
for two- and three-lane analysis directions. Estimated FFS uses Exhibit 12-18
posted-speed defaults (+7 mi/h below 50 mi/h; +5 mi/h from 50 through 65
mi/h), Exhibits 12-20, 12-22, 12-23, and 12-24. The four-lane and six-lane
lateral-clearance tables are selected by analysis-direction lane count and
interpolated to the nearest 0.1 mi/h. Divided-median estimated FFS uses an
explicit left-side clearance; undivided and TWLTL medians use the HCM 6 ft
left-side treatment. Measured FFS has no active geometry inputs.

The method uses HCM7 Eq. 12-1 and Exhibit 12-6 through capacity: breakpoint
1,400 pc/h/ln, capacity density 45 pc/mi/ln, and Multilane exponent 1.31.
Above capacity it returns LOS F and an explicit capacity-failure status; it
does not return an oversaturated speed or density prediction.

Internal PCE lookup supports the reviewed general-terrain and printed
specific-grade table domain, with source and lookup-path audit fields. A
positive finite external PCE bypasses the lookup. Unprinted truck mixes and
the ambiguous terminal `>25%` category remain unsupported. Driver population
is fixed to 1.0 because Chapter 12 states that no equivalent Multilane
speed-flow adjustment is available. Chapter 26 Example 4 remains regression
evidence, not a runtime calculation branch.

## 1. Completion definition

The method is complete when supported inputs drive the full declared segment calculation without example-specific lookup constraints, unsupported combinations fail explicitly, intermediate results are auditable, and UI/save/export/report paths consume the same calculation result.

This milestone does **not** include Basic Freeway Segments, ramps, weaving, merge/diverge analysis, managed lanes, work zones, reliability, or facility/corridor analysis.

## 2. Current implemented capability

- One-direction, one-segment uninterrupted-flow Multilane Highway calculation.
- Measured or user-supplied free-flow speed.
- Estimated free-flow speed for the currently implemented geometry branch.
- Lane-width, lateral-clearance, median, and access-point adjustments.
- Capacity from adjusted free-flow speed.
- Heavy-vehicle adjustment using either a supplied PCE or the bounded Example 4 lookup.
- Demand flow rate, density, capacity check, and LOS.
- Explicit unsupported-scope validation and auditable intermediate outputs.

## 3. Material gaps

| Area | Current state | Completion requirement | Priority |
|---|---|---|---|
| Speed-flow relationship | Speed is implemented only for demand below the 1,400 pc/h/ln breakpoint, where speed equals FFS | Implement and verify the complete supported speed-flow branch up to capacity; define above-capacity behavior without implying oversaturated operational analysis | P0 |
| Heavy-vehicle PCE | Internal lookup is restricted to Example 4 grade, length, heavy-vehicle percentage, and truck mix; otherwise the user must supply PCE | Implement the declared HCM7 PCE lookup domain or explicitly adopt a controlled user-supplied-PCE workflow with complete validation and traceability | P0 |
| Estimated FFS | Posted-speed branch is restricted to below 50 mi/h; lateral-clearance calculation is limited to TWLTL and the four-lane table | Implement all estimated-FFS branches declared in scope, including supported median/lane-count combinations and table interpolation rules | P0 |
| Driver population | Input is explicitly rejected | Decide and document whether the completed method supports a driver population factor; implement consistently if required by the declared methodology | P1 |
| Geometry domain | Estimated FFS requires two lanes in the analysis direction | Expand to the lane-count domain supported by the selected HCM exhibits, or state a defensible narrower boundary | P1 |
| Truck mix | Only the default 30% SUT / 70% TT mix is accepted | Implement the supported truck-mix treatment or formalize PCE as an externally supplied engineering input | P1 |
| Capacity boundary | Capacity exceedance is identified, but the engine cannot reach the non-constant speed branch | Define deterministic near-capacity and above-capacity outputs and warnings after the speed-flow implementation is expanded | P0 |
| Tests | Regression and bounded non-example tests exist | Add branch, boundary, monotonicity, invalid-input, unsupported-domain, deterministic-result, and cross-surface consistency tests | P0 |
| Product integration | v0.1 is integrated into UI/save/export/reporting | Replace v0.1 labels and assumptions only after engine qualification; verify freshness and export parity | P1 |

## 4. Required engine work packages

1. **Domain model and normalization**
   - Preserve one canonical typed input model.
   - Separate physical validation, methodology support validation, and normalized calculation inputs.
   - Define units and boundary behavior for every input.

2. **Free-flow-speed completion**
   - Complete base-FFS and adjustment branches selected for the supported domain.
   - Replace TWLTL-only and four-lane-only assumptions where the source methodology supports additional cases.
   - Keep measured-FFS workflow independent from estimated-FFS geometry inputs.

3. **Heavy-vehicle treatment**
   - Remove Example 4 identity checks from production lookup logic.
   - Implement table selection/interpolation for the accepted terrain, grade, length, heavy-vehicle percentage, and vehicle-mix domain, or formally constrain the engine to validated user-supplied PCE.
   - Record lookup inputs and table/interpolation path in intermediate values.

4. **Speed, density, and LOS**
   - Implement the supported speed-flow relationship below and above the breakpoint through the capacity boundary.
   - Treat demand above capacity as a scope/status condition, not as an unverified oversaturated speed estimate.
   - Keep LOS and warning behavior deterministic at exact boundaries.

5. **Verification**
   - Retain Example 4 as regression evidence, not as a runtime dependency.
   - Add independent non-example cases for every supported branch.
   - Add monotonicity checks for demand, PHF, heavy vehicles, access density, and geometric reductions where physically applicable.

## 5. Explicitly out of scope

- Basic Freeway Segment methodology.
- Ramp junctions and ramp influence areas.
- Weaving, merge, and diverge segments.
- Multilane facility/corridor travel-time analysis.
- Managed lanes, work zones, reliability, and simulation.
- Calibration beyond coefficients and adjustment factors explicitly included in the selected HCM7 scope.

## 6. Exit criteria

- No production calculation branch depends on Example 4-specific identity checks.
- Every declared input either affects a verified calculation branch or is rejected with an explicit reason.
- The complete supported speed-flow range through capacity is tested.
- Exact breakpoint, LOS threshold, capacity, and interpolation boundaries are tested.
- UI, save/load, exports, and reports use the same result object without formula duplication.
- Full repository regression, clean Python 3.12 installation, and Streamlit smoke tests pass.
- Method documentation states supported and unsupported domains without overclaiming.
