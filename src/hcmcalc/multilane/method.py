"""HCM7 Multilane Highway Segment engine v0.1."""

from math import isfinite
from typing import Any

from hcmcalc.core import (
    CalculationResult,
    HCMCalcError,
    IntermediateValue,
    UnsupportedScopeError,
)

from .coefficients import (
    EXAMPLE_4_PCE_BY_EFFECTIVE_GRADE,
    FOUR_LANE_TLC_REDUCTIONS_MPH,
    LOS_DENSITY_UPPER_BOUNDS,
    MEDIAN_FFS_REDUCTIONS_MPH,
    MULTILANE_BREAKPOINT_PC_H_LN,
    MULTILANE_MAX_CAPACITY_PC_H_LN,
)
from .models import MultilaneBasicSegmentInputs
from .validation import reject_unsupported_scope_keys, validate_inputs


class MultilaneHighwayLOSMethod:
    """Run bounded one-direction Multilane Highway Segment calculations."""

    facility_type = "multilane_highway"
    method_name = "hcm7_multilane_los"

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        """Calculate one bounded Multilane Highway Segment."""

        if not isinstance(inputs, dict):
            raise HCMCalcError("Multilane Basic Segment inputs must be a mapping.")
        reject_unsupported_scope_keys(inputs)
        try:
            parsed = MultilaneBasicSegmentInputs.from_mapping(inputs)
        except (TypeError, ValueError) as exc:
            raise HCMCalcError(str(exc)) from exc
        validate_inputs(parsed)

        lane_adjustment = None
        total_clearance = None
        clearance_adjustment = None
        median_adjustment = None
        access_adjustment = None
        base_ffs = parsed.free_flow_speed_mph
        if parsed.ffs_source == "estimated":
            base_ffs = estimate_base_free_flow_speed(parsed.posted_speed_limit_mph)
            lane_adjustment = lane_width_adjustment(parsed.lane_width_ft)
            total_clearance = total_lateral_clearance(
                parsed.roadside_lateral_clearance_ft, parsed.median_type
            )
            clearance_adjustment = total_lateral_clearance_adjustment(total_clearance)
            median_adjustment = median_type_adjustment(parsed.median_type)
            access_adjustment = access_point_adjustment(
                parsed.access_point_density_per_mi
            )
            ffs = adjusted_free_flow_speed(
                base_ffs,
                lane_adjustment,
                clearance_adjustment,
                median_adjustment,
                access_adjustment,
            )
        else:
            ffs = parsed.free_flow_speed_mph
        capacity = multilane_capacity(ffs)
        pce = (
            parsed.passenger_car_equivalent
            if parsed.passenger_car_equivalent is not None
            else example_4_passenger_car_equivalent(
                parsed.grade_percent,
                parsed.segment_length_ft / 5280.0,
                parsed.heavy_vehicle_percent,
                parsed.truck_mix,
            )
        )
        hv_factor = heavy_vehicle_adjustment_factor(parsed.heavy_vehicle_percent, pce)
        flow_rate = demand_flow_rate(
            parsed.demand_volume_veh_h,
            parsed.peak_hour_factor,
            parsed.number_of_lanes,
            hv_factor,
        )
        speed = mean_speed_below_breakpoint(flow_rate, ffs)
        density = traffic_density(flow_rate, speed)
        los = level_of_service(density, demand_exceeds_capacity=flow_rate > capacity)

        assumptions = [
            "One-direction, one-segment uninterrupted-flow Multilane Highway analysis.",
            "TWLTL supplies 6 ft left-side clearance; roadside clearance is capped at 6 ft.",
            "Default truck mix is 30% SUTs and 70% TTs.",
            "Demand is below the 1,400 pc/h/ln Multilane Highway breakpoint, so speed equals FFS.",
        ]
        if parsed.ffs_source == "estimated":
            assumptions.append(
                "Base FFS is posted speed limit plus 7 mi/h because the posted "
                "speed is below 50 mi/h."
            )
        else:
            assumptions.append("Free-flow speed is measured or user supplied.")
        if parsed.passenger_car_equivalent is None:
            assumptions.append(
                "Downgrades steeper than 2% use the Exhibit 12-26 2% downgrade PCE."
            )
        else:
            assumptions.append(
                "Passenger-car equivalent is user supplied for this bounded "
                "v0.1 calculation."
            )
        warnings = [
            "Multilane Segment v0.1 is bounded to the implemented Chapter 12 "
            "one-direction segment scope; Example 4 remains regression evidence."
        ]
        unsupported_scope_notes = [
            "No Basic Freeway, ramp, weaving, merge/diverge, managed-lane, work-zone, reliability, or facility/corridor analysis.",
            "No specific-grade PCE table expansion beyond supplied PCE or the Example 4 lookup.",
            "Estimated FFS remains limited to the implemented four-lane lateral-clearance table.",
        ]
        source_references = [
            "HCM7 Eq. 12-3; Exhibits 12-20, 12-22, 12-23, 12-24",
            "HCM7 Eq. 12-7",
            "HCM7 Eq. 12-9 and Eq. 12-10; Exhibit 12-26",
            "HCM7 Eq. 12-1 constant-speed branch; Eq. 12-11; Exhibit 12-15",
            "HCM7 Chapter 26 Multilane Highway Example Problem 4",
        ]
        outputs = {
            "calculation_type": "multilane_basic_segment_v0_1",
            "support_status": "bounded_multilane_segment_v0_1",
            "scope_status": "bounded_multilane_segment_v0_1",
            "input_summary": parsed.__dict__,
            "ffs_source": parsed.ffs_source,
            "base_free_flow_speed_mph": base_ffs,
            "lane_width_adjustment_mph": lane_adjustment,
            "total_lateral_clearance_ft": total_clearance,
            "total_lateral_clearance_adjustment_mph": clearance_adjustment,
            "median_type_adjustment_mph": median_adjustment,
            "access_point_adjustment_mph": access_adjustment,
            "adjusted_free_flow_speed_mph": ffs,
            "capacity_pc_h_ln": capacity,
            "effective_grade_for_pce_percent": (
                -2.0 if parsed.grade_percent < -2.0 else parsed.grade_percent
            ),
            "passenger_car_equivalent": pce,
            "heavy_vehicle_adjustment_factor": hv_factor,
            "demand_flow_rate_pc_h_ln": flow_rate,
            "demand_capacity_ratio": flow_rate / capacity,
            "demand_exceeds_capacity": flow_rate > capacity,
            "capacity_check": "demand_exceeds_capacity" if flow_rate > capacity else "within_capacity",
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


def estimate_base_free_flow_speed(posted_speed_limit_mph: float) -> float:
    """HCM7 Chapter 12 base-FFS estimate used by Example Problem 4."""

    _finite(posted_speed_limit_mph, "posted speed limit")
    if posted_speed_limit_mph <= 0:
        raise HCMCalcError("Posted speed limit must be greater than zero.")
    if posted_speed_limit_mph >= 50:
        raise UnsupportedScopeError(
            "v0.1 implements only the posted-speed-below-50 base-FFS branch."
        )
    return posted_speed_limit_mph + 7.0


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


def total_lateral_clearance(roadside_clearance_ft: float, median_type: str) -> float:
    """HCM7 Eq. 12-4, including the TWLTL left-clearance rule."""

    _finite(roadside_clearance_ft, "roadside lateral clearance")
    if roadside_clearance_ft < 0:
        raise HCMCalcError("Roadside lateral clearance must be nonnegative.")
    if median_type != "twltl":
        raise UnsupportedScopeError("v0.1 implements the TWLTL clearance rule only.")
    return min(roadside_clearance_ft, 6.0) + 6.0


def total_lateral_clearance_adjustment(total_clearance_ft: float) -> float:
    """Interpolate HCM7 Exhibit 12-22 for a four-lane highway."""

    _finite(total_clearance_ft, "total lateral clearance")
    if not 0 <= total_clearance_ft <= 12:
        raise HCMCalcError("Total lateral clearance must be between 0 and 12 ft.")
    if total_clearance_ft in FOUR_LANE_TLC_REDUCTIONS_MPH:
        return FOUR_LANE_TLC_REDUCTIONS_MPH[total_clearance_ft]
    lower = max(value for value in FOUR_LANE_TLC_REDUCTIONS_MPH if value < total_clearance_ft)
    upper = min(value for value in FOUR_LANE_TLC_REDUCTIONS_MPH if value > total_clearance_ft)
    lower_reduction = FOUR_LANE_TLC_REDUCTIONS_MPH[lower]
    upper_reduction = FOUR_LANE_TLC_REDUCTIONS_MPH[upper]
    return lower_reduction + (upper_reduction - lower_reduction) * (
        (total_clearance_ft - lower) / (upper - lower)
    )


def median_type_adjustment(median_type: str) -> float:
    """HCM7 Exhibit 12-23 median adjustment."""

    try:
        return MEDIAN_FFS_REDUCTIONS_MPH[median_type]
    except KeyError as exc:
        raise HCMCalcError(f"Unsupported median type: {median_type!r}.") from exc


def access_point_adjustment(access_point_density_per_mi: float) -> float:
    """HCM7 Exhibit 12-24 linear access-point adjustment."""

    _finite(access_point_density_per_mi, "access point density")
    if not 0 <= access_point_density_per_mi <= 40:
        raise UnsupportedScopeError(
            "Exhibit 12-24 access-point density must be between 0 and 40 per mile."
        )
    return 0.25 * access_point_density_per_mi


def adjusted_free_flow_speed(
    base_ffs: float,
    lane_width_reduction: float,
    clearance_reduction: float,
    median_reduction: float,
    access_reduction: float,
) -> float:
    """HCM7 Eq. 12-3."""

    for value, label in (
        (base_ffs, "base FFS"),
        (lane_width_reduction, "lane width adjustment"),
        (clearance_reduction, "total lateral clearance adjustment"),
        (median_reduction, "median type adjustment"),
        (access_reduction, "access point adjustment"),
    ):
        _finite(value, label)
    ffs = (
        base_ffs
        - lane_width_reduction
        - clearance_reduction
        - median_reduction
        - access_reduction
    )
    if ffs <= 0:
        raise HCMCalcError("Adjusted FFS must be greater than zero.")
    return ffs


def multilane_capacity(adjusted_ffs_mph: float) -> float:
    """HCM7 Eq. 12-7, capped by the Multilane Highway maximum."""

    _finite(adjusted_ffs_mph, "adjusted FFS")
    if not 45 <= adjusted_ffs_mph <= 70:
        raise UnsupportedScopeError("Multilane FFS must be between 45 and 70 mi/h.")
    return min(
        1900.0 + 20.0 * (adjusted_ffs_mph - 45.0),
        MULTILANE_MAX_CAPACITY_PC_H_LN,
    )


def example_4_passenger_car_equivalent(
    grade_percent: float,
    segment_length_mi: float,
    heavy_vehicle_percent: float,
    truck_mix: str,
) -> float:
    """Return the two Exhibit 12-26 PCE values used by Example Problem 4."""

    if segment_length_mi != 1.25 or heavy_vehicle_percent != 6.0:
        raise UnsupportedScopeError(
            "v0.1 PCE lookup supports only the Example Problem 4 grade length "
            "and truck percentage."
        )
    if truck_mix != "default_30_sut_70_tt":
        raise UnsupportedScopeError(
            "v0.1 PCE lookup supports only the default 30% SUT / 70% TT mix."
        )
    effective_grade = -2.0 if grade_percent < -2.0 else grade_percent
    try:
        return EXAMPLE_4_PCE_BY_EFFECTIVE_GRADE[effective_grade]
    except KeyError as exc:
        raise UnsupportedScopeError(
            "v0.1 PCE lookup supports only Example Problem 4's upgrade and downgrade."
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


def mean_speed_below_breakpoint(flow_rate: float, adjusted_ffs_mph: float) -> float:
    """HCM7 Eq. 12-1 constant-speed branch used by Example Problem 4."""

    _finite(flow_rate, "demand flow rate")
    _finite(adjusted_ffs_mph, "adjusted FFS")
    if flow_rate <= 0:
        raise HCMCalcError("Demand flow rate must be greater than zero.")
    if adjusted_ffs_mph <= 0:
        raise HCMCalcError("Adjusted FFS must be greater than zero.")
    if flow_rate > MULTILANE_BREAKPOINT_PC_H_LN:
        raise UnsupportedScopeError(
            "v0.1 implements only the Example Problem 4 flow-below-breakpoint branch."
        )
    return adjusted_ffs_mph


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


def _intermediate_values(outputs: dict[str, Any]) -> list[IntermediateValue]:
    sources = {
        "base_free_flow_speed_mph": "HCM7 Chapter 12 base-FFS guidance",
        "lane_width_adjustment_mph": "HCM7 Exhibit 12-20",
        "total_lateral_clearance_ft": "HCM7 Eq. 12-4",
        "total_lateral_clearance_adjustment_mph": "HCM7 Exhibit 12-22",
        "median_type_adjustment_mph": "HCM7 Exhibit 12-23",
        "access_point_adjustment_mph": "HCM7 Exhibit 12-24",
        "adjusted_free_flow_speed_mph": "HCM7 Eq. 12-3",
        "capacity_pc_h_ln": "HCM7 Eq. 12-7",
        "passenger_car_equivalent": "HCM7 Exhibit 12-26",
        "heavy_vehicle_adjustment_factor": "HCM7 Eq. 12-10",
        "demand_flow_rate_pc_h_ln": "HCM7 Eq. 12-9",
        "demand_capacity_ratio": "HCM7 Eq. 12-7 capacity check",
        "demand_exceeds_capacity": "HCM7 Eq. 12-7 capacity check",
        "capacity_check": "HCM7 Eq. 12-7 capacity check",
        "mean_speed_mph": "HCM7 Eq. 12-1",
        "speed_used_for_density_mph": "HCM7 Eq. 12-11 input",
        "density_pc_mi_ln": "HCM7 Eq. 12-11",
        "level_of_service": "HCM7 Exhibit 12-15",
    }
    return [
        IntermediateValue(name, outputs[name], source=source)
        for name, source in sources.items()
    ]
