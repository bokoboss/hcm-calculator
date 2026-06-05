"""HCM 7th Edition Chapter 15 Two-Lane Highway method.

Only the Chapter 26 Example Problems 1 and 2 calculation paths are enabled. The
formulas implemented here are Chapter 15 formulas for level Passing Constrained
segments and are intentionally kept independent from any UI.
"""

from math import exp, log, sqrt
from typing import Any

from hcmcalc.core import (
    CalculationResult,
    HCMCalcError,
    IntermediateValue,
    MethodNotImplementedError,
)
from hcmcalc.methods.two_lane_highway_coefficients import (
    HEAVY_VEHICLE_COEFFICIENTS,
    HORIZONTAL_CURVE_CLASS_SPEED_INTERCEPT,
    HORIZONTAL_CURVE_CLASS_SPEED_SLOPE,
    HORIZONTAL_CURVE_HEAVY_VEHICLE_COEFFICIENT,
    HORIZONTAL_CURVE_SPEED_COEFFICIENTS,
    PF_25_CAPACITY_COEFFICIENTS,
    PF_CAPACITY_COEFFICIENTS,
    PF_POWER_COEFFICIENTS,
    PF_SLOPE_COEFFICIENTS,
    PercentFollowersCapacityCoefficients,
    SPEED_POWER_COEFFICIENTS,
    SPEED_SLOPE_COEFFICIENTS,
)
from hcmcalc.methods.two_lane_highway_models import (
    HORIZONTAL_CURVES_ALIGNMENT,
    OPPOSING_FLOW_EXAMPLE_1_VEH_H,
    PASSING_CONSTRAINED,
    STRAIGHT_ALIGNMENT,
    HorizontalAlignmentSubsegment,
    TwoLaneExampleProblem1Inputs,
    TwoLaneExampleProblem2Inputs,
)


class TwoLaneHighwayChapter15Method:
    """Partial two-lane highway motorized vehicle analysis implementation."""

    facility_type = "two_lane_highway"
    method_name = "hcm7_ch15_two_lane_motorized"

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        """Run the validated Chapter 26 Example Problem 1 or 2 calculation path."""

        case_id = inputs.get("case_id")
        if case_id not in {"TLH-CH15-001", "TLH-CH15-002"}:
            raise MethodNotImplementedError(
                "Only HCM Chapter 26 Two-Lane Highway Example Problems 1 and 2 "
                "are implemented. Additional Chapter 15 cases require "
                "methodology mapping and validation before implementation."
            )

        if case_id == "TLH-CH15-001":
            parsed_inputs = _parse_example_problem_1_inputs(inputs)
            _validate_example_problem_1_scope(parsed_inputs)
        else:
            parsed_inputs = _parse_example_problem_2_inputs(inputs)
            _validate_example_problem_2_scope(parsed_inputs)

        base = _calculate_passing_constrained_base_values(parsed_inputs)

        if case_id == "TLH-CH15-002":
            return _calculate_example_problem_2_result(parsed_inputs, base)

        return _calculate_example_problem_1_result(parsed_inputs, base)


def _calculate_passing_constrained_base_values(
    parsed_inputs: TwoLaneExampleProblem1Inputs,
) -> dict[str, float | int | str]:
    demand = demand_flow_rate(
        parsed_inputs.analysis_direction_volume_veh_h,
        parsed_inputs.peak_hour_factor,
    )
    capacity = passing_constrained_capacity()
    demand_capacity_ratio = demand / capacity
    vertical_class = vertical_alignment_class(
        parsed_inputs.segment_length_mi,
        parsed_inputs.grade_percent,
    )
    bffs = base_free_flow_speed(parsed_inputs.posted_speed_mph)
    f_ls = lane_shoulder_adjustment(
        parsed_inputs.lane_width_ft,
        parsed_inputs.shoulder_width_ft,
    )
    f_a = access_point_adjustment(parsed_inputs.access_point_density_per_mi)
    hv_coefficient = heavy_vehicle_ffs_coefficient(
        vertical_class,
        bffs,
        parsed_inputs.segment_length_mi,
        OPPOSING_FLOW_EXAMPLE_1_VEH_H,
    )
    ffs = estimated_free_flow_speed(
        bffs,
        hv_coefficient,
        parsed_inputs.heavy_vehicle_percent,
        f_ls,
        f_a,
    )
    speed_m = average_speed_slope_coefficient(
        vertical_class,
        ffs,
        OPPOSING_FLOW_EXAMPLE_1_VEH_H,
        parsed_inputs.segment_length_mi,
        parsed_inputs.heavy_vehicle_percent,
    )
    speed_p = average_speed_power_coefficient(
        vertical_class,
        ffs,
        OPPOSING_FLOW_EXAMPLE_1_VEH_H,
        parsed_inputs.segment_length_mi,
        parsed_inputs.heavy_vehicle_percent,
    )
    speed = average_speed(ffs, demand, speed_m, speed_p)
    pf_cap = percent_followers_at_capacity(
        vertical_class,
        parsed_inputs.segment_length_mi,
        ffs,
        parsed_inputs.heavy_vehicle_percent,
        OPPOSING_FLOW_EXAMPLE_1_VEH_H,
    )
    pf_25_cap = percent_followers_at_25_percent_capacity(
        vertical_class,
        parsed_inputs.segment_length_mi,
        ffs,
        parsed_inputs.heavy_vehicle_percent,
        OPPOSING_FLOW_EXAMPLE_1_VEH_H,
    )
    pf_m = percent_followers_slope_coefficient(
        parsed_inputs.segment_type,
        pf_cap,
        pf_25_cap,
        capacity,
    )
    pf_p = percent_followers_power_coefficient(
        parsed_inputs.segment_type,
        pf_cap,
        pf_25_cap,
        capacity,
    )
    followers = percent_followers(demand, pf_m, pf_p)
    density = follower_density(demand, speed, followers)
    los = level_of_service(density, parsed_inputs.posted_speed_mph)

    return {
        "demand_flow_rate_veh_h": demand,
        "capacity_veh_h": capacity,
        "demand_capacity_ratio": demand_capacity_ratio,
        "vertical_class": vertical_class,
        "base_free_flow_speed_mph": bffs,
        "lane_shoulder_adjustment_mph": f_ls,
        "access_point_adjustment_mph": f_a,
        "heavy_vehicle_ffs_coefficient": hv_coefficient,
        "free_flow_speed_mph": ffs,
        "average_speed_slope_coefficient": speed_m,
        "average_speed_power_coefficient": speed_p,
        "average_speed_mph": speed,
        "percent_followers_at_capacity": pf_cap,
        "percent_followers_at_25_percent_capacity": pf_25_cap,
        "percent_followers_slope_coefficient": pf_m,
        "percent_followers_power_coefficient": pf_p,
        "percent_followers": followers,
        "follower_density_followers_mi_ln": density,
        "level_of_service": los,
    }


def _calculate_example_problem_1_result(
    parsed_inputs: TwoLaneExampleProblem1Inputs,
    base: dict[str, float | int | str],
) -> CalculationResult:
    return CalculationResult(
            method=TwoLaneHighwayChapter15Method.method_name,
            facility_type=TwoLaneHighwayChapter15Method.facility_type,
            outputs={
                "demand_flow_rate_veh_h": base["demand_flow_rate_veh_h"],
                "capacity_veh_h": base["capacity_veh_h"],
                "demand_capacity_ratio": base["demand_capacity_ratio"],
                "vertical_class": base["vertical_class"],
                "base_free_flow_speed_mph": base["base_free_flow_speed_mph"],
                "lane_shoulder_adjustment_mph": base["lane_shoulder_adjustment_mph"],
                "access_point_adjustment_mph": base["access_point_adjustment_mph"],
                "heavy_vehicle_ffs_coefficient": base["heavy_vehicle_ffs_coefficient"],
                "free_flow_speed_mph": base["free_flow_speed_mph"],
                "average_speed_slope_coefficient": base[
                    "average_speed_slope_coefficient"
                ],
                "average_speed_power_coefficient": base[
                    "average_speed_power_coefficient"
                ],
                "average_speed_mph": base["average_speed_mph"],
                "percent_followers_at_capacity": base["percent_followers_at_capacity"],
                "percent_followers_at_25_percent_capacity": base[
                    "percent_followers_at_25_percent_capacity"
                ],
                "percent_followers_slope_coefficient": base[
                    "percent_followers_slope_coefficient"
                ],
                "percent_followers_power_coefficient": base[
                    "percent_followers_power_coefficient"
                ],
                "percent_followers": base["percent_followers"],
                "follower_density_followers_mi_ln": base[
                    "follower_density_followers_mi_ln"
                ],
                "level_of_service": base["level_of_service"],
            },
            intermediate_values=[
                IntermediateValue(
                    "demand_flow_rate",
                    base["demand_flow_rate_veh_h"],
                    "veh/h",
                    "HCM Eq. 15-1",
                ),
                IntermediateValue(
                    "passing_constrained_capacity",
                    base["capacity_veh_h"],
                    "veh/h",
                    "HCM Ch. 15 Passing Constrained segment capacity",
                ),
                IntermediateValue(
                    "demand_capacity_ratio", base["demand_capacity_ratio"]
                ),
                IntermediateValue(
                    "vertical_alignment_class",
                    base["vertical_class"],
                    source="HCM Exhibit 15-11",
                ),
                IntermediateValue(
                    "base_free_flow_speed",
                    base["base_free_flow_speed_mph"],
                    "mph",
                    "HCM Eq. 15-2",
                ),
                IntermediateValue(
                    "lane_shoulder_adjustment",
                    base["lane_shoulder_adjustment_mph"],
                    "mph",
                    "HCM Eq. 15-5",
                ),
                IntermediateValue(
                    "access_point_adjustment",
                    base["access_point_adjustment_mph"],
                    "mph",
                    "HCM Eq. 15-6",
                ),
                IntermediateValue(
                    "heavy_vehicle_ffs_coefficient",
                    base["heavy_vehicle_ffs_coefficient"],
                    source="HCM Eq. 15-4 and Exhibit 15-12",
                ),
                IntermediateValue(
                    "free_flow_speed",
                    base["free_flow_speed_mph"],
                    "mph",
                    "HCM Eq. 15-3",
                ),
                IntermediateValue(
                    "average_speed_slope_coefficient",
                    base["average_speed_slope_coefficient"],
                    source="HCM Eq. 15-8 and Exhibit 15-13",
                ),
                IntermediateValue(
                    "average_speed_power_coefficient",
                    base["average_speed_power_coefficient"],
                    source="HCM Eq. 15-11 and Exhibit 15-19",
                ),
                IntermediateValue(
                    "average_speed",
                    base["average_speed_mph"],
                    "mph",
                    "HCM Eq. 15-7",
                ),
                IntermediateValue(
                    "percent_followers_at_capacity",
                    base["percent_followers_at_capacity"],
                    "%",
                    "HCM Eq. 15-18 and Exhibit 15-24",
                ),
                IntermediateValue(
                    "percent_followers_at_25_percent_capacity",
                    base["percent_followers_at_25_percent_capacity"],
                    "%",
                    "HCM Eq. 15-20 and Exhibit 15-26",
                ),
                IntermediateValue(
                    "percent_followers_slope_coefficient",
                    base["percent_followers_slope_coefficient"],
                    source="HCM Eq. 15-22 and Exhibit 15-28",
                ),
                IntermediateValue(
                    "percent_followers_power_coefficient",
                    base["percent_followers_power_coefficient"],
                    source="HCM Eq. 15-23 and Exhibit 15-29",
                ),
                IntermediateValue(
                    "percent_followers",
                    base["percent_followers"],
                    "%",
                    "HCM Eq. 15-17",
                ),
                IntermediateValue(
                    "follower_density",
                    base["follower_density_followers_mi_ln"],
                    "followers/mi/ln",
                    "HCM Eq. 15-35",
                ),
            ],
            assumptions=[
                "Validated only for HCM Chapter 26 Two-Lane Highway Example Problem 1.",
                "Applies to a level, straight Passing Constrained segment.",
                "Example Problem 1 opposing flow is 1,500 veh/h.",
            ],
        )


def _calculate_example_problem_2_result(
    parsed_inputs: TwoLaneExampleProblem2Inputs,
    base: dict[str, float | int | str],
) -> CalculationResult:
    subsegment_results = horizontal_curve_subsegment_speeds(
        subsegments=parsed_inputs.horizontal_alignment_subsegments,
        base_free_flow_speed_mph=float(base["base_free_flow_speed_mph"]),
        heavy_vehicle_percent=parsed_inputs.heavy_vehicle_percent,
        lane_shoulder_adjustment_mph=float(base["lane_shoulder_adjustment_mph"]),
        access_point_adjustment_mph=float(base["access_point_adjustment_mph"]),
        demand_flow_rate_veh_h=float(base["demand_flow_rate_veh_h"]),
        average_speed_power_coefficient=float(base["average_speed_power_coefficient"]),
        tangent_average_speed_mph=float(base["average_speed_mph"]),
    )
    adjusted_speed = length_weighted_adjusted_average_speed(subsegment_results)
    outputs = dict(base)
    outputs.update(
        {
            "tangent_free_flow_speed_mph": base["free_flow_speed_mph"],
            "tangent_average_speed_mph": base["average_speed_mph"],
            "horizontal_curve_subsegments": subsegment_results,
            "adjusted_average_speed_mph": adjusted_speed,
        }
    )

    intermediate_values = _calculate_example_problem_1_result(
        parsed_inputs,
        base,
    ).intermediate_values
    intermediate_values = [
        *intermediate_values,
        IntermediateValue(
            "tangent_free_flow_speed",
            base["free_flow_speed_mph"],
            "mph",
            "HCM Eq. 15-3",
        ),
        IntermediateValue(
            "tangent_average_speed",
            base["average_speed_mph"],
            "mph",
            "HCM Eq. 15-7",
        ),
    ]
    for subsegment in subsegment_results:
        if subsegment["subsegment_type"] == "horizontal_curve":
            index = subsegment["index"]
            intermediate_values.extend(
                [
                    IntermediateValue(
                        f"subsegment_{index}_horizontal_curve_bffs",
                        subsegment["base_free_flow_speed_mph"],
                        "mph",
                        "HCM Eq. 15-14",
                    ),
                    IntermediateValue(
                        f"subsegment_{index}_horizontal_curve_ffs",
                        subsegment["free_flow_speed_mph"],
                        "mph",
                        "HCM Eq. 15-13",
                    ),
                    IntermediateValue(
                        f"subsegment_{index}_horizontal_curve_speed_coefficient_m",
                        subsegment["speed_coefficient_m"],
                        source="HCM Eq. 15-15",
                    ),
                    IntermediateValue(
                        f"subsegment_{index}_horizontal_curve_average_speed",
                        subsegment["average_speed_mph"],
                        "mph",
                        "HCM Eq. 15-12",
                    ),
                ]
            )
    intermediate_values.append(
        IntermediateValue(
            "adjusted_average_speed",
            adjusted_speed,
            "mph",
            "HCM Eq. 15-16",
        )
    )

    return CalculationResult(
        method=TwoLaneHighwayChapter15Method.method_name,
        facility_type=TwoLaneHighwayChapter15Method.facility_type,
        outputs=outputs,
        intermediate_values=intermediate_values,
        assumptions=[
            "Validated only for HCM Chapter 26 Two-Lane Highway Example Problem 2.",
            "Applies to a level Passing Constrained segment with horizontal curves.",
            "Example Problem 2 reuses Example Problem 1 base segment calculations.",
            "Passing lane, facility, and downstream segment calculations are not implemented.",
        ],
    )


def _parse_example_problem_1_inputs(
    inputs: dict[str, Any],
) -> TwoLaneExampleProblem1Inputs:
    try:
        return TwoLaneExampleProblem1Inputs(
            segment_length_mi=float(inputs["segment_length_mi"]),
            segment_type=str(inputs["segment_type"]),
            analysis_direction_volume_veh_h=float(
                inputs["analysis_direction_volume_veh_h"]
            ),
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


def _parse_example_problem_2_inputs(
    inputs: dict[str, Any],
) -> TwoLaneExampleProblem2Inputs:
    try:
        subsegments = tuple(
            _parse_horizontal_alignment_subsegment(subsegment)
            for subsegment in inputs["horizontal_alignment_subsegments"]
        )
        return TwoLaneExampleProblem2Inputs(
            segment_length_mi=float(inputs["segment_length_mi"]),
            segment_type=str(inputs["segment_type"]),
            analysis_direction_volume_veh_h=float(
                inputs["analysis_direction_volume_veh_h"]
            ),
            peak_hour_factor=float(inputs["peak_hour_factor"]),
            posted_speed_mph=float(inputs["posted_speed_mph"]),
            heavy_vehicle_percent=float(inputs["heavy_vehicle_percent"]),
            grade_percent=float(inputs["grade_percent"]),
            horizontal_alignment=str(inputs["horizontal_alignment"]),
            lane_width_ft=float(inputs["lane_width_ft"]),
            shoulder_width_ft=float(inputs["shoulder_width_ft"]),
            access_point_density_per_mi=float(inputs["access_point_density_per_mi"]),
            upstream_passing_lane=bool(inputs["upstream_passing_lane"]),
            horizontal_alignment_subsegments=subsegments,
        )
    except KeyError as exc:
        raise HCMCalcError(f"Missing Example Problem 2 input: {exc.args[0]}") from exc


def _parse_horizontal_alignment_subsegment(
    subsegment: dict[str, Any],
) -> HorizontalAlignmentSubsegment:
    return HorizontalAlignmentSubsegment(
        subsegment_type=str(subsegment["type"]),
        length_ft=float(subsegment["length_ft"]),
        superelevation_percent=_optional_float(subsegment.get("superelevation_percent")),
        radius_ft=_optional_float(subsegment.get("radius_ft")),
        central_angle_deg=_optional_float(subsegment.get("central_angle_deg")),
        horizontal_class=_optional_int(subsegment.get("horizontal_class")),
    )


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _validate_example_problem_1_scope(inputs: TwoLaneExampleProblem1Inputs) -> None:
    if inputs.segment_type != PASSING_CONSTRAINED:
        raise MethodNotImplementedError(
            "Only Passing Constrained segments are implemented."
        )
    if inputs.horizontal_alignment != STRAIGHT_ALIGNMENT:
        raise MethodNotImplementedError(
            "Only straight horizontal alignment is implemented."
        )
    if inputs.upstream_passing_lane:
        raise MethodNotImplementedError(
            "Upstream passing lane adjustment is not implemented."
        )
    if inputs.peak_hour_factor <= 0:
        raise HCMCalcError("peak_hour_factor must be greater than zero.")


def _validate_example_problem_2_scope(inputs: TwoLaneExampleProblem2Inputs) -> None:
    if inputs.segment_type != PASSING_CONSTRAINED:
        raise MethodNotImplementedError(
            "Only Passing Constrained segments are implemented."
        )
    if inputs.horizontal_alignment != HORIZONTAL_CURVES_ALIGNMENT:
        raise MethodNotImplementedError(
            "Only Example Problem 2 horizontal curve alignment is implemented."
        )
    if inputs.upstream_passing_lane:
        raise MethodNotImplementedError(
            "Upstream passing lane adjustment is not implemented."
        )
    if inputs.peak_hour_factor <= 0:
        raise HCMCalcError("peak_hour_factor must be greater than zero.")
    if len(inputs.horizontal_alignment_subsegments) != 11:
        raise HCMCalcError("Example Problem 2 requires 11 horizontal subsegments.")

    total_length_ft = 0.0
    for subsegment in inputs.horizontal_alignment_subsegments:
        if subsegment.length_ft <= 0:
            raise HCMCalcError("Horizontal subsegment length must be positive.")
        total_length_ft += subsegment.length_ft
        if subsegment.subsegment_type == "horizontal_curve":
            _validate_horizontal_curve_subsegment(subsegment)
        elif subsegment.subsegment_type != "tangent":
            raise HCMCalcError(
                "Horizontal subsegment type must be tangent or horizontal_curve."
            )

    expected_length_ft = inputs.segment_length_mi * 5280.0
    if abs(total_length_ft - expected_length_ft) > 1.0:
        raise HCMCalcError(
            "Horizontal subsegment lengths must match the segment length."
        )


def _validate_horizontal_curve_subsegment(
    subsegment: HorizontalAlignmentSubsegment,
) -> None:
    if subsegment.superelevation_percent is None:
        raise HCMCalcError("Horizontal curve requires superelevation_percent.")
    if subsegment.radius_ft is None:
        raise HCMCalcError("Horizontal curve requires radius_ft.")
    if subsegment.central_angle_deg is None:
        raise HCMCalcError("Horizontal curve requires central_angle_deg.")
    if subsegment.horizontal_class not in HORIZONTAL_CURVE_SPEED_COEFFICIENTS:
        raise HCMCalcError("Horizontal curve class must be 1 through 5.")


def demand_flow_rate(
    analysis_direction_volume_veh_h: float,
    peak_hour_factor: float,
) -> float:
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
        raise HCMCalcError(
            "Passing Constrained vertical class 1 segment length must be 0.25 to 3.0 mi."
        )
    return 1


def base_free_flow_speed(posted_speed_mph: float) -> float:
    """HCM Eq. 15-2 BFFS estimate."""

    return 1.14 * posted_speed_mph


def lane_shoulder_adjustment(lane_width_ft: float, shoulder_width_ft: float) -> float:
    """HCM Eq. 15-5 lane and shoulder width adjustment."""

    if not 9.0 <= lane_width_ft <= 12.0:
        raise HCMCalcError("lane_width_ft must be within the HCM range of 9 to 12 ft.")
    if not 0.0 <= shoulder_width_ft <= 6.0:
        raise HCMCalcError(
            "shoulder_width_ft must be within the HCM range of 0 to 6 ft."
        )
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

    coefficients = HEAVY_VEHICLE_COEFFICIENTS[vertical_class]
    modeled = (
        coefficients.a0
        + coefficients.a1 * base_free_flow_speed_mph
        + coefficients.a2 * segment_length_mi
        + max(
            0.0,
            coefficients.a3
            + coefficients.a4 * base_free_flow_speed_mph
            + coefficients.a5 * segment_length_mi,
        )
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

    coefficients = SPEED_SLOPE_COEFFICIENTS[vertical_class]
    modeled = (
        coefficients.b0
        + coefficients.b1 * free_flow_speed_mph
        + coefficients.b2 * sqrt(opposing_flow_veh_h / 1000.0)
        + max(0.0, coefficients.b3) * sqrt(segment_length_mi)
        + max(0.0, coefficients.b4) * sqrt(heavy_vehicle_percent)
    )
    return max(coefficients.b5, modeled)


def average_speed_power_coefficient(
    vertical_class: int,
    free_flow_speed_mph: float,
    opposing_flow_veh_h: float,
    segment_length_mi: float,
    heavy_vehicle_percent: float,
) -> float:
    """HCM Eq. 15-11 power coefficient for Eq. 15-7."""

    coefficients = SPEED_POWER_COEFFICIENTS[vertical_class]
    opposing_flow_thousands = opposing_flow_veh_h / 1000.0
    modeled = (
        coefficients.f0
        + coefficients.f1 * free_flow_speed_mph
        + coefficients.f2 * segment_length_mi
        + coefficients.f3 * opposing_flow_thousands
        + coefficients.f4 * sqrt(opposing_flow_thousands)
        + coefficients.f5 * heavy_vehicle_percent
        + coefficients.f6 * sqrt(heavy_vehicle_percent)
        + coefficients.f7 * (segment_length_mi * heavy_vehicle_percent)
    )
    return max(coefficients.f8, modeled)


def average_speed(
    free_flow_speed_mph: float,
    demand_flow_rate_veh_h: float,
    slope_coefficient: float,
    power_coefficient: float,
) -> float:
    """HCM Eq. 15-7 Passing Constrained average speed."""

    if demand_flow_rate_veh_h <= 100.0:
        return free_flow_speed_mph
    return free_flow_speed_mph - slope_coefficient * (
        demand_flow_rate_veh_h / 1000.0 - 0.1
    ) ** power_coefficient


def horizontal_curve_base_free_flow_speed(
    base_free_flow_speed_mph: float,
    horizontal_class: int,
) -> float:
    """HCM Eq. 15-14 horizontal curve BFFS."""

    if horizontal_class not in HORIZONTAL_CURVE_SPEED_COEFFICIENTS:
        raise HCMCalcError("Horizontal curve class must be 1 through 5.")
    class_speed = (
        HORIZONTAL_CURVE_CLASS_SPEED_INTERCEPT
        - HORIZONTAL_CURVE_CLASS_SPEED_SLOPE * horizontal_class
    )
    return min(base_free_flow_speed_mph, class_speed)


def horizontal_curve_free_flow_speed(
    horizontal_curve_base_free_flow_speed_mph: float,
    heavy_vehicle_percent: float,
    lane_shoulder_adjustment_mph: float,
    access_point_adjustment_mph: float,
) -> float:
    """HCM Eq. 15-13 horizontal curve FFS."""

    return (
        horizontal_curve_base_free_flow_speed_mph
        - HORIZONTAL_CURVE_HEAVY_VEHICLE_COEFFICIENT * heavy_vehicle_percent
        - lane_shoulder_adjustment_mph
        - access_point_adjustment_mph
    )


def horizontal_curve_speed_coefficient_m(horizontal_class: int) -> float:
    """HCM Eq. 15-15 horizontal curve speed coefficient."""

    if horizontal_class not in HORIZONTAL_CURVE_SPEED_COEFFICIENTS:
        raise HCMCalcError("Horizontal curve class must be 1 through 5.")
    return HORIZONTAL_CURVE_SPEED_COEFFICIENTS[horizontal_class]


def horizontal_curve_average_speed(
    horizontal_curve_free_flow_speed_mph: float,
    demand_flow_rate_veh_h: float,
    speed_coefficient_m: float,
    average_speed_power_coefficient: float,
    tangent_average_speed_mph: float,
) -> float:
    """HCM Eq. 15-12 horizontal curve average speed."""

    if demand_flow_rate_veh_h <= 100.0:
        curve_speed = horizontal_curve_free_flow_speed_mph
    else:
        curve_speed = horizontal_curve_free_flow_speed_mph - speed_coefficient_m * (
            demand_flow_rate_veh_h / 1000.0 - 0.1
        ) ** average_speed_power_coefficient
    return min(tangent_average_speed_mph, curve_speed)


def horizontal_curve_subsegment_speeds(
    subsegments: tuple[HorizontalAlignmentSubsegment, ...],
    base_free_flow_speed_mph: float,
    heavy_vehicle_percent: float,
    lane_shoulder_adjustment_mph: float,
    access_point_adjustment_mph: float,
    demand_flow_rate_veh_h: float,
    average_speed_power_coefficient: float,
    tangent_average_speed_mph: float,
) -> list[dict[str, float | int | str | None]]:
    """Calculate tangent and curve subsegment speeds for HCM Eq. 15-16."""

    results: list[dict[str, float | int | str | None]] = []
    for index, subsegment in enumerate(subsegments, start=1):
        result: dict[str, float | int | str | None] = {
            "index": index,
            "subsegment_type": subsegment.subsegment_type,
            "length_ft": subsegment.length_ft,
            "superelevation_percent": subsegment.superelevation_percent,
            "radius_ft": subsegment.radius_ft,
            "central_angle_deg": subsegment.central_angle_deg,
            "horizontal_class": subsegment.horizontal_class,
        }
        if subsegment.subsegment_type == "tangent":
            result.update(
                {
                    "base_free_flow_speed_mph": base_free_flow_speed_mph,
                    "free_flow_speed_mph": None,
                    "speed_coefficient_m": None,
                    "average_speed_mph": tangent_average_speed_mph,
                }
            )
        else:
            horizontal_class = _required_horizontal_class(subsegment)
            curve_bffs = horizontal_curve_base_free_flow_speed(
                base_free_flow_speed_mph,
                horizontal_class,
            )
            curve_ffs = horizontal_curve_free_flow_speed(
                horizontal_curve_base_free_flow_speed_mph=curve_bffs,
                heavy_vehicle_percent=heavy_vehicle_percent,
                lane_shoulder_adjustment_mph=lane_shoulder_adjustment_mph,
                access_point_adjustment_mph=access_point_adjustment_mph,
            )
            curve_m = horizontal_curve_speed_coefficient_m(horizontal_class)
            curve_speed = horizontal_curve_average_speed(
                horizontal_curve_free_flow_speed_mph=curve_ffs,
                demand_flow_rate_veh_h=demand_flow_rate_veh_h,
                speed_coefficient_m=curve_m,
                average_speed_power_coefficient=average_speed_power_coefficient,
                tangent_average_speed_mph=tangent_average_speed_mph,
            )
            result.update(
                {
                    "base_free_flow_speed_mph": curve_bffs,
                    "free_flow_speed_mph": curve_ffs,
                    "speed_coefficient_m": curve_m,
                    "average_speed_mph": curve_speed,
                }
            )
        results.append(result)
    return results


def _required_horizontal_class(subsegment: HorizontalAlignmentSubsegment) -> int:
    if subsegment.horizontal_class is None:
        raise HCMCalcError("Horizontal curve class must be 1 through 5.")
    return subsegment.horizontal_class


def length_weighted_adjusted_average_speed(
    subsegment_results: list[dict[str, float | int | str | None]],
) -> float:
    """HCM Eq. 15-16 segment speed weighted by subsegment length."""

    total_length = sum(float(subsegment["length_ft"]) for subsegment in subsegment_results)
    if total_length <= 0:
        raise HCMCalcError("Total subsegment length must be positive.")
    speed_distance_sum = sum(
        float(subsegment["length_ft"]) * float(subsegment["average_speed_mph"])
        for subsegment in subsegment_results
    )
    return speed_distance_sum / total_length


def percent_followers_at_capacity(
    vertical_class: int,
    segment_length_mi: float,
    free_flow_speed_mph: float,
    heavy_vehicle_percent: float,
    opposing_flow_veh_h: float,
) -> float:
    """HCM Eq. 15-18 PF at capacity for Passing Constrained segments."""

    coefficients = PF_CAPACITY_COEFFICIENTS[vertical_class]
    return _percent_followers_capacity_value(
        coefficients,
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

    coefficients = PF_25_CAPACITY_COEFFICIENTS[vertical_class]
    return _percent_followers_capacity_value(
        coefficients,
        segment_length_mi,
        free_flow_speed_mph,
        heavy_vehicle_percent,
        opposing_flow_veh_h,
    )


def _percent_followers_capacity_value(
    coefficients: PercentFollowersCapacityCoefficients,
    segment_length_mi: float,
    free_flow_speed_mph: float,
    heavy_vehicle_percent: float,
    opposing_flow_veh_h: float,
) -> float:
    opposing_flow_thousands = opposing_flow_veh_h / 1000.0
    return (
        coefficients.c0
        + coefficients.c1 * segment_length_mi
        + coefficients.c2 * sqrt(segment_length_mi)
        + coefficients.c3 * free_flow_speed_mph
        + coefficients.c4 * sqrt(free_flow_speed_mph)
        + coefficients.c5 * heavy_vehicle_percent
        + coefficients.c6 * (free_flow_speed_mph * opposing_flow_thousands)
        + coefficients.c7 * sqrt(opposing_flow_thousands)
    )


def percent_followers_slope_coefficient(
    segment_type: str,
    percent_followers_capacity: float,
    percent_followers_25_capacity: float,
    capacity_veh_h: float,
) -> float:
    """HCM Eq. 15-22 slope coefficient for Eq. 15-17."""

    coefficients = PF_SLOPE_COEFFICIENTS[segment_type]
    term_25_cap = _percent_followers_capacity_log_term(
        percent_followers_25_capacity,
        capacity_veh_h,
        capacity_multiplier=0.25,
    )
    term_cap = _percent_followers_capacity_log_term(
        percent_followers_capacity,
        capacity_veh_h,
        capacity_multiplier=1.0,
    )
    return coefficients.d1 * term_25_cap + coefficients.d2 * term_cap


def percent_followers_power_coefficient(
    segment_type: str,
    percent_followers_capacity: float,
    percent_followers_25_capacity: float,
    capacity_veh_h: float,
) -> float:
    """HCM Eq. 15-23 power coefficient for Eq. 15-17."""

    coefficients = PF_POWER_COEFFICIENTS[segment_type]
    term_25_cap = _percent_followers_capacity_log_term(
        percent_followers_25_capacity,
        capacity_veh_h,
        capacity_multiplier=0.25,
    )
    term_cap = _percent_followers_capacity_log_term(
        percent_followers_capacity,
        capacity_veh_h,
        capacity_multiplier=1.0,
    )
    return (
        coefficients.e0
        + coefficients.e1 * term_25_cap
        + coefficients.e2 * term_cap
        + coefficients.e3 * sqrt(term_25_cap)
        + coefficients.e4 * sqrt(term_cap)
    )


def _percent_followers_capacity_log_term(
    percent_followers_value: float,
    capacity_veh_h: float,
    capacity_multiplier: float,
) -> float:
    return -log(1.0 - percent_followers_value / 100.0) / (
        capacity_multiplier * (capacity_veh_h / 1000.0)
    )


def percent_followers(
    demand_flow_rate_veh_h: float,
    slope_coefficient: float,
    power_coefficient: float,
) -> float:
    """HCM Eq. 15-17 Passing Constrained percent followers."""

    return 100.0 * (
        1.0
        - exp(slope_coefficient * (demand_flow_rate_veh_h / 1000.0) ** power_coefficient)
    )


def follower_density(
    demand_flow_rate_veh_h: float,
    average_speed_mph: float,
    percent_followers_value: float,
) -> float:
    """HCM Eq. 15-35 follower density."""

    return demand_flow_rate_veh_h / average_speed_mph * (percent_followers_value / 100.0)


def level_of_service(
    follower_density_followers_mi_ln: float,
    posted_speed_mph: float,
) -> str:
    """HCM Exhibit 15-6 LOS thresholds for two-lane highways."""

    if posted_speed_mph < 50.0:
        thresholds = (2.5, 5.0, 10.0, 15.0, 20.0)
    else:
        thresholds = (2.0, 4.0, 8.0, 12.0, 18.0)

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
