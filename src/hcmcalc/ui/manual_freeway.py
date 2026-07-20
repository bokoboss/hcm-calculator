"""Streamlit-independent adapter for the bounded Basic Freeway v0.1 worksheet."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from hcmcalc.cli import find_case, load_input_file
from hcmcalc.freeway import BasicFreewaySegmentMethod
from hcmcalc.freeway.validation import DRIVER_POPULATION_FACTORS
from hcmcalc.ui.input_contracts import reject_unknown_keys, require_finite_number
from hcmcalc.ui.units import MILES_TO_KILOMETERS


ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = ROOT / "references" / "freeway_example_inputs.yaml"
PRESET_LABELS = {
    "BF-CH26-001": "Chapter 26 Example 1 starting values",
}
SUPPORTED_UNIT_SYSTEMS = {"metric", "imperial"}
FREEWAY_UI_INPUT_KEYS = {
    "number_of_lanes", "segment_length", "ffs_source", "free_flow_speed",
    "base_free_flow_speed", "lane_width", "right_side_lateral_clearance",
    "total_ramp_density", "demand_volume_veh_h", "peak_hour_factor",
    "heavy_vehicle_percent", "terrain_type", "truck_mix", "grade_percent",
    "pce_mode", "passenger_car_equivalent",
    "passenger_car_equivalent_provenance", "speed_adjustment_factor",
    "capacity_adjustment_factor", "speed_adjustment_factor_source",
    "capacity_adjustment_factor_source", "driver_population_category",
}
MANUAL_FREEWAY_CALCULATION_TYPE = "manual_basic_freeway_segment_v1"
MANUAL_FREEWAY_LIMITATIONS = [
    "Manual Basic Freeway Segment v0.1 supports bounded one-direction, one-segment uninterrupted-flow Chapter 12 basic segment calculations.",
    "BF-CH26-001 remains available as optional example defaults and regression evidence.",
    "It is not a general freeway facility calculator.",
    "One direction, one segment, uninterrupted flow, and general-purpose lanes only.",
    "Ramp, weaving, merge/diverge, managed-lane, work-zone, reliability, and facility/corridor workflows are unsupported.",
    "Calculations remain engine-native Imperial; Metric values are UI/reporting conversions.",
    "Save/Load and export/reporting preserve only this bounded Basic Freeway Segment workflow.",
]


def freeway_preset_options() -> dict[str, str]:
    """Return the supported Basic Freeway starting-value presets."""

    return dict(PRESET_LABELS)


def clear_manual_freeway_state(state: dict[str, Any]) -> None:
    """Clear result and worksheet widget state after preset or unit changes."""

    for key in tuple(state):
        if (
            key.startswith("manual_freeway_input_")
            or key
            in {
                "manual_freeway_error",
                "manual_freeway_result",
                "manual_freeway_audit",
            }
        ):
            state.pop(key, None)
    calculation_state = state.get("calculation_workflow_state")
    if isinstance(calculation_state, dict):
        calculation_state.pop("manual_freeway", None)


def load_freeway_preset(case_id: str) -> dict[str, Any]:
    """Load a copy of the Basic Freeway example starting values."""

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
    displayed = {
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
        "truck_mix": inputs.get("truck_mix", "default_30_sut_70_tt"),
        "grade_percent": inputs.get("grade_percent"),
        "pce_mode": "external" if inputs.get("passenger_car_equivalent") is not None else "internal",
        "passenger_car_equivalent": inputs.get("passenger_car_equivalent"),
        "passenger_car_equivalent_provenance": inputs.get("passenger_car_equivalent_provenance"),
        "speed_adjustment_factor": float(inputs["speed_adjustment_factor"]),
        "capacity_adjustment_factor": float(inputs["capacity_adjustment_factor"]),
        "speed_adjustment_factor_source": inputs.get("speed_adjustment_factor_source", "hcm_base_conditions"),
        "capacity_adjustment_factor_source": inputs.get("capacity_adjustment_factor_source", "hcm_base_conditions"),
        "driver_population_category": inputs.get("driver_population_category", "regular"),
    }
    return displayed


def freeway_ui_inputs_to_engine(
    values: dict[str, Any], preset_inputs: dict[str, Any], unit_system: str
) -> dict[str, Any]:
    """Convert user-facing worksheet values to engine-native Imperial inputs."""

    reject_unknown_keys(values, FREEWAY_UI_INPUT_KEYS, "Basic Freeway UI")
    metric = _normalize_unit_system(unit_system) == "metric"
    speed_factor = 1.0 / MILES_TO_KILOMETERS if metric else 1.0
    length_factor = 1.0 / MILES_TO_KILOMETERS if metric else 1.0
    width_factor = 1.0 / 0.3048 if metric else 1.0
    ramp_density_factor = MILES_TO_KILOMETERS if metric else 1.0
    ffs_source = values["ffs_source"]
    pce_mode = values.get("pce_mode", "internal")
    if ffs_source not in {"measured", "estimated"}:
        raise ValueError("ffs_source must be measured or estimated.")
    if pce_mode not in {"internal", "external"}:
        raise ValueError("pce_mode must be internal or external.")
    driver_category = values.get("driver_population_category", "regular")
    if driver_category not in DRIVER_POPULATION_FACTORS:
        raise ValueError("driver_population_category is unsupported.")
    for name in (
        "number_of_lanes", "segment_length", "demand_volume_veh_h",
        "peak_hour_factor", "heavy_vehicle_percent", "speed_adjustment_factor",
        "capacity_adjustment_factor",
    ):
        require_finite_number(name, values[name])
    if ffs_source == "measured":
        require_finite_number("free_flow_speed", values.get("free_flow_speed"))
    else:
        for name in (
            "base_free_flow_speed", "lane_width", "right_side_lateral_clearance",
            "total_ramp_density",
        ):
            require_finite_number(name, values.get(name))
    if pce_mode == "external":
        require_finite_number("passenger_car_equivalent", values.get("passenger_car_equivalent"))
    engine_inputs = {
        "case_id": preset_inputs["case_id"],
        "facility_type": preset_inputs["facility_type"],
        "analysis_type": preset_inputs["analysis_type"],
        "direction": preset_inputs["direction"],
        "number_of_lanes": int(values["number_of_lanes"]),
        "segment_length_mi": _rounded(float(values["segment_length"]) * length_factor),
        "demand_volume_veh_h": float(values["demand_volume_veh_h"]),
        "peak_hour_factor": float(values["peak_hour_factor"]),
        "heavy_vehicle_percent": float(values["heavy_vehicle_percent"]),
        "terrain_type": values.get("terrain_type", "level") if pce_mode == "internal" else "level",
        "truck_mix": (
            values.get("truck_mix", "default_30_sut_70_tt")
            if pce_mode == "internal" and values.get("terrain_type") == "specific_grade"
            else "default_30_sut_70_tt"
        ),
        "grade_percent": (
            float(values["grade_percent"])
            if pce_mode == "internal" and values.get("terrain_type") == "specific_grade"
            else None
        ),
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
        "speed_adjustment_factor_source": values.get("speed_adjustment_factor_source", "hcm_base_conditions"),
        "capacity_adjustment_factor_source": values.get("capacity_adjustment_factor_source", "hcm_base_conditions"),
        "driver_population_category": driver_category,
        "passenger_car_equivalent": (
            float(values["passenger_car_equivalent"]) if pce_mode == "external" else None
        ),
        "passenger_car_equivalent_provenance": (
            str(values.get("passenger_car_equivalent_provenance") or "").strip()
            if pce_mode == "external" else None
        ),
    }
    if driver_category != "regular":
        saf, caf = DRIVER_POPULATION_FACTORS[driver_category]
        engine_inputs.update(
            speed_adjustment_factor=saf,
            capacity_adjustment_factor=caf,
            speed_adjustment_factor_source="chapter_26_driver_population",
            capacity_adjustment_factor_source="chapter_26_driver_population",
        )
    return engine_inputs


def freeway_display_outputs(
    engine_outputs: dict[str, Any], unit_system: str
) -> dict[str, dict[str, Any]]:
    """Return primary Basic Freeway outputs in the selected UI unit system."""

    metric = _normalize_unit_system(unit_system) == "metric"
    speed_factor = MILES_TO_KILOMETERS if metric else 1.0
    density_factor = 1.0 / MILES_TO_KILOMETERS if metric else 1.0
    def optional(value: Any, factor: float = 1.0) -> float | None:
        return None if value is None else float(value) * factor

    return {
        "density": {
            "value": optional(engine_outputs["density_pc_mi_ln"], density_factor),
            "unit": "pc/km/ln" if metric else "pc/mi/ln",
        },
        "speed_used_for_density": {
            "value": optional(engine_outputs["speed_used_for_density_mph"], speed_factor),
            "unit": "km/h" if metric else "mph",
        },
        "adjusted_free_flow_speed": {
            "value": float(engine_outputs["adjusted_free_flow_speed_mph"])
            * speed_factor,
            "unit": "km/h" if metric else "mph",
        },
        "free_flow_speed_before_saf": {
            "value": float(engine_outputs["free_flow_speed_before_saf_mph"]) * speed_factor,
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
        "support_status": "supported_basic_freeway_segment_v0_1",
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
