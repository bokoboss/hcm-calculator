# Thailand-first Metric Units and Left-Hand-Traffic Crosswalk

Related issue: #146  
Status: **READY FOR INDEPENDENT REVIEW**  
Work mode: **STRICT**  
Audited baseline: `bff49db32c4adb1475a784b9a6dc3572c00ee7c1`

## 1. Research question

How should HCM Calculator present and persist units and traffic-side semantics for Thailand while preserving the qualified HCM numerical methods, source terminology, calculation identity, and auditability?

This audit answers the question at the contract level. It does **not** authorize a blanket left/right mirror of HCM methods.

## 2. Research-gate verdict

**GO WITH CONDITIONS** for the Thailand-first product contract and for narrowly scoped follow-up work.

There is sufficient repository and HCM source mapping to keep Metric as the primary user-facing unit system and to classify traffic-side semantics by method. There is **not** sufficient evidence to treat every right-side HCM term or right-side ramp method as automatically mirror-equivalent under left-hand traffic.

Conditions:

1. Preserve HCM-native US customary inputs inside the Python numerical engines.
2. Metric conversion remains a deterministic application/UI boundary operation; do not rewrite HCM equations or coefficients in Metric units.
3. Do not add HCM formula logic to TypeScript.
4. Do not silently rename a source-side term from right to left, or vice versa, unless the mapping is proven to be functionally mirror-equivalent by primary methodology evidence.
5. Traffic-side-sensitive cases without that evidence must retain source terminology, expose the support boundary, or fail closed.
6. Any future calculation-relevant `traffic_side` input must participate in normalized input identity, persistence, fingerprints, exports, and migration; it must not be introduced as presentation-only metadata.
7. Presentation-only terminology changes must not alter engine keys, normalized values, fingerprints, or saved-project semantics.

### Evidence used

Repository evidence:

- `src/hcmcalc/ui/units.py`
- `src/hcmcalc/application/phase3_workflows.py`
- `src/hcmcalc/multilane/models.py`
- `src/hcmcalc/multilane/method.py`
- `src/hcmcalc/freeway/models.py`
- `src/hcmcalc/weaving/models.py`
- `src/hcmcalc/weaving/geometry.py`
- `src/hcmcalc/ramp_influence/models.py`
- `docs/methodology/two_lane_phase_1_implementation_spec.md`
- `docs/methodology/multilane_method_gap_analysis.md`
- `docs/methodology/basic_freeway_method_gap_analysis.md`
- `docs/methodology/weaving_phase_1_support_contract.md`
- `docs/methodology/merge_diverge_hcm_7_0_methodology_map.md`
- `docs/methodology/merge_diverge_support_contract.md`
- packaged traffic diagrams under `src/hcmcalc/ui/assets/`

Primary/source-governance references already mapped by the repository include HCM 7th Edition Chapters 12, 14, 15, 26, 27, and 28. The current merge/diverge methodology map records the licensed HCM Chapter 14 source pages and explicitly distinguishes right-side core methodology from left-side extensions.

Supplemental public source check:

- HCM Volume 4 official portal: https://hcmvolume4.org/
- HCM7 corrections/clarifications/updates: https://hcmvolume4.org/wp-content/uploads/2024/10/HCM7-corrections-clarifications-updates-12-2022.pdf

No public correction or interpretation located during this audit authorizes a general RHT-to-LHT mirroring rule. Absence of such an item is not evidence of equivalence; therefore unresolved mappings remain conservative.

## 3. Metric architecture contract

Thailand-first means **Metric at the user boundary**, not a Metric rewrite of HCM methodology.

The accepted architecture is:

```text
Metric user input
  -> deterministic unit conversion
  -> HCM-native Python engine (US customary where required by HCM)
  -> canonical HCM result
  -> deterministic Metric display/report conversion
```

Canonical exact factors already used by the application boundary:

- `1 mi = 1.609344 km`
- `1 ft = 0.3048 m`

Required behavior:

- km/h -> mph: divide by `1.609344`;
- km -> mi: divide by `1.609344`;
- m -> ft: divide by `0.3048`;
- density and per-distance rates convert dimensionally and deterministically;
- `veh/h` and `pc/h/ln` are not distance-converted;
- equivalent Metric and Imperial physical cases must normalize to equivalent engine inputs/results;
- do not round display-side values before normalization or before capacity/LOS boundary decisions.

This is already consistent with `src/hcmcalc/ui/units.py` and the Phase 3 application-service boundary, where displayed-unit normalization is deliberately outside the HCM engines.

## 4. Traffic-side classification

Use exactly these classifications for #146 follow-up decisions:

- **traffic-side invariant** — the physical/mathematical concept does not change when the road system is mirrored. Presentation may be Thailand-first without changing calculation identity.
- **mirror-equivalent with evidence** — a side-specific source construct has primary evidence showing that the opposite-side LHT configuration uses the same method after a defined mirror operation.
- **traffic-side-sensitive / unresolved** — side is part of the method geometry, calibration, lane selection, or diagram meaning and mirror equivalence has not been qualified. Preserve the source contract, explicitly encode side, or fail closed.

No item in this audit is classified `mirror-equivalent with evidence` merely from geometric intuition.

## 5. Crosswalk

| Method | HCM source term / current engine key | Current UI / product term | Unit | Traffic-side class | Thailand/LHT term | Mapping rule | Primary evidence | Action |
|---|---|---|---|---|---|---|---|---|
| Two-Lane Segment | analysis-direction / opposing-direction volumes | Analysis direction / opposing direction | veh/h | traffic-side invariant | Same directional terms | Direction is relative to the analysis stream, not physical left/right roadway edge | HCM7 Ch15 mapping; `two_lane_phase_1_implementation_spec.md` | `KEEP` |
| Two-Lane Segment | lane width, shoulder width, access-point density | Same | m primary; ft native; per km primary | traffic-side invariant | Same functional terms | Metric boundary conversion only | Ch15 mapping; `phase3_workflows.py`; `units.py` | `KEEP` |
| Two-Lane Segment | passing-constrained / passing-zone / passing-lane | Same workflow names | n/a | traffic-side invariant numerically; diagram-sensitive in presentation | Same method terms with LHT schematic | Existing packaged two-lane schematics are explicitly left-hand assets and do not drive engine math | `assets/schematics/two_lane/left_hand/`; packaged `ui/assets/two_lane/` | `KEEP` |
| Two-Lane Facility | ordered segment sequence, analysis/opposing volumes, passing-lane role | Facility segment table | mixed | traffic-side invariant for current numerical contract | Same directional/functional terms | Segment ordering and passing-lane role are longitudinal/directional, not a road-edge side input | `manual_facility.py`; Ch15/Ch26 facility evidence | `KEEP` |
| Multilane | `roadside_lateral_clearance_ft` | Roadside lateral clearance | m primary; ft native | traffic-side invariant as a functional roadside concept | Roadside lateral clearance | Preserve functional roadside meaning; do not convert this into a hard-coded left/right label | Ch12 Eq. 12-4 implementation in `multilane/method.py` | `RENAME_PRESENTATION_ONLY` if any surface uses a side-specific label |
| Multilane | `left_side_lateral_clearance_ft` for divided median | Left-side lateral clearance | m primary; ft native | traffic-side-sensitive / unresolved | Retain HCM source-side term until qualified | Engine currently explicitly sums roadside clearance with **left-side** clearance for divided roadways. Do not rename to right/median-side by intuition | `multilane/method.py`; HCM7 Eq. 12-4 / Exh. 12-20/22/23/24 mapping | `DEFER` |
| Multilane | `median_type` | Divided / undivided / TWLTL | n/a | traffic-side invariant | Same | Median form itself is not LHT/RHT-specific; its interaction with source-side clearance remains governed by the preceding row | Ch12 implementation | `KEEP` |
| Multilane | access-point density | Access-point density | per km primary; per mi native | traffic-side invariant | Same | Scalar density conversion only | Ch12 implementation; `units.py` | `KEEP` |
| Basic Freeway | `right_side_lateral_clearance_ft` | Right-side lateral clearance | m primary; ft native | traffic-side-sensitive / unresolved | **HCM source term: right-side lateral clearance** | Do not silently relabel as left-side/roadside for LHT until the Chapter 12 adjustment is qualified as functional mirror-equivalent | `freeway/models.py`; `basic_freeway_method_gap_analysis.md` | `DEFER` |
| Basic Freeway | total ramp density | Total ramp density | per km primary; per mi native | traffic-side invariant as a scalar density in the current contract | Same | Unit conversion only; no implied ramp-side geometry | Ch12 Basic Freeway mapping | `KEEP` |
| Weaving | FF / FR / RF / RR movement labels | FF / FR / RF / RR | veh/h | traffic-side invariant | Same movement labels | Labels denote **origin/destination**, not left/right lane position | `weaving_phase_1_support_contract.md` | `KEEP` |
| Weaving | `entry_side`, `exit_side` in geometry basis | Entry side / exit side | n/a | traffic-side-sensitive / unresolved | Explicit physical side | Never infer or mirror side from FF/FR/RF/RR labels. One-sided requires same entry/exit side; two-sided requires different sides | `weaving/models.py`; `weaving/geometry.py` | `ADD_EXPLICIT_TRAFFIC_SIDE` in any future generalized project contract |
| Weaving | `right_side_lateral_clearance_ft` | Right-side lateral clearance | m primary; ft native | traffic-side-sensitive / unresolved | Retain HCM source term | Ch12 estimated-FFS dependency must not be mirrored without evidence | `weaving_phase_1_support_contract.md`; Ch12 FFS handoff | `DEFER` |
| Weaving | one-sided / two-sided reference PNGs | Configuration diagram | visual | traffic-side-sensitive / unresolved | Thailand/LHT diagram only after visual/evidence qualification | Do not horizontally flip an authored diagram and call it HCM-equivalent without checking geometry meaning, arrows, entry/exit side and labels | `ui/assets/weaving/` | `DEFER` |
| Merge HCM7.0 | `ramp_side = right`; right-side on-ramp core | Right-side merge / on-ramp | n/a | traffic-side-sensitive / unresolved | Explicit **right-side HCM7.0** configuration | Current supported method is intentionally bounded to isolated one-lane right-side ramp. A Thailand/LHT left-side representation is not an automatic mirror | HCM7 Ch14 methodology map; `merge_diverge_support_contract.md` | `FAIL_CLOSED` for left-side/LHT remap |
| Merge HCM7.0 | LA / ramp influence-area lane selection | Merge influence-area quantities | mixed | traffic-side-sensitive / unresolved | Source-native right-ramp lane selection | Keep current source geometry only. Left-side extension requires separate protected methodology qualification | HCM7 Ch14 map | `FAIL_CLOSED` |
| Merge HCM7.0 | `merge_right_on_ramp.svg` | Merge reference diagram | visual | traffic-side-sensitive / unresolved | Label clearly as right-side supported geometry | Do not mirror current asset to imply qualified LHT support | `ui/assets/ramp_influence/merge_right_on_ramp.svg` | `KEEP` with explicit scope note |
| Diverge HCM7.0 | `ramp_side = right`; right-side off-ramp core | Right-side diverge / off-ramp | n/a | traffic-side-sensitive / unresolved | Explicit **right-side HCM7.0** configuration | Same rule as merge; current method does not authorize left-side Thailand mapping | HCM7 Ch14 methodology map; `merge_diverge_support_contract.md` | `FAIL_CLOSED` for left-side/LHT remap |
| Diverge HCM7.0 | LD / ramp influence-area lane selection | Diverge influence-area quantities | mixed | traffic-side-sensitive / unresolved | Source-native right-ramp lane selection | Keep current source geometry only; left-side extension is separate protected work | HCM7 Ch14 map | `FAIL_CLOSED` |
| Diverge HCM7.0 | `diverge_right_off_ramp.svg` | Diverge reference diagram | visual | traffic-side-sensitive / unresolved | Label clearly as right-side supported geometry | Do not mirror current asset to imply qualified LHT support | `ui/assets/ramp_influence/diverge_right_off_ramp.svg` | `KEEP` with explicit scope note |

## 6. Method conclusions

### 6.1 Two-Lane Segment and Facility

The current numerical contract is fundamentally directional rather than roadside-specific. Analysis direction, opposing direction, grade direction, segment sequence, passing-zone and passing-lane roles do not require a left/right numerical reinterpretation. Existing two-lane presentation assets already have a left-hand set.

**Audit decision:** preserve calculations and engine keys. Thailand-first work is primarily Metric presentation and diagram/terminology consistency.

### 6.2 Multilane

The current implementation intentionally distinguishes `roadside_lateral_clearance_ft` from `left_side_lateral_clearance_ft`. For a divided roadway, HCM Eq. 12-4 is currently implemented by summing capped roadside and left-side clearances. That left-side source term must not be silently converted into a right-side or median-side term under LHT without Chapter 12 evidence.

**Audit decision:** functional roadside terminology is safe; source-specific left-side mapping is deferred.

### 6.3 Basic Freeway

`right_side_lateral_clearance_ft` is part of the HCM Chapter 12 estimated-FFS branch and is encoded explicitly in engine and product contracts. Thailand-first presentation does not justify swapping the key or value to the left side.

**Audit decision:** retain source terminology and defer any LHT remap pending primary evidence.

### 6.4 Weaving

FF/FR/RF/RR are movement-origin/destination labels and must not be interpreted as physical left/right. Geometry side is separately encoded through entry/exit side. This separation is correct and should be preserved.

**Audit decision:** movement labels stay unchanged; future generalized Thailand geometry must encode side explicitly. Current diagrams require visual/evidence audit before LHT claims.

### 6.5 Merge and Diverge

The current HCM7.0 support contract is intentionally a one-lane **right-side** ramp method. Repository source mapping records left-side ramps as extension methodology outside the current supported release. Therefore a Thailand/LHT mirror would be a methodology expansion, not localization.

**Audit decision:** left-side/LHT remapping fails closed. Keep right-side HCM7.0 capability explicitly labeled as such. Qualifying the HCM left-side extension is a separate protected engineering task.

## 7. Persistence, fingerprint, and migration decision

No schema or fingerprint change is authorized by this audit.

### Presentation-only changes

A terminology or help-text change that does not alter normalized physical meaning must:

- preserve the existing engine key;
- preserve canonical normalized inputs;
- preserve Project v2 serialization meaning;
- preserve calculation fingerprints;
- preserve current/stale behavior;
- preserve exports/report numerical identity.

### Calculation-relevant traffic side

If a future weaving, merge, diverge, or other method begins accepting `traffic_side` or a mirrored physical side that changes lane selection or geometry interpretation, the field is calculation-relevant and must be treated as part of the engineering contract. At that point it must have:

- an explicit engine/application input;
- Project v2 persistence and migration rules;
- normalized-input/fingerprint participation;
- stale-result behavior after changes;
- EN/TH labels and export/report traceability;
- method-specific validation that fails closed outside qualified combinations.

Do not add a cosmetic `traffic_side = left` flag that leaves a right-side calculation unchanged.

## 8. Required follow-up work packages

These are deliberately separated so safe localization cannot accidentally authorize methodology changes.

### A. Metric physical-equivalence qualification

For all seven workflows, add paired Imperial/Metric cases representing the same physical inputs and assert equivalent canonical engine inputs/results before display rounding. Include cases near capacity and LOS thresholds.

This is primarily a qualification task; no formula rewrite is expected.

### B. Safe presentation-only Thailand terminology

Only after this audit is accepted:

- prefer functional `roadside` wording where the engine already models roadside clearance functionally;
- add source-term disclosure where `left-side` or `right-side` remains HCM-native;
- explicitly label merge/diverge diagrams and help text as right-side HCM7.0 supported geometry;
- do not change engine keys or persisted normalized values.

### C. Weaving side/diagram qualification

Inspect one-sided and two-sided authored diagrams against `entry_side`, `exit_side`, FF/FR/RF/RR movement definitions and the HCM7.0 geometry contract. Produce LHT-specific assets only if their mapping is proven and separately tested.

### D. HCM7.0 left-side merge/diverge extension

If Thailand use requires left-side on/off-ramp analysis, treat it as a protected methodology implementation:

- map the HCM Chapter 14 left-side extension procedure;
- identify lane-selection changes and equations;
- add explicit ramp/traffic side to method identity;
- independently validate examples/non-example cases;
- version/persist/fingerprint it correctly;
- add corresponding diagrams.

It must not be implemented as a front-end mirror of the right-side method.

### E. Versioned future HCM7.1 work

HCM7.1 replacement methodology remains outside #146. Do not use Thailand/LHT work as a reason for a silent HCM7.0 -> HCM7.1 migration.

## 9. Acceptance-gate mapping

| Gate | Audit result | Required evidence before implementation acceptance |
|---|---|---|
| TH-G1 — primary-source evidence | **Conditional pass** | Current source maps support source-native terminology and right-side ramp boundary; unresolved LHT mirrors remain `DEFER`/`FAIL_CLOSED` |
| TH-G2 — Metric/Imperial physical equivalence | **Architecture pass; regression expansion required** | Add paired seven-workflow equivalence matrix in follow-up A |
| TH-G3 — boundary precision | **Contract defined** | Follow-up equivalence cases must avoid pre-decision display rounding near capacity/LOS boundaries |
| TH-G4 — no TS HCM math | **Pass by architecture** | Keep all future conversion/calculation authority in Python/application boundary; TS presentation only |
| TH-G5 — LHT diagrams | **Partial** | Two-lane LHT assets exist; weaving unresolved; merge/diverge right-side-only assets must remain explicitly scoped |
| TH-G6 — legacy safety | **Pass for audit** | No schema/fingerprint mutation in this document; future calculation-relevant side requires migration |
| TH-G7 — cross-surface consistency | **Specified, not yet requalified** | Presentation follow-up must check UI/project/export/report terminology together |
| TH-G8 — independent review | **Pending** | Fresh-context review required before #146 is accepted |

## 10. Unknowns and explicit non-assumptions

- This audit does not assert that every Thailand freeway ramp is on one physical side.
- It does not infer that HCM `right-side lateral clearance` means generic roadside clearance.
- It does not infer that the Multilane `left-side lateral clearance` may be renamed to median-side/right-side for LHT.
- It does not infer that a horizontally mirrored weaving/ramp image is methodologically equivalent.
- It does not authorize left-side HCM ramp extension equations without primary-source qualification.

Unknown is acceptable; unsupported engineering equivalence is not.

## 11. Recommended issue state

Proposed final state after independent review:

`THAILAND_METRIC_LHT_AUDIT_COMPLETE`

This state means the crosswalk and safe boundaries are complete. It does **not** mean every LHT geometry is implemented. Unresolved items are intentionally classified `DEFER` or `FAIL_CLOSED`, which is the required engineering outcome until primary evidence supports broader behavior.

Current state of this document:

`READY_FOR_INDEPENDENT_REVIEW`
