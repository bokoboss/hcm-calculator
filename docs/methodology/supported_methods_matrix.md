# Supported methods matrix

This is the authoritative product-scope matrix for the qualified v0.6
release. It describes the implemented calculator contract, not all HCM
capabilities. A missing capability is not represented as a zero-valued result.

| Method | Analysis unit | FFS modes | Heavy-vehicle / PCE modes | Grade / terrain support | Capacity and above-capacity behavior | Primary LOS measure | Save / load and exports | Major exclusions | Latest qualified release |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Two-Lane Highway Segment | One guarded Chapter 15 segment | Method-specific Chapter 15 speed path; no separate measured/estimated FFS selector | Implemented Chapter 15 motorized-vehicle adjustments only | Guarded level, validated nonlevel, and supported horizontal-curve paths | Method-specific capacity checks; no unsupported oversaturated prediction is created | Follower density (`fol/mi/ln` or `fol/km/ln`) with ATS and percent followers | Project JSON; JSON, CSV, Excel, Markdown, and report JSON when current | Arbitrary Chapter 15 combinations, unsupported curve/grade combinations, corridor and reliability analysis | v0.5 |
| Two-Lane Highway Facility | Ordered, guarded multi-segment Chapter 15 facility | Segment-method inputs; facility result is not a segment result | Implemented Chapter 15 segment adjustments aggregated through the guarded facility workflow | Example-backed level and mountainous facility paths, including supported passing-lane/downstream contexts | Facility aggregation only; unsupported combinations are rejected | Facility follower density (`fol/mi/ln` or `fol/km/ln`) | Project JSON; JSON, CSV, Excel, Markdown, and report JSON when current | General arbitrary facility composition, corridor/reliability analysis, unsupported segment order or context | v0.5 |
| Multilane Highway Segment | One direction, one Chapter 12 Multilane Highway Segment | Measured FFS or estimated FFS; estimated mode supports two or three lanes/direction | Internal printed-table PCE lookup or external auditable PCE override | Level, rolling, and bounded printed specific-grade PCE domains | At capacity is calculated. Above capacity reports LOS F and capacity failure; mean speed and density are **Not predicted** | Density (`pc/mi/ln` or `pc/km/ln`) | Project JSON; JSON, CSV, Excel, Markdown, and report JSON when current | Basic freeway, ramps, weaving, merge/diverge, managed lanes, work zones, reliability, facility/corridor analysis, table extrapolation | v0.5 |
| Basic Freeway Segment | One direction, one uninterrupted-flow Chapter 12 Basic Freeway Segment | Measured FFS or estimated FFS | Internal level, rolling, and printed specific-grade PCE lookup, or external auditable PCE override; governed SAF/CAF and driver-population inputs | Level, rolling, and bounded printed specific-grade PCE domains; mountainous and mixed-flow domains rejected | At capacity is calculated. Above capacity reports LOS F and capacity failure; mean speed and density are **Not predicted** | Density (`pc/mi/ln` or `pc/km/ln`) | Project JSON; JSON, CSV, Excel, Markdown, and report JSON when current | Freeway facilities, ramps, weaving, merge/diverge, managed lanes, work zones, reliability, corridor analysis, queue/delay/travel-time prediction | v0.5 |
| Freeway Weaving Segment | Isolated HCM 7.0 Chapter 13 operational freeway segment | Measured FFS or qualified Chapter 12 estimated FFS | Common segment-level level/rolling PCE and `fHV`; HCM base SAF/CAF only | Level or rolling general terrain | Only unrounded `v/c > 1.00` is above capacity (LOS F, speed/density **Not predicted**). `LS >= LMAX` is a Chapter 12/14 handoff with no LOS. | Density (`pc/mi/ln` or `pc/km/ln`) when predicted | Version-pinned project JSON; JSON, CSV, Excel, Markdown, and report JSON when current | HCM 7.1, C-D/multilane weaving, Design/Sensitivity, overlapping weaves, queues, managed lanes, signal/ramp control, grade/truck-mix paths, and automatic geometry derivation | v0.6 |
| Freeway Merge Segment | Isolated HCM 7.0 Chapter 14 one-lane right-side on-ramp operational segment | Measured freeway FFS or qualified Chapter 12 estimated freeway FFS; explicit ramp FFS | Separate freeway and on-ramp level/rolling PCE and `fHV`; HCM base SAF/CAF only | Level or rolling general terrain | Capacity failure reports LOS F with capacity and `v/c`; speed/density **Not predicted**. Maximum desirable influence flow is warning-only unless capacity also fails. | Density (`pc/mi/ln` or `pc/km/ln`) when predicted | `manual_freeway_merge_segment_v1`; JSON, CSV, Excel, Markdown, and report JSON when current | HCM 7.1, adjacent ramps, left/two-lane ramps, lane additions, major merges, managed lanes, C-D roads, queues, ramp metering, work zones, and design/service-volume analysis | v0.7 |
| Freeway Diverge Segment | Isolated HCM 7.0 Chapter 14 one-lane right-side off-ramp operational segment | Measured freeway FFS or qualified Chapter 12 estimated freeway FFS; explicit ramp FFS | Separate freeway and off-ramp level/rolling PCE and `fHV`; HCM base SAF/CAF only | Level or rolling general terrain | Capacity failure reports LOS F with capacity and `v/c`; speed/density **Not predicted**. Maximum desirable influence flow is warning-only unless capacity also fails. | Density (`pc/mi/ln` or `pc/km/ln`) when predicted | `manual_freeway_diverge_segment_v1`; JSON, CSV, Excel, Markdown, and report JSON when current | HCM 7.1, adjacent ramps, left/two-lane ramps, lane drops, option lanes, major diverges, managed lanes, C-D roads, queues, ramp metering, work zones, and design/service-volume analysis | v0.7 |

## Thai/English presentation

All active calculators support English and Thai presentation. Locale is not an
engineering input: canonical method values, normalized payloads, fingerprints,
and qualified results remain language-independent. Project schema 1.2 may hold
optional presentation metadata, while JSON retains canonical machine keys. See
the [localization architecture](../localization/localization_architecture.md).

## Shared product contract

- All calculators use a compact single-page worksheet: setup, roadway/geometry,
  traffic, heavy-vehicle controls, applicable advanced controls, calculation,
  results, audit details, and save/export actions.
- A result is current only when its effective normalized inputs, method
  identifier, and input contract match. Hidden inactive controls are normalized
  to non-operative values and cannot make a result stale.
- Save/load retains inputs in the selected display units and stores
  engine-native normalized inputs. A migrated or incompatible result is clearly
  identified; a result requiring recalculation cannot be exported.
- Reports are rendered from an existing engine result. JSON, CSV, Excel,
  Markdown, and report JSON retain assumptions, warnings, limitations, units,
  provenance/audit context, and null semantics. `None` is rendered as blank or
  **Not predicted**, never as zero.

## Terminology decisions

| Canonical label | Use | Deliberate distinction |
| --- | --- | --- |
| Analysis direction | Directional traffic inputs and segment scope | Do not imply a two-direction facility output where none exists. |
| Number of lanes | Lanes in the analysis direction | Always show the unitless count. |
| Demand volume | Input volume in `veh/h` | Distinct from demand flow rate in `pc/h/ln`. |
| Peak-hour factor | Input factor | Unitless. |
| Heavy vehicles | Input percentage | PCE source and lookup provenance remain separate. |
| Measured FFS / Estimated FFS | FFS-source mode selector | Base FFS, pre-adjustment FFS, adjusted FFS, and mean speed are never collapsed. |
| Capacity | Capacity in `pc/h/ln` | Base and adjusted capacity remain separately named where the method has both. |
| Demand-to-capacity ratio | Dimensionless capacity check | Distinct from capacity status. |
| Mean speed | Multilane/Freeway predicted speed in `mi/h` or `km/h` | Above capacity is **Not predicted**. |
| Density | Multilane/Freeway `pc/mi/ln` or `pc/km/ln` | Not used to label Two-Lane follower density. |
| Follower density | Two-Lane `fol/mi/ln` or `fol/km/ln` | Never labeled ordinary density. |
| Percent followers | Two-Lane percent | Never substituted for follower density. |
| Capacity status | Within capacity or demand exceeds capacity | Above capacity is not a software failure. |
| Assumptions, warnings, limitations, references | Result and export context | Assumptions explain applied conditions; warnings and limitations do not imply calculation failure. |

