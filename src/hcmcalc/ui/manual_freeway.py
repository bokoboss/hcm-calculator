"""Streamlit-independent adapter for the guarded Basic Freeway v0.1 worksheet."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from hcmcalc.cli import find_case, load_input_file
from hcmcalc.freeway import BasicFreewaySegmentMethod
from hcmcalc.ui.units import MILES_TO_KILOMETERS


ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = ROOT / "references" / "freeway_example_inputs.yaml"
PRESET_LABELS = {
    "BF-CH26-001": "Chapter 26 Example 1 starting values",
}
SUPPORTED_UNIT_SYSTEMS = {"metric", "imperial"}
MANUAL_FREEWAY_CALCULATION_TYPE = "manual_basic_freeway_segment_v0_1"
MANUAL_FREEWAY_LIMITATIONS = [
    "Manual Basic Freeway Segment v0.1 is limited to the BF-CH26-001-compatible validated path.",
    "It is not a general freeway facility calculator.",
    "One direction, one segment, uninterrupted flow, and general-purpose lanes only.",
    "Ramp, weaving, merge/diverge, managed-lane, work-zone, reliability, and facility/corridor workflows are unsupported.",
    "Calculations remain engine-native Imperial; Metric values are UI/reporting conversions.",
    "Save/Load and export/reporting preserve only this guarded Basic Freeway Segment v0.1 workflow.",
]


def freeway_preset_options() -> dict[str, str]:
    """Return the supported Basic Freeway starting-value presets."""

    return dict(PRESET_LABELS)


def clear_manual_freeway_state(state: dict[str, Any]) -> None:
    """Clear result and worksheet widget state after preset or unit changes."""

    for key in tuple(state):
        if key.startswith("manual_freeway_input_") or key in {
            "manual_freeway_result",
            "manual_freeway_error",
            "manual_freeway_audit",
        }:
            state.pop(key, None)


def load_freeway_preset(case_id: str) -> dict[str, Any]:
    """Load a copy of the validated Basic Freeway starting values."""

    if case_id not in PRESET_LABELS:
        raise ValueError(f"Unsupported Basic Freeway preset: {case_id}.")
    case = find_case(load_input_file(FIXTURE_PATH), case_id)
    return {
        "case_id": case_id,
        "preset_label": PRESET_LABELS[case_id],
        "description": case["description"],
        "validation_status": case["validation_status"],
        "inputs": deepcopy(case["inputs"]),
    }


def freeway_preset_ui_inputs(
    case_id: str, unit_system: str = "imperial"
) -> dict[str, Any]:
    """Load preset inputs in the selected UI unit system."""

    return freeway_engine_inputs_to_ui(load_freeway_preset(case_id)["inputs"], unit_system)


def freeway_engine_inputs_to_ui(
    inputs: dict[str, Any], unit_system: str
) -> dict[str, Any]:
    """Convert engine-native Imperial inputs to user-facing worksheet values."""

    metric = _normalize_unit_system(unit_system) == "metric"
    speed_factor = MILES_TO_KILOMETERS if metric else 1.0
    length_factor = MILES_TO_KILOMETERS if metric else 1.0
    density_factor = 1.0 / MILES_TO_KILOMETERS if metric else 1.0
    return {
        "number_of_lanes": int(inputs["number_of_lanes"]),
        "segment_length": float(inputs["segment_length_mi"]) * length_factor,
        "ffs_source": inputs["ffs_source"],
        "free_flow_speed": _optional_scaled_value(
            inputs.get("free_flow_speed_mph"), speed_factor
        ),
        "base_free_flow_speed": _optional_scaled_value(
            inputs.get("base_free_flow_speed_mph"), speed_factor
        ),
        "lane_width": _optional_scaled_value(inputs.get("lane_width_ft"), 0.3048)
        if metric
        else inputs.get("lane_width_ft"),
        "right_side_lateral_clearance": _optional_scaled_value(
            inputs.get("right_side_lateral_clearance_ft"), 0.3048
        )
        if metric
        else inputs.get("right_side_lateral_clearance_ft"),
        "total_ramp_density": (
            _optional_scaled_value(inputs.get("total_ramp_density_per_mi"), density_factor)
        ),
        "demand_volume_veh_h": float(inputs["demand_volume_veh_h"]),
        "peak_hour_factor": float(inputs["peak_hour_factor"]),
        "heavy_vehicle_percent": float(inputs["heavy_vehicle_percent"]),
        "terrain_type": inputs["terrain_type"],
        "speed_adjustment_factor": float(inputs["speed_adjustment_factor"]),
        "capacity_adjustment_factor": float(inputs["capacity_adjustment_factor"]),
    }


def freeway_ui_inputs_to_engine(
    values: dict[str, Any], preset_inputs: dict[str, Any], unit_system: str
) -> dict[str, Any]:
    """Convert user-facing worksheet values to engine-native Imperial inputs."""

    metric = _normalize_unit_system(unit_system) == "metric"
    speed_factor = 1.0 / MILES_TO_KILOMETERS if metric else 1.0
    length_factor = 1.0 / MILES_TO_KILOMETERS if metric else 1.0
    width_factor = 1.0 / 0.3048 if metric else 1.0
    ramp_density_factor = MILES_TO_KILOMETERS if metric else 1.0
    ffs_source = values["ffs_source"]
    return {
        **preset_inputs,
        "number_of_lanes": int(values["number_of_lanes"]),
        "segment_length_mi": _rounded(float(values["segment_length"]) * length_factor),
        "demand_volume_veh_h": float(values["demand_volume_veh_h"]),
        "peak_hour_factor": float(values["peak_hour_factor"]),
        "heavy_vehicle_percent": float(values["heavy_vehicle_percent"]),
        "terrain_type": values["terrain_type"],
        "ffs_source": ffs_source,
        "free_flow_speed_mph": (
            _rounded(float(values["free_flow_speed"]) * speed_factor)
            if ffs_source == "measured"
            else None
        ),
        "base_free_flow_speed_mph": (
            _rounded(float(values["base_free_flow_speed"]) * speed_factor)
            if ffs_source == "estimated"
            else None
        ),
        "lane_width_ft": (
            _rounded(float(values["lane_width"]) * width_factor)
            if ffs_source == "estimated"
            else None
        ),
        "right_side_lateral_clearance_ft": (
            _rounded(float(values["right_side_lateral_clearance"]) * width_factor)
            if ffs_source == "estimated"
            else None
        ),
        "total_ramp_density_per_mi": (
            _rounded(float(values["total_ramp_density"]) * ramp_density_factor)
            if ffs_source == "estimated"
            else None
        ),
        "speed_adjustment_factor": float(values["speed_adjustment_factor"]),
        "capacity_adjustment_factor": float(values["capacity_adjustment_factor"]),
    }


def freeway_display_outputs(
    engine_outputs: dict[str, Any], unit_system: str
) -> dict[str, dict[str, Any]]:
    """Return primary Basic Freeway outputs in the selected UI unit system."""

    metric = _normalize_unit_system(unit_system) == "metric"
    speed_factor = MILES_TO_KILOMETERS if metric else 1.0
    density_factor = 1.0 / MILES_TO_KILOMETERS if metric else 1.0
    return {
        "density": {
            "value": float(engine_outputs["density_pc_mi_ln"]) * density_factor,
            "unit": "pc/km/ln" if metric else "pc/mi/ln",
        },
        "speed_used_for_density": {
            "value": float(engine_outputs["speed_used_for_density_mph"]) * speed_factor,
            "unit": "km/h" if metric else "mph",
        },
        "adjusted_free_flow_speed": {
            "value": float(engine_outputs["adjusted_free_flow_speed_mph"])
            * speed_factor,
            "unit": "km/h" if metric else "mph",
        },
        "base_free_flow_speed": {
            "value": float(engine_outputs["base_free_flow_speed_mph"]) * speed_factor,
            "unit": "km/h" if metric else "mph",
        },
        "demand_flow_rate": {
            "value": float(engine_outputs["demand_flow_rate_pc_h_ln"]),
            "unit": "pc/h/ln",
        },
        "capacity": {
            "value": float(engine_outputs["capacity_pc_h_ln"]),
            "unit": "pc/h/ln",
        },
        "adjusted_capacity": {
            "value": float(engine_outputs["adjusted_capacity_pc_h_ln"]),
            "unit": "pc/h/ln",
        },
    }


def run_manual_freeway(inputs: dict[str, Any]):
    """Run submitted worksheet values through the existing Basic Freeway engine."""

    return BasicFreewaySegmentMethod().calculate(inputs)


def build_manual_freeway_audit_record(
    preset_id: str,
    inputs: dict[str, Any],
    *,
    unit_system: str = "imperial",
    displayed_inputs: dict[str, Any] | None = None,
    result: Any | None = None,
    error: Exception | None = None,
) -> dict[str, Any]:
    """Build a compact audit record without adding calculation behavior."""

    return {
        "calculation_type": MANUAL_FREEWAY_CALCULATION_TYPE,
        "preset_id": preset_id,
        "unit_system": _normalize_unit_system(unit_system),
        "support_status": "chapter_26_example_validated_v0_1",
        "displayed_inputs": deepcopy(displayed_inputs),
        "submitted_inputs": deepcopy(inputs),
        "calculation_succeeded": result is not None,
        "validation_error": str(error) if error is not None else None,
        "unsupported_behavior_notes": list(MANUAL_FREEWAY_LIMITATIONS),
    }


def _normalize_unit_system(unit_system: str) -> str:
    normalized = str(unit_system).strip().lower()
    if normalized not in SUPPORTED_UNIT_SYSTEMS:
        raise ValueError("unit_system must be metric or imperial.")
    return normalized


def _optional_scaled_value(value: Any, factor: float) -> float | None:
    if value is None:
        return None
    return float(value) * factor


def _rounded(value: float) -> float:
    """Remove insignificant binary conversion noise before exact guardrails."""

    return round(value, 10)
