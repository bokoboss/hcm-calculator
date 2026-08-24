# Application Rebuild R0 — Product Architecture

Status: Draft baseline for R0 planning
Date: 2026-08-24
Branch: `planning/application-rebuild-r0`
Base: `main` at `8dc1481163d9864df71e2091ce23f0963b702e92`

## 1. Purpose

This document defines the product and application architecture direction for the HCM Calculator rebuild before any production implementation begins.

The rebuild is intentionally **engine-preserving**. The current numerical methods, validation foundation, project contracts, reporting logic, audit records, and deterministic result-state behavior are not being replaced merely to obtain a new interface.

The product problem being addressed is that the current Streamlit application behaves primarily like a collection of polished worksheets/calculators. The target product is an engineering analysis application that makes real professional workflows easier to understand, execute, review, compare, save, reopen, and audit.

R0 is planning and architecture only. No production frontend rewrite is authorized by this document alone.

## 2. Product definition

The target product is an **HCM Analysis Workspace**: a professional engineering application for creating, managing, calculating, reviewing, comparing, documenting, and exporting analyses based on supported Highway Capacity Manual methods.

The application should guide the user through engineering tasks rather than expose the internal structure of the calculation engine.

The target mental model is:

```text
Project
  -> Analysis
      -> Scenario
          -> Engineering Inputs
              -> HCM Calculation
                  -> Result + Interpretation
                      -> Compare / Review / Report / Audit
```

The application must remain suitable for a single quick calculation, but its architecture must also support multi-analysis project work.

## 3. Primary product goals

1. Make the required engineering workflow obvious without requiring the user to understand software internals.
2. Preserve calculation authority in the existing Python HCM engine.
3. Preserve auditability, intermediate values, method identity, assumptions, warnings, and result freshness semantics.
4. Support one-off calculations without forcing project-management overhead.
5. Support real projects containing many analyses and alternatives.
6. Make scenario comparison a first-class future capability.
7. Support additional HCM facility types and chapters later without redesigning the entire application shell.
8. Maintain bilingual Thai/English presentation.
9. Maintain backward compatibility with qualified v0.9 project files during migration.
10. Use automated numerical, contract, compatibility, browser-journey, and visual-regression harnesses before release acceptance.

## 4. Non-goals for R0

R0 does not:

- rewrite validated HCM mathematics;
- duplicate HCM equations in the frontend;
- implement all future HCM chapters;
- introduce a general-purpose plugin SDK;
- introduce a desktop shell such as Electron or Tauri before the web-local application architecture is proven;
- require every calculation to belong to a persistent project;
- merge or adopt the existing Phase 17 planning branch as the new implementation authority;
- authorize production implementation before workflow, result, wireframe, design-system, technology, compatibility, and acceptance specifications are completed.

## 5. Product object model

### 5.1 Project

A Project represents a real engineering study or work package, for example:

- Highway 344 Improvement
- Airport Access Study
- Interchange A Operations Review

A Project may contain multiple analyses, scenarios, and reports.

### 5.2 Analysis

An Analysis is one HCM analytical unit with a defined method and engineering context, for example:

- Multilane WB Segment 01
- Merge A
- Weaving Area 01
- Two-Lane Facility Northbound

An Analysis owns its method identity and scenarios.

### 5.3 Scenario

A Scenario is an alternative within one Analysis, for example:

- Existing
- Future No-Build
- Option A — Add Lane
- Option B — Improve Geometry

Scenario functionality must not create unnecessary UX overhead. A newly created Analysis should receive a default Base Scenario automatically. Users who only need one calculation should be able to ignore the scenario concept.

### 5.4 Calculation Result

A result is associated with:

- method identity and version;
- normalized engine inputs;
- input/calculation fingerprint;
- status/freshness;
- primary and secondary performance measures;
- warnings and scope limitations;
- intermediate values and audit evidence.

A stored result must become stale when material inputs change and must never be silently presented as current.

### 5.5 Report / Export

Reports and exports are presentations of an existing accepted/current result. Report generation must not silently rerun or modify the engineering calculation.

## 6. Quick Analysis and Project Workspace

The target UX should support two practical entry patterns.

### Quick Analysis

For one-off work:

```text
New Analysis -> Choose Method -> Enter Inputs -> Calculate -> Review -> Export
```

A persistent Project is optional.

### Project Workspace

For study work:

```text
Open/Create Project
  -> Add Analysis
      -> Base Scenario
      -> Duplicate Scenario as needed
      -> Calculate / Review
  -> Compare
  -> Reports
```

A Quick Analysis may later be saved into a Project without changing its calculation identity.

## 7. Information architecture

The application navigation is organized by **facility / engineering task**, not by HCM chapter number.

Chapter number and HCM edition are methodology metadata presented within the analysis context.

Proposed top-level structure:

```text
HCM Analysis Workspace

PROJECT
  Overview

ANALYSIS
  Highways
    Two-Lane Highway
    Multilane Highway

  Freeways
    Basic Freeway Segment
    Weaving Segment
    Merge Segment
    Diverge Segment

  Intersections                 [future]
    Signalized Intersection
    Two-Way Stop-Controlled
    All-Way Stop-Controlled
    Roundabout

  Urban Streets                 [future]
  Pedestrian                    [future]
  Bicycle                       [future]
  Transit                       [future]

REVIEW
  Compare
  Reports

REFERENCE
  Supported Methods
  Methodology
  Help
```

This avoids coupling application navigation to chapter numbering that may differ by HCM edition.

## 8. Application shell

The Airport Curbside Analysis Tool v1.1 provides a useful reference pattern because it separates application-level actions from analysis content.

The HCM application should adopt the same broad grammar without copying every visual detail:

```text
Header Toolbar

Left Navigation  |  Main Workspace

Persistent Status Bar
```

### 8.1 Header toolbar

The header contains application/project-level actions only, such as:

- New
- Open
- Save
- Import
- Export / Report
- Help
- language selection
- current project identity

Project load/save/export actions must not be embedded inside the engineering calculation form.

### 8.2 Left navigation

The left navigation exposes the current project, supported analysis families, review functions, and reference content.

The user should be able to understand where they are without selecting a calculator from nested dropdowns.

### 8.3 Main workspace

The main workspace displays the active Project, Analysis, Scenario, input workflow, result, comparison, report, or reference page.

### 8.4 Persistent status

The application should expose persistent state such as:

- ready / invalid / calculation current / stale;
- active method;
- HCM edition and chapter;
- unit system;
- saved/unsaved state where applicable.

## 9. Common analysis design grammar

All analysis methods should use the same high-level grammar while allowing method-specific controls and visualizations.

```text
Analysis Header
  - analysis name
  - scenario
  - HCM edition / chapter / method

Setup / Context
Traffic
Geometry
Method-specific Conditions
Readiness / Validation
Calculate

Results
Engineering Interpretation
Details
Methodology & Assumptions
Audit / Intermediate Values

Scenario / Compare / Export actions
```

Examples of method-specific presentation are allowed:

- Two-Lane Facility may require an editable segment grid;
- Weaving may benefit from a geometry diagram;
- future signalized-intersection methods may use phase/laning diagrams.

The overall application shell and result hierarchy should remain familiar across methods.

## 10. Input UX principles

1. Present engineering decisions, not internal variable names.
2. Separate required, conditional, optional, and advanced inputs.
3. Reveal conditional fields only when the selected method requires them.
4. Keep units explicit and close to values.
5. Provide concise engineering help at the point of use.
6. Validate before calculation and explain how to recover from invalid states.
7. Do not treat audit/debug information as equal in visual priority to required engineering inputs.

Example:

Instead of exposing an internal selector such as `PCE mode`, present an engineering choice such as:

```text
Heavy-vehicle adjustment
  - General terrain
  - Specific grade
  - External PCE
```

The framework-independent adapter/application layer maps this choice to engine-native inputs.

## 11. Result architecture

Results must use a four-level hierarchy.

### Level 1 — Answer

The primary engineering outcome, for example:

- LOS;
- primary operating status;
- capacity failure or method handoff state.

### Level 2 — Engineering performance

Method-relevant measures such as:

- density;
- speed;
- v/c;
- follower density;
- percent time-spent-following;
- facility measures;
- other method-specific outputs.

### Level 3 — Interpretation

Deterministic engineering interpretation derived from the accepted result/state, for example:

- demand below/above calculated capacity;
- governing performance measure;
- active heavy-vehicle treatment;
- scope limitation affecting the result;
- stale-result notice;
- HCM method handoff requirement.

The application must not invent methodology or unsupported design recommendations.

### Level 4 — Evidence

Detailed traceability:

- method and version;
- normalized inputs;
- factors;
- intermediate calculations;
- assumptions;
- warnings;
- source references where available;
- audit record / machine-readable evidence.

Level 1 through Level 4 must not receive equal visual weight.

## 12. Future-method extensibility

The rebuild must support future HCM methods without requiring edits to a monolithic application dispatcher.

A lightweight Analysis Registry should define each method conceptually through metadata and contracts such as:

```text
id
family
name
HCM edition
chapter
method identifier
supported unit systems
input/workflow definition
result definition
engine adapter
project adapter
report adapter
localization/help/scope content
```

This is intentionally not a speculative universal plugin framework.

Adding a method should primarily mean adding/registering an analysis module that conforms to the common application contracts.

## 13. Engine/application boundary

The target directional architecture is:

```text
Product Experience
  -> Application / Workflow Layer
      -> Existing HCM Engine
          -> Engineering Foundation
```

The application/workflow layer owns:

- user workflow;
- state transitions;
- conditional presentation decisions;
- validation presentation;
- result interpretation;
- scenario/project orchestration;
- serialization/report orchestration.

The HCM engine remains the single calculation authority.

Frontend code must not reproduce or independently implement HCM equations.

## 14. Existing assets to preserve

The rebuild should preserve or deliberately migrate the following qualified concepts/assets:

- numerical engines and method modules;
- core/domain models;
- validation fixtures;
- numerical and cross-method tests;
- unit conversion;
- framework-independent `manual_*` adapter concepts;
- result-state taxonomy;
- fingerprint and stale-result detection;
- project schema compatibility;
- reporting behavior that does not rerun calculations;
- audit records;
- supported-scope metadata;
- bilingual localization content.

Several current `ui/` modules contain framework-independent application logic. During implementation these should be evaluated for relocation into an explicit application layer rather than discarded because of their current directory name.

## 15. Existing assets to replace

The rebuild is expected to replace the Streamlit-specific product composition, including:

- monolithic `streamlit_app.py` orchestration;
- current Streamlit navigation model;
- current two-column worksheet-centric shell;
- Streamlit-specific layout/rendering components where they prevent the target application workflow.

Replacement of presentation code must not imply replacement of validated engineering calculations.

## 16. Backward compatibility

The new application must support qualified v0.9 project files during transition.

A legacy single-analysis project should be importable as a new Analysis with its method identity, stored inputs, result, warnings, assumptions, audit evidence, and calculation identity preserved where verifiable.

Conceptual migration:

```text
Open legacy v0.9 project
  -> detect project type / method
  -> create Analysis
  -> create Base Scenario
  -> import display and normalized inputs
  -> verify fingerprint/result identity
  -> retain current result only when compatibility checks pass
```

Existing compatibility and stale-result safeguards must not be weakened.

## 17. Representative prototype methods

The production rebuild should not begin by porting every supported method.

Recommended representative workflows:

1. **Multilane Highway Segment**
   - conditional input branches;
   - free-flow-speed handling;
   - heavy vehicles;
   - unit conversion;
   - capacity failure;
   - project/export behavior.

2. **Two-Lane Facility**
   - multi-segment/tabular inputs;
   - row-level validation;
   - segment/facility aggregation;
   - complex result presentation.

If the architecture handles these two extremes well, the remaining methods should fit the same product grammar more credibly.

Weaving may be used as a later diagram-heavy prototype if required.

## 18. Required acceptance harnesses

The rebuild must eventually be qualified through distinct layers:

1. **Numerical harness** — existing pytest and validated HCM fixtures.
2. **Application contract harness** — user/application request to normalized engine input to expected result/state.
3. **Project compatibility harness** — legacy v0.9 project to new application with preserved calculation identity/result where valid.
4. **User journey harness** — browser automation for create/open/calculate/review/edit/stale/recalculate/export workflows.
5. **Visual regression harness** — reference screenshots/diffs for critical screens and responsive layouts.

A green numerical suite alone is not sufficient application acceptance.

## 19. R0 remaining work

The following must be completed before production implementation is authorized:

- R0.5 Workflow Architecture for all currently supported methods;
- R0.6 Result Architecture specification and interpretation rules;
- R0.7 screen inventory and wireframes;
- R0.8 design system and interaction rules;
- R0.9 technology decision and application boundary ADR;
- R0.10 prototype specification and implementation backlog;
- acceptance criteria for the representative prototypes.

## 20. Current design direction summary

The following directions are accepted as the baseline for continued R0 planning:

1. The product is an engineering analysis workspace, not a collection of calculators.
2. `Project -> Analysis -> Scenario -> Result` is the primary object model.
3. Scenario complexity remains optional in normal use; a Base Scenario is automatic.
4. Navigation is facility/task-based, not chapter-number-based.
5. HCM edition/chapter is methodology metadata.
6. Project/Open/Save/Export actions belong to the application shell, not calculation forms.
7. The application uses a Curbside-inspired header + left navigation + main workspace + persistent-status grammar.
8. Methods share a common analysis grammar but may use method-specific inputs, grids, and diagrams.
9. Future methods register through lightweight application contracts rather than a monolithic dispatcher.
10. Existing validated engines remain calculation authority.
11. Legacy project compatibility is a migration requirement.
12. R0 remains architecture/specification only until the remaining gates are completed.
