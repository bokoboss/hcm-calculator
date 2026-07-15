"""Small, deterministic presentation-only localization service.

Calculation modules deliberately do not import this module.  Catalog entries use
stable semantic identifiers and named ``str.format`` placeholders rather than
English display text as identifiers.
"""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any


DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = ("en", "th")


EN: dict[str, str] = {
    "app.title": "HCM Calculator",
    "app.scope_notice": "Manual HCM worksheets with auditable inputs, calculation details, project files, and report exports.",
    "app.limitations_footer": "Use each calculator's Validation basis and limitations section for method coverage details.",
    "nav.calculator_mode": "Calculator mode",
    "nav.two_lane_segment": "Two-Lane Segment",
    "nav.two_lane_facility": "Two-Lane Facility",
    "nav.multilane_segment": "Multilane Segment",
    "nav.basic_freeway_segment": "Basic Freeway Segment",
    "nav.supported_workflows": "Supported Workflows",
    "locale.label": "Language",
    "locale.en": "English",
    "locale.th": "Thai",
    "status.calculation": "Calculation status: {status}",
    "status.ready": "Ready",
    "status.calculated": "Calculated",
    "status.stale": "Input changed — recalculate required",
    "status.missing_required": "Missing required input",
    "status.not_predicted": "Not predicted",
    "status.result_current": "Result is current",
    "status.result_stale": "Result is stale",
    "project.load_current": "Project loaded with a current result. Review the restored inputs as needed.",
    "project.migrated": "Project migrated to the current input contract. Review the restored inputs before using the retained result.",
    "project.recalculation_required": "Project loaded, but its stored result is not current. Review the restored inputs and click Run calculation to recalculate.",
    "project.locale_restored": "Saved project language restored: {language}.",
    "project.presentation_locale": "Presentation language",
    "export.language": "Export language",
    "export.same_as_ui": "Same as current UI",
    "export.english": "English",
    "export.thai": "Thai",
    "export.download_csv": "Download CSV",
    "export.download_excel": "Download Excel",
    "export.download_markdown": "Download Markdown",
    "export.download_json": "Download Report JSON",
    "export.unavailable": "Report export unavailable: {error}",
    "export.guidance": "Exports reflect this calculated result in the selected display unit system and language. They do not broaden methodology support.",
    "report.summary": "Summary Result",
    "report.inputs": "Key Inputs",
    "report.normalized_inputs": "Normalized Engine Inputs",
    "report.segment_results": "Segment Results",
    "report.assumptions": "Assumptions",
    "report.warnings": "Warnings",
    "report.limitations": "Limitations",
    "report.audit": "Audit / Source References Summary",
    "report.intermediate_values": "Intermediate Values",
    "report.label": "Label",
    "report.value": "Value",
    "report.unit": "Unit",
    "report.category": "Category",
    "report.text": "Text",
    "report.no_rows": "No rows reported.",
    "report.none": "No {heading} reported.",
    "result.key_summary": "Key result summary",
    "result.outputs": "Outputs",
    "result.segment_outputs": "Segment outputs",
    "result.level_of_service": "Level of service",
    "result.capacity": "Capacity",
    "result.demand_flow_rate": "Demand flow rate",
    "result.free_flow_speed": "Free-flow speed",
    "result.mean_speed": "Mean speed",
    "result.density": "Density",
    "result.follower_density": "Follower density",
    "result.percent_followers": "Percent followers",
    "result.average_travel_speed": "Average travel speed",
    "result.adjusted_capacity": "Adjusted capacity",
    "result.demand_capacity_ratio": "Demand-to-capacity ratio",
    "result.heavy_vehicle_factor": "Heavy-vehicle factor",
    "result.speed_adjustment_factor": "Speed adjustment factor",
    "result.capacity_adjustment_factor": "Capacity adjustment factor",
    "result.full_json": "Full result JSON",
    "result.download_json": "Download full result JSON",
    "common.method": "Method",
    "common.facility_type": "Facility type",
    "common.result": "Result",
    "common.assumptions": "Assumptions",
    "common.warnings": "Warnings",
    "common.intermediate_values": "Intermediate values",
    "common.no_assumptions": "No assumptions reported.",
    "common.no_warnings": "No warnings reported.",
    "common.no_outputs": "No scalar outputs were returned.",
    "error.unsupported_methodology": "Unsupported methodology.",
    "error.unsupported_export": "Unsupported export format: {format}.",
    "error.invalid_locale": "Unsupported locale: {locale}.",
    "field.level_of_service": "Level of service",
    "field.capacity": "Capacity",
    "field.adjusted_capacity": "Adjusted capacity",
    "field.demand_flow_rate": "Demand flow rate",
    "field.free_flow_speed": "Free-flow speed",
    "field.average_speed": "Average travel speed",
    "field.follower_density": "Follower density",
    "field.capacity_pc_h_ln": "Capacity",
    "field.adjusted_capacity_pc_h_ln": "Adjusted capacity",
    "field.demand_flow_rate_pc_h_ln": "Demand flow rate",
    "field.density_pc_mi_ln": "Density",
    "field.mean_speed_mph": "Mean speed",
    "field.average_speed_mph": "Average travel speed",
    "field.free_flow_speed_mph": "Free-flow speed",
    "field.adjusted_free_flow_speed_mph": "Adjusted free-flow speed",
    "field.base_free_flow_speed_mph": "Base free-flow speed",
    "field.follower_density_followers_mi_ln": "Follower density",
    "field.percent_followers": "Percent followers",
    "field.peak_hour_factor": "Peak-hour factor (PHF)",
    "field.passenger_car_equivalent": "Passenger-car equivalent (PCE)",
    "field.heavy_vehicle_adjustment_factor": "Heavy-vehicle factor",
    "field.speed_adjustment_factor": "Speed adjustment factor (SAF)",
    "field.capacity_adjustment_factor": "Capacity adjustment factor (CAF)",
    "field.demand_capacity_ratio": "Demand-to-capacity ratio",
    "field.segment_length": "Segment length",
    "field.lane_width": "Lane width",
    "field.grade_percent": "Grade",
    "field.access_point_density": "Access-point density",
    "enum.measured": "Measured",
    "enum.estimated": "Estimated",
    "enum.external": "External",
    "enum.internal": "Internal",
    "enum.not_predicted": "Not predicted",
}

TH: dict[str, str] = {
    "app.title": "เครื่องคำนวณ HCM",
    "app.scope_notice": "แบบฟอร์ม HCM สำหรับการวิเคราะห์ที่ตรวจสอบย้อนกลับได้ พร้อมรายละเอียดการคำนวณ ไฟล์โครงการ และการส่งออกรายงาน",
    "app.limitations_footer": "โปรดดูส่วนเกณฑ์การตรวจสอบและข้อจำกัดของเครื่องคำนวณแต่ละรายการสำหรับขอบเขตของวิธีการ",
    "nav.calculator_mode": "โหมดเครื่องคำนวณ",
    "nav.two_lane_segment": "ช่วงถนนสองช่องจราจร",
    "nav.two_lane_facility": "สิ่งอำนวยความสะดวกถนนสองช่องจราจร",
    "nav.multilane_segment": "ช่วงถนนหลายช่องจราจร",
    "nav.basic_freeway_segment": "ช่วงทางด่วนพื้นฐาน",
    "nav.supported_workflows": "ขั้นตอนการทำงานที่รองรับ",
    "locale.label": "ภาษา",
    "locale.en": "อังกฤษ",
    "locale.th": "ไทย",
    "status.calculation": "สถานะการคำนวณ: {status}",
    "status.ready": "พร้อม",
    "status.calculated": "คำนวณแล้ว",
    "status.stale": "ข้อมูลนำเข้าเปลี่ยนแปลง — ต้องคำนวณใหม่",
    "status.missing_required": "ข้อมูลนำเข้าที่จำเป็นไม่ครบ",
    "status.not_predicted": "ไม่มีการพยากรณ์ค่า",
    "status.result_current": "ผลลัพธ์เป็นปัจจุบัน",
    "status.result_stale": "ผลลัพธ์ไม่เป็นปัจจุบัน",
    "project.load_current": "โหลดโครงการพร้อมผลลัพธ์ปัจจุบันแล้ว โปรดตรวจสอบข้อมูลนำเข้าที่กู้คืนตามความเหมาะสม",
    "project.migrated": "ย้ายโครงการไปยังสัญญาข้อมูลนำเข้าปัจจุบันแล้ว โปรดตรวจสอบข้อมูลนำเข้าที่กู้คืนก่อนใช้ผลลัพธ์ที่เก็บไว้",
    "project.recalculation_required": "โหลดโครงการแล้ว แต่ผลลัพธ์ที่เก็บไว้ไม่เป็นปัจจุบัน โปรดตรวจสอบข้อมูลนำเข้าที่กู้คืนและกดคำนวณใหม่",
    "project.locale_restored": "กู้คืนภาษาที่บันทึกไว้ของโครงการแล้ว: {language}",
    "project.presentation_locale": "ภาษาสำหรับการแสดงผล",
    "export.language": "ภาษาส่งออก",
    "export.same_as_ui": "เหมือนภาษาในหน้าจอ",
    "export.english": "อังกฤษ",
    "export.thai": "ไทย",
    "export.download_csv": "ดาวน์โหลด CSV",
    "export.download_excel": "ดาวน์โหลด Excel",
    "export.download_markdown": "ดาวน์โหลด Markdown",
    "export.download_json": "ดาวน์โหลด JSON รายงาน",
    "export.unavailable": "ไม่สามารถส่งออกรายงานได้: {error}",
    "export.guidance": "การส่งออกสะท้อนผลลัพธ์ที่คำนวณแล้วตามหน่วยแสดงผลและภาษาที่เลือก โดยไม่ขยายขอบเขตของวิธีการ",
    "report.summary": "สรุปผลลัพธ์",
    "report.inputs": "ข้อมูลนำเข้าหลัก",
    "report.normalized_inputs": "ข้อมูลนำเข้าของเครื่องมือที่ปรับมาตรฐานแล้ว",
    "report.segment_results": "ผลลัพธ์รายช่วง",
    "report.assumptions": "ข้อสมมติ",
    "report.warnings": "คำเตือน",
    "report.limitations": "ข้อจำกัด",
    "report.audit": "สรุปการตรวจสอบ / แหล่งอ้างอิง",
    "report.intermediate_values": "ค่าระหว่างการคำนวณ",
    "report.label": "รายการ",
    "report.value": "ค่า",
    "report.unit": "หน่วย",
    "report.category": "หมวดหมู่",
    "report.text": "ข้อความ",
    "report.no_rows": "ไม่มีรายการรายงาน",
    "report.none": "ไม่มี {heading} ที่รายงาน",
    "result.key_summary": "สรุปผลลัพธ์หลัก",
    "result.outputs": "ผลลัพธ์",
    "result.segment_outputs": "ผลลัพธ์รายช่วง",
    "result.level_of_service": "ระดับการให้บริการ (LOS)",
    "result.capacity": "ความจุ",
    "result.demand_flow_rate": "อัตราการไหลความต้องการ",
    "result.free_flow_speed": "ความเร็วการไหลอิสระ (FFS)",
    "result.mean_speed": "ความเร็วเฉลี่ย",
    "result.density": "ความหนาแน่น",
    "result.follower_density": "ความหนาแน่นของรถตาม",
    "result.percent_followers": "ร้อยละของรถตาม",
    "result.average_travel_speed": "ความเร็วเดินทางเฉลี่ย",
    "result.adjusted_capacity": "ความจุที่ปรับแล้ว",
    "result.demand_capacity_ratio": "อัตราส่วนความต้องการต่อความจุ",
    "result.heavy_vehicle_factor": "ตัวคูณปรับยานพาหนะหนัก",
    "result.speed_adjustment_factor": "ตัวคูณปรับความเร็ว (SAF)",
    "result.capacity_adjustment_factor": "ตัวคูณปรับความจุ (CAF)",
    "result.full_json": "JSON ผลลัพธ์ทั้งหมด",
    "result.download_json": "ดาวน์โหลด JSON ผลลัพธ์ทั้งหมด",
    "common.method": "วิธีการ",
    "common.facility_type": "ประเภทสิ่งอำนวยความสะดวก",
    "common.result": "ผลลัพธ์",
    "common.assumptions": "ข้อสมมติ",
    "common.warnings": "คำเตือน",
    "common.intermediate_values": "ค่าระหว่างการคำนวณ",
    "common.no_assumptions": "ไม่มีข้อสมมติที่รายงาน",
    "common.no_warnings": "ไม่มีคำเตือนที่รายงาน",
    "common.no_outputs": "ไม่มีผลลัพธ์เชิงตัวเลขที่ส่งกลับ",
    "error.unsupported_methodology": "ไม่รองรับวิธีการนี้",
    "error.unsupported_export": "รูปแบบการส่งออกไม่รองรับ: {format}",
    "error.invalid_locale": "ไม่รองรับภาษา: {locale}",
    "field.level_of_service": "ระดับการให้บริการ (LOS)",
    "field.capacity": "ความจุ",
    "field.adjusted_capacity": "ความจุที่ปรับแล้ว",
    "field.demand_flow_rate": "อัตราการไหลความต้องการ",
    "field.free_flow_speed": "ความเร็วการไหลอิสระ (FFS)",
    "field.average_speed": "ความเร็วเดินทางเฉลี่ย",
    "field.follower_density": "ความหนาแน่นของรถตาม",
    "field.capacity_pc_h_ln": "ความจุ",
    "field.adjusted_capacity_pc_h_ln": "ความจุที่ปรับแล้ว",
    "field.demand_flow_rate_pc_h_ln": "อัตราการไหลความต้องการ",
    "field.density_pc_mi_ln": "ความหนาแน่น",
    "field.mean_speed_mph": "ความเร็วเฉลี่ย",
    "field.average_speed_mph": "ความเร็วเดินทางเฉลี่ย",
    "field.free_flow_speed_mph": "ความเร็วการไหลอิสระ (FFS)",
    "field.adjusted_free_flow_speed_mph": "ความเร็วการไหลอิสระที่ปรับแล้ว",
    "field.base_free_flow_speed_mph": "ความเร็วการไหลอิสระฐาน",
    "field.follower_density_followers_mi_ln": "ความหนาแน่นของรถตาม",
    "field.percent_followers": "ร้อยละของรถตาม",
    "field.peak_hour_factor": "ตัวคูณชั่วโมงเร่งด่วน (PHF)",
    "field.passenger_car_equivalent": "ค่าเทียบเท่ารถยนต์นั่ง (PCE)",
    "field.heavy_vehicle_adjustment_factor": "ตัวคูณปรับยานพาหนะหนัก",
    "field.speed_adjustment_factor": "ตัวคูณปรับความเร็ว (SAF)",
    "field.capacity_adjustment_factor": "ตัวคูณปรับความจุ (CAF)",
    "field.demand_capacity_ratio": "อัตราส่วนความต้องการต่อความจุ",
    "field.segment_length": "ความยาวช่วงถนน",
    "field.lane_width": "ความกว้างช่องจราจร",
    "field.grade_percent": "ความชัน",
    "field.access_point_density": "ความหนาแน่นจุดเข้าออก",
    "enum.measured": "วัดได้",
    "enum.estimated": "ประมาณค่า",
    "enum.external": "ภายนอก",
    "enum.internal": "ภายใน",
    "enum.not_predicted": "ไม่มีการพยากรณ์ค่า",
}

CATALOGS: dict[str, Mapping[str, str]] = {"en": EN, "th": TH}


def normalize_locale(locale: str | None) -> str:
    """Return a supported locale, deterministically falling back to English."""

    return str(locale or DEFAULT_LOCALE).lower() if str(locale or DEFAULT_LOCALE).lower() in CATALOGS else DEFAULT_LOCALE


def translate(key: str, locale: str | None = None, /, **params: Any) -> str:
    """Translate one semantic key with English fallback and named interpolation."""

    active_locale = normalize_locale(locale)
    template = CATALOGS[active_locale].get(key) or EN.get(key)
    if template is None:
        # A user should never see an internal key. English remains the explicit
        # fallback for an unknown noncritical presentation key.
        return key.replace(".", " ").replace("_", " ").capitalize()
    return template.format(**params)


def translation_key_sets() -> dict[str, set[str]]:
    """Expose catalog key sets for deterministic QA without mutable access."""

    return {locale: set(catalog) for locale, catalog in CATALOGS.items()}


def placeholder_names(value: str) -> set[str]:
    """Return named ``str.format`` placeholders used by a translation value."""

    return set(re.findall(r"(?<!\{)\{([a-zA-Z_][a-zA-Z0-9_]*)[^}]*\}", value))


def validate_catalogs() -> list[str]:
    """Return deterministic catalog parity, blank-value, and placeholder errors."""

    errors: list[str] = []
    english_keys = set(EN)
    for locale, catalog in CATALOGS.items():
        missing = english_keys - set(catalog)
        extra = set(catalog) - english_keys
        if missing:
            errors.append(f"{locale}: missing keys: {', '.join(sorted(missing))}")
        if extra:
            errors.append(f"{locale}: extra keys: {', '.join(sorted(extra))}")
        for key in sorted(english_keys & set(catalog)):
            if not catalog[key].strip():
                errors.append(f"{locale}: blank value for {key}")
            if placeholder_names(catalog[key]) != placeholder_names(EN[key]):
                errors.append(f"{locale}: placeholder mismatch for {key}")
    return errors


def field_label(field: str, locale: str | None = None) -> str:
    """Localize known machine field names without ever altering the field itself."""

    key = f"field.{field}"
    if key in EN:
        return translate(key, locale)
    return field.replace("_", " ").strip().title()


def enum_label(value: Any, locale: str | None = None) -> str:
    """Render known canonical enum values while returning the canonical value unchanged."""

    key = f"enum.{value}"
    return translate(key, locale) if key in EN else str(value)


__all__ = [
    "CATALOGS", "DEFAULT_LOCALE", "EN", "SUPPORTED_LOCALES", "TH",
    "enum_label", "field_label", "normalize_locale", "placeholder_names",
    "translate", "translation_key_sets", "validate_catalogs",
]
