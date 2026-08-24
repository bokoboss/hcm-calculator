# Application Rebuild R0.7 — Screen Inventory and Low-Fidelity Wireframes

Status: Draft baseline for R0 planning
Date: 2026-08-24
Branch: `planning/application-rebuild-r0`

## 1. Purpose

This document converts the approved product, workflow, and result architecture into a concrete screen model before visual design or implementation begins.

The wireframes are intentionally low fidelity. They define hierarchy, placement, interaction, and information density—not final colors, fonts, spacing tokens, or frontend components.

The shell is inspired by the proven Airport Curbside Analysis Tool pattern:

```text
Header Toolbar
Left Navigation | Main Workspace
Persistent Status
```

The HCM application extends that pattern with Project, Analysis, Scenario, Compare, and multi-method workflows.

## 2. Desktop-first target

This is a professional engineering application. The primary design target is desktop/laptop use.

Recommended design assumptions for R0.7:

- primary workspace target: approximately 1280 px and wider;
- optimized review/layout target: approximately 1440–1600 px;
- narrow laptop widths must remain usable without horizontal page scrolling;
- tables/grids may use local horizontal scrolling where technically necessary;
- tablet layouts should stack secondary panels;
- phone layout should preserve project/result reading and basic editing but is not the primary data-entry experience.

Exact breakpoints belong to R0.8.

## 3. Global application shell

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ HCM ANALYSIS                                                   EN | ไทย     │
│ Highway 344 Improvement                  New  Open  Save  Export  Help      │
├───────────────────┬──────────────────────────────────────────────────────────┤
│                   │                                                          │
│ PROJECT           │                  MAIN WORKSPACE                          │
│ Overview          │                                                          │
│                   │                                                          │
│ ANALYSES          │                                                          │
│ Highways          │                                                          │
│  Two-Lane         │                                                          │
│  Multilane        │                                                          │
│                   │                                                          │
│ Freeways          │                                                          │
│  Basic Segment    │                                                          │
│  Weaving          │                                                          │
│  Merge            │                                                          │
│  Diverge          │                                                          │
│                   │                                                          │
│ REVIEW            │                                                          │
│ Compare           │                                                          │
│ Reports           │                                                          │
│                   │                                                          │
│ REFERENCE         │                                                          │
│ Methods           │                                                          │
│ Methodology       │                                                          │
│ Help              │                                                          │
├───────────────────┴──────────────────────────────────────────────────────────┤
│ Ready │ Multilane Segment │ HCM 7.0 │ Metric │ Saved                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Shell rules

Header:

- application-level actions only;
- project name/context;
- language;
- never contain method input fields.

Left navigation:

- current project/application structure;
- facility/task navigation;
- current item visibly selected;
- no calculator dropdown required.

Main workspace:

- one task at a time;
- full width available to complex tables/results;
- result pages may use wider content than input pages.

Status bar:

- concise persistent state;
- no long warnings;
- e.g. Ready / Current / Stale, method, unit system, save state.

## 4. Screen inventory

| ID | Screen | Purpose |
|---|---|---|
| S01 | Home | Start Quick Analysis or open/create Project |
| S02 | Project Overview | See analyses, scenarios, status, key outcomes |
| S03 | New Analysis | Choose facility/method by engineering task |
| S04 | Analysis Workspace — Input | Enter method-specific engineering inputs |
| S05 | Analysis Workspace — Result | Review answer, metrics, interpretation, evidence |
| S06 | Two-Lane Facility — Grid | Multi-segment editing and validation |
| S07 | Two-Lane Facility — Result | Facility summary + segment evidence |
| S08 | Weaving — Geometry Workflow | Geometry + movement-flow-oriented setup |
| S09 | Merge/Diverge — Geometry Workflow | Diagram + paired freeway/ramp inputs |
| S10 | Stale Result State | Recover after input changes |
| S11 | Compare Scenarios | Compare current compatible scenario results |
| S12 | Report / Export | Select presentation output from current results |
| S13 | Methodology / Scope | Method support, limitations, references |
| S14 | Evidence / Audit | Detailed inputs, intermediates, audit record |

## 5. S01 — Home

Goal: make the first decision obvious without forcing project setup.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ HCM ANALYSIS                                                   EN | ไทย     │
│                                               Open Project       Help       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Highway Capacity Analysis                                                   │
│  Analyze supported HCM facilities with auditable calculations.              │
│                                                                              │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐   │
│  │ QUICK ANALYSIS                  │  │ PROJECT WORKSPACE               │   │
│  │                                 │  │                                 │   │
│  │ Start one analysis without      │  │ Organize multiple analyses and │   │
│  │ creating a project.             │  │ scenarios in a study.          │   │
│  │                                 │  │                                 │   │
│  │ [ New Analysis ]                │  │ [ New Project ]                │   │
│  └─────────────────────────────────┘  └─────────────────────────────────┘   │
│                                                                              │
│  RECENT PROJECTS                                                             │
│  Highway 344 Improvement          12 analyses        Modified ...            │
│  Airport Access Study              4 analyses        Modified ...            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

Rules:

- Quick Analysis and Project Workspace have equal legitimacy.
- Opening the tool should not immediately show a dense engineering form.
- Recent projects are secondary to the two primary starting actions.

## 6. S02 — Project Overview

Goal: make a multi-analysis engineering project legible at a glance.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Highway 344 Improvement                                      Save  Export   │
├───────────────────┬──────────────────────────────────────────────────────────┤
│ PROJECT           │  PROJECT OVERVIEW                                        │
│ Overview ●        │                                                          │
│                   │  12 analyses     9 current     2 stale     1 warning     │
│ ANALYSES          │                                                          │
│ Highways          │  [ + New Analysis ]                                      │
│ Freeways          │                                                          │
│                   │  ANALYSES                                                │
│ REVIEW            │  ┌────────────────────────────────────────────────────┐ │
│ Compare           │  │ Name              Method       Scenario     Result │ │
│ Reports           │  ├────────────────────────────────────────────────────┤ │
│                   │  │ WB Segment 01     Multilane    Existing       C    │ │
│ REFERENCE         │  │ WB Segment 01     Multilane    Option A       B    │ │
│                   │  │ Merge A           Merge        Existing       E    │ │
│                   │  │ Weaving 01        Weaving      Existing     stale  │ │
│                   │  └────────────────────────────────────────────────────┘ │
│                   │                                                          │
│                   │  FILTER: [All methods] [All states] [Search...]          │
├───────────────────┴──────────────────────────────────────────────────────────┤
│ Project saved │ 12 analyses                                                  │
└──────────────────────────────────────────────────────────────────────────────┘
```

Rules:

- Project Overview is a work list, not a dashboard full of decorative charts.
- Status and primary result are visible.
- Clicking a row opens the Analysis.
- Analysis name and Scenario must remain distinct concepts.
- Filters become useful only when projects grow; they should not dominate small projects.

## 7. S03 — New Analysis

Goal: choose the correct method through facility/task recognition.

```text
NEW ANALYSIS

What do you want to analyze?

HIGHWAYS
┌─────────────────────────────┐  ┌─────────────────────────────┐
│ Two-Lane Highway Segment    │  │ Two-Lane Facility          │
│ One supported segment       │  │ Ordered multi-segment      │
│ HCM 7 · Chapter 15          │  │ facility workflow          │
│ [ Select ]                  │  │ [ Select ]                  │
└─────────────────────────────┘  └─────────────────────────────┘

┌─────────────────────────────┐
│ Multilane Highway Segment   │
│ One-direction segment       │
│ [ Select ]                  │
└─────────────────────────────┘

FREEWAYS
┌─────────────────────────────┐  ┌─────────────────────────────┐
│ Basic Freeway Segment       │  │ Weaving Segment            │
│ Uninterrupted-flow segment  │  │ Isolated weaving area      │
└─────────────────────────────┘  └─────────────────────────────┘

┌─────────────────────────────┐  ┌─────────────────────────────┐
│ Merge Segment               │  │ Diverge Segment            │
│ Isolated right-side on-ramp │  │ Isolated right-side off-   │
│ operational analysis        │  │ ramp operational analysis  │
└─────────────────────────────┘  └─────────────────────────────┘
```

After selection:

```text
Analysis name      [ WB Segment 01                 ]
Scenario           Base Scenario (created automatically)
Units              Metric / Imperial
Starting values    Blank / Optional HCM reference example

[ Create Analysis ]
```

Rules:

- do not display future unsupported chapters as clickable placeholders;
- HCM chapter/version is secondary metadata;
- each card includes a one-line scope description;
- limitations available via `Scope` link/detail, not a paragraph wall.

## 8. S04 — Multilane Input Workspace

This is the representative form-based workflow.

```text
Multilane Highway Segment
WB Segment 01                         Base Scenario
HCM 7 · Multilane Segment             Metric      Ready
───────────────────────────────────────────────────────────────────────────────

TRAFFIC
┌─────────────────────────────────────────────────────────────────────────────┐
│ Demand volume              PHF                 Heavy vehicles               │
│ [ 1,690 veh/h ]            [ 0.92 ]            [ 8.0 % ]                   │
└─────────────────────────────────────────────────────────────────────────────┘

SEGMENT
┌─────────────────────────────────────────────────────────────────────────────┐
│ Number of lanes             Segment length                                 │
│ [ 2 ]                       [ 1.20 km ]                                    │
└─────────────────────────────────────────────────────────────────────────────┘

FREE-FLOW SPEED
┌─────────────────────────────────────────────────────────────────────────────┐
│ ● Estimate from roadway characteristics                                    │
│ ○ Use measured FFS                                                         │
│                                                                             │
│ Posted speed     Lane width     Roadside clearance     Median               │
│ [ ... ]          [ ... ]        [ ... ]                [ Divided ▼ ]        │
│                                                                             │
│ Left clearance   Access-point density                                      │
│ [ ... ]          [ ... ]                                                    │
└─────────────────────────────────────────────────────────────────────────────┘

HEAVY-VEHICLE ADJUSTMENT
┌─────────────────────────────────────────────────────────────────────────────┐
│ ● General terrain    ○ Specific grade    ○ External PCE                    │
│                                                                             │
│ Terrain [ Rolling ▼ ]                                                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ ✓ Ready to calculate                                       [ Calculate ]    │
└─────────────────────────────────────────────────────────────────────────────┘
```

Key behavior:

- vertical single-column section flow rather than permanently splitting input/result into equal columns;
- within a section, related fields may use 2–4 columns;
- conditional branches replace inactive fields rather than leaving disabled clutter everywhere;
- Calculate is visually attached to Readiness.

## 9. S05 — Multilane Result Workspace

After Calculate, the page changes hierarchy.

```text
Multilane Highway Segment
WB Segment 01                         Base Scenario
HCM 7 · Multilane Segment             Metric      Current
───────────────────────────────────────────────────────────────────────────────

RESULT
┌───────────────────────────────┐
│             LOS C             │
│ Density 18.4 pc/km/ln         │
│ Current result                │
└───────────────────────────────┘

KEY PERFORMANCE
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐
│ Density         │ │ Speed           │ │ Demand flow     │ │ Capacity      │
│ 18.4 pc/km/ln   │ │ 91.2 km/h       │ │ 1,540 pc/h/ln   │ │ 2,100 pc/h/ln │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └───────────────┘

ENGINEERING ASSESSMENT
┌─────────────────────────────────────────────────────────────────────────────┐
│ ✓ Demand is below applicable segment capacity.                             │
│ • FFS was estimated from roadway characteristics.                          │
│ • Heavy vehicles: General terrain / Rolling.                               │
│ • No active scope warning affects this result.                             │
└─────────────────────────────────────────────────────────────────────────────┘

[ Edit Inputs ]     [ Duplicate Scenario ]     [ Compare ]     [ Export ]

DETAILS
Calculation Details     Methodology & Assumptions     Inputs     Audit
```

Rules:

- inputs are no longer equal visual peers with results;
- `Edit Inputs` returns to input sections but keeps result context;
- Details can use tabs or accordions later; raw JSON is never the default.

## 10. Capacity-failure variant

```text
RESULT
┌──────────────────────────────────────────────────────────────┐
│ LOS F — CAPACITY EXCEEDED                                   │
│ Demand exceeds applicable segment capacity                  │
│ Speed and density are not predicted in this state           │
└──────────────────────────────────────────────────────────────┘

KEY PERFORMANCE
Demand flow        Capacity        v/c/status
2,260 pc/h/ln      2,100 pc/h/ln   Above capacity

ENGINEERING ASSESSMENT
• The qualified method does not predict congested speed/density here.
• Queue, delay, and travel time are not calculated by this workflow.
```

Unavailable metrics are omitted or explicitly labeled `Not predicted`, never shown as zero.

## 11. S06 — Two-Lane Facility Grid

Goal: make a multi-segment facility feel like an engineering table, not seven stacked forms.

```text
Two-Lane Facility
Facility Northbound                         Base Scenario
Qualified context: Example 3-backed level facility
───────────────────────────────────────────────────────────────────────────────

FACILITY BASIS
┌─────────────────────────────────────────────────────────────────────────────┐
│ Example 3-backed level facility                                             │
│ Editable: names, lengths, speeds, directional volumes, PHF, heavy vehicles │
│ Locked: segment types, terrain/alignment, passing-lane context              │
│ [ Change basis ]                                                            │
└─────────────────────────────────────────────────────────────────────────────┘

SEGMENTS
┌────┬───────────┬──────────┬────────┬──────────┬──────┬─────┬───────────────┐
│ ID │ Name      │ Type     │ Length │ Volume   │ PHF  │ HV% │ ...           │
├────┼───────────┼──────────┼────────┼──────────┼──────┼─────┼───────────────┤
│ 1  │ Segment 1 │ Constr.  │ 0.80   │ 650      │ .92  │ 8   │ ...           │
│ 2  │ Segment 2 │ Pass Ln  │ 1.20   │ 650      │ .92  │ 8   │ ...           │
│ 3  │ Segment 3 │ ...      │ 0.70   │ 650      │ .92  │ 8   │ ...           │
└────┴───────────┴──────────┴────────┴──────────┴──────┴─────┴───────────────┘

Locked cells use read-only styling, not disabled low-contrast text.
Conditional cells appear only when applicable.

VALIDATION
✓ 3 segments valid
✓ Passing-lane sequence valid

[ Calculate Facility ]
```

If validation fails:

```text
VALIDATION — 2 items require attention
[ Segment 2 / PHF ] must be > 0 and <= 1
[ Segment 3 / Opposing volume ] required for passing zone
```

Each message should navigate/focus the relevant cell where technically practical.

## 12. S07 — Two-Lane Facility Result

```text
RESULT
┌────────────────────────────────────┐
│               LOS C                │
│ Follower density: 11.8 foll/mi/ln  │
│ Facility result                    │
└────────────────────────────────────┘

FACILITY PERFORMANCE
Average speed       Percent followers       Critical segment
49.2 mph            61.0 %                  Segment 3

ENGINEERING ASSESSMENT
• Facility metrics are length weighted under HCM Eq. 15-39.
• Facility LOS is determined from final facility follower density.
• Segment LOS letters are not averaged.

SEGMENT RESULTS
┌────┬───────────┬────────────┬───────────┬───────────────┬─────┬───────────┐
│ ID │ Name      │ Avg Speed  │ Followers │ Follower dens │ LOS │ Warning   │
├────┼───────────┼────────────┼───────────┼───────────────┼─────┼───────────┤
│ 1  │ Segment 1 │ ...        │ ...       │ ...           │ B   │           │
│ 2  │ Segment 2 │ ...        │ ...       │ ...           │ C   │           │
│ 3  │ Segment 3 │ ...        │ ...       │ ...           │ D   │ critical  │
└────┴───────────┴────────────┴───────────┴───────────────┴─────┴───────────┘

[ Select segment ] -> opens segment evidence panel
```

Facility result and segment evidence must remain visually separate.

## 13. S08 — Weaving Geometry Workflow

Goal: avoid presenting the weaving contract as a flat list of technical variables.

```text
Weaving Segment
Weaving Area 01                         Base Scenario
───────────────────────────────────────────────────────────────────────────────

CONFIGURATION
┌─────────────────────────────────────────────────────────────────────────────┐
│ ○ One-sided weaving                  ● Two-sided weaving                    │
│                                                                             │
│         [ simplified geometry diagram updates here ]                        │
│                                                                             │
│ Segment length [ ... ]   Total lanes [ 4 ]   Weaving lanes [ ... ]         │
│ Entry side [ ... ]       Exit side [ ... ]                                 │
└─────────────────────────────────────────────────────────────────────────────┘

MOVEMENT FLOWS
┌─────────────────────────────────────────────────────────────────────────────┐
│ Diagram / matrix                                                            │
│                                                                             │
│ FF [ ... veh/h ]     FR [ ... veh/h ]                                      │
│ RF [ ... veh/h ]     RR [ ... veh/h ]                                      │
└─────────────────────────────────────────────────────────────────────────────┘

LANE RELATIONSHIPS
┌─────────────────────────────────────────────────────────────────────────────┐
│ Reachable lanes / option lanes shown as grouped O-D relationships          │
│ [ Engineering details ] reveals NWL basis / lane-change basis              │
└─────────────────────────────────────────────────────────────────────────────┘

TRAFFIC CONDITIONS
PHF     Heavy vehicles     Interchange density     Terrain

FREE-FLOW SPEED
Measured / Estimated selector

[ Readiness ]                                               [ Calculate ]
```

Technical fields that users must supply remain available, but diagram/context comes first.

## 14. Weaving handoff result

```text
RESULT
┌─────────────────────────────────────────────────────────────────────────────┐
│ HCM METHOD HANDOFF                                                         │
│ No weaving LOS is assigned for this condition.                             │
│ The calculated weaving length condition reaches the method stopping rule.  │
└─────────────────────────────────────────────────────────────────────────────┘

ENGINEERING ASSESSMENT
• Active weaving method stops at this condition.
• Preserve the calculated geometry/flow evidence below.

[ Review applicable analysis path ]

DETAILS
Stopping condition     Inputs     Intermediate values     Methodology
```

Do not show a warning card above an otherwise normal LOS result because there is no normal weaving LOS in this state.

## 15. S09 — Merge / Diverge Geometry Workflow

Use the same screen grammar for both.

```text
Merge Segment
Interchange A On-Ramp                         Base Scenario
───────────────────────────────────────────────────────────────────────────────

QUALIFIED GEOMETRY
┌─────────────────────────────────────────────────────────────────────────────┐
│ [ right-side on-ramp diagram ]                                             │
│                                                                             │
│ Freeway lanes [ 3 ]             Acceleration lane length [ ... ]           │
│                                                                             │
│ Scope: isolated · one ramp lane · right-side · 2-4 freeway lanes           │
└─────────────────────────────────────────────────────────────────────────────┘

TRAFFIC
┌───────────────────────────────┬─────────────────────────────────────────────┐
│ FREEWAY                       │ RAMP                                        │
│ Demand [ ... ]                │ Demand [ ... ]                              │
│ PHF [ ... ]                   │ PHF [ ... ]                                 │
│ Heavy vehicles [ ... ]        │ Heavy vehicles [ ... ]                      │
└───────────────────────────────┴─────────────────────────────────────────────┘

SPEED / CONDITIONS
Freeway FFS: Measured / Estimated
Ramp FFS [ ... ]
Terrain [ Level / Rolling ]

ENGINEERING EVIDENCE                         [ optional details ]
Geometry source / notes

[ Ready ]                                                   [ Calculate ]
```

Diverge changes diagram, `acceleration` to `deceleration`, and traffic labels to upstream freeway / off-ramp.

## 16. S10 — Stale result recovery

The stale state should not erase the previous result abruptly.

```text
INPUT CHANGED — RECALCULATION REQUIRED

The current inputs no longer match the result below.

[ Recalculate ]     [ Review changed inputs ]

PREVIOUS RESULT — STALE
┌────────────────────────────┐
│ LOS C                      │
│ Previous calculation       │
│ Not available for current  │
│ export/report              │
└────────────────────────────┘
```

Rules:

- stale banner sits above previous result;
- previous answer remains readable for orientation;
- export button is disabled/redirected to recalculation requirement;
- if inputs return exactly to the accepted fingerprint, current status may be restored according to the existing deterministic fingerprint contract.

## 17. S11 — Compare Scenarios

```text
COMPARE — WB Segment 01
Multilane Highway Segment

Scenarios: [ Existing ✓ ] [ Option A ✓ ] [ Option B ✓ ]

┌────────────────────────────┬────────────┬────────────┬────────────┐
│ Metric                     │ Existing   │ Option A   │ Option B   │
├────────────────────────────┼────────────┼────────────┼────────────┤
│ LOS                        │ D          │ C          │ C          │
│ Density                    │ 28.1       │ 19.7       │ 21.0       │
│ Speed                      │ 78.2       │ 91.4       │ 88.1       │
│ Demand flow                │ ...        │ ...        │ ...        │
│ Capacity                   │ ...        │ ...        │ ...        │
└────────────────────────────┴────────────┴────────────┴────────────┘

CHANGES FROM EXISTING
Option A: LOS D -> C; density -8.4 ...
Option B: LOS D -> C; density -7.1 ...

[ Open Existing ]  [ Open Option A ]  [ Export Comparison ]
```

Rules:

- only current, compatible scenarios are compared by default;
- stale scenario appears as `Recalculate required`, not an old numeric value pretending to be current;
- LOS delta shown as grade transition, not percentage;
- comparison does not produce an automatic design recommendation.

## 18. S12 — Export / Report

Export should feel like an application action, not a hidden expander below calculation details.

```text
EXPORT / REPORT

Source
  Project: Highway 344 Improvement
  Analysis: WB Segment 01
  Scenario: Existing
  Result: Current

OUTPUT
  ○ Engineering Summary
  ○ Detailed Calculation Report
  ○ Comparison Report
  ○ CSV data
  ○ Excel data
  ○ Markdown
  ○ Report JSON
  ○ Project JSON

[ Export ]
```

The exact output types depend on the existing reporting/project contracts.

Export must not rerun the calculation.

## 19. S13 — Methodology / Scope

```text
MULTILANE HIGHWAY SEGMENT
HCM 7 · [chapter metadata]

SUPPORTED
• bounded one-direction segment analysis
• measured or supported estimated FFS
• supported heavy-vehicle treatments
...

NOT SUPPORTED
• freeway ramp influence
• weaving
• facility/corridor workflow
...

METHOD REFERENCES
...

[ Start this analysis ]
```

This page is reference-oriented; it should not duplicate the full manual inside every analysis form.

## 20. S14 — Evidence / Audit

Evidence is structured for human review first.

```text
CALCULATION EVIDENCE

[ Method & Scope ] [ Inputs ] [ Calculation Details ] [ Assumptions ] [ Audit ]

METHOD & SCOPE
Method identifier     multilane_segment
Method version        ...
Calculation contract  ...
Fingerprint           ...

INPUTS
Displayed inputs      [ readable table ]
Normalized inputs     [ readable table ]

CALCULATION DETAILS
Step / variable / value / unit / equation / source

AUDIT
[ View structured JSON ]
[ Copy / Export audit ]
```

Raw JSON is one evidence view, not the primary human interface.

## 21. Input-section interaction rules

Input pages should prefer visible sections over excessive expanders.

Default visible:

- required traffic;
- required geometry;
- primary method decisions;
- readiness.

Progressive/secondary:

- external provenance;
- geometry notes;
- technical basis fields;
- advanced adjustment factors;
- audit-only metadata.

An expander is appropriate only when content is secondary to the main task.

## 22. Form density

Target density is professional and compact, not consumer-app spaciousness.

Rules:

- related numeric fields can share a row;
- labels remain fully readable;
- unit appears in or immediately beside the field;
- help text is on demand rather than permanent paragraphs;
- section spacing is stronger than field spacing;
- no large decorative cards for each individual input.

## 23. Persistent actions

Long input pages may use a sticky lower action region on desktop:

```text
────────────────────────────────────────────────────────────
✓ Ready to calculate                  [ Calculate ]
```

After an edit to a previously calculated scenario:

```text
────────────────────────────────────────────────────────────
Input changed — previous result stale  [ Recalculate ]
```

This should be evaluated in browser prototypes during implementation.

## 24. Navigation behavior inside an Analysis

Do not create a permanent seven-step wizard if users need frequent back-and-forth engineering review.

Preferred baseline:

- one analysis page with clear anchored sections;
- compact local section navigation when the workflow becomes long;
- result becomes dominant after calculation;
- `Edit Inputs` returns to the relevant section structure.

A full Next/Back wizard remains rejected unless user testing later shows a clear benefit for a specific complex method.

## 25. Responsive behavior

### Wide desktop

- left navigation persistent;
- main workspace centered/wide;
- 2–4 field columns inside sections;
- facility grids use full available width.

### Narrow laptop/tablet

- left navigation collapsible;
- field rows reduce column count;
- result metric grid wraps;
- diagram and inputs stack where needed.

### Phone

- left nav becomes drawer;
- forms become one-column;
- result/evidence remains readable;
- large facility-grid editing may use focused row/card editor rather than forcing the whole desktop grid into the viewport.

Phone editing is secondary, but the application must not become unusable or inaccessible.

## 26. Screen-level acceptance questions

Before R0.7 is accepted, the wireframes should satisfy these questions:

- Can a new user tell the difference between Quick Analysis and Project Workspace?
- Can a user select an analysis without knowing the HCM chapter number?
- Is Project Save/Open/Export visually separate from engineering inputs?
- Does a Multilane calculation read top-to-bottom as Traffic -> Segment -> FFS -> Heavy Vehicles -> Calculate?
- Does the result visibly outrank the input form after calculation?
- Is capacity failure unmistakably different from a normal LOS result?
- Is stale result unmistakably not current?
- Does Two-Lane Facility feel like a segment facility rather than repeated forms?
- Does Weaving provide spatial/flow context before technical geometry fields?
- Do Merge/Diverge visibly communicate their fixed qualified geometry?
- Can audit evidence be reached without cluttering the default result?
- Can scenarios be compared without pretending LOS is a continuous numeric metric?

## 27. R0.7 recommendation

Adopt these low-fidelity wireframes as the baseline for R0.8 visual/design-system work, with Multilane and Two-Lane Facility as the first high-fidelity prototype screens.

The key UI direction is deliberately conventional:

- stable application shell;
- clear left navigation;
- visible engineering sections;
- results-first hierarchy;
- explicit state/recalculation;
- restrained use of cards;
- evidence available on demand.

The goal is not visual novelty. The goal is a professional engineering tool that is immediately legible and remains extensible as more HCM methods are added.
