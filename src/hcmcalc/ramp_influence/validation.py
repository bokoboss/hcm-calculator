"""Strict validation for ramp influence inputs."""

from math import isfinite
from numbers import Real

from hcmcalc.core import HCMCalcError, UnsupportedScopeError

from .models import BaseRampInfluenceInputs, DivergeSegmentInputs, MergeSegmentInputs


def require_finite(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(float(value)):
        raise HCMCalcError(f"{name} must be a finite numeric value.")


def validate_base(inputs: BaseRampInfluenceInputs, *, facility_type: str) -> None:
    for name in (
        "method_version",
        "case_id",
        "facility_type",
        "analysis_type",
        "ramp_side",
        "terrain_type",
        "ffs_source",
        "speed_adjustment_factor_source",
        "capacity_adjustment_factor_source",
        "adjacent_ramp_context",
    ):
        if not isinstance(getattr(inputs, name), str) or not getattr(inputs, name).strip():
            raise HCMCalcError(f"{name} must be a nonempty string.")
    for name in (
        "analysis_period_minutes",
        "freeway_lanes",
        "ramp_lanes",
        "freeway_demand_veh_h",
        "ramp_demand_veh_h",
        "freeway_peak_hour_factor",
        "ramp_peak_hour_factor",
        "freeway_heavy_vehicle_percent",
        "ramp_heavy_vehicle_percent",
        "ramp_ffs_mph",
        "speed_adjustment_factor",
        "capacity_adjustment_factor",
    ):
        require_finite(name, getattr(inputs, name))
    for name in (
        "free_flow_speed_mph",
        "base_free_flow_speed_mph",
        "lane_width_ft",
        "right_side_lateral_clearance_ft",
        "total_ramp_density_per_mi",
    ):
        value = getattr(inputs, name)
        if value is not None:
            require_finite(name, value)
    if inputs.method_version != "hcm_7_0":
        raise HCMCalcError("HCM 7.0 ramp influence methods require method_version 'hcm_7_0'.")
    if inputs.facility_type != facility_type:
        raise UnsupportedScopeError(f"Only {facility_type} is qualified.")
    if inputs.analysis_type != "operational_analysis":
        raise UnsupportedScopeError("Only operational_analysis is qualified.")
    if inputs.analysis_period_minutes != 15:
        raise UnsupportedScopeError("The qualified ramp influence method uses the peak 15-minute analysis period.")
    if isinstance(inputs.freeway_lanes, bool) or not isinstance(inputs.freeway_lanes, int) or inputs.freeway_lanes not in {2, 3, 4}:
        raise UnsupportedScopeError("freeway_lanes must be 2, 3, or 4 lanes per direction.")
    if inputs.ramp_side != "right":
        raise UnsupportedScopeError("Only right-side ramps are qualified.")
    if isinstance(inputs.ramp_lanes, bool) or not isinstance(inputs.ramp_lanes, int) or inputs.ramp_lanes != 1:
        raise UnsupportedScopeError("Only one-lane ramps are qualified.")
    if inputs.adjacent_ramp_context != "isolated":
        raise UnsupportedScopeError("Adjacent-ramp branches are explicitly deferred and must not be analyzed as isolated.")
    if inputs.terrain_type not in {"level", "rolling"}:
        raise UnsupportedScopeError("Only level and rolling general-terrain heavy-vehicle paths are qualified.")
    if inputs.freeway_demand_veh_h <= 0 or inputs.ramp_demand_veh_h < 0:
        raise HCMCalcError("freeway_demand_veh_h must be positive and ramp_demand_veh_h must be nonnegative.")
    if not 0 < inputs.freeway_peak_hour_factor <= 1 or not 0 < inputs.ramp_peak_hour_factor <= 1:
        raise HCMCalcError("Peak-hour factors must be greater than zero and at most 1.")
    if not 0 <= inputs.freeway_heavy_vehicle_percent <= 100 or not 0 <= inputs.ramp_heavy_vehicle_percent <= 100:
        raise HCMCalcError("Heavy-vehicle percentages must be between 0 and 100.")
    if not 0 < inputs.speed_adjustment_factor <= 1 or not 0 < inputs.capacity_adjustment_factor <= 1:
        raise HCMCalcError("SAF and CAF must be greater than zero and at most 1.")
    if inputs.ramp_ffs_mph <= 0:
        raise HCMCalcError("ramp_ffs_mph must be greater than zero.")
    _validate_ffs(inputs)
    for value in inputs.geometry_evidence.__dict__.values():
        if not isinstance(value, str) or not value.strip():
            raise HCMCalcError("geometry_evidence fields must be nonempty strings.")


def validate_merge(inputs: MergeSegmentInputs) -> None:
    validate_base(inputs, facility_type="freeway_merge_segment")
    require_finite("acceleration_lane_length_ft", inputs.acceleration_lane_length_ft)
    if inputs.acceleration_lane_length_ft < 0:
        raise HCMCalcError("acceleration_lane_length_ft must be nonnegative.")
    if inputs.lane_addition:
        raise UnsupportedScopeError("Lane additions are Chapter 12 handoff cases, not qualified merge calculations.")
    if inputs.major_merge:
        raise UnsupportedScopeError("Major merge areas are outside the qualified Phase 14.2 scope.")
    if inputs.downstream_freeway_demand_veh_h is not None:
        require_finite("downstream_freeway_demand_veh_h", inputs.downstream_freeway_demand_veh_h)


def validate_diverge(inputs: DivergeSegmentInputs) -> None:
    validate_base(inputs, facility_type="freeway_diverge_segment")
    require_finite("deceleration_lane_length_ft", inputs.deceleration_lane_length_ft)
    if inputs.deceleration_lane_length_ft < 0:
        raise HCMCalcError("deceleration_lane_length_ft must be nonnegative.")
    if inputs.lane_drop:
        raise UnsupportedScopeError("Lane drops are Chapter 12 handoff cases, not qualified diverge calculations.")
    if inputs.option_lane:
        raise UnsupportedScopeError("Option-lane diverges are outside the qualified Phase 14.2 scope.")
    if inputs.major_diverge:
        raise UnsupportedScopeError("Major diverge areas are outside the qualified Phase 14.2 scope.")
    if inputs.ramp_demand_veh_h > inputs.freeway_demand_veh_h:
        raise HCMCalcError("off-ramp demand cannot exceed upstream freeway demand.")
    if inputs.continuing_freeway_demand_veh_h is not None:
        require_finite("continuing_freeway_demand_veh_h", inputs.continuing_freeway_demand_veh_h)


def _validate_ffs(inputs: BaseRampInfluenceInputs) -> None:
    estimated = ("base_free_flow_speed_mph", "lane_width_ft", "right_side_lateral_clearance_ft", "total_ramp_density_per_mi")
    if inputs.ffs_source == "measured":
        if inputs.free_flow_speed_mph is None:
            raise HCMCalcError("Measured FFS requires free_flow_speed_mph.")
        if any(getattr(inputs, name) is not None for name in estimated):
            raise HCMCalcError("Measured FFS rejects inactive FFS-estimation fields.")
    elif inputs.ffs_source == "estimated":
        if inputs.free_flow_speed_mph is not None or any(getattr(inputs, name) is None for name in estimated):
            raise HCMCalcError("Estimated FFS requires complete estimation inputs and rejects measured FFS.")
    else:
        raise UnsupportedScopeError("ffs_source must be measured or estimated.")
