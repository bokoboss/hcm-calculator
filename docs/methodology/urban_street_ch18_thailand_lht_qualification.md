# HCM 7 Chapter 18 — Thailand/LHT Semantic Qualification

Status: **GO WITH CONDITIONS — Thailand/LHT physical-side semantics are sufficiently evidenced for a bounded adapter to the already-qualified Chapter 18 engine. This is not Thai empirical calibration and does not authorize new turn-dependent Chapter 18/30 submethods.**

Parent authority: Issue #172  
Research/qualification work package: Issue #179  
Accepted bounded engine: Issue #174 / PR #175  
Accepted application integration: Issue #176 / PR #177  
Baseline `main`: `e09042d6fba8bd7912801ee4615e548b98528d97`

## Decision

The accepted Chapter 18 Python engine should remain the single numerical authority and should **not** be mirrored, sign-changed, or recalibrated merely because Thailand uses left-hand traffic.

Thailand/LHT support should be implemented as a **role-based physical-side adapter** that converts Thai road-side semantics into the existing qualified HCM-reference canonical fields. The accepted RHT-reference application contract must remain immutable for existing projects and fingerprints; Thailand/LHT support therefore requires a new application/persistence contract identity.

The qualification is deliberately limited to the already-bounded signalized 15-minute workflow that uses explicit access-point delays and externally qualified downstream through performance.

## Existing HCM/project evidence

The accepted Chapter 18 research gate (`docs/methodology/urban_street_ch18_research_gate.md`) already established that:

- length, lane count, speed, direction-specific demand/capacity/delay are orientation-neutral;
- restrictive-median proportion is geometrically orientation-neutral;
- curb and parking proportions require LHT reinterpretation because the HCM RHT reference defines the relevant roadside on the right side in the direction of travel;
- subject/opposing access counts and future turn-side/bay terms require explicit physical-side mapping;
- automatic numerical mirroring is prohibited;
- the Example Problem 1 value `S_calib = 0` is not evidence of Thai local calibration.

The accepted bounded engine uses:

- `curb_proportion` and `parking_proportion` in the base-free-flow-speed chain;
- `subject_side_access_count + opposing_side_access_count` symmetrically for access density;
- explicit qualified per-access-point delays rather than an internal turn/access-delay model;
- explicit external downstream `v_th`, `c_th`, and `d_t` rather than an internal signalized-intersection solver.

This bounded architecture materially reduces the number of sided terms that must be qualified for Thailand/LHT use.

## External evidence

### Thailand traffic side

Thailand Road Traffic Act Section 39, in the Royal Thai Police English reference, states that a driver facing oncoming traffic shall drive near the **left edge** of the road. The Thai text remains the legal authority; this reference is used only to establish traffic-side orientation.

- Royal Thai Police reference: https://www.royalthaipolice.go.th/downloads/laws/laws_03_05-07.pdf

### LHT capacity-manual precedent

The official Malaysian Highway Capacity Manual 2011, Ministry of Works Malaysia, defines an access point for one direction of a multilane highway as a junction or driveway on the **left-hand side of the roadway** and determines directional access-point density from access points on the left side. Malaysia is an LHT jurisdiction. This is not adopted as Chapter 18 methodology; it is corroborating evidence that a capacity methodology should preserve the **roadside/outer-side role** when moving from RHT to LHT rather than preserving an RHT physical-right label.

- Official Ministry of Works repository: https://crr.kkr.gov.my/en/dokumen/umum/WK.1.2011.84
- Relevant sections: MHCM 2011 Chapter 4 §4.2.1.3 and §4.3.1.

The Malaysian manual also states that Malaysian highway-capacity studies were undertaken because direct use of the U.S. HCM might not adequately represent local conditions. That supports a distinction between **semantic LHT mapping** and **local empirical calibration**.

### LHT road-side and turn roles

Austroads road-management guidance uses **kerbside** and **median-side** lane roles in LHT operation and discusses right-turning vehicles in the median-side lane. New Zealand guidance similarly places normal travel and left turns on the left/kerb side and right turns toward the centre line/median side.

- Austroads Guide to Traffic Management Part 5: https://austroads.com.au/__data/assets/pdf_file/0023/342770/AGTM05-19_Guide_to_Traffic_Management_Part_5_Road_Management.pdf
- NZTA keeping-left guidance: https://www.nzta.govt.nz/driving-skills/learn-to-drive/roadcode/general-road-code/about-driving/key-driving-skills/keeping-left
- NZTA lane-use guidance: https://www.nzta.govt.nz/driving-skills/learn-to-drive/roadcode/motorcycle-code/about-riding/key-riding-skills/using-lanes-correctly

These sources support role-based terminology such as **kerbside**, **median-side**, **subject roadside**, and **opposite roadside** rather than blind left/right substitution.

### Thai empirical calibration remains unresolved

A 2024 Thai field study comparing HCM 2010/2016 estimates with measured capacity on one Thai urban multilane highway found the HCM estimates approximately 35% above the empirical capacity and discussed differences in driver behavior, traffic characteristics, and motorcycle composition. This is not a Chapter 18 calibration study and must not be used to alter Chapter 18 coefficients, but it is direct evidence against calling an uncalibrated HCM transfer “Thai-calibrated.”

- Srisurin & Amprayn (2024), DOI `10.14456/easr.2024.70`: https://murex.mahidol.ac.th/en/publications/evaluation-of-the-highway-capacity-manual-hcm-and-thailands-depar/

Research using Bangkok signalized-intersection field data also shows motorcycle composition can materially affect saturation flow and start-up lost time. The bounded architecture appropriately leaves downstream through capacity/delay external and qualified rather than embedding an unvalidated Thailand-specific intersection solver.

- Nakatsuji, T., Hai, N. G., Taweesilp, S., & Tanaboriboon, Y. (2001), “Effects of Motorcycle on Capacity of Signalized Intersections,” *Doboku Gakkai Ronbunshu / Infrastructure Planning Review*, Vol. 18, pp. 935–942, DOI `10.2208/journalip.18.935`: https://doi.org/10.2208/journalip.18.935

## Qualified mapping for the bounded Thailand/LHT adapter

The mapping is by **functional road-side role**, not by copying an RHT physical-right/left label.

| Thailand/LHT displayed concept | Existing canonical engine field | Qualified treatment |
|---|---|---|
| Segment length | `segment_length_ft` | Orientation-neutral; unit conversion only. |
| Upstream intersection width | `upstream_intersection_width_ft` | Orientation-neutral; unit conversion only. |
| Signal/control spacing | `signal_control_spacing_ft` | Orientation-neutral; unit conversion only. |
| Through lane count | `through_lane_count` | Orientation-neutral. |
| Subject direction / through movement | existing identity fields | Preserve explicit direction and movement identity; no mirroring. |
| Posted speed | `posted_speed_limit_mph` | Orientation-neutral; unit conversion only. |
| Calibration adjustment | `s_calib_mph` | Numerically orientation-neutral, but not Thai-calibrated by default; provenance/disclosure required. |
| Restrictive-median proportion | `restrictive_median_proportion` | Preserve value. |
| **Kerbside curb proportion** in the subject direction — physical **left** in Thailand | `curb_proportion` | Map role 1:1. Do not complement, negate, or otherwise transform the numerical value. |
| **Kerbside parking proportion** in the subject direction — physical **left** in Thailand | `parking_proportion` | Map role 1:1. Do not alter the numerical value. |
| Access count on the roadside adjacent to the subject-direction carriageway — physical left/kerbside in Thailand | `subject_side_access_count` | Preserve role identity. Current v1 uses the sum of subject and opposing counts, but provenance must remain correct. |
| Access count on the opposite roadside — physical right relative to the subject direction | `opposing_side_access_count` | Preserve role identity. No arithmetic mirroring. |
| Midsegment demand | `v_m_veh_h` | Direction-specific but orientation-neutral. |
| Qualified per-access-point delays | `access_point_delays_s_veh` | Must represent the actual Thailand/LHT access geometry; no internal side/turn model is inferred. |
| Other supported delay | `d_other_s_veh` | Orientation-neutral if source/scope is valid. |
| Downstream through demand/capacity/delay | external `v_th_veh_h`, `c_th_veh_h`, `d_t_s_veh` | Direction-specific but orientation-neutral; all must describe the same Thailand/LHT through movement, period, and control. |

### Important numerical consequence

For the current bounded engine, `subject_side_access_count` and `opposing_side_access_count` enter the access-density term through their **sum**. Therefore swapping the two counts would not change the current Eq. 18-3 numerical result, but it would corrupt provenance and would become dangerous if future sided access/turn procedures were added. The adapter must preserve the role identity even where the present formula is symmetric.

## Deferred/fail-closed LHT terms

This qualification does **not** authorize the following:

- Exhibit 18-13 planning access-delay turn-percentage/bay adjustments;
- `p_ap,lt` or other opposing-side turn-accessibility logic;
- automatic left-turn/right-turn reinterpretation in Chapter 30 §4 access-delay calculations;
- internal lane-group aggregation where turn shares, storage, or bays require physical-side interpretation;
- TWSC/YIELD/STOP conflict logic;
- measured or default Thailand-specific free-flow calibration;
- Thailand-specific motorcycle/PCE/capacity correction factors.

These remain separately gated and must fail closed or remain unavailable.

The existing bounded signalized workflow can still proceed because it requires explicit qualified per-access-point delays and explicit externally qualified downstream through performance.

## Calibration status

Thailand/LHT **semantic qualification is not empirical Thai calibration**.

A production adapter should carry an auditable calibration state. Recommended states are:

- `hcm_reference_uncalibrated` — HCM coefficients/reference calibration are used without a Thailand-specific empirical calibration claim;
- `user_local_calibration` — the operator supplies `S_calib` together with a source/note identifying the local evidence.

No Thailand default `S_calib` is qualified by this research. A future empirical calibration study must use a separately accepted calibration profile/version rather than silently changing this contract.

## Architecture implications

### Preserve the engine

Do not change Chapter 18 equations or coefficients in `src/hcmcalc/urban_street_ch18.py` to implement LHT.

The existing engine remains the qualified canonical HCM-reference kernel. The LHT adapter maps physical role-based inputs into its existing canonical fields.

### Preserve the accepted RHT contract

The merged contract:

`hcm7_ch18_bounded_signalized_15min_rht_reference_v1`

must remain immutable for existing Project v2 records, result identities, and fingerprints.

Thailand/LHT support therefore requires a **new application/persistence identity** rather than changing the existing contract in place.

The architecture-preferred starting point for scrutiny is a distinct adapter/method variant that reuses the same numerical engine, for example:

- `method_id`: `urban_street_segment_th_lht`
- `family`: `urban_streets`
- `method_identifier`: `hcm7_urban_street_segment_th_lht`
- `engine_method_identifier`: `urban_street_segment_ch18_v0_1`
- `method_version`: `hcm_7_0_bounded_th_lht_v1`
- `input_contract`: `hcm7_ch18_bounded_signalized_15min_th_lht_semantic_v1`
- `project_type`: `manual_urban_street_segment_th_lht_v1`

These identities are **proposed inputs to architecture scrutiny**, not yet accepted implementation identities.

## Required verification strategy

No authoritative published HCM Chapter 18 Thailand/LHT worked example was identified. Do not invent a local fixture and present it as primary evidence. Acceptance should instead combine the accepted HCM RHT fixture with metamorphic adapter tests.

Required tests:

1. **Role-mirror equivalence** — represent Chapter 30 Example Problem 1 using Thailand/LHT physical roles; after adapter normalization the canonical engine mapping and serialized result must be identical to the accepted RHT-reference case.
2. **Asymmetric-side fixture** — use deliberately different physical-side curb/parking/access values so a wrong side mapping cannot pass accidentally.
3. **Access provenance** — subject/opposing access identity must survive normalization even though the current equation uses their sum.
4. **Direction identity** — subject direction, external direction, through movement, period, control type, `v_m`, `v_th`, `c_th`, and `d_t` must remain internally consistent.
5. **RHT project immutability** — existing `urban_street_segment` RHT-reference Project v2 projects/fingerprints/results must remain unchanged.
6. **Numerical-kernel invariance** — direct canonical engine inputs must produce serialized-equivalent results before and after the adapter is added.
7. **Fail-closed future scope** — no Exhibit 18-13, internal Chapter 30 access-delay, TWSC/YIELD/STOP, or other unqualified turn-side feature becomes available merely because the LHT adapter exists.

## Scrutiny result

**GO WITH CONDITIONS.** The problem is correctly framed as semantic adaptation, not numerical mirroring.

Conditions before implementation acceptance:

1. architecture scrutiny must confirm the new method/contract identity and backward-compatibility strategy;
2. role-based LHT mapping must be explicit in schema, code, audit, report, and EN/TH copy;
3. existing RHT Project v2 records and fingerprints must remain immutable;
4. semantic mirror and asymmetric mapping tests must pass;
5. calibration status must be explicit and no Thailand default may be invented;
6. deferred turn-dependent methods remain fail closed;
7. full engine/application/Project/API/export/frontend regressions pass;
8. fresh-context independent review of the actual implementation is required before merge.

## Research uncertainties retained

- No Thailand-specific Chapter 18 empirical calibration dataset/reference was identified that would justify changing HCM coefficients or establishing a Thailand default `S_calib`.
- Malaysian/Australasian LHT evidence supports the physical-role mapping but is not a substitute for Thai empirical calibration.
- Motorcycle/mixed-flow effects remain a local empirical uncertainty; downstream intersection performance should remain externally qualified, and any future local free-flow calibration must be separately evidenced.

## Final verdict

**GO WITH CONDITIONS** for a new Thailand/LHT **semantic adapter contract** over the existing bounded Chapter 18 numerical engine.

This qualification authorizes development of a role-based Thailand/LHT adapter and UI semantics. It does **not** authorize equation changes, a Thai calibration claim, automatic turn-side algorithms, or expansion beyond the currently bounded signalized 15-minute workflow.
