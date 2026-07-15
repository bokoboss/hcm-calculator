# Phase 13.2 Engine Qualification: Versioned Freeway Weaving Segment

## Scope and architecture

- Starting `main` SHA: `76b45ecc42699165008695f4f94d221bc4d1e95b`.
- Qualified method: `hcm_7_0`, `hcm7_v70_freeway_weaving_segment`.
- Known but unqualified method: `hcm_7_1`; see
  [the HCM 7.1 audit](weaving_hcm_7_1_methodology_audit.md).
- Public API: `WeavingSegmentMethod(version="hcm_7_0").calculate(inputs)`.
  Dispatch happens once in `weaving.registry`; the 7.0 package does not import
  a 7.1 module or coefficient.

The qualified envelope is isolated freeway operational analysis only: one- and
two-sided geometry; `N=3` or `4`; one-sided `NWL=2` or `3`; two-sided `NWL=0`;
explicit LC values and structured geometry evidence; 15-minute equivalent
hourly demand; measured or Chapter 12-estimated FFS; common segment HV factor;
and level or rolling general terrain. C-D/multilane facilities, Design and
Sensitivity modes, multiple segments, ramp metering, queue prediction,
facility/reliability analysis, specific grades, movement-specific HV factors,
and a Chapter 14 calculation are not supported.

## Sources and implementation mapping

The governing material was the local licensed `HCM 7th.pdf`: Chapter 13 printed
pp. 13-1--13-41 (PDF pp. 526--566) and Chapter 27 Examples 1--3 (PDF pp.
1521--1535). No licensed PDF, image, OCR output, or source narrative is
committed. The Phase 13.1 crosswalk and support contract remain controlling
context. The legacy repository at `8bcdf89038329fbdc46dac286733d6d18f9f3504`
was diagnostic only.

| Engine stage | HCM 7.0 evidence |
| --- | --- |
| Demand conversion and movement classification | Eq. 13-1; pp. 13-16--13-19 |
| Configuration, `LCMIN`, and `LMAX` | Eqs. 13-2--13-4; pp. 13-19--13-21 |
| Density and weaving-flow capacity | Eqs. 13-5--13-10; pp. 13-22--13-24 |
| Lane-change branches | Eqs. 13-11--13-17; pp. 13-25--13-27 |
| Speed, density, LOS | Eqs. 13-18--13-23; pp. 13-28--13-29; Exhibit 13-6 |
| FFS, base capacity, PCE, `fHV` | Chapter 12 Eq. 12-2, Eq. 12-6, Eq. 12-10 and Exhibits 12-20, 12-21, 12-25 |

Only demonstrably identical Chapter 12 helpers are reused without moving or
changing their existing implementation: FFS adjustment, basic freeway capacity,
general-terrain PCE, and `fHV`. Chapter 12 speed-flow, density, LOS, and
capacity-failure contracts are not reused.

## Validation evidence

`references/weaving_example_inputs.yaml` records visually checked Chapter 27
inputs, selected intermediate values, source pages, and display-level
tolerances. All three compatible examples pass:

| Example | Configuration | Final expected result |
| --- | --- | --- |
| 1 | one-sided major | 53.1 mi/h, 26.3 pc/mi/ln, LOS C |
| 2 | one-sided ramp | 61.9 mi/h, 20.2 pc/mi/ln, LOS C |
| 3 | two-sided | 45.8 mi/h, 39.2 pc/mi/ln, LOS E |

Example 3's published nonweaving lane-change chain uses 5,015 pc/h although its
Equation 13-1 flow is 4,995 pc/h (rounded). The engine applies the equation
defined, unrounded flow and the regression prevents using the inconsistent
printed value. A separate published 4,573 veh/h discussion value is not used;
Equation 13-5/13-6 governs.

Boundary/unit tests cover strict mapping parsing, boolean/nonfinite rejection,
option-lane geometry evidence, all one-sided lane/NWL pairs, two-sided geometry,
`LS == LMAX` and `LS > LMAX` handoff, unrounded `v/c == 1.00`, `v/c > 1.00`
null predictions/LOS F, and the lane-change low/high/interpolated logic through
the Chapter 27 and synthetic cases. Version tests reject unknown versions,
known-unqualified 7.1, input/version mismatch, and v7.0 source imports of 7.1.

## Defects, limitations, and Phase 13.3 gate

The legacy's permissive/ambiguous geometry, its capacity-failure continuation,
and the Chapter 27 Example 3 printed chain are not replicated. No Phase 13.1
assumption was broadened. The stable UI boundary is the public facade above and
the result's `method_family`, `method_version`, `calculation_contract`,
`support_status`, `scope_status`, input summary, geometry, movement flow map,
capacity fields, status/reason, assumptions, warnings, and source references.

Phase 13.3 may build a single-page worksheet only on that version-pinned API;
it must preserve the explicit geometry/provenance inputs, show null prediction
semantics for HCM handoff/capacity failure, and may not expose `hcm_7_1` until
its separate qualification gate passes.
