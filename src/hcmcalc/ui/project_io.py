"""Save and load helpers for guarded manual project files."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from hcmcalc import __version__
from hcmcalc.core import HCMCalcError
from hcmcalc.ui.curve_editor import validate_curve_setup
from hcmcalc.ui.manual_facility import (
    FACILITY_TEMPLATES,
    build_manual_facility_inputs,
    load_facility_template,
)
from hcmcalc.ui.manual_freeway import (
    MANUAL_FREEWAY_LIMITATIONS,
    PRESET_LABELS,
    freeway_display_outputs,
    freeway_ui_inputs_to_engine,
    load_freeway_preset,
    run_manual_freeway,
)
from hcmcalc.ui.manual_multilane import (
    MANUAL_MULTILANE_LIMITATIONS,
    TEMPLATE_LABELS,
    load_multilane_template,
    multilane_display_outputs,
    multilane_ui_inputs_to_engine,
    run_manual_multilane,
)
from hcmcalc.ui.manual_segment import build_manual_segment_inputs
from hcmcalc.ui.workflow_state import normalized_input_fingerprint


PROJECT_SCHEMA_VERSION = "1.0"
MANUAL_SINGLE_SEGMENT_PROJECT_TYPE = "manual_single_segment"
MANUAL_FACILITY_PROJECT_TYPE = "manual_two_lane_facility_v1"
LEGACY_MANUAL_FACILITY_PROJECT_TYPE = "manual_facility_v0"
MANUAL_MULTILANE_PROJECT_TYPE = "manual_multilane_v0"
MANUAL_BASIC_FREEWAY_PROJECT_TYPE = "manual_basic_freeway_v0"
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
        "calculation_fingerprint": (
            normalized_input_fingerprint(normalized_engine_inputs)
            if normalized_engine_inputs is not None
            else None
        ),
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

    payload = _load_project_document(data)
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
    normalized_inputs = build_manual_segment_inputs(manual_inputs)
    _discard_stale_single_segment_result(payload, normalized_inputs)
    return payload


def create_manual_facility_project_payload(
    template_id: str,
    unit_system: str,
    segment_rows: list[dict[str, Any]],
    *,
    result: dict[str, Any] | None = None,
    audit_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a JSON-ready guarded manual facility project payload."""

    template = load_facility_template(template_id, unit_system)
    segment_rows = _json_ready(segment_rows)
    normalized_inputs = build_manual_facility_inputs(
        template_id, segment_rows, unit_system
    )
    result = _json_ready(result) if result is not None else None
    audit_record = _json_ready(audit_record) if audit_record is not None else None
    outputs = result.get("outputs", {}) if result else {}
    fingerprint = normalized_input_fingerprint(normalized_inputs)
    return {
        "schema_version": PROJECT_SCHEMA_VERSION,
        "project_type": MANUAL_FACILITY_PROJECT_TYPE,
        "generated_by": f"hcm-calculator {__version__}",
        "app_version": __version__,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "unit_system": template["unit_system"],
        "template_id": template_id,
        "template_name": template["template_label"],
        "editable_facility_inputs": {"segments": segment_rows},
        "normalized_facility_inputs": normalized_inputs,
        "calculation_fingerprint": fingerprint,
        "segment_rows": segment_rows,
        "calculation_result": result,
        "facility_outputs": {key: value for key, value in outputs.items() if key != "segments"},
        "segment_outputs": outputs.get("segments", []),
        "audit": audit_record,
        "warnings": _calculation_context("warnings", result, audit_record),
        "assumptions": _calculation_context("assumptions", result, audit_record),
        "unsupported_behavior_notes": template["unsupported_behavior_notes"],
    }


def create_manual_facility_project_json(
    template_id: str,
    unit_system: str,
    segment_rows: list[dict[str, Any]],
    *,
    result: dict[str, Any] | None = None,
    audit_record: dict[str, Any] | None = None,
) -> str:
    """Create formatted JSON for a guarded manual facility project."""

    return json.dumps(
        create_manual_facility_project_payload(
            template_id,
            unit_system,
            segment_rows,
            result=result,
            audit_record=audit_record,
        ),
        indent=2,
    )


def load_manual_facility_project_json(data: str | bytes) -> dict[str, Any]:
    """Parse and validate a guarded manual facility project JSON document."""

    payload = _load_project_document(data)
    if payload.get("project_type") not in {MANUAL_FACILITY_PROJECT_TYPE, LEGACY_MANUAL_FACILITY_PROJECT_TYPE}:
        raise ProjectFileError("Wrong project_type. Expected manual_two_lane_facility_v1 or manual_facility_v0.")
    if "template_id" not in payload:
        raise ProjectFileError("Missing required field: template_id.")
    if payload["template_id"] not in FACILITY_TEMPLATES:
        raise ProjectFileError(f"Unknown template_id: {payload['template_id']}.")
    if "unit_system" not in payload:
        raise ProjectFileError("Missing required field: unit_system.")
    if payload["unit_system"] not in {"metric", "imperial"}:
        raise ProjectFileError("unit_system must be metric or imperial.")
    if "segment_rows" not in payload:
        raise ProjectFileError("Missing required field: segment_rows.")
    if not isinstance(payload["segment_rows"], list):
        raise ProjectFileError("Malformed segment rows: expected a list.")
    try:
        normalized_inputs = build_manual_facility_inputs(
            payload["template_id"], payload["segment_rows"], payload["unit_system"]
        )
    except HCMCalcError as exc:
        raise ProjectFileError(f"Malformed or unsupported segment rows: {exc}") from exc
    _discard_stale_facility_result(payload, normalized_inputs)
    return payload


def create_manual_multilane_project_payload(
    template_id: str,
    unit_system: str,
    displayed_inputs: dict[str, Any],
    *,
    result: dict[str, Any] | None = None,
    audit_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a JSON-ready guarded Manual Multilane project payload."""

    template = load_multilane_template(template_id)
    unit_system = _validate_multilane_unit_system(unit_system)
    displayed_inputs = _json_ready(displayed_inputs)
    normalized_inputs = _build_multilane_inputs(
        template_id, unit_system, displayed_inputs
    )
    try:
        run_manual_multilane(normalized_inputs)
    except HCMCalcError as exc:
        raise ProjectFileError(f"Malformed or unsupported input payload: {exc}") from exc
    result = _json_ready(result) if result is not None else None
    audit_record = _json_ready(audit_record) if audit_record is not None else None
    outputs = result.get("outputs", {}) if result else {}
    return {
        "schema_version": PROJECT_SCHEMA_VERSION,
        "project_type": MANUAL_MULTILANE_PROJECT_TYPE,
        "generated_by": f"hcm-calculator {__version__}",
        "app_version": __version__,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "unit_system": unit_system,
        "template_id": template_id,
        "template_name": template["template_label"],
        "direction": template["inputs"]["direction"],
        "displayed_ui_inputs": displayed_inputs,
        "normalized_engine_inputs": normalized_inputs,
        "calculation_result": result,
        "display_result": (
            multilane_display_outputs(outputs, unit_system) if outputs else None
        ),
        "audit": audit_record,
        "warnings": _calculation_context("warnings", result, audit_record),
        "assumptions": _calculation_context("assumptions", result, audit_record),
        "limitations": list(MANUAL_MULTILANE_LIMITATIONS),
        "unsupported_behavior_notes": list(MANUAL_MULTILANE_LIMITATIONS),
    }


def create_manual_multilane_project_json(
    template_id: str,
    unit_system: str,
    displayed_inputs: dict[str, Any],
    *,
    result: dict[str, Any] | None = None,
    audit_record: dict[str, Any] | None = None,
) -> str:
    """Create formatted JSON for a guarded Manual Multilane project."""

    return json.dumps(
        create_manual_multilane_project_payload(
            template_id,
            unit_system,
            displayed_inputs,
            result=result,
            audit_record=audit_record,
        ),
        indent=2,
    )


def load_manual_multilane_project_json(data: str | bytes) -> dict[str, Any]:
    """Parse and validate a guarded Manual Multilane project JSON document."""

    payload = _load_project_document(data)
    if payload.get("project_type") != MANUAL_MULTILANE_PROJECT_TYPE:
        raise ProjectFileError("Wrong project_type. Expected manual_multilane_v0.")
    if "unit_system" not in payload:
        raise ProjectFileError("Missing required field: unit_system.")
    unit_system = _validate_multilane_unit_system(payload["unit_system"])
    if "template_id" not in payload:
        raise ProjectFileError("Missing required field: template_id.")
    template_id = payload["template_id"]
    if template_id not in TEMPLATE_LABELS:
        raise ProjectFileError(f"Unknown template_id: {template_id}.")
    displayed_inputs = payload.get("displayed_ui_inputs")
    if not isinstance(displayed_inputs, dict):
        raise ProjectFileError(
            "Malformed input payload: displayed_ui_inputs must be an object."
        )
    saved_normalized_inputs = payload.get("normalized_engine_inputs")
    normalized_inputs = _build_multilane_inputs(
        template_id, unit_system, displayed_inputs
    )
    try:
        run_manual_multilane(normalized_inputs)
    except HCMCalcError as exc:
        raise ProjectFileError(f"Malformed or unsupported input payload: {exc}") from exc
    payload["normalized_engine_inputs"] = normalized_inputs
    if saved_normalized_inputs != normalized_inputs:
        payload["calculation_result"] = None
        payload["display_result"] = None
        payload["audit"] = None
    return payload


def create_manual_freeway_project_payload(
    preset_id: str,
    unit_system: str,
    displayed_inputs: dict[str, Any],
    *,
    result: dict[str, Any] | None = None,
    audit_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a JSON-ready bounded Manual Basic Freeway project payload."""

    preset = load_freeway_preset(preset_id)
    unit_system = _validate_unit_system(unit_system)
    displayed_inputs = _json_ready(displayed_inputs)
    normalized_inputs = _build_freeway_inputs(preset_id, unit_system, displayed_inputs)
    try:
        run_manual_freeway(normalized_inputs)
    except HCMCalcError as exc:
        raise ProjectFileError(f"Malformed or unsupported input payload: {exc}") from exc
    result = _json_ready(result) if result is not None else None
    audit_record = _json_ready(audit_record) if audit_record is not None else None
    outputs = result.get("outputs", {}) if result else {}
    return {
        "schema_version": PROJECT_SCHEMA_VERSION,
        "project_type": MANUAL_BASIC_FREEWAY_PROJECT_TYPE,
        "generated_by": f"hcm-calculator {__version__}",
        "app_version": __version__,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "unit_system": unit_system,
        "preset_id": preset_id,
        "preset_name": preset["preset_label"],
        "displayed_ui_inputs": displayed_inputs,
        "normalized_engine_inputs": normalized_inputs,
        "calculation_result": result,
        "display_result": (
            freeway_display_outputs(outputs, unit_system) if outputs else None
        ),
        "audit": audit_record,
        "warnings": _calculation_context("warnings", result, audit_record),
        "assumptions": _calculation_context("assumptions", result, audit_record),
        "limitations": list(MANUAL_FREEWAY_LIMITATIONS),
        "unsupported_behavior_notes": list(MANUAL_FREEWAY_LIMITATIONS),
    }


def create_manual_freeway_project_json(
    preset_id: str,
    unit_system: str,
    displayed_inputs: dict[str, Any],
    *,
    result: dict[str, Any] | None = None,
    audit_record: dict[str, Any] | None = None,
) -> str:
    """Create formatted JSON for a bounded Manual Basic Freeway project."""

    return json.dumps(
        create_manual_freeway_project_payload(
            preset_id,
            unit_system,
            displayed_inputs,
            result=result,
            audit_record=audit_record,
        ),
        indent=2,
    )


def load_manual_freeway_project_json(data: str | bytes) -> dict[str, Any]:
    """Parse and validate a bounded Manual Basic Freeway project JSON document."""

    payload = _load_project_document(data)
    if payload.get("project_type") != MANUAL_BASIC_FREEWAY_PROJECT_TYPE:
        raise ProjectFileError(
            "Wrong project_type. Expected manual_basic_freeway_v0."
        )
    if "unit_system" not in payload:
        raise ProjectFileError("Missing required field: unit_system.")
    unit_system = _validate_unit_system(payload["unit_system"])
    if "preset_id" not in payload:
        raise ProjectFileError("Missing required field: preset_id.")
    preset_id = payload["preset_id"]
    if preset_id not in PRESET_LABELS:
        raise ProjectFileError(f"Unknown preset_id: {preset_id}.")
    displayed_inputs = payload.get("displayed_ui_inputs")
    if not isinstance(displayed_inputs, dict):
        raise ProjectFileError(
            "Malformed input payload: displayed_ui_inputs must be an object."
        )
    saved_normalized_inputs = payload.get("normalized_engine_inputs")
    normalized_inputs = _build_freeway_inputs(preset_id, unit_system, displayed_inputs)
    try:
        run_manual_freeway(normalized_inputs)
    except HCMCalcError as exc:
        raise ProjectFileError(f"Malformed or unsupported input payload: {exc}") from exc
    payload["normalized_engine_inputs"] = normalized_inputs
    if saved_normalized_inputs != normalized_inputs:
        payload["calculation_result"] = None
        payload["display_result"] = None
        payload["audit"] = None
    return payload


def _load_project_document(data: str | bytes) -> dict[str, Any]:
    try:
        payload = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ProjectFileError("Invalid JSON project file.") from exc
    if not isinstance(payload, dict):
        raise ProjectFileError("Project JSON must contain an object.")
    if "project_type" not in payload:
        raise ProjectFileError("Missing required field: project_type.")
    if payload.get("schema_version") != PROJECT_SCHEMA_VERSION:
        raise ProjectFileError(
            f"Unsupported schema_version. Expected {PROJECT_SCHEMA_VERSION}."
        )
    return payload


def _validate_multilane_unit_system(unit_system: Any) -> str:
    return _validate_unit_system(unit_system)


def _validate_unit_system(unit_system: Any) -> str:
    normalized = str(unit_system).strip().lower()
    if normalized not in {"metric", "imperial"}:
        raise ProjectFileError("unit_system must be metric or imperial.")
    return normalized


def _build_multilane_inputs(
    template_id: str, unit_system: str, displayed_inputs: dict[str, Any]
) -> dict[str, Any]:
    try:
        template_inputs = load_multilane_template(template_id)["inputs"]
        return multilane_ui_inputs_to_engine(
            displayed_inputs, template_inputs, unit_system
        )
    except (HCMCalcError, KeyError, TypeError, ValueError) as exc:
        raise ProjectFileError(f"Malformed input payload: {exc}") from exc


def _build_freeway_inputs(
    preset_id: str, unit_system: str, displayed_inputs: dict[str, Any]
) -> dict[str, Any]:
    try:
        preset_inputs = load_freeway_preset(preset_id)["inputs"]
        return freeway_ui_inputs_to_engine(displayed_inputs, preset_inputs, unit_system)
    except (HCMCalcError, KeyError, TypeError, ValueError) as exc:
        raise ProjectFileError(f"Malformed input payload: {exc}") from exc


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


def _discard_stale_single_segment_result(
    payload: dict[str, Any], normalized_inputs: dict[str, Any]
) -> None:
    """Never restore a result unless its normalized-input fingerprint matches."""

    saved_fingerprint = payload.get("calculation_fingerprint")
    current_fingerprint = normalized_input_fingerprint(normalized_inputs)
    payload["normalized_engine_inputs"] = normalized_inputs
    if saved_fingerprint == current_fingerprint:
        return
    payload["result"] = None
    payload["audit_record"] = None
    payload["warnings"] = []
    payload["assumptions"] = []


def _discard_stale_facility_result(
    payload: dict[str, Any], normalized_inputs: dict[str, Any]
) -> None:
    """Discard stale or legacy stored facility results while retaining inputs."""

    saved_fingerprint = payload.get("calculation_fingerprint")
    current_fingerprint = normalized_input_fingerprint(normalized_inputs)
    payload["normalized_facility_inputs"] = normalized_inputs
    payload["calculation_fingerprint"] = current_fingerprint
    if saved_fingerprint == current_fingerprint:
        return
    payload["calculation_result"] = None
    payload["facility_outputs"] = {}
    payload["segment_outputs"] = []
    payload["audit"] = None
    payload["warnings"] = []
    payload["assumptions"] = []


def _json_ready(value: Any) -> Any:
    return json.loads(json.dumps(value, default=_json_default))


def _json_default(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict(orient="records")
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"{type(value).__name__} is not JSON serializable")
