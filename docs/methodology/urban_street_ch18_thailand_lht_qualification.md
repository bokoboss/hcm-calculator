# HCM 7 Chapter 18 — Thailand/LHT Semantic Qualification

Status: **GO WITH CONDITIONS for a role-based Thailand/LHT semantic adapter over the accepted HCM-reference Chapter 18 kernel. This is an HCM-reference transfer, not Thai empirical calibration.**

Parent authority: Issue #172  
Research/qualification work package: Issue #179  
Evidence-resolution follow-up: Issue #181  
Accepted bounded engine: Issue #174 / PR #175  
Accepted application integration: Issue #176 / PR #177  
Baseline `main`: `e09042d6fba8bd7912801ee4615e548b98528d97`

## Decision

The accepted Chapter 18 Python engine remains the single numerical authority and must not be mirrored, sign-changed, or recalibrated merely because Thailand uses left-hand traffic.

Thailand/LHT support may proceed as a **functional-role semantic adapter** that maps the physical outside/kerbside and median-side roles of a Thai road into the source-native HCM-reference fields. The adapter must not claim that the HCM coefficients are empirically calibrated for Thailand.

The accepted RHT-reference application contract remains immutable. Thailand/LHT therefore requires a new application/persistence identity and explicit audit of the physical-side-to-functional-role mapping.

The qualification remains bounded to the already accepted signalized 15-minute Chapter 18 workflow using explicit access-point delays and externally qualified downstream through performance. It does not authorize deferred turn-dependent Chapter 18/30 procedures.

## Why functional-role mirroring is different from numerical mirroring

The HCM/NCHRP source uses physical right/left language because the development context is U.S. right-hand traffic. The relevant model structure, however, distinguishes the **outside/roadside edge** from the **median-side edge**:

- NCHRP Project 3-79 defines curb presence from the right side of the traveled way in its U.S. RHT calibration sites and states that left-side curb presence is represented through median type. In RHT operation, the right side is the outside/kerbside edge and the left side is the median-side edge.
- The NCHRP calibration tables record parking on the right side and lateral clearance from the right edge of the outside through lane. This again ties the observed variable to the outside roadway edge in the RHT study context.
- A later Bonneson working paper describing the HCM 2010 urban-street method summarizes the predictor as **outside curb presence**, which supports the functional-roadside interpretation rather than an intrinsic physical-right effect.
- HCM directional access counts are defined on the right side of each direction of travel. For a two-way RHT street, those two direction-relative right sides represent the two outside roadsides. The current bounded Eq. 18-3 term uses their sum, so the numerical access-density effect is already symmetric across the two outside roadsides.

Therefore the adapter should mirror **physical geometry into the same functional role**. It must not mirror numbers blindly, swap unrelated source-side variables, or change coefficients.

## Relation to prior Thailand-first work

This is consistent with the existing project approach rather than a special exception:

- Two-Lane Highway workflows are primarily analysis-direction/opposing-direction based; LHT presentation can mirror roadway schematics without changing the numerical kernel.
- Multilane work already distinguishes functional roadside meaning from source-specific median-side terms. Functional roadside wording can be localized while unresolved source-side constructs remain explicit.
- Merge/diverge remain different because the accepted Chapter 14 method itself is explicitly bounded to a right-side ramp geometry; that is a methodology/configuration change, not merely an outside-roadside role label.

Chapter 18 curb/parking/access terms are closer to the functional-roadside case than to the Chapter 14 right-ramp case.

## International-use interpretation

HCM Chapter 1 explicitly recognizes international use of HCM methods while cautioning that most research/defaults are North American and that equations/procedures should be calibrated to local conditions where needed.

That distinction matters here:

1. **Traffic-side semantic mapping** answers which physical Thai roadside corresponds to the HCM functional outside/roadside role.
2. **Thai empirical calibration** answers whether the HCM coefficients/defaults predict Thai behavior accurately enough.

The first can be qualified without claiming the second.

Malaysia provides useful corroboration: the U.S. HCM was historically used extensively in Malaysian highway design, while Malaysia later developed local capacity manuals because local behavior and traffic characteristics differed. Its LHT methodologies use the left/outside roadside for directional access concepts. This supports functional-side adaptation while reinforcing the need to distinguish reference-method use from local calibration.

## Evidence

### Primary methodology

Bonneson, Pratt, and Vandehey, *Predicting the Performance of Automobile Traffic on Urban Streets*, Final Report, NCHRP Project 3-79, Texas Transportation Institute / TRB, January 2008.

The model-development material establishes:

- U.S. calibration using right-side curb presence;
- left-side curb represented through median type;
- right-side/outside parking observations;
- lateral clearance measured from the outside through lane;
- access observations tied to the roadside geometry of the RHT study sites.

This evidence is interpreted as an outside-versus-median functional distinction, not as proof that the biological/behavioral effect is inherently tied to the word “right.”

### Method-author terminology

J. Bonneson, *Comparison of Urban Streets Methodologies in HCM 2000 and HCM 2010*, Working Paper 3, 2013, describes the HCM 2010 free-flow-speed procedure as using speed limit, median type, **outside curb presence**, access-point density, and number of lanes.

This is important supporting evidence for the functional-roadside interpretation.

### HCM international-use guidance

HCM 7 Chapter 1 states that the general methods have international value but their use outside North America requires emphasis on local calibration and recognition of differences in traffic composition, user behavior, geometrics, and control.

This supports keeping the numerical HCM-reference method available under explicit uncalibrated/local-calibration status rather than treating LHT alone as a reason to invent new coefficients.

### LHT corroboration

- Thailand Road Traffic Act establishes left-hand road operation.
- Malaysian Highway Capacity Manual uses left-side/outside directional access concepts in LHT operation and documents why local calibration/research may be needed.
- Austroads/NZTA guidance uses kerbside and median-side functional roles under LHT.

These sources are corroborating semantic evidence, not substitutes for Chapter 18 methodology authority or Thai empirical calibration.

## Qualified mapping for the bounded Thailand/LHT adapter

The mapping is by **functional road-side role**, not by copying a physical right/left label.

| Thailand/LHT displayed concept | Existing canonical engine field | Qualified treatment |
|---|---|---|
| Segment length | `segment_length_ft` | Orientation-neutral; unit conversion only. |
| Upstream intersection width | `upstream_intersection_width_ft` | Orientation-neutral; unit conversion only. |
| Signal/control spacing | `signal_control_spacing_ft` | Orientation-neutral; unit conversion only. |
| Through lane count | `through_lane_count` | Orientation-neutral. |
| Subject direction / through movement | existing identity fields | Preserve actual movement identity; no compass mirroring. |
| Posted speed | `posted_speed_limit_mph` | Orientation-neutral; unit conversion only. |
| Calibration adjustment | `s_calib_mph` | Numerically orientation-neutral; no Thai default is implied. |
| Restrictive-median proportion | `restrictive_median_proportion` | Preserve median-role value. |
| **Outside/kerbside curb proportion** — physical left in Thailand | `curb_proportion` | Map functional outside-roadside role 1:1; do not complement, negate, or transform the numerical value. |
| **Outside/kerbside parking proportion** — physical left in Thailand | `parking_proportion` | Map functional outside-roadside role 1:1. |
| Access count on the outside roadside for the subject direction — physical left in Thailand | `subject_side_access_count` | Preserve direction-relative outside-roadside identity. |
| Access count on the outside roadside for the opposing direction — physical left in that opposing travel direction | `opposing_side_access_count` | Preserve direction-relative outside-roadside identity. |
| Midsegment demand | `v_m_veh_h` | Direction-specific but orientation-neutral. |
| Qualified per-access-point delays | `access_point_delays_s_veh` | Must represent the actual Thailand/LHT access geometry; no internal turn-side model is inferred. |
| Other supported delay | `d_other_s_veh` | Orientation-neutral if source/scope is valid. |
| Downstream through demand/capacity/delay | external `v_th_veh_h`, `c_th_veh_h`, `d_t_s_veh` | Must describe the same actual Thailand/LHT through movement, period, and control. |

### Access-density consequence

The bounded engine uses `subject_side_access_count + opposing_side_access_count` in Eq. 18-3. Under either RHT or LHT, the intended semantic mapping is the outside roadside of each travel direction. Swapping labels without respecting direction would corrupt provenance, but the aggregate numerical density remains the sum of the two outside roadsides.

## Calibration status

Thailand/LHT semantic qualification is **not** empirical Thai calibration.

Required auditable states:

- `hcm_reference_uncalibrated` — use the HCM-reference coefficients with Thailand/LHT functional-role mapping and an explicit disclosure that local empirical calibration has not been established;
- `user_local_calibration` — operator supplies `S_calib` together with traceable local evidence/source notes;
- any future accepted Thailand-specific calibration profile must receive its own version/identity and validation record.

No Thailand default `S_calib`, motorcycle/PCE adjustment, capacity correction, or other coefficient change is qualified here.

## Deferred/fail-closed LHT terms

This qualification does **not** authorize:

- Exhibit 18-13 planning access-delay turn-percentage/bay adjustments;
- `p_ap,lt` or other turn-accessibility logic requiring a left/right maneuver reinterpretation;
- automatic Chapter 30 §4 access-delay calculations;
- internal lane-group aggregation where turn shares, storage, or bays require physical-side interpretation;
- TWSC/YIELD/STOP conflict logic;
- Thailand-specific saturation-flow, PCE, motorcycle, or capacity factors;
- a claim that the HCM-reference result is locally validated for Thailand.

The bounded signalized workflow can proceed because per-access-point delays and downstream through performance remain explicit/external.

## Architecture decision

### Preserve the numerical kernel

Do not change equations or coefficients in `src/hcmcalc/urban_street_ch18.py` merely for LHT.

### Preserve the accepted RHT contract

`hcm7_ch18_bounded_signalized_15min_rht_reference_v1`

remains immutable for existing Project v2 records, result identities, and fingerprints.

### New Thailand/LHT application identity

Architecture scrutiny should use a distinct application/persistence identity while reusing the same engine, for example:

- `method_id`: `urban_street_segment_th_lht`
- `family`: `urban_streets`
- `method_identifier`: `hcm7_urban_street_segment_th_lht`
- `engine_method_identifier`: `urban_street_segment_ch18_v0_1`
- `method_version`: `hcm_7_0_bounded_th_lht_v1`
- `input_contract`: `hcm7_ch18_bounded_signalized_15min_th_lht_semantic_v1`
- `project_type`: `manual_urban_street_segment_th_lht_v1`

The exact identity must be frozen before implementation acceptance.

## Required adapter/audit semantics

The Thailand/LHT contract should expose role-based displayed fields such as:

- `kerbside_curb_proportion`;
- `kerbside_parking_proportion`;
- `subject_kerbside_access_count`;
- `opposing_kerbside_access_count`.

Audit/report evidence must retain:

- traffic side = LHT;
- displayed physical-side semantics (kerbside = physical left for each direction in Thailand);
- canonical HCM-reference field mapping;
- calibration status;
- explicit external-through provenance;
- no-rerun/current-result fingerprint guarantees.

Do not expose the RHT physical-right wording as if it were the Thai user-facing geometry.

## Required verification strategy

No authoritative Thailand/LHT HCM Chapter 18 worked example was identified. Acceptance therefore combines the accepted HCM RHT fixture with semantic/metamorphic and asymmetric tests.

1. **Role-mirror equivalence** — express the Chapter 30 Example Problem 1 using LHT functional-roadside inputs; normalization must yield the same canonical HCM-reference values and serialized numerical result as the accepted RHT fixture.
2. **Asymmetric physical-side fixture** — deliberately give different kerbside and median-side physical conditions so the adapter fails if it reads the wrong side.
3. **Access-direction provenance** — subject/opposing kerbside identities survive normalization even though Eq. 18-3 uses their sum.
4. **Direction identity** — subject direction, external direction, movement, period, control, `v_m`, `v_th`, `c_th`, and `d_t` remain consistent.
5. **RHT immutability** — existing RHT Project v2 records/fingerprints/results are byte/semantic stable.
6. **Kernel invariance** — direct canonical engine inputs produce equivalent results before and after adding the adapter.
7. **Calibration disclosure** — default LHT result is audibly `hcm_reference_uncalibrated`; no Thai-calibrated wording appears without evidence.
8. **Fail-closed future scope** — no deferred turn-side procedure becomes enabled through the semantic adapter.
9. **Full regression** — engine/application/Project/API/export/frontend suites remain green.
10. **Fresh independent review** of the implementation before merge.

## Issue #181 role

Issue #181 remains useful, but it is no longer treated as a blocker to the semantic adapter. Its purpose is to strengthen the evidence base and determine whether a later release can claim stronger transferability or Thai-specific validation:

- Track A: obtain an authoritative HCM/TRB/method-author clarification of outside/kerbside semantics and coefficient transfer;
- Track B: perform Thailand/LHT empirical validation/calibration if higher local predictive validity is required.

An authoritative contrary interpretation would trigger re-evaluation of this qualification before a production release.

## Final verdict

**GO WITH CONDITIONS** for a new Thailand/LHT **functional-role semantic adapter** over the existing bounded HCM Chapter 18 engine.

This authorizes semantic mapping of the outside/kerbside roadside from physical right under the HCM RHT reference to physical left under Thai LHT, while keeping the equations/coefficients unchanged and explicitly labeling the result as HCM-reference unless locally calibrated.

It does not authorize Thai empirical calibration claims, automatic turn-side algorithms, new Chapter 30 access-delay procedures, or expansion beyond the already bounded signalized 15-minute workflow.