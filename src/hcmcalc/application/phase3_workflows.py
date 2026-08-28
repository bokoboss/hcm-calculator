"""Application services for the Phase 3 HCM workflow migration.

The Phase 3 services deliberately sit above the existing Streamlit-independent
adapters.  They own worksheet metadata, displayed-unit normalization, result
presentation state, and audit assembly; the HCM engines remain the only place
where numerical methodology is executed.
"""

from __future__ import annotations

from copy import deepcopy
from math import isfinite
from typing import Any, Mapping

from hcmcalc.cli import find_case, result_to_dict
from hcmcalc.core import HCMCalcError, UnsupportedScopeError
from hcmcalc.freeway.models import BasicFreewaySegmentInputs
from hcmcalc.freeway.validation import validate_inputs as validate_freeway_inputs
from hcmcalc.ramp_influence.models import (
    DivergeSegmentInputs,
    MergeSegmentInputs,
)
from hcmcalc.ramp_influence.validation import validate_diverge, validate_merge
from hcmcalc.ui.manual_freeway import (
    freeway_engine_inputs_to_ui,
    freeway_display_outputs,
    freeway_preset_options,
    freeway_ui_inputs_to_engine,
    load_freeway_preset,
    run_manual_freeway,
    build_manual_freeway_audit_record,
)
from hcmcalc.ui.manual_ramp_influence import (
    ramp_display_outputs,
    ramp_engine_inputs_to_ui,
    ramp_preset_options,
    ramp_preset_ui_inputs,
    ramp_ui_inputs_to_engine,
    run_manual_ramp,
)
from hcmcalc.ui.manual_segment import build_manual_segment_inputs, run_manual_single_segment
from hcmcalc.ui.manual_weaving import (
    weaving_display_outputs,
    weaving_engine_inputs_to_ui,
    weaving_preset_options,
    weaving_preset_ui_inputs,
    weaving_ui_inputs_to_engine,
    run_manual_weaving,
)
from hcmcalc.ui.runtime_resources import load_packaged_yaml
from hcmcalc.ui.units import FEET_TO_METERS, MILES_TO_KILOMETERS, manual_defaults
from hcmcalc.weaving.geometry import validate_v70_geometry
from hcmcalc.weaving.models import WeavingSegmentInputs
from hcmcalc.weaving.validation import validate_common as validate_weaving_common
from hcmcalc.application.workflow_state import MetricAvailability


PHASE3_METHOD_IDS = frozenset(
    {
        "two_lane_segment",
        "basic_freeway_segment",
        "weaving_segment",
        "merge_segment",
        "diverge_segment",
    }
)


def _field(
    key: str,
    kind: str,
    label_key: str,
    *,
    required: bool = False,
    required_if: Mapping[str, Any] | None = None,
    options: tuple[str, ...] = (),
    unit: str | None = None,
    unit_metric: str | None = None,
    unit_imperial: str | None = None,
    conditional: str | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "key": key,
        "kind": kind,
        "label_key": label_key,
    }
    if required:
        value["required"] = True
    if required_if:
        value["required_if"] = dict(required_if)
    if options:
        value["options"] = list(options)
    if unit is not None:
        value["unit"] = unit
    if unit_metric is not None:
        value["unit_metric"] = unit_metric
    if unit_imperial is not None:
        value["unit_imperial"] = unit_imperial
    if conditional is not None:
        value["conditional"] = conditional
    return value


TWO_LANE_SEGMENT_FIELDS: tuple[dict[str, Any], ...] = (
    _field(
        "segment_type",
        "choice",
        "two_lane_segment.segment_type",
        required=True,
        options=("passing_constrained", "passing_zone", "passing_lane"),
    ),
    _field(
        "terrain_type",
        "choice",
        "two_lane_segment.terrain_type",
        required=True,
        options=("level", "mountainous"),
    ),
    _field(
        "horizontal_alignment",
        "choice",
        "two_lane_segment.horizontal_alignment",
        required=True,
        options=("straight", "horizontal_curves"),
    ),
    _field(
        "segment_length",
        "number",
        "two_lane_segment.segment_length",
        required=True,
        unit_metric="km",
        unit_imperial="mi",
    ),
    _field(
        "posted_speed",
        "number",
        "two_lane_segment.posted_speed",
        required=True,
        unit_metric="km/h",
        unit_imperial="mph",
    ),
    _field(
        "analysis_direction_volume",
        "number",
        "two_lane_segment.analysis_direction_volume",
        required=True,
        unit="veh/h",
    ),
    _field(
        "opposing_direction_volume",
        "number",
        "two_lane_segment.opposing_direction_volume",
        required_if={"segment_type": "passing_zone"},
        unit="veh/h",
    ),
    _field(
        "peak_hour_factor",
        "number",
        "two_lane_segment.peak_hour_factor",
        required=True,
        unit="PHF",
    ),
    _field(
        "heavy_vehicle_percent",
        "number",
        "two_lane_segment.heavy_vehicle_percent",
        required=True,
        unit="%",
    ),
    _field(
        "grade_percent",
        "number",
        "two_lane_segment.grade_percent",
        required_if={"terrain_type": "mountainous"},
        unit="%",
    ),
    _field(
        "lane_width",
        "number",
        "two_lane_segment.lane_width",
        required=True,
        unit_metric="m",
        unit_imperial="ft",
    ),
    _field(
        "shoulder_width",
        "number",
        "two_lane_segment.shoulder_width",
        required=True,
        unit_metric="m",
        unit_imperial="ft",
    ),
    _field(
        "access_point_density",
        "number",
        "two_lane_segment.access_point_density",
        required=True,
        unit_metric="per km",
        unit_imperial="per mi",
    ),
    _field(
        "horizontal_alignment_subsegments",
        "json",
        "two_lane_segment.horizontal_alignment_subsegments",
        required_if={"horizontal_alignment": "horizontal_curves"},
        conditional="horizontal_curves",
    ),
)


BASIC_FREEWAY_FIELDS: tuple[dict[str, Any], ...] = (
    _field(
        "number_of_lanes",
        "integer",
        "basic_freeway.number_of_lanes",
        required=True,
        unit="lanes",
    ),
    _field(
        "segment_length",
        "number",
        "basic_freeway.segment_length",
        required=True,
        unit_metric="km",
        unit_imperial="mi",
    ),
    _field(
        "demand_volume_veh_h",
        "number",
        "basic_freeway.demand_volume",
        required=True,
        unit="veh/h",
    ),
    _field(
        "peak_hour_factor",
        "number",
        "basic_freeway.peak_hour_factor",
        required=True,
        unit="PHF",
    ),
    _field(
        "heavy_vehicle_percent",
        "number",
        "basic_freeway.heavy_vehicle_percent",
        required=True,
        unit="%",
    ),
    _field(
        "ffs_source",
        "choice",
        "basic_freeway.ffs_source",
        required=True,
        options=("estimated", "measured"),
    ),
    _field(
        "free_flow_speed",
        "number",
        "basic_freeway.free_flow_speed",
        required_if={"ffs_source": "measured"},
        unit_metric="km/h",
        unit_imperial="mph",
    ),
    _field(
        "base_free_flow_speed",
        "number",
        "basic_freeway.base_free_flow_speed",
        required_if={"ffs_source": "estimated"},
        unit_metric="km/h",
        unit_imperial="mph",
    ),
    _field(
        "lane_width",
        "number",
        "basic_freeway.lane_width",
        required_if={"ffs_source": "estimated"},
        unit_metric="m",
        unit_imperial="ft",
    ),
    _field(
        "right_side_lateral_clearance",
        "number",
        "basic_freeway.right_side_lateral_clearance",
        required_if={"ffs_source": "estimated"},
        unit_metric="m",
        unit_imperial="ft",
    ),
    _field(
        "total_ramp_density",
        "number",
        "basic_freeway.total_ramp_density",
        required_if={"ffs_source": "estimated"},
        unit_metric="per km",
        unit_imperial="per mi",
    ),
    _field(
        "terrain_type",
        "choice",
        "basic_freeway.terrain_type",
        required=True,
        options=("level", "rolling", "specific_grade"),
    ),
    _field(
        "truck_mix",
        "choice",
        "basic_freeway.truck_mix",
        required=True,
        options=(
            "default_30_sut_70_tt",
            "equal_50_sut_50_tt",
            "majority_70_sut_30_tt",
        ),
    ),
    _field(
        "grade_percent",
        "number",
        "basic_freeway.grade_percent",
        required_if={"terrain_type": "specific_grade"},
        unit="%",
    ),
    _field(
        "pce_mode",
        "choice",
        "basic_freeway.pce_mode",
        required=True,
        options=("internal", "external"),
    ),
    _field(
        "passenger_car_equivalent",
        "number",
        "basic_freeway.passenger_car_equivalent",
        required_if={"pce_mode": "external"},
        unit="PCE",
    ),
    _field(
        "passenger_car_equivalent_provenance",
        "text",
        "basic_freeway.passenger_car_equivalent_provenance",
        required_if={"pce_mode": "external"},
    ),
    _field(
        "driver_population_category",
        "choice",
        "basic_freeway.driver_population_category",
        required=True,
        options=(
            "regular",
            "mostly_familiar",
            "balanced",
            "mostly_unfamiliar",
            "overwhelmingly_unfamiliar",
        ),
    ),
    _field(
        "speed_adjustment_factor",
        "number",
        "basic_freeway.speed_adjustment_factor",
        required=True,
    ),
    _field(
        "capacity_adjustment_factor",
        "number",
        "basic_freeway.capacity_adjustment_factor",
        required=True,
    ),
    _field(
        "speed_adjustment_factor_source",
        "choice",
        "basic_freeway.speed_adjustment_factor_source",
        required=True,
        options=(
            "hcm_base_conditions",
            "chapter_26_driver_population",
            "project_local_calibration",
        ),
    ),
    _field(
        "capacity_adjustment_factor_source",
        "choice",
        "basic_freeway.capacity_adjustment_factor_source",
        required=True,
        options=(
            "hcm_base_conditions",
            "chapter_26_driver_population",
            "project_local_calibration",
        ),
    ),
)


WEAVING_FIELDS: tuple[dict[str, Any], ...] = (
    _field(
        "configuration",
        "choice",
        "weaving.configuration",
        required=True,
        options=("one_sided", "two_sided"),
    ),
    _field(
        "segment_length",
        "number",
        "weaving.segment_length",
        required=True,
        unit_metric="m",
        unit_imperial="ft",
    ),
    _field(
        "number_of_lanes",
        "integer",
        "weaving.number_of_lanes",
        required=True,
        unit="lanes",
    ),
    _field(
        "number_of_weaving_lanes",
        "integer",
        "weaving.number_of_weaving_lanes",
        required=True,
        unit="lanes",
    ),
    _field(
        "entry_side",
        "choice",
        "weaving.entry_side",
        required=True,
        options=("left", "right"),
    ),
    _field(
        "exit_side",
        "choice",
        "weaving.exit_side",
        required=True,
        options=("left", "right"),
    ),
    _field(
        "option_fr",
        "boolean",
        "weaving.option_fr",
        required=True,
        options=("false", "true"),
    ),
    _field(
        "option_rf",
        "boolean",
        "weaving.option_rf",
        required=True,
        options=("false", "true"),
    ),
    _field(
        "option_rr",
        "boolean",
        "weaving.option_rr",
        required=True,
        options=("false", "true"),
    ),
    _field(
        "reachable_ff",
        "text",
        "weaving.reachable_ff",
        required=True,
    ),
    _field(
        "reachable_fr",
        "text",
        "weaving.reachable_fr",
        required=True,
    ),
    _field(
        "reachable_rf",
        "text",
        "weaving.reachable_rf",
        required=True,
    ),
    _field(
        "reachable_rr",
        "text",
        "weaving.reachable_rr",
        required=True,
    ),
    _field(
        "nwl_basis",
        "text",
        "weaving.nwl_basis",
        required=True,
    ),
    _field(
        "lane_change_basis",
        "text",
        "weaving.lane_change_basis",
        required=True,
    ),
    _field(
        "lc_rf",
        "integer",
        "weaving.lc_rf",
        required_if={"configuration": "one_sided"},
        unit="lc/h",
    ),
    _field(
        "lc_fr",
        "integer",
        "weaving.lc_fr",
        required_if={"configuration": "one_sided"},
        unit="lc/h",
    ),
    _field(
        "lc_rr",
        "integer",
        "weaving.lc_rr",
        required_if={"configuration": "two_sided"},
        unit="lc/h",
    ),
    _field(
        "volume_ff_veh_h",
        "number",
        "weaving.volume_ff",
        required=True,
        unit="veh/h",
    ),
    _field(
        "volume_fr_veh_h",
        "number",
        "weaving.volume_fr",
        required=True,
        unit="veh/h",
    ),
    _field(
        "volume_rf_veh_h",
        "number",
        "weaving.volume_rf",
        required=True,
        unit="veh/h",
    ),
    _field(
        "volume_rr_veh_h",
        "number",
        "weaving.volume_rr",
        required=True,
        unit="veh/h",
    ),
    _field(
        "peak_hour_factor",
        "number",
        "weaving.peak_hour_factor",
        required=True,
        unit="PHF",
    ),
    _field(
        "interchange_density",
        "number",
        "weaving.interchange_density",
        required=True,
        unit_metric="per km",
        unit_imperial="per mi",
    ),
    _field(
        "ffs_source",
        "choice",
        "weaving.ffs_source",
        required=True,
        options=("measured", "estimated"),
    ),
    _field(
        "free_flow_speed",
        "number",
        "weaving.free_flow_speed",
        required_if={"ffs_source": "measured"},
        unit_metric="km/h",
        unit_imperial="mph",
    ),
    _field(
        "base_free_flow_speed",
        "number",
        "weaving.base_free_flow_speed",
        required_if={"ffs_source": "estimated"},
        unit_metric="km/h",
        unit_imperial="mph",
    ),
    _field(
        "lane_width",
        "number",
        "weaving.lane_width",
        required_if={"ffs_source": "estimated"},
        unit_metric="m",
        unit_imperial="ft",
    ),
    _field(
        "right_side_lateral_clearance",
        "number",
        "weaving.right_side_lateral_clearance",
        required_if={"ffs_source": "estimated"},
        unit_metric="m",
        unit_imperial="ft",
    ),
    _field(
        "total_ramp_density",
        "number",
        "weaving.total_ramp_density",
        required_if={"ffs_source": "estimated"},
        unit_metric="per km",
        unit_imperial="per mi",
    ),
    _field(
        "heavy_vehicle_percent",
        "number",
        "weaving.heavy_vehicle_percent",
        required=True,
        unit="%",
    ),
    _field(
        "terrain_type",
        "choice",
        "weaving.terrain_type",
        required=True,
        options=("level", "rolling"),
    ),
)


RAMP_FIELDS: tuple[dict[str, Any], ...] = (
    _field(
        "freeway_lanes",
        "integer",
        "ramp.freeway_lanes",
        required=True,
        unit="lanes",
    ),
    _field(
        "auxiliary_lane_length",
        "number",
        "ramp.auxiliary_lane_length",
        required=True,
        unit_metric="m",
        unit_imperial="ft",
    ),
    _field(
        "freeway_demand_veh_h",
        "number",
        "ramp.freeway_demand",
        required=True,
        unit="veh/h",
    ),
    _field(
        "ramp_demand_veh_h",
        "number",
        "ramp.ramp_demand",
        required=True,
        unit="veh/h",
    ),
    _field(
        "freeway_peak_hour_factor",
        "number",
        "ramp.freeway_peak_hour_factor",
        required=True,
        unit="PHF",
    ),
    _field(
        "ramp_peak_hour_factor",
        "number",
        "ramp.ramp_peak_hour_factor",
        required=True,
        unit="PHF",
    ),
    _field(
        "freeway_heavy_vehicle_percent",
        "number",
        "ramp.freeway_heavy_vehicle_percent",
        required=True,
        unit="%",
    ),
    _field(
        "ramp_heavy_vehicle_percent",
        "number",
        "ramp.ramp_heavy_vehicle_percent",
        required=True,
        unit="%",
    ),
    _field(
        "terrain_type",
        "choice",
        "ramp.terrain_type",
        required=True,
        options=("level", "rolling"),
    ),
    _field(
        "ffs_source",
        "choice",
        "ramp.ffs_source",
        required=True,
        options=("measured", "estimated"),
    ),
    _field(
        "free_flow_speed",
        "number",
        "ramp.free_flow_speed",
        required_if={"ffs_source": "measured"},
        unit_metric="km/h",
        unit_imperial="mph",
    ),
    _field(
        "base_free_flow_speed",
        "number",
        "ramp.base_free_flow_speed",
        required_if={"ffs_source": "estimated"},
        unit_metric="km/h",
        unit_imperial="mph",
    ),
    _field(
        "lane_width",
        "number",
        "ramp.lane_width",
        required_if={"ffs_source": "estimated"},
        unit_metric="m",
        unit_imperial="ft",
    ),
    _field(
        "right_side_lateral_clearance",
        "number",
        "ramp.right_side_lateral_clearance",
        required_if={"ffs_source": "estimated"},
        unit_metric="m",
        unit_imperial="ft",
    ),
    _field(
        "total_ramp_density",
        "number",
        "ramp.total_ramp_density",
        required_if={"ffs_source": "estimated"},
        unit_metric="per km",
        unit_imperial="per mi",
    ),
    _field(
        "ramp_ffs",
        "number",
        "ramp.ramp_ffs",
        required=True,
        unit_metric="km/h",
        unit_imperial="mph",
    ),
    _field(
        "speed_adjustment_factor_source",
        "choice",
        "ramp.speed_adjustment_factor_source",
        required=True,
        options=(
            "hcm_base_conditions",
            "project_local_calibration",
        ),
    ),
    _field(
        "capacity_adjustment_factor_source",
        "choice",
        "ramp.capacity_adjustment_factor_source",
        required=True,
        options=(
            "hcm_base_conditions",
            "project_local_calibration",
        ),
    ),
    _field(
        "geometry_source",
        "choice",
        "ramp.geometry_source",
        required=True,
        options=("chapter_28_example", "user_entered"),
    ),
    _field(
        "geometry_notes",
        "text",
        "ramp.geometry_notes",
        required=True,
    ),
)


PHASE3_GROUPS: dict[str, tuple[dict[str, Any], ...]] = {
    "two_lane_segment": (
        {"key": "segment", "label_key": "two_lane_segment.group_segment", "field_keys": ["segment_type", "terrain_type", "horizontal_alignment", "segment_length", "posted_speed"]},
        {"key": "traffic", "label_key": "two_lane_segment.group_traffic", "field_keys": ["analysis_direction_volume", "opposing_direction_volume", "peak_hour_factor", "heavy_vehicle_percent", "grade_percent"]},
        {"key": "roadway", "label_key": "two_lane_segment.group_roadway", "field_keys": ["lane_width", "shoulder_width", "access_point_density", "horizontal_alignment_subsegments"]},
    ),
    "basic_freeway_segment": (
        {"key": "traffic", "label_key": "basic_freeway.group_traffic", "field_keys": ["number_of_lanes", "segment_length", "demand_volume_veh_h", "peak_hour_factor"]},
        {"key": "free_flow", "label_key": "basic_freeway.group_free_flow", "field_keys": ["ffs_source", "free_flow_speed", "base_free_flow_speed", "lane_width", "right_side_lateral_clearance", "total_ramp_density"]},
        {"key": "heavy_vehicles", "label_key": "basic_freeway.group_heavy_vehicles", "field_keys": ["heavy_vehicle_percent", "terrain_type", "truck_mix", "grade_percent", "pce_mode", "passenger_car_equivalent", "passenger_car_equivalent_provenance"]},
        {"key": "provenance", "label_key": "basic_freeway.group_provenance", "field_keys": ["driver_population_category", "speed_adjustment_factor", "capacity_adjustment_factor", "speed_adjustment_factor_source", "capacity_adjustment_factor_source"]},
    ),
    "weaving_segment": (
        {"key": "geometry", "label_key": "weaving.group_geometry", "field_keys": ["configuration", "segment_length", "number_of_lanes", "number_of_weaving_lanes", "entry_side", "exit_side", "option_fr", "option_rf", "option_rr", "reachable_ff", "reachable_fr", "reachable_rf", "reachable_rr", "nwl_basis", "lane_change_basis", "lc_rf", "lc_fr", "lc_rr"]},
        {"key": "movements", "label_key": "weaving.group_movements", "field_keys": ["volume_ff_veh_h", "volume_fr_veh_h", "volume_rf_veh_h", "volume_rr_veh_h", "peak_hour_factor", "interchange_density"]},
        {"key": "free_flow", "label_key": "weaving.group_free_flow", "field_keys": ["ffs_source", "free_flow_speed", "base_free_flow_speed", "lane_width", "right_side_lateral_clearance", "total_ramp_density"]},
        {"key": "heavy_vehicles", "label_key": "weaving.group_heavy_vehicles", "field_keys": ["heavy_vehicle_percent", "terrain_type"]},
    ),
    "merge_segment": (
        {"key": "geometry", "label_key": "ramp.group_geometry_merge", "field_keys": ["freeway_lanes", "auxiliary_lane_length", "geometry_source", "geometry_notes"]},
        {"key": "traffic", "label_key": "ramp.group_traffic", "field_keys": ["freeway_demand_veh_h", "ramp_demand_veh_h", "freeway_peak_hour_factor", "ramp_peak_hour_factor", "freeway_heavy_vehicle_percent", "ramp_heavy_vehicle_percent", "terrain_type"]},
        {"key": "free_flow", "label_key": "ramp.group_free_flow", "field_keys": ["ffs_source", "free_flow_speed", "base_free_flow_speed", "lane_width", "right_side_lateral_clearance", "total_ramp_density", "ramp_ffs"]},
        {"key": "provenance", "label_key": "ramp.group_provenance", "field_keys": ["speed_adjustment_factor_source", "capacity_adjustment_factor_source"]},
    ),
    "diverge_segment": (
        {"key": "geometry", "label_key": "ramp.group_geometry_diverge", "field_keys": ["freeway_lanes", "auxiliary_lane_length", "geometry_source", "geometry_notes"]},
        {"key": "traffic", "label_key": "ramp.group_traffic", "field_keys": ["freeway_demand_veh_h", "ramp_demand_veh_h", "freeway_peak_hour_factor", "ramp_peak_hour_factor", "freeway_heavy_vehicle_percent", "ramp_heavy_vehicle_percent", "terrain_type"]},
        {"key": "free_flow", "label_key": "ramp.group_free_flow", "field_keys": ["ffs_source", "free_flow_speed", "base_free_flow_speed", "lane_width", "right_side_lateral_clearance", "total_ramp_density", "ramp_ffs"]},
        {"key": "provenance", "label_key": "ramp.group_provenance", "field_keys": ["speed_adjustment_factor_source", "capacity_adjustment_factor_source"]},
    ),
}


def phase3_fields(method_id: str) -> tuple[dict[str, Any], ...]:
    if method_id == "two_lane_segment":
        return TWO_LANE_SEGMENT_FIELDS
    if method_id == "basic_freeway_segment":
        return BASIC_FREEWAY_FIELDS
    if method_id == "weaving_segment":
        return WEAVING_FIELDS
    if method_id in {"merge_segment", "diverge_segment"}:
        return RAMP_FIELDS
    raise KeyError(method_id)


def phase3_groups(method_id: str) -> tuple[dict[str, Any], ...]:
    return PHASE3_GROUPS[method_id]


def _two_lane_display_from_engine(inputs: Mapping[str, Any], unit_system: str) -> dict[str, Any]:
    metric = unit_system == "metric"
    speed_factor = MILES_TO_KILOMETERS if metric else 1.0
    length_factor = FEET_TO_METERS if metric else 1.0
    density_factor = 1.0 / MILES_TO_KILOMETERS if metric else 1.0
    subsegments = []
    for item in inputs.get("horizontal_alignment_subsegments", []):
        subsegments.append(
            {
                "type": item.get("type", item.get("subsegment_type")),
                "length": float(item["length_ft"]) * length_factor,
                "superelevation_percent": item.get("superelevation_percent"),
                "radius": (
                    None
                    if item.get("radius_ft") is None
                    else float(item["radius_ft"]) * length_factor
                ),
                "central_angle_deg": item.get("central_angle_deg"),
                "horizontal_class": item.get("horizontal_class"),
            }
        )
    return {
        "segment_type": inputs.get("segment_type", "passing_constrained"),
        "terrain_type": "mountainous" if float(inputs.get("grade_percent", 0.0)) else "level",
        "horizontal_alignment": inputs.get("horizontal_alignment", "straight"),
        "segment_length": float(inputs["segment_length_mi"]) * (MILES_TO_KILOMETERS if metric else 1.0),
        "posted_speed": float(inputs["posted_speed_mph"]) * speed_factor,
        "analysis_direction_volume": float(inputs["analysis_direction_volume_veh_h"]),
        "opposing_direction_volume": inputs.get("opposing_direction_volume_veh_h"),
        "peak_hour_factor": float(inputs["peak_hour_factor"]),
        "heavy_vehicle_percent": float(inputs["heavy_vehicle_percent"]),
        "grade_percent": float(inputs.get("grade_percent", 0.0)),
        "lane_width": float(inputs["lane_width_ft"]) * length_factor,
        "shoulder_width": float(inputs["shoulder_width_ft"]) * length_factor,
        "access_point_density": float(inputs["access_point_density_per_mi"]) * density_factor,
        "horizontal_alignment_subsegments": subsegments,
    }


def _two_lane_templates() -> dict[str, dict[str, Any]]:
    fixture = load_packaged_yaml("example_inputs.yaml")
    result: dict[str, dict[str, Any]] = {
        "blank_custom": {
            "template_label": "Blank/custom starting values",
            "template_description": "A valid straight-segment worksheet starter; replace values before release use.",
            "validation_status": "ui_starter_only",
            "displayed_inputs": {},
        }
    }
    result["blank_custom"]["displayed_inputs"] = {
        **manual_defaults("imperial"),
        "segment_type": "passing_constrained",
        "terrain_type": "level",
        "horizontal_alignment": "straight",
        "horizontal_alignment_subsegments": [],
    }
    result["legacy_import"] = {
        "template_label": "Imported legacy worksheet",
        "template_description": "The displayed values are restored from a legacy Project 1.x file.",
        "validation_status": "legacy_import",
        "displayed_inputs": deepcopy(result["blank_custom"]["displayed_inputs"]),
    }
    for case_id in ("TLH-CH15-001", "TLH-CH15-002"):
        case = find_case(fixture, case_id)
        result[case_id] = {
            "template_label": f"{case['source']['example_problem']} starting values",
            "template_description": case["source"]["segment_description"],
            "validation_status": case["validation_status"],
            "displayed_inputs": _two_lane_display_from_engine(case["inputs"], "imperial"),
        }
    return result


def _phase3_template_inputs(method_id: str, template_id: str, unit_system: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if method_id == "two_lane_segment":
        templates = _two_lane_templates()
        if template_id not in templates:
            raise ValueError(f"Unsupported Two-Lane Segment template: {template_id}.")
        item = templates[template_id]
        displayed = (
            {
                **manual_defaults(unit_system),
                "segment_type": "passing_constrained",
                "terrain_type": "level",
                "horizontal_alignment": "straight",
                "horizontal_alignment_subsegments": [],
            }
            if template_id == "blank_custom"
            or template_id == "legacy_import"
            else _two_lane_display_from_engine(
                find_case(load_packaged_yaml("example_inputs.yaml"), template_id)["inputs"],
                unit_system,
            )
        )
        return displayed, item

    if method_id == "basic_freeway_segment":
        options = {"blank_custom": "Blank/custom starting values", **freeway_preset_options()}
        if template_id not in options:
            raise ValueError(f"Unsupported Basic Freeway template: {template_id}.")
        source = load_freeway_preset("BF-CH26-001")
        source["inputs"]["case_id"] = "CUSTOM-BASIC-FREEWAY" if template_id == "blank_custom" else template_id
        item = {
            "template_label": options[template_id],
            "template_description": source["description"],
            "validation_status": "ui_starter_only" if template_id == "blank_custom" else source["validation_status"],
        }
        return freeway_engine_inputs_to_ui(source["inputs"], unit_system), item

    if method_id == "weaving_segment":
        options = weaving_preset_options()
        if template_id not in options:
            raise ValueError(f"Unsupported Weaving template: {template_id}.")
        item = {
            "template_label": options[template_id],
            "template_description": "Explicit Chapter 27 geometry and movement-flow evidence.",
            "validation_status": "ui_starter_only" if template_id == "blank_custom" else "reference_fixture",
        }
        return weaving_preset_ui_inputs(template_id, unit_system), item

    if method_id in {"merge_segment", "diverge_segment"}:
        workflow = "merge" if method_id == "merge_segment" else "diverge"
        options = ramp_preset_options(workflow)
        if template_id not in options:
            raise ValueError(f"Unsupported {workflow} template: {template_id}.")
        item = {
            "template_label": options[template_id],
            "template_description": "Explicit isolated one-lane right-side ramp geometry evidence.",
            "validation_status": "ui_starter_only" if template_id == "blank_custom" else "reference_fixture",
        }
        return ramp_preset_ui_inputs(workflow, template_id, unit_system), item

    raise KeyError(method_id)


def _copy_displayed(values: Mapping[str, Any]) -> dict[str, Any]:
    return deepcopy(dict(values))


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise HCMCalcError(f"{label} must be a finite numeric value.")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise HCMCalcError(f"{label} must be a finite numeric value.") from exc
    if not isfinite(number):
        raise HCMCalcError(f"{label} must be a finite numeric value.")
    return number


def _validate_two_lane_normalized(values: Mapping[str, Any]) -> None:
    allowed_types = {"passing_constrained", "passing_zone", "passing_lane"}
    if values.get("segment_type") not in allowed_types:
        raise UnsupportedScopeError("Unsupported two-lane segment type.")
    if values.get("terrain_type") not in {"level", "mountainous"}:
        raise UnsupportedScopeError("Two-Lane Segment supports level or mountainous terrain.")
    if values.get("horizontal_alignment") not in {"straight", "horizontal_curves"}:
        raise UnsupportedScopeError("Two-Lane Segment supports straight or horizontal-curves alignment.")
    for key in (
        "segment_length_mi",
        "posted_speed_mph",
        "analysis_direction_volume_veh_h",
        "peak_hour_factor",
        "heavy_vehicle_percent",
        "grade_percent",
        "lane_width_ft",
        "shoulder_width_ft",
        "access_point_density_per_mi",
    ):
        _finite(values.get(key), key)
    if values["segment_length_mi"] <= 0 or values["posted_speed_mph"] <= 0:
        raise HCMCalcError("Segment length and posted speed must be greater than zero.")
    if values["analysis_direction_volume_veh_h"] < 0:
        raise HCMCalcError("Analysis-direction volume cannot be negative.")
    if not 0 < values["peak_hour_factor"] <= 1:
        raise HCMCalcError("Peak hour factor must be greater than zero and at most 1.")
    if not 0 <= values["heavy_vehicle_percent"] <= 100:
        raise HCMCalcError("Heavy-vehicle percentage must be between 0 and 100.")
    if not 9 <= values["lane_width_ft"] <= 12:
        raise HCMCalcError("Lane width must be within the supported range of 9 to 12 ft.")
    if not 0 <= values["shoulder_width_ft"] <= 6:
        raise HCMCalcError("Shoulder width must be within the supported range of 0 to 6 ft.")
    if values["access_point_density_per_mi"] < 0:
        raise HCMCalcError("Access-point density cannot be negative.")
    opposing = values.get("opposing_direction_volume_veh_h")
    if opposing is not None:
        _finite(opposing, "opposing_direction_volume_veh_h")
        if opposing < 0:
            raise HCMCalcError("Opposing-direction volume cannot be negative.")
    if values["segment_type"] == "passing_zone" and (opposing is None or opposing <= 0):
        raise HCMCalcError("Passing Zone requires an opposing-direction volume greater than zero.")
    if values["segment_type"] != "passing_zone" and opposing is not None:
        raise HCMCalcError("Opposing-direction volume is accepted only for Passing Zone segments.")
    subsegments = values.get("horizontal_alignment_subsegments", [])
    if not isinstance(subsegments, list):
        raise HCMCalcError("Horizontal alignment subsegments must be an array.")
    if values["horizontal_alignment"] == "straight" and subsegments:
        raise HCMCalcError("Straight alignment cannot include horizontal subsegments.")
    if values["horizontal_alignment"] == "horizontal_curves" and not subsegments:
        raise HCMCalcError("Horizontal curve alignment requires horizontal subsegments.")
    total = 0.0
    for subsegment in subsegments:
        if not isinstance(subsegment, Mapping):
            raise HCMCalcError("Each horizontal subsegment must be an object.")
        if subsegment.get("type") not in {"tangent", "horizontal_curve"}:
            raise HCMCalcError("Horizontal subsegment type must be tangent or horizontal_curve.")
        length = _finite(subsegment.get("length_ft"), "horizontal subsegment length")
        if length <= 0:
            raise HCMCalcError("Horizontal subsegment length must be positive.")
        total += length
        if subsegment["type"] == "horizontal_curve":
            radius = _finite(subsegment.get("radius_ft"), "horizontal curve radius")
            if radius <= 0:
                raise HCMCalcError("Horizontal curve radius must be positive.")
    if subsegments and abs(total - values["segment_length_mi"] * 5280.0) > 1.0:
        raise HCMCalcError("Horizontal subsegment lengths must match the segment length.")


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in {"true", "1", "yes"}:
        return True
    if isinstance(value, str) and value.strip().lower() in {"false", "0", "no"}:
        return False
    raise HCMCalcError("Boolean worksheet values must be true or false.")


class Phase3Workflow:
    """One generic application boundary for a Phase 3 delivered method."""

    def __init__(self, method_id: str) -> None:
        if method_id not in PHASE3_METHOD_IDS:
            raise KeyError(method_id)
        self.method_id = method_id
        from hcmcalc.application.workflows import _definition

        self.definition = _definition(method_id)

    def templates(self) -> dict[str, Any]:
        if self.method_id == "two_lane_segment":
            options = _two_lane_templates()
        elif self.method_id == "basic_freeway_segment":
            options = {
                key: {
                    "template_label": label,
                    "template_description": "Bounded Chapter 12 Basic Freeway worksheet.",
                    "validation_status": "reference_fixture" if key != "blank_custom" else "ui_starter_only",
                }
                for key, label in {"blank_custom": "Blank/custom starting values", **freeway_preset_options()}.items()
            }
        elif self.method_id == "weaving_segment":
            options = {
                key: {
                    "template_label": label,
                    "template_description": "Explicit Chapter 27 geometry and movement-flow evidence.",
                    "validation_status": "reference_fixture" if key != "blank_custom" else "ui_starter_only",
                }
                for key, label in weaving_preset_options().items()
            }
        else:
            workflow = "merge" if self.method_id == "merge_segment" else "diverge"
            options = {
                key: {
                    "template_label": label,
                    "template_description": "Explicit isolated one-lane right-side ramp geometry evidence.",
                    "validation_status": "reference_fixture" if key != "blank_custom" else "ui_starter_only",
                }
                for key, label in ramp_preset_options(workflow).items()
            }
        return {
            "method_id": self.method_id,
            "unit_systems": ["metric", "imperial"],
            "templates": [
                {
                    "template_id": template_id,
                    "label": item["template_label"],
                    "description": item.get("template_description"),
                    "validation_status": item.get("validation_status"),
                }
                for template_id, item in options.items()
            ],
            "fields": [deepcopy(field) for field in phase3_fields(self.method_id)],
            "groups": [deepcopy(group) for group in phase3_groups(self.method_id)],
            "branches": {
                "phase": "phase_3_full_migration",
                "validation_without_calculation": True,
            },
            "scope_notes": [
                "Python remains the sole HCM calculation authority.",
                "Displayed Metric values are converted at the application boundary; engines retain their established native units.",
                "Starting values are bounded fixtures or worksheet starters; they do not broaden the underlying HCM scope.",
            ],
        }

    def starting_values(self, template_id: str, unit_system: str) -> dict[str, Any]:
        from hcmcalc.application.workflows import _json_ready, _normalize_unit_system

        unit = _normalize_unit_system(unit_system)
        try:
            displayed, item = _phase3_template_inputs(self.method_id, template_id, unit)
        except Exception as exc:
            raise self._application_error(str(exc), "invalid_template", "api.invalid_template", {"template_id": template_id}) from exc
        return _json_ready(
            {
                "method_id": self.method_id,
                "template_id": template_id,
                "template_label": item["template_label"],
                "template_description": item.get("template_description"),
                "validation_status": item.get("validation_status"),
                "unit_system": unit,
                "displayed_inputs": displayed,
                "fields": [deepcopy(field) for field in phase3_fields(self.method_id)],
                "groups": [deepcopy(group) for group in phase3_groups(self.method_id)],
                "scope_notes": self.templates()["scope_notes"],
            }
        )

    def _normalized(
        self,
        template_id: str,
        unit_system: str,
        displayed_inputs: Mapping[str, Any],
    ) -> dict[str, Any]:
        from hcmcalc.application.workflows import _normalize_unit_system

        unit = _normalize_unit_system(unit_system)
        if not isinstance(displayed_inputs, Mapping):
            raise self._application_error("displayed_inputs must be an object.", "invalid_input", "api.invalid_input", {"field": "displayed_inputs"})
        values = dict(displayed_inputs)
        try:
            if self.method_id == "two_lane_segment":
                normalized = build_manual_segment_inputs({**values, "unit_system": unit})
                _validate_two_lane_normalized(normalized)
            elif self.method_id == "basic_freeway_segment":
                preset_id = template_id if template_id in freeway_preset_options() else "BF-CH26-001"
                preset = load_freeway_preset(preset_id)["inputs"]
                if template_id == "blank_custom":
                    preset = deepcopy(preset)
                    preset["case_id"] = "CUSTOM-BASIC-FREEWAY"
                normalized = freeway_ui_inputs_to_engine(values, preset, unit)
                parsed = BasicFreewaySegmentInputs.from_mapping(normalized)
                validate_freeway_inputs(parsed)
            elif self.method_id == "weaving_segment":
                normalized = weaving_ui_inputs_to_engine(values, unit)
                parsed = WeavingSegmentInputs.from_mapping(normalized)
                validate_weaving_common(parsed)
                validate_v70_geometry(parsed)
            else:
                workflow = "merge" if self.method_id == "merge_segment" else "diverge"
                normalized = ramp_ui_inputs_to_engine(workflow, values, unit)
                parsed = MergeSegmentInputs.from_mapping(normalized) if workflow == "merge" else DivergeSegmentInputs.from_mapping(normalized)
                validate_merge(parsed) if workflow == "merge" else validate_diverge(parsed)
            return self._json_ready(normalized)
        except self._application_error_type():
            raise
        except Exception as exc:
            code = "unsupported_scope" if isinstance(exc, UnsupportedScopeError) else "invalid_input"
            raise self._application_error(str(exc), code, f"api.{code}") from exc

    def normalized_legacy(
        self,
        *,
        template_id: str,
        unit_system: str,
        displayed_inputs: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Normalize a legacy display payload without executing an engine."""

        if template_id == "legacy_import" and self.method_id != "two_lane_segment":
            raise self._application_error(
                "A released Phase 3 legacy payload must retain its preset/template identity.",
                "invalid_input",
                "api.invalid_input",
            )
        return self._normalized(template_id, unit_system, displayed_inputs)

    def validate(
        self,
        *,
        template_id: str,
        unit_system: str,
        displayed_inputs: Mapping[str, Any],
    ) -> dict[str, Any]:
        from hcmcalc.application.workflows import (
            _error_issue,
            _json_ready,
            _normalize_unit_system,
            _snapshot,
        )
        from hcmcalc.application.workflow_state import ResultPresentationState

        try:
            normalized = self._normalized(template_id, unit_system, displayed_inputs)
        except Exception as exc:
            issue = _error_issue(exc)
            return {
                "method_id": self.method_id,
                "template_id": template_id,
                "unit_system": str(unit_system).lower(),
                "valid": False,
                "ready": False,
                "validation_status": issue["code"],
                "errors": [issue],
                "displayed_inputs": _copy_displayed(displayed_inputs) if isinstance(displayed_inputs, Mapping) else {},
                "normalized_inputs": None,
                "calculation_state": {
                    "presentation_state": ResultPresentationState.INVALID_INPUT.value,
                    "has_result": False,
                    "warnings": [],
                },
            }
        snapshot = _snapshot(
            self.definition,
            template_id=template_id,
            unit_system=_normalize_unit_system(unit_system),
            displayed_inputs=displayed_inputs,
            normalized_inputs=normalized,
        )
        return _json_ready(
            {
                **snapshot,
                "valid": True,
                "ready": True,
                "validation_status": "valid",
                "errors": [],
                "calculation_state": {
                    "presentation_state": ResultPresentationState.PRERUN.value,
                    "calculation_fingerprint": snapshot["calculation_fingerprint"],
                    "has_result": False,
                    "warnings": [],
                },
            }
        )

    def calculate(
        self,
        *,
        template_id: str,
        unit_system: str,
        displayed_inputs: Mapping[str, Any],
    ) -> dict[str, Any]:
        from hcmcalc.application.workflows import (
            _available_metric,
            _capacity_failure,
            _interpretation_mappings,
            _json_ready,
            _normalize_unit_system,
            _result_envelope,
            _snapshot,
        )
        from hcmcalc.application.interpretation import InterpretationCode
        from hcmcalc.application.workflow_state import (
            MetricAvailability,
            READY,
            ResultPresentationState,
            resolve_result_presentation_state,
        )

        unit = _normalize_unit_system(unit_system)
        normalized = self._normalized(template_id, unit, displayed_inputs)
        snapshot = _snapshot(
            self.definition,
            template_id=template_id,
            unit_system=unit,
            displayed_inputs=displayed_inputs,
            normalized_inputs=normalized,
        )
        try:
            if self.method_id == "two_lane_segment":
                engine_result = run_manual_single_segment({**dict(displayed_inputs), "unit_system": unit})
            elif self.method_id == "basic_freeway_segment":
                engine_result = run_manual_freeway(normalized)
            elif self.method_id == "weaving_segment":
                engine_result = run_manual_weaving(normalized)
            else:
                workflow = "merge" if self.method_id == "merge_segment" else "diverge"
                engine_result = run_manual_ramp(workflow, normalized)
            result = result_to_dict(engine_result)
        except Exception as exc:
            code = "unsupported_scope" if isinstance(exc, UnsupportedScopeError) else "invalid_input"
            raise self._application_error(str(exc), code, f"api.{code}") from exc

        outputs = result["outputs"]
        capacity_failure = _capacity_failure(result)
        handoff = (
            outputs.get("support_status") == "hcm_handoff_required"
            or str(outputs.get("scope_status", "")).startswith("hcm_handoff")
            or outputs.get("capacity_status") == "not_evaluated_after_handoff"
        )
        warnings = tuple(result.get("warnings", []))
        state = resolve_result_presentation_state(
            freshness=READY,
            has_result=True,
            warnings=warnings,
            capacity_failure=capacity_failure,
            stopping_or_handoff=handoff,
        )
        metrics = self._metrics(outputs, unit, _available_metric, capacity_failure, handoff)
        answer = {
            "key": "level_of_service",
            "value": outputs.get("level_of_service"),
            "available": outputs.get("level_of_service") is not None,
            "source": self._answer_source(),
        }
        capacity = {
            "status": outputs.get("capacity_status", outputs.get("capacity_check")),
            "failure": capacity_failure,
            "demand_capacity_ratio": outputs.get("demand_capacity_ratio"),
            "source": self._capacity_source(),
        }
        if handoff:
            capacity["failure"] = False
        interpretation_codes: tuple[InterpretationCode, ...] = ()
        if not capacity_failure and not handoff:
            interpretation_codes = (InterpretationCode.CAPACITY_BELOW_LIMIT,)
        if handoff:
            interpretation_codes = (InterpretationCode.WEAVING_HANDOFF,)
        presentation: dict[str, Any] = {
            "answer": answer,
            "metrics": metrics,
            "capacity": capacity,
            "interpretations": _interpretation_mappings(state, warning_codes=interpretation_codes),
            "evidence": {
                "intermediate_values": result.get("intermediate_values", []),
                "source_references": outputs.get("source_references", []),
                "assumptions": result.get("assumptions", []),
                "warnings": list(warnings),
            },
            "workflow": self._workflow_presentation(outputs),
        }
        if handoff:
            presentation["handoff"] = {
                "reason": outputs.get("stopping_handoff_reason"),
                "scope_status": outputs.get("scope_status"),
            }
        audit = self._audit(template_id, normalized, unit, displayed_inputs, engine_result)
        return _result_envelope(
            self.definition,
            snapshot=snapshot,
            result=result,
            state=state,
            presentation=presentation,
            audit=audit,
        )

    def _metrics(self, outputs: Mapping[str, Any], unit: str, factory: Any, capacity_failure: bool, handoff: bool) -> list[dict[str, Any]]:
        unavailable = MetricAvailability.NOT_PREDICTED if capacity_failure or handoff else None
        if self.method_id == "two_lane_segment":
            from hcmcalc.ui.units import display_outputs

            displayed = display_outputs(dict(outputs), unit)
            order = ("follower_density", "average_speed", "percent_followers", "demand_flow_rate", "capacity", "free_flow_speed")
            sources = {
                "follower_density": "HCM Eq. 15-35",
                "average_speed": "HCM Eq. 15-9 through Eq. 15-16",
                "percent_followers": "HCM Eq. 15-17 through Eq. 15-21",
                "demand_flow_rate": "HCM Eq. 15-1",
                "capacity": "HCM Chapter 15 capacity discussion",
                "free_flow_speed": "HCM Eq. 15-2 through Eq. 15-6",
            }
        elif self.method_id == "basic_freeway_segment":
            displayed = freeway_display_outputs(dict(outputs), unit)
            order = ("density", "speed_used_for_density", "adjusted_free_flow_speed", "base_free_flow_speed", "demand_flow_rate", "capacity", "adjusted_capacity")
            sources = {key: "HCM Chapter 12" for key in order}
        elif self.method_id == "weaving_segment":
            displayed = weaving_display_outputs(dict(outputs), unit)
            order = ("mean_speed", "weaving_speed", "nonweaving_speed", "density", "capacity", "demand")
            sources = {key: "HCM Chapter 13" for key in order}
        else:
            displayed = ramp_display_outputs(dict(outputs), unit)
            order = ("density", "ramp_influence_speed", "all_lanes_speed", "governing_capacity", "governing_vc")
            sources = {key: "HCM Chapter 14" for key in order}
        result = []
        for key in order:
            item = displayed[key]
            result.append(
                factory(
                    key,
                    item.get("value"),
                    item.get("unit"),
                    source=sources[key],
                    availability=unavailable,
                    capacity_failure=capacity_failure,
                )
            )
        return result

    def _workflow_presentation(self, outputs: Mapping[str, Any]) -> dict[str, Any]:
        keys = {
            "two_lane_segment": ("segment_type", "horizontal_alignment", "terrain_type"),
            "basic_freeway_segment": ("ffs_source", "terrain_grade_classification", "pce_source", "driver_population_category"),
            "weaving_segment": ("configuration", "scope_status", "capacity_status"),
            "merge_segment": ("geometry_evidence", "capacity_status", "maximum_desirable_influence_flow_exceeded"),
            "diverge_segment": ("geometry_evidence", "capacity_status", "maximum_desirable_influence_flow_exceeded"),
        }[self.method_id]
        return {key: outputs.get(key) for key in keys}

    def _answer_source(self) -> str:
        return {
            "two_lane_segment": "HCM7 Exhibit 15-6",
            "basic_freeway_segment": "HCM7 Chapter 12 LOS thresholds",
            "weaving_segment": "HCM7 Exhibit 13-6",
            "merge_segment": "HCM7 Exhibit 14-3",
            "diverge_segment": "HCM7 Exhibit 14-3",
        }[self.method_id]

    def _capacity_source(self) -> str:
        return {
            "two_lane_segment": "HCM7 Chapter 15 capacity discussion",
            "basic_freeway_segment": "HCM7 Chapter 12 capacity check",
            "weaving_segment": "HCM7 Chapter 13 capacity check",
            "merge_segment": "HCM7 Chapter 14 freeway/ramp capacity checks",
            "diverge_segment": "HCM7 Chapter 14 freeway/ramp capacity checks",
        }[self.method_id]

    def _audit(self, template_id: str, normalized: Mapping[str, Any], unit: str, displayed: Mapping[str, Any], engine_result: Any) -> dict[str, Any]:
        if self.method_id == "basic_freeway_segment":
            return build_manual_freeway_audit_record(template_id, dict(normalized), unit_system=unit, displayed_inputs=dict(displayed), result=engine_result)
        if self.method_id == "weaving_segment":
            from hcmcalc.ui.manual_weaving import build_manual_weaving_audit_record

            return build_manual_weaving_audit_record(template_id, dict(normalized), unit_system=unit, displayed_inputs=dict(displayed), result=engine_result)
        if self.method_id in {"merge_segment", "diverge_segment"}:
            from hcmcalc.ui.manual_ramp_influence import build_manual_ramp_audit_record

            workflow = "merge" if self.method_id == "merge_segment" else "diverge"
            return build_manual_ramp_audit_record(workflow, template_id, dict(normalized), unit_system=unit, displayed_inputs=dict(displayed), result=engine_result)
        outputs = getattr(engine_result, "outputs", {})
        return {
            "calculation_type": "manual_single_segment",
            "method_family": "two_lane_segment",
            "method_version": "hcm7.0",
            "input_contract": self.definition.input_contract,
            "template_id": template_id,
            "unit_system": unit,
            "displayed_inputs": deepcopy(dict(displayed)),
            "normalized_engine_inputs": deepcopy(dict(normalized)),
            "outputs": deepcopy(outputs),
            "assumptions": list(getattr(engine_result, "assumptions", [])),
            "warnings": list(getattr(engine_result, "warnings", [])),
            "limitations": [
                "Single two-lane segment only; no facility-wide passing-lane sequence effects.",
                "Unsupported combinations remain guarded by the qualified Chapter 15 engine.",
            ],
        }

    @staticmethod
    def _json_ready(value: Any) -> Any:
        from hcmcalc.application.workflows import _json_ready

        return _json_ready(value)

    @staticmethod
    def _application_error_type() -> type[ValueError]:
        from hcmcalc.application.workflows import ApplicationWorkflowError

        return ApplicationWorkflowError

    @staticmethod
    def _application_error(message: str, code: str, message_key: str, details: Mapping[str, Any] | None = None) -> ValueError:
        from hcmcalc.application.workflows import ApplicationWorkflowError

        return ApplicationWorkflowError(message, code=code, message_key=message_key, details=details)


def phase3_workflow_for_method(method_id: str) -> Phase3Workflow:
    return Phase3Workflow(method_id)


def normalized_phase3_legacy_inputs(
    method_id: str,
    *,
    template_id: str,
    unit_system: str,
    displayed_inputs: Mapping[str, Any],
) -> dict[str, Any]:
    return Phase3Workflow(method_id).normalized_legacy(
        template_id=template_id,
        unit_system=unit_system,
        displayed_inputs=displayed_inputs,
    )
