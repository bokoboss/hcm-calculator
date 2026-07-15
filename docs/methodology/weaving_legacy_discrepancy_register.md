# HCM7 Weaving Legacy Discrepancy Register

## Audit boundary

Audited repository: `bokoboss/hcm7-weaving-segments`, `main` commit
`8bcdf89038329fbdc46dac286733d6d18f9f3504` (2025-10-07).  The audit covered
its complete five-commit history and current `README.md`, `index.html`,
`one-side.png`, and `two-side.png`.  There are no license, tests, fixtures,
build files, validation baselines, or calculation-only modules.  References in
this register point to HCM **Version 7.0** Chapter 13/27, the governing source
identified in [the crosswalk](weaving_chapter_13_crosswalk.md), not to the
legacy application's claims.

The application is a useful risk inventory but is not licensed or evidenced
well enough for code or image reuse.  Its single HTML file couples calculation,
DOM interaction, design search, sensitivity charting, and rendering; none is a
production implementation candidate.

## McTrans/HCS comparison addendum

McTrans/HCS is official implementation-reference evidence, not a replacement
for the HCM 7.0 column in this register.  Its current HCS 2025/2026 material is
mixed-version: the [official version history](https://mctrans.ce.ufl.edu/highway-capacity-software-hcs/version-history/)
states that HCS 2025 release 8.4 added selectable HCM 7.1/NCHRP 07-26
single-segment weave analysis, while [McTrans update news](https://mctrans.ce.ufl.edu/highway-capacity-software-hcs/hcs-update-news/)
states users can select HCM 7 or HCM 7.1.  Any observed current-HCS output
without an explicit HCM 7 selection is therefore unusable for parity.

| Register topic | HCM 7.0/project decision | HCS implementation evidence | Legacy comparison/action |
| --- | --- | --- | --- |
| Method version | v7.0 equations and 43 pc/mi/ln freeway LOS F density boundary govern | HCS 2025/2026 also offers 7.1 with a new method and 35 pc/mi/ln capacity-density statement | legacy’s undifferentiated “HCM7” claim is `unverified`; add version tag to every diagnostic comparison |
| C-D/multilane | freeway-only; v7.0 describes C-D/multilane as approximate | [HCS knowledge base](https://mctrans.ce.ufl.edu/highway-capacity-software-hcs/knowledge-base/) exposes “Highway or C-D Roadway” and asks for multilane-consistent FFS | HCS availability does not cure legacy `multilane_cd` overreach; retain `unsupported_overreach` |
| Option lanes / lane changes | LC inputs and N_WL must be geometry-derived and auditable | HCS says LC_RF, LC_FR, and N_WL are separate inputs; option-lane exit is not a lane change | legacy lacks an auditable option-lane geometry contract; retain `methodology_defect` and add option-lane tests |
| Movement coding | FF/FR/RF/RR remain HCM-defined | HCS labels LC_RF/LC_FR by movement | legacy labels require source-backed mapping, not HCS-output parity |
| Validation severity | malformed input vs unsupported scope vs HCM handoff are distinct | HCS information box presents error/warning/info; warning may accompany software adjustment | legacy’s permissive parsing/clipping is not validated by HCS; project must not normalize silently |
| Capacity/above capacity | only v7.0 `v/c > 1.00` stops speed/density | HCS history notes LOS/F and facility-analysis warnings, but current reports are mixed-version | legacy speed/density continuation remains a defect; HCS does not authorize a v7.0 alternative |
| Diagrams | redraw/provenance required | HCS option-lane diagrams are proprietary UX material | legacy PNGs remain not approved; do not reuse either source’s imagery |

| Legacy item | Legacy location | Legacy behavior/value | Governing HCM evidence | Classification | Risk | Required production action | Test implication |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Scope claim | README; `index.html:3,11,35` | Calls itself a complete HCM7 Ch. 13 tool | HCM 7.0 Ch. 13; no legacy source map | unsupported_overreach | high | Treat as secondary only | no parity test |
| Provenance | constants `569-600`, formulas `769-864` | Equation labels without edition/page/exhibit evidence | HCM 7.0 Ch. 13 pp. 13-18--29 | unverified | high | Independently map every rule | source-tag tests |
| Example validation | `1535-1591` | Loadable examples, no expected results | HCM 7.0 Ch. 27 | example_only_behavior | blocker | Create reviewed fixtures later, not branches | example regressions |
| SI/imperial conversion | UI helpers and labels | mixed UI conversion without a documented native contract | Ch. 13 native method units | unit_defect | high | Imperial engine, UI-boundary conversion only | round-trip/unit tests |
| `LS` | `769-864` | used in core formulas but no stop/audit record | Eq. 13-4, pp. 13-20--21 | boundary_defect | high | retain LS and applicability result | LS boundaries |
| `LMAX` | core calculation | calculated/used without a formal handoff result | Eq. 13-4; `LS >= LMAX` handoff | boundary_defect | high | explicit Chapter 12/14 stop | equality and above tests |
| Long segment | core/design | treats numerical search output as a solution | Ch. 13 p. 13-21 | methodology_defect | high | no weaving speed/density at/above LMAX | handoff test |
| Lane count | UI/compute | permissive lane inputs/table substitution | Ch. 13 pp. 13-5--8 | silent_clipping_or_extrapolation | high | validate configuration-specific N | invalid lane tests |
| Weaving lanes | core | exposes values without a typed configuration contract | one-sided NWL 2/3; two-sided 0 | boundary_defect | high | derive/validate, never infer | per-config tests |
| One/two-sided | UI options/core | broad toggle with unclear movement rule | Ch. 13 pp. 13-5--8 | methodology_defect | high | typed one/two-sided models | movement mapping tests |
| FF/FR/RF/RR labels | UI/core | labels not source-backed in audit record | Ch. 13 Exhibits 13-3--13-5 | unverified | high | canonical labels + diagram description | movement classification tests |
| Minimum lane changes | core equations | result is not fully traceable by config | Eqs. 13-2, 13-3 | confirmed_but_requires_refactor | high | separate one/two-sided equations | equation tests |
| Volume ratio | core | legacy interpretation not independently evidenced | Ch. 13 pp. 13-18--20 | unverified | high | rebuild from source | VR tests |
| Interchange density | FFS UI/core | accepts arbitrary values/units | Ch. 12 freeway FFS route | unit_defect | medium | source-tag `ID` and bounds | units/domain tests |
| Capacity units | `783,827` | mixes per-lane/segment labels and vehicle/pc presentation | Eqs. 13-5--10 | unit_defect | high | name every capacity with units | capacity identity tests |
| Capacity ordering | `783,827` | applies user CAF/SAF with no provenance | Eqs. 13-5--10; Ch. 12 CAF | methodology_defect | high | govern/order source-backed factor only | CAF tests |
| Vehicle-capacity conversion | core output | presents capacity without an auditable pc/veh convention | Eqs. 13-6, 13-8 | unverified | high | preserve pc/h; no unsupported conversion | unit tests |
| Heavy vehicles | `720-740`; form `389-408` | per-movement SUT/TT accepted | Eq. 13-1 and singular capacity fHV | deferred | high | first release common mix only | reject differing factors |
| HV composition | parser `1308-1315` | SUT+TT may exceed 100% | Chapter 12 Eq. 12-10 contract | methodology_defect | high | strict composition validation | >100% rejected |
| General/specific PCE | `PCE_DATA 569-600` | arrays lack source/table domains | Ch. 12 Exs. 12-25--28 | unverified | high | reuse only qualified shared tables | sentinel/table-domain tests |
| Truck mix | PCE selector | undocumented mix handling | Ch. 12 printed mixtures | unsupported_overreach | high | reject unprinted mix/domain | no extrapolation tests |
| Interpolation helper | `_interpolate1D 609-616` | endpoint clipping is implicit | Ch. 13 permits only stated lane-change interpolation | silent_clipping_or_extrapolation | high | explicit authorized interpolation only | endpoints/outside tests |
| Lane-width FFS | `_estimateFFS 618-666`, call `627` | reverses x/y into ascending-only interpolation; fLW becomes 0 for 10--12 ft | Ch. 12 FFS/exhibit route | transcription_defect | high | do not port; validate qualified helper | 10,10.5,11,11.5,12 ft |
| FFS endpoints | `_estimateFFS` | clips/table substitutes rather than rejects | Ch. 12 FFS/exhibit domain | silent_clipping_or_extrapolation | high | bounds-aware FFS contract | endpoint/outside tests |
| Grade/HV clipping | PCE helper | endpoint behavior not evidenced | Ch. 12 exhibits | silent_clipping_or_extrapolation | high | no unapproved clipping | grade/mix tests |
| One-sided weave capacity | `805,812` | hardcoded branch, unverified coefficients | Eq. 13-7 | unverified | high | source-coded with NWL 2/3 guards | candidate-capacity tests |
| Two-sided capacity | core | legacy treatment unproven | Eq. 13-7 says no NWL0 weaving-flow limit | methodology_defect | high | density capacity only when applicable | two-sided test |
| Oversaturation | `843-856` | may continue speed/density/LOS calculations | Ch. 13 p. 13-24 | methodology_defect | high | LOS F; speed/density Not predicted | v/c boundary tests |
| LOS | `classify_los` | facility branches include noncore categories | Ex. 13-6 | unsupported_overreach | high | freeway thresholds only | all LOS boundaries |
| `multilane_cd` | facility branch | claims multilane/C-D operational support | Ch. 13 p. 13-30 is approximate | unsupported_overreach | high | exclude/guard first release | unsupported-scope test |
| Ch. 12 route choice | FFS/PCE core | conflates freeway and multilane paths | Ch. 12 + Ch. 13 freeway core | methodology_defect | high | select only qualified freeway helpers | contract tests |
| Design mode | `897-956`, especially `917-954` | 50--3000 m, 20-iteration search; internally treats `LS_ge_LMAX` as pass, but final prose says no target is met before non-weaving when no density pass exists | Ch. 13 operational method and LMAX handoff | non_hcm_numerical_wrapper | high | defer; never accept non-weaving as a target-LOS solution | design/handoff separation test |
| Sensitivity mode | `1049-1084` | chart connects gaps (`spanGaps`) | no HCM sensitivity method | non_hcm_numerical_wrapper | medium | defer | no chart behavior |
| Defaults/placeholders | form and examples | values can become engineering inputs silently | project audit contract | methodology_defect | high | required explicit inputs/provenance | default/unknown-key tests |
| Diagram assets | `one-side.png`, `two-side.png`; commit `00bd48c` | source/ownership/correspondence undocumented | no provenance evidence | asset_not_approved_for_reuse | medium | redraw or obtain written provenance | provenance review |
| License | repository history | no LICENSE/COPYING/NOTICE; README “Open Source” only | no reuse grant | asset_not_approved_for_reuse | high | do not copy code/assets | legal gate |
| CDN dependencies | `index.html:6-10,317,567-568` | mutable Tailwind/Chart/fonts/raw-main images | reproducibility requirement | deferred | low | no production dependency reuse | N/A |

## Reconciliation notes

### Literal legacy coefficient and table inventory

The following inventory makes grouped legacy evidence reproducible without
endorsing any value.  Every item remains subject to the classifications above:

| Legacy group/location | Literal inventory | Register treatment |
| --- | --- | --- |
| `562-566` | `FT_PER_M`, `MI_PER_KM`, `KM_PER_MI`; freeway density thresholds `[10,20,28,35,43]`; multilane `[12,24,32,36,40]` | units/LOS rows |
| `569-572` | Exhibit-12-4-like FFS/capacity maps: freeway 55--75 mi/h to 2,250--2,400 and multilane 45--70 to 1,900--2,300 | provenance/FFS/LOS rows |
| `573-589` | lane width 10/11/12 ft -> 6.6/1.9/0; RLC 0--6 with lanes 2--5; TLC 0--12 with lanes 2/3 | lane-width defect/FFS endpoint rows |
| `590-601` | PCE dimensions: truck % 2,4,5,6,8,10,15,20,25; mixes 30/70,50/50,70/30; grades -2,0,2,2.5,3.5,4.5,5.5,6; length cells about .125--1.5 mi | PCE/truck-mix/clipping rows |
| `643,655,662,734` | ramp-density coefficient 3.22 and exponent .84; undivided-median 1.6 mi/h; APD 0--40 to 0--10; general ET 2/3 | FFS/PCE provenance rows |
| `805,812-817` | LMAX 5,728/1,566; density capacity 438.2/.0765/119.8; weaving limits 2,400/3,500 | LMAX/capacity rows |
| `842-850` | lane-change constants .39,300,10,000,.206,.542,192.6,2,135,.223,1,300/1,950/650 | lane-change/interpolation rows |
| `853-856` | speed constants .226,.789,15,.0072,.0048 | speed/oversaturation/provenance rows |

The most concrete confirmed numerical defect is the reversed lane-width
interpolation call.  Direct evaluation at each valid 10--12 ft point produces
zero lane-width reduction, which contaminates estimated FFS and downstream
capacity/speed/density/LOS.  This is not a rounding difference.

Chapter 27 Example 3 also contains a governing-source ambiguity: it defines
nonweaving flow as 4,995 pc/h but later uses 5,015 pc/h in the nonweaving
lane-change chain.  The legacy result must not decide which is correct; a
production implementation follows the equation-defined sum and records the
published intermediate as an example tolerance exception.
