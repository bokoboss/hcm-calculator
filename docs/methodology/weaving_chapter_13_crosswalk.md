# HCM7 Chapter 13 Weaving Segment Methodology Crosswalk

## Scope, source hierarchy, and audit record

This is a Phase 13.1 reference inventory, not an implemented method or a
calculation specification approved for production.  It records the evidence a
Phase 2 implementation must preserve and the questions it must guard.  The
governing source is the user-owned **Highway Capacity Manual, Version 7.0**
(`local_references/HCM 7th.pdf`), Chapter 13, printed pp. 13-1--13-41, and
Chapter 27, printed pp. 27-1 onward.  The copy is HCM 7.0; it was inspected by
targeted text navigation and visual review of the equation, exhibit, figure,
footnote, and example pages listed below.  No portion of that source, page
image, or extracted text is committed.

Version alert: official HCM 7.1 material materially revises this procedure.
Accordingly, this crosswalk is explicitly **Version 7.0 only** and is not
authority to build a Version 7.1 engine.  A deliberate 7.1 retarget requires a
new governing-source audit, equations, examples, and scope contract.

The Chapter 13 method is a freeway weaving-segment method.  Chapter 12 is a
dependency only where Chapter 13 says so; existing Chapter 12 code is not
method authority.  The legacy `bokoboss/hcm7-weaving-segments` application is
secondary implementation evidence only.  The official corroborating records
consulted on 2026-07-15 were the [official National Academies HCM 7.1 chapter
release](https://nap.nationalacademies.org/resource/26432/Highway_Capacity_Manual_Edition_7.1_Chapters.pdf),
the [NCHRP Report 1038 proposed chapters](https://onlinepubs.trb.org/onlinepubs/nchrp/nchrp_rpt_1038Proposed.pdf),
and the National Academies record for [*Update of Highway Capacity Manual:
Merge, Diverge, and Weaving Methodologies*](https://nap.nationalacademies.org/catalog/27044/update-of-highway-capacity-manual-merge-diverge-and-weaving-methodologies).
They corroborate that future revisions exist; they do **not** replace the
locally inspected HCM 7.0 governing procedure.

Source ledger:

| Source | Edition/status | Exact material used | Inspection |
| --- | --- | --- | --- |
| `HCM 7th.pdf` | HCM 7.0, governing | Ch. 12 pp. 12-9--12-39; Ch. 13 pp. 13-1--13-41 (PDF pp. 526--566); Ch. 27 Examples 1--3, printed pp. 27-2--27-16 (PDF pp. 1521--1535) | text navigation plus visual equations/exhibits/examples |
| `HCM7 CH12 Basic Freeway and Mulilane Highway Segments.pdf` | HCM 7 extract, governing only for identified Ch. 12 dependencies | Ch. 12 FFS, demand, HV/PCE, SAF/CAF and capacity material | text and visual cross-check |
| NCHRP Report 1038 proposed chapters | primary institutional corroboration, not governing HCM 7.0 | proposed 7.1 Ch. 13/27 wording and LOS context | web/text review |
| `hcm7-weaving-segments` at `8bcdf89038329fbdc46dac286733d6d18f9f3504` | secondary only | implementation inventory and risk discovery | source review |

## McTrans/HCS implementation-reference evidence

McTrans/HCS is an implementation and UX reference, ranked below the governing
HCM 7.0 source.  It is not an equation, coefficient, threshold, or applicability
authority.  The ledger was accessed on 2026-07-15; no guide, screenshot,
report, extracted HTML, or proprietary HCS content is committed.

| McTrans source | HCS/version mapping | Relevant section | Evidence type | Finding classification and relation to HCM 7.0 | Contract effect |
| --- | --- | --- | --- | --- | --- |
| [HCS User Guide archive](https://mctrans.ce.ufl.edu/userguide/) and [2024 Freeways guide](https://mctranswordpresssa.blob.core.windows.net/uploads/2024/01/Freeways-User-Guide-2024.pdf) | HCS 2024, HCM 7.0-era; version inferred from the official history: 7.1 is added only in HCS 2025 | Freeways guide listing | method-version/source availability | `confirms_phase_1`: a versioned freeway guide exists, but it is not evidence for 7.1 behavior | v7.0 reference candidate only |
| [2025 Freeways guide](https://mctranswordpresssa.blob.core.windows.net/uploads/2024/10/HCS-2025-User-Guide-Freeways.pdf) | HCS 2025 / release 8.4: HCM 7 plus selectable HCM 7.1 single-segment method | Freeways release entry | method-version difference | `hcm_7_1_only` for its new merge/diverge/weave path; mixed-version guide | never use without explicit method selection |
| [2026 Freeways guide](https://mctranswordpresssa.blob.core.windows.net/uploads/2025/09/HCS-2026-User-Guide-Freeways.pdf) | HCS 2026; current product supports HCM 7 and 7.1 selection | contents: Freeway Weaving Segments, Chs. 13/27, operational/design/report sections | terminology, input/report behavior | `ux_reference_only`: guide structure is useful, but version selection remains mandatory | no numerical rule imported |
| [HCS version history](https://mctrans.ce.ufl.edu/highway-capacity-software-hcs/version-history/) | HCS 2023 implements 7th Edition; HCS 2025 release 8.4 adds HCM 7.1/NCHRP 07-26 for single merge/diverge/weave | HCS 2023; HCS 2025 release 8.4; later freeway notes | method-version difference, report behavior | `clarifies_phase_1`: a software version/year does not itself identify the procedure | add version/method pinning gate |
| [HCS 2026 update news](https://mctrans.ce.ufl.edu/highway-capacity-software-hcs/hcs-update-news/) | latest HCS can select HCM 7 or HCM 7.1 | “New methods – Freeway Segments (HCM 7.1)” | method-version difference, report behavior | `hcm_7_1_only`: 7.1 has a new approach and 35 pc/mi/ln capacity-density statement | explicit contamination control |
| [HCS knowledge base](https://mctrans.ce.ufl.edu/highway-capacity-software-hcs/knowledge-base/) | current HCS; individual tip does not state selected HCM method | “Multilane Highways Merge/Diverge and Weaving Segments” | applicability/UX | `hcs_software_specific`: HCS exposes “Highway or C-D Roadway”; its availability is not v7.0 release evidence | retain freeway-only scope |
| [HCS knowledge base](https://mctrans.ce.ufl.edu/highway-capacity-software-hcs/knowledge-base/) | current HCS; method version not identified | “Modeling Option Lanes in Freeway Weaves” | terminology, input coding | `clarifies_phase_1`: HCS names LC_RF, LC_FR and N_WL as separate lane-changing inputs | add explicit geometry-coding requirements |
| [HCS knowledge base](https://mctrans.ce.ufl.edu/highway-capacity-software-hcs/knowledge-base/) | current HCS, all-module feature | “Information Box” | validation behavior | `hcs_software_specific`: error/warning/info severity is UX evidence only | recommend analogous taxonomy, no auto-adjustment |
| [McTrans HCM page](https://mctrans.ce.ufl.edu/highway-capacity-software-hcs/order-hcm/) | HCS 2025 onward permits HCM 7 / 7.1 choice | “Beyond HCM 7th Edition” | method-version difference | `hcm_7_1_only`: HCM 7.1 chapters are a later method, including 35 pc/mi/ln capacity density | version selection required before Phase 2 |

### Version mapping and contamination control

The version history says HCS 2023 implements the seventh edition; the 2024
release contains Freeways changes but no listed HCM 7.1 weave method.  HCS 2025
release 8.4 explicitly adds HCM 7.1/NCHRP 07-26 single-segment merge, diverge,
and weaving analyses.  McTrans then states that the latest HCS allows the user
to choose HCM 7 or HCM 7.1.  Therefore HCS 2024 is usable only as a **v7.0-era
implementation reference**, HCS 2025/2026 documentation is mixed-version, and
no current-guide behavior is v7.0 evidence unless the selected method is
identified as HCM 7.

**Phase 2 contamination-control rule:** every weaving source, fixture, report
sample, screen observation, and test must carry `method_version = hcm_7_0`.
Reject or quarantine evidence labeled HCM 7.1, NCHRP 07-26, 35 pc/mi/ln,
“volume served,” queue/work-zone output, or an unspecified current-HCS method
until a reviewer maps it to the governing v7.0 equation/exhibit.  HCS version
year alone is insufficient, and HCS 2025/2026 dual-method screens/reports must
record the selected method before comparison.

### HCS observations and limits

HCS’s option-lane tip states that the inputs are: `LC_RF` (minimum
ramp-to-freeway lane changes), `LC_FR` (minimum freeway-to-ramp lane changes),
and `N_WL` (lanes from which a weaving maneuver can be completed with zero or
one lane change).  Its stated coding interpretation is that a freeway-to-ramp
exit through an option lane is not itself a lane change.  This clarifies an
implementation input convention; it does not change HCM 7.0 movement
definitions.  The tip does not establish a lane-edge versus centerline counting
rule, an `LC_RR` option-lane rule, an automatic `N_WL` derivation, or numerical
lane-count bounds.  Those remain `unresolved` pending an HCM-backed geometry
crosswalk.

Thus the future UI/model must collect a configuration diagram or structured
movement-to-destination lane information sufficient to enter `LC_RF`, `LC_FR`,
`LC_RR` when applicable, and `N_WL` independently.  Two sites with equal `N`
may legitimately have different lane-change inputs because an option lane
changes the available destination movement; neither HCS nor this project may
silently infer the values from lane count alone.

The HCS knowledge base says the software permits an isolated “Highway or C-D
Roadway” option and asks the user to match multilane FFS inputs.  That is
software/applicability evidence only.  It neither supersedes the v7.0 Chapter
13 approximation warning nor adds Chapter 27 validation evidence, so it has no
effect on the freeway-only first-release decision.

HCS’s general information box distinguishes errors (invalid results prevented),
warnings (software/HCM adjustment but results produced), and information
(defaults/optional inputs, normal results).  Use this as a UX taxonomy
reference only.  The future contract must not copy HCS automatic adjustment or
clipping: unknown or out-of-domain values remain input errors or unsupported
scope unless HCM explicitly authorizes normalization.  HCS release notes do
confirm a warning to use facility analysis when single-segment LOS is F, but do
not establish v7.0 speed/density output semantics.  The governing HCM null
behavior remains unchanged.

HCS documentation inspected here does not provide a version-qualified
movement-specific heavy-vehicle aggregation rule.  The HCS 2025 release note
that SAF and CAF are global inputs does not identify the selected method, so it
is excluded as software-release behavior rather than treated as HCM 7.0
evidence.  Accordingly, the Phase 1 common segment-level `fHV` decision remains
`confirms_phase_1` by absence of contrary governing evidence; it is not changed
by HCS UI capability.

| Crosswalk IDs | HCS implementation-evidence status | Effect |
| --- | --- | --- |
| W13-001, W13-007--009 | `clarifies_phase_1` for separate configuration/lane-change coding | collect geometry and LC/N_WL inputs explicitly |
| W13-004, W13-012--017 | `unresolved` for v7.0 HV/SAF/CAF aggregation | retain governing v7.0/common-fHV scope |
| W13-010--011 | `hcs_software_specific`/no v7.0 behavior proof | retain HCM LMAX handoff |
| W13-018, W13-022--023 | HCS 7.1/report behavior excluded; v7.0 HCS evidence incomplete | retain HCM LOS F/null semantics |
| W13-001, W13-024 | HCS C-D option is `hcs_software_specific` | no expansion beyond freeway-only |

## Verified operational sequence

For a supported freeway case, Phase 2 must implement the following sequence in
this order and retain each material intermediate with its source and native
unit.  The equations and exhibits below use the HCM's terminology; the source
shall be consulted directly for exact mathematical expression, rounding, and
table selection before coding.

1. Validate that the facility, period, configuration, geometry, traffic
   movements, and FFS/HV inputs lie in the Chapter 13 applicability envelope.
2. Identify FF, FR, RF, and RR movements; classify the segment as one-sided or
   two-sided; derive total, weaving, and nonweaving demand flows.
3. Convert each movement volume to passenger-car flow rate using Eq. 13-1 and
   the applicable Chapter 12 heavy-vehicle factor.  The first release uses one
   common, auditable segment vehicle mix because Chapter 13 does not define how
   differing movement-specific factors aggregate into its singular capacity
   factor; movement-specific capacity treatment is deferred rather than
   invented.
4. Obtain Chapter 12 freeway FFS and applicable driver-population adjustment
   inputs only by the route authorized in Chapter 13; preserve their source.
5. Compute volume ratio, minimum required lane changes, and maximum weaving
   length.  If `LS >= LMAX`, stop weaving analysis and direct the applicable
   movements to Chapter 14 merge/diverge and the remaining mainline to Chapter
   12; this is a method handoff, not a clipped calculation.
6. Determine the density-governed and, where applicable, weaving-flow-governed
   capacity; apply the authorized CAF and calculate demand/capacity.  A
   capacity failure stops speed/density prediction and produces LOS F.
7. For within-capacity cases, calculate weaving and nonweaving lane changes,
   using only the prescribed low/high branch or the expressly required
   interpolation interval.
8. Calculate weaving intensity, weaving and nonweaving speeds, weighted mean
   speed, density, and LOS.  Keep movement, lane-change, branch, and governing
   capacity evidence in the audit result.

## Equation and exhibit crosswalk

| Crosswalk ID | Method step | Input / constant / equation / exhibit | Governing HCM location | Native units | Applicability and bounds | Interpolation / extrapolation rule | Chapter 12 dependency | Required intermediate/output | Verification status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| W13-001 | Scope | Freeway weaving-segment definition/configurations | Ch. 13 pp. 13-3--13-8, Exs. 13-1--13-5 | — | freeway method; multilane/C-D treatment is approximate/extension material | none | facility classification | configuration, scope decision | confirmed |
| W13-002 | Period | Peak 15-min demand expressed as equivalent hourly rate | Ch. 13 p. 13-11 | veh/h | peak period of analysis hour | no inferred alternative period | demand-flow convention | period/PHF provenance | confirmed |
| W13-003 | Movements | FF, FR, RF, RR classification | Ch. 13 pp. 13-4--13-8 | veh/h then pc/h | all four movements explicitly accounted for | none | none | movement map, `vW`, `vNW`, `v` | confirmed |
| W13-004 | Flow conversion | Eq. 13-1, `v_i = V_i/(PHF*fHV)` | Ch. 13 p. 13-18 | veh/h to pc/h | first release: one common segment factor | none | Chapter 12 HV/PCE procedure | each `v_i`, common factor/PCE provenance | confirmed |
| W13-005 | FFS | Freeway FFS path | Ch. 13 pp. 13-12--13-18 | mi/h | only Chapter-13-authorized freeway path | no silent default | Ch. 12 FFS and adjustments | FFS and source mode | confirmed |
| W13-006 | Ratio | Weaving volume ratio `VR` | Ch. 13 pp. 13-18--13-20 | ratio | valid weaving movement definitions required | none | none | VR | confirmed |
| W13-007 | Lanes | Number of lanes `N` and weaving lanes `NWL` | Ch. 13 pp. 13-5--13-8, 13-20 | lanes | configuration-specific; two-sided has `NWL=0` | no lane/table substitution | none | N, NWL | confirmed |
| W13-008 | Lane changes | Eq. 13-2, one-sided `LCMIN` | Ch. 13 p. 13-19 | lane changes/h | one-sided movement definitions | none | none | LCMIN | confirmed |
| W13-009 | Lane changes | Eq. 13-3, two-sided `LCMIN` | Ch. 13 p. 13-20 | lane changes/h | two-sided; RR weaving movement | none | none | LCMIN | confirmed |
| W13-010 | Length | Eq. 13-4 `LMAX` | Ch. 13 p. 13-20 | ft | depends on VR and NWL | no extrapolation beyond applicable configuration | none | LMAX | confirmed |
| W13-011 | Handoff | `LS < LMAX` continuation; `LS >= LMAX` merge/diverge/basic-segment handoff | Ch. 13 pp. 13-20--13-21 | ft | equality is explicitly outside weaving continuation | no clipping | Ch. 12/14 handoff | stopping condition and destination | confirmed |
| W13-012 | Capacity | Eq. 13-5 density-governed ideal lane capacity | Ch. 13 p. 13-22 | pc/h/ln | applicable configurations/inputs only | none | HV factor later | `cIWL` | confirmed |
| W13-013 | Capacity | Eq. 13-6 density-governed prevailing segment capacity | Ch. 13 p. 13-22 | veh/h | `cIWL × N × fHV` | none | Chapter 12 HV factor | `cw_density` | confirmed |
| W13-014 | Capacity | Eq. 13-7 ideal all-lanes weaving-flow capacity | Ch. 13 p. 13-23 | pc/h | one-sided NWL 2/3; no limit for two-sided NWL 0 | no invented two-sided limit | none | `cIW` / not-applicable | confirmed |
| W13-015 | Capacity | Eq. 13-8 prevailing weaving-flow segment capacity | Ch. 13 p. 13-23 | veh/h | only when W13-014 applies | none | Chapter 12 HV factor | `cw_weaving_flow` | confirmed |
| W13-016 | Capacity | smaller applicable capacity; Eq. 13-9 CAF | Ch. 13 pp. 13-23--13-24 | veh/h | CAF must be authoritative/qualified | no arbitrary user factor | Chapter 12 CAF only if authorized | unadjusted/adjusted governing capacity | confirmed |
| W13-017 | Capacity check | Eq. 13-10 `(v × fHV)/cwa` | Ch. 13 p. 13-24 | ratio | `v` is ideal pc/h; numerator/cwa are prevailing veh/h | none | none | v/c, status | confirmed |
| W13-018 | Capacity failure | only unrounded `v/c > 1.00` terminates, LOS F, no speed/density | Ch. 13 p. 13-24 | — | equality continues; input/output leg failures also recorded | no rounding-based stop | Chapter 10/11 facility context as applicable | null predictions, reason | confirmed |
| W13-019 | Lane changes | Eqs. 13-11--13-17, weaving/nonweaving demand | Ch. 13 pp. 13-25--13-27 | lane changes/h | within-capacity, configuration-specific | interpolate only across stated `I_NW` 1300--1950 interval; no extrapolation | none | LCW, LCNW, branch | confirmed |
| W13-020 | Intensity | Weaving intensity | Ch. 13 pp. 13-27--13-28 | dimensionless | within-capacity | only stated procedure | none | intensity | confirmed |
| W13-021 | Speeds | Eqs. 13-18--13-22, weaving/nonweaving speeds | Ch. 13 pp. 13-28--13-29 | mi/h | within-capacity, valid branch/configuration | no hidden endpoint clipping | FFS inputs | Sw, Snw | confirmed |
| W13-022 | Output | Eq. 13-23 weighted mean speed and density | Ch. 13 p. 13-29 | mi/h; pc/mi/ln | prediction only when method continues | none | none | S, D | confirmed |
| W13-023 | LOS | Exhibit 13-6 freeway thresholds | Ch. 13 p. 13-10 | pc/mi/ln | freeway scope | none | none | LOS | confirmed |
| W13-024 | Limitations | oversaturation, interacting segments, urban streets and other exclusions | Ch. 13 p. 13-12 and relevant procedure pages | — | must be guarded | none | Ch. 12/14 where handed off | limitation/stopping record | confirmed |

## Input inventory

Inputs must retain source provenance, explicit units, and the distinction
between observed demand `V` (`veh/h`) and adjusted flow `v` (`pc/h`).  Required
inputs are: analysis period/PHF; configuration and directional lane geometry;
weaving length `LS`; interchange/ramp-density inputs when the selected FFS
route requires them; FFS source and its evidence; the four movement volumes;
one common segment HV composition and PCE source; applicable terrain/grade and
truck-mix inputs for the selected Chapter 12 route; and authorized SAF/CAF or
their default/provenance.  `NWL`, configuration, and FFS mode are not
interchangeable optional values.

Zero is meaningful only for a documented absent movement where the selected
configuration permits it.  It must never be silently used for PHF, a required
lane count, weaving length, FFS, PCE/HV composition, clearance, density,
SAF/CAF, or an unprovided traffic movement.  Inputs must be rejected when
composition is impossible (for example, heavy-vehicle components exceed 100%)
or when an inactive field would otherwise alter a result.

## Output and intermediate inventory

The Phase 2 result must include normalized inputs; `V_i`, common `fHV`, `v_i`;
`vW`, `vNW`, total `v`, VR, N, NWL, LCMIN, LS, LMAX; each capacity candidate,
CAF, adjusted/governing capacity, v/c and status; lane-change candidates and
chosen/interpolated branch; intensity; weaving/nonweaving/mean speed; density;
LOS; assumptions, warnings, limitations, and equation/exhibit source labels.
Ideal lane and weaving-flow capacities are pc/h/ln or pc/h as explicitly
named; prevailing unadjusted/adjusted segment capacities are veh/h after
`fHV`/CAF.  Do not mix them.  Above capacity, speed and density are
`None`/Not predicted, never zero or a capacity-point proxy.

## Validity and stopping conditions

Reject malformed physical inputs and unsupported source/table combinations.
Return an explicit unsupported-scope outcome for configurations, facility
types, periods, geometries, truck mixes, grade domains, or FFS paths not
qualified by this contract.  Stop the weaving method (not software execution)
when `LS >= LMAX`; identify the Chapter 12/14 handoff.  Stop operational
prediction and return LOS F only when unrounded `v/c > 1.00` or a relevant
input/output-leg capacity failure occurs; exactly `v/c = 1.00` continues to
speed/density/LOS prediction.  Do not calculate speed or density in an
oversaturated case.

## Chapter 12 dependency map

| Dependency | Current implementation | Qualification/reuse decision |
| --- | --- | --- |
| Core audit record and source-tagged intermediate values | `src/hcmcalc/core/audit.py` | qualified; reuse unchanged |
| Invalid input vs methodology boundary exceptions | `src/hcmcalc/core/exceptions.py` | qualified; reuse unchanged |
| Freeway measured/estimated FFS, lane/lateral/ramp-density adjustments | `src/hcmcalc/freeway/{models,validation,method,coefficients}.py` | qualified for its own bounded contract; extract only evidence-identical pure helpers in Phase 2 |
| Ch. 12 HV/PCE data and demand conversion | presently split across `freeway/` and `multilane/`; freeway imports some `multilane/coefficients.py` data | requires a neutral shared refactor; must accept per-movement inputs |
| SAF/CAF and driver population | `src/hcmcalc/freeway/` | qualified only under current freeway contract; do not expose arbitrary factors; crosswalk first |
| Multilane FFS/capacity/LOS | `src/hcmcalc/multilane/` | not reusable for freeway weaving or C-D scope without separate evidence |

## Chapter 27 example inventory

The local full HCM includes the following Chapter 27 weaving evidence, visually
located and not copied.  Example 1 (major weaving segment, pp. 27-2--27-7),
Example 2 (ramp weaving segment, pp. 27-7--27-11), and Example 3 (two-sided
weaving segment, pp. 27-12--27-16) are candidate operational validation
evidence.  Example 4 (design, pp. 27-17--27-23) is not an operational
regression fixture.  Example 5 (service volumes, pp. 27-24--27-27) and
Example 6 (multilane access/cross-weaving, p. 27-28 onward) are outside the
proposed first qualified freeway operational contract unless separately mapped.

No `references/weaving_example_inputs.yaml` is created in Phase 13.1.  Each
candidate's complete inputs, movement mapping, intermediate values, published
rounding, and tolerance must be independently transcribed from visually checked
pages and reviewed against this crosswalk before a runtime-neutral fixture is
introduced.  This avoids a fixture that falsely implies an implemented engine.

## Unresolved questions

Blocking for Phase 2 code: verify the exact source/page details and numerical
values for every candidate Ch. 27 operational example in a second independent
transcription; reconcile Chapter 13's capacity-equality wording with product
null semantics; and map every selected Ch. 12 FFS/PCE/SAF/CAF route down to its
exhibit/table domain.  Nonblocking for the first freeway release: whether a
future HCM 7.1 revision should supersede HCM 7.0, and the qualified scope for
multilane/C-D weaving and multiple/cross-weaving extensions.
