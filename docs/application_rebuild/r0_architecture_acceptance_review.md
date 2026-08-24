# Application Rebuild R0 — Architecture Acceptance Review

Status: **Accepted with clarifications incorporated by this review**
Date: 2026-08-24
Reviewed branch: `planning/application-rebuild-r0`
Reviewed PR: #129 — Application Rebuild R0: Product & Architecture Reset
Base: `main` at `8dc1481163d9864df71e2091ce23f0963b702e92`

## 1. Purpose

This document is the final cross-document architecture review for R0.

It checks the R0 product model, workflow architecture, result architecture, wireframes, design system, technology architecture, and prototype implementation plan against each other and against the qualified repository behavior.

This review is intentionally stricter than a documentation proofread. It looks for implementation traps such as contradictory ownership, dead navigation, serialized stale state, unproven release assumptions, and UI promises that have no persistence model.

Where this document clarifies or tightens an earlier R0 example, **this review takes precedence for R1/R2 implementation**. It does not change HCM numerical methodology or engine contracts.

## 2. Review outcome

**Disposition: ACCEPT R0 FOR IMPLEMENTATION AFTER THIS REVIEW IS MERGED.**

No blocker was found that requires reopening the product direction or replacing the selected architecture.

The selected direction remains appropriate:

```text
React + TypeScript + Vite SPA
        |
        | local HTTP / JSON
        v
FastAPI application/API boundary
        |
        v
Python application services
        |
        v
Existing qualified HCM engines
```

The review found several implementation ambiguities that could produce avoidable architecture drift if left implicit. They are resolved below as binding R1/R2 guardrails.

## 3. Findings summary

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| AR-01 | Major | Engine-supported method and new-frontend-delivered method were not explicitly separated | Resolved by dual availability rule |
| AR-02 | Major | Project v2 conceptual shape persisted `presentation_state`, risking serialized UI state becoming authoritative | Resolved by derived-state rule |
| AR-03 | Major | Home wireframe promised Recent Projects without a persistence/reopen model | Deferred; not required in R1/R2 |
| AR-04 | Medium | Release architecture assumed compiled SPA served by Python, while Gate R1 only required development-form launch | R1 gate strengthened |
| AR-05 | Medium | Loopback security baseline did not explicitly prohibit permissive cross-origin API access | Security rule strengthened |
| AR-06 | Medium | Project Overview examples could flatten Scenario rows and weaken `Analysis -> Scenario` hierarchy | Hierarchy clarified |
| AR-07 | Medium | Header toolbar examples could expose actions that are meaningless in Quick Analysis/Home contexts | Context-aware toolbar rule added |
| AR-08 | Medium | Project schema v2 remained conceptual without a dedicated schema acceptance gate before persistence work | R2C schema gate added |
| AR-09 | Low | Early R0 documents retain sequential draft/future-tense wording | README/review precedence handles this intentionally |

## 4. AR-01 — Separate engineering availability from frontend delivery

### Problem

R0 correctly makes the backend/application Analysis Registry authoritative for engineering method identity and supported scope.

However, R1/R2 intentionally migrates only representative methods first. If the frontend simply renders all backend registry entries as selectable analyses, the new application can expose cards whose engineering engine exists but whose React workflow has not yet been delivered.

That would create dead-end navigation and incorrectly imply feature parity.

### Decision

Availability has at least two distinct dimensions:

1. **Engineering availability** — the Python application/engine has a qualified method contract.
2. **Frontend delivery availability** — the rebuilt frontend has a registered, qualified workflow module for that method.

The backend registry remains authoritative for engineering identity, method version, scope, capability, and whether a calculation is supported by Python.

The frontend module registry remains authoritative for whether the rebuilt application can render and operate that method.

Normal user-facing `New Analysis` selection must expose as actionable only the safe intersection:

```text
engine_supported(method_id)
AND
frontend_module_delivered(method_id)
AND
frontend_module_contract_compatible(method_id)
```

Methods that remain available only in the qualified Streamlit UI during migration must not appear as active dead-end cards in the rebuilt normal user workflow.

Development/reference views may show migration status explicitly, but that is not the normal product navigation.

### R1 acceptance implication

R1 may register all seven current method definitions in the backend while the normal frontend enables none or only explicitly delivered prototype/test modules.

R2A enables Multilane after its workflow is qualified.

R2B enables Two-Lane Facility after its workflow is qualified.

R3 enables each remaining method only after its rebuilt module passes its acceptance gate.

## 5. AR-02 — Presentation/current/stale state is derived, not trusted from project files

### Problem

The conceptual Project schema v2 example included `presentation_state` inside each Scenario.

That field is useful in an in-memory presentation model, but treating a serialized UI state as authoritative risks loading a project that says `current` even when displayed inputs, normalized inputs, method contract, or stored result fingerprint no longer match.

The current application already treats fingerprint identity and stale-result protection as engineering safety behavior.

### Decision

Project persistence may store result identity and evidence, but **current/stale/presentation state must be recomputed on load**.

A persisted scenario should conceptually store:

```text
scenario_id
name
displayed_inputs
normalized_inputs
method_identifier
method_version
input_contract
stored_calculation_fingerprint
stored_result
stored_audit
warnings
assumptions
presentation_metadata?   # non-authoritative UI preferences only
```

On load:

```text
validate schema
-> validate method/input contract compatibility
-> normalize/verify inputs as required
-> recompute expected fingerprint
-> compare with stored result identity
-> retain result only when compatibility rules pass
-> derive current/stale/presentation state
```

`presentation_state` may be cached for diagnostics or migration evidence only if it is explicitly non-authoritative and ignored/recomputed for engineering use.

The same principle applies to legacy 1.2 import.

### Result

Serialized files cannot self-declare a stale result as current.

## 6. AR-03 — Do not promise Recent Projects until reopen semantics exist

### Problem

The Home wireframe contains a `Recent Projects` list.

R0.9 deliberately chooses browser-local, user-initiated file Open/Save and no required database. A normal browser file upload does not provide a durable permission to silently reopen arbitrary project files later.

A list of project names without a reliable reopen action would be misleading.

### Decision

`Recent Projects` is **not an R1/R2 requirement**.

R1/R2 Home requires only:

- New Quick Analysis;
- New Project;
- Open Project;
- Help/Reference as appropriate.

A recent-project experience may be introduced later only after an explicit persistence design is accepted, for example:

- browser-local metadata plus user re-selection;
- a local application-managed recent-file index with safe filesystem semantics;
- a desktop-shell file permission model;
- another reviewed mechanism.

Do not add a database merely to satisfy the early wireframe example.

## 7. AR-04 — Prove the single-endpoint release-like architecture in R1

### Problem

R0.9 selects a release model in which Python serves the compiled SPA and API from one localhost endpoint so normal users do not run Vite/Node.

The original R1 gate only required local/offline launch to be demonstrated in development form. That leaves a material architecture assumption untested until too late.

### Decision

Gate R1 must include a **release-like integration smoke**, even though installer/desktop packaging is still deferred.

Required R1 proof:

```text
frontend production build
-> compiled assets available to Python application
-> FastAPI serves SPA + API from one loopback origin
-> browser opens/loads shell
-> health/method discovery works
-> no Node/Vite runtime required for that smoke
```

Development may still use separate Vite and FastAPI servers.

This is not an EXE/MSI/Tauri requirement. It is proof of the selected runtime architecture.

## 8. AR-05 — Local API must be same-origin/deny-by-default for cross-origin access

### Problem

Binding to loopback is necessary but should not be the only local security assumption.

A browser-based application should not expose a permissive local API configuration to unrelated web origins.

### Decision

R1 security baseline:

- bind to loopback only by default;
- release-like SPA and API use the same origin;
- do not enable wildcard CORS;
- development CORS/proxy rules, if needed, allow only explicit known local development origins;
- calculation/project write endpoints accept typed JSON contracts rather than permissive form/text payloads;
- imported project content is schema-validated and never executed;
- browser-rendered diagnostics/audit text is escaped safely;
- no public network listening without a later explicit design decision.

Authentication remains unnecessary for the loopback-only single-user baseline unless the deployment model changes.

## 9. AR-06 — Project Overview preserves Analysis as the parent object

### Problem

One low-fidelity Project Overview example shows the same Analysis name on multiple Scenario rows.

That is visually plausible but can accidentally train implementation toward a flat `analysis-scenario row` model instead of the accepted object hierarchy.

### Decision

Project Overview is **analysis-first**.

Default conceptual row:

```text
Analysis name
Method
Scenario count
Base/current scenario summary
Highest-priority current/stale/warning indicator
Open action
```

Opening or expanding an Analysis exposes its Scenario list.

A flat scenario table may be used in a dedicated scenario/compare context, but the Project domain model remains:

```text
Project
  -> Analysis
      -> Scenario
```

The Project Overview must not duplicate an Analysis as if each Scenario were a separate Analysis entity.

## 10. AR-07 — Application toolbar is context-aware

### Problem

Global shell examples use `New / Open / Save / Export / Help` for clarity, but some actions are meaningless or misleading outside a Project.

### Decision

Toolbar actions depend on application context.

Conceptual baseline:

### Home

```text
Open Project
Help
```

Primary New Analysis/New Project actions live in Home content.

### Quick Analysis

```text
New
Save to Project
Export/Report   # current-result rules still apply
Help
```

Do not label an unsaved Quick Analysis action simply `Save Project`.

### Project Workspace

```text
New Analysis
Open Project
Save Project
Export/Report
Help
```

Method inputs never belong in the application toolbar.

Actions that are not valid in the current context should be omitted rather than creating persistent disabled clutter unless a specific usability test supports otherwise.

## 11. AR-08 — Project schema v2 requires an explicit schema gate before R2C persistence

### Problem

R0 intentionally leaves exact Project v2 serialization details conceptual.

That is acceptable for architecture planning but not enough authority for Codex to invent persistence semantics during R2C.

### Decision

Before implementation treats Project v2 as a durable release format, R2C must create and review a dedicated schema/compatibility specification containing at minimum:

- schema versioning and upgrade policy;
- stable ID semantics;
- Project/Analysis/Scenario relationships;
- method/input contract identity;
- displayed vs normalized input ownership;
- stored result identity;
- fingerprint verification rules;
- result discard/retain behavior on load;
- warnings/assumptions/audit storage;
- localization/presentation metadata boundary;
- legacy schema 1.2 import mapping;
- unknown/future version rejection behavior;
- deterministic round-trip fixtures.

No `2.0` schema should be declared release-stable merely because the conceptual example exists in R0.10.

Suggested R2C artifact:

```text
docs/application_rebuild/r2_project_schema_v2.md
```

## 12. AR-09 — Sequential wording is historical, not contradictory authority

Early R0 documents were written before later gates existed and therefore contain lines such as `Next R0 gate` and `Draft baseline`.

This is retained as planning history rather than rewritten to make the sequence appear simultaneous.

Authority order for implementation is:

1. this acceptance review;
2. `README.md` current status/index;
3. `r0_prototype_implementation_plan.md`;
4. `r0_technology_architecture.md`;
5. workflow/result/wireframe/design/product documents for their respective details;
6. earlier sequential status prose only as historical context.

A numerical/engineering contract on qualified `main` still outranks a presentation example if the two conflict; implementation must stop and record the conflict rather than changing the engine silently.

## 13. R1 gate after review

R1 is accepted only when all of the following are true:

1. Existing qualified numerical tests remain green or every intentional engineering change is separately reviewed.
2. `hcmcalc.application` is framework-independent and does not require Streamlit/FastAPI.
3. FastAPI is thin and contains no duplicated HCM formulas.
4. Backend method registry exposes stable engineering metadata.
5. Frontend delivery registry prevents undelivered rebuilt methods from becoming active user workflows.
6. React/TypeScript/Vite production build passes.
7. Release-like single-origin loopback smoke serves compiled SPA + API without Node runtime.
8. Same-origin/deny-by-default local API security rules are verified.
9. AppShell, localization, method discovery/reference, and initial browser journeys pass.
10. Contract drift checks exist between OpenAPI/backend and frontend assumptions.
11. No TypeScript HCM calculation formula is introduced.
12. Current/stale result identity remains fingerprint-driven.

## 14. R2A gate after review

Multilane remains the first representative method.

In addition to R0.10:

- `multilane_segment` becomes normal-user selectable in the rebuilt frontend only after its frontend module and API contract pass R2A acceptance;
- other unmigrated methods remain non-actionable in the rebuilt normal workflow;
- legacy project import derives state from verified identity rather than persisted presentation state.

## 15. R2B gate after review

Two-Lane Facility remains the second representative method.

In addition to R0.10:

- `two_lane_facility` becomes normal-user selectable only after its grid/browser acceptance passes;
- Project Overview remains analysis-first;
- no general unrestricted facility builder is implied.

## 16. R2C gate after review

Before Project v2 persistence is considered stable:

1. approve the dedicated Project v2 schema specification;
2. implement deterministic schema fixtures and round-trip tests;
3. import legacy schema 1.2 without modifying the original file;
4. derive current/stale/result presentation state from verified stored identity;
5. prove Quick Analysis -> Save to Project preserves calculation identity;
6. prove Analysis -> Scenario hierarchy survives save/reopen;
7. prove stale/incompatible results are discarded or marked according to explicit compatibility rules;
8. keep Recent Projects out of scope unless a separate persistence design is approved.

## 17. Architecture acceptance statement

With the clarifications above, the R0 package is internally coherent enough to authorize R1 implementation.

The product direction is accepted:

- engineering workspace rather than calculator collection;
- Project -> Analysis -> Scenario -> Result hierarchy;
- task/facility navigation;
- result-first engineering presentation;
- deterministic interpretation without unsupported recommendations;
- React/TypeScript/Vite frontend;
- FastAPI/local Python application boundary;
- existing Python engine as calculation authority;
- incremental representative-method migration;
- browser, contract, project-compatibility, visual, and numerical gates.

No finding from this review justifies returning to the current monolithic Streamlit composition as the target architecture.

## 18. Repository action after this review

After this review document and the updated index are present in PR #129:

1. PR #129 may be marked ready for review/acceptance.
2. If no new blocking finding appears, squash-merge PR #129 to `main`.
3. Issue #130 becomes the implementation authority for R1/R2 together with the merged R0 documents.
4. Start implementation on an isolated R1 branch/worktree.
5. Do not begin R2A until Gate R1 passes.
