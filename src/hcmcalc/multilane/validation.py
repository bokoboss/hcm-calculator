"""Validation and scope guardrails for Multilane Basic Segment v0.1."""

from math import isfinite
from numbers import Real
from typing import Any

from hcmcalc.core import HCMCalcError, UnsupportedScopeError

from .models import MultilaneBasicSegmentInputs


SUPPORTED_CASES = {
    "MLH-CH26-004-EB": {
        "direction": "eastbound",
        "grade_percent": -3.5,
        "access_point_density_per_mi": 10.0,
    },
    "MLH-CH26-004-WB": {
        "direction": "westbound",
        "grade_percent": 3.5,
        "access_point_density_per_mi": 0.0,
    },
}

UNSUPPORTED_SCOPE_KEYS = {
    "basic_freeway": "Basic Freeway Segment",
    "ramp": "ramp/merge/diverge",
    "ramps": "ramp/merge/diverge",
    "merge": "ramp/merge/diverge",
    "diverge": "ramp/merge/diverge",
    "merge_diverge": "ramp/merge/diverge",
    "weaving": "weaving",
    "managed_lanes": "managed lanes",
    "work_zone": "work zones",
    "reliability_analysis": "reliability analysis",
    "facility": "facility/corridor workflow",
    "facility_workflow": "facility/corridor workflow",
    "corridor": "facility/corridor workflow",
    "corridor_workflow": "facility/corridor workflow",
}

UNSUPPORTED_INPUT_KEYS = {
    "driver_population_factor": "driver population adjustment",
    "base_free_flow_speed_mph": "user-supplied base free-flow speed",
    "free_flow_speed_mph": "user-supplied free-flow speed",
    "adjusted_free_flow_speed_mph": "user-supplied adjusted free-flow speed",
}


def reject_unsupported_scope_keys(values: dict[str, Any]) -> None:
    """Reject explicit requests for methodologies outside Multilane v0.1."""

    for key, label in UNSUPPORTED_SCOPE_KEYS.items():
        if values.get(key):
            raise UnsupportedScopeError(
                f"Multilane Basic Segment v0.1 does not support {label}.",
                unsupported_reason=label,
            )
    for key, label in UNSUPPORTED_INPUT_KEYS.items():
        if key in values:
            raise UnsupportedScopeError(
                f"Multilane Basic Segment v0.1 does not accept {label}.",
                unsupported_reason=label,
            )


def validate_inputs(inputs: MultilaneBasicSegmentInputs) -> None:
    """Validate physical values, then enforce the Example Problem 4 boundary."""

    text_fields = {
        "case_id": inputs.case_id,
        "facility_type": inputs.facility_type,
        "analysis_type": inputs.analysis_type,
        "direction": inputs.direction,
        "truck_mix": inputs.truck_mix,
        "median_type": inputs.median_type,
    }
    for name, value in text_fields.items():
        if not isinstance(value, str) or not value.strip():
            raise HCMCalcError(f"{name} must be a nonempty string.")

    numeric_fields = {
        "number_of_lanes": inputs.number_of_lanes,
        "segment_length_ft": inputs.segment_length_ft,
        "demand_volume_veh_h": inputs.demand_volume_veh_h,
        "peak_hour_factor": inputs.peak_hour_factor,
        "heavy_vehicle_percent": inputs.heavy_vehicle_percent,
        "grade_percent": inputs.grade_percent,
        "posted_speed_limit_mph": inputs.posted_speed_limit_mph,
        "lane_width_ft": inputs.lane_width_ft,
        "roadside_lateral_clearance_ft": inputs.roadside_lateral_clearance_ft,
        "access_point_density_per_mi": inputs.access_point_density_per_mi,
    }
    for name, value in numeric_fields.items():
        if (
            isinstance(value, bool)
            or not isinstance(value, Real)
            or not isfinite(float(value))
        ):
            raise HCMCalcError(f"{name} must be a finite numeric value.")

    if not isinstance(inputs.number_of_lanes, int):
        raise HCMCalcError("number_of_lanes must be an integer.")
    if inputs.number_of_lanes <= 0:
        raise HCMCalcError("number_of_lanes must be greater than zero.")
    if inputs.segment_length_ft <= 0:
        raise HCMCalcError("segment_length_ft must be greater than zero.")
    if inputs.demand_volume_veh_h <= 0:
        raise HCMCalcError("demand_volume_veh_h must be greater than zero.")
    if not 0 < inputs.peak_hour_factor <= 1:
        raise HCMCalcError("peak_hour_factor must be greater than zero and at most 1.")
    if not 0 <= inputs.heavy_vehicle_percent <= 100:
        raise HCMCalcError("heavy_vehicle_percent must be between 0 and 100.")
    if inputs.posted_speed_limit_mph <= 0:
        raise HCMCalcError("posted_speed_limit_mph must be greater than zero.")
    if inputs.lane_width_ft <= 0:
        raise HCMCalcError("lane_width_ft must be greater than zero.")
    if inputs.roadside_lateral_clearance_ft < 0:
        raise HCMCalcError("roadside_lateral_clearance_ft must be nonnegative.")
    if inputs.access_point_density_per_mi < 0:
        raise HCMCalcError("access_point_density_per_mi must be nonnegative.")
    if inputs.access_point_density_per_mi > 40:
        raise UnsupportedScopeError(
            "Multilane Basic Segment v0.1 does not support access point density "
            "above the implemented Exhibit 12-24 range of 40 per mile."
        )

    if inputs.facility_type != "multilane_highway":
        raise UnsupportedScopeError(
            "Multilane Basic Segment v0.1 supports only facility_type "
            "'multilane_highway'; Basic Freeway Segment inputs are unsupported."
        )
    if inputs.analysis_type != "basic_segment":
        raise UnsupportedScopeError(
            "Multilane Basic Segment v0.1 supports only analysis_type "
            "'basic_segment'; Basic Freeway, ramp, weaving, merge/diverge, and "
            "facility/corridor analyses are unsupported."
        )

    expected = SUPPORTED_CASES.get(inputs.case_id)
    if expected is None:
        raise UnsupportedScopeError(
            "Multilane Basic Segment v0.1 is limited to Chapter 26 Example "
            "Problem 4 eastbound and westbound cases."
        )

    exact_scope = {
        "direction": expected["direction"],
        "number_of_lanes": 2,
        "segment_length_ft": 6600.0,
        "demand_volume_veh_h": 1500.0,
        "peak_hour_factor": 0.90,
        "heavy_vehicle_percent": 6.0,
        "truck_mix": "default_30_sut_70_tt",
        "grade_percent": expected["grade_percent"],
        "posted_speed_limit_mph": 45.0,
        "lane_width_ft": 12.0,
        "roadside_lateral_clearance_ft": 12.0,
        "median_type": "twltl",
        "access_point_density_per_mi": expected["access_point_density_per_mi"],
    }
    mismatches = [
        name
        for name, expected_value in exact_scope.items()
        if getattr(inputs, name) != expected_value
    ]
    if mismatches:
        raise UnsupportedScopeError(
            "Multilane Basic Segment v0.1 is validated only for the exact "
            f"Chapter 26 Example Problem 4 inputs; unsupported fields: {', '.join(mismatches)}.",
            context={"unsupported_fields": mismatches},
        )
