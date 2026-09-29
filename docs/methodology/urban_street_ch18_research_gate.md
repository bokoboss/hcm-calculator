# HCM 7.0 Chapter 18 Urban Street Segment — Research Gate

Status: **GO WITH CONDITIONS for product direction; numerical implementation blocked pending final HCM7 Chapter 18/30 evidence.**

Issue authority: #172

## Decision

The next candidate method is a bounded HCM 7.0 Chapter 18 Urban Street Segment workflow for the motorized-vehicle mode. The first release should accept a final downstream **through-movement control delay** from an external HCM-compatible intersection analysis tool instead of implementing Chapter 19 first.

The proposed boundary is:

```text
External intersection analysis
  -> downstream through control delay + downstream through capacity state/v-c
  -> Chapter 18 segment running-time calculation
  -> segment travel speed
  -> motorized LOS
```

This direction fits the current application architecture and avoids duplicating a full signalized-intersection engine before it is needed.

## Verified project state

The accepted application architecture is:

```text
React + TypeScript + Vite
  -> FastAPI
  -> framework-independent Python application layer
  -> qualified Python HCM engines
```

Python is the sole numerical authority. The current registry contains seven qualified workflows: Two-Lane Segment, Two-Lane Facility, Multilane Segment, Basic Freeway Segment, Weaving Segment, Merge Segment, and Diverge Segment.

A Chapter 18 implementation must be additive. Existing numerical behavior, method identifiers, Project v2 compatibility, current/stale semantics, fingerprints, exports, and reports remain protected.

## External evidence reviewed

### National Academies 2024 guide

Source:

- https://www.nationalacademies.org/read/27895/chapter/14

The guide explicitly maps its urban-street methodology to HCM7 Chapters 16 and 18 and states that Chapter 18 calculates link running performance and combines link running time with downstream intersection control delay to obtain segment average travel time and average speed.

The guide identifies the planning-level methodology in HCM7 Chapter 30 Section 5 / Exhibit 30-8 and references the following Chapter 18 calculation elements:

- Eq. 18-3: base free-flow speed;
- Eq. 18-4: signal-spacing adjustment;
- Eq. 18-5: free-flow speed;
- Eq. 18-6: proximity adjustment;
- Eq. 18-7: segment running time;
- Eq. 18-8: control-type adjustment;
- Step 5: downstream through delay from the applicable intersection methodology;
- Eq. 18-15: travel speed from running time and through delay;
- Exhibit 18-1: motorized LOS criteria.

It also states that LOS is determined for the major-road through movement in the analysis direction and that LOS is F when downstream through-movement v/c exceeds 1.0.

The same source explains that the full platoon-dispersion model is data- and computation-intensive and describes the planning-level path as the simpler alternative for progression treatment.

### HCM Volume 4

Source:

- https://hcmvolume4.org/

HCM Volume 4 is the official free online Applications Guide and includes supplemental chapters, detailed methodology, example problems, interpretations, updates, and errata. Registration is required.

Chapter 30 is therefore the preferred authoritative acceptance source for the planning-level Chapter 18 implementation and example fixture.

### HCM7 corrections / clarifications

Source:

- https://hcmvolume4.org/wp-content/uploads/2024/10/HCM7-corrections-clarifications-updates-12-2022.pdf

The December 2022 correction record was reviewed. No motorized Chapter 18 correction was identified in the public correction list examined for this research pass. This does not replace review of the final Chapter 18/30 sources or later official interpretations.

### PTV Vistro

Sources:

- https://cgi.ptvgroup.com/vision-help/VISTRO_2025_ENG/Content/Content-Topics/hcm-signal-intersect-analysis.htm
- https://cgi.ptvgroup.com/vision-help/VISTRO_2025_ENG/Content/Content-Topics/hcm-signal-intersect.htm

Vistro implements HCM 7th Edition signalized-intersection analysis and exposes distinct lane-group control delay, movement delay, approach delay, intersection delay, and v/c results. This makes it suitable as an external source, provided the Chapter 18 contract maps the exact required **through-movement** quantity and does not substitute approach or whole-intersection delay.

Vistro is an example external source, not a dependency. The HCM Calculator input contract should remain vendor-neutral.

## Available local evidence

The current user/project Library search contains existing final HCM7 sources used elsewhere in this project, including Chapter 13, Chapter 15, and Chapter 26 example material. No final HCM7 Chapter 18 or Chapter 30 file was found in the available Library search during this pass.

Therefore final Chapter 18/30 evidence is a named dependency before numerical implementation.

## Proposed v1 support envelope

### Supported

- HCM 7.0.
- Chapter 18 motorized-vehicle mode only.
- One urban-street segment and one subject direction per analysis.
- Planning-level / bounded methodology.
- HCM Chapter 18/30 BFFS, FFS, and running-time calculation after primary-source verification.
- External final downstream through control delay, in s/veh.
- Explicit downstream through capacity state / v/c quantity sufficient to enforce the Chapter 18 LOS-F rule.
- Explicit downstream control type.
- Explicit `d_other` only if the final method supports it as a direct input in the selected path.
- Metric-first presentation with HCM-native internal calculation units under the existing unit-conversion pattern.
- EN/TH UI and documentation.
- Full Project v2, fingerprint, current/stale, report/export, API, and Handbook integration after engine qualification.

### Deferred

- Chapter 16 facility aggregation.
- Internal Chapter 19, 20, 21, or 22 calculation.
- Full operational platoon-dispersion facility model.
- Pedestrian LOS.
- Bicycle LOS.
- Automatic Vistro import or vendor-specific file parsing.
- Traffic-demand balancing / O-D / sustained-spillback procedures unless the final bounded Chapter 18 path proves they are mandatory.
- Through stop-rate and spatial stop-rate outputs if they are outside the selected planning-level implementation.

## External-delay contract

The external result must represent the final downstream **through-movement control delay** required by Chapter 18.

The UI and persisted audit evidence should distinguish at least:

- source class: external HCM-compatible vs future internal HCM;
- source/tool note;
- HCM edition/method note where known;
- subject travel direction and through movement identity;
- final through control delay, s/veh;
- downstream through v/c or the exact equivalent quantity required by the final HCM source;
- analyst note / provenance.

Do not accept an unlabeled generic `intersection delay` field.

Do not recompute progression or intersection control delay on top of a final external through delay unless final HCM evidence explicitly requires an additional Chapter 18 adjustment. The design objective is to avoid double counting.

## Material unresolved questions

These are **BLOCKERS** for numerical code, not optional polish.

1. Obtain the final HCM7 Chapter 18 and Chapter 30 Section 5/example sources.
2. Verify exact equations, coefficients, ranges, table rules, defaults, and fail-closed boundaries for Eq. 18-3, 18-4, 18-5, 18-6, 18-7, 18-8, and 18-15.
3. Verify the exact use and bounds of Exhibit 18-13 or the applicable turn-delay procedure.
4. Confirm Chapter 18 segment applicability and spatial/temporal limits.
5. Confirm the exact downstream through-movement v/c definition, especially when an approach has multiple through lanes/lane groups.
6. Confirm that supplying final external through delay allows the bounded v1 workflow to bypass the internal arrival-during-green / signal-phase steps without losing another required Chapter 18 adjustment.
7. Extract an authoritative final Chapter 30 planning-level example into a non-copyrighted numerical fixture with expected intermediate and final results.
8. Classify every physically sided term for Thailand/LHT. Terms involving curb, parking, access points, and opposing-side left-turn access must not be mirrored by intuition.

## Preliminary input model

Names are provisional until the final source crosswalk is accepted.

### Segment / geometry

- unit system;
- segment length;
- number of through lanes in subject direction;
- posted speed limit;
- restrictive-median proportion;
- curb proportion / physically sided curb input after LHT qualification;
- access-point data or an accepted HCM default-density path;
- on-street-parking proportion after LHT qualification;
- adjacent signal spacing where required;
- downstream control type.

### Demand / performance boundary

- midsegment demand flow rate;
- through-demand flow rate if separately required;
- external downstream through control delay;
- downstream through v/c or required capacity inputs;
- other segment delay where explicitly supported.

### Provenance

- delay source class;
- source/tool name;
- source method / HCM edition note;
- direction / movement identifier;
- analyst note.

## Preliminary output model

At minimum, if confirmed by final HCM evidence:

- base free-flow speed;
- free-flow speed;
- running time;
- downstream through control delay used;
- total segment travel time;
- through travel speed;
- downstream through v/c / capacity status;
- motorized LOS;
- active assumptions/defaults;
- audit/intermediate values sufficient to reproduce the result.

## Architecture consequences

A new method should use a dedicated Python engine/module and a new explicit method identity such as `urban_street_segment`. No HCM equation should be introduced in TypeScript.

The external-delay and capacity-state inputs materially affect calculation interpretation and therefore belong in normalized inputs/fingerprints and project persistence rather than presentation-only metadata. Provenance text that does not affect calculation may be stored separately from numerical identity if the project contract permits; this decision must be explicit.

Existing seven workflows must remain behaviorally unchanged.

## Scrutiny

### Why this direction is preferable

Implementing Chapter 19 first is not necessary to obtain a useful Chapter 18 product. Treating the downstream intersection as a qualified external boundary:

- dramatically reduces initial method scope;
- maps to the Chapter 18 separation between link running performance and intersection delay;
- supports real engineering workflows using existing HCM-compatible intersection software;
- leaves a clean future seam for internal Chapter 19/20/21/22 engines.

### Main failure modes

- using approach/intersection delay instead of through-movement delay;
- selecting the wrong v/c quantity from a multi-lane downstream approach;
- double counting progression;
- silently using a planning simplification outside its support envelope;
- applying right-hand-traffic sided terms directly to Thailand/LHT;
- validating only final LOS while intermediate equations are wrong;
- accepting a method against a draft/public secondary source instead of the final HCM example.

## Acceptance sequence

1. Final-source evidence crosswalk.
2. Explicit support contract and fail-closed cases.
3. Python engine plus authoritative Chapter 30 numerical fixture.
4. Boundary/unit-equivalence tests and independent methodology review.
5. Application/API integration.
6. Project v2 / fingerprint / report / export integration.
7. EN/TH React workflow and Handbook entry.
8. Full existing regression suite and browser qualification.
9. Vercel Preview verification.
10. Fresh-context independent review of actual equations, fixtures, diff, and supported-scope claims before merge.

## Research-gate verdict

**GO WITH CONDITIONS.**

The product architecture and external-delay concept are viable. The next action is not speculative coding: it is to obtain final HCM7 Chapter 18 and Chapter 30 evidence and close the eight blocker questions above. Once those are closed, the numerical engine can be implemented as a bounded STRICT work package.