# Multilane UX Pilot Specification

Baseline: `fd5172ec3e4abdb161f268507c29c74b4848047c`
Phase: 16.1 design specification only

## Non-Goals

- Do not change Multilane formulas, lookup tables, interpolation behavior, validation boundaries, schema, fingerprints, or project compatibility.
- Do not add custom Truck Mix interpolation or imply HCM interpolation support.
- Do not create a multi-page wizard.
- Do not remove auditability, intermediate values, assumptions, warnings, or export records.

## Current Task Flow

1. User selects Multilane Segment from global navigation.
2. Load project appears first.
3. User sees Starting values and units.
4. Optional defaults are collapsed.
5. User chooses Free-flow speed source.
6. Geometry, estimated/measured FFS fields, traffic demand, grade, Heavy Vehicle %, PCE source, terrain, Truck Mix, and advanced note appear in a compact form.
7. User clicks Calculate.
8. Result summary appears in the right column.
9. Calculation details, audit JSON, full JSON, Project file, and Export / Report are available after the result.
10. Input changes make the result stale and hide report exports.

Main issue: the form is method-structured, not task-structured. Users must infer which fields are core, which are branch-specific, and which are HCM table-domain controls.

## Proposed Task Flow

Keep one page, but make it a guided worksheet with progressive disclosure:

1. **Start**
   - Blank case.
   - Optional template.
   - Unit system.
   - Optional project load as secondary action.
2. **Traffic and Segment Basics**
   - Number of lanes.
   - Segment length.
   - Demand volume.
   - Peak-hour factor.
   - Heavy Vehicle %.
3. **Free-Flow Speed**
   - Choose Measured FFS or Estimated FFS.
   - Show only fields required by the selected branch.
4. **Heavy-Vehicle Adjustment**
   - Replace separate `PCE Mode` plus `terrain_type` with one three-way method choice:
     - General terrain lookup.
     - Specific grade lookup.
     - External PCE.
5. **Calculate**
   - Single primary action.
   - Readiness summary above the button.
   - Inline validation near affected sections.
6. **Result Summary**
   - LOS.
   - Demand/capacity ratio.
   - Speed.
   - Density.
7. **Details and Engineering Record**
   - Adjusted FFS.
   - Capacity.
   - PCE and source.
   - Heavy-vehicle adjustment factor.
   - Assumptions, warnings, lookup path, intermediate values, audit record.
8. **Project and Export**
   - After current result: Save project and Export report in one action area.
   - After stale result: show Recalculate, hide report exports, save project without stale result only.

## Information Architecture

| Section | Default visibility | Purpose |
| --- | --- | --- |
| Start | Open | Choose blank/template/unit or load existing project. |
| Traffic and Segment Basics | Open | Collect inputs most users already have. |
| Free-Flow Speed | Open | Select measured or estimated branch. |
| Heavy-Vehicle Adjustment | Open | Select lookup/external method and show only relevant fields. |
| Calculate | Open | Confirm readiness and run current inputs. |
| Result Summary | Open after result | Show engineering decision outputs first. |
| Details | Collapsed after result | Preserve transparency without competing with primary result. |
| Project and Export | Compact action row after result | Save or export only the current engineering record. |

## Conditional Field Matrix

| Field | Always | Measured FFS | Estimated FFS | General terrain | Specific grade | External PCE |
| --- | --- | --- | --- | --- | --- | --- |
| Unit system | Yes | Yes | Yes | Yes | Yes | Yes |
| Number of lanes | Yes | Yes | Yes | Yes | Yes | Yes |
| Segment length | Yes | Yes | Yes | Yes | Yes | Yes |
| Demand volume | Yes | Yes | Yes | Yes | Yes | Yes |
| Peak-hour factor | Yes | Yes | Yes | Yes | Yes | Yes |
| Heavy Vehicle % | Yes | Yes | Yes | Yes | Yes | Yes |
| Measured FFS | No | Show | Hide | n/a | n/a | n/a |
| Posted speed | No | Hide | Show | n/a | n/a | n/a |
| Lane width | No | Hide | Show | n/a | n/a | n/a |
| Right-side lateral clearance | No | Hide | Show | n/a | n/a | n/a |
| Median type | No | Hide | Show | n/a | n/a | n/a |
| Left-side lateral clearance | No | Hide | Show only when median is divided | n/a | n/a | n/a |
| Access-point density | No | Hide | Show | n/a | n/a | n/a |
| Terrain type level/rolling | No | n/a | n/a | Show | Hide | Hide |
| Grade | No | n/a | n/a | Hide | Show | Hide |
| Grade length | No | n/a | n/a | Hide unless method requires distinct grade length | Show if implemented contract requires it; otherwise state segment length is used | Hide |
| Heavy-vehicle composition | No | n/a | n/a | Hide | Show | Hide |
| External PCE | No | n/a | n/a | Hide | Hide | Show |
| PCE source/provenance | No | n/a | n/a | Internal lookup | Internal lookup | User-supplied source/provenance |

## Labels And Help Text

### English

| Current | Recommended |
| --- | --- |
| Free-flow speed source | Free-flow speed method |
| Estimated | Estimate from roadway features |
| Measured | Use measured field speed |
| Passenger-car-equivalent source | Heavy-vehicle adjustment method |
| Internal HCM lookup | Use HCM lookup from terrain/grade |
| External override | Enter externally approved PCE |
| PCE terrain treatment | Terrain/grade lookup |
| Truck mix | Heavy-vehicle composition (SUT/TT) |
| Heavy vehicles (%) | Heavy vehicles in total traffic (%) |
| External passenger-car equivalent | External PCE |

Inline help:

- **Heavy vehicles in total traffic (%):** Percent of all traffic made up of heavy vehicles.
- **Heavy-vehicle composition (SUT/TT):** Composition within the heavy-vehicle portion only. SUT = single-unit trucks; TT = tractor-trailers.
- **Specific grade lookup:** Uses the implemented HCM table domain for grade, segment/grade length, and printed SUT/TT mixtures.
- **External PCE:** Use when the project has an approved PCE or when the internal lookup table does not cover the truck mix or boundary.

### Thai

| Current | Recommended |
| --- | --- |
| แหล่งที่มาค่าเทียบเท่ารถยนต์นั่ง | วิธีปรับผลของยานพาหนะหนัก |
| ค้นจากตาราง HCM ภายใน | ใช้ค่าจากตาราง HCM ตามภูมิประเทศ/ความชัน |
| กำหนดค่าภายนอก | กรอกค่า PCE ภายนอกที่ได้รับอนุมัติ |
| สัดส่วนรถบรรทุก | สัดส่วนยานพาหนะหนัก (SUT/TT) |
| Heavy vehicles (%) / ยานพาหนะหนัก | ยานพาหนะหนักในกระแสจราจรรวม (%) |
| ค่าเทียบเท่ารถยนต์นั่งภายนอก | ค่า PCE ภายนอก |

Inline help:

- **ยานพาหนะหนักในกระแสจราจรรวม (%):** สัดส่วนยานพาหนะหนักเมื่อเทียบกับปริมาณจราจรทั้งหมด
- **สัดส่วนยานพาหนะหนัก (SUT/TT):** สัดส่วนภายในกลุ่มยานพาหนะหนักเท่านั้น; SUT คือรถบรรทุกเดี่ยว และ TT คือรถกึ่งพ่วง/รถพ่วง
- **ใช้ค่าจากตาราง HCM:** ใช้เฉพาะขอบเขตตาราง HCM ที่ระบบรองรับในปัจจุบัน
- **ค่า PCE ภายนอก:** ใช้เมื่อโครงการมีค่า PCE ที่ได้รับอนุมัติ หรือเมื่อสัดส่วน/ขอบเขตอยู่นอกตารางที่ระบบรองรับ

## Truck Mix UX Resolution

Truck Mix must not appear as a general traffic mix field. In the pilot:

- Rename it to **Heavy-vehicle composition (SUT/TT)**.
- Place it only inside **Specific grade lookup**.
- Keep only the three currently supported choices:
  - 30% SUT / 70% TT.
  - 50% SUT / 50% TT.
  - 70% SUT / 30% TT.
- Add inline copy: `Other heavy-vehicle compositions are outside the current internal HCM lookup domain. Choose External PCE if the project has an approved value.`
- When External PCE is active, hide terrain lookup, grade, grade length, and Heavy-vehicle composition.
- Do not imply interpolation or custom mix support.

## Validation Messages

Validation should be section-local when possible:

| Scenario | Message |
| --- | --- |
| Missing/invalid measured FFS | `Measured FFS must be a positive finite speed. Enter a measured speed or choose Estimated FFS.` |
| Estimated FFS lane count unsupported | `Estimated FFS is currently supported for two or three lanes in the analysis direction. Use Measured FFS or revise the lane count.` |
| Divided median without left clearance | `Left-side lateral clearance is required when Median type is Divided.` |
| Unsupported internal PCE mix/domain | `The selected grade, length, or heavy-vehicle composition is outside the implemented HCM lookup domain. Choose External PCE if an approved value is available.` |
| External PCE missing | `External PCE must be a positive finite value and should be traceable to an approved source.` |
| Capacity failure | `Demand exceeds capacity. LOS F is reported; speed and density are not predicted by the bounded method.` |

Thai copies should preserve technical terms PCE, FFS, SUT, and TT where translation would reduce precision, while explaining them in Thai on first use.

## Stale-State Behavior

Current behavior correctly hides report exports when inputs change. The pilot should strengthen hierarchy:

- Replace generic stale panel with: `Inputs changed. Recalculate to update LOS, speed, density, and report exports.`
- Show `Recalculate` as the only primary action.
- Hide old LOS, speed, density, and report export controls.
- Allow Save project, but label the consequence: `Save inputs only; stale result will not be included.`
- Keep audit/details for the old run hidden unless an explicit `Show previous run details` disclosure is added.

## Result Hierarchy

Primary summary:

1. LOS.
2. Demand/capacity ratio.
3. Speed used for density.
4. Density.

Secondary summary:

- Adjusted FFS.
- Capacity.
- PCE.
- Heavy-vehicle adjustment factor.
- Capacity status.

Details:

- FFS lookup path and adjustments.
- PCE source and lookup path.
- Normalized inputs.
- Units.
- Method version and calculation contract.
- Assumptions.
- Warnings.
- Intermediate values.
- Audit record.

Capacity failure:

- Keep LOS F primary.
- Replace speed and density values with `Not predicted`.
- Put the failure explanation directly under LOS F, not below details.

## Project And Export Placement

Before calculation:

- Start section includes `Load project` as a secondary disclosure.
- Result column says calculation is required.
- Project save is secondary and states it saves inputs only.

After current result:

- Show compact action row:
  - Save project.
  - Export report.
  - Details.
- Put CSV, Excel, Markdown, and Report JSON inside Export report.

After stale input:

- Hide report export.
- Save project remains available as inputs-only.
- Primary action is Recalculate.

## Accessibility Requirements

- All branch controls must be keyboard reachable.
- Section order must match reading order: Start, Basics, FFS, Heavy-vehicle adjustment, Calculate, Results, Details, Project/export.
- Essential status must not rely on color alone.
- Thai labels must fit at 768 px without overlapping controls.
- Help text must be attached to the control it explains or appear immediately below it.
- Collapsed sections must have descriptive labels, not generic `Advanced`.

## Acceptance Criteria

- Multilane can complete a default Metric calculation with fewer visible branch-only fields before the first Calculate.
- Measured FFS hides estimated FFS fields.
- Estimated FFS shows divided-median left clearance only when needed.
- Heavy-vehicle adjustment is a three-way task choice, not separate PCE Mode plus terrain controls.
- General terrain hides Truck Mix, grade length, and External PCE.
- Specific grade shows grade and Heavy-vehicle composition with table-domain copy.
- External PCE hides terrain lookup and Heavy-vehicle composition.
- Truck Mix copy explicitly distinguishes heavy-vehicle composition from Heavy Vehicle %.
- Stale result hides old primary metrics and report exports.
- Current result exposes LOS, demand/capacity ratio, speed, and density before details.
- Audit record still includes normalized inputs, units, method version, calculation contract, PCE source, lookup path, assumptions, warnings, intermediate values, and exports.
- Existing Multilane calculation, project, export, localization, and regression tests continue to pass.
