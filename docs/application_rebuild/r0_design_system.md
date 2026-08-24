# Application Rebuild R0.8 — Design System and Interaction Rules

Status: Draft baseline for R0 planning
Date: 2026-08-24
Branch: `planning/application-rebuild-r0`

## 1. Purpose

This document defines the visual and interaction grammar for the rebuilt HCM application so implementation does not drift into different UI styles across methods.

The design intentionally favors a conventional professional engineering application over novelty.

The Airport Curbside Analysis Tool is a useful reference because its usability comes from consistent shell geometry, compact form density, strong field/unit treatment, clear table behavior, visible focus/error states, and answer-first result presentation. HCM should inherit those principles while establishing its own reusable design system.

## 2. Design character

Target qualities:

- professional;
- engineering-focused;
- compact but not cramped;
- restrained;
- highly legible;
- auditable;
- predictable;
- desktop-efficient;
- bilingual-ready;
- accessible.

Avoid:

- consumer-dashboard styling;
- excessive gradients/shadows;
- oversized cards for every value;
- decorative illustrations unrelated to engineering understanding;
- glassmorphism;
- excessive rounded containers;
- animation-heavy transitions;
- hidden controls that require discovery;
- dense walls of help text.

## 3. Default appearance

R1 should target a high-quality light application theme first.

Reasoning:

- engineering forms/tables are typically reviewed for long periods;
- printed/exported views map naturally from a light UI;
- current Curbside/HCM user expectations are already light-oriented;
- a second theme would multiply QA surface before the new application architecture is proven.

Dark mode may be added later but is not an R1 acceptance requirement.

## 4. Typography

Use a native/system UI font stack unless the selected frontend framework provides an equally legible local default.

Preferred Windows-first stack concept:

```text
Segoe UI, system-ui, -apple-system, BlinkMacSystemFont, sans-serif
```

Do not require downloadable web fonts for normal local operation.

### Type scale

Recommended baseline:

| Role | Approx. size | Weight |
|---|---:|---:|
| App title | 18–20 px | 700–800 |
| Page title | 19–22 px | 700–800 |
| Section title | 13–15 px | 700–800 |
| Body / input | 14 px | 400–500 |
| Field label | 12–13 px | 600–700 |
| Secondary/help | 11–12 px | 400–500 |
| Result hero | 26–36 px | 800–900 |
| Metric value | 20–26 px | 700–900 |

Thai typography must be reviewed at actual rendered line height; do not reduce Thai help text merely to make it fit an English-sized container.

## 5. Numeric typography

Engineering numbers should use tabular numerals where the font supports them.

Apply to:

- result values;
- tabular inputs;
- result comparisons;
- segment grids;
- calculation evidence.

Decimal alignment in dense result tables is preferred where feasible.

## 6. Spacing system

Use a simple 4 px-derived spacing scale.

Recommended tokens:

```text
4   micro
8   compact
12  field/group
16  section internal
24  section separation
32  major page separation
```

The application should feel slightly denser than a general SaaS product.

Section separation should be stronger than spacing between fields within one engineering concept.

## 7. Shell geometry

Desktop baseline:

```text
Header:       64–72 px
Sidebar:      ~240 px
Status bar:   28–34 px
Main padding: 16–24 px
```

Sidebar width should remain stable across methods.

Main content must use `min-width: 0` or equivalent layout behavior so wide tables do not force the entire application beyond the viewport.

## 8. Main content width

Do not impose one fixed maximum width on every screen.

Use content modes:

### Form mode

Readable working width, approximately 900–1200 px depending on viewport.

### Result mode

May expand wider to support metric rows and interpretation.

### Grid mode

Use the full available workspace for Two-Lane Facility and future table-heavy analyses.

### Compare mode

Use full available width with horizontally scrollable comparison only when necessary.

## 9. Color architecture

Use semantic tokens rather than hard-coded page-specific colors.

Recommended baseline palette direction:

```text
app-bg           #eef3f8 / similar cool neutral
panel-bg         #ffffff
soft-bg          #f7f9fc
border           #d8e1ea
text-primary     #142033
text-secondary   #64748b
brand-navy       #082a52 / similar
brand-blue       #1769aa / similar
focus            strong accessible blue
```

Exact final contrast values must be accessibility-checked in the implemented design.

The HCM application may use the same general navy/blue engineering character as the Curbside Tool without copying every token.

## 10. Semantic colors

Semantic state must always include text/iconography in addition to color.

Recommended categories:

- information / current: blue;
- valid/success: green;
- warning: amber/orange;
- capacity failure/error: red;
- stale: amber/orange with explicit `Stale` label;
- unavailable/inactive: neutral gray.

### LOS colors

Preserve a familiar ordered LOS color grammar:

- A: strong green;
- B: green;
- C: amber;
- D: orange;
- E: red;
- F: dark red.

LOS must always display the letter and label; color is supplemental.

## 11. Borders, radius, shadows

Baseline:

- 1 px neutral borders;
- 6–8 px radius for panels/controls;
- 4–6 px radius for inputs;
- minimal low-opacity shadow only where it improves separation;
- avoid floating-card visual noise.

A section should usually be separated by border/background and spacing, not a heavy shadow.

## 12. Application header

Header contains:

- product identity;
- current project identity where applicable;
- New/Open/Save/Export/Help;
- language selector.

Toolbar buttons are compact, mostly secondary-outline style.

Only the most important contextual action may use a stronger treatment.

Do not make Save/Open visually compete with Calculate inside the analysis page.

## 13. Sidebar

Sidebar should be visually distinct from the main canvas.

Recommended behavior:

- dark/navy surface on desktop;
- grouped labels: Project / Analyses / Review / Reference;
- selected item uses background + left marker + weight;
- hover/focus states clear;
- group headings small and uppercase or otherwise visually secondary;
- no excessive icons required.

Icons may support recognition but text labels remain mandatory.

## 14. Page header

Each workspace page starts with:

- page/analysis title;
- method metadata;
- scenario/current status;
- optional page-level actions.

Example:

```text
Multilane Highway Segment
WB Segment 01 · Existing
HCM 7 · [chapter] · Metric                     Current
```

Do not repeat the full navigation breadcrumb if the sidebar already establishes location.

## 15. Panels / Engineering Sections

Use panels for meaningful engineering groups, not every field.

Typical panel:

```text
FREE-FLOW SPEED
short optional note
-----------------------------------------------
fields / method choice / conditional inputs
```

Panel header:

- concise title;
- optional status/help action;
- no marketing copy.

Panel body:

- 12–16 px padding baseline;
- compact grid spacing.

## 16. Form fields

Every numeric field should have:

- visible label;
- input;
- explicit unit;
- inline validation state;
- on-demand help where required.

Preferred unit treatment:

```text
┌──────────────────┬────────┐
│ 1,690            │ veh/h  │
└──────────────────┴────────┘
```

This is preferred over placing units only in distant section text.

## 17. Required / optional / advanced fields

Do not rely on asterisks alone.

Baseline rules:

- required fields are the default visible set;
- optional fields labeled `Optional` where ambiguity exists;
- advanced/governed fields grouped under clearly named secondary sections;
- inactive conditional fields should usually be removed from layout rather than disabled in place.

## 18. Input precision

Display/edit precision must respect engineering meaning and existing engine contracts.

Do not round canonical inputs simply for visual neatness.

The presentation layer may format displayed values, but conversions must preserve the existing normalized/fingerprint semantics.

## 19. Choice controls

Use radio/segmented controls for short mutually exclusive engineering decisions.

Examples:

```text
Free-Flow Speed
● Measured
○ Estimated
```

```text
Heavy-vehicle adjustment
● General terrain
○ Specific grade
○ External PCE
```

Use dropdowns for larger enumerations such as terrain subtype/truck mix where appropriate.

Avoid a dropdown when the decision itself is important enough that options should remain visible.

## 20. Conditional content

When a method choice changes active inputs:

- preserve values internally only when safe/intentional;
- clearly update the visible branch;
- immediately recompute readiness;
- mark current result stale if the calculation identity changes.

Transitions should be quick and restrained; animation is not required.

## 21. Help text

Three levels:

### Field help

Short tooltip/popover or one-line note.

### Section help

Explains an engineering decision or qualified boundary.

### Methodology

Full reference content on Methodology/Scope pages or evidence view.

Do not put methodology paragraphs permanently below every field.

## 22. Validation styling

### Field error

- red border/background hint;
- concise inline message;
- `aria-invalid` or framework equivalent.

### Section error

- section status marker;
- count of issues.

### Error summary

Before Calculate, show a compact actionable list:

```text
2 items require attention
- Segment 2: PHF must be > 0 and <= 1
- Opposing-direction volume is required
```

Where technically feasible, selecting a message focuses the relevant field/cell.

## 23. Focus states

All interactive elements require strong keyboard-visible focus.

Baseline:

- 2–3 px accessible outline;
- offset from component edge;
- focus must remain visible on both light main content and dark sidebar surfaces.

Do not rely on subtle border-color change alone.

## 24. Buttons

### Primary

Use for the one dominant task action:

- Calculate;
- Recalculate;
- Create Analysis;
- Export confirmation.

### Secondary

- Edit Inputs;
- Duplicate Scenario;
- Compare;
- Change Basis.

### Toolbar

Compact New/Open/Save/Export/Help controls.

### Destructive

Distinct treatment and confirmation where data loss is possible.

Avoid more than one dominant primary button in the same action region.

## 25. Readiness / Calculation action bar

Long analysis pages should have a visually stable action area.

Ready:

```text
✓ Ready to calculate                         [ Calculate ]
```

Blocked:

```text
2 items required                             [ Calculate disabled ]
```

Stale:

```text
Input changed — result stale                 [ Recalculate ]
```

This may become sticky at the bottom of the main workspace on desktop if browser testing confirms it improves usability.

## 26. Result hero

Primary result hero should be stronger than ordinary cards but not enormous.

Baseline:

```text
┌──────────────────────────────────┐
│ LEVEL OF SERVICE                 │
│ LOS C                            │
│ Density 18.4 pc/km/ln            │
│ Current result                   │
└──────────────────────────────────┘
```

Capacity failure/handoff changes the semantic title and wording rather than merely changing color.

## 27. Metric cards

Use compact metric cards only for high-priority results.

Recommended normal maximum visible at once:

- approximately 3–6 depending on screen width;
- lower-priority metrics move to a compact table/details section.

Do not create a card for every scalar engine output.

## 28. Engineering Assessment panel

This is a major differentiator from the current worksheet experience.

Style:

- normal panel, not a chat bubble;
- deterministic bullet/statement structure;
- severity icons where useful;
- no generated conversational prose required.

Example:

```text
ENGINEERING ASSESSMENT
✓ Demand is below applicable capacity.
• FFS: estimated from roadway characteristics.
• Heavy vehicles: general terrain / rolling.
• No active scope limitation affects this result.
```

Interpretation rules must be unit-tested.

## 29. Stale result styling

Stale must be impossible to mistake for current.

Required:

- stale banner/status label;
- previous result visually subdued but readable;
- Recalculate primary action;
- current export disabled/guarded.

Do not delete the previous result immediately unless required by safety/integrity.

## 30. Capacity failure styling

Use strong but controlled error semantics.

Primary content:

```text
LOS F — Capacity exceeded
Speed and density are not predicted in this state
```

Avoid alarming generic software-error presentation because this is a valid engineering outcome.

## 31. HCM handoff styling

Use a dedicated method-state presentation distinct from capacity failure.

Example:

```text
HCM Method Handoff
No weaving LOS is assigned for this condition.
```

Use warning/transition visual language rather than software-error red unless the method contract requires otherwise.

## 32. Tables

Tables are first-class engineering components.

Baseline behavior:

- sticky header;
- optional sticky first column for wide grids;
- local horizontal scrolling;
- compact 11–13 px table text;
- tabular numerals;
- row hover/selection;
- keyboard-visible focus;
- clear editable vs calculated/read-only cells;
- error/warning cell backgrounds plus text/icon cues.

## 33. Two-Lane Facility grid

Additional requirements:

- locked cells retain readable contrast;
- do not use browser-disabled styling that makes engineering context hard to read;
- conditional opposing-volume cells activate only for passing-zone rows;
- validation can reference segment ID/name;
- results preserve row identity;
- segment result selection opens evidence without losing facility result context.

## 34. Read-only calculated cells

Calculated values shown inside data grids should look selectable/readable, not like editable inputs.

Recommended:

- soft neutral background;
- border;
- tabular number;
- text selection allowed;
- no fake input affordance.

## 35. Geometry diagrams

Diagrams should explain engineering configuration, not decorate the page.

Baseline visual language:

- simple vector/SVG line work;
- labels legible at normal desktop size;
- active lane/movement states visibly distinguishable;
- avoid perspective/3D unless it improves understanding;
- textual scope summary accompanies the diagram.

Initial uses:

- Weaving;
- Merge;
- Diverge.

Interactive diagram-based input may be evaluated later; R1 prototype may remain diagram + conventional controls.

## 36. Compare view

Comparison is table-first.

Use columns for scenarios and rows for canonical metrics.

Highlight meaningful changes using restrained semantic indicators.

Do not use charts unless they materially improve a comparison with many scenarios/segments.

LOS displays as grade transition, e.g. `D -> C`, not numeric percentage improvement.

## 37. Evidence views

Evidence should feel like an engineering calculation trace.

Preferred components:

- key/value definition lists;
- input tables;
- equation/step tables;
- source-reference links/text;
- structured warning/assumption lists;
- optional raw JSON code viewer.

Monospaced type is appropriate for identifiers/JSON only, not all engineering values.

## 38. Status badges

Badges are compact secondary state indicators.

Examples:

- Current;
- Stale;
- Warning;
- Capacity exceeded;
- Unsupported;
- HCM 7.0;
- Metric.

Do not turn every metadata value into a pill/badge.

## 39. Icons

Use icons sparingly for:

- New/Open/Save/Export;
- warning/error/current;
- expand/details;
- help;
- diagram controls.

Text labels remain visible for primary actions.

Avoid mixing multiple icon families.

## 40. Motion

Motion is functional only.

Allowed:

- subtle panel reveal;
- focus/selection transitions;
- loading indicator during calculation/API request.

Avoid:

- animated metric counts;
- bouncing alerts;
- decorative page transitions.

Respect reduced-motion preferences where framework support permits.

## 41. Loading state

Calculation request should show clear localized state:

```text
Calculating…
```

Rules:

- prevent duplicate submit;
- do not blank all inputs;
- preserve page location;
- on completion move visual focus to Result heading/summary appropriately.

## 42. Bilingual design

Thai and English must use the same engineering identity and layout hierarchy.

Design rules:

- allow labels/buttons to expand roughly 20–35% without clipping;
- avoid fixed-width text buttons;
- tables may use abbreviations only when both locales remain understandable;
- variable symbols may remain language-neutral with localized explanatory labels;
- units remain canonical engineering units;
- language switching must not recalculate the engine.

## 43. Unit-system switching

Metric/Imperial is presentation/application state, not a visual theme.

Switching units should:

- convert visible values using existing adapters;
- preserve calculation identity when canonical engine inputs remain equivalent;
- update unit suffixes immediately;
- avoid losing inactive conditional branch values unnecessarily.

## 44. Accessibility baseline

R1 UI acceptance requires:

- keyboard navigation for primary flows;
- visible focus;
- semantic labels for inputs;
- error association with fields;
- sufficient contrast;
- no color-only states;
- skip-to-main support or equivalent;
- table semantics where practical;
- diagrams accompanied by textual descriptions;
- reduced-motion-safe behavior.

## 45. Print / report design relationship

The on-screen application is not itself the final printed report.

Do not compromise the UI to make browser printing mimic the screen.

Use reporting/export templates that share:

- typography hierarchy;
- semantic result colors where printable;
- result terminology;
- method metadata;
- audit identity.

## 46. Component inventory for prototype

The first frontend prototype should implement/qualify at least these shared components:

```text
AppShell
AppHeader
SidebarNavigation
StatusBar
PageHeader
AnalysisHeader
EngineeringSection
Field
InputWithUnit
ChoiceGroup
StartingValuesControl
ScopeNotice
ErrorSummary
ReadinessBar
PrimaryAction
ResultHero
MetricCard
EngineeringAssessment
StatusBadge
DetailsTabs/Disclosure
DataGrid/Table
GeometryDiagramContainer
StaleResultBanner
CapacityFailurePanel
HandoffPanel
```

Method-specific components can be composed from these.

## 47. Design tokens

The final framework should centralize tokens for:

- colors;
- typography;
- spacing;
- radius;
- borders;
- focus ring;
- semantic states;
- layout dimensions;
- elevation.

No method page should define its own arbitrary color/spacing system.

## 48. Quality anti-pattern checklist

Reject a screen if it exhibits any of the following:

- application Save/Open embedded inside calculation inputs;
- more than one unrelated primary action;
- every field inside a separate card;
- raw JSON visible by default;
- full audit detail before the primary result;
- disabled inputs with unreadably low contrast;
- units detached from numeric fields;
- generic `Something went wrong` for an engineering capacity state;
- LOS conveyed only by color;
- dropdowns hiding important three-option engineering decisions;
- wide tables forcing whole-page horizontal scroll;
- active result remaining visually current after inputs change;
- duplicated HCM formulas in frontend components.

## 49. R0.8 acceptance criteria

R0.8 is acceptable when:

1. The visual character is explicitly conventional/professional rather than novelty-driven.
2. A compact desktop density is defined.
3. Shell geometry is consistent across methods.
4. Input/unit/error/focus behavior is standardized.
5. Required/conditional/advanced content hierarchy is defined.
6. Result hero, metric, assessment, stale, capacity, and handoff states have distinct design rules.
7. Engineering tables are treated as first-class components.
8. Bilingual and accessibility requirements are design inputs, not release cleanup.
9. Shared components/tokens are defined before method-specific pages.
10. The design remains implementable in more than one plausible frontend framework.

## 50. Next R0 gate

R0.9 should select the technology architecture and record the application boundary, including:

- frontend framework;
- Python API/application layer;
- local execution model;
- project file access model;
- calculation request/result contracts;
- frontend state strategy;
- test stack;
- packaging boundary;
- migration path from Streamlit.
