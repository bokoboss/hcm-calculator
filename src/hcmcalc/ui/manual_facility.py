"""General ordered Two-Lane facility adapter for the Streamlit worksheet."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
from math import isfinite
from pathlib import Path
from typing import Any

from hcmcalc import __version__
from hcmcalc.cli import find_case, load_input_file
from hcmcalc.core import CalculationResult, HCMCalcError, MethodNotImplementedError
from hcmcalc.methods.two_lane_highway_ch15 import TwoLaneHighwayChapter15Method
from hcmcalc.methods.two_lane_highway_models import PASSING_LANE_ROLE_SEGMENT
from hcmcalc.ui.units import MILES_TO_KILOMETERS


ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = ROOT / "references" / "example_inputs.yaml"
MANUAL_FACILITY_CALCULATION_TYPE = "manual_two_lane_facility_v1"

FACILITY_TEMPLATES = {
    "level_example_3": {
        "label": "Chapter 26 Example 3 starting values",
        "basis": "Example Problem 3",
        "supported_context": (
            "Validated example-based level facility workflow with the selected "
            "segment sequence and passing-lane/downstream context."
        ),
        "safe_edit_summary": (
            "Segment names, lengths, posted speeds, directional volumes, PHF, "
            "and heavy-vehicle percentages."
        ),
        "locked_summary": (
            "Segment types, level terrain, horizontal alignment, passing-lane "
            "placement, and downstream context."
        ),
        "case_id": "TLH-CH15-003",
        "source_reference": "HCM Chapter 26 Two-Lane Highway Example Problem 3",
        "editable_fields": {
            "segment_name",
            "segment_length",
            "posted_speed",
            "analysis_direction_volume_veh_h",
            "opposing_direction_volume_veh_h",
            "peak_hour_factor",
            "heavy_vehicle_percent",
        },
    },
    "mountainous_example_4": {
        "label": "Chapter 26 Example 4 starting values",
        "basis": "Example Problem 4",
        "supported_context": (
            "Validated example-based mountainous facility workflow preserving "
            "the Example Problem 4 curve, grade, passing-lane, and downstream context."
        ),
        "safe_edit_summary": (
            "Segment names, posted speeds, analysis-direction volumes, and PHF."
        ),
        "locked_summary": (
            "Segment lengths and types, opposing volumes, heavy vehicles, grades, "
            "curves, passing-lane placement, and downstream context."
        ),
        "case_id": "TLH-CH15-004",
        "source_reference": "HCM Chapter 26 Two-Lane Highway Example Problem 4",
        "editable_fields": {
            "segment_name",
            "posted_speed",
            "analysis_direction_volume_veh_h",
            "peak_hour_factor",
        },
    },
}


def facility_template_options() -> dict[str, str]:
    """Return stable starting-value identifiers and user-facing labels."""

    return {
        template_id: str(template["label"])
        for template_id, template in FACILITY_TEMPLATES.items()
    }


def clear_manual_facility_result_state(state: Any) -> None:
    """Clear stale facility calculation state after selection or input changes."""

    for key in ("manual_facility_error",):
        state.pop(key, None)


def validate_manual_facility_table(rows: list[dict[str, Any]] | Any) -> dict[str, Any]:
    """Return a compact UI validation summary without running the method."""

    rows = _records(rows)
    if not rows:
        return {
            "status": "missing_required",
            "blocking": True,
            "messages": ["Facility requires at least one segment row."],
        }

    messages: list[str] = []
    segment_ids: set[int] = set()
    required = {
        "segment_id",
        "segment_type",
        "segment_length",
        "posted_speed",
        "analysis_direction_volume_veh_h",
        "peak_hour_factor",
        "heavy_vehicle_percent",
        "grade_percent",
        "horizontal_alignment",
        "lane_width",
        "shoulder_width",
        "access_point_density",
        "passing_lane_role",
    }
    numeric_positive = {"segment_length", "posted_speed", "lane_width"}
    numeric_nonnegative = {
        "analysis_direction_volume_veh_h",
        "heavy_vehicle_percent",
        "grade_percent",
        "shoulder_width",
        "access_point_density",
    }
    allowed_segment_types = {"passing_constrained", "passing_zone", "passing_lane"}
    allowed_roles = {"none", "passing_lane", "downstream_affected"}
    allowed_alignment = {"straight", "horizontal_curves"}
    allowed_terrain = {"level", "mountainous"}

    for index, row in enumerate(rows, start=1):
        segment_label = row.get("segment_id", index)
        missing = sorted(field for field in required if _is_blank(row.get(field)))
        if missing:
            messages.append(
                f"Segment {segment_label}: missing required field(s): {', '.join(missing)}."
            )
        try:
            segment_id = int(row.get("segment_id"))
        except (TypeError, ValueError):
            messages.append(f"Segment row {index}: segment_id must be an integer.")
        else:
            if segment_id in segment_ids:
                messages.append(f"Segment {segment_id}: duplicate segment_id.")
            segment_ids.add(segment_id)
            if segment_id <= 0:
                messages.append(f"Segment {segment_id}: segment_id must be positive.")

        segment_type = str(row.get("segment_type", "")).strip()
        role = str(row.get("passing_lane_role", "")).strip()
        alignment = str(row.get("horizontal_alignment", "")).strip()
        terrain = str(row.get("terrain_type", "")).strip()
        if segment_type and segment_type not in allowed_segment_types:
            messages.append(f"Segment {segment_label}: unsupported segment_type {segment_type}.")
        if role and role not in allowed_roles:
            messages.append(f"Segment {segment_label}: unsupported passing_lane_role {role}.")
        if alignment and alignment not in allowed_alignment:
            messages.append(f"Segment {segment_label}: unsupported horizontal_alignment {alignment}.")
        if terrain and terrain not in allowed_terrain:
            messages.append(f"Segment {segment_label}: unsupported terrain_type {terrain}.")
        if segment_type == "passing_lane" and role != "passing_lane":
            messages.append(
                f"Segment {segment_label}: Passing Lane segment requires passing_lane_role=passing_lane."
            )
        if segment_type != "passing_lane" and role == "passing_lane":
            messages.append(
                f"Segment {segment_label}: only a Passing Lane segment may use passing_lane_role=passing_lane."
            )
        if role == "downstream_affected" and index == 1:
            messages.append(
                f"Segment {segment_label}: downstream_affected requires an upstream Passing Lane segment."
            )
        if segment_type == "passing_zone" and _is_blank(row.get("opposing_direction_volume_veh_h")):
            messages.append(
                f"Segment {segment_label}: passing_zone requires opposing_direction_volume_veh_h."
            )

        for field in numeric_positive:
            _validate_numeric_field(messages, row, segment_label, field, positive=True)
        for field in numeric_nonnegative:
            _validate_numeric_field(messages, row, segment_label, field, positive=False)
        phf = _parse_float(row.get("peak_hour_factor"))
        if phf is None or not 0.0 < phf <= 1.0:
            messages.append(
                f"Segment {segment_label}: peak_hour_factor must be greater than 0 and at most 1."
            )

    if messages:
        status = (
            "missing_required"
            if any("missing required" in message for message in messages)
            else "unsupported_scope"
            if any("unsupported" in message or "Passing Lane" in message for message in messages)
            else "invalid_numeric"
        )
        return {"status": status, "blocking": True, "messages": messages}
    return {
        "status": "valid_table",
        "blocking": False,
        "messages": ["Segment table has the required fields for calculation."],
    }


def load_facility_template(
    template_id: str, unit_system: str = "imperial"
) -> dict[str, Any]:
    """Load an Example 3/4-backed template in user-facing units."""

    template = _template_definition(template_id)
    case = find_case(load_input_file(FIXTURE_PATH), str(template["case_id"]))
    engine_inputs = deepcopy(case["inputs"])
    rows = _engine_segments_to_user_rows(engine_inputs["segments"], unit_system)
    return {
        "template_id": template_id,
        "template_label": template["label"],
        "template_source_reference": template["source_reference"],
        "template_basis": template["basis"],
        "supported_context": template["supported_context"],
        "safe_edit_summary": template["safe_edit_summary"],
        "locked_summary": template["locked_summary"],
        "unit_system": _normalize_unit_system(unit_system),
        "segments": rows,
        "editable_fields": sorted(template["editable_fields"]),
        "unsupported_behavior_notes": _unsupported_behavior_notes(),
    }


def run_manual_facility(
    template_id: str,
    rows: list[dict[str, Any]],
    unit_system: str = "imperial",
) -> CalculationResult:
    """Validate an editable facility worksheet and delegate to the general engine."""

    engine_inputs = build_manual_facility_inputs(template_id, rows, unit_system)
    return TwoLaneHighwayChapter15Method().calculate_facility(engine_inputs)


def build_manual_facility_inputs(
    template_id: str,
    rows: list[dict[str, Any]],
    unit_system: str = "imperial",
) -> dict[str, Any]:
    """Normalize visible worksheet values into the general facility schema.

    ``template_id`` selects starting values only; it never supplies hidden
    calculation context after the rows have been loaded.
    """

    template = _template_definition(template_id)
    unit_system = _normalize_unit_system(unit_system)
    rows = _records(rows)
    if not rows:
        raise HCMCalcError("Facility requires at least one segment row.")
    normalized_segments: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise HCMCalcError(f"Facility segment row {index} must be an object.")
        required = {"segment_id", "segment_type", "segment_length", "posted_speed", "analysis_direction_volume_veh_h", "peak_hour_factor", "heavy_vehicle_percent", "grade_percent", "horizontal_alignment", "lane_width", "shoulder_width", "access_point_density"}
        missing = sorted(field for field in required if row.get(field) is None)
        if missing:
            raise HCMCalcError(f"Facility segment {row.get('segment_id', index)} requires {', '.join(missing)}.")
        try:
            normalized = {
                "segment_id": int(row["segment_id"]), "segment_type": str(row["segment_type"]),
                "segment_length_mi": float(row["segment_length"]) / (MILES_TO_KILOMETERS if unit_system == "metric" else 1.0),
                "posted_speed_mph": float(row["posted_speed"]) / (MILES_TO_KILOMETERS if unit_system == "metric" else 1.0),
                "analysis_direction_volume_veh_h": float(row["analysis_direction_volume_veh_h"]),
                "peak_hour_factor": float(row["peak_hour_factor"]), "heavy_vehicle_percent": float(row["heavy_vehicle_percent"]),
                "grade_percent": float(row["grade_percent"]), "horizontal_alignment": str(row["horizontal_alignment"]),
                "lane_width_ft": float(row["lane_width"]) / (3.280839895 if unit_system == "metric" else 1.0),
                "shoulder_width_ft": float(row["shoulder_width"]) / (3.280839895 if unit_system == "metric" else 1.0),
                "access_point_density_per_mi": float(row["access_point_density"]) * (MILES_TO_KILOMETERS if unit_system == "metric" else 1.0),
                "passing_lane_role": str(row.get("passing_lane_role", PASSING_LANE_ROLE_SEGMENT if row["segment_type"] == "passing_lane" else "none")),
                "horizontal_alignment_subsegments": row.get("horizontal_alignment_subsegments", []),
            }
        except (TypeError, ValueError) as exc:
            raise HCMCalcError(f"Facility segment {row.get('segment_id', index)} has invalid numeric input.") from exc
        if row.get("opposing_direction_volume_veh_h") not in (None, ""):
            normalized["opposing_direction_volume_veh_h"] = float(row["opposing_direction_volume_veh_h"])
        normalized_segments.append(normalized)
    return {
        "facility_id": template_id,
        "facility_length_mi": sum(float(segment["segment_length_mi"]) for segment in normalized_segments),
        "segments": normalized_segments,
        # Published presets intentionally retain their documented displayed
        # one-decimal aggregation convention; generic facilities omit this.
        "published_display_density_rounding_decimals": 1 if template_id in FACILITY_TEMPLATES else None,
    }


def facility_segment_result_rows(
    result: CalculationResult, user_rows: list[dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    """Return compact facility segment results for the UI table."""

    rows = []
    names = {
        row["segment_id"]: row.get("segment_name")
        for row in user_rows or []
        if row.get("segment_id") is not None
    }
    for segment in result.outputs["segments"]:
        rows.append(
            {
                "segment_id": segment["segment_id"],
                "segment_name": names.get(segment["segment_id"]),
                "segment_type": segment["segment_type"],
                "segment_length_mi": segment["segment_length_mi"],
                "average_speed_mph": segment["average_speed_mph"],
                "percent_followers": segment["percent_followers"],
                "follower_density_followers_mi_ln": segment[
                    "follower_density_followers_mi_ln"
                ],
                "level_of_service": segment["level_of_service"],
                "vertical_class": segment["vertical_class"],
                "horizontal_curve_adjustment_applied": segment[
                    "horizontal_curve_adjustment_applied"
                ],
                "passing_lane": segment["segment_type"] == "passing_lane",
                "downstream_adjustment_applied": segment.get(
                    "downstream_adjustment_applied", False
                ),
                "key_warnings": _segment_warning(segment),
            }
        )
    return rows


def build_manual_facility_audit_record(
    template_id: str,
    rows: list[dict[str, Any]],
    unit_system: str,
    *,
    result: CalculationResult | None = None,
    error: HCMCalcError | None = None,
) -> dict[str, Any]:
    """Build a JSON-ready audit record for a facility submission."""

    template = _template_definition(template_id)
    rows = _records(rows)
    try:
        normalized_inputs = build_manual_facility_inputs(template_id, rows, unit_system)
    except HCMCalcError:
        normalized_inputs = {}
    result_data = asdict(result) if result is not None else {}
    return {
        "calculation_type": MANUAL_FACILITY_CALCULATION_TYPE,
        "template_id": template_id,
        "template_source_reference": template["source_reference"],
        "unit_system": _normalize_unit_system(unit_system),
        "facility_inputs": {"segments": deepcopy(rows)},
        "normalized_segment_inputs": normalized_inputs.get("segments", []),
        "segment_outputs": result_data.get("outputs", {}).get("segments", []),
        "facility_outputs": {
            key: value
            for key, value in result_data.get("outputs", {}).items()
            if key != "segments"
        },
        "warnings": result_data.get("warnings", []),
        "assumptions": result_data.get("assumptions", []),
        "unsupported_behavior_notes": _unsupported_behavior_notes(),
        "calculation_status": (
            "succeeded" if result is not None else "failed" if error is not None else "not_run"
        ),
        "error_type": type(error).__name__ if error is not None else None,
        "error_message": str(error) if error is not None else None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "app_version": __version__,
    }


def _engine_segments_to_user_rows(
    segments: list[dict[str, Any]], unit_system: str
) -> list[dict[str, Any]]:
    unit_system = _normalize_unit_system(unit_system)
    metric = unit_system == "metric"
    rows = []
    passing_lane_seen = False
    for segment in segments:
        is_passing_lane = segment["segment_type"] == "passing_lane"
        rows.append(
            {
                "segment_id": segment["segment_id"],
                "segment_name": f"Segment {segment['segment_id']}",
                "segment_type": segment["segment_type"],
                "segment_length": float(segment["segment_length_mi"])
                * (MILES_TO_KILOMETERS if metric else 1.0),
                "posted_speed": float(segment["posted_speed_mph"])
                * (MILES_TO_KILOMETERS if metric else 1.0),
                "analysis_direction_volume_veh_h": segment[
                    "analysis_direction_volume_veh_h"
                ],
                "opposing_direction_volume_veh_h": segment.get(
                    "opposing_direction_volume_veh_h"
                ),
                "peak_hour_factor": segment["peak_hour_factor"],
                "heavy_vehicle_percent": segment["heavy_vehicle_percent"],
                "terrain_type": "level"
                if float(segment["grade_percent"]) == 0.0
                else "mountainous",
                "grade_percent": segment["grade_percent"],
                "horizontal_alignment": segment["horizontal_alignment"],
                "lane_width": float(segment["lane_width_ft"]) * (3.280839895 if metric else 1.0),
                "shoulder_width": float(segment["shoulder_width_ft"]) * (3.280839895 if metric else 1.0),
                "access_point_density": float(segment["access_point_density_per_mi"]) / (MILES_TO_KILOMETERS if metric else 1.0),
                "horizontal_alignment_subsegments": segment.get("horizontal_alignment_subsegments", []),
                "passing_lane_role": "passing_lane" if is_passing_lane else ("downstream_affected" if passing_lane_seen else "none"),
                "passing_lane": is_passing_lane,
                "downstream_affected": passing_lane_seen and not is_passing_lane,
            }
        )
        passing_lane_seen = passing_lane_seen or is_passing_lane
    return rows


def _validate_locked_context(
    row: dict[str, Any],
    source_row: dict[str, Any],
    editable_fields: set[str],
    index: int,
) -> None:
    for field, value in source_row.items():
        if field not in editable_fields and row.get(field) != value:
            raise MethodNotImplementedError(
                "Unsupported combination: "
                f"{field} is locked by the selected facility template at segment {index}."
            )
    if "manual_downstream_adjustment" in row:
        raise MethodNotImplementedError(
            "Unsupported combination: manual downstream adjustment is not available. "
            "Downstream context is derived from the selected validated template."
        )


def _apply_editable_values(
    normalized: dict[str, Any],
    row: dict[str, Any],
    editable_fields: set[str],
    unit_system: str,
    index: int,
) -> None:
    field_map = {
        "segment_length": "segment_length_mi",
        "posted_speed": "posted_speed_mph",
        "analysis_direction_volume_veh_h": "analysis_direction_volume_veh_h",
        "opposing_direction_volume_veh_h": "opposing_direction_volume_veh_h",
        "peak_hour_factor": "peak_hour_factor",
        "heavy_vehicle_percent": "heavy_vehicle_percent",
    }
    for user_field, engine_field in field_map.items():
        if user_field not in editable_fields:
            continue
        value = row.get(user_field)
        if value is None:
            if engine_field == "opposing_direction_volume_veh_h":
                normalized.pop(engine_field, None)
                continue
            raise HCMCalcError(f"Facility segment {index} requires {user_field}.")
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise HCMCalcError(
                f"Facility segment {index} {user_field} must be numeric."
            ) from exc
        if unit_system == "metric" and user_field in {"segment_length", "posted_speed"}:
            numeric /= MILES_TO_KILOMETERS
        normalized[engine_field] = numeric


def _template_definition(template_id: str) -> dict[str, Any]:
    try:
        return FACILITY_TEMPLATES[template_id]
    except KeyError as exc:
        raise MethodNotImplementedError(
            "Unsupported combination: select a validated Example 3 or Example 4 "
            "facility template."
        ) from exc


def _normalize_unit_system(unit_system: str) -> str:
    normalized = str(unit_system).strip().lower()
    if normalized not in {"metric", "imperial"}:
        raise HCMCalcError("unit_system must be metric or imperial.")
    return normalized


def _records(rows: Any) -> list[dict[str, Any]]:
    if hasattr(rows, "to_dict"):
        rows = rows.to_dict(orient="records")
    if not isinstance(rows, list):
        raise HCMCalcError("Facility segment table must contain a list of rows.")
    return [dict(row) if isinstance(row, dict) else row for row in rows]


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _parse_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if isfinite(parsed) else None


def _validate_numeric_field(
    messages: list[str],
    row: dict[str, Any],
    segment_label: Any,
    field: str,
    *,
    positive: bool,
) -> None:
    value = _parse_float(row.get(field))
    if value is None:
        messages.append(f"Segment {segment_label}: {field} must be numeric.")
    elif positive and value <= 0.0:
        messages.append(f"Segment {segment_label}: {field} must be greater than 0.")
    elif not positive and value < 0.0:
        messages.append(f"Segment {segment_label}: {field} must be 0 or greater.")


def _segment_warning(segment: dict[str, Any]) -> str:
    warnings = []
    if segment["horizontal_curve_adjustment_applied"]:
        warnings.append("Validated-template horizontal curve")
    if segment["segment_type"] == "passing_lane":
        warnings.append("Passing-lane midpoint density")
    if segment.get("downstream_adjustment_applied"):
        warnings.append("Downstream passing-lane adjustment")
    return "; ".join(warnings)


def _unsupported_behavior_notes() -> list[str]:
    return [
        "This does not represent full general Chapter 15 facility support.",
        "Arbitrary segment sequences and arbitrary nonlevel facilities are unsupported.",
        "Arbitrary horizontal curve and nonlevel combinations are unsupported.",
        "Passing-lane placement and downstream adjustment context are template-controlled.",
    ]
