"""Validation and scope guardrails for Basic Freeway Segment v0.1."""

from math import isfinite
from numbers import Real
from typing import Any

from hcmcalc.core import HCMCalcError, UnsupportedScopeError

from .models import BasicFreewaySegmentInputs


UNSUPPORTED_SCOPE_KEYS = {
    "multilane_highway": "Multilane Highway Segment",
    "multilane": "Multilane Highway Segment",
    "ramp": "ramp/merge/diverge",
    "ramps": "ramp/merge/diverge",
    "merge": "ramp/merge/diverge",
    "diverge": "ramp/merge/diverge",
    "merge_diverge": "ramp/merge/diverge",
    "weaving": "weaving",
    "managed_lane": "managed lanes",
    "managed_lanes": "managed lanes",
    "work_zone": "work zones",
    "work_zones": "work zones",
    "reliability": "reliability analysis",
    "reliability_analysis": "reliability analysis",
    "facility": "facility/corridor workflow",
    "facility_workflow": "facility/corridor workflow",
    "corridor": "facility/corridor workflow",
    "corridor_workflow": "facility/corridor workflow",
}

UNSUPPORTED_INPUT_KEYS = {
    "access_point_density_per_mi": "Multilane Highway access point density",
    "median_type": "Multilane Highway median adjustment",
    "total_lateral_clearance_ft": "Multilane Highway total lateral clearance",
    "left_side_lateral_clearance_ft": "Multilane Highway left-side lateral clearance",
    "grade_percent": "specific grade PCE branch",
}

SUPPORTED_ANALYSIS_TYPES = {"basic_segment", "basic_freeway_segment"}
SUPPORTED_FFS_SOURCES = {"measured", "estimated"}
SUPPORTED_TERRAIN_TYPES = {"level", "rolling"}
SUPPORTED_TRUCK_MIX = "default_30_sut_70_tt"


def reject_unsupported_scope_keys(values: dict[str, Any]) -> None:
    """Reject explicit requests for methodologies outside Basic Freeway v0.1."""

    for key, label in UNSUPPORTED_SCOPE_KEYS.items():
        if values.get(key):
            raise UnsupportedScopeError(
                f"Basic Freeway Segment v0.1 does not support {label}.",
                unsupported_reason=label,
            )
    for key, label in UNSUPPORTED_INPUT_KEYS.items():
        if key in values:
            raise UnsupportedScopeError(
                f"Basic Freeway Segment v0.1 does not accept {label}.",
                unsupported_reason=label,
            )


def validate_inputs(inputs: BasicFreewaySegmentInputs) -> None:
    """Validate physical values and v0.1 support boundaries."""

    text_fields = {
        "case_id": inputs.case_id,
        "facility_type": inputs.facility_type,
        "analysis_type": inputs.analysis_type,
        "direction": inputs.direction,
        "truck_mix": inputs.truck_mix,
        "terrain_type": inputs.terrain_type,
        "ffs_source": inputs.ffs_source,
    }
    for name, value in text_fields.items():
        if not isinstance(value, str) or not value.strip():
            raise HCMCalcError(f"{name} must be a nonempty string.")

    numeric_fields = {
        "number_of_lanes": inputs.number_of_lanes,
        "segment_length_mi": inputs.segment_length_mi,
        "demand_volume_veh_h": inputs.demand_volume_veh_h,
        "peak_hour_factor": inputs.peak_hour_factor,
        "heavy_vehicle_percent": inputs.heavy_vehicle_percent,
        "speed_adjustment_factor": inputs.speed_adjustment_factor,
        "capacity_adjustment_factor": inputs.capacity_adjustment_factor,
    }
    for name, value in numeric_fields.items():
        _require_finite_number(name, value)

    optional_numeric_fields = {
        "free_flow_speed_mph": inputs.free_flow_speed_mph,
        "base_free_flow_speed_mph": inputs.base_free_flow_speed_mph,
        "lane_width_ft": inputs.lane_width_ft,
        "right_side_lateral_clearance_ft": inputs.right_side_lateral_clearance_ft,
        "total_ramp_density_per_mi": inputs.total_ramp_density_per_mi,
    }
    for name, value in optional_numeric_fields.items():
        if value is not None:
            _require_finite_number(name, value)

    if not isinstance(inputs.number_of_lanes, int):
        raise HCMCalcError("number_of_lanes must be an integer.")
    if inputs.number_of_lanes < 2:
        raise UnsupportedScopeError(
            "Basic Freeway Segment v0.1 supports at least two lanes in the analysis direction."
        )
    if inputs.segment_length_mi <= 0:
        raise HCMCalcError("segment_length_mi must be greater than zero.")
    if inputs.demand_volume_veh_h <= 0:
        raise HCMCalcError("demand_volume_veh_h must be greater than zero.")
    if not 0 < inputs.peak_hour_factor <= 1:
        raise HCMCalcError("peak_hour_factor must be greater than zero and at most 1.")
    if not 0 <= inputs.heavy_vehicle_percent <= 100:
        raise HCMCalcError("heavy_vehicle_percent must be between 0 and 100.")
    if not 0 < inputs.speed_adjustment_factor <= 1:
        raise HCMCalcError(
            "speed_adjustment_factor must be greater than zero and at most 1."
        )
    if not 0 < inputs.capacity_adjustment_factor <= 1:
        raise HCMCalcError(
            "capacity_adjustment_factor must be greater than zero and at most 1."
        )

    if inputs.facility_type != "basic_freeway":
        raise UnsupportedScopeError(
            "Basic Freeway Segment v0.1 supports only facility_type 'basic_freeway'."
        )
    if inputs.analysis_type not in SUPPORTED_ANALYSIS_TYPES:
        raise UnsupportedScopeError(
            "Basic Freeway Segment v0.1 supports only one-segment uninterrupted-flow "
            "basic segment analysis."
        )
    if inputs.truck_mix != SUPPORTED_TRUCK_MIX:
        raise UnsupportedScopeError(
            "Basic Freeway Segment v0.1 supports only the Chapter 12 default "
            "30% SUT / 70% TT truck mix for general-terrain PCEs."
        )
    if inputs.terrain_type not in SUPPORTED_TERRAIN_TYPES:
        raise UnsupportedScopeError(
            "Basic Freeway Segment v0.1 supports only general-terrain level and "
            "rolling PCEs; specific grades and mountainous terrain are unsupported."
        )
    if inputs.ffs_source not in SUPPORTED_FFS_SOURCES:
        raise UnsupportedScopeError(
            "ffs_source must be 'measured' or 'estimated' for Basic Freeway Segment v0.1."
        )

    if inputs.ffs_source == "measured":
        if inputs.free_flow_speed_mph is None:
            raise HCMCalcError(
                "free_flow_speed_mph is required when ffs_source is 'measured'."
            )
        _reject_present_estimation_fields(inputs)
    else:
        if inputs.free_flow_speed_mph is not None:
            raise HCMCalcError(
                "free_flow_speed_mph must be omitted when ffs_source is 'estimated'."
            )
        missing_estimation = [
            name
            for name in (
                "base_free_flow_speed_mph",
                "lane_width_ft",
                "right_side_lateral_clearance_ft",
                "total_ramp_density_per_mi",
            )
            if getattr(inputs, name) is None
        ]
        if missing_estimation:
            raise HCMCalcError(
                "Estimated FFS requires: " + ", ".join(missing_estimation) + "."
            )
        if inputs.base_free_flow_speed_mph <= 0:
            raise HCMCalcError("base_free_flow_speed_mph must be greater than zero.")
        if inputs.lane_width_ft < 10:
            raise UnsupportedScopeError(
                "Exhibit 12-20 does not support lane widths below 10 ft."
            )
        if inputs.right_side_lateral_clearance_ft < 0:
            raise HCMCalcError("right_side_lateral_clearance_ft must be nonnegative.")
        if inputs.right_side_lateral_clearance_ft > 10:
            raise UnsupportedScopeError(
                "Basic Freeway Segment v0.1 supports right-side lateral clearance "
                "within the Chapter 12 required-data range of 0 to 10 ft."
            )
        if not 0 <= inputs.total_ramp_density_per_mi <= 6:
            raise UnsupportedScopeError(
                "Basic Freeway Segment v0.1 supports total ramp density from 0 to 6 ramps/mi."
            )


def _reject_present_estimation_fields(inputs: BasicFreewaySegmentInputs) -> None:
    present = [
        name
        for name in (
            "base_free_flow_speed_mph",
            "lane_width_ft",
            "right_side_lateral_clearance_ft",
            "total_ramp_density_per_mi",
        )
        if getattr(inputs, name) is not None
    ]
    if present:
        raise HCMCalcError(
            "Measured FFS does not use geometric FFS estimation fields: "
            + ", ".join(present)
            + "."
        )


def _require_finite_number(name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(float(value)):
        raise HCMCalcError(f"{name} must be a finite numeric value.")
