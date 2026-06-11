"""Save and load helpers for manual single-segment project files."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from hcmcalc import __version__
from hcmcalc.core import HCMCalcError
from hcmcalc.ui.curve_editor import validate_curve_setup
from hcmcalc.ui.manual_segment import build_manual_segment_inputs


PROJECT_SCHEMA_VERSION = "1.0"
MANUAL_SINGLE_SEGMENT_PROJECT_TYPE = "manual_single_segment"
REQUIRED_MANUAL_INPUTS = {
    "segment_type",
    "terrain_type",
    "horizontal_alignment",
    "segment_length",
    "posted_speed",
    "lane_width",
    "shoulder_width",
    "access_point_density",
    "analysis_direction_volume",
    "peak_hour_factor",
    "heavy_vehicle_percent",
}


class ProjectFileError(ValueError):
    """Raised when a manual project file cannot be loaded safely."""


def create_manual_project_payload(
    manual_inputs: dict[str, Any],
    *,
    result: dict[str, Any] | None = None,
    audit_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a JSON-ready manual single-segment project payload."""

    manual_inputs = _json_ready(manual_inputs)
    audit_record = _json_ready(audit_record) if audit_record is not None else None
    result = _json_ready(result) if result is not None else None

    normalized_engine_inputs = None
    if audit_record:
        normalized_engine_inputs = audit_record.get("normalized_engine_inputs")
    if normalized_engine_inputs is None:
        try:
            normalized_engine_inputs = build_manual_segment_inputs(manual_inputs)
        except HCMCalcError:
            normalized_engine_inputs = None

    warnings = _calculation_context("warnings", result, audit_record)
    assumptions = _calculation_context("assumptions", result, audit_record)
    return {
        "schema_version": PROJECT_SCHEMA_VERSION,
        "project_type": MANUAL_SINGLE_SEGMENT_PROJECT_TYPE,
        "generated_by": f"hcm-calculator {__version__}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "unit_system": manual_inputs.get("unit_system"),
        "manual_inputs": manual_inputs,
        "normalized_engine_inputs": normalized_engine_inputs,
        "result": result,
        "audit_record": audit_record,
        "warnings": warnings,
        "assumptions": assumptions,
    }


def create_manual_project_json(
    manual_inputs: dict[str, Any],
    *,
    result: dict[str, Any] | None = None,
    audit_record: dict[str, Any] | None = None,
) -> str:
    """Create formatted JSON for a manual single-segment project."""

    return json.dumps(
        create_manual_project_payload(
            manual_inputs, result=result, audit_record=audit_record
        ),
        indent=2,
    )


def load_manual_project_json(data: str | bytes) -> dict[str, Any]:
    """Parse and validate a manual single-segment project JSON document."""

    try:
        payload = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ProjectFileError("Invalid JSON project file.") from exc

    if not isinstance(payload, dict):
        raise ProjectFileError("Project JSON must contain an object.")
    if payload.get("schema_version") != PROJECT_SCHEMA_VERSION:
        raise ProjectFileError(
            f"Unsupported schema_version. Expected {PROJECT_SCHEMA_VERSION}."
        )
    if payload.get("project_type") != MANUAL_SINGLE_SEGMENT_PROJECT_TYPE:
        raise ProjectFileError(
            "Wrong project_type. Expected manual_single_segment."
        )
    if "unit_system" not in payload or "manual_inputs" not in payload:
        raise ProjectFileError(
            "Missing required fields: unit_system and manual_inputs are required."
        )
    if payload["unit_system"] not in {"metric", "imperial"}:
        raise ProjectFileError("unit_system must be metric or imperial.")
    if not isinstance(payload["manual_inputs"], dict):
        raise ProjectFileError("manual_inputs must be an object.")

    manual_inputs = payload["manual_inputs"]
    missing = sorted(REQUIRED_MANUAL_INPUTS - manual_inputs.keys())
    if missing:
        raise ProjectFileError(
            f"Missing required manual_inputs fields: {', '.join(missing)}."
        )
    if manual_inputs.get("unit_system", payload["unit_system"]) != payload["unit_system"]:
        raise ProjectFileError("manual_inputs unit_system must match unit_system.")
    _validate_manual_inputs(manual_inputs)
    return payload


def _validate_manual_inputs(manual_inputs: dict[str, Any]) -> None:
    if manual_inputs["segment_type"] not in {
        "passing_constrained",
        "passing_zone",
        "passing_lane",
    }:
        raise ProjectFileError("manual_inputs segment_type is invalid.")
    if manual_inputs["terrain_type"] not in {"level", "mountainous"}:
        raise ProjectFileError("manual_inputs terrain_type is invalid.")
    if manual_inputs["horizontal_alignment"] not in {
        "straight",
        "horizontal_curves",
    }:
        raise ProjectFileError("manual_inputs horizontal_alignment is invalid.")
    if (
        manual_inputs["segment_type"] == "passing_zone"
        and manual_inputs.get("opposing_direction_volume") is None
    ):
        raise ProjectFileError(
            "Missing required manual_inputs field: opposing_direction_volume."
        )
    if (
        manual_inputs["terrain_type"] == "mountainous"
        and manual_inputs.get("grade_percent") is None
    ):
        raise ProjectFileError("Missing required manual_inputs field: grade_percent.")

    subsegments = manual_inputs.get("horizontal_alignment_subsegments", [])
    if manual_inputs["horizontal_alignment"] == "horizontal_curves":
        curve_setup = manual_inputs.get("curve_setup")
        if curve_setup is not None:
            try:
                validate_curve_setup(curve_setup)
            except HCMCalcError as exc:
                raise ProjectFileError(f"Malformed curve_setup: {exc}") from exc
        _validate_horizontal_subsegments(subsegments)
    elif subsegments is not None and not isinstance(subsegments, list):
        raise ProjectFileError("Malformed horizontal curve subsegments: expected a list.")


def _validate_horizontal_subsegments(subsegments: Any) -> None:
    if not isinstance(subsegments, list) or not subsegments:
        raise ProjectFileError(
            "Malformed horizontal curve subsegments: expected a non-empty list."
        )
    for index, subsegment in enumerate(subsegments, start=1):
        if not isinstance(subsegment, dict):
            raise ProjectFileError(
                f"Malformed horizontal curve subsegment {index}: expected an object."
            )
        subsegment_type = subsegment.get("type")
        if subsegment_type not in {"tangent", "horizontal_curve"}:
            raise ProjectFileError(
                f"Malformed horizontal curve subsegment {index}: invalid type."
            )
        required = {"length"}
        if subsegment_type == "horizontal_curve":
            required.update(
                {
                    "superelevation_percent",
                    "radius",
                    "central_angle_deg",
                    "horizontal_class",
                }
            )
        missing = sorted(
            field for field in required if subsegment.get(field) is None
        )
        if missing:
            raise ProjectFileError(
                f"Malformed horizontal curve subsegment {index}: missing "
                f"{', '.join(missing)}."
            )
        for field in required - {"type"}:
            try:
                float(subsegment[field])
            except (TypeError, ValueError) as exc:
                raise ProjectFileError(
                    f"Malformed horizontal curve subsegment {index}: "
                    f"{field} must be numeric."
                ) from exc


def _calculation_context(
    name: str,
    result: dict[str, Any] | None,
    audit_record: dict[str, Any] | None,
) -> list[Any]:
    if result is not None:
        return list(result.get(name, []))
    if audit_record is not None:
        return list(audit_record.get(name, []))
    return []


def _json_ready(value: Any) -> Any:
    return json.loads(json.dumps(value, default=_json_default))


def _json_default(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict(orient="records")
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"{type(value).__name__} is not JSON serializable")
