# Phase 16.2 Multilane UX Pilot Implementation

Status: implementation and local qualification complete; PR/CI/merge status is tracked separately.

Authoritative baseline: `72d9de8841db8e158077372bf60df93a9f5bcdab` (`origin/main`)

Package version: `0.8.0`

Scope: Multilane Highway Segment only. This is a presentation and workflow refactor. It does not add HCM methodology.

## Problem and decision

The existing Multilane worksheet was numerically sound but presented measured and estimated FFS controls, PCE mode, terrain, Truck Mix, project actions, and engineering evidence as competing peers. That increased cognitive load and made stale-result recovery harder to discover.

The simpler-alternative review rejected copy-only changes because they would leave the irrelevant controls visible, and rejected a wizard because the repository requires a single-page guided worksheet. The selected solution is progressive disclosure inside the existing page, with a UI-only adapter that emits the existing engine inputs.

## Implemented flow

The page now follows this single-page hierarchy:

1. **Start** — Template / Blank case, Unit system, and subordinate Load project.
2. **Traffic and segment** — lanes, length, demand, PHF, and Heavy Vehicle % of total traffic.
3. **Free-flow speed** — one Measured/Estimated choice; only the active branch fields are rendered.
4. **Heavy-vehicle adjustment** — one General terrain / Specific grade / External PCE choice.
5. **Calculate / Recalculate** — the primary action is explicit after active input changes.
6. **Result summary** — LOS hero, density support, demand/capacity, mean speed, capacity, status, flow, adjusted FFS, PCE, and heavy-vehicle factor.
7. **Result actions** — project save and report export before a single Details / engineering record expander.

Before a calculation, project load is available but subordinate. With a stale result, metrics and report exports are hidden, the stale message is explicit, and project save remains available according to the existing contract.

## Heavy-vehicle mapping

The user-facing three-way choice maps to the existing engine-native fields; no localized label is stored as an enum.

| User choice | Active UI fields | Existing engine mapping |
| --- | --- | --- |
| General terrain | Level or Rolling | `terrain_type=level|rolling`, default supported `truck_mix`, internal PCE, neutral grade `0.0` |
| Specific grade | Grade %, segment length, Heavy-vehicle composition | `terrain_type=specific_grade`, selected `truck_mix`, internal grade PCE |
| External PCE | Engineer-supplied PCE | `terrain_type=specific_grade`, default supported `truck_mix`, user PCE, neutral grade `0.0` |

Measured FFS emits a measured `free_flow_speed_mph` and nulls estimated geometry. Estimated FFS emits posted speed, lane width, lateral clearances, median, and access density; divided median alone activates left clearance. Inactive fields are not validated, do not affect the normalized fingerprint, and do not reach the engine.

Legacy UI payloads containing `pce_mode`, `terrain_type`, and the prior Truck Mix structure remain accepted by the adapter. The new task-oriented payload is translated at the UI boundary; the calculation method, result contract, project schema, and report payload fields remain unchanged.

## Truck Mix and PCE wording

The UI now labels Truck Mix as **Heavy-vehicle composition (SUT/TT)** and explains:

> Heavy-vehicle composition is the SUT/TT mix within the heavy-vehicle portion of traffic.

It also states that the internal HCM lookup supports only 30/70, 50/50, and 70/30 table compositions, that other observed compositions should use External PCE, and that no Truck Mix interpolation is applied. External PCE copy states that the internal lookup is bypassed and the value must be established and traceable separately by the engineer.

Heavy Vehicle % is explicitly defined as the percentage of total traffic composed of heavy vehicles, distinguishing it from the SUT/TT mix within the heavy-vehicle portion.

## State, projects, fingerprints, and exports

Compatibility checks preserve:

- project schema `1.2`;
- project type `manual_multilane_v0`;
- method identifier `hcm7_multilane_los`;
- result contract `phase_8`;
- normalized-input and fingerprint comparison behavior;
- current/stale result protection;
- project JSON and existing CSV/Markdown/Excel/Report JSON export formats;
- Chapter 26 Example 4 EB/WB presets and bounded support behavior.

Project round-trip tests cover blank/task values, measured and estimated FFS, general terrain, specific grade, External PCE, Metric, Imperial, and retained current results. Existing v0.8 project inputs continue through the legacy adapter path without schema migration.

A real-browser defect was found and fixed during qualification: after a result, switching from English to Thai could leave a formatted unit segmented-control value in Streamlit state and raise `ValueError: unit_system must be metric or imperial`. Canonical pre-widget normalization now protects unit, FFS-source, and heavy-method state across locale reruns. The regression is covered by AppTest and system-Chrome qualification.

## Numerical-equivalence evidence

The adapter tests compare the old UI contract and the task-oriented contract with exact equality for normalized engine inputs and exact result dictionaries. Coverage includes:

- measured FFS;
- estimated FFS;
- General terrain Level and Rolling;
- Specific grade 30/70, 50/50, and 70/30;
- External PCE;
- capacity-failure behavior.

The tests also verify that changing hidden/inactive values does not change the normalized input fingerprint, while changing an active field does produce a stale state. No tolerance was loosened and no numerical method code was changed.

## Browser qualification

Python Playwright 1.61.0 drove the local Streamlit server with system Chrome at `C:\Program Files\Google\Chrome\Application\chrome.exe`.

- 25/25 browser rows passed.
- Browser console/page errors: 0.
- Primary viewport: 1280 × 1100, English and Thai.
- Compact viewport: 768 × 1000, with no horizontal overflow observed.
- Covered: blank, measured, estimated, General terrain, Specific grade, External PCE, Truck Mix guidance, stable result, stale/Recalculate, capacity failure/correction, project save/load, report export, Metric/Imperial, and EN/TH.

Temporary screenshots, downloaded project/report files, and the matrix JSON/CSV are under `output/playwright/phase16_2_multilane_ux_pilot/` locally and are intentionally not committed.

## Before / after UX findings

The Phase 16.1 baseline exposed multiple technical decisions and inactive fields at once. The pilot materially improves the workflow by:

- reducing visible fields through measured/estimated and heavy-vehicle branch disclosure;
- separating total-traffic Heavy Vehicle % from within-heavy-vehicle SUT/TT composition;
- providing a clear External PCE escape path without exposing internal lookup controls;
- making Recalculate the explicit stale-state recovery action;
- surfacing LOS and density first, with engineering detail preserved behind one expander;
- separating project-save and report-export actions from the calculation entry path;
- retaining narrow-layout usability and Thai presentation without storing localized enums.

No numeric UX score is claimed; the evidence is behavioral, structural, and browser-based rather than a human time-on-task study.

## Known limitations

- Blank case is a UI starter and uses the existing validated fixture only as a static facility base; it is not a new HCM fixture.
- The calculator remains bounded to its existing one-direction Multilane Highway Segment scope and HCM table domain. Unsupported methodology is still rejected by the engine.
- Browser qualification is not a substitute for a moderated traffic-engineer usability study or a full accessibility audit.
- Other workflows were deliberately not redesigned in this change.

## Scrutinize verdict and rollout recommendation

Independent end-to-end review traced widget values through the UI adapter, engine validation/calculation, audit/session state, fingerprint freshness, project I/O, and report export. The material claims hold under unit tests, AppTest, and real-browser evidence. The review verdict is **ship** for the Multilane pilot.

Do not roll the pattern to Basic Freeway, Merge, Diverge, or other workflows in this change. Use Phase 16.3 for a human usability/accessibility review of the Multilane pilot and to decide which task-section patterns generalize cleanly before a separate rollout phase.
