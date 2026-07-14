"""Audit records for manual UI calculations."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from hcmcalc.core import (
    CalculationResult,
    HCMCalcError,
    MethodNotImplementedError,
    UnsupportedScopeError,
)
from hcmcalc.ui.manual_segment import build_manual_segment_inputs
from hcmcalc.ui.units import DEFAULT_UNIT_SYSTEM


MANUAL_AUDIT_SCHEMA_VERSION = "1.0"


def build_manual_calculation_audit_record(
    user_inputs: dict[str, Any],
    *,
    result: CalculationResult | None = None,
    error: HCMCalcError | None = None,
) -> dict[str, Any]:
    """Build a JSON-ready record of a manual single-segment submission."""

    try:
        normalized_engine_inputs = build_manual_segment_inputs(user_inputs)
    except HCMCalcError:
        normalized_engine_inputs = {}

    if result is not None:
        result_data = asdict(result)
        scope_status = "supported"
        calculation_status = "succeeded"
    elif error is not None:
        result_data = {}
        scope_status = (
            error.scope_status
            if isinstance(error, UnsupportedScopeError)
            else "unsupported"
            if isinstance(error, MethodNotImplementedError)
            else "invalid"
        )
        calculation_status = "failed"
    else:
        result_data = {}
        scope_status = "not_evaluated"
        calculation_status = "not_run"

    unsupported_reason = (
        error.unsupported_reason
        if isinstance(error, UnsupportedScopeError)
        else str(error)
        if isinstance(error, MethodNotImplementedError)
        else None
    )
    error_context = error.context if isinstance(error, UnsupportedScopeError) else {}
    supported_scope_status = (
        "supported"
        if scope_status == "supported"
        else "unsupported"
        if str(scope_status).startswith("unsupported")
        else scope_status
    )
    validation_context = {}
    if error is not None:
        validation_context = {
            "status": supported_scope_status,
            "error_type": type(error).__name__,
            "message": str(error),
        }
    validation_basis = (
        "HCM method availability: Exhibit 15-10/15-11 applicability and "
        "Chapter 15 Steps 2-6, 8, and 10; Chapter 26 examples are "
        "published regression evidence."
        if result is not None
        else None
    )

    return {
        "schema_version": MANUAL_AUDIT_SCHEMA_VERSION,
        "calculation_type": "manual_single_segment",
        "unit_system": str(user_inputs.get("unit_system", DEFAULT_UNIT_SYSTEM)).lower(),
        "user_inputs": dict(user_inputs),
        "normalized_engine_inputs": normalized_engine_inputs,
        "selected_segment_type": user_inputs.get("segment_type"),
        "selected_terrain_type": user_inputs.get("terrain_type"),
        "selected_horizontal_alignment": user_inputs.get(
            "horizontal_alignment", "straight"
        ),
        "grade_percent": normalized_engine_inputs.get(
            "grade_percent", user_inputs.get("grade_percent")
        ),
        "grade_length": error_context.get(
            "grade_length_mi",
            normalized_engine_inputs.get("grade_length_mi"),
        ),
        "vertical_class": error_context.get(
            "vertical_class",
            result_data.get("outputs", {}).get(
                "vertical_class", user_inputs.get("vertical_class")
            ),
        ),
        "heavy_vehicle_percent": normalized_engine_inputs.get(
            "heavy_vehicle_percent", user_inputs.get("heavy_vehicle_percent")
        ),
        "scope_status": scope_status,
        "validation_basis": validation_basis,
        "unsupported_reason": unsupported_reason,
        "supported_scope_status": supported_scope_status,
        "assumptions": result_data.get("assumptions", []),
        "warnings": result_data.get("warnings", []),
        "outputs": result_data.get("outputs", {}),
        "intermediate_values": result_data.get("intermediate_values", []),
        "validation_context": validation_context,
        "calculation_metadata": {
            "status": calculation_status,
            "method": result_data.get("method"),
            "facility_type": result_data.get("facility_type"),
            "error_type": type(error).__name__ if error is not None else None,
            "error_message": str(error) if error is not None else None,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
