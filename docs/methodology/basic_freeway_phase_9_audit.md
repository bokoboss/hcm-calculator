# Basic Freeway Phase 9 Method Audit

## Supported calculation contract

The engine supports one direction and one uninterrupted Basic Freeway Segment under HCM7 Chapter 12. It accepts a measured FFS (without geometry adjustments) or an estimated FFS using Equation 12-2, Exhibits 12-20 and 12-21, and total ramp density. Measured FFS is a field-study input: Chapter 12 identifies low-to-moderate-flow observation conditions; collection design remains outside calculator scope.

The supported adjusted FFS range is 55--75 mi/h. Capacity is Equation 12-6, capped at 2,400 pc/h/ln, and CAF is applied once by Equation 12-8. SAF is applied once to FFS by Equation 12-5. Both default to 1.0 for base conditions. User-entered values are limited to `(0, 1]` as project governance, not represented as universally HCM-calibrated values; each needs provenance. The supported provenance values are `hcm_base_conditions`, `chapter_26_driver_population`, and `project_local_calibration`.

Chapter 26 Exhibit 26-9 is implemented as a driver-population category that requires its paired SAF/CAF values and provenance. The historical demand-flow driver-population factor is not applied: Chapter 26 states that the unified Chapter 12 procedure replaces it with the paired FFS and capacity adjustments. The retained `driver_population_factor = 1.0` result field is an audit compatibility marker only.

## Heavy vehicles and grade boundary

General terrain uses Exhibit 12-25 (level and rolling). Specific-grade support uses the printed 30/70, 50/50, and 70/30 SUT/TT grids in Exhibits 12-26--12-28 with interpolation only between numeric grade, length, and truck-percentage cells. The final `>25%` column is not treated as a numeric endpoint, so the internal path stops at 20% heavy vehicles. An externally supplied positive PCE with provenance bypasses internal lookup. Buses and RVs are classified with SUTs by Equation 12-10; no separate RV table is implied.

Mountainous terrain, grade/length combinations outside the printed grids, nonprinted truck mixes, and PCE extrapolation are rejected. The Chapter 12 text recommends a mixed-flow method for steep/high-truck conditions; that method is out of scope.

## Speed, LOS, and exclusions

Demand flow uses Equation 12-9 exactly once for volume, PHF, lanes, and heavy-vehicle factor. The speed-flow relationship follows Equation 12-1 and Exhibit 12-6: constant FFS through breakpoint, decreasing speed from breakpoint through capacity, and exact capacity at 45 pc/mi/ln. Density uses Equation 12-11 and LOS boundaries use Exhibit 12-15.

When demand exceeds adjusted capacity, the result is LOS F and an explicit capacity-failure status; it contains no speed or density prediction. Ramps as influence areas, merge/diverge, weaving, managed lanes, work zones, reliability, facility aggregation, queues, and oversaturated prediction are excluded.

## References inspected

Local licensed references were inspected in place and not copied: HCM7 Chapter 12 pp. 12-8--12-10, 12-19, and 12-27--12-39; Chapter 26 p. 26-14; and Chapter 26 Example Problem 1. Rendered pages were used to verify equation grouping, table headings, units, terminal categories, interpolation notes, and the above-capacity limitation. Public corroboration is limited to [the National Academies HCM 7.1 chapter release](https://nap.nationalacademies.org/resource/26432/Highway_Capacity_Manual_Edition_7.1_Chapters.pdf) and [FHWA Traffic Analysis Toolbox guidance](https://ops.fhwa.dot.gov/publications/fhwahop08054/sect4.htm); the local HCM remains the detailed authority.
