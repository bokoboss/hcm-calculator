"""Streamlit-independent adapter for the bounded Multilane v0.1 worksheet."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from hcmcalc.cli import find_case, load_input_file
from hcmcalc.multilane import MultilaneHighwayLOSMethod
from hcmcalc.ui.units import FEET_TO_METERS, MILES_TO_KILOMETERS


ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = ROOT / "references" / "multilane_example_inputs.yaml"
TEMPLATE_LABELS = {
    "MLH-CH26-004-EB": "Chapter 26 Example 4 - Eastbound starting values",
    "MLH-CH26-004-WB": "Chapter 26 Example 4 - Westbound starting values",
}
SUPPORTED_UNIT_SYSTEMS = {"metric", "imperial"}
MANUAL_MULTILANE_CALCULATION_TYPE = "manual_multilane_v0"
MANUAL_MULTILANE_LIMITATIONS = [
    "Manual Multilane v0.1 is a bounded one-direction Multilane Highway "
    "Segment calculator within the implemented HCM scope.",
    "Chapter 26 Example 4 EB/WB remains available as optional defaults and "
    "regression evidence.",
    "Basic Freeway, ramps, weaving, merge/diverge, managed lanes, work zones, "
    "reliability, and facility/corridor workflows are unsupported.",
    "Specific-grade PCE table expansion remains unsupported unless an auditable PCE is supplied.",
    "Calculations remain engine-native Imperial; Metric values are UI/reporting conversions.",
]


def multilane_template_options() -> dict[str, str]:
    """Return the two validated Multilane starter templates."""

    return dict(TEMPLATE_LABELS)


def clear_manual_multilane_state(state: dict[str, Any]) -> None:
    """Clear result and worksheet widget state after template or unit changes."""

    for key in tuple(state):
        if key.startswith("manual_multilane_input_") or key in {
            "manual_multilane_result",
            "manual_multilane_error",
            "manual_multilane_audit",
        }:
            state.pop(key, None)


def load_multilane_template(case_id: str) -> dict[str, Any]:
    """Load a copy of a validated Example Problem 4 input template."""

    if case_id not in TEMPLATE_LABELS:
        raise ValueError(f"Unsupported Multilane template: {case_id}.")
    case = find_case(load_input_file(FIXTURE_PATH), case_id)
    return {
        "case_id": case_id,
        "template_label": TEMPLATE_LABELS[case_id],
        "description": case["description"],
        "validation_status": case["validation_status"],
        "inputs": deepcopy(case["inputs"]),
    }


def multilane_template_ui_inputs(
    case_id: str, unit_system: str = "imperial"
) -> dict[str, Any]:
    """Load validated template inputs in the selected UI unit system."""

    return multilane_engine_inputs_to_ui(
        load_multilane_template(case_id)["inputs"], unit_system
    )


def multilane_engine_inputs_to_ui(
    inputs: dict[str, Any], unit_system: str
) -> dict[str, Any]:
    """Convert engine-native Imperial inputs to user-facing worksheet values."""

    metric = _normalize_unit_system(unit_system) == "metric"
    displayed = {
        "number_of_lanes": int(inputs["number_of_lanes"]),
        "segment_length": (
            float(inputs["segment_length_ft"]) * FEET_TO_METERS / 1000.0
            if metric
            else float(inputs["segment_length_ft"])
        ),
        "posted_speed_limit": (
            float(inputs["posted_speed_limit_mph"]) * MILES_TO_KILOMETERS
            if metric
            else float(inputs["posted_speed_limit_mph"])
        ),
        "lane_width": (
            float(inputs["lane_width_ft"]) * FEET_TO_METERS
            if metric
            else float(inputs["lane_width_ft"])
        ),
        "roadside_lateral_clearance": (
            float(inputs["roadside_lateral_clearance_ft"]) * FEET_TO_METERS
            if metric
            else float(inputs["roadside_lateral_clearance_ft"])
        ),
        "access_point_density": (
            float(inputs["access_point_density_per_mi"]) / MILES_TO_KILOMETERS
            if metric
            else float(inputs["access_point_density_per_mi"])
        ),
        "demand_volume_veh_h": float(inputs["demand_volume_veh_h"]),
        "peak_hour_factor": float(inputs["peak_hour_factor"]),
        "heavy_vehicle_percent": float(inputs["heavy_vehicle_percent"]),
        "grade_percent": float(inputs["grade_percent"]),
    }
    if "ffs_source" in inputs:
        displayed["ffs_source"] = inputs["ffs_source"]
    if inputs.get("free_flow_speed_mph") is not None:
        displayed["free_flow_speed"] = (
            float(inputs["free_flow_speed_mph"]) * MILES_TO_KILOMETERS
            if metric
            else float(inputs["free_flow_speed_mph"])
        )
    if inputs.get("passenger_car_equivalent") is not None:
        displayed["passenger_car_equivalent"] = inputs["passenger_car_equivalent"]
    return displayed


def multilane_ui_inputs_to_engine(
    values: dict[str, Any], template_inputs: dict[str, Any], unit_system: str
) -> dict[str, Any]:
    """Convert user-facing worksheet values to engine-native Imperial inputs."""

    metric = _normalize_unit_system(unit_system) == "metric"
    engine_inputs = {
        **template_inputs,
        "number_of_lanes": int(values["number_of_lanes"]),
        "segment_length_ft": (
            _rounded(float(values["segment_length"]) * 1000.0 / FEET_TO_METERS)
            if metric
            else float(values["segment_length"])
        ),
        "posted_speed_limit_mph": (
            _rounded(float(values["posted_speed_limit"]) / MILES_TO_KILOMETERS)
            if metric
            else float(values["posted_speed_limit"])
        ),
        "lane_width_ft": (
            _rounded(float(values["lane_width"]) / FEET_TO_METERS)
            if metric
            else float(values["lane_width"])
        ),
        "roadside_lateral_clearance_ft": (
            _rounded(float(values["roadside_lateral_clearance"]) / FEET_TO_METERS)
            if metric
            else float(values["roadside_lateral_clearance"])
        ),
        "access_point_density_per_mi": (
            _rounded(float(values["access_point_density"]) * MILES_TO_KILOMETERS)
            if metric
            else float(values["access_point_density"])
        ),
        "demand_volume_veh_h": float(values["demand_volume_veh_h"]),
        "peak_hour_factor": float(values["peak_hour_factor"]),
        "heavy_vehicle_percent": float(values["heavy_vehicle_percent"]),
        "grade_percent": float(values["grade_percent"]),
    }
    if "ffs_source" in values or "ffs_source" in template_inputs:
        engine_inputs["ffs_source"] = values.get(
            "ffs_source", template_inputs.get("ffs_source", "estimated")
        )
    if "free_flow_speed" in values or "free_flow_speed_mph" in template_inputs:
        engine_inputs["free_flow_speed_mph"] = (
            None
            if values.get("free_flow_speed") is None
            else (
                _rounded(float(values["free_flow_speed"]) / MILES_TO_KILOMETERS)
                if metric
                else float(values["free_flow_speed"])
            )
        )
    if (
        "passenger_car_equivalent" in values
        or "passenger_car_equivalent" in template_inputs
    ):
        engine_inputs["passenger_car_equivalent"] = values.get(
            "passenger_car_equivalent",
            template_inputs.get("passenger_car_equivalent"),
        )
    return engine_inputs


def multilane_display_outputs(
    engine_outputs: dict[str, Any], unit_system: str
) -> dict[str, dict[str, Any]]:
    """Return primary Multilane outputs in the selected UI unit system."""

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
    }


def run_manual_multilane(inputs: dict[str, Any]):
    """Run submitted worksheet values through the existing Multilane engine."""

    return MultilaneHighwayLOSMethod().calculate(inputs)


def build_manual_multilane_audit_record(
    template_id: str,
    inputs: dict[str, Any],
    *,
    unit_system: str = "imperial",
    displayed_inputs: dict[str, Any] | None = None,
    result: Any | None = None,
    error: Exception | None = None,
) -> dict[str, Any]:
    """Build a compact audit record without adding calculation behavior."""

    return {
        "calculation_type": MANUAL_MULTILANE_CALCULATION_TYPE,
        "template_id": template_id,
        "unit_system": _normalize_unit_system(unit_system),
        "support_status": "bounded_multilane_segment_v0_1",
        "displayed_inputs": deepcopy(displayed_inputs),
        "submitted_inputs": deepcopy(inputs),
        "calculation_succeeded": result is not None,
        "validation_error": str(error) if error is not None else None,
        "unsupported_behavior_notes": list(MANUAL_MULTILANE_LIMITATIONS),
    }


def _normalize_unit_system(unit_system: str) -> str:
    normalized = str(unit_system).strip().lower()
    if normalized not in SUPPORTED_UNIT_SYSTEMS:
        raise ValueError("unit_system must be metric or imperial.")
    return normalized


def _rounded(value: float) -> float:
    """Remove insignificant binary conversion noise before exact guardrails."""

    return round(value, 10)
