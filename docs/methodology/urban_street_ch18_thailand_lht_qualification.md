# HCM 7 Chapter 18 — Thailand/LHT Qualification Boundary

Status: **NEEDS MORE EVIDENCE for a general Thailand/LHT semantic adapter. GO WITH CONDITIONS only for orientation-neutral behavior and a narrowly restricted side-neutral subset.**

Parent authority: Issue #172  
Research/qualification work package: Issue #179  
Accepted bounded engine: Issue #174 / PR #175  
Accepted application integration: Issue #176 / PR #177  
Baseline `main`: `e09042d6fba8bd7912801ee4615e548b98528d97`

## Decision

Do **not** implement a general Thailand/LHT adapter that automatically maps the HCM Chapter 18 right-hand-side curb, parking, or access variables to the physical left/kerbside of a Thai street.

The available evidence establishes Thailand's left-hand-traffic orientation and supports role-based LHT terminology in general traffic engineering, but the primary methodology evidence does **not** establish mirror equivalence for the calibrated Chapter 18 free-flow-speed model.

The accepted HCM numerical engine remains unchanged and retains its source-native HCM RHT-reference semantics.

This research does qualify:

1. the Chapter 18 inputs that are genuinely traffic-side invariant;
2. explicit external downstream performance for a correctly identified Thai/LHT through movement;
3. a narrow side-neutral subset in which unresolved right-side terms have no numerical contribution;
4. the evidence and validation required before broader Thailand/LHT support may be claimed.

## Why the earlier kerbside mapping is not accepted

The project-wide Thailand/LHT crosswalk already requires primary methodology evidence before converting a side-specific HCM source term to the opposite physical side. Geometric intuition or a presentation mirror is not sufficient.

The Chapter 18/NCHRP evidence confirms that the free-flow-speed coefficients are source-side specific:

- HCM defines `p_curb` as the proportion of the segment with curb on the **right-hand side**;
- HCM defines `N_ap,s` and `N_ap,o` using access-point approaches on the **right side** in the subject and opposing directions;
- the parking adjustment uses on-street parking available on the **right-hand side**;
- the model was calibrated from U.S. urban-street data.

Most importantly, the NCHRP Project 3-79 final report used to develop the methodology states that curb presence is based on the **right-hand side of the traveled way**, while curb presence on the **left-hand side is represented through median type**. The calibration data tables likewise record right-hand-side parking and right-hand-side/accessibility-based access variables.

Therefore changing a Thai input from physical right to physical left can change Eq. 18-3 and LOS for asymmetric streets. No metamorphic software test can prove that this methodological substitution is valid; such a test would only encode the assumption being tested.

## Primary methodology evidence

### NCHRP Project 3-79

Bonneson, Pratt, and Vandehey, *Predicting the Performance of Automobile Traffic on Urban Streets*, Final Report, NCHRP Project 3-79, Texas Transportation Institute / TRB, January 2008.

Author-hosted report index:
https://sites.google.com/site/jbreportsandtools/home/reports/hcm

The report's free-flow-speed model development states, in substance:

- curb presence is represented by an indicator for a curb on the right-hand side of the traveled way;
- left-side curb presence is represented through median type;
- calibration-site access data include right-hand-side approaches and left-side approaches only where accessible across the median;
- calibration-site parking data record parking on the right-hand side in the direction of travel.

This is stronger evidence than a generic LHT road-role analogy and blocks an automatic right-to-left coefficient transfer.

### HCM Chapter 18

The accepted local HCM 7 Chapter 18 research gate records the same source definitions in Exhibit 18-11 / Eq. 18-3:

- `p_curb`: curb on right-hand side;
- `N_ap,s`, `N_ap,o`: right-side access-point approaches;
- `p_pk`: right-hand-side on-street parking.

The Chapter 18 model is a U.S.-calibrated empirical model, not a geometry-only identity.

## External LHT evidence — useful but not sufficient for coefficient transfer

### Thailand traffic side

Thailand Road Traffic Act Section 39, Royal Thai Police English reference, establishes left-hand road operation:
https://www.royalthaipolice.go.th/downloads/laws/laws_03_05-07.pdf

### Malaysian and Australasian evidence

The Malaysian Highway Capacity Manual and Austroads/NZTA material support LHT concepts such as outer/kerbside and median-side roles. The Malaysian manual, for example, counts directional multilane access points on the left side in its own locally developed LHT methodology.

These sources show how LHT facilities are normally described. They do **not** establish that the U.S.-calibrated Chapter 18 right-side coefficients are unchanged when applied to the physical left side.

- MHCM 2011: https://crr.kkr.gov.my/en/dokumen/umum/WK.1.2011.84
- Austroads GTM Part 5: https://austroads.com.au/__data/assets/pdf_file/0023/342770/AGTM05-19_Guide_to_Traffic_Management_Part_5_Road_Management.pdf
- NZTA keeping-left guidance: https://www.nzta.govt.nz/driving-skills/learn-to-drive/roadcode/general-road-code/about-driving/key-driving-skills/keeping-left

## Thai empirical transferability evidence

No Thai Chapter 18 calibration dataset or accepted coefficient set was identified.

A 2024 Thai multilane-highway field study found material differences between measured Thai capacity and HCM 2010/2016 estimates for that facility. It is not a Chapter 18 study and does not provide a Chapter 18 correction factor, but it reinforces the need to avoid an unsupported “Thai-calibrated” claim.

- Srisurin & Amprayn (2024), DOI `10.14456/easr.2024.70`.

Bangkok signalized-intersection data also show that motorcycle composition can materially affect saturation flow and start-up lost time. This supports keeping downstream intersection capacity/delay externally qualified rather than adding an unvalidated Thai intersection model.

- Nakatsuji, Hai, Taweesilp & Tanaboriboon (2001), “Effects of Motorcycle on Capacity of Signalized Intersections,” DOI `10.2208/journalip.18.935`.

Neither source authorizes transferring Chapter 18 right-side curb/parking/access coefficients to the opposite side.

## Qualification matrix

| Concept | Thailand/LHT status | Required treatment |
|---|---|---|
| Segment length | **Qualified orientation-neutral** | Unit conversion only. |
| Upstream intersection width | **Qualified orientation-neutral** | Unit conversion only. |
| Signal/control spacing | **Qualified orientation-neutral** | Unit conversion only. |
| Through lane count | **Qualified orientation-neutral** | Preserve count. |
| Subject direction / through movement identity | **Qualified directional identity** | Preserve explicit Thai/LHT movement identity; no mirroring. |
| Posted speed | **Qualified orientation-neutral** | Unit conversion only. |
| `S_calib` | **Orientation-neutral parameter, Thai calibration unresolved** | No Thailand default; explicit user/local evidence only if claimed. |
| Restrictive-median proportion | **Qualified geometrically for the existing equation** | Preserve source definition; no side swap. |
| `curb_proportion` | **UNRESOLVED / source-side-sensitive** | Retain HCM right-hand source semantics or fail closed for a Thailand/LHT semantic workflow. Do not substitute physical-left kerbside value automatically. |
| `parking_proportion` | **UNRESOLVED / source-side-sensitive** | Same: no automatic right-to-left transfer. |
| `subject_side_access_count` / `opposing_side_access_count` | **UNRESOLVED / source-side-sensitive** | Preserve canonical HCM source semantics; do not relabel Thai kerbside counts as equivalent without evidence. |
| Explicit access-point delays | **Conditionally usable** | Must correspond to the actual physical Thai/LHT access geometry; however they do not by themselves remove the Eq. 18-3 access-density source-side issue. |
| `v_m` | **Qualified direction-specific** | Preserve subject-direction meaning. |
| External `v_th`, `c_th`, `d_t` | **Qualified as external boundary data** | Must describe the same Thai/LHT movement, period, and control; methodology/source must be auditable. |
| `d_other` | **Conditionally orientation-neutral** | Use only when source/scope is valid and no hidden side reinterpretation is introduced. |
| LOS thresholds / Eq. 18-6 / travel-time equations | **Qualified numerical kernel** | No traffic-side transformation; existing domain remains unchanged. |

## Restricted side-neutral Thailand/LHT subset

A narrowly bounded Thailand/LHT use can avoid the unresolved source-side transfer entirely when all Chapter 18 source-side terms have **zero numerical contribution**.

The minimum safe conditions are:

- `curb_proportion = 0`;
- `parking_proportion = 0`;
- `subject_side_access_count = 0`;
- `opposing_side_access_count = 0`;
- no access-point delay entries;
- no deferred turn/access procedure is invoked;
- downstream `v_th`, `c_th`, and `d_t` are externally qualified for the actual Thai/LHT through movement;
- the workflow is explicitly labeled **HCM-reference / not Thai-calibrated** unless a separately documented local `S_calib` is supplied.

Under these conditions, the unresolved right-versus-left variables do not affect the numerical path, so traffic-side mirroring is not required.

This subset is intentionally narrow and should not be marketed as general Thailand Chapter 18 support.

### Symmetric roadsides are not automatically accepted

Even if left and right curb/parking proportions happen to be numerically equal, that coincidence does not validate the empirical transfer of coefficients. It may make one specific numerical result insensitive to the choice, but it does not qualify the method generally. Any such use remains HCM-reference rather than Thailand/LHT-qualified unless the side-sensitive model is separately evidenced.

## Deferred/fail-closed scope

The following remain unqualified:

- automatic physical-left mapping for `p_curb`, `p_pk`, `N_ap,s`, or `N_ap,o`;
- Exhibit 18-13 planning access-delay turn/bay adjustments;
- `p_ap,lt` and opposing-side turn accessibility;
- Chapter 30 §4 left/right access-delay reinterpretation;
- internal lane-group aggregation where turn shares, storage, or bays require side interpretation;
- TWSC/YIELD/STOP conflict logic;
- Thailand motorcycle/PCE/capacity corrections;
- any Thailand default free-flow calibration.

## Persistence and architecture decision

### Existing RHT contract remains immutable

The accepted application contract:

`hcm7_ch18_bounded_signalized_15min_rht_reference_v1`

must not change meaning. Existing Project v2 fingerprints/results remain tied to that identity.

### Do not create the previously proposed general LHT method variant yet

The previously proposed identities such as:

`urban_street_segment_th_lht`

must **not** be implemented as a general method while the source-side Eq. 18-3 terms remain unresolved. A new method identity would make the unsupported mapping look qualified merely by versioning it.

If the restricted side-neutral subset is later implemented, it requires a contract name that states that restriction explicitly rather than implying full LHT support.

### Engine remains unchanged

No Chapter 18 equation or coefficient change is authorized.

## What evidence can unlock general Thailand/LHT support?

At least one of the following is required:

1. **Authoritative methodology interpretation** from TRB/HCM or the methodology authors explicitly establishing that the Chapter 18 right-side variables are intended as functional outside/kerbside variables and that the calibrated coefficients transfer unchanged under an LHT mirror; or
2. **Thailand/LHT empirical validation/calibration** using representative urban-street free-flow-speed data and physical-side variables, sufficient to validate the transferred coefficients or estimate a separately versioned Thai model.

A software metamorphic test alone cannot supply this evidence.

## Empirical-validation path if authoritative interpretation is unavailable

A future Thailand study should, at minimum:

- sample multiple urban street segments and directions across relevant speed limits, median conditions, lane counts, curb/parking conditions, and access densities;
- measure free-flow speeds under the HCM low-volume definition;
- record both physical-left and physical-right curb, parking, and access variables so alternative mappings can be tested;
- document motorcycle/mixed-flow composition;
- compare the source-right HCM model, kerbside-mirrored model, and locally recalibrated alternatives out of sample;
- quantify bias/error and coefficient uncertainty;
- preserve a validation set not used for calibration;
- version any accepted Thai coefficient profile rather than changing the HCM-reference kernel silently.

This is a methodology research project, not a UI localization task.

## Required software tests after the methodology boundary is accepted

Even before general LHT support exists, software must prove that:

1. the existing RHT contract and Project v2 fingerprints remain immutable;
2. no Thailand/LHT flag silently changes `curb_proportion`, `parking_proportion`, or access counts;
3. any restricted side-neutral contract rejects nonzero unresolved side-sensitive values;
4. external Thai/LHT movement identity/provenance is retained correctly;
5. the canonical Chapter 18 numerical engine remains serialized-equivalent for identical canonical inputs;
6. deferred turn/access procedures remain unavailable.

## Scrutiny result

**REPLAN for the previously proposed general role-mirrored adapter.**

The objective — safe Thailand/LHT use — remains valid, but the proposed automatic kerbside mapping crossed an evidence boundary. The revised direction is:

- preserve the accepted RHT-reference kernel and contract;
- qualify orientation-neutral pieces explicitly;
- optionally implement only a clearly named restricted side-neutral Thailand/LHT contract;
- keep general curb/parking/access-side mapping fail closed;
- pursue authoritative clarification or Thai empirical validation before broader support.

## Final research-gate verdict

**NEEDS MORE EVIDENCE for general Thailand/LHT Chapter 18 support.**

**GO WITH CONDITIONS for a restricted side-neutral subset** where unresolved right-side terms are zero and downstream through performance is externally qualified for the actual Thai/LHT movement.

This result is intentionally conservative. It prevents a presentation/localization change from becoming an unvalidated methodology change.