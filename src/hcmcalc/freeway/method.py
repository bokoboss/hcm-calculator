"""HCM7 Chapter 12 Basic Freeway Segment engine v0.1."""

from dataclasses import asdict
from math import isfinite
from typing import Any

from hcmcalc.core import (
    CalculationResult,
    HCMCalcError,
    IntermediateValue,
    UnsupportedScopeError,
)

from .coefficients import (
    FREEWAY_DENSITY_AT_CAPACITY_PC_MI_LN,
    FREEWAY_MAX_CAPACITY_PC_H_LN,
    FREEWAY_MAX_FFS_MPH,
    FREEWAY_MIN_FFS_MPH,
    FREEWAY_SPEED_FLOW_EXPONENT,
    GENERAL_TERRAIN_PCE,
    LOS_DENSITY_UPPER_BOUNDS,
    RIGHT_LATERAL_CLEARANCE_REDUCTIONS_MPH,
)
from .models import BasicFreewaySegmentInputs
from .validation import reject_unsupported_scope_keys, validate_inputs


class BasicFreewaySegmentMethod:
    """Run one-direction, one-segment Basic Freeway Segment calculations."""

    facility_type = "basic_freeway"
    method_name = "hcm7_basic_freeway_segment"

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        """Calculate an auditable Basic Freeway Segment result."""

        if not isinstance(inputs, dict):
            raise HCMCalcError("Basic Freeway Segment inputs must be a mapping.")
        reject_unsupported_scope_keys(inputs)
        try:
            parsed = BasicFreewaySegmentInputs.from_mapping(inputs)
        except (TypeError, ValueError) as exc:
            raise HCMCalcError(str(exc)) from exc
        validate_inputs(parsed)

        lane_adjustment = None
        right_clearance_adjustment = None
        ramp_density_adjustment = None
        base_free_flow_speed = parsed.free_flow_speed_mph
        if parsed.ffs_source == "estimated":
            lane_adjustment = lane_width_adjustment(parsed.lane_width_ft)
            right_clearance_adjustment = right_lateral_clearance_adjustment(
                parsed.right_side_lateral_clearance_ft, parsed.number_of_lanes
            )
            ramp_density_adjustment = total_ramp_density_adjustment(
                parsed.total_ramp_density_per_mi
            )
            base_free_flow_speed = estimated_free_flow_speed(
                parsed.base_free_flow_speed_mph,
                lane_adjustment,
                right_clearance_adjustment,
                parsed.total_ramp_density_per_mi,
            )

        adjusted_ffs = adjusted_free_flow_speed(
            base_free_flow_speed, parsed.speed_adjustment_factor
        )
        capacity = basic_freeway_capacity(adjusted_ffs)
        adjusted_capacity = adjusted_capacity_pc_h_ln(
            capacity, parsed.capacity_adjustment_factor
        )
        breakpoint = breakpoint_flow_rate(
            adjusted_ffs, parsed.capacity_adjustment_factor
        )
        pce = general_terrain_passenger_car_equivalent(parsed.terrain_type)
        hv_factor = heavy_vehicle_adjustment_factor(parsed.heavy_vehicle_percent, pce)
        driver_population_factor = 1.0
        flow_rate = demand_flow_rate(
            parsed.demand_volume_veh_h,
            parsed.peak_hour_factor,
            parsed.number_of_lanes,
            hv_factor,
        )
        demand_exceeds_capacity = flow_rate > adjusted_capacity
        speed = speed_from_flow_rate(flow_rate, adjusted_ffs, breakpoint, adjusted_capacity)
        density = traffic_density(flow_rate, speed)
        _validate_computed_output(speed, "computed speed")
        _validate_computed_output(density, "computed density", allow_zero=True)
        los = level_of_service(density, demand_exceeds_capacity=demand_exceeds_capacity)

        warnings = [
            "Basic Freeway Segment v0.1 is validated only against Chapter 26 "
            "Example Problem 1 for the supported one-segment operational path."
        ]
        if demand_exceeds_capacity:
            warnings.append(
                "Demand flow rate exceeds adjusted capacity; LOS is F and speed is capped "
                "at the Chapter 12 density-at-capacity point for audit continuity."
            )
        assumptions = [
            "One-direction, one-segment uninterrupted-flow Basic Freeway Segment analysis.",
            "Driver population consists of regular users; driver population factor = 1.0.",
            "General-purpose lanes only; no ramps, weaving, merge/diverge, managed lanes, work zones, reliability, or facility workflow.",
            "Heavy-vehicle PCE uses Chapter 12 general-terrain level/rolling defaults only.",
        ]
        if parsed.speed_adjustment_factor == 1.0:
            assumptions.append("Base speed adjustment factor SAF = 1.0.")
        if parsed.capacity_adjustment_factor == 1.0:
            assumptions.append("Base capacity adjustment factor CAF = 1.0.")

        unsupported_scope_notes = [
            "No Multilane Highway Segment calculations.",
            "No ramp, weaving, merge/diverge, managed-lane, work-zone, reliability, or facility/corridor analysis.",
            "No specific-grade or mountainous-terrain PCE tables in v0.1.",
            "No UI, Save/Load, or export/reporting integration.",
        ]
        source_references = [
            "HCM7 Chapter 12 Step 1 and Exhibit 12-18",
            "HCM7 Eq. 12-1 and Exhibit 12-6",
            "HCM7 Eq. 12-2; Exhibits 12-20 and 12-21",
            "HCM7 Eq. 12-5, Eq. 12-6, Eq. 12-8",
            "HCM7 Eq. 12-9 and Eq. 12-10; Exhibit 12-25",
            "HCM7 Eq. 12-11; Exhibit 12-15",
            "HCM7 Chapter 26 Freeway and Multilane Highway Example Problem 1",
        ]
        outputs = {
            "calculation_type": "basic_freeway_segment_v0_1",
            "support_status": "chapter_26_example_validated_v0_1",
            "scope_status": "supported_basic_freeway_segment_v0_1",
            "input_summary": asdict(parsed),
            "ffs_source": parsed.ffs_source,
            "base_free_flow_speed_mph": base_free_flow_speed,
            "lane_width_adjustment_mph": lane_adjustment,
            "right_lateral_clearance_adjustment_mph": right_clearance_adjustment,
            "total_ramp_density_adjustment_mph": ramp_density_adjustment,
            "speed_adjustment_factor": parsed.speed_adjustment_factor,
            "adjusted_free_flow_speed_mph": adjusted_ffs,
            "capacity_pc_h_ln": capacity,
            "capacity_adjustment_factor": parsed.capacity_adjustment_factor,
            "adjusted_capacity_pc_h_ln": adjusted_capacity,
            "breakpoint_flow_rate_pc_h_ln": breakpoint,
            "passenger_car_equivalent": pce,
            "heavy_vehicle_adjustment_factor": hv_factor,
            "driver_population_factor": driver_population_factor,
            "demand_flow_rate_pc_h_ln": flow_rate,
            "demand_capacity_ratio": flow_rate / adjusted_capacity,
            "demand_exceeds_capacity": demand_exceeds_capacity,
            "capacity_check": (
                "demand_exceeds_capacity" if demand_exceeds_capacity else "within_capacity"
            ),
            "mean_speed_mph": speed,
            "speed_used_for_density_mph": speed,
            "density_pc_mi_ln": density,
            "level_of_service": los,
            "source_references": source_references,
            "assumptions": assumptions,
            "warnings": warnings,
            "unsupported_scope_notes": unsupported_scope_notes,
        }
        return CalculationResult(
            method=self.method_name,
            facility_type=self.facility_type,
            outputs=outputs,
            intermediate_values=_intermediate_values(outputs),
            assumptions=assumptions,
            warnings=warnings,
        )


def lane_width_adjustment(lane_width_ft: float) -> float:
    """HCM7 Exhibit 12-20 lane-width adjustment."""

    _finite(lane_width_ft, "lane width")
    if lane_width_ft >= 12.0:
        return 0.0
    if lane_width_ft >= 11.0:
        return 1.9
    if lane_width_ft >= 10.0:
        return 6.6
    raise UnsupportedScopeError("Exhibit 12-20 does not support lane widths below 10 ft.")


def right_lateral_clearance_adjustment(clearance_ft: float, lanes: int) -> float:
    """Interpolate HCM7 Exhibit 12-21 for Basic Freeway Segments."""

    _finite(clearance_ft, "right-side lateral clearance")
    _finite(lanes, "lane count")
    if clearance_ft < 0:
        raise HCMCalcError("Right-side lateral clearance must be nonnegative.")
    if lanes < 2 or isinstance(lanes, bool) or int(lanes) != lanes:
        raise HCMCalcError("Lane count must be an integer of at least 2.")
    if clearance_ft >= 6:
        return 0.0
    table = RIGHT_LATERAL_CLEARANCE_REDUCTIONS_MPH[min(int(lanes), 5)]
    if clearance_ft in table:
        return table[clearance_ft]
    lower = max(value for value in table if value < clearance_ft)
    upper = min(value for value in table if value > clearance_ft)
    lower_reduction = table[lower]
    upper_reduction = table[upper]
    return lower_reduction + (upper_reduction - lower_reduction) * (
        (clearance_ft - lower) / (upper - lower)
    )


def total_ramp_density_adjustment(total_ramp_density_per_mi: float) -> float:
    """HCM7 Eq. 12-2 total-ramp-density FFS reduction term."""

    _finite(total_ramp_density_per_mi, "total ramp density")
    if not 0 <= total_ramp_density_per_mi <= 6:
        raise UnsupportedScopeError("Total ramp density must be from 0 to 6 ramps/mi.")
    return 3.22 * (total_ramp_density_per_mi**0.84)


def estimated_free_flow_speed(
    base_free_flow_speed_mph: float,
    lane_width_reduction_mph: float,
    right_lateral_clearance_reduction_mph: float,
    total_ramp_density_per_mi: float,
) -> float:
    """HCM7 Eq. 12-2 Basic Freeway Segment FFS estimate."""

    for value, label in (
        (base_free_flow_speed_mph, "base FFS"),
        (lane_width_reduction_mph, "lane width adjustment"),
        (right_lateral_clearance_reduction_mph, "right-side lateral clearance adjustment"),
        (total_ramp_density_per_mi, "total ramp density"),
    ):
        _finite(value, label)
    ffs = (
        base_free_flow_speed_mph
        - lane_width_reduction_mph
        - right_lateral_clearance_reduction_mph
        - total_ramp_density_adjustment(total_ramp_density_per_mi)
    )
    if ffs <= 0:
        raise HCMCalcError("Estimated FFS must be greater than zero.")
    return ffs


def adjusted_free_flow_speed(free_flow_speed_mph: float, speed_adjustment_factor: float) -> float:
    """HCM7 Eq. 12-5 Basic Freeway Segment adjusted FFS."""

    _finite(free_flow_speed_mph, "free-flow speed")
    _finite(speed_adjustment_factor, "speed adjustment factor")
    if free_flow_speed_mph <= 0:
        raise HCMCalcError("Free-flow speed must be greater than zero.")
    if speed_adjustment_factor <= 0:
        raise HCMCalcError("Speed adjustment factor must be greater than zero.")
    ffs = free_flow_speed_mph * speed_adjustment_factor
    if not FREEWAY_MIN_FFS_MPH <= ffs <= FREEWAY_MAX_FFS_MPH:
        raise UnsupportedScopeError(
            "Basic Freeway Segment FFS must be between 55 and 75 mi/h."
        )
    return ffs


def basic_freeway_capacity(adjusted_ffs_mph: float) -> float:
    """HCM7 Eq. 12-6, capped by Exhibit 12-4."""

    _finite(adjusted_ffs_mph, "adjusted FFS")
    if not FREEWAY_MIN_FFS_MPH <= adjusted_ffs_mph <= FREEWAY_MAX_FFS_MPH:
        raise UnsupportedScopeError(
            "Basic Freeway Segment FFS must be between 55 and 75 mi/h."
        )
    return min(
        2200.0 + 10.0 * (adjusted_ffs_mph - 50.0),
        FREEWAY_MAX_CAPACITY_PC_H_LN,
    )


def adjusted_capacity_pc_h_ln(capacity_pc_h_ln: float, capacity_adjustment_factor: float) -> float:
    """HCM7 Eq. 12-8 Basic Freeway Segment adjusted capacity."""

    _finite(capacity_pc_h_ln, "capacity")
    _finite(capacity_adjustment_factor, "capacity adjustment factor")
    if capacity_pc_h_ln <= 0:
        raise HCMCalcError("Capacity must be greater than zero.")
    if capacity_adjustment_factor <= 0:
        raise HCMCalcError("Capacity adjustment factor must be greater than zero.")
    return capacity_pc_h_ln * capacity_adjustment_factor


def breakpoint_flow_rate(
    adjusted_ffs_mph: float, capacity_adjustment_factor: float = 1.0
) -> float:
    """HCM7 Exhibit 12-6 Basic Freeway Segment breakpoint."""

    _finite(adjusted_ffs_mph, "adjusted FFS")
    _finite(capacity_adjustment_factor, "capacity adjustment factor")
    if capacity_adjustment_factor <= 0:
        raise HCMCalcError("Capacity adjustment factor must be greater than zero.")
    return (1000.0 + 40.0 * (75.0 - adjusted_ffs_mph)) * (
        capacity_adjustment_factor**2
    )


def general_terrain_passenger_car_equivalent(terrain_type: str) -> float:
    """HCM7 Exhibit 12-25 general-terrain PCE."""

    try:
        return GENERAL_TERRAIN_PCE[terrain_type]
    except KeyError as exc:
        raise UnsupportedScopeError(
            "Basic Freeway Segment v0.1 supports only level and rolling general terrain."
        ) from exc


def heavy_vehicle_adjustment_factor(heavy_vehicle_percent: float, pce: float) -> float:
    """HCM7 Eq. 12-10."""

    _finite(heavy_vehicle_percent, "heavy vehicle percentage")
    _finite(pce, "passenger car equivalent")
    if not 0 <= heavy_vehicle_percent <= 100:
        raise HCMCalcError("Heavy vehicle percentage must be between 0 and 100.")
    if pce <= 0:
        raise HCMCalcError("Passenger car equivalent must be greater than zero.")
    return 1.0 / (1.0 + heavy_vehicle_percent / 100.0 * (pce - 1.0))


def demand_flow_rate(volume: float, phf: float, lanes: int, hv_factor: float) -> float:
    """HCM7 Eq. 12-9."""

    for value, label in (
        (volume, "demand volume"),
        (phf, "peak hour factor"),
        (lanes, "lane count"),
        (hv_factor, "heavy vehicle adjustment factor"),
    ):
        _finite(value, label)
    if volume <= 0:
        raise HCMCalcError("Demand volume must be greater than zero.")
    if not 0 < phf <= 1:
        raise HCMCalcError("Peak hour factor must be greater than zero and at most 1.")
    if lanes <= 0 or isinstance(lanes, bool) or int(lanes) != lanes:
        raise HCMCalcError("Lane count must be a positive integer.")
    if hv_factor <= 0:
        raise HCMCalcError("Heavy vehicle adjustment factor must be greater than zero.")
    return volume / (phf * lanes * hv_factor)


def speed_from_flow_rate(
    flow_rate: float,
    adjusted_ffs_mph: float,
    breakpoint_pc_h_ln: float,
    adjusted_capacity_pc_h_ln_value: float,
) -> float:
    """HCM7 Eq. 12-1 Basic Freeway Segment speed-flow relationship."""

    for value, label in (
        (flow_rate, "demand flow rate"),
        (adjusted_ffs_mph, "adjusted FFS"),
        (breakpoint_pc_h_ln, "breakpoint"),
        (adjusted_capacity_pc_h_ln_value, "adjusted capacity"),
    ):
        _finite(value, label)
    if flow_rate <= 0:
        raise HCMCalcError("Demand flow rate must be greater than zero.")
    if adjusted_ffs_mph <= 0:
        raise HCMCalcError("Adjusted FFS must be greater than zero.")
    if adjusted_capacity_pc_h_ln_value <= breakpoint_pc_h_ln:
        raise HCMCalcError("Adjusted capacity must be greater than breakpoint.")
    if flow_rate <= breakpoint_pc_h_ln:
        return adjusted_ffs_mph
    if flow_rate > adjusted_capacity_pc_h_ln_value:
        return adjusted_capacity_pc_h_ln_value / FREEWAY_DENSITY_AT_CAPACITY_PC_MI_LN
    speed_at_capacity = (
        adjusted_capacity_pc_h_ln_value / FREEWAY_DENSITY_AT_CAPACITY_PC_MI_LN
    )
    return adjusted_ffs_mph - (adjusted_ffs_mph - speed_at_capacity) * (
        ((flow_rate - breakpoint_pc_h_ln) ** FREEWAY_SPEED_FLOW_EXPONENT)
        / (
            (adjusted_capacity_pc_h_ln_value - breakpoint_pc_h_ln)
            ** FREEWAY_SPEED_FLOW_EXPONENT
        )
    )


def traffic_density(flow_rate: float, mean_speed_mph: float) -> float:
    """HCM7 Eq. 12-11."""

    _finite(flow_rate, "demand flow rate")
    _finite(mean_speed_mph, "mean speed")
    if flow_rate <= 0:
        raise HCMCalcError("Demand flow rate must be greater than zero.")
    if mean_speed_mph <= 0:
        raise HCMCalcError("Mean speed must be greater than zero.")
    return flow_rate / mean_speed_mph


def level_of_service(density: float, *, demand_exceeds_capacity: bool = False) -> str:
    """HCM7 Exhibit 12-15."""

    _finite(density, "density")
    if density < 0:
        raise HCMCalcError("Density must be nonnegative.")
    if demand_exceeds_capacity:
        return "F"
    for level, upper_bound in LOS_DENSITY_UPPER_BOUNDS:
        if density <= upper_bound:
            return level
    return "F"


def _finite(value: float, label: str) -> None:
    try:
        finite = isfinite(float(value))
    except (TypeError, ValueError) as exc:
        raise HCMCalcError(f"{label} must be finite.") from exc
    if not finite:
        raise HCMCalcError(f"{label} must be finite.")


def _validate_computed_output(
    value: float, label: str, *, allow_zero: bool = False
) -> None:
    _finite(value, label)
    if value < 0 or (value == 0 and not allow_zero):
        raise HCMCalcError(f"{label} must be greater than zero.")


def _intermediate_values(outputs: dict[str, Any]) -> list[IntermediateValue]:
    sources = {
        "base_free_flow_speed_mph": "HCM7 Step 2; measured FFS or Eq. 12-2",
        "lane_width_adjustment_mph": "HCM7 Exhibit 12-20",
        "right_lateral_clearance_adjustment_mph": "HCM7 Exhibit 12-21",
        "total_ramp_density_adjustment_mph": "HCM7 Eq. 12-2",
        "speed_adjustment_factor": "HCM7 Eq. 12-5",
        "adjusted_free_flow_speed_mph": "HCM7 Eq. 12-5",
        "capacity_pc_h_ln": "HCM7 Eq. 12-6; Exhibit 12-4",
        "capacity_adjustment_factor": "HCM7 Eq. 12-8",
        "adjusted_capacity_pc_h_ln": "HCM7 Eq. 12-8",
        "breakpoint_flow_rate_pc_h_ln": "HCM7 Exhibit 12-6",
        "passenger_car_equivalent": "HCM7 Exhibit 12-25",
        "heavy_vehicle_adjustment_factor": "HCM7 Eq. 12-10",
        "driver_population_factor": "HCM7 Chapter 26 Example Problem 1 regular users",
        "demand_flow_rate_pc_h_ln": "HCM7 Eq. 12-9",
        "demand_capacity_ratio": "HCM7 capacity check",
        "demand_exceeds_capacity": "HCM7 capacity check",
        "capacity_check": "HCM7 capacity check",
        "mean_speed_mph": "HCM7 Eq. 12-1",
        "speed_used_for_density_mph": "HCM7 Eq. 12-11 input",
        "density_pc_mi_ln": "HCM7 Eq. 12-11",
        "level_of_service": "HCM7 Exhibit 12-15",
    }
    return [
        IntermediateValue(name, outputs[name], source=source)
        for name, source in sources.items()
    ]
