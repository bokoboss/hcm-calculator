# HCM 7.0 Chapter 18 Urban Street Segment — Research Gate

Status: **GO WITH CONDITIONS — primary methodology research is sufficient to authorize a separate, bounded Chapter 18 Python engine qualification work package.** This is not qualification of a complete operational Chapter 18 network/intersection workflow, application release, or Thailand/LHT use.

Issue authority: #172
Research PR: #173

## Decision and selected scope

The selected first engine is a **bounded operational Chapter 18 motorized Urban Street Segment calculation using externally qualified downstream through-movement performance**. The acceptance fixture is Chapter 30 §8 Example Problem 1, an operational, coordinated-actuated signal example evaluated over a 15-minute period.

The engine calculates the bounded segment running-performance chain, travel speed from supplied final downstream through delay, downstream through v/c from supplied through demand and through capacity, and motorized LOS within the stated domain. It does not claim to perform all operational Chapter 18 network or intersection analysis.

The external boundary/preconditions are that demand is already balanced and capacity-adjusted for the analyzed flows; any applicable capacity effects are resolved; the period and direction agree across inputs; no sustained or cyclic spillback invalidates the result; and the external downstream through-movement result is HCM-compatible and traceable.

The first qualification defers internal Chapter 30 Step 1 demand balancing/OD/metering/spillback analysis, an internal Chapter 19 intersection solver, full Chapter 30 §3 platoon dispersion, computed Chapter 30 §4 access-point delay, other boundary-control types, stop-rate/perception outputs, nonmotorized modes, and Chapter 16 facility aggregation.

## Primary evidence and provenance

Local primary sources inspected:

- `local_references/HCM7 CH18 Urban Street Segments.pdf`, HCM 7.0, Chapter 18.
- `local_references/HCM7 CH30 Urban Street Segments Supplemental.pdf`, HCM 7.0, Chapter 30.
- `local_references/HCM 7th.pdf`, complete local HCM7 PDF. Sampled Chapter 18 pages agree with the standalone Chapter 18 source.
- The official HCM7 [corrections, clarifications, and updates through December 2022](https://hcmvolume4.org/wp-content/uploads/2024/10/HCM7-corrections-clarifications-updates-12-2022.pdf) was reviewed. No material Chapter 18 or Chapter 30 methodology correction was identified in that list. This does not establish that no later official interpretation exists.

All equation descriptions below are paraphrases or compact formula transcriptions; no substantial HCM passage is reproduced. Chapter/page/exhibit references use HCM printed pagination.

## Scope and boundary conditions

Chapter 18 evaluates a segment bounded by intersections, measured stop-line to stop-line (or yield-line equivalent) along the street centerline. Link length used in calculations is segment length less upstream intersection width. Each direction is evaluated separately. Segment LOS combines link performance with the downstream boundary intersection; HCM does not define link-only LOS. See Chapter 18 pp. 18-4–6, 18-19, 18-38–39.

The method’s general control coverage includes signalized, two-way STOP, all-way STOP, and YIELD-controlled boundaries; ramp terminals use Chapter 23, and roundabouts require Chapter 30 §9, including geometric delay. The first engine qualification is narrower: conventional signalized boundaries matching Example Problem 1. Other control types require their own accepted fixture and behavior qualification. See Chapter 18 pp. 18-8–13, 18-34–35; Chapter 30 §9.

The analysis period is 15 minutes to 1 hour; 15 minutes is the operational default and the most useful period for capturing peaks. The first acceptance fixture uses a 15-minute period. Short signalized segments can be unreliable where cyclic spillback occurs; Chapter 18 gives approximately 700 ft as a short-segment warning heuristic and identifies an upper segment length of 2 mi. See Chapter 18 pp. 18-10–13, 18-20, 18-23–27.

A qualified bounded result requires consistent period/direction data, already balanced and capacity-adjusted demand, no unresolved capacity metering, and no spillback that invalidates the analysis. The HCM Example Problem 1 reports its Step 1 balance and spillback check; the bounded engine will take those as preconditions rather than claim it performs the complete Step 1 process.

## External downstream performance contract

Keep these quantities distinct:

- **v_m**: midsegment demand flow rate used by Eq. 18-6 and access-delay methods.
- **v_th**: downstream through demand flow rate.
- **c_th**: downstream through-movement capacity.
- **d_t**: final downstream through delay used in the travel-time path. For the signalized first scope, this is the externally qualified through control delay; conventional three-/four-leg geometric delay is considered negligible.

Chapter 18 defines through control delay as control delay to the through movement at the downstream boundary. Where lane groups serve the movement, HCM weights their delays by their share of through vehicles. Capacity is similarly aggregated by lane-group capacity weighted by its share of through vehicles. The LOS v/c is downstream through demand divided by this through-movement capacity. Do not substitute an approach-average delay, whole-intersection delay, critical v/c, or unrelated lane-group delay. See Chapter 18 pp. 18-20–21, 18-35, 18-39.

The first engine accepts an externally qualified final through delay and aggregate through capacity. It does not add an internal lane-group aggregation algorithm. The external evidence must identify control type, subject direction, through movement, analysis period, HCM edition/method when known, source/tool/run note, final through delay, final through demand, and final through capacity. The values must refer to a consistent analysis.

Supplying final through delay allows the bounded travel-speed path to bypass internal Chapter 18 Steps 3–5: arrival-during-green and phase-duration calculations produce the downstream delay that Eq. 18-15 consumes. It does not waive the Step 1 preconditions above, nor other inputs required by the bounded equations (notably v_m, v_th, c_th, control type, geometry, access delay, and applicable other delay). For coordinated signals, progression/upstream filtering must already be reflected in the supplied final delay; do not apply progression again.

For the Example Problem 1 boundary, v_m=1,150 veh/h, v_th=968 veh/h, c_th=1,848 veh/h, and d_t=18.310 s/veh. The qualified path must require v_m explicitly; it must not substitute v_th.

## Equation and exhibit crosswalk

| HCM item | Role, inputs, units and domain | First-engine treatment |
|---|---|---|
| Eq. 18-1; Ex. 18-7, p. 18-19 | Optional default access-count path. N_ap,s = 0.5 D_a L / 5,280, with density D_a in points/mi and length L in ft. Ex. 18-7 depends on area type, median type, and speed-limit columns 25–55 mph. | **Deferred.** Require explicit documented access counts. No inferred table interpolation/default behavior; fail closed if explicit inputs are missing. |
| Eq. 18-2, p. 18-21 | TWSC uncontrolled through-capacity calculation: c_th = 1,800(N_th − 1 + p*0,j), where p*0,j comes from Chapter 20 Eq. 20-43 and is 1.0 when a major-street left-turn bay is present. | **Deferred.** First scope is signalized; accept aggregate c_th externally. |
| Eq. 18-3; Ex. 18-11, p. 18-28 | Base free-flow speed: S_fo = S_calib + S_0 + f_CS + f_A + f_pk. Ex. 18-11 note equations: S_0 = 25.6 + 0.47 S_pl; f_CS = 1.5 p_rm − 0.47 p_curb − 3.7 p_curb p_rm; f_A = −0.078 D_a/N_th; f_pk = −3 p_pk; with explicit counts D_a = 5,280(N_ap,s + N_ap,o)/L_link. Inputs include speed limit, calibration (mi/h), restrictive-median proportion, curb/parking proportions, explicit subject/opposing access counts, link length, and through lanes. | **Calculate internally.** Report all intermediate terms. Example fixture uses S_calib=0; do not imply this is locally calibrated for Thailand. |
| Eq. 18-4, p. 18-29 | Signal/control spacing adjustment f_L = 1.02 − 4.7(S_fo−19.5)/max(L_s,400), capped at 1.0. L_s is the distance between bracketing intersections that require stop/yield on the subject movement. | **Calculate internally.** Require valid spacing and HCM control interpretation. |
| Eq. 18-5, p. 18-29 | Free-flow speed S_f = max(S_fo f_L, S_pl); alternatively field-measured S_f may be input, but S_fo is still needed for LOS. Speeds in mi/h. | **Calculate internally** in first fixture path. Measured-speed override is deferred. |
| Eq. 18-6, p. 18-30 | Vehicle-proximity factor f_v = 2/[1+(1−v_m/(52.8N_thS_f))^0.21]. Uses v_m in veh/h, N_th lanes, S_f in mi/h. | **Calculate internally** only for a valid real-valued domain. Negative/non-real base or invalid denominator => reject; never clamp to imitate a defensive implementation. |
| Ex. 18-13, p. 18-31 | Planning estimate of per-point delay (s/veh/point), table rows 200–700 veh/h/lane and columns 1–3 lanes; baseline 10% left and 10% right turns. HCM text allows proportional reduction below those turn percentages and 0.5/zero multipliers for adequate turn bays. | **Deferred.** Require explicit qualified per-point d_ap,i. Do not interpolate/extrapolate or clamp unsupported values. |
| Eqs. 18-7/18-8, pp. 18-31–32 | Running time: t_R = ((6−l_1)/(0.0025L))f_x + (3,600L/(5,280S_f))f_v + Σd_ap,i + d_other. Here L is ft; t_R and delay terms are seconds or s/veh as applicable. f_x=1 for signal/STOP, 0 for uncontrolled, min(v_th/c_th,1) for YIELD; l_1=2.0 s for signal and 2.5 s for STOP/YIELD. N_ap=N_ap,s + p_ap,lt N_ap,o. | **Calculate internally** for the signalized first scope, supplied access delays, explicit access geometry/counts, and explicit supported d_other. Other controls deferred. |
| Eq. 18-9, p. 18-34 | Arrival proportion during green P; depends on arrival profile, downstream lane-group flow, cycle, and effective green. | **Deferred/bypassed** when final qualified downstream through delay is supplied. |
| Eq. 18-10, pp. 18-35–36 | HCM lane-group weighting for signalized through delay when through shares lanes with turns; uses lane-group delays, flows, lane counts, and turn shares. | **External aggregate required.** HCM rule is documented here; no new internal aggregation in v1. |
| Chapter 30 §4, Eqs. 30-31–30-68 | Computed access-point delay uses movement flows, lane/turn geometry, storage, conflicting flow and blockage procedures. | **Deferred.** The acceptance fixture supplies published per-point outputs from Ex. 30-35. |
| Eq. 18-15, p. 18-38 | Travel speed S_T,seg = 3,600L/[5,280(t_R+d_t)]; L in ft, time in s, speed in mi/h. | **Calculate internally** from t_R and final external d_t. |
| Eq. 18-16, p. 18-38 | Spatial stop rate H_seg = 5,280(h+h_other)/L, requiring boundary full-stop rate h and other stops h_other. | **Deferred output** in v1; it is not needed for travel speed/LOS. |
| Ex. 18-1, pp. 18-38–39 | Motorized LOS based on travel speed relative to thresholds interpolated by base FFS S_fo plus the downstream through v/c rule. BFFS domain is 25–55 mph. | **Calculate internally** only inside the table domain; strict greater-than comparisons; reject outside domain rather than extrapolate. |

### Fail-closed and LOS rules

- Reject Eq. 18-6 when its fractional-power base is negative or otherwise outside the real-valued domain. CrossTraffic’s protective clamp is not an HCM rule.
- Do not silently supply Exhibit 18-7 defaults or infer unresolved lookup interpolation. Do not interpolate, extrapolate, or clamp Exhibit 18-13 outside a method explicitly qualified from primary HCM evidence.
- Ex. 18-1 A–E thresholds use strict greater-than comparisons; equality goes to the next lower LOS.
- If downstream through v/c > 1.0, LOS is F regardless of travel speed. At exactly 1.0 the v/c rule alone does not force F; apply speed thresholds.
- Do not extrapolate Ex. 18-1 thresholds outside the 25–55 mph BFFS domain.
- Unresolved demand balancing, capacity metering, invalidating cyclic/sustained spillback, or material unmodeled midsegment delay must fail closed or require an explicit supported input.
- Keep the LOS rule distinct from qualification of the speed estimate: v/c > 1.0 forces LOS F, while queue carryover/spillback that violates the bounded assumptions invalidates the operational travel-speed result itself.

## Chapter 30 §8 Example Problem 1 acceptance fixture

Source: Chapter 30 §8, pp. 30-48–56, Exhibits 30-26–30-36. The example is operational, coordinated-actuated, and 15 minutes. It includes demand adjustment/balance and a spillback check, which the bounded engine treats as external preconditions.

Published inputs and outputs are distinguished from formula-derived intermediates:

| Quantity | Value | Evidence/status |
|---|---:|---|
| Segment length; upstream intersection width; link length | 1,800 ft; 50 ft; 1,750 ft | Published, Ex. 30-30 |
| Through lanes; speed limit | 2 per direction; 35 mi/h | Published, Ex. 30-30 |
| Restrictive median; curb; parking | 0; 0.70; 0 | Published, Ex. 30-30 |
| Access counts, subject/opposing | 4 / 4 | Published, Ex. 30-30 |
| Midsegment flow v_m | 1,150 veh/h | Published/derived from entering approach movements (1,000 through + 50 right + 100 left), Ex. 30-29; distinct from v_th |
| Downstream through demand/capacity | 968 / 1,848 veh/h | Published, Ex. 30-32 and Ex. 30-36 |
| Final downstream through delay d_t | 18.310 s/veh | Published, Ex. 30-36 |
| Per-point access delay | 0.193 and 0.194 s/veh | Published, Ex. 30-35; supplied inputs for v1 |
| S_0; f_CS; f_A; f_pk | 42.05; −0.329; −0.941; 0 | Formula-derived from Ex. 18-11 inputs |
| S_fo; f_L; S_f; f_v | 40.78; 0.9644; 39.33; 1.034 | S_fo is published Ex. 30-36; remaining values formula-derived |
| Total access delay; running time | 0.387 s/veh; 33.54 s | Access sum from Ex. 30-35; running time published Ex. 30-36 |
| Running speed; travel speed | 36.59; 23.67 mi/h | Published, Ex. 30-36 |
| Through v/c; LOS | 0.52; C | Published, Ex. 30-36; unrounded ratio 968/1,848 = 0.52381 |

HCM’s interpolated thresholds at S_fo=40.78 mi/h are A >32.6, B >27.5, C >20.5, D >16.3, E >12.3 mi/h; the 23.67 mi/h result is LOS C. Stop rate 0.547, spatial stop rate 1.61, perception score 2.53, and no spillback are also shown in Ex. 30-36, but are not required bounded-v1 outputs. CrossTraffic’s internal P result is not an acceptance output.

## Thailand/LHT qualification gates

Engine numerical qualification may proceed against the HCM right-hand-traffic reference fixture using explicit HCM physical-side semantics. That qualification makes no Thailand-qualified claim. Keep sided inputs explicit and never automatically mirror them.

Thailand/LHT production qualification remains separate and gated:

| Term | Classification | Required treatment |
|---|---|---|
| Length, lane count, speed, direction-specific demand/capacity/delay | Orientation-neutral | Preserve direction and boundary identity. |
| Restrictive-median length | Orientation-neutral geometrically | Preserve movement definitions for turn-dependent effects. |
| Curb and parking proportions | Requires LHT reinterpretation | HCM defines these on the right side in direction of travel; map to the correct physical side before Thai use. |
| Subject/opposing access counts | Requires LHT reinterpretation | Preserve HCM side labels explicitly; validate physical mapping. |
| Opposing-side left-turn accessibility, left/right turns, inside lane, turn bays | Requires LHT reinterpretation | Validate movement and storage semantics for LHT. |
| Diagram/map reflection | Presentation-only mirror | Permitted only after sided meanings are mapped; never mirror numerical values automatically. |
| Thai calibration/local qualification | Unresolved / fail closed | HCM example’s S_calib=0 is not Thai calibration evidence. |

## CrossTraffic independent implementation evidence

CrossTraffic was inspected only as independent implementation/cross-validation evidence; HCM 7.0 remains the methodology authority. The checked-in transportations-library fixture and CrossTraffic WASM boundary test agree with the Chapter 30 Example Problem 1 values and intermediates listed above.

Behaviors intentionally not adopted:

- Its Eq. 18-6 defensive clamp is implementation-specific, not an HCM instruction.
- Its Exhibit 18-13 helper clips values to 200–700 veh/h/lane and 1–3 lanes; those clamps are not HCM authority.
- Its LOS helper clamps BFFS to 25–55 mph; this engine instead rejects outside the HCM table domain.
- The library can default omitted midsegment flow to through demand. That is unsafe for the acceptance fixture because 1,150 ≠ 968; the qualified contract requires explicit v_m.
- A CrossTraffic boundary test reports uniform-arrival P=0.486 while the HCM Example Problem 1 coordinated output includes P=0.493. This is outside the v1 contract because final d_t is supplied; the bounded engine does not claim internal progression reproduction.
- The MCP Chapter 18 tool docstring refers to Exhibit 18-8 for LOS; HCM motorized LOS is Exhibit 18-1, and the library helper is named for Exhibit 18-1. Treat this as a documentation discrepancy.
- The transportations-library Chapter 18 narrative describes Chapter 30 §4 computed access delay as deferred, while newer integration tests include a computed §4 case. Tests/code may be newer than that narrative.

The inspected transportations-library repository carries both LICENSE-MIT and LICENSE-APACHE. No CrossTraffic implementation source is to be copied; the Chapter 18 engine must be independently implemented from HCM methodology.

## Protected-engineering constraints

The repository’s Python engine remains the sole numerical authority. Any future Chapter 18 engine is additive, framework-independent, and must not change the seven existing qualified engines. Numerical inputs that affect interpretation belong in the persisted input/fingerprint contract; provenance and assumptions must remain auditable. No Chapter 18 formula belongs in TypeScript.

## Qualification and release gates

**Engine acceptance requires:**

1. Test-first implementation from this accepted HCM crosswalk.
2. Reproduction of Chapter 30 Example Problem 1 to tolerances based on HCM’s printed precision, including intermediates.
3. Explicit invalid-domain/fail-closed tests and strict LOS-boundary tests.
4. Tests that distinguish v_m from v_th and reject missing v_m.
5. External downstream provenance and through-delay/capacity contract tests; no approach/intersection average substitution or double progression.
6. Unit equivalence and full regression evidence; the existing seven numerical engines remain unchanged.
7. Fresh-context independent methodology and code review before engine acceptance.

**Application/Thailand release additionally requires:**

- persisted provenance and Project v2/fingerprint/current-stale/report/export integration;
- API/UI/Handbook work and EN/TH presentation;
- validated Thailand/LHT physical-side mapping and localized qualification;
- browser/deployment qualification.

## Research-gate verdict

**GO WITH CONDITIONS — primary methodology research is sufficient to authorize a separate bounded Chapter 18 Python engine qualification work package.**

Optional Exhibit 18-7 defaults and Exhibit 18-13 planning shortcuts are excluded from the first engine and do not block that numerical qualification. Thailand/LHT production mapping is a later release gate, not a blocker to numerical HCM qualification against the HCM reference fixture.

This verdict does not authorize a claim of complete operational Chapter 18 network/intersection analysis or Thailand-ready production support. Issue #172 remains open through engine and application qualification.
