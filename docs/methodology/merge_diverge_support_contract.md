# Merge and Diverge Support Contract

## Contract Status

This Phase 14.1 contract proposes the support envelope for the first qualified
Merge Segment and Diverge Segment releases. It is provisional until Phase 14.2
implements engines, validates official examples, and reviews the complete diff.

No production calculation implementation is added in this phase.

## Proposed Identifiers

| Item | Merge | Diverge |
| --- | --- | --- |
| Method family | `merge_segment` | `diverge_segment` |
| Candidate shared package | `ramp_influence` | `ramp_influence` |
| Method name | `hcm7_v70_freeway_merge_segment` | `hcm7_v70_freeway_diverge_segment` |
| Facility type | `freeway_merge_segment` | `freeway_diverge_segment` |
| Calculation type | `operational_analysis` | `operational_analysis` |
| Method version | `hcm_7_0` | `hcm_7_0` |
| Future project type | `manual_freeway_merge_segment_v1` | `manual_freeway_diverge_segment_v1` |
| Native units | US customary: ft, mi, mi/h, veh/h, pc/h, pc/h/ln, pc/mi/ln | same |

Recommendation: implement a shared `src/hcmcalc/ramp_influence/` package for
version dispatch, common models, demand conversion, capacity result records, and
audit helpers, but keep `merge/` and `diverge/` subpackages separate. The
method family exposed to users should remain separate (`merge_segment` and
`diverge_segment`) because the equations, adjacent-ramp branches, density
models, geometry semantics, and failure interpretation are not symmetric.

## Qualified First-Release Scope

| Scope Item | Merge | Diverge |
| --- | --- | --- |
| Facility | isolated general-purpose freeway ramp-freeway junction | isolated general-purpose freeway ramp-freeway junction |
| Ramp geometry | one-lane, right-side on-ramp | one-lane, right-side off-ramp |
| Lane domain | 2-4 freeway lanes per analysis direction pending example/boundary tests | 2-4 freeway lanes per analysis direction pending example/boundary tests |
| Adjacent ramps | isolated plus official-example adjacent cases after validated branch tests | isolated plus official-example adjacent cases after validated branch tests |
| FFS | measured freeway FFS or qualified Chapter 12 estimated freeway FFS; ramp FFS required for capacity/speed | same |
| Heavy vehicles | component-level Chapter 12 general-terrain `fHV` where source-equal; first release level/rolling unless specific-grade review is completed | same |
| SAF/CAF | HCM default 1.00 unless a governed source path is explicitly implemented | same |
| Output | capacity status, density, LOS A-E for stable cases, optional speed outputs; LOS F/null predictions on capacity failure | same |

Excluded from first release:

- HCM 7.1;
- C-D roadway and multilane highway approximate applications;
- two-lane ramps;
- left-side ramps;
- lane additions and lane drops as calculation cases;
- major merge and major diverge areas;
- managed lane access points;
- ramp metering and work zones;
- freeway facility/reliability/corridor analysis;
- queue, delay, volume-served, and spillback prediction;
- service-flow/service-volume design tables;
- automatic geometry derivation from diagrams.

## Input Contract Draft

| Field | Merge Meaning | Diverge Meaning | Unit | Required | Notes |
| --- | --- | --- | --- | --- | --- |
| `method_version` | `hcm_7_0` | `hcm_7_0` | none | yes | reject `hcm_7_1` until qualified |
| `analysis_period_minutes` | analysis period basis | analysis period basis | min | yes | peak 15-min equivalent hourly flow convention |
| `peak_hour_factor` | freeway/ramp PHF or component PHFs | freeway/ramp PHF or component PHFs | ratio | yes | no missing-to-one except explicit governed default |
| `freeway_lanes` | lanes in analysis direction upstream/downstream | lanes in analysis direction upstream/downstream | count | yes | lane additions/drops excluded initially |
| `ramp_side` | right side only | right side only | enum | yes | left side unsupported until extension qualified |
| `ramp_lanes_at_junction` | one | one | count | yes | two-lane ramps unsupported initially |
| `acceleration_lane_length_ft` | calculation-relevant `LA` | not applicable | ft | merge yes | includes taper where HCM defines it |
| `deceleration_lane_length_ft` | not applicable | calculation-relevant `LD` | ft | diverge yes | includes taper where HCM defines it |
| `freeway_demand_veh_h` | immediately upstream of on-ramp | immediately upstream of off-ramp | veh/h | yes | preserve raw observed demand |
| `ramp_demand_veh_h` | on-ramp demand entering freeway | off-ramp demand leaving freeway | veh/h | yes | preserve raw observed demand |
| `downstream_freeway_demand_veh_h` | derived `freeway + ramp` unless lane/add/drop special case | derived continuing flow `freeway - ramp` | veh/h | derived | retain in audit |
| `freeway_ffs_mph` | freeway FFS | freeway FFS | mi/h | yes | Chapter 12 source/provenance |
| `ramp_ffs_mph` | on-ramp FFS for ramp capacity/speed | off-ramp FFS for ramp capacity/speed | mi/h | yes | Exhibit 14-12 capacity selection |
| `terrain/heavy_vehicle_inputs` | freeway and ramp component paths | freeway and ramp component paths | %, ratio | yes | component-specific support to be validated |
| `adjacent_ramp_context` | upstream/downstream ramp type, side, spacing, demand | upstream/downstream ramp type, side, spacing, demand | ft, veh/h | conditional | branch rules differ by method |
| `saf/caf` | speed/capacity adjustment provenance | speed/capacity adjustment provenance | ratio | conditional | default 1.00 unless governed |
| `geometry_evidence` | structured geometry source and diagram subtype | structured geometry source and diagram subtype | none | yes | image selector cannot drive computation |

## Result Contract Draft

Both methods should return the existing `CalculationResult` shape with expanded
outputs following Weaving conventions:

- method identity and `method_version`;
- normalized input summary and source provenance;
- converted component flows and `fHV` records;
- lane distribution branch, original `v12`, adjusted `v12`, and adjustment reason;
- capacity candidates, CAF, adjusted capacities, unrounded `v/c`, and governing
  status;
- maximum desirable influence-area flow warning when applicable;
- stable-case density and LOS;
- stable-case speed outputs where computed;
- null speed/density when the method stops or capacity fails;
- assumptions, warnings, limitations, and HCM equation/exhibit source labels.

## Geometry and Configuration Contract

Calculation-relevant geometry:

| Geometry Field | Merge | Diverge |
| --- | --- | --- |
| ramp side | selects right-side core or unsupported left-side extension | selects right-side core or unsupported left-side extension |
| ramp lanes at junction | one-lane core; two-lane unsupported initially | one-lane core; two-lane/option-lane unsupported initially |
| auxiliary lane length | acceleration lane length `LA`; taper included | deceleration lane length `LD`; taper included |
| lane addition/drop | Chapter 12 handoff or unsupported first release | Chapter 12 handoff or unsupported first release |
| adjacent ramp spacing | branch selection for certain adjacent off-ramps | branch selection for certain adjacent on/downstream off ramps |
| freeway lanes | lane-distribution branch and reasonableness adjustment | lane-distribution branch and reasonableness adjustment |

Presentation-only diagram fields:

- arrow labels and color;
- lane striping style;
- gore shape details not used by HCM equations;
- accessibility text and alt-label variants;
- compact/mobile rendering variants.

Unsupported or unresolved geometry:

- left-side ramps;
- two-lane on-ramps and two-lane off-ramps;
- option-lane diverges;
- lane additions/drops longer than the core influence-area definition;
- major merge/diverge;
- managed lane access;
- overlapping weaving/merge/diverge where separate segment results must be
  reconciled.

## Configuration Image Plan

No copyrighted HCM/HCS figures or screenshots may be reused. Phase 14.3 must
create original local diagrams or use assets with documented permission.

Minimum diagram set:

| Diagram | Calculation-Relevant? | Engine Fields | Asset Status |
| --- | --- | --- | --- |
| one-lane right-side on-ramp | yes | `method=merge`, `ramp_side=right`, `ramp_lanes=1`, `LA` | original asset required |
| one-lane right-side off-ramp | yes | `method=diverge`, `ramp_side=right`, `ramp_lanes=1`, `LD` | original asset required |
| adjacent off-ramp affecting merge | yes for branch evidence | adjacent ramp type/spacing/demand | original asset required before UI exposure |
| adjacent on/off ramp affecting diverge | yes for branch evidence | adjacent ramp type/spacing/demand | original asset required before UI exposure |
| lane addition / lane drop | yes as unsupported/handoff state | add/drop flags, length | original asset required if displayed |
| two-lane on-ramp | future support | ramp lanes, `LA1`, `LA2`, isolation | no authorized asset |
| two-lane off-ramp / option lane | future support | ramp lanes, option lane, `LD1`, `LD2` | no authorized asset |
| left-side merge/diverge | future support | ramp side, leftmost lane influence | no authorized asset |

Accessibility requirements: every diagram must have concise alt text naming the
movement, ramp side, lane count, and whether the image is calculation-relevant
or explanatory only. UI controls must show explicit structured fields; diagrams
must never be the only source of calculation geometry.

## Error and Validation Taxonomy

| Category | Examples |
| --- | --- |
| malformed input | missing required demand, PHF <= 0, negative length, nonfinite FFS, impossible HV percentage |
| unsupported geometry | left-side ramp, two-lane ramp, major merge/diverge, managed lane, C-D/multilane branch |
| unsupported method scope | HCM 7.1 requested, service volume analysis, work zone, ramp metering, facility analysis |
| HCM stopping condition | lane addition/drop handoff, weaving handoff, method requires Chapter 10/23/38 queue analysis |
| capacity failure | freeway demand exceeds capacity, ramp demand exceeds ramp capacity |
| warning | maximum desirable influence-area flow exceeded, adjacent influence areas overlap, predictions likely optimistic |
| informational note | governed defaults used, optional speed calculated, diagram subtype is presentation-only |
| qualified result | stable LOS A-E with complete audit trail |

## Phase 14.2 Blueprint

Recommended package structure:

```text
src/hcmcalc/ramp_influence/
|-- __init__.py
|-- models.py
|-- registry.py
|-- common.py
|-- capacity.py
|-- validation.py
|-- merge/
|   `-- v7_0/
|       |-- __init__.py
|       |-- method.py
|       `-- coefficients.py
`-- diverge/
    `-- v7_0/
        |-- __init__.py
        |-- method.py
        `-- coefficients.py
```

Implementation order:

1. Add typed input models and version dispatch with `hcm_7_1` known but
   unsupported.
2. Add strict validation and unsupported-scope tests before numerical code.
3. Extract or reuse Chapter 12 helpers only where Basic Freeway tests prove
   identical source semantics.
4. Implement Merge lane distribution, capacity, density, speed, and examples.
5. Implement Diverge lane distribution, capacity, density, speed, and examples.
6. Add shared capacity/failure result model and warning taxonomy.
7. Add Chapter 28 fixtures after independent transcription.
8. Add non-example boundary tests and version-isolation tests.
9. Run full repository tests and clean Python 3.12 qualification.

Phase 14.2 entry gate:

- second reviewer or second pass completes Chapter 28 example transcription;
- every equation/exhibit/table boundary used in code is mapped to a source page;
- capacity/failure and null-output semantics are accepted for Merge and Diverge
  separately;
- geometry/image requirements are approved;
- `hcm_7_1` remains guarded unless its separate audit is complete.
