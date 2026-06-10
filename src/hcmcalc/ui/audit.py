"""Audit records for manual UI calculations."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from hcmcalc.core import CalculationResult, HCMCalcError, MethodNotImplementedError
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
        supported_scope_status = "supported"
        calculation_status = "succeeded"
    elif error is not None:
        result_data = {}
        supported_scope_status = (
            "unsupported" if isinstance(error, MethodNotImplementedError) else "invalid"
        )
        calculation_status = "failed"
    else:
        result_data = {}
        supported_scope_status = "not_evaluated"
        calculation_status = "not_run"

    return {
        "schema_version": MANUAL_AUDIT_SCHEMA_VERSION,
        "calculation_type": "manual_single_segment",
        "unit_system": str(user_inputs.get("unit_system", DEFAULT_UNIT_SYSTEM)).lower(),
        "user_inputs": dict(user_inputs),
        "normalized_engine_inputs": normalized_engine_inputs,
        "selected_segment_type": user_inputs.get("segment_type"),
        "selected_terrain_type": user_inputs.get("terrain_type"),
        "supported_scope_status": supported_scope_status,
        "assumptions": result_data.get("assumptions", []),
        "warnings": result_data.get("warnings", []),
        "outputs": result_data.get("outputs", {}),
        "intermediate_values": result_data.get("intermediate_values", []),
        "calculation_metadata": {
            "status": calculation_status,
            "method": result_data.get("method"),
            "facility_type": result_data.get("facility_type"),
            "error_type": type(error).__name__ if error is not None else None,
            "error_message": str(error) if error is not None else None,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
