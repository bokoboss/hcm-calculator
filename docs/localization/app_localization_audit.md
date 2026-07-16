# Application localization audit (Phase 15.1)

## Architecture finding

`hcmcalc.ui.i18n` is the single presentation localization mechanism and correctly keeps calculation modules independent. `validate_catalogs()` checks key parity, blank values, and named placeholders. Its English fallback is safe from crashes but leaks English to Thai users; Phase 15.2 must add a test that every rendered UI string originates in a catalog or is explicitly marked language-neutral. Do not localize JSON keys, schemas, HCM equation references, method identifiers, or standard engineering units.

Visible English-only/hardcoded surfaces include app constants (`SCOPE_NOTICE`, `LIMITATIONS_FOOTER`, default/template labels, segment-type labels), validated-case viewer, Supported Workflows page headings/body, shared layout labels, report/export prose, exception strings, and parts of diagrams/captions. Merge/diverge catalog entries were added as English fallbacks in the Thai dictionary for `nav.merge_segment`, `nav.diverge_segment`, `ramp.merge.title`, `ramp.diverge.title`, and project-file wording; these are fallback leakage, not completed Thai translation. Reports are presently English language-neutral artifacts and need an explicit product decision before translation.

## Terminology decisions

| English | Recommended Thai | Acronym/context | Discourage |
|---|---|---|---|
| Two-Lane Segment | ช่วงถนนสองช่องจราจร | keep HCM | ถนนสองเลน (ambiguous) |
| Two-Lane Facility | สิ่งอำนวยความสะดวกถนนสองช่องจราจร | explain once | สถานีถนน |
| Multilane Segment | ช่วงถนนหลายช่องจราจร | — | ถนนหลายเลน (informal alone) |
| Basic Freeway Segment | ช่วงทางด่วนพื้นฐาน | HCM Chapter 12 | ทางด่วนพื้นฐาน (without ช่วง) |
| Weaving Segment | ช่วงสานการจราจร | retain “weaving” once in parentheses | ช่วงทอผ้า |
| Merge / Diverge Segment | ช่วงรวมกระแส / ช่วงแยกกระแส | HCM 7.0 | ทางรวม/ทางแยก (too broad) |
| free-flow / base / adjusted FFS | ความเร็วไหลอิสระ / ความเร็วไหลอิสระฐาน / ความเร็วไหลอิสระปรับแก้ | show FFS after first use | ความเร็วอิสระ |
| demand flow rate | อัตราการไหลของความต้องการ | veh/h unchanged | ปริมาณความต้องการ |
| capacity / adjusted capacity | ความจุ / ความจุปรับแก้ | — | ความสามารถ |
| density | ความหนาแน่น | units remain visible | ความหนาแน่นของรถยนต์ (unless needed) |
| level of service | ระดับการให้บริการ | LOS remains visible | ระดับบริการ |
| ramp influence area | พื้นที่อิทธิพลทางลาด | — | เขตทางลาด |
| acceleration / deceleration lane | ช่องเร่ง / ช่องชะลอ | LA/LD preserved | ช่องความเร็ว |
| weaving lanes | ช่องจราจรสาน | NWL preserved | ช่องสาน |
| heavy vehicles / PCE / PHF | ยานพาหนะหนัก / เทียบเท่ารถยนต์นั่ง / ตัวคูณชั่วโมงสูงสุด | PCE, PHF visible | รถใหญ่ / ปัจจัยพีก |
| lateral clearance / access-point density | ระยะเคลียร์ด้านข้าง / ความหนาแน่นจุดทางเข้าออก | — | ระยะข้าง / ความหนาแน่นทางเข้า |
| terrain / rolling / specific grade | ภูมิประเทศ / ลูกคลื่น / ความชันเฉพาะ | — | ลูกกลิ้ง |
| capacity failure | เกินความจุ | not an application error | ล้มเหลว |
| stopping condition / handoff | เงื่อนไขหยุด / ส่งต่อการวิเคราะห์ | distinguish | หยุดระบบ |
| not predicted / stale result | ไม่ทำนาย / ผลลัพธ์ไม่เป็นปัจจุบัน | — | ไม่มีค่า / เก่า |
| calculation required/current result | ต้องคำนวณ / ผลลัพธ์ปัจจุบัน | — | จำเป็นต้องคำนวณ |
| unsupported scope | อยู่นอกขอบเขตที่รองรับ | — | ไม่รองรับ (without scope) |
| geometry evidence/configuration reference | หลักฐานเรขาคณิต/ภาพอ้างอิงรูปแบบ | diagram is not input | รูปแบบเรขาคณิต |
| project file/export report | ไฟล์โครงการ/รายงานส่งออก | JSON, CSV unchanged | ไฟล์งาน/รายงานออก |

## Phase 15.2 backlog

1. Move all visible constants into semantic keys; retain one catalog and named placeholders.
2. Replace Thai English fallback entries with reviewed text above; test exact key-set and placeholders.
3. Audit diagrams and captions for Thai wrapping, alt text, and conceptual-reference disclaimer.
4. Map engine/project exceptions to localized presentation messages while retaining technical detail in audit output.
5. Decide whether exports are localized; if yes, localize templates only, never serialized schema keys.
