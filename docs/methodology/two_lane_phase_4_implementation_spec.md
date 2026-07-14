# Two-Lane Highway Phase 4 — General Facility and Step 11

Related issue: #82

> **Final annotation:** Phase 5 release qualification supersedes this phase specification's provisional scope statements; see `two_lane_phase_5_release_qualification.md`.

## Authority and supported envelope

The facility calculation uses HCM7 Chapter 15 Steps 1–10 as implemented in
Phases 1–3 and Step 11, Eq. 15-39, for length-weighted facility aggregation.
The local Chapter 15 PDF is authoritative; Chapter 26 Examples 3 and 4 are
published regression evidence only.  The engine accepts an arbitrary nonempty,
explicitly ordered list of Passing Constrained, Passing Zone, and Passing Lane
segments that independently satisfy Exhibit 15-10 and the implemented
Step 1–10 domains.

Each segment has a unique stable `segment_id`; list order is the facility order
(an optional `segment_order` must match it exactly). Segment length is positive
and total facility length is the sum of segment lengths. There is no template
ID, fixed count, or fixture name in the engine input.

## Passing Lane and final segment measure

`passing_lane_role` is explicit: `passing_lane`, `downstream_affected`, or
`none`. A Passing Lane requires an entering preceding segment. A downstream
role requires an active upstream Passing Lane; an explicit `none` terminates
the opt-in context. A new Passing Lane resets the context. The Step 9 distance
is cumulative from the Passing Lane start to the affected segment endpoint;
outside the effective length no adjustment is applied. Overlapping or
contradictory roles are rejected.

The final density is Eq. 15-35 ordinarily, Eq. 15-34 midpoint density for a
Passing Lane, and Eq. 15-38 only for an explicitly adjusted downstream segment.
Unadjusted, midpoint, and adjusted values remain in segment audit output.

## Step 11

For every facility metric the denominator is total length. Average speed,
percent followers, and follower density each use their own audited numerator;
they are not derived from LOS letters. Facility LOS is determined from final
length-weighted follower density using Exhibit 15-6. Capacity is never capped
or excluded: each segment exposes capacity and demand/capacity ratio, while the
facility exposes a capacity-failure flag and the maximum-ratio critical segment.

The published Example 3/4 adapter explicitly requests the Chapter 26 displayed
one-decimal density convention only for regression comparability. General
facility inputs use unrounded calculated densities.

## Deliberately unsupported

Reliability, pedestrians/bicycles, automatic segmentation, passing-lane warrant
or geometric design, and overlapping Passing Lane interactions remain outside
the envelope. Invalid physical/numerical inputs and unsupported curve/Pasing
Lane combinations fail explicitly; they do not receive defaults or interpolation.

## Project/UI migration

`manual_facility_v0` remains a loader-compatible template project type. New
general facility projects use `manual_two_lane_facility_v1`; their complete
visible normalized segments, role/context, result fingerprint, audit values,
and result are persisted. Templates are optional starting values only.
