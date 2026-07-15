"""Shared source-identical HCM ramp influence calculations."""

from typing import Any

from hcmcalc.freeway.method import (
    basic_freeway_capacity,
    estimated_free_flow_speed,
    general_terrain_passenger_car_equivalent,
    heavy_vehicle_adjustment_factor,
    lane_width_adjustment,
    right_lateral_clearance_adjustment,
)

from .models import BaseRampInfluenceInputs


LOS_DENSITY_UPPER_BOUNDS = (("A", 10.0), ("B", 20.0), ("C", 28.0), ("D", 35.0))


def freeway_ffs(inputs: BaseRampInfluenceInputs) -> float:
    if inputs.ffs_source == "measured":
        assert inputs.free_flow_speed_mph is not None
        ffs = inputs.free_flow_speed_mph
    else:
        ffs = estimated_free_flow_speed(
            inputs.base_free_flow_speed_mph,
            lane_width_adjustment(inputs.lane_width_ft),
            right_lateral_clearance_adjustment(inputs.right_side_lateral_clearance_ft, inputs.freeway_lanes),
            inputs.total_ramp_density_per_mi,
        )
    if not 55.0 <= ffs <= 75.0:
        from hcmcalc.core import UnsupportedScopeError

        raise UnsupportedScopeError("The qualified ramp influence freeway FFS must be from 55 through 75 mi/h.")
    return ffs


def component_flows(inputs: BaseRampInfluenceInputs) -> dict[str, Any]:
    pce = general_terrain_passenger_car_equivalent(inputs.terrain_type)
    freeway_fhv = heavy_vehicle_adjustment_factor(inputs.freeway_heavy_vehicle_percent, pce)
    ramp_fhv = heavy_vehicle_adjustment_factor(inputs.ramp_heavy_vehicle_percent, pce)
    return {
        "passenger_car_equivalent": pce,
        "freeway_heavy_vehicle_adjustment_factor": freeway_fhv,
        "ramp_heavy_vehicle_adjustment_factor": ramp_fhv,
        "freeway_flow_pc_h": inputs.freeway_demand_veh_h / (inputs.freeway_peak_hour_factor * freeway_fhv),
        "ramp_flow_pc_h": inputs.ramp_demand_veh_h / (inputs.ramp_peak_hour_factor * ramp_fhv),
    }


def adjust_v12_reasonableness(freeway_lanes: int, freeway_flow_pc_h: float, v12_pc_h: float) -> tuple[float, str, dict[str, float]]:
    if freeway_lanes == 2:
        return v12_pc_h, "not_applicable_two_lane_direction", {}
    candidates: list[tuple[str, float]] = []
    details: dict[str, float] = {}
    if freeway_lanes == 3:
        outer = freeway_flow_pc_h - v12_pc_h
        details["outer_lane_flow_pc_h_ln"] = outer
        if outer > 2700.0:
            candidates.append(("outer_lane_flow_gt_2700", freeway_flow_pc_h - 2700.0))
        if outer > 1.5 * (v12_pc_h / 2.0):
            candidates.append(("outer_lane_flow_gt_1_5_influence_average", freeway_flow_pc_h / 1.75))
    else:
        outer = (freeway_flow_pc_h - v12_pc_h) / 2.0
        details["outer_lane_flow_pc_h_ln"] = outer
        if outer > 2700.0:
            candidates.append(("outer_lane_flow_gt_2700", freeway_flow_pc_h - 5400.0))
        if outer > 1.5 * (v12_pc_h / 2.0):
            candidates.append(("outer_lane_flow_gt_1_5_influence_average", freeway_flow_pc_h / 2.5))
    if not candidates:
        return v12_pc_h, "original_lane_distribution_reasonable", details
    reason, adjusted = max(candidates, key=lambda item: item[1])
    return adjusted, reason, details


def freeway_capacity_pc_h(ffs_mph: float, lanes: int, caf: float) -> tuple[float, float]:
    unadjusted = basic_freeway_capacity(ffs_mph) * lanes
    return unadjusted, unadjusted * caf


def los_for_density(density: float) -> str:
    for level, bound in LOS_DENSITY_UPPER_BOUNDS:
        if density <= bound:
            return level
    return "E"


def outer_lane_speed_merge(ffs: float, saf: float, outer_flow_pc_h_ln: float) -> float | None:
    if outer_flow_pc_h_ln < 0:
        return None
    adjusted = ffs * saf
    if outer_flow_pc_h_ln < 500:
        return adjusted
    if outer_flow_pc_h_ln <= 2300:
        return adjusted - 0.0036 * (outer_flow_pc_h_ln - 500.0)
    return adjusted - 6.53 - 0.006 * (outer_flow_pc_h_ln - 2300.0)


def outer_lane_speed_diverge(ffs: float, saf: float, outer_flow_pc_h_ln: float) -> float | None:
    if outer_flow_pc_h_ln < 0:
        return None
    adjusted = 1.097 * ffs * saf
    if outer_flow_pc_h_ln < 1000:
        return adjusted
    return adjusted - 0.0039 * (outer_flow_pc_h_ln - 1000.0)
