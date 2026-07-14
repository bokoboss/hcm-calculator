# Two-Lane Highway Phase 3 implementation specification

> **Final annotation:** Phase 5 release qualification supersedes this phase specification's provisional scope statements; see `two_lane_phase_5_release_qualification.md`.

## Authority and boundary

Phase 3 implements HCM7 Chapter 15 Passing Lane Steps 2, 4--10 within the
Exhibit 15-10 length ranges and Exhibit 15-11 Classes 1--5. The calculation
authority is `local_references/HCM7 CH15 Two-Lane HW Motorized.pdf`: Exhibit
15-5 (capacity), Exhibits 15-12--15-29 (Step 4--7 coefficients), Eq. 15-24
through Eq. 15-34 (Passing Lane midpoint measures), and Eq. 15-36 through
Eq. 15-38 (downstream adjustment). Chapter 26 Examples 3 and 4 remain
published regression evidence, not method availability gates.

| Area | HCM mapping | Audited result | Guardrail |
| --- | --- | --- | --- |
| Applicability | Exhibits 15-10, 15-11 | submitted length, range, vertical class and direction | no clamping; Classes 1--5 only |
| Capacity | Exhibit 15-5 | total Passing Lane merge-point capacity, d/c and exceeded flag | no flow capping or redistribution |
| Step 7a--b | Eq. 15-24--15-30 | total HV, lane flow, lane HV count and percentage | flow/HV conservation and finite bounded values |
| Step 7c | Eq. 15-31--15-33 | lane initial and midpoint speeds, differential | positive finite speeds |
| Step 7d / 8 | Step 6 Passing Lane tables; Eq. 15-34 | lane PF and components; **Passing Lane midpoint follower density** | lane-specific Exhibit 15-5 capacity selected by lane HV% |
| Step 9 | Eq. 15-36--15-38 | upstream identity, entering PF, distance, improvements, unadjusted/adjusted density | closest upstream lane only; no extrapolation past effective length |

## Context model

`calculate_sequence()` accepts ordered segment contexts. `passing_lane_role` is
one of `none`, `passing_lane`, or `downstream_affected`. A Passing Lane role
must have a Passing Lane segment and a preceding ordinary segment (the entering
PF source). A downstream role must have an active preceding Passing Lane. A
Passing Lane cannot be downstream affected. A second Passing Lane resets the
closest-upstream context. An explicit `none` ends the opt-in context, preventing
an adjustment from being silently propagated.

Downstream distance is the HCM `DownstreamDistance`: from the start of the
Passing Lane to the downstream segment endpoint. Effective length is the lesser
of the Eq. 15-36 PF-improvement-zero distance and the distance where density
reaches 95% of the condition entering the Passing Lane. A valid downstream
context beyond that length returns `downstream_adjustment_applied=false` with a
reason; it does not use a decayed or extrapolated formula.

## Supported and deliberately unsupported behavior

A standalone Passing Lane returns lane-specific midpoint measures and LOS based
on Eq. 15-34, with an explicit warning that it is not a downstream or facility
result. Explicit ordered sequence analysis supports Step 9. Step 11 aggregation,
arbitrary UI facility editing, overlapping-lane interaction, reliability, and
automatic segmentation remain Phase 4/5 work.
