"""Validation and scope guardrails for Multilane Basic Segment v0.1."""

from math import isfinite
from numbers import Real
from typing import Any

from hcmcalc.core import HCMCalcError, UnsupportedScopeError

from .models import MultilaneBasicSegmentInputs


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
    "adjusted_free_flow_speed_mph": "user-supplied adjusted free-flow speed",
}

ALLOWED_INPUT_KEYS = set(MultilaneBasicSegmentInputs.__dataclass_fields__)
SUPPORTED_ANALYSIS_TYPES = {"basic_segment", "multilane_basic_segment"}
SUPPORTED_FFS_SOURCES = {"estimated", "measured"}
SUPPORTED_TRUCK_MIX = "default_30_sut_70_tt"


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
    extra_keys = sorted(set(values) - ALLOWED_INPUT_KEYS - set(UNSUPPORTED_SCOPE_KEYS))
    if extra_keys:
        raise UnsupportedScopeError(
            "Multilane Basic Segment v0.1 does not accept unrecognized or "
            "out-of-scope inputs: " + ", ".join(extra_keys) + ".",
            unsupported_reason="unrecognized or out-of-scope inputs",
        )


def validate_inputs(inputs: MultilaneBasicSegmentInputs) -> None:
    """Validate physical values and v0.1 support boundaries."""

    text_fields = {
        "case_id": inputs.case_id,
        "facility_type": inputs.facility_type,
        "analysis_type": inputs.analysis_type,
        "direction": inputs.direction,
        "truck_mix": inputs.truck_mix,
        "median_type": inputs.median_type,
        "ffs_source": inputs.ffs_source,
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
    for name, value in {
        "free_flow_speed_mph": inputs.free_flow_speed_mph,
        "passenger_car_equivalent": inputs.passenger_car_equivalent,
    }.items():
        if value is not None:
            _require_finite_number(name, value)

    if not isinstance(inputs.number_of_lanes, int):
        raise HCMCalcError("number_of_lanes must be an integer.")
    if inputs.number_of_lanes < 2:
        raise HCMCalcError("number_of_lanes must be at least 2.")
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
    if inputs.analysis_type not in SUPPORTED_ANALYSIS_TYPES:
        raise UnsupportedScopeError(
            "Multilane Basic Segment v0.1 supports only analysis_type "
            "'basic_segment'; Basic Freeway, ramp, weaving, merge/diverge, and "
            "facility/corridor analyses are unsupported."
        )
    if inputs.truck_mix != SUPPORTED_TRUCK_MIX:
        raise UnsupportedScopeError(
            "Multilane Basic Segment v0.1 supports only the default 30% SUT / "
            "70% TT truck mix."
        )
    if inputs.ffs_source not in SUPPORTED_FFS_SOURCES:
        raise UnsupportedScopeError(
            "ffs_source must be 'estimated' or 'measured' for Multilane Basic "
            "Segment v0.1."
        )
    if inputs.ffs_source == "measured":
        if inputs.free_flow_speed_mph is None:
            raise HCMCalcError(
                "free_flow_speed_mph is required when ffs_source is 'measured'."
            )
        if inputs.free_flow_speed_mph <= 0:
            raise HCMCalcError("free_flow_speed_mph must be greater than zero.")
    else:
        if inputs.free_flow_speed_mph is not None:
            raise HCMCalcError(
                "free_flow_speed_mph must be omitted when ffs_source is 'estimated'."
            )
        if inputs.number_of_lanes not in {2, 3}:
            raise UnsupportedScopeError(
                "Estimated FFS supports two or three lanes in the analysis direction "
                "because Exhibit 12-22 supplies four- and six-lane tables only."
            )
        if inputs.median_type == "divided":
            raise UnsupportedScopeError(
                "Estimated FFS for divided medians requires an explicit left-side "
                "clearance input, which is not in the canonical v0.1 payload; use measured FFS."
            )
    if inputs.passenger_car_equivalent is None:
        raise UnsupportedScopeError(
            "Internal specific-grade PCE lookup is not implemented; provide a positive "
            "externally selected passenger_car_equivalent with its engineering provenance."
        )
    if inputs.passenger_car_equivalent <= 0:
        raise HCMCalcError("passenger_car_equivalent must be greater than zero.")


def _require_finite_number(name: str, value: Any) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, Real)
        or not isfinite(float(value))
    ):
        raise HCMCalcError(f"{name} must be a finite numeric value.")
