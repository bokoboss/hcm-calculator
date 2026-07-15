"""Strict common validation for versioned weaving inputs."""

from math import isfinite
from numbers import Real

from hcmcalc.core import HCMCalcError, UnsupportedScopeError

from .models import WeavingSegmentInputs


def require_finite(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(float(value)):
        raise HCMCalcError(f"{name} must be a finite numeric value.")


def validate_common(inputs: WeavingSegmentInputs) -> None:
    for name in ("method_version", "case_id", "facility_type", "analysis_type", "direction", "configuration", "ffs_source", "terrain_type", "speed_adjustment_factor_source", "capacity_adjustment_factor_source"):
        if not isinstance(getattr(inputs, name), str) or not getattr(inputs, name).strip():
            raise HCMCalcError(f"{name} must be a nonempty string.")
    for name in ("analysis_period_minutes", "peak_hour_factor", "segment_length_ft", "number_of_lanes", "number_of_weaving_lanes", "volume_ff_veh_h", "volume_fr_veh_h", "volume_rf_veh_h", "volume_rr_veh_h", "interchange_density_per_mi", "heavy_vehicle_percent", "speed_adjustment_factor", "capacity_adjustment_factor"):
        require_finite(name, getattr(inputs, name))
    for name in ("free_flow_speed_mph", "base_free_flow_speed_mph", "lane_width_ft", "right_side_lateral_clearance_ft", "total_ramp_density_per_mi"):
        value = getattr(inputs, name)
        if value is not None:
            require_finite(name, value)
    if inputs.facility_type != "freeway_weaving_segment":
        raise UnsupportedScopeError("Only freeway_weaving_segment is qualified.")
    if inputs.analysis_type != "operational_analysis":
        raise UnsupportedScopeError("Only operational_analysis is qualified.")
    if inputs.analysis_period_minutes != 15:
        raise UnsupportedScopeError("The qualified weaving method uses the peak 15-minute analysis period.")
    if not 0 < inputs.peak_hour_factor <= 1:
        raise HCMCalcError("peak_hour_factor must be greater than zero and at most 1.")
    if inputs.segment_length_ft <= 0 or inputs.interchange_density_per_mi < 0:
        raise HCMCalcError("segment_length_ft must be positive and interchange density nonnegative.")
    if any(getattr(inputs, name) < 0 for name in ("volume_ff_veh_h", "volume_fr_veh_h", "volume_rf_veh_h", "volume_rr_veh_h")):
        raise HCMCalcError("Movement volumes must be nonnegative.")
    if sum((inputs.volume_ff_veh_h, inputs.volume_fr_veh_h, inputs.volume_rf_veh_h, inputs.volume_rr_veh_h)) <= 0:
        raise HCMCalcError("At least one movement volume must be positive.")
    if not 0 <= inputs.heavy_vehicle_percent <= 100:
        raise HCMCalcError("heavy_vehicle_percent must be between 0 and 100.")
    if not 0 < inputs.speed_adjustment_factor <= 1 or not 0 < inputs.capacity_adjustment_factor <= 1:
        raise HCMCalcError("SAF and CAF must be greater than zero and at most 1.")
    if isinstance(inputs.number_of_lanes, bool) or not isinstance(inputs.number_of_lanes, int):
        raise HCMCalcError("number_of_lanes must be an integer.")
    if isinstance(inputs.number_of_weaving_lanes, bool) or not isinstance(inputs.number_of_weaving_lanes, int):
        raise HCMCalcError("number_of_weaving_lanes must be an integer.")
    if inputs.terrain_type not in {"level", "rolling"}:
        raise UnsupportedScopeError("Only general-terrain level and rolling PCE paths are qualified.")
    _validate_ffs(inputs)
    geometry = inputs.geometry
    if geometry.entry_side not in {"left", "right"} or geometry.exit_side not in {"left", "right"}:
        raise HCMCalcError("geometry entry_side and exit_side must be 'left' or 'right'.")
    if not isinstance(geometry.reachable_origin_destination_lanes, dict) or set(geometry.reachable_origin_destination_lanes) != {"ff", "fr", "rf", "rr"}:
        raise HCMCalcError("geometry must explicitly identify reachable lanes for FF, FR, RF, and RR.")
    if any(not isinstance(value, str) or not value.strip() for value in geometry.reachable_origin_destination_lanes.values()):
        raise HCMCalcError("Each geometry reachable-lane basis must be a nonempty string.")
    if not isinstance(geometry.option_lane_status, dict) or set(geometry.option_lane_status) != {"fr", "rf", "rr"} or any(not isinstance(value, bool) for value in geometry.option_lane_status.values()):
        raise HCMCalcError("geometry must explicitly state boolean option-lane status for FR, RF, and RR.")
    if not isinstance(geometry.nwl_basis, str) or not geometry.nwl_basis.strip() or not isinstance(geometry.lane_change_basis, str) or not geometry.lane_change_basis.strip():
        raise HCMCalcError("geometry requires nonempty NWL and lane-change engineering basis.")


def _validate_ffs(inputs: WeavingSegmentInputs) -> None:
    estimated = ("base_free_flow_speed_mph", "lane_width_ft", "right_side_lateral_clearance_ft", "total_ramp_density_per_mi")
    if inputs.ffs_source == "measured":
        if inputs.free_flow_speed_mph is None:
            raise HCMCalcError("Measured FFS requires free_flow_speed_mph.")
        if any(getattr(inputs, name) is not None for name in estimated):
            raise HCMCalcError("Measured FFS rejects inactive FFS-estimation fields.")
    elif inputs.ffs_source == "estimated":
        if inputs.free_flow_speed_mph is not None or any(getattr(inputs, name) is None for name in estimated):
            raise HCMCalcError("Estimated FFS requires its complete geometry fields and rejects measured FFS.")
    else:
        raise UnsupportedScopeError("ffs_source must be measured or estimated.")
