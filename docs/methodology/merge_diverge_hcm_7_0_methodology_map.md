# HCM 7.0 Merge and Diverge Methodology Map

## Phase Status

This is the Phase 14.1 source-audit and implementation-planning record for
freeway Merge Segment and Diverge Segment methods. It is not an implemented
engine specification by itself, and it does not add production coefficients,
runtime fixtures, UI workflows, persistence, exports, navigation, presets, or
image assets.

Starting `main` SHA: `e64baf5af17e0effd88c28f0f2cd9954c8c5ee8d`.

The governing HCM 7.0 source is the local licensed `local_references/HCM
7th.pdf`. It was inspected with targeted text navigation and visual review of
Chapter 14 pages, Chapter 28 examples, and referenced Chapter 12/13/23/26
dependencies. No licensed PDF, page image, OCR output, figure, table, or
substantial source narrative is committed.

## Source Ledger

| Source | Role | Location Used | Phase 14.1 Use |
| --- | --- | --- | --- |
| `local_references/HCM 7th.pdf` | Governing HCM 7.0 method | Chapter 14, printed pp. 14-i through 14-48, PDF pp. 568-617 | Merge/diverge definitions, core sequence, capacity checks, speed/density/LOS, extensions, limitations |
| `local_references/HCM 7th.pdf` | Compatible official examples | Chapter 28, printed pp. 28-i through 28-29, PDF pp. 1562-1592 | Operational example inventory and validation planning |
| `local_references/HCM 7th.pdf` | Shared freeway dependencies | Chapter 12 and Chapter 26; Chapter 13 handoff references; Chapter 23/38 queue-storage references | FFS, heavy vehicles, SAF/CAF, adjacent method boundaries |
| `docs/methodology/basic_freeway_phase_9_audit.md` and `src/hcmcalc/freeway/` | Existing qualified implementation evidence | Local repository | Reuse candidate for Chapter 12 FFS/PCE/capacity helpers only where source semantics match |
| `docs/methodology/weaving_*` and `src/hcmcalc/weaving/` | Existing qualified implementation evidence | Local repository | Version dispatch, geometry provenance, audit/null-semantics patterns |
| Official HCM 7.1 replacement chapters | Version-difference evidence only | National Academies HCM Edition 7.1 Chapters, November 2025 | Quarantine material differences from HCM 7.0 |
| Official McTrans/HCS material | Implementation/version evidence only | HCS version history, update news, knowledge base | Terminology, mixed-version warning, future UX/validation questions |

## Governing Chapter Identification

HCM 7.0 Merge Segment and Diverge Segment methods are governed jointly by
Chapter 14, **Freeway Merge and Diverge Segments**. The compatible official
examples are in Chapter 28, **Freeway Merges and Diverges: Supplemental**. The
Chapter 14 core method was calibrated for one-lane, right-side ramp-freeway
junctions; other cases are handled through Chapter 14 extensions and must not
be silently treated as core geometry.

Chapter 14 dependencies:

| Dependency | Method Effect |
| --- | --- |
| Chapter 12 | Freeway FFS estimation, base freeway capacity, heavy-vehicle/PCE foundations, driver population inputs where applicable |
| Chapter 10 and Chapter 11 | Freeway facility and reliability context; oversaturated/queue behavior outside isolated single-segment prediction |
| Chapter 13 | Weaving handoff when ramp influence areas form a weaving segment or overlap a weaving segment |
| Chapter 23 and Chapter 38 | Ramp-terminal queue storage and network spillback checks outside the isolated method |
| Chapter 26 | Supplemental examples and capacity/default guidance referenced by Chapter 14 |

## Shared HCM 7.0 Operational Frame

Both Merge and Diverge are isolated ramp-freeway junction methods whose service
measure is density in the 1,500-ft ramp influence area for stable LOS A-E. LOS F
is capacity-failure status, not a density-threshold extrapolation. The ramp
influence area is downstream of an on-ramp merge point and upstream of an
off-ramp diverge point. For right-side ramps, the influence area involves Lanes 1
and 2 plus the acceleration or deceleration lane where present; for left-side
ramps, the two leftmost lanes are used through the extension procedure.

Core computational steps:

1. Specify geometric, traffic, FFS, heavy-vehicle, PHF, ramp, adjacent-ramp, and
   adjustment-factor inputs.
2. Convert demand volumes to passenger-car flow rates under equivalent ideal
   conditions with HCM 7.0 Equation 14-1 and the Chapter 12 heavy-vehicle path.
3. Estimate the flow in the two ramp-influence freeway lanes immediately
   upstream of the ramp influence area, using the merge-specific or
   diverge-specific lane-distribution procedure.
4. Check capacities for the freeway checkpoint, ramp roadway, and maximum
   desirable flow entering the ramp influence area.
5. For stable cases only, estimate density in the ramp influence area and assign
   LOS from Exhibit 14-3.
6. Optionally estimate speed in the ramp influence area, outer lanes, and all
   lanes using the speed exhibits, but only for stable LOS A-E.

All flow values in the operational equations are in `pc/h` unless explicitly a
prevailing `veh/h` capacity after adjustment. The future engine must preserve
both raw observed volumes and converted passenger-car flow rates.

## Merge Segment Sequence

First-release Merge means an isolated one-lane, right-side on-ramp to a
general-purpose freeway, analyzed as an operational segment under HCM 7.0
Chapter 14 core methodology.

| ID | Step | HCM Location | Inputs and Units | Branches / Bounds | Output / Audit Requirement | Implementation Risk |
| --- | --- | --- | --- | --- | --- | --- |
| M14-001 | Scope and facility check | Ch. 14 pp. 14-1 through 14-10 | freeway/ramp facility type; ramp side; ramp lanes; segment relationship | Core is one-lane right-side ramp-freeway junction; C-D/multilane use is approximate and excluded from first release | `facility_type`, `analysis_type`, `scope_status` | HCS can expose highway/C-D options, but they are not first-release authority |
| M14-002 | Influence area | Ch. 14 pp. 14-4 through 14-5; Exhibit 14-1 | ramp type and side | on-ramp influence area is downstream of merge; adjacent influence areas may overlap | influence-area geometry and overlap note | Do not infer influence direction from a diagram selector |
| M14-003 | Input data | Ch. 14 pp. 14-10 through 14-12; Exhibit 14-4 and 14-5 | freeway FFS 55-75 mi/h; 2-5 lanes per direction; terrain; heavy vehicles; upstream freeway demand; on-ramp demand; PHF <= 1.0; acceleration length; ramp FFS; adjacent ramp data | first release should qualify only 2-4 freeway lanes, one ramp lane, right-side, level/rolling general terrain until examples/boundaries prove more | normalized inputs with provenance | Chapter permits broader domains than example-backed first-release scope |
| M14-004 | Demand conversion | Ch. 14 p. 14-15; Eq. 14-1 | `V_F`, `V_R`, PHF, `fHV`, driver population | separate component demands may have separate PHF/HV paths | `vF`, `vR`, `fHV` records | Existing freeway helper assumes one segment input; ramp and freeway components need explicit provenance |
| M14-005 | Merge lane distribution | Ch. 14 pp. 14-17 through 14-18; Exhibit 14-8; Eqs. 14-2 through 14-7 | freeway lanes, `vF`, `vR`, adjacent off-ramp demand/spacing when applicable, ramp FFS where needed | four-lane: all flow in influence lanes; six-lane has isolated/upstream/downstream off-ramp branches and equilibrium distance checks; eight-lane has ramp-demand/ramp-FFS branch | `PFM`, selected equation/exhibit row, `v12`, adjacent-ramp decision | Adjacent on-ramps are ignored for merge lane distribution; adjacent off-ramps are not |
| M14-006 | Lane-distribution reasonableness | Ch. 14 pp. 14-20 through 14-21; Eqs. 14-14 through 14-19 | `vF`, `v12`, lane count | no outer-lane check for four-lane freeways; six- and eight-lane freeways adjust `v12` when outer-lane checks fail | original and adjusted `v12` with governing reason | Easy to apply six-lane adjustment to eight-lane or vice versa |
| M14-007 | Capacity checks | Ch. 14 pp. 14-22 through 14-25; Exhibits 14-10 and 14-12; Eq. 14-21 | downstream freeway demand `vFO = vF + vR`, on-ramp demand, `vR12 = v12 + vR`, freeway/ramp FFS, CAF | downstream freeway capacity and ramp roadway capacity failures produce LOS F; maximum desirable influence-area flow exceedance is warning/interpretation, not automatic LOS F | capacity candidates, adjusted capacity, unrounded `v/c`, status | Must not turn maximum desirable flow exceedance into capacity failure |
| M14-008 | Density and LOS | Ch. 14 pp. 14-25 through 14-26; Eq. 14-22; Exhibit 14-3 | `vR`, `v12`, `LA` | stable operations only | merge influence density `DM`, LOS A-E | Above-capacity density is not predicted |
| M14-009 | Speed | Ch. 14 pp. 14-26 through 14-29; Exhibits 14-13 and 14-15 | freeway FFS, ramp FFS, SAF, `LA`, `vR12`, `v12`, outer-lane flow | stable operations only; merge speed does not exceed FFS | ramp-influence speed, outer-lane speed, all-lane average speed | Speed is optional but needed for facility integration; do not compute when LOS F |
| M14-010 | Extensions | Ch. 14 pp. 14-30 through 14-36 | lane addition, two-lane on-ramp, left-side ramp, 10-lane freeway, major merge, managed lane | first release excludes these except as documented unsupported geometry; lane additions route to Chapter 12 | unsupported-scope notes and future image subtypes | Two-lane ramps and left-side ramps have modified inputs, not a simple boolean |

## Diverge Segment Sequence

First-release Diverge means an isolated one-lane, right-side off-ramp from a
general-purpose freeway, analyzed as an operational segment under HCM 7.0
Chapter 14 core methodology.

| ID | Step | HCM Location | Inputs and Units | Branches / Bounds | Output / Audit Requirement | Implementation Risk |
| --- | --- | --- | --- | --- | --- | --- |
| D14-001 | Scope and facility check | Ch. 14 pp. 14-1 through 14-10 | freeway/ramp facility type; ramp side; ramp lanes; segment relationship | Core is one-lane right-side ramp-freeway junction; C-D/multilane approximate branch excluded | `facility_type`, `analysis_type`, `scope_status` | Diverge cannot inherit merge scope because off-ramp queue behavior differs |
| D14-002 | Influence area | Ch. 14 pp. 14-4 through 14-5; Exhibit 14-1 | ramp type and side | off-ramp influence area is upstream of diverge; overlapping influence areas use the worse operating result | influence-area geometry and overlap note | Wrong influence direction corrupts adjacent-ramp interpretation |
| D14-003 | Input data | Ch. 14 pp. 14-10 through 14-12; Exhibit 14-4 and 14-5 | upstream freeway demand, off-ramp demand, continuing freeway demand, freeway/ramp FFS, `LD`, ramp FFS, PHF/HV, adjacent ramps | first release should qualify only 2-4 freeway lanes, one ramp lane, right-side, level/rolling general terrain until examples/boundaries prove more | normalized inputs with provenance | Continuing freeway flow must be derived and retained, not ignored |
| D14-004 | Demand conversion | Ch. 14 p. 14-15; Eq. 14-1 | `V_F`, `V_R`, PHF, `fHV`, driver population | separate component demand paths allowed | `vF`, `vR`, `vFO = vF - vR` | Off-ramp demand is part of `vF` upstream, unlike merge ramp demand |
| D14-005 | Diverge lane distribution | Ch. 14 pp. 14-18 through 14-20; Exhibit 14-9; Eqs. 14-8 through 14-13 | freeway lanes, upstream freeway demand, off-ramp demand, adjacent upstream on-ramp/downstream off-ramp data | four-lane: all flow in influence lanes; six-lane has isolated/upstream-on/downstream-off branches plus calibration cap; eight-lane constant branch | `PFD`, selected equation/exhibit row, `v12`, adjacent-ramp decision | Adjacent upstream off-ramps and downstream on-ramps are ignored; the opposite pair may matter |
| D14-006 | Lane-distribution reasonableness | Ch. 14 pp. 14-20 through 14-21; Eqs. 14-14 through 14-19 | `vF`, `v12`, lane count | same adjustment framework as merge, after diverge-specific `v12` prediction | original and adjusted `v12` with governing reason | Adjustment equations are shared only after `v12` semantics are confirmed |
| D14-007 | Capacity checks | Ch. 14 pp. 14-22 through 14-25; Exhibits 14-10 and 14-12; Eq. 14-21 | upstream freeway demand, downstream freeway demand where lane drop/add applies, off-ramp demand, `v12`, freeway/ramp FFS, CAF | upstream freeway and off-ramp capacity failures produce LOS F; maximum desirable `v12` exceedance is warning/interpretation, not automatic LOS F | capacity candidates, adjusted capacity, unrounded `v/c`, status | Off-ramp/ramp-terminal queue risk must be warning and external-method handoff unless ramp roadway capacity itself fails |
| D14-008 | Density and LOS | Ch. 14 pp. 14-25 through 14-26; Eq. 14-23; Exhibit 14-3 | `v12`, `LD` | stable operations only | diverge influence density `DD`, LOS A-E | No separate `vR` density term because off-ramp flow is already in `v12` |
| D14-009 | Speed | Ch. 14 pp. 14-26 through 14-29; Exhibits 14-14 and 14-15 | freeway FFS, ramp FFS, SAF, `LD`, `vR`, `v12`, outer-lane flow | stable operations only; all-lane average speed capped at FFS | ramp-influence speed, outer-lane speed, all-lane average speed | Diverge outer-lane speed can exceed FFS before all-lane capping; merge logic is not symmetric |
| D14-010 | Extensions | Ch. 14 pp. 14-30 through 14-36 | lane drop, two-lane off-ramp, option lane, left-side ramp, major diverge, managed lane | first release excludes these except as documented unsupported geometry; lane drops route to Chapter 12 | unsupported-scope notes and future image subtypes | Two-lane off-ramp with option lane differs from two deceleration lanes |

## Capacity and Failure Semantics

| Case | Merge | Diverge | Future Result Semantics |
| --- | --- | --- | --- |
| Freeway capacity checkpoint | Downstream freeway after the on-ramp, plus upstream/downstream checks when lane additions are involved | Upstream freeway before the off-ramp, plus downstream checks when lane drops are involved | Failure if unrounded demand/capacity is greater than 1.00; LOS F; no speed/density prediction |
| Ramp roadway capacity | On-ramp demand checked, but failure mainly queues outside freeway | Off-ramp demand checked; failure is a common diverge failure mode and may spill back | Failure if ramp demand exceeds ramp roadway capacity; LOS F; external queue analysis note |
| Maximum desirable flow in influence area | `vR12` for merge | `v12` for diverge | Exceedance does not by itself assign LOS F; result should include warning that predictions may understate turbulence |
| Capacity adjustment | Chapter 14 Eq. 14-21 with CAF from governing source/default | Same | Preserve unadjusted and adjusted capacity and CAF provenance |
| Exact equality | Not a failure | Not a failure | `v/c == 1.00` remains stable for method continuation unless HCM-specific example proves otherwise |
| Above capacity | No stable speed/density/LOS A-E prediction | No stable speed/density/LOS A-E prediction | LOS F capacity failure; speed/density `None`/Not predicted; queues/delay outside scope |

## Shared Versus Method-Specific Logic

Potentially shared, after tests prove source identity:

- version dispatch and known-unqualified version guard;
- demand conversion wrapper preserving per-component PHF/HV provenance;
- Chapter 12 measured/estimated FFS and general-terrain PCE helpers;
- capacity candidate/result model and `v/c` audit object;
- lane-distribution reasonableness adjustment after method-specific `v12`
  prediction;
- SAF/CAF provenance and default handling;
- audit/result/null-semantics patterns from Basic Freeway and Weaving.

Must remain method-specific:

- influence-area direction and geometry meaning;
- movement inputs and derived downstream/continuing flow;
- `PFM` versus `PFD` branch selection;
- adjacent-ramp significance rules;
- density equations and variable meanings;
- speed exhibits and capping details;
- extension handling for two-lane ramps, option lanes, lane additions/drops, and
  major merge/diverge areas;
- warning text for off-ramp queue/spillback risk.

## Official Example Inventory

Chapter 28 contains five HCM 7.0 examples. Phase 14.2 should transcribe only
operational examples as runtime fixtures after a second visual review.

| Example | Method | Pages | Geometry | Phase 14.2 Fixture Suitability |
| --- | --- | --- | --- | --- |
| 1 | Merge | pp. 28-2 through 28-4, PDF pp. 1565-1567 | isolated one-lane right-side on-ramp to four-lane freeway | Strong core merge fixture; includes demand conversion, four-lane lane distribution, capacity checks, density, LOS, speed |
| 2 | Diverge | pp. 28-4 through 28-9, PDF pp. 1568-1572 | two adjacent one-lane right-side off-ramps on six-lane freeway | Strong diverge fixture; includes adjacent-ramp equilibrium and overlap treatment |
| 3 | Merge and Diverge pair | pp. 28-9 through 28-14, PDF pp. 1572-1577 | one-lane on-ramp followed by one-lane off-ramp on eight-lane freeway | Strong combined fixture; exercises eight-lane reasonableness adjustment and overlap |
| 4 | Merge special case | pp. 28-14 through 28-17, PDF pp. 1578-1580 | single-lane left-side on-ramp on six-lane freeway | Special-case fixture only after left-side support is explicitly qualified |
| 5 | Merge service volumes | pp. 28-17 through 28-21, PDF pp. 1581-1584 | isolated on-ramp on six-lane freeway | Not a first engine regression; service-flow/design planning evidence only |
| Alternative tool problems | Out of core scope | pp. 28-22 through 28-29, PDF pp. 1585-1592 | ramp metering and HOV-lane simulation | Exclusion evidence; no HCM engine fixture |

## Independent Validation Plan

Phase 14.2 must add non-example cases for both methods:

| Family | Required Cases |
| --- | --- |
| Merge | low-demand isolated on-ramp; moderate merge; near-capacity merge; downstream-freeway-capacity-governed case; ramp-capacity-governed case; maximum-desirable-`vR12` warning case; short and long acceleration lanes; exact-capacity case; above-capacity case; lane-addition unsupported or handoff case |
| Diverge | low off-ramp flow; moderate diverge; near-capacity diverge; upstream-freeway-capacity-governed case; off-ramp-capacity-governed case; maximum-desirable-`v12` warning case; short and long deceleration lanes; exact-capacity case; above-capacity case; lane-drop/option-lane unsupported or handoff case |
| Shared boundaries | every lane-count branch; every ramp FFS capacity-bin boundary; every FFS capacity-bin boundary; PHF invalid/one; nonfinite and negative input rejection; adjacent-ramp distance equality behavior; HCM 7.1 evidence rejected on HCM 7.0 path |

## Implementation Readiness Notes

Phase 14.2 may proceed only after every Chapter 28 operational example input,
intermediate value, and rounded output is independently transcribed into a
reviewed inventory. The first implementation PR should implement Merge and
Diverge together because the governing source is joint, but with separate
method packages and separate support contracts to avoid symmetric-equation
mistakes.
