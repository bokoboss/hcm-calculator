# Phase 7.1 Reference Audit

## Scope and sources

This audit preceded Phase 8 work. Licensed local references were read in place, text-extracted for navigation, and visually inspected for every implemented equation and table. No PDF, page image, or large source extract is committed.

| Local file | Edition/material | Audited chapters, pages, equations, exhibits, and examples |
| --- | --- | --- |
| `HCM 7th.pdf` | HCM 7th Edition | Ch. 12 pp. 12-9--12-39; Ch. 15 motorized method; Ch. 26 pp. 26-1--26-14 and examples |
| `HCM7 CH12 Basic Freeway and Mulilane Highway Segments.pdf` | HCM7 Ch. 12 extract | Eqs. 12-1--12-11; Exhibits 12-6, 12-15, 12-18, 12-20--12-28 |
| `HCM7 CH15 Two-Lane HW Motorized.pdf` | HCM7 Ch. 15 extract | Eqs. 15-1--15-39; Exhibits 15-1--15-29 |
| `HCM7 CH26 Multilane HW EX Problems.pdf` | HCM7 Ch. 26 extract | Example Problem 4, pp. 26-38--26-40 |
| `HCM7 CH26 Two-Lane HW EX Problems.pdf` | HCM7 Ch. 26 extract | Example Problems 1--4, pp. 26-54--26-97 |
| `7 Two-Lane Highway Segment Analysis Methodology _ Reliability and Quality of Service Evaluation Methods for Rural Highways_ A Guide _ The National Academies Press.pdf` | National Academies guide | Independent Chapter 15 methodology context |

Mathematical pages and tables were rendered and visually checked; this included Exhibit 12-22 and every row/column of Exhibits 12-26--12-28. Values were cross-checked for units, neighboring cells, monotonic trends, and Chapter 26 Example Problem 4.

## Corroborating public sources

The local licensed HCM is the governing methodology. Public primary sources were used only to corroborate interpretation:

- [National Academies HCM Edition 7.1 chapter release](https://nap.nationalacademies.org/resource/26432/Highway_Capacity_Manual_Edition_7.1_Chapters.pdf)
- [FHWA Traffic Analysis Toolbox guidance](https://ops.fhwa.dot.gov/publications/fhwahop08054/sect4.htm)
- [FHWA Traffic Analysis Toolbox Volume III](https://ops.fhwa.dot.gov/trafficanalysistools/tat_vol3/sect6.htm)
- [FHWA freight operations technical report](https://ops.fhwa.dot.gov/freight/sw/map21tswstudy/ctsw/linkage/02modal_shift.htm)

## Findings and actions

| Classification | Finding and correction / boundary | Governing reference |
| --- | --- | --- |
| Confirmed methodology defect | Multilane required an externally supplied PCE even though the local HCM supplies the applicable tables. Added internal general-terrain and specific-grade PCE workflow with provenance, printed truck mixes, interpolation, and override bypass. | Eq. 12-10; Exhibits 12-25--12-28 |
| Confirmed methodology defect | Estimated divided-median FFS was rejected because no left clearance input existed. Added optional canonical left-side clearance; Eq. 12-4 and Exhibit 12-22 now apply correctly. | Eqs. 12-3, 12-4; Exhibits 12-22--12-24 |
| Boundary defect | Basic Freeway generated capacity-point speed/density after demand exceeded capacity. It now reports LOS F with no predicted speed or density. | Ch. 12 Step 5; Eq. 12-11; Exhibit 12-15 |
| Shared-validation defect | Basic Freeway numeric helper accepted booleans through Python coercion. It now rejects them. | Project typed-input contract |
| Non-defect limitation | Estimated Multilane FFS remains two or three lanes per direction only; Exhibit 12-22 supplies four- and six-lane tables only. Wider cases require measured FFS. | Exhibit 12-22 |
| Unresolved reference ambiguity | Specific-grade PCE accepts only the three printed SUT/TT mixtures and printed grade/length ranges. The terminal `>25%` heading is not a numeric interpolation endpoint, so internal lookup is bounded at 20% total heavy vehicles; above that an external PCE is required. | Exhibits 12-26--12-28 |
| Unresolved reference ambiguity | Chapter 12 states no multilane speed-flow CAF adjustment is available, while Chapter 26 Section 4 presents driver-population SAF/CAF guidance for freeway or multilane highways. The bounded method retains default 1.0 and rejects user adjustment. | Ch. 12 p. 12-33; Ch. 26 pp. 26-1, 26-14 |

## PCE and FFS decisions

- General terrain uses Exhibit 12-25: level `E_T = 2.0`, rolling `E_T = 3.0`.
- Specific grade uses the printed fixed 30/70, 50/50, or 70/30 SUT/TT PCE exhibit; total heavy-vehicle percentage excludes passenger cars and is applied once in Eq. 12-10.
- Interpolation is linear only between printed numeric cells. The final `>25%` table heading is not a numeric interpolation endpoint, so internal lookup is intentionally bounded at 20% total heavy vehicles; higher values require an external PCE.
- Downgrades below -2% use the -2% row, exactly as directed in Chapter 26 Example Problem 4. Grades above 6%, sparse unsupported grade-length cells, and unprinted truck mixes are rejected.
- A supplied `passenger_car_equivalent` is a controlled external override. Internal lookup is bypassed and reported.
- Undivided and TWLTL medians use 6 ft on the left; divided medians require explicitly supplied left and right clearances. Clearances greater than 6 ft are normalized to the HCM maximum.

## Regression evidence and changed behavior

Chapter 26 Example Problem 4 remains reproduced by internal lookup: eastbound PCE 2.24, flow about 896 pc/h/ln, density about 18.1 pc/mi/ln, LOS C; westbound PCE 3.97, flow about 980 pc/h/ln, density about 18.8 pc/mi/ln, LOS C. The fixture no longer injects PCE values, so it cannot be a runtime example branch.

The only changed historical result is Basic Freeway above capacity: the old result synthesized speed and density at the capacity point; the corrected result returns `LOS F`, `mean_speed_mph = None`, and `density_pc_mi_ln = None`.

## Tests and Phase 8 implication

Tests cover independent Eq. 12-10 calculations, every stored PCE row shape, visually reviewed sentinel cells, interpolation, no extrapolation, downgrade handling, divided medians, LOS boundaries, and above-capacity handling. Existing Ch. 26 examples remain regression evidence, not calculation branches.

Phase 8 must preserve PCE provenance and absent speed/density for failures. It must not claim support for unprinted truck mixes, wide estimated-FFS geometries, mixed-flow modeling, or the unresolved driver-population adjustment.
