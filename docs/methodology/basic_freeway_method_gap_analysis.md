# Basic Freeway Method Completion Gap Analysis

Status: Phase 6 scope lock  
Target: HCM7 one-direction, one-segment Basic Freeway Segment analysis  
Current implementation: `basic_freeway_segment_v0_1`

## 1. Completion definition

The method is complete when the declared Basic Freeway Segment domain is input-driven, independently verified beyond Example Problem 1, explicit at capacity and support boundaries, and consistently integrated across UI, save/load, exports, and reports.

This milestone does **not** include ramp influence areas, weaving, merge/diverge analysis, managed lanes, work zones, reliability, or freeway facility analysis.

## 2. Current implemented capability

- One-direction, one-segment uninterrupted-flow Basic Freeway Segment calculation.
- Measured/user-supplied or estimated free-flow speed.
- Lane-width, right-side lateral-clearance, and total-ramp-density FFS adjustments.
- Speed and capacity adjustment factors.
- Capacity, breakpoint flow, speed-flow relationship, density, LOS, and capacity check.
- General-terrain PCE for level and rolling terrain.
- Explicit above-capacity warning with a bounded audit-continuity output.
- Auditable intermediate values and explicit unsupported-scope validation.

## 3. Material gaps

| Area | Current state | Completion requirement | Priority |
|---|---|---|---|
| Heavy-vehicle PCE | Only level and rolling general-terrain defaults are implemented | Implement the declared specific-grade/mountainous domain, or explicitly exclude it with a defensible completed-scope definition | P0 |
| Driver population | Hard-coded to 1.0 for regular users | Decide whether a driver population factor belongs in the completed segment scope; if supported, expose, validate, calculate, and report it consistently | P1 |
| Adjustment factors | SAF and CAF are accepted as user inputs | Define provenance, valid ranges, defaults, and warning behavior so arbitrary factors cannot silently imply unsupported calibration | P0 |
| Above-capacity behavior | LOS F is returned and speed is capped at density-at-capacity for audit continuity | Confirm the intended engineering contract: capacity-status result rather than oversaturated operational prediction; ensure wording is identical across all surfaces | P0 |
| Estimated FFS | Core branches are implemented for lane width, right clearance, and ramp density | Verify all table domains, lane-count handling, interpolation boundaries, and base-FFS input requirements against the selected HCM7 scope | P0 |
| Speed-flow relationship | Implemented through breakpoint/capacity equations | Add independent branch and boundary qualification, including exact breakpoint, exact capacity, and adjusted-capacity cases | P0 |
| Tests | Example 1 and bounded guardrail tests exist | Add non-example normal cases, sensitivity/monotonicity, interpolation, invalid-input, deterministic, and cross-surface consistency tests | P0 |
| Product integration | v0.1 is integrated into UI/save/export/reporting | Replace v0.1 labels only after qualification; verify calculation freshness and report/export parity | P1 |

## 4. Required engine work packages

1. **Domain model and factor governance**
   - Preserve a canonical typed input model and normalized calculation payload.
   - Define valid and supported ranges for SAF, CAF, FFS, lane count, ramp density, and all percentages.
   - Record whether each factor is default, measured, agency-supplied, or user-entered.

2. **Free-flow-speed qualification**
   - Verify lane-width and right-clearance table selection and interpolation across supported lane counts.
   - Verify total-ramp-density equation boundaries.
   - Keep measured-FFS and estimated-FFS workflows mutually clear and free from irrelevant inputs.

3. **Heavy-vehicle treatment**
   - Complete PCE selection for the declared terrain/grade scope.
   - If specific grades remain excluded, enforce that boundary before calculation and state it in all outputs.
   - Include PCE source and lookup path in intermediate values.

4. **Speed, capacity, density, and LOS**
   - Qualify exact breakpoint and capacity behavior.
   - Treat demand above adjusted capacity as a capacity failure/status result, not an unverified congested-regime estimate.
   - Ensure adjustment factors propagate consistently to breakpoint, capacity, speed, density, and LOS.

5. **Verification**
   - Retain Example Problem 1 as regression evidence, not as the sole qualification basis.
   - Add independent cases for measured and estimated FFS, level and rolling terrain, multiple lane counts, non-unity SAF/CAF, near-capacity, at-capacity, and above-capacity conditions.
   - Add monotonicity checks where physically applicable.

## 5. Explicitly out of scope

- Multilane Highway Segment calculations.
- Ramp influence-area LOS analysis.
- Weaving, merge, and diverge analysis.
- Managed lanes, work zones, reliability, and simulation.
- Freeway facility/corridor analysis and travel-time aggregation.
- Oversaturated operational prediction beyond an explicit demand-exceeds-capacity status.

## 6. Exit criteria

- Every declared terrain and PCE branch is implemented and tested, or explicitly excluded before calculation.
- SAF and CAF have documented provenance, ranges, and deterministic behavior.
- Exact breakpoint, capacity, LOS threshold, and interpolation boundaries are tested.
- Above-capacity outputs cannot be mistaken for a congested-regime speed prediction.
- UI, save/load, exports, and reports consume one calculation result without formula duplication.
- Full repository regression, clean Python 3.12 installation, and Streamlit smoke tests pass.
- Documentation states supported and unsupported domains without overclaiming.
