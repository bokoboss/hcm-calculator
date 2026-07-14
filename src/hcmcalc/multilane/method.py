"""HCM7 one-direction Multilane Highway Segment engine (v0.1 contract)."""

from math import isfinite
from typing import Any

from hcmcalc.core import CalculationResult, HCMCalcError, IntermediateValue, UnsupportedScopeError

from .coefficients import (
    FOUR_LANE_TLC_REDUCTIONS_MPH,
    LOS_DENSITY_UPPER_BOUNDS,
    MEDIAN_FFS_REDUCTIONS_MPH,
    MULTILANE_BREAKPOINT_PC_H_LN,
    MULTILANE_DENSITY_AT_CAPACITY_PC_MI_LN,
    MULTILANE_MAX_CAPACITY_PC_H_LN,
    MULTILANE_SPEED_FLOW_EXPONENT,
    SIX_LANE_TLC_REDUCTIONS_MPH,
)
from .models import MultilaneBasicSegmentInputs
from .validation import reject_unsupported_scope_keys, validate_inputs


class MultilaneHighwayLOSMethod:
    """Calculate one supported HCM7 Multilane Highway basic segment."""

    facility_type = "multilane_highway"
    method_name = "hcm7_multilane_los"

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        if not isinstance(inputs, dict):
            raise HCMCalcError("Multilane Basic Segment inputs must be a mapping.")
        reject_unsupported_scope_keys(inputs)
        try:
            parsed = MultilaneBasicSegmentInputs.from_mapping(inputs)
        except (TypeError, ValueError) as exc:
            raise HCMCalcError(str(exc)) from exc
        validate_inputs(parsed)

        adjustments: dict[str, float | None] = {
            "lane_width_adjustment_mph": None,
            "total_lateral_clearance_ft": None,
            "total_lateral_clearance_adjustment_mph": None,
            "median_type_adjustment_mph": None,
            "access_point_adjustment_mph": None,
        }
        base_ffs = parsed.free_flow_speed_mph
        if parsed.ffs_source == "estimated":
            base_ffs = estimate_base_free_flow_speed(parsed.posted_speed_limit_mph)
            adjustments["lane_width_adjustment_mph"] = lane_width_adjustment(parsed.lane_width_ft)
            adjustments["total_lateral_clearance_ft"] = total_lateral_clearance(parsed.roadside_lateral_clearance_ft, parsed.median_type)
            adjustments["total_lateral_clearance_adjustment_mph"] = total_lateral_clearance_adjustment(adjustments["total_lateral_clearance_ft"], parsed.number_of_lanes)
            adjustments["median_type_adjustment_mph"] = median_type_adjustment(parsed.median_type)
            adjustments["access_point_adjustment_mph"] = access_point_adjustment(parsed.access_point_density_per_mi)
            ffs = adjusted_free_flow_speed(base_ffs, *[adjustments[key] for key in ("lane_width_adjustment_mph", "total_lateral_clearance_adjustment_mph", "median_type_adjustment_mph", "access_point_adjustment_mph")])
        else:
            ffs = parsed.free_flow_speed_mph

        capacity = multilane_capacity(ffs)
        pce = parsed.passenger_car_equivalent
        hv_factor = heavy_vehicle_adjustment_factor(parsed.heavy_vehicle_percent, pce)
        flow_rate = demand_flow_rate(parsed.demand_volume_veh_h, parsed.peak_hour_factor, parsed.number_of_lanes, hv_factor)
        exceeds_capacity = flow_rate > capacity
        speed = None if exceeds_capacity else speed_from_flow_rate(flow_rate, ffs, capacity)
        density = None if speed is None else traffic_density(flow_rate, speed)
        los = "F" if exceeds_capacity else level_of_service(density)
        capacity_status = "demand_exceeds_capacity" if exceeds_capacity else "within_capacity"

        assumptions = [
            "One-direction, one-segment uninterrupted-flow Multilane Highway analysis.",
            "Driver population factor is fixed at 1.0; HCM7 provides no Multilane speed-flow adjustment for this factor.",
            "Passenger-car equivalent is externally supplied; truck mix is non-operative in this controlled PCE workflow.",
        ]
        assumptions.append("Free-flow speed is measured or user supplied." if parsed.ffs_source == "measured" else "Estimated base FFS is speed limit +7 mi/h below 50 mi/h and +5 mi/h from 50 through 65 mi/h.")
        warnings = ["Chapter 26 Example Problem 4 is regression evidence, not a calculation branch."]
        if exceeds_capacity:
            warnings.append("Demand exceeds HCM base capacity; no oversaturated speed or density is predicted.")
        notes = [
            "No Basic Freeway, ramp, weaving, merge/diverge, managed-lane, work-zone, reliability, or facility/corridor analysis.",
            "Internal Exhibit 12-26 through 12-28 PCE lookup is unsupported; an externally selected PCE is required.",
            "Estimated divided-median FFS is unsupported because the canonical input has no left-side clearance field.",
        ]
        references = [
            "HCM7 Eq. 12-1; Exhibit 12-6 and Exhibit 12-8",
            "HCM7 Eq. 12-3 and Eq. 12-4; Exhibits 12-20, 12-22, 12-23, and 12-24",
            "HCM7 Eq. 12-7, Eq. 12-9, Eq. 12-10, Eq. 12-11; Exhibit 12-15",
        ]
        outputs = {
            "calculation_type": "multilane_basic_segment_v0_1", "support_status": "bounded_multilane_segment_v0_1", "scope_status": "bounded_multilane_segment_v0_1",
            "input_summary": parsed.__dict__, "ffs_source": parsed.ffs_source, "base_free_flow_speed_mph": base_ffs,
            **adjustments, "adjusted_free_flow_speed_mph": ffs, "capacity_pc_h_ln": capacity,
            "passenger_car_equivalent": pce, "pce_source": "external_user_supplied", "pce_lookup_path": "external_pce_required_no_internal_lookup",
            "effective_grade_for_pce_percent": parsed.grade_percent, "heavy_vehicle_adjustment_factor": hv_factor,
            "driver_population_factor": 1.0, "demand_flow_rate_pc_h_ln": flow_rate, "demand_capacity_ratio": flow_rate / capacity,
            "demand_exceeds_capacity": exceeds_capacity, "capacity_check": capacity_status, "capacity_status": capacity_status,
            "breakpoint_pc_h_ln": MULTILANE_BREAKPOINT_PC_H_LN, "speed_flow_branch": "above_capacity_no_prediction" if exceeds_capacity else ("constant_ffs" if flow_rate <= MULTILANE_BREAKPOINT_PC_H_LN else "decreasing_speed"),
            "mean_speed_mph": speed, "speed_used_for_density_mph": speed, "density_pc_mi_ln": density, "level_of_service": los,
            "source_references": references, "assumptions": assumptions, "warnings": warnings, "unsupported_scope_notes": notes,
        }
        return CalculationResult(self.method_name, self.facility_type, outputs, _intermediate_values(outputs), assumptions, warnings)


def estimate_base_free_flow_speed(posted_speed_limit_mph: float) -> float:
    """HCM7 Exhibit 12-18 Multilane Highway base-FFS defaults."""
    _finite(posted_speed_limit_mph, "posted speed limit")
    if not 0 < posted_speed_limit_mph <= 65:
        raise UnsupportedScopeError("Estimated Multilane base FFS supports posted speeds through 65 mi/h; use measured FFS otherwise.")
    return posted_speed_limit_mph + (7.0 if posted_speed_limit_mph < 50 else 5.0)


def lane_width_adjustment(lane_width_ft: float) -> float:
    _finite(lane_width_ft, "lane width")
    if lane_width_ft >= 12: return 0.0
    if lane_width_ft >= 11: return 1.9
    if lane_width_ft >= 10: return 6.6
    raise UnsupportedScopeError("Exhibit 12-20 does not support lane widths below 10 ft.")


def total_lateral_clearance(roadside_clearance_ft: float, median_type: str) -> float:
    _finite(roadside_clearance_ft, "roadside lateral clearance")
    if roadside_clearance_ft < 0: raise HCMCalcError("Roadside lateral clearance must be nonnegative.")
    if median_type == "divided": raise UnsupportedScopeError("Divided median clearance must be supplied separately.")
    return min(roadside_clearance_ft, 6.0) + 6.0


def total_lateral_clearance_adjustment(total_clearance_ft: float, number_of_lanes: int = 2) -> float:
    """Interpolate HCM7 Exhibit 12-22 four- or six-lane table."""
    _finite(total_clearance_ft, "total lateral clearance")
    table = FOUR_LANE_TLC_REDUCTIONS_MPH if number_of_lanes == 2 else SIX_LANE_TLC_REDUCTIONS_MPH if number_of_lanes == 3 else None
    if table is None: raise UnsupportedScopeError("Exhibit 12-22 supports only two or three lanes in the analysis direction.")
    if not 0 <= total_clearance_ft <= 12: raise HCMCalcError("Total lateral clearance must be between 0 and 12 ft.")
    if total_clearance_ft in table: return table[total_clearance_ft]
    lower, upper = max(x for x in table if x < total_clearance_ft), min(x for x in table if x > total_clearance_ft)
    return round(table[lower] + (table[upper] - table[lower]) * (total_clearance_ft-lower)/(upper-lower), 1)


def median_type_adjustment(median_type: str) -> float:
    try: return MEDIAN_FFS_REDUCTIONS_MPH[median_type]
    except KeyError as exc: raise UnsupportedScopeError(f"Unsupported median type: {median_type!r}.") from exc


def access_point_adjustment(access_point_density_per_mi: float) -> float:
    _finite(access_point_density_per_mi, "access point density")
    if not 0 <= access_point_density_per_mi <= 40: raise UnsupportedScopeError("Exhibit 12-24 access-point density must be between 0 and 40 per mile.")
    return round(0.25 * access_point_density_per_mi, 1)


def adjusted_free_flow_speed(base_ffs: float, lane: float, clearance: float, median: float, access: float) -> float:
    for value, label in ((base_ffs,"base FFS"),(lane,"lane width adjustment"),(clearance,"clearance adjustment"),(median,"median adjustment"),(access,"access adjustment")): _finite(value,label)
    result = base_ffs-lane-clearance-median-access
    if result <= 0: raise HCMCalcError("Adjusted FFS must be greater than zero.")
    return result


def multilane_capacity(adjusted_ffs_mph: float) -> float:
    _finite(adjusted_ffs_mph, "adjusted FFS")
    if not 45 <= adjusted_ffs_mph <= 70: raise UnsupportedScopeError("Multilane FFS must be between 45 and 70 mi/h.")
    return min(1900 + 20*(adjusted_ffs_mph-45), MULTILANE_MAX_CAPACITY_PC_H_LN)


def heavy_vehicle_adjustment_factor(heavy_vehicle_percent: float, pce: float) -> float:
    _finite(heavy_vehicle_percent,"heavy vehicle percentage"); _finite(pce,"passenger car equivalent")
    if not 0 <= heavy_vehicle_percent <= 100: raise HCMCalcError("Heavy vehicle percentage must be between 0 and 100.")
    if pce <= 0: raise HCMCalcError("Passenger car equivalent must be greater than zero.")
    return 1/(1+heavy_vehicle_percent/100*(pce-1))


def demand_flow_rate(volume: float, phf: float, lanes: int, hv_factor: float) -> float:
    for value,label in ((volume,"demand volume"),(phf,"peak hour factor"),(lanes,"lane count"),(hv_factor,"heavy vehicle adjustment factor")): _finite(value,label)
    if volume <= 0: raise HCMCalcError("Demand volume must be greater than zero.")
    if not 0 < phf <= 1: raise HCMCalcError("Peak hour factor must be greater than zero and at most 1.")
    if lanes <= 0 or isinstance(lanes,bool) or int(lanes)!=lanes: raise HCMCalcError("Lane count must be a positive integer.")
    if hv_factor <= 0: raise HCMCalcError("Heavy vehicle adjustment factor must be greater than zero.")
    return volume/(phf*lanes*hv_factor)


def speed_from_flow_rate(flow_rate: float, adjusted_ffs_mph: float, capacity: float) -> float:
    """HCM7 Eq. 12-1 and Exhibit 12-6 Multilane speed-flow curve."""
    for value,label in ((flow_rate,"demand flow rate"),(adjusted_ffs_mph,"adjusted FFS"),(capacity,"capacity")): _finite(value,label)
    if not 0 < flow_rate <= capacity: raise HCMCalcError("Speed-flow prediction requires demand within capacity.")
    if flow_rate <= MULTILANE_BREAKPOINT_PC_H_LN: return adjusted_ffs_mph
    capacity_speed = capacity/MULTILANE_DENSITY_AT_CAPACITY_PC_MI_LN
    return adjusted_ffs_mph-(adjusted_ffs_mph-capacity_speed)*((flow_rate-MULTILANE_BREAKPOINT_PC_H_LN)/(capacity-MULTILANE_BREAKPOINT_PC_H_LN))**MULTILANE_SPEED_FLOW_EXPONENT


def mean_speed_below_breakpoint(flow_rate: float, adjusted_ffs_mph: float) -> float:
    if flow_rate > MULTILANE_BREAKPOINT_PC_H_LN: raise UnsupportedScopeError("Use speed_from_flow_rate for flow above the breakpoint.")
    return speed_from_flow_rate(flow_rate, adjusted_ffs_mph, MULTILANE_MAX_CAPACITY_PC_H_LN)


def traffic_density(flow_rate: float, mean_speed_mph: float) -> float:
    _finite(flow_rate,"demand flow rate"); _finite(mean_speed_mph,"mean speed")
    if flow_rate <= 0 or mean_speed_mph <= 0: raise HCMCalcError("Flow and mean speed must be greater than zero.")
    return flow_rate/mean_speed_mph


def level_of_service(density: float, *, demand_exceeds_capacity: bool = False) -> str:
    if demand_exceeds_capacity: return "F"
    _finite(density,"density")
    if density < 0: raise HCMCalcError("Density must be nonnegative.")
    return next((level for level, upper in LOS_DENSITY_UPPER_BOUNDS if density <= upper), "F")


def _finite(value: float, label: str) -> None:
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not isfinite(float(value)): raise HCMCalcError(f"{label} must be finite.")


def _intermediate_values(outputs: dict[str, Any]) -> list[IntermediateValue]:
    sources = {"base_free_flow_speed_mph":"HCM7 Exhibit 12-18","lane_width_adjustment_mph":"HCM7 Exhibit 12-20","total_lateral_clearance_ft":"HCM7 Eq. 12-4","total_lateral_clearance_adjustment_mph":"HCM7 Exhibit 12-22","median_type_adjustment_mph":"HCM7 Exhibit 12-23","access_point_adjustment_mph":"HCM7 Exhibit 12-24","adjusted_free_flow_speed_mph":"HCM7 Eq. 12-3","capacity_pc_h_ln":"HCM7 Eq. 12-7","passenger_car_equivalent":"externally supplied","pce_source":"PCE provenance","pce_lookup_path":"PCE selection path","heavy_vehicle_adjustment_factor":"HCM7 Eq. 12-10","driver_population_factor":"fixed scope assumption","demand_flow_rate_pc_h_ln":"HCM7 Eq. 12-9","demand_capacity_ratio":"capacity check","capacity_status":"capacity check","breakpoint_pc_h_ln":"HCM7 Exhibit 12-6","speed_flow_branch":"HCM7 Eq. 12-1","mean_speed_mph":"HCM7 Eq. 12-1","density_pc_mi_ln":"HCM7 Eq. 12-11","level_of_service":"HCM7 Exhibit 12-15"}
    return [IntermediateValue(name,outputs[name],source=source) for name,source in sources.items() if outputs[name] is not None]
