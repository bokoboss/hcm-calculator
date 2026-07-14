# Two-Lane Highway Phase 2 implementation specification

> **Final annotation:** Phase 5 release qualification supersedes this phase specification's provisional scope statements; see `two_lane_phase_5_release_qualification.md`.

## Authority and scope

This specification implements the HCM 7 Chapter 15 single homogeneous segment
sequence for **Passing Constrained** and **Passing Zone** segments.  It uses the
local `HCM7 CH15 Two-Lane HW Motorized.pdf` as the calculation authority and
the local Chapter 26 examples only as published regression evidence.  NCHRP
Research Report 1102 Chapter 7 remains provenance for the method lineage, not
a substitute for an HCM table.

Phase 2 includes Steps 1--6, 8, and 10.  Passing Lane Steps 7--9, downstream
passing-lane effects, and facility aggregation remain out of scope.

| Step | Equation / exhibit | Inputs and rule | Output / audit |
| --- | --- | --- | --- |
| 1 | Exhibit 15-10 | Actual segment length must be within the inclusive range for segment type and Exhibit 15-11 class; never clamp. | submitted length, inclusive range, status, source |
| 2 | Eq. 15-1; Ch. 15 capacity text | `v_d=V/PHF`; Passing Constrained and Passing Zone use 1,700 veh/h/ln under base conditions. | submitted volume, PHF, demand, capacity, d/c, exceeded status |
| 3 | Exhibit 15-11 | Derive Class 1--5 and direction from analysis length and signed grade. | class, direction, table row/column |
| 4 | Eq. 15-2--15-6; Exhibit 15-12 | Class-indexed HV coefficient; lane 9--12 ft, shoulder 0--6 ft, HV 0--100%, nonnegative opposing flow. | BFFS, coefficient, all adjustments, FFS and references |
| 5a | Eq. 15-7--15-11; Exhibits 15-13, 15-15, 15-17, 15-19 | Passing Constrained/Zone coefficient set for derived Class 1--5. Passing Constrained uses 1,500 veh/h opposing flow; Passing Zone uses opposing volume/PHF. | b3, b4, m, p, tangent speed |
| 5b | Eq. 15-12--15-16; Exhibit 15-22 | One or more tangent/curve subsegments total the segment length; curve radius positive, superelevation nonnegative. Dash cells are tangents, not curve classes. | classifications, subsegment speeds, weighted speed |
| 6 | Eq. 15-17--15-23; Exhibits 15-24, 15-26, 15-28, 15-29 | Same Class 1--5 PC/PZ coefficients and Step 2 capacity. PFcap/PF25cap are constrained by the HCM equations before log fitting. | PFcap, PF25cap, m, p, PF, opposing-flow provenance |
| 8 | Eq. 15-35 | PC/PZ only: `FD=(PF/100)*v_d/S`; finite nonnegative values required. | FD, equation, inputs |
| 10 | Exhibit 15-6 | Use posted speed <50 or >=50 mph threshold group; at d/c >1, Chapter 15 states LOS F and detailed method is not applicable. | thresholds, density basis, LOS, capacity status |

## Supported envelope

| Combination | Phase 2 status |
| --- | --- |
| Passing Constrained, Classes 1--5, level or nonlevel, straight | Supported |
| Passing Zone, Classes 1--5, level or nonlevel, straight | Supported when opposing-direction volume is submitted |
| Passing Constrained or Passing Zone, level/nonlevel horizontal curves | Supported when complete valid subsegments are submitted; Eq. 15-12--15-16 are alignment adjustments to the Step 5 tangent calculation |
| Upgrade and downgrade | Supported through Exhibit 15-11 derived class/direction |
| Passing Lane, all general single-segment paths | UnsupportedScopeError (Phase 3) |
| Upstream/downstream passing-lane context or facility analysis | UnsupportedScopeError (Phase 3) |

Inputs outside Exhibit 15-10, invalid physical/numerical domains, and invalid
subsegments are invalid input (`HCMCalcError`) or explicit applicability scope
errors.  No Chapter 26 fixture or validation metadata authorizes a method
branch.  A demand above 1,700 veh/h/ln is not capped: it is reported with a
`capacity_exceeded` audit flag and LOS F per the Chapter 15 capacity discussion.

## Validation evidence

Published Chapter 26 Examples 1--4 are `published_reference_case` regression
evidence.  New synthetic cases are `method_conformance_case`: independently
calculated from the equations/tables above and never represented as published
examples.  Public support requires Exhibit 15-10/15-11 applicability, complete
table data, focused equation tests, and at least one such non-example case for
the supported path.
