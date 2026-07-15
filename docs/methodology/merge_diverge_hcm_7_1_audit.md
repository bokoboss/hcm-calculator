# HCM 7.1 Merge and Diverge Audit

## Decision

`hcm_7_1` is a known but unqualified method version for Merge Segment and
Diverge Segment in Phase 14.1. It must not route into the HCM 7.0 engine, share
HCM 7.0 coefficients by default, or be accepted in a project file as a
calculated method. A future implementation requires a separate qualification
gate with official examples, input models, equations, boundaries, and
version-isolation tests.

## Authoritative Sources

| Source | Status | Use |
| --- | --- | --- |
| National Academies, `Highway_Capacity_Manual_Edition_7.1_Chapters.pdf`, November 2025 | Finalized official HCM Edition 7.1 replacement Chapters 13, 14, 27, and 28 | Governing source for any future HCM 7.1 path |
| NCHRP Research Report 1038 / NCHRP 07-26 | Research basis for HCM 7.1 replacement chapters | Background only after finalized HCM 7.1 text is available |
| McTrans HCS 2025/2026 version and update pages | Implementation/version evidence | Confirms HCS exposes HCM 7/HCM 7.1 selection and flags material method change |
| Local HCM 7.0 Chapter 14 | Prior method | Comparison baseline only |

The official 7.1 PDF states that it contains replacement Chapters 13, 14, 27,
and 28 for Edition 7 and that the replacement chapters are based on NCHRP
Research Report 1038. It was inspected as web-accessible official material; no
source PDF or extracted text is committed.

## Version Difference Register

| Finding | Merge | Diverge | Classification | Implementation Effect |
| --- | --- | --- | --- | --- |
| Chapter 14 is replaced, not amended in place | yes | yes | `changed_in_hcm_7_1` | Require separate `hcm_7_1` package and tests |
| 7.1 flowchart has four primary steps and estimates speed before capacity/density | yes | yes | `changed_in_hcm_7_1` | Do not reuse HCM 7.0 step order as implementation authority |
| 7.1 uses `SM` and `SD` ramp-influence speeds and density equations based on speed and flow | yes | yes | `changed_in_hcm_7_1` | HCM 7.0 density regression equations are not reusable |
| 7.1 capacity check exhibits focus neighboring segment/ramp checks rather than HCM 7.0 maximum desirable flow exhibits | yes | yes | `changed_in_hcm_7_1` | Capacity result model must be re-audited from 7.1 |
| 7.1 Chapter 14 includes capacity checks for neighboring freeway segments and multilane/C-D segments | yes | yes | `changed_in_hcm_7_1` | C-D/multilane handling cannot inherit 7.0 approximate policy |
| 7.1 still limits LOS density definitions to stable flow and sends LOS F/congestion to facility analysis | yes | yes | `same_as_hcm_7_0` at policy level | Null speed/density policy still needs equation-specific review |
| 7.1 extensions include one-lane lane additions/drops, two-lane ramps without lane addition/option-lane cases, major merge/diverge, managed lanes | yes | yes | `changed_in_hcm_7_1` | Geometry contract differs from 7.0 extensions |
| 7.1 major diverge density model remains a special extension | no | yes | `same_as_hcm_7_0` concept, `changed_in_hcm_7_1` source numbering | Separate major-diverge support gate |
| McTrans says HCS 2025 release 8.4 adds HCM 7.1/NCHRP 07-26 single-segment merge/diverge/weaving analyses | yes | yes | `software_specific` for HCS behavior, `changed_in_hcm_7_1` for method existence | HCS screenshots/reports must record selected HCM method |
| McTrans update page says current HCS can choose HCM 7 or HCM 7.1 and highlights 35 pc/mi/ln capacity-density change from NCHRP | yes | yes | `software_specific` corroboration | Treat current-HCS output as contaminated unless method version is explicit |

## HCM 7.1 Implementation Eligibility

Not eligible in Phase 14.2 unless all of the following are completed:

1. Visually transcribe and review the HCM 7.1 Chapter 14 input domain,
   equations, exhibits, boundaries, capacity checks, and extension rules.
2. Independently transcribe Chapter 28 HCM 7.1 examples and published
   intermediate values.
3. Define separate HCM 7.1 typed inputs for speed-based merge/diverge method
   variables and geometry, including any changed two-lane ramp and lane
   add/drop rules.
4. Create HCM 7.1-only equation tests, example fixtures, boundary tests, and
   HCM 7.0/7.1 import-isolation tests.
5. Decide whether first-release HCM 7.1 scope is core one-lane right-side only
   or includes any extensions; document unsupported geometry explicitly.
6. Confirm all capacity/failure/null behavior from HCM 7.1, not from HCM 7.0
   or HCS reports.

## Contamination Controls

- Every source record, fixture, project type, and result must carry
  `method_version`.
- `hcm_7_0` engines must reject HCM 7.1 example IDs, replacement-chapter
  source references, 7.1 equation labels, and speed/capacity model terms.
- HCS 2025/2026 report observations are admissible only if the selected HCM
  method is recorded. Software version alone is not enough.
- Any mention of volume served, queues, work-zone analysis, expanded lane
  add/drop support, or HCM 7.1 capacity-density changes is quarantined from
  the HCM 7.0 implementation.
- A future HCM 7.1 implementation must not be a flag inside the HCM 7.0 module.
  It needs separate coefficients and dispatch.

## Unresolved Blockers

| Blocker | Impact |
| --- | --- |
| HCM 7.1 Chapter 28 examples not independently transcribed | No official validation fixtures |
| HCM 7.1 input and geometry boundaries not fully mapped | No support contract |
| Capacity and above-capacity semantics need direct 7.1 review | Cannot safely decide null outputs |
| HCS dual-method output not available with selected-method proof | No software comparison baseline |
| Extension domains are broader than likely first release | Risk of exposing unsupported geometry |
