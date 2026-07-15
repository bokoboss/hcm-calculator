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
    "driver_population_factor": "obsolete driver-population factor; use driver_population_category",
}

ALLOWED_INPUT_KEYS = {
    "case_id",
    "facility_type",
    "analysis_type",
    "direction",
    "number_of_lanes",
    "segment_length_mi",
    "demand_volume_veh_h",
    "peak_hour_factor",
    "heavy_vehicle_percent",
    "truck_mix",
    "terrain_type",
    "ffs_source",
    "free_flow_speed_mph",
    "base_free_flow_speed_mph",
    "lane_width_ft",
    "right_side_lateral_clearance_ft",
    "total_ramp_density_per_mi",
    "speed_adjustment_factor",
    "capacity_adjustment_factor",
    "speed_adjustment_factor_source",
    "capacity_adjustment_factor_source",
    "driver_population_category",
    "grade_percent",
    "passenger_car_equivalent",
    "passenger_car_equivalent_provenance",
}

SUPPORTED_ANALYSIS_TYPES = {"basic_segment", "basic_freeway_segment"}
SUPPORTED_FFS_SOURCES = {"measured", "estimated"}
SUPPORTED_TERRAIN_TYPES = {"level", "rolling", "specific_grade"}
SUPPORTED_TRUCK_MIXES = {
    "default_30_sut_70_tt",
    "equal_50_sut_50_tt",
    "majority_70_sut_30_tt",
}
FACTOR_SOURCES = {
    "hcm_base_conditions",
    "chapter_26_driver_population",
    "project_local_calibration",
}
DRIVER_POPULATION_FACTORS = {
    "regular": (1.000, 1.000),
    "mostly_familiar": (0.975, 0.968),
    "balanced": (0.950, 0.939),
    "mostly_unfamiliar": (0.913, 0.898),
    "overwhelmingly_unfamiliar": (0.863, 0.852),
}


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
    extra_keys = sorted(set(values) - ALLOWED_INPUT_KEYS)
    if extra_keys:
        raise UnsupportedScopeError(
            "Basic Freeway Segment v0.1 does not accept unrecognized or "
            "out-of-scope inputs: " + ", ".join(extra_keys) + ".",
            unsupported_reason="unrecognized or out-of-scope inputs",
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
        "speed_adjustment_factor_source": inputs.speed_adjustment_factor_source,
        "capacity_adjustment_factor_source": inputs.capacity_adjustment_factor_source,
        "driver_population_category": inputs.driver_population_category,
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
        "grade_percent": inputs.grade_percent,
        "passenger_car_equivalent": inputs.passenger_car_equivalent,
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
    if inputs.truck_mix not in SUPPORTED_TRUCK_MIXES:
        raise UnsupportedScopeError(
            "Basic Freeway Segment supports only the printed Chapter 12 "
            "30/70, 50/50, or 70/30 SUT/TT truck mixes."
        )
    if inputs.terrain_type not in SUPPORTED_TERRAIN_TYPES:
        raise UnsupportedScopeError(
            "Basic Freeway Segment supports general terrain and printed specific-grade "
            "PCEs; mountainous terrain requires the mixed-flow method."
        )
    if inputs.ffs_source not in SUPPORTED_FFS_SOURCES:
        raise UnsupportedScopeError(
            "ffs_source must be 'measured' or 'estimated' for Basic Freeway Segment v0.1."
        )
    if inputs.speed_adjustment_factor_source not in FACTOR_SOURCES:
        raise HCMCalcError("speed_adjustment_factor_source is not a recognized provenance.")
    if inputs.capacity_adjustment_factor_source not in FACTOR_SOURCES:
        raise HCMCalcError("capacity_adjustment_factor_source is not a recognized provenance.")
    if inputs.driver_population_category not in DRIVER_POPULATION_FACTORS:
        raise UnsupportedScopeError("driver_population_category is outside Exhibit 26-9.")
    expected_saf, expected_caf = DRIVER_POPULATION_FACTORS[inputs.driver_population_category]
    if inputs.driver_population_category != "regular":
        if (inputs.speed_adjustment_factor_source != "chapter_26_driver_population" or
                inputs.capacity_adjustment_factor_source != "chapter_26_driver_population"):
            raise HCMCalcError("Non-regular driver population requires Chapter 26 driver-population SAF and CAF provenance.")
        if abs(inputs.speed_adjustment_factor - expected_saf) > 1e-9 or abs(inputs.capacity_adjustment_factor - expected_caf) > 1e-9:
            raise HCMCalcError("Non-regular driver population SAF and CAF must match Exhibit 26-9.")
    if inputs.passenger_car_equivalent is not None:
        if inputs.passenger_car_equivalent <= 0:
            raise HCMCalcError("passenger_car_equivalent must be greater than zero.")
        if not isinstance(inputs.passenger_car_equivalent_provenance, str) or not inputs.passenger_car_equivalent_provenance.strip():
            raise HCMCalcError("External passenger_car_equivalent requires nonempty provenance.")
    elif inputs.passenger_car_equivalent_provenance is not None:
        raise HCMCalcError("passenger_car_equivalent_provenance is only valid with an external PCE.")
    if inputs.terrain_type == "specific_grade":
        if inputs.grade_percent is None:
            raise HCMCalcError("specific_grade terrain requires grade_percent.")
        if inputs.passenger_car_equivalent is None:
            if not -2.0 <= inputs.grade_percent <= 6.0:
                raise UnsupportedScopeError("Specific-grade PCE supports grades from -2% through 6%.")
            if not 0.125 <= inputs.segment_length_mi <= 1.5:
                raise UnsupportedScopeError("Specific-grade PCE supports printed segment lengths from 0.125 through 1.5 mi.")
    elif inputs.grade_percent is not None:
        raise HCMCalcError("grade_percent is only applicable to terrain_type 'specific_grade'.")

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
