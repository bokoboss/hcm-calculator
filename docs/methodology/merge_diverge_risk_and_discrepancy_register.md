# Merge and Diverge Risk and Discrepancy Register

## Purpose

This register records Phase 14.1 risks that must be resolved or explicitly
accepted before implementing Merge Segment and Diverge Segment engines.

## Risks

| ID | Area | Risk | Severity | Phase 14.1 Decision | Phase 14.2 Action |
| --- | --- | --- | --- | --- | --- |
| MD-RISK-001 | Version contamination | HCM 7.1 replaces Chapter 14 and changes method structure; HCS 2025/2026 can select HCM 7 or HCM 7.1 | high | Treat `hcm_7_1` as known unqualified | Add import/source/version isolation tests |
| MD-RISK-002 | Merge/diverge symmetry | Similar variable names can hide different lane-distribution equations and adjacent-ramp branch rules | high | Separate method packages and tests | Build merge and diverge branches independently |
| MD-RISK-003 | Capacity semantics | Maximum desirable influence-area flow exceedance is not automatic LOS F, while freeway/ramp capacity failure is LOS F | high | Record distinct capacity/warning outcomes | Add tests for each capacity candidate |
| MD-RISK-004 | Units | Demand conversion uses `veh/h` to `pc/h`; capacity tables and CAF-adjusted values can be `pc/h` or `veh/h` depending on path | high | Preserve native units in every intermediate | Add unit-labeled result model and tests |
| MD-RISK-005 | Above capacity | Speed/density exhibits apply only to stable LOS A-E | high | LOS F gets null/not-predicted speed and density | Add exact-capacity and above-capacity tests |
| MD-RISK-006 | Adjacent ramps | Adjacent-ramp influence rules are asymmetric and limited to specific one-lane right-side ramp cases | high | First release supports only validated adjacent cases | Reject unsupported adjacent geometry explicitly |
| MD-RISK-007 | Lane-distribution adjustment | Six- and eight-lane reasonableness adjustments occur after method-specific `v12` prediction | medium | Share only after tests prove identical semantics | Add isolated tests for all lane-count branches |
| MD-RISK-008 | Geometry inference | Diagram selectors could hide calculation-relevant fields such as side, lane count, acceleration/deceleration length, option lane | high | Structured geometry is required; diagrams are not source of truth | UI must bind explicit fields, not infer from image |
| MD-RISK-009 | Two-lane ramps | HCM extensions modify effective lengths and isolation assumptions | medium | Exclude from first release | Separate extension audit before support |
| MD-RISK-010 | Left-side ramps | HCM 7.0 offers rational modifications but not a direct method | medium | Exclude from first release | Add separate support contract if implemented |
| MD-RISK-011 | Major merge/diverge | Major merge has no direct LOS model; major diverge has special density model | high | Exclude from first release | Implement only as separate extension phase |
| MD-RISK-012 | C-D/multilane | HCM/HCS mention approximate use beyond freeways | medium | Exclude from first release | Require measured FFS and validation evidence before expansion |
| MD-RISK-013 | Official examples | Chapter 28 examples require second transcription before fixtures | high | Documentation inventory only in Phase 14.1 | Create reviewed YAML fixtures in Phase 14.2 |
| MD-RISK-014 | HCS evidence | HCS reports may include volume served, queues, work zones, or HCM 7.1 outputs | medium | HCS is terminology/version evidence only | Compare only version-qualified HCM 7 reports |
| MD-RISK-015 | Image licensing | HCM/HCS figures are copyrighted/proprietary | medium | Do not commit or reuse source figures | Create original diagrams in Phase 14.3 |
| MD-RISK-016 | Queue/spillback | Off-ramp failures may involve ramp terminal or network spillback outside isolated method | high | Isolated method checks ramp roadway only and points to Chapter 23/38 | Add warning and unsupported external-analysis handoff |
| MD-RISK-017 | Existing helper reuse | Basic Freeway and Multilane helpers may bundle contracts not identical to Chapter 14 needs | medium | Reuse only source-identical pure helpers | Protect existing regressions during refactor |
| MD-RISK-018 | Supported-method claims | Documentation could imply implemented Merge/Diverge support | high | Do not update supported methods matrix as implemented | Keep no registry/UI/navigation changes |

## Source Ambiguities and Discrepancies

| ID | Observation | Impact | Resolution |
| --- | --- | --- | --- |
| MD-DISC-001 | Chapter 14 core method is calibrated for one-lane right-side ramps, but extensions describe additional geometries | First release could overstate support | Contract limits first release to core right-side one-lane ramps |
| MD-DISC-002 | HCM 7.0 allows approximate high-speed C-D/multilane applications, while HCS exposes a software option | Could expand product beyond validation | C-D/multilane excluded until separately validated |
| MD-DISC-003 | Lane additions/drops are described as Chapter 12-style handoffs, not ordinary ramp-influence calculations | Risk of coding a fake ramp method | Treat as unsupported/handoff in first release |
| MD-DISC-004 | Maximum desirable flow exceedance produces interpretation warning, not LOS F | Risk of false capacity failure | Separate warning status from capacity failure |
| MD-DISC-005 | HCM 7.1 HCS update material says current software includes queues/volume served and work zones | Risk of importing software behavior into HCM 7.0 | Quarantine as software-specific unless HCM 7.0 source supports it |

## Red-Team Checklist for Phase 14.2

Before merge, confirm that a future diff cannot:

- use `PFM` logic for Diverge or `PFD` logic for Merge;
- skip upstream/downstream freeway capacity checks;
- assign LOS F because maximum desirable influence-area flow is exceeded alone;
- mix `veh/h`, `pc/h`, and `pc/h/ln`;
- compute speed or density after a capacity failure;
- accept HCM 7.1 examples in an HCM 7.0 engine;
- infer calculation geometry from an image selector;
- expose left-side, two-lane, major merge/diverge, C-D, multilane, or managed-lane
  geometry without a support contract;
- stage HCM/HCS images, screenshots, OCR text, or source PDFs;
- update the supported-methods matrix as if Merge/Diverge were implemented.

## Open Questions

| Question | Needed Before |
| --- | --- |
| What exact Chapter 28 intermediate values and tolerances should fixtures use? | Phase 14.2 engine PR |
| Should first release include adjacent-ramp examples or only isolated core cases? | Phase 14.2 support envelope freeze |
| Should speed outputs be always calculated for stable cases or optional engineering outputs? | Result contract implementation |
| How should off-ramp queue storage warnings be represented without implementing Chapter 23/38? | Diverge validation and UI planning |
| Which original diagrams are required before product navigation exposes the workflows? | Phase 14.3 product integration |
