"""HCM 7th Edition Chapter 15 Two-Lane Highway method.

Only the Chapter 26 Example Problem 1 calculation path is enabled. The formulas
implemented here are Chapter 15 formulas for the level, straight Passing
Constrained case and are intentionally independent from any UI.
"""

from dataclasses import dataclass
from math import exp, log, sqrt
from typing import Any

from hcmcalc.core import CalculationResult, HCMCalcError, IntermediateValue, MethodNotImplementedError


PASSING_CONSTRAINED = "passing_constrained"
OPPOSING_FLOW_EXAMPLE_1_VEH_H = 1500.0


@dataclass(frozen=True)
class TwoLaneExampleProblem1Inputs:
    """Validated input shape for HCM Chapter 26 Two-Lane Example Problem 1."""

    segment_length_mi: float
    segment_type: str
    analysis_direction_volume_veh_h: float
    peak_hour_factor: float
    posted_speed_mph: float
    heavy_vehicle_percent: float
    grade_percent: float
    horizontal_alignment: str
    lane_width_ft: float
    shoulder_width_ft: float
    access_point_density_per_mi: float
    upstream_passing_lane: bool


# HCM Ch. 15 Exhibit 15-12, vertical class 1 coefficients for Eq. 15-4.
HEAVY_VEHICLE_COEFFICIENTS = {1: (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)}
# HCM Ch. 15 Exhibit 15-13, vertical class 1 coefficients for Eq. 15-8.
SPEED_SLOPE_COEFFICIENTS = {1: (0.0558, 0.0542, 0.3278, 0.1029, 0.0, 0.0)}
# HCM Ch. 15 Exhibit 15-19, vertical class 1 coefficients for Eq. 15-11.
SPEED_POWER_COEFFICIENTS = {1: (0.67576, 0.0, 0.0, 0.1206, -0.35919, 0.0, 0.0, 0.0, 0.0)}
# HCM Ch. 15 Exhibit 15-24, vertical class 1 coefficients for Eq. 15-18.
PF_CAPACITY_COEFFICIENTS = {1: (37.6808, 3.05089, -7.90866, -0.94321, 13.64266, -0.00050, -0.05500, 7.13758)}
# HCM Ch. 15 Exhibit 15-26, vertical class 1 coefficients for Eq. 15-20.
PF_25_CAPACITY_COEFFICIENTS = {1: (18.01780, 10.00000, -21.60000, -0.97853, 12.05214, -0.00750, -0.06700, 11.60405)}
# HCM Ch. 15 Exhibits 15-28 and 15-29 for Passing Constrained segments.
PF_SLOPE_COEFFICIENTS = {PASSING_CONSTRAINED: (-0.29764, -0.71917)}
PF_POWER_COEFFICIENTS = {PASSING_CONSTRAINED: (0.81165, 0.3792, -0.49524, -2.11289, 2.41146)}


class TwoLaneHighwayChapter15Method:
    """Partial two-lane highway motorized vehicle analysis implementation."""

    facility_type = "two_lane_highway"
    method_name = "hcm7_ch15_two_lane_motorized"

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        """Run the validated Chapter 26 Example Problem 1 calculation path."""

        if inputs.get("case_id") != "TLH-CH15-001":
            raise MethodNotImplementedError(
                "Only HCM Chapter 26 Two-Lane Highway Example Problem 1 is implemented."
            )

        parsed = _parse_example_problem_1_inputs(inputs)
        _validate_example_problem_1_scope(parsed)

        demand = demand_flow_rate(parsed.analysis_direction_volume_veh_h, parsed.peak_hour_factor)
        capacity = passing_constrained_capacity()
        d_c = demand / capacity
        vertical_class = vertical_alignment_class(parsed.segment_length_mi, parsed.grade_percent)
        bffs = base_free_flow_speed(parsed.posted_speed_mph)
        f_ls = lane_shoulder_adjustment(parsed.lane_width_ft, parsed.shoulder_width_ft)
        f_a = access_point_adjustment(parsed.access_point_density_per_mi)
        hv_a = heavy_vehicle_ffs_coefficient(
            vertical_class, bffs, parsed.segment_length_mi, OPPOSING_FLOW_EXAMPLE_1_VEH_H
        )
        ffs = estimated_free_flow_speed(bffs, hv_a, parsed.heavy_vehicle_percent, f_ls, f_a)
        speed_m = average_speed_slope_coefficient(
            vertical_class,
            ffs,
            OPPOSING_FLOW_EXAMPLE_1_VEH_H,
            parsed.segment_length_mi,
            parsed.heavy_vehicle_percent,
        )
        speed_p = average_speed_power_coefficient(
            vertical_class,
            ffs,
            OPPOSING_FLOW_EXAMPLE_1_VEH_H,
            parsed.segment_length_mi,
            parsed.heavy_vehicle_percent,
        )
        speed = average_speed(ffs, demand, speed_m, speed_p)
        pf_cap = percent_followers_at_capacity(
            vertical_class,
            parsed.segment_length_mi,
            ffs,
            parsed.heavy_vehicle_percent,
            OPPOSING_FLOW_EXAMPLE_1_VEH_H,
        )
        pf_25_cap = percent_followers_at_25_percent_capacity(
            vertical_class,
            parsed.segment_length_mi,
            ffs,
            parsed.heavy_vehicle_percent,
            OPPOSING_FLOW_EXAMPLE_1_VEH_H,
        )
        pf_m = percent_followers_slope_coefficient(parsed.segment_type, pf_cap, pf_25_cap, capacity)
        pf_p = percent_followers_power_coefficient(parsed.segment_type, pf_cap, pf_25_cap, capacity)
        pf = percent_followers(demand, pf_m, pf_p)
        density = follower_density(demand, speed, pf)
        los = level_of_service(density, parsed.posted_speed_mph)

        outputs = {
            "demand_flow_rate_veh_h": demand,
            "capacity_veh_h": capacity,
            "demand_capacity_ratio": d_c,
            "vertical_class": vertical_class,
            "base_free_flow_speed_mph": bffs,
            "lane_shoulder_adjustment_mph": f_ls,
            "access_point_adjustment_mph": f_a,
            "heavy_vehicle_ffs_coefficient": hv_a,
            "free_flow_speed_mph": ffs,
            "average_speed_slope_coefficient": speed_m,
            "average_speed_power_coefficient": speed_p,
            "average_speed_mph": speed,
            "percent_followers_at_capacity": pf_cap,
            "percent_followers_at_25_percent_capacity": pf_25_cap,
            "percent_followers_slope_coefficient": pf_m,
            "percent_followers_power_coefficient": pf_p,
            "percent_followers": pf,
            "follower_density_followers_mi_ln": density,
            "level_of_service": los,
        }
        intermediate_values = [
            IntermediateValue("demand_flow_rate", demand, "veh/h", "HCM Eq. 15-1"),
            IntermediateValue("passing_constrained_capacity", capacity, "veh/h"),
            IntermediateValue("demand_capacity_ratio", d_c),
            IntermediateValue("vertical_alignment_class", vertical_class, source="HCM Exhibit 15-11"),
            IntermediateValue("base_free_flow_speed", bffs, "mph", "HCM Eq. 15-2"),
            IntermediateValue("lane_shoulder_adjustment", f_ls, "mph", "HCM Eq. 15-5"),
            IntermediateValue("access_point_adjustment", f_a, "mph", "HCM Eq. 15-6"),
            IntermediateValue("heavy_vehicle_ffs_coefficient", hv_a, source="HCM Eq. 15-4"),
            IntermediateValue("free_flow_speed", ffs, "mph", "HCM Eq. 15-3"),
            IntermediateValue("average_speed_slope_coefficient", speed_m, source="HCM Eq. 15-8"),
            IntermediateValue("average_speed_power_coefficient", speed_p, source="HCM Eq. 15-11"),
            IntermediateValue("average_speed", speed, "mph", "HCM Eq. 15-7"),
            IntermediateValue("percent_followers_at_capacity", pf_cap, "%", "HCM Eq. 15-18"),
            IntermediateValue("percent_followers_at_25_percent_capacity", pf_25_cap, "%", "HCM Eq. 15-20"),
            IntermediateValue("percent_followers_slope_coefficient", pf_m, source="HCM Eq. 15-22"),
            IntermediateValue("percent_followers_power_coefficient", pf_p, source="HCM Eq. 15-23"),
            IntermediateValue("percent_followers", pf, "%", "HCM Eq. 15-17"),
            IntermediateValue("follower_density", density, "followers/mi/ln", "HCM Eq. 15-35"),
        ]
        return CalculationResult(
            method=self.method_name,
            facility_type=self.facility_type,
            outputs=outputs,
            intermediate_values=intermediate_values,
            assumptions=[
                "Validated only for HCM Chapter 26 Two-Lane Highway Example Problem 1.",
                "Applies to a level, straight Passing Constrained segment.",
                "Example Problem 1 opposing flow is 1,500 veh/h.",
            ],
        )


def _parse_example_problem_1_inputs(inputs: dict[str, Any]) -> TwoLaneExampleProblem1Inputs:
    try:
        return TwoLaneExampleProblem1Inputs(
            segment_length_mi=float(inputs["segment_length_mi"]),
            segment_type=str(inputs["segment_type"]),
            analysis_direction_volume_veh_h=float(inputs["analysis_direction_volume_veh_h"]),
            peak_hour_factor=float(inputs["peak_hour_factor"]),
            posted_speed_mph=float(inputs["posted_speed_mph"]),
            heavy_vehicle_percent=float(inputs["heavy_vehicle_percent"]),
            grade_percent=float(inputs["grade_percent"]),
            horizontal_alignment=str(inputs["horizontal_alignment"]),
            lane_width_ft=float(inputs["lane_width_ft"]),
            shoulder_width_ft=float(inputs["shoulder_width_ft"]),
            access_point_density_per_mi=float(inputs["access_point_density_per_mi"]),
            upstream_passing_lane=bool(inputs["upstream_passing_lane"]),
        )
    except KeyError as exc:
        raise HCMCalcError(f"Missing Example Problem 1 input: {exc.args[0]}") from exc


def _validate_example_problem_1_scope(inputs: TwoLaneExampleProblem1Inputs) -> None:
    if inputs.segment_type != PASSING_CONSTRAINED:
        raise MethodNotImplementedError("Only Passing Constrained segments are implemented.")
    if inputs.horizontal_alignment != "straight":
        raise MethodNotImplementedError("Only straight horizontal alignment is implemented.")
    if inputs.upstream_passing_lane:
        raise MethodNotImplementedError("Upstream passing lane adjustment is not implemented.")
    if inputs.peak_hour_factor <= 0:
        raise HCMCalcError("peak_hour_factor must be greater than zero.")


def demand_flow_rate(analysis_direction_volume_veh_h: float, peak_hour_factor: float) -> float:
    """HCM Eq. 15-1 demand flow rate."""

    return analysis_direction_volume_veh_h / peak_hour_factor


def passing_constrained_capacity() -> float:
    """HCM Ch. 15 Passing Constrained segment capacity."""

    return 1700.0


def vertical_alignment_class(segment_length_mi: float, grade_percent: float) -> int:
    """HCM Exhibit 15-11 vertical class mapping for level terrain."""

    if grade_percent != 0:
        raise MethodNotImplementedError("Only level terrain is implemented.")
    if not 0.25 <= segment_length_mi <= 3.0:
        raise HCMCalcError("Passing Constrained vertical class 1 segment length must be 0.25 to 3.0 mi.")
    return 1


def base_free_flow_speed(posted_speed_mph: float) -> float:
    """HCM Eq. 15-2 BFFS estimate."""

    return 1.14 * posted_speed_mph


def lane_shoulder_adjustment(lane_width_ft: float, shoulder_width_ft: float) -> float:
    """HCM Eq. 15-5 lane and shoulder width adjustment."""

    if not 9.0 <= lane_width_ft <= 12.0:
        raise HCMCalcError("lane_width_ft must be within the HCM range of 9 to 12 ft.")
    if not 0.0 <= shoulder_width_ft <= 6.0:
        raise HCMCalcError("shoulder_width_ft must be within the HCM range of 0 to 6 ft.")
    return 0.6 * (12.0 - lane_width_ft) + 0.7 * (6.0 - shoulder_width_ft)


def access_point_adjustment(access_point_density_per_mi: float) -> float:
    """HCM Eq. 15-6 access point density adjustment."""

    if access_point_density_per_mi < 0:
        raise HCMCalcError("access_point_density_per_mi must not be negative.")
    return min(access_point_density_per_mi / 4.0, 10.0)


def heavy_vehicle_ffs_coefficient(
    vertical_class: int,
    base_free_flow_speed_mph: float,
    segment_length_mi: float,
    opposing_flow_veh_h: float,
) -> float:
    """HCM Eq. 15-4 coefficient for the HV% term in Eq. 15-3."""

    a0, a1, a2, a3, a4, a5 = HEAVY_VEHICLE_COEFFICIENTS[vertical_class]
    modeled = (
        a0
        + a1 * base_free_flow_speed_mph
        + a2 * segment_length_mi
        + max(0.0, a3 + a4 * base_free_flow_speed_mph + a5 * segment_length_mi)
        * (opposing_flow_veh_h / 1000.0)
    )
    return max(0.0333, modeled)


def estimated_free_flow_speed(
    base_free_flow_speed_mph: float,
    heavy_vehicle_coefficient: float,
    heavy_vehicle_percent: float,
    lane_shoulder_adjustment_mph: float,
    access_point_adjustment_mph: float,
) -> float:
    """HCM Eq. 15-3 FFS estimate."""

    return (
        base_free_flow_speed_mph
        - heavy_vehicle_coefficient * heavy_vehicle_percent
        - lane_shoulder_adjustment_mph
        - access_point_adjustment_mph
    )


def average_speed_slope_coefficient(
    vertical_class: int,
    free_flow_speed_mph: float,
    opposing_flow_veh_h: float,
    segment_length_mi: float,
    heavy_vehicle_percent: float,
) -> float:
    """HCM Eq. 15-8 slope coefficient for Eq. 15-7."""

    b0, b1, b2, b3, b4, b5 = SPEED_SLOPE_COEFFICIENTS[vertical_class]
    modeled = (
        b0
        + b1 * free_flow_speed_mph
        + b2 * sqrt(opposing_flow_veh_h / 1000.0)
        + max(0.0, b3) * sqrt(segment_length_mi)
        + max(0.0, b4) * sqrt(heavy_vehicle_percent)
    )
    return max(b5, modeled)


def average_speed_power_coefficient(
    vertical_class: int,
    free_flow_speed_mph: float,
    opposing_flow_veh_h: float,
    segment_length_mi: float,
    heavy_vehicle_percent: float,
) -> float:
    """HCM Eq. 15-11 power coefficient for Eq. 15-7."""

    f0, f1, f2, f3, f4, f5, f6, f7, f8 = SPEED_POWER_COEFFICIENTS[vertical_class]
    opposing_flow_thousands = opposing_flow_veh_h / 1000.0
    modeled = (
        f0
        + f1 * free_flow_speed_mph
        + f2 * segment_length_mi
        + f3 * opposing_flow_thousands
        + f4 * sqrt(opposing_flow_thousands)
        + f5 * heavy_vehicle_percent
        + f6 * sqrt(heavy_vehicle_percent)
        + f7 * (segment_length_mi * heavy_vehicle_percent)
    )
    return max(f8, modeled)


def average_speed(
    free_flow_speed_mph: float,
    demand_flow_rate_veh_h: float,
    slope_coefficient: float,
    power_coefficient: float,
) -> float:
    """HCM Eq. 15-7 Passing Constrained average speed."""

    if demand_flow_rate_veh_h <= 100.0:
        return free_flow_speed_mph
    return free_flow_speed_mph - slope_coefficient * (demand_flow_rate_veh_h / 1000.0 - 0.1) ** power_coefficient


def percent_followers_at_capacity(
    vertical_class: int,
    segment_length_mi: float,
    free_flow_speed_mph: float,
    heavy_vehicle_percent: float,
    opposing_flow_veh_h: float,
) -> float:
    """HCM Eq. 15-18 PF at capacity for Passing Constrained segments."""

    return _percent_followers_capacity_value(
        PF_CAPACITY_COEFFICIENTS[vertical_class],
        segment_length_mi,
        free_flow_speed_mph,
        heavy_vehicle_percent,
        opposing_flow_veh_h,
    )


def percent_followers_at_25_percent_capacity(
    vertical_class: int,
    segment_length_mi: float,
    free_flow_speed_mph: float,
    heavy_vehicle_percent: float,
    opposing_flow_veh_h: float,
) -> float:
    """HCM Eq. 15-20 PF at 25 percent capacity for Passing Constrained segments."""

    return _percent_followers_capacity_value(
        PF_25_CAPACITY_COEFFICIENTS[vertical_class],
        segment_length_mi,
        free_flow_speed_mph,
        heavy_vehicle_percent,
        opposing_flow_veh_h,
    )


def _percent_followers_capacity_value(
    coefficients: tuple[float, float, float, float, float, float, float, float],
    segment_length_mi: float,
    free_flow_speed_mph: float,
    heavy_vehicle_percent: float,
    opposing_flow_veh_h: float,
) -> float:
    c0, c1, c2, c3, c4, c5, c6, c7 = coefficients
    opposing_flow_thousands = opposing_flow_veh_h / 1000.0
    return (
        c0
        + c1 * segment_length_mi
        + c2 * sqrt(segment_length_mi)
        + c3 * free_flow_speed_mph
        + c4 * sqrt(free_flow_speed_mph)
        + c5 * heavy_vehicle_percent
        + c6 * (free_flow_speed_mph * opposing_flow_thousands)
        + c7 * sqrt(opposing_flow_thousands)
    )


def percent_followers_slope_coefficient(
    segment_type: str,
    percent_followers_capacity: float,
    percent_followers_25_capacity: float,
    capacity_veh_h: float,
) -> float:
    """HCM Eq. 15-22 slope coefficient for Eq. 15-17."""

    d1, d2 = PF_SLOPE_COEFFICIENTS[segment_type]
    term_25_cap = _percent_followers_capacity_log_term(percent_followers_25_capacity, capacity_veh_h, 0.25)
    term_cap = _percent_followers_capacity_log_term(percent_followers_capacity, capacity_veh_h, 1.0)
    return d1 * term_25_cap + d2 * term_cap


def percent_followers_power_coefficient(
    segment_type: str,
    percent_followers_capacity: float,
    percent_followers_25_capacity: float,
    capacity_veh_h: float,
) -> float:
    """HCM Eq. 15-23 power coefficient for Eq. 15-17."""

    e0, e1, e2, e3, e4 = PF_POWER_COEFFICIENTS[segment_type]
    term_25_cap = _percent_followers_capacity_log_term(percent_followers_25_capacity, capacity_veh_h, 0.25)
    term_cap = _percent_followers_capacity_log_term(percent_followers_capacity, capacity_veh_h, 1.0)
    return e0 + e1 * term_25_cap + e2 * term_cap + e3 * sqrt(term_25_cap) + e4 * sqrt(term_cap)


def _percent_followers_capacity_log_term(
    percent_followers_value: float,
    capacity_veh_h: float,
    capacity_multiplier: float,
) -> float:
    return -log(1.0 - percent_followers_value / 100.0) / (capacity_multiplier * (capacity_veh_h / 1000.0))


def percent_followers(
    demand_flow_rate_veh_h: float,
    slope_coefficient: float,
    power_coefficient: float,
) -> float:
    """HCM Eq. 15-17 Passing Constrained percent followers."""

    return 100.0 * (1.0 - exp(slope_coefficient * (demand_flow_rate_veh_h / 1000.0) ** power_coefficient))


def follower_density(
    demand_flow_rate_veh_h: float,
    average_speed_mph: float,
    percent_followers_value: float,
) -> float:
    """HCM Eq. 15-35 follower density."""

    return demand_flow_rate_veh_h / average_speed_mph * (percent_followers_value / 100.0)


def level_of_service(follower_density_followers_mi_ln: float, posted_speed_mph: float) -> str:
    """HCM Exhibit 15-6 LOS thresholds for two-lane highways."""

    thresholds = (2.5, 5.0, 10.0, 15.0, 20.0) if posted_speed_mph < 50.0 else (2.0, 4.0, 8.0, 12.0, 18.0)
    if follower_density_followers_mi_ln <= thresholds[0]:
        return "A"
    if follower_density_followers_mi_ln <= thresholds[1]:
        return "B"
    if follower_density_followers_mi_ln <= thresholds[2]:
        return "C"
    if follower_density_followers_mi_ln <= thresholds[3]:
        return "D"
    if follower_density_followers_mi_ln <= thresholds[4]:
        return "E"
    return "F"
