"""Streamlit-independent adapter for the qualified HCM 7.0 weaving worksheet.

This module is deliberately limited to presentation-unit conversion, preset loading,
and audit assembly.  All numerical analysis is delegated to the public versioned
``WeavingSegmentMethod`` facade.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from hcmcalc.cli import find_case
from hcmcalc.core import HCMCalcError
from hcmcalc.ui.input_contracts import reject_unknown_keys, require_finite_number
from hcmcalc.ui.runtime_resources import load_packaged_yaml
from hcmcalc.ui.units import FEET_TO_METERS, MILES_TO_KILOMETERS
from hcmcalc.weaving import WeavingSegmentMethod


FIXTURE_FILENAME = "weaving_example_inputs.yaml"
WEAVING_METHOD_VERSION = "hcm_7_0"
WEAVING_METHOD_IDENTIFIER = "weaving_segment"
WEAVING_CALCULATION_CONTRACT = "hcm_7_0_weaving_segment_operational_v1"
MANUAL_WEAVING_CALCULATION_TYPE = "manual_freeway_weaving_segment_v1"
PRESET_LABELS = {
    "blank_custom": "Blank/custom starting values",
    "WVG-CH27-001": "Example 1 reference preset",
    "WVG-CH27-002": "Example 2 reference preset",
    "WVG-CH27-003": "Example 3 reference preset",
}
WEAVING_UI_INPUT_KEYS = {
    "case_name", "configuration", "segment_length", "number_of_lanes",
    "number_of_weaving_lanes", "entry_side", "exit_side", "option_fr",
    "option_rf", "option_rr", "reachable_ff", "reachable_fr", "reachable_rf",
    "reachable_rr", "nwl_basis", "lane_change_basis", "lc_rf", "lc_fr", "lc_rr",
    "volume_ff_veh_h", "volume_fr_veh_h", "volume_rf_veh_h", "volume_rr_veh_h",
    "peak_hour_factor", "interchange_density", "ffs_source", "free_flow_speed",
    "base_free_flow_speed", "lane_width", "right_side_lateral_clearance",
    "total_ramp_density", "heavy_vehicle_percent", "terrain_type",
}
MANUAL_WEAVING_LIMITATIONS = [
    "Qualified HCM 7.0 isolated freeway weaving operational analysis only.",
    "One-sided (N=3/4; NWL=2/3) and two-sided (N=3/4; NWL=0) geometry only.",
    "HCM 7.1, C-D roadways, multilane highway weaving, Design, Sensitivity, queues, and automatic geometry derivation are not available.",
    "LS >= LMAX is a Chapter 12/14 handoff; no weaving LOS is assigned.",
    "Only unrounded v/c > 1.00 is above capacity; speed and density are not predicted in that state.",
]


def weaving_preset_options() -> dict[str, str]:
    return dict(PRESET_LABELS)


def clear_manual_weaving_state(state: dict[str, Any]) -> None:
    for key in tuple(state):
        if key.startswith("manual_weaving_input_") or key in {
            "manual_weaving_result", "manual_weaving_audit", "manual_weaving_error",
            "manual_weaving_loaded_displayed",
        }:
            state.pop(key, None)


def load_weaving_preset(preset_id: str) -> dict[str, Any]:
    """Return an independently transcribed validation preset, never a new method."""

    if preset_id not in PRESET_LABELS:
        raise ValueError(f"Unsupported weaving preset: {preset_id}.")
    case_id = "WVG-CH27-001" if preset_id == "blank_custom" else preset_id
    case = find_case(load_packaged_yaml(FIXTURE_FILENAME), case_id)
    return {
        "preset_id": preset_id,
        "preset_label": PRESET_LABELS[preset_id],
        "inputs": deepcopy(case["inputs"]),
        "validation_reference": case_id if preset_id != "blank_custom" else None,
    }


def weaving_preset_ui_inputs(preset_id: str, unit_system: str = "imperial") -> dict[str, Any]:
    return weaving_engine_inputs_to_ui(load_weaving_preset(preset_id)["inputs"], unit_system)


def weaving_engine_inputs_to_ui(inputs: dict[str, Any], unit_system: str) -> dict[str, Any]:
    metric = _normalize_unit_system(unit_system) == "metric"
    length_factor = FEET_TO_METERS if metric else 1.0
    speed_factor = MILES_TO_KILOMETERS if metric else 1.0
    density_factor = 1.0 / MILES_TO_KILOMETERS if metric else 1.0
    geometry = inputs["geometry"]
    return {
        "case_name": inputs["case_id"], "configuration": inputs["configuration"],
        "segment_length": inputs["segment_length_ft"] * length_factor,
        "number_of_lanes": inputs["number_of_lanes"],
        "number_of_weaving_lanes": inputs["number_of_weaving_lanes"],
        "entry_side": geometry["entry_side"], "exit_side": geometry["exit_side"],
        "option_fr": geometry["option_lane_status"]["fr"],
        "option_rf": geometry["option_lane_status"]["rf"],
        "option_rr": geometry["option_lane_status"]["rr"],
        "reachable_ff": geometry["reachable_origin_destination_lanes"]["ff"],
        "reachable_fr": geometry["reachable_origin_destination_lanes"]["fr"],
        "reachable_rf": geometry["reachable_origin_destination_lanes"]["rf"],
        "reachable_rr": geometry["reachable_origin_destination_lanes"]["rr"],
        "nwl_basis": geometry["nwl_basis"], "lane_change_basis": geometry["lane_change_basis"],
        "lc_rf": inputs["lc_rf"], "lc_fr": inputs["lc_fr"], "lc_rr": inputs["lc_rr"],
        "volume_ff_veh_h": inputs["volume_ff_veh_h"], "volume_fr_veh_h": inputs["volume_fr_veh_h"],
        "volume_rf_veh_h": inputs["volume_rf_veh_h"], "volume_rr_veh_h": inputs["volume_rr_veh_h"],
        "peak_hour_factor": inputs["peak_hour_factor"],
        "interchange_density": inputs["interchange_density_per_mi"] * density_factor,
        "ffs_source": inputs["ffs_source"],
        "free_flow_speed": _scaled(inputs.get("free_flow_speed_mph"), speed_factor),
        "base_free_flow_speed": _scaled(inputs.get("base_free_flow_speed_mph"), speed_factor),
        "lane_width": _scaled(inputs.get("lane_width_ft"), length_factor),
        "right_side_lateral_clearance": _scaled(inputs.get("right_side_lateral_clearance_ft"), length_factor),
        "total_ramp_density": _scaled(inputs.get("total_ramp_density_per_mi"), density_factor),
        "heavy_vehicle_percent": inputs["heavy_vehicle_percent"], "terrain_type": inputs["terrain_type"],
    }


def weaving_ui_inputs_to_engine(values: dict[str, Any], unit_system: str) -> dict[str, Any]:
    """Normalize UI values into the exact public-engine contract."""

    reject_unknown_keys(values, WEAVING_UI_INPUT_KEYS, "Weaving Segment UI")
    metric = _normalize_unit_system(unit_system) == "metric"
    configuration = values["configuration"]
    if configuration not in {"one_sided", "two_sided"}:
        raise HCMCalcError("configuration must be one_sided or two_sided.")
    ffs_source = values["ffs_source"]
    if ffs_source not in {"measured", "estimated"}:
        raise HCMCalcError("ffs_source must be measured or estimated.")
    for name in (
        "segment_length", "peak_hour_factor", "interchange_density", "volume_ff_veh_h",
        "volume_fr_veh_h", "volume_rf_veh_h", "volume_rr_veh_h", "heavy_vehicle_percent",
    ):
        require_finite_number(name, values.get(name))
    for name in ("number_of_lanes", "number_of_weaving_lanes"):
        value = values.get(name)
        if isinstance(value, bool) or not isinstance(value, int):
            raise HCMCalcError(f"{name} must be an integer.")
    if not isinstance(values.get("case_name"), str) or not values["case_name"].strip():
        raise HCMCalcError("case_name is required.")
    length_factor = 1.0 / FEET_TO_METERS if metric else 1.0
    speed_factor = 1.0 / MILES_TO_KILOMETERS if metric else 1.0
    density_factor = MILES_TO_KILOMETERS if metric else 1.0
    estimated = ffs_source == "estimated"
    active_ffs = ("base_free_flow_speed", "lane_width", "right_side_lateral_clearance", "total_ramp_density")
    if estimated:
        for name in active_ffs:
            require_finite_number(name, values.get(name))
    else:
        require_finite_number("free_flow_speed", values.get("free_flow_speed"))
    lc_rf = _lane_change(values.get("lc_rf"), "lc_rf") if configuration == "one_sided" else None
    lc_fr = _lane_change(values.get("lc_fr"), "lc_fr") if configuration == "one_sided" else None
    lc_rr = _lane_change(values.get("lc_rr"), "lc_rr") if configuration == "two_sided" else None
    return {
        "method_version": WEAVING_METHOD_VERSION, "case_id": values["case_name"].strip(),
        "facility_type": "freeway_weaving_segment", "analysis_type": "operational_analysis",
        "direction": "peak_direction", "configuration": configuration,
        "analysis_period_minutes": 15, "peak_hour_factor": float(values["peak_hour_factor"]),
        "segment_length_ft": float(values["segment_length"]) * length_factor,
        "number_of_lanes": values["number_of_lanes"],
        "number_of_weaving_lanes": values["number_of_weaving_lanes"],
        "volume_ff_veh_h": float(values["volume_ff_veh_h"]), "volume_fr_veh_h": float(values["volume_fr_veh_h"]),
        "volume_rf_veh_h": float(values["volume_rf_veh_h"]), "volume_rr_veh_h": float(values["volume_rr_veh_h"]),
        "interchange_density_per_mi": float(values["interchange_density"]) * density_factor,
        "ffs_source": ffs_source,
        "free_flow_speed_mph": (float(values["free_flow_speed"]) * speed_factor if not estimated else None),
        "base_free_flow_speed_mph": (float(values["base_free_flow_speed"]) * speed_factor if estimated else None),
        "lane_width_ft": (float(values["lane_width"]) * length_factor if estimated else None),
        "right_side_lateral_clearance_ft": (float(values["right_side_lateral_clearance"]) * length_factor if estimated else None),
        "total_ramp_density_per_mi": (float(values["total_ramp_density"]) * density_factor if estimated else None),
        "heavy_vehicle_percent": float(values["heavy_vehicle_percent"]), "terrain_type": values["terrain_type"],
        "speed_adjustment_factor": 1.0, "capacity_adjustment_factor": 1.0,
        "speed_adjustment_factor_source": "hcm_base_conditions",
        "capacity_adjustment_factor_source": "hcm_base_conditions",
        "lc_rf": lc_rf, "lc_fr": lc_fr, "lc_rr": lc_rr,
        "geometry": {
            "entry_side": values["entry_side"], "exit_side": values["exit_side"],
            "reachable_origin_destination_lanes": {
                key: values[f"reachable_{key}"] for key in ("ff", "fr", "rf", "rr")
            },
            "option_lane_status": {"fr": values["option_fr"], "rf": values["option_rf"], "rr": values["option_rr"]},
            "nwl_basis": values["nwl_basis"], "lane_change_basis": values["lane_change_basis"],
        },
    }


def run_manual_weaving(inputs: dict[str, Any]):
    return WeavingSegmentMethod(version=WEAVING_METHOD_VERSION).calculate(inputs)


def weaving_display_outputs(outputs: dict[str, Any], unit_system: str) -> dict[str, dict[str, Any]]:
    metric = _normalize_unit_system(unit_system) == "metric"
    speed_factor = MILES_TO_KILOMETERS if metric else 1.0
    density_factor = 1.0 / MILES_TO_KILOMETERS if metric else 1.0
    return {
        "mean_speed": _metric(outputs.get("mean_speed_mph"), speed_factor, "km/h" if metric else "mph"),
        "weaving_speed": _metric(outputs.get("weaving_speed_mph"), speed_factor, "km/h" if metric else "mph"),
        "nonweaving_speed": _metric(outputs.get("nonweaving_speed_mph"), speed_factor, "km/h" if metric else "mph"),
        "density": _metric(outputs.get("density_pc_mi_ln"), density_factor, "pc/km/ln" if metric else "pc/mi/ln"),
        "capacity": _metric(outputs.get("adjusted_prevailing_capacity_veh_h"), 1.0, "veh/h"),
        "demand": _metric(outputs.get("total_flow_pc_h"), 1.0, "pc/h"),
    }


def build_manual_weaving_audit_record(preset_id: str, submitted_inputs: dict[str, Any], *, unit_system: str, displayed_inputs: dict[str, Any], result: Any | None = None, error: Exception | None = None) -> dict[str, Any]:
    outputs = result.outputs if result is not None else {}
    return {
        "workflow": MANUAL_WEAVING_CALCULATION_TYPE, "preset_id": preset_id,
        "method_family": WEAVING_METHOD_IDENTIFIER, "method_version": WEAVING_METHOD_VERSION,
        "calculation_contract": WEAVING_CALCULATION_CONTRACT, "unit_system": _normalize_unit_system(unit_system),
        "displayed_inputs": deepcopy(displayed_inputs), "submitted_inputs": deepcopy(submitted_inputs),
        "normalized_engine_inputs": deepcopy(submitted_inputs), "outputs": deepcopy(outputs),
        "assumptions": list(outputs.get("assumptions", [])), "warnings": list(outputs.get("warnings", [])),
        "limitations": list(MANUAL_WEAVING_LIMITATIONS), "error": str(error) if error else None,
    }


def _normalize_unit_system(unit_system: str) -> str:
    normalized = str(unit_system).strip().lower()
    if normalized not in {"metric", "imperial"}:
        raise HCMCalcError("unit_system must be metric or imperial.")
    return normalized


def _lane_change(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise HCMCalcError(f"{name} must be an integer lane-change count.")
    return value


def _scaled(value: Any, factor: float) -> float | None:
    return float(value) * factor if value is not None else None


def _metric(value: Any, factor: float, unit: str) -> dict[str, Any]:
    return {"value": float(value) * factor if value is not None else None, "unit": unit}
