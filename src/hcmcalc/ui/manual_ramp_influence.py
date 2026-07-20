"""UI-boundary adapters for qualified HCM 7.0 merge and diverge workflows."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Literal

from hcmcalc.core import HCMCalcError
from hcmcalc.ramp_influence import DivergeSegmentMethod, MergeSegmentMethod
from hcmcalc.ui.input_contracts import reject_unknown_keys, require_finite_number
from hcmcalc.ui.runtime_resources import load_packaged_yaml
from hcmcalc.ui.units import FEET_TO_METERS, MILES_TO_KILOMETERS


RampWorkflow = Literal["merge", "diverge"]

FIXTURE_FILENAME = "merge_diverge_example_inputs.yaml"
ASSET_ROOT = Path(__file__).resolve().parent / "assets" / "ramp_influence"
METHOD_VERSION = "hcm_7_0"
MERGE_METHOD_FAMILY = "merge_segment"
DIVERGE_METHOD_FAMILY = "diverge_segment"
MERGE_CALCULATION_CONTRACT = (
    "hcm7_v70_chapter_14_isolated_right_side_one_lane_merge_operational"
)
DIVERGE_CALCULATION_CONTRACT = (
    "hcm7_v70_chapter_14_isolated_right_side_one_lane_diverge_operational"
)
MANUAL_MERGE_PROJECT_TYPE = "manual_freeway_merge_segment_v1"
MANUAL_DIVERGE_PROJECT_TYPE = "manual_freeway_diverge_segment_v1"

MERGE_PRESET_LABELS = {
    "blank_custom": "Blank/custom",
    "chapter_28_example_1_merge": "Chapter 28 Example 1",
    "chapter_28_example_3_merge_component": "Chapter 28 Example 3 merge component",
}
DIVERGE_PRESET_LABELS = {
    "blank_custom": "Blank/custom",
    "chapter_28_example_3_diverge_component": "Chapter 28 Example 3 diverge component",
}
UI_INPUT_KEYS = {
    "case_name",
    "freeway_lanes",
    "auxiliary_lane_length",
    "freeway_demand_veh_h",
    "ramp_demand_veh_h",
    "freeway_peak_hour_factor",
    "ramp_peak_hour_factor",
    "freeway_heavy_vehicle_percent",
    "ramp_heavy_vehicle_percent",
    "terrain_type",
    "ffs_source",
    "free_flow_speed",
    "base_free_flow_speed",
    "lane_width",
    "right_side_lateral_clearance",
    "total_ramp_density",
    "ramp_ffs",
    "speed_adjustment_factor_source",
    "capacity_adjustment_factor_source",
    "geometry_source",
    "geometry_notes",
}


LIMITATIONS = [
    "Qualified HCM 7.0 isolated general-purpose freeway ramp influence operational analysis only.",
    "One-lane right-side ramp, 2-4 freeway lanes, level or rolling terrain only.",
    "HCM 7.1, adjacent ramps, left-side ramps, lane additions/drops, option lanes, C-D roadways, queues, delay, spillback, and design/service-volume analysis are unavailable.",
    "Roadway capacity failure reports LOS F with speed and density not predicted.",
    "Maximum desirable influence-area flow exceedance is a warning when roadway capacity is not failed.",
]


def ramp_preset_options(workflow: RampWorkflow) -> dict[str, str]:
    return dict(MERGE_PRESET_LABELS if workflow == "merge" else DIVERGE_PRESET_LABELS)


def method_family(workflow: RampWorkflow) -> str:
    return MERGE_METHOD_FAMILY if workflow == "merge" else DIVERGE_METHOD_FAMILY


def project_type(workflow: RampWorkflow) -> str:
    return MANUAL_MERGE_PROJECT_TYPE if workflow == "merge" else MANUAL_DIVERGE_PROJECT_TYPE


def calculation_contract(workflow: RampWorkflow) -> str:
    return MERGE_CALCULATION_CONTRACT if workflow == "merge" else DIVERGE_CALCULATION_CONTRACT


def diagram_path(workflow: RampWorkflow) -> Path:
    name = "merge_right_on_ramp.svg" if workflow == "merge" else "diverge_right_off_ramp.svg"
    return ASSET_ROOT / name


def clear_manual_ramp_state(state: dict[str, Any], workflow: RampWorkflow) -> None:
    prefix = f"manual_{workflow}_"
    for key in tuple(state):
        if key.startswith(prefix) and (
            "_input_" in key
            or key.endswith("_result")
            or key.endswith("_audit")
            or key.endswith("_error")
            or key.endswith("_loaded_displayed")
        ):
            state.pop(key, None)


def load_ramp_preset(workflow: RampWorkflow, preset_id: str) -> dict[str, Any]:
    labels = ramp_preset_options(workflow)
    if preset_id not in labels:
        raise ValueError(f"Unsupported {workflow} preset: {preset_id}.")
    fixture_id = _default_case_id(workflow) if preset_id == "blank_custom" else preset_id
    fixture = load_packaged_yaml(FIXTURE_FILENAME)
    for case in fixture["examples"]:
        if case["id"] == fixture_id and case["method_family"] == method_family(workflow):
            return {
                "preset_id": preset_id,
                "preset_label": labels[preset_id],
                "validation_reference": None if preset_id == "blank_custom" else fixture_id,
                "inputs": deepcopy(case["inputs"]),
            }
    raise ValueError(f"Preset fixture not found: {fixture_id}.")


def ramp_preset_ui_inputs(
    workflow: RampWorkflow, preset_id: str, unit_system: str = "imperial"
) -> dict[str, Any]:
    return ramp_engine_inputs_to_ui(load_ramp_preset(workflow, preset_id)["inputs"], unit_system)


def ramp_engine_inputs_to_ui(inputs: dict[str, Any], unit_system: str) -> dict[str, Any]:
    metric = _normalize_unit_system(unit_system) == "metric"
    length_factor = FEET_TO_METERS if metric else 1.0
    speed_factor = MILES_TO_KILOMETERS if metric else 1.0
    density_factor = 1.0 / MILES_TO_KILOMETERS if metric else 1.0
    geometry = inputs.get("geometry_evidence", {})
    aux = inputs.get("acceleration_lane_length_ft", inputs.get("deceleration_lane_length_ft"))
    return {
        "case_name": inputs["case_id"],
        "freeway_lanes": int(inputs["freeway_lanes"]),
        "auxiliary_lane_length": float(aux) * length_factor,
        "freeway_demand_veh_h": float(inputs["freeway_demand_veh_h"]),
        "ramp_demand_veh_h": float(inputs["ramp_demand_veh_h"]),
        "freeway_peak_hour_factor": float(inputs["freeway_peak_hour_factor"]),
        "ramp_peak_hour_factor": float(inputs["ramp_peak_hour_factor"]),
        "freeway_heavy_vehicle_percent": float(inputs["freeway_heavy_vehicle_percent"]),
        "ramp_heavy_vehicle_percent": float(inputs["ramp_heavy_vehicle_percent"]),
        "terrain_type": inputs["terrain_type"],
        "ffs_source": inputs["ffs_source"],
        "free_flow_speed": _scaled(inputs.get("free_flow_speed_mph"), speed_factor),
        "base_free_flow_speed": _scaled(inputs.get("base_free_flow_speed_mph"), speed_factor),
        "lane_width": _scaled(inputs.get("lane_width_ft"), length_factor),
        "right_side_lateral_clearance": _scaled(inputs.get("right_side_lateral_clearance_ft"), length_factor),
        "total_ramp_density": _scaled(inputs.get("total_ramp_density_per_mi"), density_factor),
        "ramp_ffs": float(inputs["ramp_ffs_mph"]) * speed_factor,
        "speed_adjustment_factor_source": inputs.get("speed_adjustment_factor_source", "hcm_base_conditions"),
        "capacity_adjustment_factor_source": inputs.get("capacity_adjustment_factor_source", "hcm_base_conditions"),
        "geometry_source": geometry.get("source", "user_entered"),
        "geometry_notes": geometry.get("notes", ""),
    }


def ramp_ui_inputs_to_engine(
    workflow: RampWorkflow, values: dict[str, Any], unit_system: str
) -> dict[str, Any]:
    reject_unknown_keys(values, UI_INPUT_KEYS, f"{workflow.title()} Segment UI")
    metric = _normalize_unit_system(unit_system) == "metric"
    length_factor = 1.0 / FEET_TO_METERS if metric else 1.0
    speed_factor = 1.0 / MILES_TO_KILOMETERS if metric else 1.0
    density_factor = MILES_TO_KILOMETERS if metric else 1.0
    for name in (
        "freeway_lanes",
        "auxiliary_lane_length",
        "freeway_demand_veh_h",
        "ramp_demand_veh_h",
        "freeway_peak_hour_factor",
        "ramp_peak_hour_factor",
        "freeway_heavy_vehicle_percent",
        "ramp_heavy_vehicle_percent",
        "ramp_ffs",
    ):
        require_finite_number(name, values.get(name))
    if values["ffs_source"] not in {"measured", "estimated"}:
        raise HCMCalcError("ffs_source must be measured or estimated.")
    if values["terrain_type"] not in {"level", "rolling"}:
        raise HCMCalcError("terrain_type must be level or rolling.")
    if values["ffs_source"] == "measured":
        require_finite_number("free_flow_speed", values.get("free_flow_speed"))
    else:
        for name in (
            "base_free_flow_speed",
            "lane_width",
            "right_side_lateral_clearance",
            "total_ramp_density",
        ):
            require_finite_number(name, values.get(name))
    lanes = int(values["freeway_lanes"])
    case_name = str(values.get("case_name") or "").strip()
    if not case_name:
        raise HCMCalcError("case_name is required.")
    if workflow == "diverge" and float(values["ramp_demand_veh_h"]) > float(values["freeway_demand_veh_h"]):
        raise HCMCalcError("off-ramp demand cannot exceed upstream freeway demand.")
    estimated = values["ffs_source"] == "estimated"
    engine = {
        "method_version": METHOD_VERSION,
        "case_id": case_name,
        "facility_type": "freeway_merge_segment" if workflow == "merge" else "freeway_diverge_segment",
        "analysis_type": "operational_analysis",
        "analysis_period_minutes": 15,
        "freeway_lanes": lanes,
        "ramp_side": "right",
        "ramp_lanes": 1,
        "freeway_demand_veh_h": float(values["freeway_demand_veh_h"]),
        "ramp_demand_veh_h": float(values["ramp_demand_veh_h"]),
        "freeway_peak_hour_factor": float(values["freeway_peak_hour_factor"]),
        "ramp_peak_hour_factor": float(values["ramp_peak_hour_factor"]),
        "freeway_heavy_vehicle_percent": float(values["freeway_heavy_vehicle_percent"]),
        "ramp_heavy_vehicle_percent": float(values["ramp_heavy_vehicle_percent"]),
        "terrain_type": values["terrain_type"],
        "ffs_source": values["ffs_source"],
        "free_flow_speed_mph": (float(values["free_flow_speed"]) * speed_factor if not estimated else None),
        "base_free_flow_speed_mph": (float(values["base_free_flow_speed"]) * speed_factor if estimated else None),
        "lane_width_ft": (float(values["lane_width"]) * length_factor if estimated else None),
        "right_side_lateral_clearance_ft": (
            float(values["right_side_lateral_clearance"]) * length_factor if estimated else None
        ),
        "total_ramp_density_per_mi": (
            float(values["total_ramp_density"]) * density_factor if estimated else None
        ),
        "ramp_ffs_mph": float(values["ramp_ffs"]) * speed_factor,
        "speed_adjustment_factor": 1.0,
        "capacity_adjustment_factor": 1.0,
        "speed_adjustment_factor_source": values.get("speed_adjustment_factor_source") or "hcm_base_conditions",
        "capacity_adjustment_factor_source": values.get("capacity_adjustment_factor_source") or "hcm_base_conditions",
        "adjacent_ramp_context": "isolated",
        "geometry_evidence": {
            "source": str(values.get("geometry_source") or "user_entered"),
            "configuration": (
                "isolated_one_lane_right_side_on_ramp"
                if workflow == "merge"
                else "isolated_one_lane_right_side_off_ramp"
            ),
            "reviewed_by": "manual_phase_14_3_workflow",
            "notes": str(values.get("geometry_notes") or "User-entered geometry evidence."),
        },
    }
    aux_ft = float(values["auxiliary_lane_length"]) * length_factor
    if workflow == "merge":
        engine.update(
            acceleration_lane_length_ft=aux_ft,
            downstream_freeway_demand_veh_h=None,
            lane_addition=False,
            major_merge=False,
        )
    else:
        engine.update(
            deceleration_lane_length_ft=aux_ft,
            continuing_freeway_demand_veh_h=None,
            lane_drop=False,
            option_lane=False,
            major_diverge=False,
        )
    return engine


def run_manual_ramp(workflow: RampWorkflow, inputs: dict[str, Any]):
    if workflow == "merge":
        return MergeSegmentMethod(version=METHOD_VERSION).calculate(inputs)
    return DivergeSegmentMethod(version=METHOD_VERSION).calculate(inputs)


def ramp_display_outputs(outputs: dict[str, Any], unit_system: str) -> dict[str, dict[str, Any]]:
    metric = _normalize_unit_system(unit_system) == "metric"
    speed_factor = MILES_TO_KILOMETERS if metric else 1.0
    density_factor = 1.0 / MILES_TO_KILOMETERS if metric else 1.0
    capacity = outputs.get("adjusted_freeway_capacity_pc_h")
    vc = outputs.get("downstream_freeway_demand_capacity_ratio", outputs.get("upstream_freeway_demand_capacity_ratio"))
    return {
        "density": _metric(outputs.get("density_pc_mi_ln"), density_factor, "pc/km/ln" if metric else "pc/mi/ln"),
        "ramp_influence_speed": _metric(outputs.get("ramp_influence_speed_mph"), speed_factor, "km/h" if metric else "mph"),
        "all_lanes_speed": _metric(outputs.get("all_lanes_speed_mph"), speed_factor, "km/h" if metric else "mph"),
        "governing_capacity": _metric(capacity, 1.0, "pc/h"),
        "governing_vc": _metric(vc, 1.0, None),
    }


def build_manual_ramp_audit_record(
    workflow: RampWorkflow,
    preset_id: str,
    submitted_inputs: dict[str, Any],
    *,
    unit_system: str,
    displayed_inputs: dict[str, Any],
    result: Any | None = None,
    error: Exception | None = None,
) -> dict[str, Any]:
    outputs = result.outputs if result is not None else {}
    return {
        "workflow": project_type(workflow),
        "preset_id": preset_id,
        "method_family": method_family(workflow),
        "method_version": METHOD_VERSION,
        "calculation_contract": calculation_contract(workflow),
        "unit_system": _normalize_unit_system(unit_system),
        "displayed_inputs": deepcopy(displayed_inputs),
        "normalized_engine_inputs": deepcopy(submitted_inputs),
        "outputs": deepcopy(outputs),
        "geometry_evidence": deepcopy(submitted_inputs.get("geometry_evidence", {})),
        "assumptions": list(outputs.get("assumptions", [])),
        "warnings": list(outputs.get("warnings", [])),
        "limitations": list(LIMITATIONS),
        "source_references": list(outputs.get("source_references", [])),
        "error": str(error) if error else None,
    }


def _default_case_id(workflow: RampWorkflow) -> str:
    return "chapter_28_example_1_merge" if workflow == "merge" else "chapter_28_example_3_diverge_component"


def _normalize_unit_system(unit_system: str) -> str:
    normalized = str(unit_system).strip().lower()
    if normalized not in {"metric", "imperial"}:
        raise HCMCalcError("unit_system must be metric or imperial.")
    return normalized


def _scaled(value: Any, factor: float) -> float | None:
    return None if value is None else float(value) * factor


def _metric(value: Any, factor: float, unit: str | None) -> dict[str, Any]:
    return {"value": None if value is None else float(value) * factor, "unit": unit}
