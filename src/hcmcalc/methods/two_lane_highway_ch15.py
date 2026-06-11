"""HCM 7th Edition Chapter 15 Two-Lane Highway method.

The implemented calculation paths are scoped to Chapter 26 Example Problems 1
through 4 and are intentionally kept independent from any UI.
"""

from math import exp, isfinite, log, sqrt
from typing import Any

from hcmcalc.core import (
    CalculationResult,
    HCMCalcError,
    IntermediateValue,
    MethodNotImplementedError,
)
from hcmcalc.methods.two_lane_highway_coefficients import (
    HEAVY_VEHICLE_COEFFICIENTS,
    HORIZONTAL_CURVE_BFFS_SLOPE,
    HORIZONTAL_CURVE_CLASS_SPEED_INTERCEPT,
    HORIZONTAL_CURVE_CLASS_SPEED_SLOPE,
    HORIZONTAL_CURVE_HEAVY_VEHICLE_COEFFICIENT,
    HORIZONTAL_CURVE_SPEED_COEFFICIENTS,
    PASSING_LANE_PF_25_CAPACITY_COEFFICIENTS,
    PASSING_LANE_PF_CAPACITY_COEFFICIENTS,
    PASSING_LANE_SPEED_POWER_COEFFICIENTS,
    PASSING_LANE_SPEED_SLOPE_B3_C1,
    PASSING_LANE_SPEED_SLOPE_B4_D1,
    PASSING_LANE_SPEED_SLOPE_BASE_COEFFICIENTS,
    PF_25_CAPACITY_COEFFICIENTS,
    PF_CAPACITY_COEFFICIENTS,
    PF_POWER_COEFFICIENTS,
    PF_SLOPE_COEFFICIENTS,
    PercentFollowersCapacityCoefficients,
    SPEED_POWER_COEFFICIENTS,
    SPEED_SLOPE_AUXILIARY_COEFFICIENTS,
    SPEED_SLOPE_COEFFICIENTS,
)
from hcmcalc.methods.two_lane_highway_models import (
    HORIZONTAL_CURVES_ALIGNMENT,
    OPPOSING_FLOW_EXAMPLE_1_VEH_H,
    PASSING_CONSTRAINED,
    PASSING_LANE,
    PASSING_ZONE,
    STRAIGHT_ALIGNMENT,
    HorizontalAlignmentSubsegment,
    TwoLaneExampleProblem1Inputs,
    TwoLaneExampleProblem2Inputs,
    TwoLaneExampleProblem3Inputs,
    TwoLaneFacilitySegmentInputs,
)
from hcmcalc.methods.two_lane_highway_scope import require_supported_vertical_scope


class TwoLaneHighwayChapter15Method:
    """Partial two-lane highway motorized vehicle analysis implementation."""

    facility_type = "two_lane_highway"
    method_name = "hcm7_ch15_two_lane_motorized"

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        """Run the validated Chapter 26 Example Problem 1 or 2 calculation path."""

        case_id = inputs.get("case_id")
        if case_id not in {"TLH-CH15-001", "TLH-CH15-002", "TLH-CH15-003", "TLH-CH15-004"}:
            raise MethodNotImplementedError(
                "Only HCM Chapter 26 Two-Lane Highway Example Problems 1 through 4 "
                "are implemented. Additional Chapter 15 cases require "
                "methodology mapping and validation before implementation."
            )

        if case_id in {"TLH-CH15-003", "TLH-CH15-004"}:
            parsed_inputs = _parse_example_problem_3_inputs(inputs)
            _validate_facility_example_scope(parsed_inputs)
            return _calculate_facility_example_result(parsed_inputs)

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

    def calculate_single_segment(self, inputs: dict[str, Any]) -> CalculationResult:
        """Calculate one segment within the validated manual-input scope."""

        try:
            segment = _parse_facility_segment({"segment_id": 1, **inputs})
        except KeyError as exc:
            raise HCMCalcError(
                "Single-segment calculation requires "
                f"{_single_segment_input_label(exc.args[0])}."
            ) from exc
        except (TypeError, ValueError) as exc:
            raise HCMCalcError(
                "Single-segment inputs must use valid numeric values."
            ) from exc

        _validate_single_segment_scope(segment)
        outputs = _calculate_facility_segment(segment)
        warnings = []
        if segment.segment_type == PASSING_LANE:
            warnings.append(
                "Single-segment passing lane results do not represent downstream "
                "passing-lane effects or full facility performance. Use facility "
                "analysis for corridor-level evaluation."
            )
        if segment.horizontal_alignment == HORIZONTAL_CURVES_ALIGNMENT:
            warnings.append(
                "Manual horizontal curve support is limited to the validated "
                "Example Problem 2 calculation path."
            )
        alignment_assumption = (
            "Analysis is limited to one straight two-lane highway segment."
            if segment.horizontal_alignment == STRAIGHT_ALIGNMENT
            else "Horizontal curve adjustment uses the validated Example Problem 2 calculation path."
        )
        assumptions = [
            alignment_assumption,
            "Motorized Vehicle LOS is based on follower density.",
            *_single_segment_type_assumptions(segment),
            "No upstream passing lane or downstream facility-wide effects are applied.",
        ]
        return CalculationResult(
            method=self.method_name,
            facility_type=self.facility_type,
            outputs=outputs,
            intermediate_values=_single_segment_intermediate_values(outputs),
            assumptions=assumptions,
            warnings=warnings,
        )


def _single_segment_input_label(name: str) -> str:
    labels = {
        "segment_type": "a segment type",
        "segment_length_mi": "a segment length",
        "posted_speed_mph": "a posted/base speed",
        "analysis_direction_volume_veh_h": "an analysis-direction volume",
        "peak_hour_factor": "a peak hour factor (PHF)",
        "heavy_vehicle_percent": "a heavy-vehicle percentage",
        "grade_percent": "a terrain grade",
        "horizontal_alignment": "a horizontal alignment",
        "lane_width_ft": "a lane width",
        "shoulder_width_ft": "a shoulder width",
        "access_point_density_per_mi": "an access-point density",
    }
    return labels.get(name, f"the {name} input")


def _single_segment_type_assumptions(
    segment: TwoLaneFacilitySegmentInputs,
) -> list[str]:
    if segment.segment_type == PASSING_ZONE:
        return [
            "Passing Zone behavior uses the submitted opposing-direction volume, "
            "converted to opposing demand flow using the submitted PHF."
        ]
    if segment.segment_type == PASSING_LANE:
        return [
            "Passing Lane LOS uses the supported single-segment midpoint follower "
            "density calculation and does not approximate downstream effects."
        ]
    return [
        "Passing Constrained calculations use the HCM-required 1,500 veh/h "
        "opposing-flow assumption."
    ]


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


def _calculate_facility_example_result(
    parsed_inputs: TwoLaneExampleProblem3Inputs,
) -> CalculationResult:
    segment_results = [
        _calculate_facility_segment(segment) for segment in parsed_inputs.segments
    ]
    passing_lane_index = next(
        index for index, segment in enumerate(parsed_inputs.segments)
        if segment.segment_type == PASSING_LANE
    )
    passing_lane_result = segment_results[passing_lane_index]
    upstream_result = segment_results[passing_lane_index - 1]

    effective_length = passing_lane_effective_length(
        upstream_follower_density_followers_mi_ln=float(
            upstream_result["follower_density_followers_mi_ln"]
        ),
        upstream_percent_followers=float(upstream_result["percent_followers"]),
        upstream_demand_flow_rate_veh_h=float(upstream_result["demand_flow_rate_veh_h"]),
        upstream_average_speed_mph=float(upstream_result["average_speed_mph"]),
        passing_lane_length_mi=float(passing_lane_result["segment_length_mi"]),
    )
    passing_lane_result["downstream_effective_length_mi"] = effective_length[
        "effective_length_mi"
    ]
    passing_lane_result["effective_length_percent_followers_zero_mi"] = (
        effective_length["percent_followers_zero_mi"]
    )
    passing_lane_result["effective_length_95_percent_density_mi"] = effective_length[
        "density_95_percent_mi"
    ]

    passing_lane_start_distance = sum(
        float(result["segment_length_mi"]) for result in segment_results[:passing_lane_index]
    )
    downstream_distance = float(passing_lane_result["segment_length_mi"])
    for result in segment_results[passing_lane_index + 1:]:
        downstream_distance += float(result["segment_length_mi"])
        distance_from_passing_lane_start = (
            passing_lane_start_distance + downstream_distance
        )
        within_effective_length = downstream_distance <= float(
            effective_length["effective_length_mi"]
        )
        result["downstream_distance_mi"] = downstream_distance
        result["distance_from_facility_start_mi"] = distance_from_passing_lane_start
        result["within_passing_lane_effective_length"] = within_effective_length
        if within_effective_length:
            adjustment = downstream_follower_density_adjustment(
                percent_followers_value=float(result["percent_followers"]),
                demand_flow_rate_veh_h=float(result["demand_flow_rate_veh_h"]),
                average_speed_mph=float(result["average_speed_mph"]),
                downstream_distance_mi=downstream_distance,
                upstream_percent_followers=float(upstream_result["percent_followers"]),
                passing_lane_length_mi=float(passing_lane_result["segment_length_mi"]),
            )
            result["unadjusted_follower_density_followers_mi_ln"] = result[
                "follower_density_followers_mi_ln"
            ]
            result["percent_followers_improvement_percent"] = adjustment[
                "percent_followers_improvement_percent"
            ]
            result["speed_improvement_percent"] = adjustment[
                "speed_improvement_percent"
            ]
            result["follower_density_followers_mi_ln"] = adjustment[
                "adjusted_follower_density_followers_mi_ln"
            ]
            result["level_of_service"] = level_of_service(
                float(result["follower_density_followers_mi_ln"]),
                float(result["posted_speed_mph"]),
            )

    facility_density = length_weighted_average(
        [
            (
                round(float(result["follower_density_followers_mi_ln"]), 1),
                float(result["segment_length_mi"]),
            )
            for result in segment_results
        ]
    )
    facility_speed = length_weighted_average(
        [
            (float(result["average_speed_mph"]), float(result["segment_length_mi"]))
            for result in segment_results
        ]
    )
    facility_los = level_of_service(
        facility_density,
        parsed_inputs.segments[0].posted_speed_mph,
    )

    outputs = {
        "facility_length_mi": parsed_inputs.facility_length_mi,
        "segments": segment_results,
        "facility_follower_density_followers_mi_ln": facility_density,
        "facility_average_speed_mph": facility_speed,
        "facility_level_of_service": facility_los,
    }
    intermediate_values = _facility_intermediate_values(segment_results, outputs)

    return CalculationResult(
        method=TwoLaneHighwayChapter15Method.method_name,
        facility_type=TwoLaneHighwayChapter15Method.facility_type,
        outputs=outputs,
        intermediate_values=intermediate_values,
        assumptions=[
            f"Validated only for HCM Chapter 26 Two-Lane Highway Example Problem {parsed_inputs.case_id[-1]}.",
            "Passing Constrained FFS and percent-followers calculations use the HCM-required 1,500 veh/h opposing flow assumption.",
            "Passing Zone calculations use actual opposing demand flow from the fixture.",
            "Passing Lane calculations are scoped to the validated vertical class 1 path.",
            "Facility follower density follows the Chapter 26 examples' displayed one-decimal segment-density convention.",
        ],
        warnings=(
            [
                "Mountainous terrain with long grade interactions may require microsimulation for detailed design; HCM Chapter 15 macroscopic method may not fully capture upstream/downstream interaction."
            ]
            if parsed_inputs.case_id == "TLH-CH15-004"
            else []
        ),
    )


def _calculate_facility_segment(
    segment: TwoLaneFacilitySegmentInputs,
) -> dict[str, Any]:
    demand = demand_flow_rate(
        segment.analysis_direction_volume_veh_h,
        segment.peak_hour_factor,
    )
    opposing_flow = _facility_segment_opposing_flow(segment)
    capacity = facility_segment_capacity(
        segment.segment_type,
        segment.heavy_vehicle_percent,
    )
    vertical_class = vertical_alignment_class(segment.segment_length_mi, segment.grade_percent)
    bffs = base_free_flow_speed(segment.posted_speed_mph)
    f_ls = lane_shoulder_adjustment(segment.lane_width_ft, segment.shoulder_width_ft)
    f_a = access_point_adjustment(segment.access_point_density_per_mi)
    hv_coefficient = heavy_vehicle_ffs_coefficient(
        vertical_class,
        bffs,
        segment.segment_length_mi,
        opposing_flow,
    )
    ffs = estimated_free_flow_speed(
        bffs,
        hv_coefficient,
        segment.heavy_vehicle_percent,
        f_ls,
        f_a,
    )

    if segment.segment_type == PASSING_LANE:
        speed_m = passing_lane_average_speed_slope_coefficient(
            vertical_class,
            ffs,
            opposing_flow,
            segment.segment_length_mi,
            segment.heavy_vehicle_percent,
        )
        speed_p = passing_lane_average_speed_power_coefficient(
            vertical_class,
            ffs,
            opposing_flow,
            segment.segment_length_mi,
            segment.heavy_vehicle_percent,
        )
        pf_cap = passing_lane_percent_followers_at_capacity(
            vertical_class,
            segment.segment_length_mi,
            ffs,
            segment.heavy_vehicle_percent,
        )
        pf_25_cap = passing_lane_percent_followers_at_25_percent_capacity(
            vertical_class,
            segment.segment_length_mi,
            ffs,
            segment.heavy_vehicle_percent,
        )
    else:
        speed_m = average_speed_slope_coefficient(
            vertical_class,
            ffs,
            opposing_flow,
            segment.segment_length_mi,
            segment.heavy_vehicle_percent,
        )
        speed_p = average_speed_power_coefficient(
            vertical_class,
            ffs,
            opposing_flow,
            segment.segment_length_mi,
            segment.heavy_vehicle_percent,
        )
        pf_cap = percent_followers_at_capacity(
            vertical_class,
            segment.segment_length_mi,
            ffs,
            segment.heavy_vehicle_percent,
            opposing_flow,
        )
        pf_25_cap = percent_followers_at_25_percent_capacity(
            vertical_class,
            segment.segment_length_mi,
            ffs,
            segment.heavy_vehicle_percent,
            opposing_flow,
        )

    speed = average_speed(ffs, demand, speed_m, speed_p)
    horizontal_results: list[dict[str, Any]] = []
    if segment.horizontal_alignment_subsegments:
        horizontal_results = horizontal_curve_subsegment_speeds(
            segment.horizontal_alignment_subsegments,
            bffs,
            segment.heavy_vehicle_percent,
            f_ls,
            f_a,
            demand,
            speed_p,
            speed,
        )
        speed = length_weighted_adjusted_average_speed(horizontal_results)
    pf_m = percent_followers_slope_coefficient(segment.segment_type, pf_cap, pf_25_cap, capacity)
    pf_p = percent_followers_power_coefficient(segment.segment_type, pf_cap, pf_25_cap, capacity)
    followers = percent_followers(demand, pf_m, pf_p)
    density = follower_density(demand, speed, followers)
    los = level_of_service(density, segment.posted_speed_mph)

    result: dict[str, Any] = {
        "segment_id": segment.segment_id,
        "segment_type": segment.segment_type,
        "segment_length_mi": segment.segment_length_mi,
        "posted_speed_mph": segment.posted_speed_mph,
        "demand_flow_rate_veh_h": demand,
        "opposing_flow_rate_veh_h": opposing_flow,
        "capacity_veh_h": capacity,
        "demand_capacity_ratio": demand / capacity,
        "vertical_class": vertical_class,
        "base_free_flow_speed_mph": bffs,
        "lane_shoulder_adjustment_mph": f_ls,
        "access_point_adjustment_mph": f_a,
        "heavy_vehicle_ffs_coefficient": hv_coefficient,
        "free_flow_speed_mph": ffs,
        "average_speed_slope_coefficient": speed_m,
        "average_speed_power_coefficient": speed_p,
        "average_speed_mph": speed,
        "horizontal_curve_subsegments": horizontal_results,
        "percent_followers_at_capacity": pf_cap,
        "percent_followers_at_25_percent_capacity": pf_25_cap,
        "percent_followers_slope_coefficient": pf_m,
        "percent_followers_power_coefficient": pf_p,
        "percent_followers": followers,
        "follower_density_followers_mi_ln": density,
        "level_of_service": los,
    }

    if segment.segment_type == PASSING_LANE:
        passing_lane_values = passing_lane_midpoint_values(
            demand_flow_rate_veh_h=demand,
            base_free_flow_speed_mph=bffs,
            heavy_vehicle_coefficient=hv_coefficient,
            lane_shoulder_adjustment_mph=f_ls,
            access_point_adjustment_mph=f_a,
            vertical_class=vertical_class,
            segment_length_mi=segment.segment_length_mi,
            heavy_vehicle_percent=segment.heavy_vehicle_percent,
            capacity_veh_h=capacity,
        )
        result.update(passing_lane_values)
        result["follower_density_endpoint_followers_mi_ln"] = density
        result["follower_density_followers_mi_ln"] = passing_lane_values[
            "midpoint_follower_density_followers_mi_ln"
        ]
        result["level_of_service"] = level_of_service(
            float(result["follower_density_followers_mi_ln"]),
            segment.posted_speed_mph,
        )

    return result


def _facility_segment_opposing_flow(segment: TwoLaneFacilitySegmentInputs) -> float:
    if segment.segment_type == PASSING_LANE:
        return 0.0
    if segment.segment_type == PASSING_ZONE:
        if segment.opposing_direction_volume_veh_h is None:
            raise HCMCalcError("Passing Zone segment requires opposing flow.")
        return demand_flow_rate(
            segment.opposing_direction_volume_veh_h,
            segment.peak_hour_factor,
        )
    return OPPOSING_FLOW_EXAMPLE_1_VEH_H


def _single_segment_intermediate_values(
    outputs: dict[str, Any],
) -> list[IntermediateValue]:
    specs = [
        ("demand_flow_rate", "demand_flow_rate_veh_h", "veh/h", "HCM Eq. 15-1"),
        ("capacity", "capacity_veh_h", "veh/h", "HCM Ch. 15 Step 2"),
        ("vertical_alignment_class", "vertical_class", None, "HCM Exhibit 15-11"),
        ("base_free_flow_speed", "base_free_flow_speed_mph", "mph", "HCM Eq. 15-2"),
        ("free_flow_speed", "free_flow_speed_mph", "mph", "HCM Eq. 15-3"),
        ("average_speed", "average_speed_mph", "mph", "HCM Eq. 15-7"),
        ("percent_followers", "percent_followers", "%", "HCM Eq. 15-17"),
        (
            "follower_density",
            "follower_density_followers_mi_ln",
            "followers/mi/ln",
            "HCM Eq. 15-35 or Eq. 15-34 for Passing Lane midpoint",
        ),
    ]
    return [
        IntermediateValue(name, outputs[key], units, source)
        for name, key, units, source in specs
    ]


def _facility_intermediate_values(
    segment_results: list[dict[str, Any]],
    outputs: dict[str, Any],
) -> list[IntermediateValue]:
    intermediate_values: list[IntermediateValue] = []
    for segment in segment_results:
        segment_id = segment["segment_id"]
        intermediate_values.extend(
            [
                IntermediateValue(
                    f"segment_{segment_id}_demand_flow_rate",
                    segment["demand_flow_rate_veh_h"],
                    "veh/h",
                    "HCM Eq. 15-1",
                ),
                IntermediateValue(
                    f"segment_{segment_id}_capacity",
                    segment["capacity_veh_h"],
                    "veh/h",
                    "HCM Ch. 15 Step 2",
                ),
                IntermediateValue(
                    f"segment_{segment_id}_vertical_alignment_class",
                    segment["vertical_class"],
                    source="HCM Exhibit 15-11",
                ),
                IntermediateValue(
                    f"segment_{segment_id}_heavy_vehicle_ffs_coefficient",
                    segment["heavy_vehicle_ffs_coefficient"],
                    source="HCM Eq. 15-4 and Exhibit 15-12",
                ),
                IntermediateValue(
                    f"segment_{segment_id}_free_flow_speed",
                    segment["free_flow_speed_mph"],
                    "mph",
                    "HCM Eq. 15-3",
                ),
                IntermediateValue(
                    f"segment_{segment_id}_average_speed_slope_coefficient",
                    segment["average_speed_slope_coefficient"],
                    source="HCM Eq. 15-8",
                ),
                IntermediateValue(
                    f"segment_{segment_id}_average_speed_power_coefficient",
                    segment["average_speed_power_coefficient"],
                    source="HCM Eq. 15-11",
                ),
                IntermediateValue(
                    f"segment_{segment_id}_average_speed",
                    segment["average_speed_mph"],
                    "mph",
                    "HCM Eq. 15-7",
                ),
                IntermediateValue(
                    f"segment_{segment_id}_percent_followers_at_capacity",
                    segment["percent_followers_at_capacity"],
                    "%",
                    "HCM Eq. 15-18 or Eq. 15-19",
                ),
                IntermediateValue(
                    f"segment_{segment_id}_percent_followers_at_25_percent_capacity",
                    segment["percent_followers_at_25_percent_capacity"],
                    "%",
                    "HCM Eq. 15-20 or Eq. 15-21",
                ),
                IntermediateValue(
                    f"segment_{segment_id}_percent_followers",
                    segment["percent_followers"],
                    "%",
                    "HCM Eq. 15-17",
                ),
                IntermediateValue(
                    f"segment_{segment_id}_follower_density",
                    segment["follower_density_followers_mi_ln"],
                    "followers/mi/ln",
                    "HCM Eq. 15-35 or Eq. 15-34 for Passing Lane midpoint",
                ),
            ]
        )
        for subsegment in segment["horizontal_curve_subsegments"]:
            if subsegment["subsegment_type"] == "horizontal_curve":
                intermediate_values.append(
                    IntermediateValue(
                        f"segment_{segment_id}_curve_{subsegment['index']}_average_speed",
                        subsegment["average_speed_mph"],
                        "mph",
                        "HCM Eq. 15-12 through Eq. 15-16",
                    )
                )
        if segment["segment_type"] == PASSING_LANE:
            intermediate_values.extend(
                [
                    IntermediateValue(
                        f"segment_{segment_id}_faster_lane_flow_rate",
                        segment["faster_lane_flow_rate_veh_h_ln"],
                        "veh/h/ln",
                        "HCM Eq. 15-26",
                    ),
                    IntermediateValue(
                        f"segment_{segment_id}_slower_lane_flow_rate",
                        segment["slower_lane_flow_rate_veh_h_ln"],
                        "veh/h/ln",
                        "HCM Eq. 15-27",
                    ),
                    IntermediateValue(
                        f"segment_{segment_id}_midpoint_follower_density",
                        segment["midpoint_follower_density_followers_mi_ln"],
                        "followers/mi/ln",
                        "HCM Eq. 15-34",
                    ),
                    IntermediateValue(
                        "passing_lane_effective_length",
                        segment["downstream_effective_length_mi"],
                        "mi",
                        "HCM Eq. 15-36 through Eq. 15-38",
                    ),
                ]
            )
        if "percent_followers_improvement_percent" in segment:
            intermediate_values.extend(
                [
                    IntermediateValue(
                        f"segment_{segment_id}_percent_followers_improvement",
                        segment["percent_followers_improvement_percent"],
                        "%",
                        "HCM Eq. 15-36",
                    ),
                    IntermediateValue(
                        f"segment_{segment_id}_speed_improvement",
                        segment["speed_improvement_percent"],
                        "%",
                        "HCM Eq. 15-37",
                    ),
                    IntermediateValue(
                        f"segment_{segment_id}_adjusted_follower_density",
                        segment["follower_density_followers_mi_ln"],
                        "followers/mi/ln",
                        "HCM Eq. 15-38",
                    ),
                ]
            )
    intermediate_values.extend(
        [
            IntermediateValue(
                "facility_follower_density",
                outputs["facility_follower_density_followers_mi_ln"],
                "followers/mi/ln",
                "HCM Eq. 15-39",
            ),
            IntermediateValue(
                "facility_average_speed",
                outputs["facility_average_speed_mph"],
                "mph",
                "Length-weighted segment average speed",
            ),
        ]
    )
    return intermediate_values


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


def _parse_example_problem_3_inputs(
    inputs: dict[str, Any],
) -> TwoLaneExampleProblem3Inputs:
    try:
        return TwoLaneExampleProblem3Inputs(
            case_id=str(inputs["case_id"]),
            facility_length_mi=float(inputs["facility_length_mi"]),
            upstream_passing_lane=bool(inputs["upstream_passing_lane"]),
            segments=tuple(
                _parse_facility_segment(segment) for segment in inputs["segments"]
            ),
        )
    except KeyError as exc:
        raise HCMCalcError(f"Missing Example Problem 3 input: {exc.args[0]}") from exc


def _parse_facility_segment(
    segment: dict[str, Any],
) -> TwoLaneFacilitySegmentInputs:
    return TwoLaneFacilitySegmentInputs(
        segment_id=int(segment["segment_id"]),
        segment_type=str(segment["segment_type"]),
        segment_length_mi=float(segment["segment_length_mi"]),
        posted_speed_mph=float(segment["posted_speed_mph"]),
        analysis_direction_volume_veh_h=float(
            segment["analysis_direction_volume_veh_h"]
        ),
        opposing_direction_volume_veh_h=_optional_float(
            segment.get("opposing_direction_volume_veh_h")
        ),
        peak_hour_factor=float(segment["peak_hour_factor"]),
        heavy_vehicle_percent=float(segment["heavy_vehicle_percent"]),
        grade_percent=float(segment["grade_percent"]),
        horizontal_alignment=str(segment["horizontal_alignment"]),
        lane_width_ft=float(segment["lane_width_ft"]),
        shoulder_width_ft=float(segment["shoulder_width_ft"]),
        access_point_density_per_mi=float(segment["access_point_density_per_mi"]),
        horizontal_alignment_subsegments=tuple(
            _parse_horizontal_alignment_subsegment(subsegment)
            for subsegment in segment.get("horizontal_alignment_subsegments", [])
        ),
        terrain_type=(
            str(segment["terrain_type"])
            if segment.get("terrain_type") is not None
            else None
        ),
        grade_length_mi=_optional_float(segment.get("grade_length_mi")),
        vertical_class=_optional_int(segment.get("vertical_class")),
    )


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


def _validate_facility_example_scope(inputs: TwoLaneExampleProblem3Inputs) -> None:
    if inputs.case_id not in {"TLH-CH15-003", "TLH-CH15-004"}:
        raise HCMCalcError("Facility example case_id must be TLH-CH15-003 or TLH-CH15-004.")
    if inputs.upstream_passing_lane:
        raise MethodNotImplementedError(
            "Example Problem 3 requires no upstream passing lane."
        )
    expected_count = 5 if inputs.case_id == "TLH-CH15-003" else 6
    if len(inputs.segments) != expected_count:
        raise HCMCalcError(f"{inputs.case_id} requires {expected_count} facility segments.")
    expected_types = (
        PASSING_CONSTRAINED,
        PASSING_LANE,
        PASSING_CONSTRAINED,
        PASSING_ZONE,
        PASSING_CONSTRAINED,
    ) if inputs.case_id == "TLH-CH15-003" else (
        PASSING_CONSTRAINED,
        PASSING_CONSTRAINED,
        PASSING_CONSTRAINED,
        PASSING_CONSTRAINED,
        PASSING_LANE,
        PASSING_CONSTRAINED,
    )
    if tuple(segment.segment_type for segment in inputs.segments) != expected_types:
        raise MethodNotImplementedError(
            "Only the Example Problem 3 segment sequence is implemented."
        )
    if [segment.segment_id for segment in inputs.segments] != list(range(1, expected_count + 1)):
        raise HCMCalcError(f"{inputs.case_id} segment IDs must be sequential.")
    total_length = sum(segment.segment_length_mi for segment in inputs.segments)
    if abs(total_length - inputs.facility_length_mi) > 0.001:
        raise HCMCalcError("Segment lengths must sum to facility_length_mi.")

    for segment in inputs.segments:
        if inputs.case_id == "TLH-CH15-003" and segment.horizontal_alignment != STRAIGHT_ALIGNMENT:
            raise MethodNotImplementedError(
                "Example Problem 3 is implemented only for straight segments."
            )
        if inputs.case_id == "TLH-CH15-003" and segment.grade_percent != 0.0:
            raise MethodNotImplementedError(
                "Example Problem 3 is implemented only for level terrain."
            )
        if segment.peak_hour_factor <= 0.0:
            raise HCMCalcError("peak_hour_factor must be greater than zero.")
        require_supported_vertical_scope(
            segment_type=segment.segment_type,
            grade_percent=segment.grade_percent,
            grade_length_mi=(
                segment.grade_length_mi
                if segment.grade_length_mi is not None
                else segment.segment_length_mi
            ),
            segment_length_mi=segment.segment_length_mi,
            heavy_vehicle_percent=segment.heavy_vehicle_percent,
            horizontal_alignment=segment.horizontal_alignment,
            terrain_type=segment.terrain_type,
            vertical_class=segment.vertical_class,
            validated_facility_example=True,
        )
        if segment.segment_type == PASSING_ZONE:
            if segment.opposing_direction_volume_veh_h is None:
                raise HCMCalcError(
                    "Passing Zone segments require opposing_direction_volume_veh_h."
                )
        elif segment.opposing_direction_volume_veh_h is not None:
            raise HCMCalcError(
                "Example Problem 3 only supplies opposing flow for Passing Zone segments."
            )
        for subsegment in segment.horizontal_alignment_subsegments:
            if subsegment.subsegment_type == "horizontal_curve":
                _validate_horizontal_curve_subsegment(subsegment)
        if segment.horizontal_alignment_subsegments:
            subsegment_length_ft = sum(
                subsegment.length_ft
                for subsegment in segment.horizontal_alignment_subsegments
            )
            if abs(subsegment_length_ft - segment.segment_length_mi * 5280.0) > 1.0:
                raise HCMCalcError(
                    "Horizontal subsegment lengths must match the facility segment length."
                )


def _validate_single_segment_scope(segment: TwoLaneFacilitySegmentInputs) -> None:
    if segment.segment_type not in {PASSING_CONSTRAINED, PASSING_ZONE, PASSING_LANE}:
        raise MethodNotImplementedError(
            f"Unsupported manual single-segment type: {segment.segment_type}."
        )
    if segment.horizontal_alignment not in {
        STRAIGHT_ALIGNMENT,
        HORIZONTAL_CURVES_ALIGNMENT,
    }:
        raise MethodNotImplementedError(
            f"Unsupported manual horizontal alignment: {segment.horizontal_alignment}."
        )
    if (
        segment.horizontal_alignment == STRAIGHT_ALIGNMENT
        and segment.horizontal_alignment_subsegments
    ):
        raise HCMCalcError("Straight alignment cannot include horizontal subsegments.")
    _validate_finite_single_segment_inputs(segment)
    if segment.segment_length_mi <= 0.0:
        raise HCMCalcError("Segment length must be greater than zero.")
    if segment.posted_speed_mph <= 0.0:
        raise HCMCalcError("Posted/base speed must be greater than zero.")
    if segment.analysis_direction_volume_veh_h < 0.0:
        raise HCMCalcError("Analysis-direction volume cannot be negative.")
    if not 0.0 < segment.peak_hour_factor <= 1.0:
        raise HCMCalcError(
            "Peak hour factor (PHF) must be greater than 0 and at most 1."
        )
    if not 0.0 <= segment.heavy_vehicle_percent <= 100.0:
        raise HCMCalcError("Heavy-vehicle percentage must be between 0 and 100.")
    if not 9.0 <= segment.lane_width_ft <= 12.0:
        raise HCMCalcError(
            "Lane width must be within the supported range of 9 to 12 ft."
        )
    if not 0.0 <= segment.shoulder_width_ft <= 6.0:
        raise HCMCalcError(
            "Shoulder width must be within the supported range of 0 to 6 ft."
        )
    if segment.access_point_density_per_mi < 0.0:
        raise HCMCalcError("Access-point density cannot be negative.")
    if (
        segment.opposing_direction_volume_veh_h is not None
        and segment.opposing_direction_volume_veh_h < 0.0
    ):
        raise HCMCalcError("Opposing-direction volume cannot be negative.")
    if (
        segment.segment_type == PASSING_ZONE
        and (
            segment.opposing_direction_volume_veh_h is None
            or segment.opposing_direction_volume_veh_h <= 0.0
        )
    ):
        raise HCMCalcError(
            "Passing Zone requires an opposing-direction volume greater than zero."
        )
    if (
        segment.segment_type != PASSING_ZONE
        and segment.opposing_direction_volume_veh_h is not None
    ):
        raise HCMCalcError(
            "Opposing-direction volume is accepted only for Passing Zone single "
            "segments."
        )
    require_supported_vertical_scope(
        segment_type=segment.segment_type,
        grade_percent=segment.grade_percent,
        grade_length_mi=(
            segment.grade_length_mi
            if segment.grade_length_mi is not None
            else segment.segment_length_mi
        ),
        segment_length_mi=segment.segment_length_mi,
        heavy_vehicle_percent=segment.heavy_vehicle_percent,
        horizontal_alignment=segment.horizontal_alignment,
        terrain_type=segment.terrain_type,
        vertical_class=segment.vertical_class,
    )
    if segment.horizontal_alignment == HORIZONTAL_CURVES_ALIGNMENT:
        _validate_manual_horizontal_curve_scope(segment)
    if (
        segment.horizontal_alignment == HORIZONTAL_CURVES_ALIGNMENT
        and not segment.horizontal_alignment_subsegments
    ):
        raise HCMCalcError("Horizontal curve alignment requires horizontal subsegments.")


def _validate_finite_single_segment_inputs(
    segment: TwoLaneFacilitySegmentInputs,
) -> None:
    fields = (
        ("Segment length", segment.segment_length_mi),
        ("Posted/base speed", segment.posted_speed_mph),
        ("Analysis-direction volume", segment.analysis_direction_volume_veh_h),
        ("Peak hour factor (PHF)", segment.peak_hour_factor),
        ("Heavy-vehicle percentage", segment.heavy_vehicle_percent),
        ("Terrain grade", segment.grade_percent),
        ("Lane width", segment.lane_width_ft),
        ("Shoulder width", segment.shoulder_width_ft),
        ("Access-point density", segment.access_point_density_per_mi),
    )
    for label, value in fields:
        if not isfinite(value):
            raise HCMCalcError(f"{label} must be a finite numeric value.")
    if (
        segment.opposing_direction_volume_veh_h is not None
        and not isfinite(segment.opposing_direction_volume_veh_h)
    ):
        raise HCMCalcError(
            "Opposing-direction volume must be a finite numeric value."
        )


def _validate_manual_horizontal_curve_scope(
    segment: TwoLaneFacilitySegmentInputs,
) -> None:
    if segment.segment_type != PASSING_CONSTRAINED or segment.grade_percent != 0.0:
        raise MethodNotImplementedError(
            "Manual horizontal curve calculation is supported only for a level "
            "Passing Constrained segment using the validated Example Problem 2 path."
        )
    if len(segment.horizontal_alignment_subsegments) != 11:
        raise HCMCalcError(
            "Manual horizontal curve calculation requires the 11-subsegment "
            "Example Problem 2 structure."
        )

    total_length_ft = 0.0
    curve_count = 0
    for subsegment in segment.horizontal_alignment_subsegments:
        if subsegment.length_ft <= 0.0:
            raise HCMCalcError("Horizontal subsegment length must be positive.")
        total_length_ft += subsegment.length_ft
        if subsegment.subsegment_type == "horizontal_curve":
            curve_count += 1
            _validate_horizontal_curve_subsegment(subsegment)
        elif subsegment.subsegment_type != "tangent":
            raise HCMCalcError(
                "Horizontal subsegment type must be tangent or horizontal_curve."
            )

    if curve_count == 0:
        raise HCMCalcError(
            "Horizontal curve alignment requires at least one horizontal_curve subsegment."
        )
    if abs(total_length_ft - segment.segment_length_mi * 5280.0) > 1.0:
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
    if subsegment.radius_ft <= 0.0:
        raise HCMCalcError("Horizontal curve radius_ft must be positive.")
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


def facility_segment_capacity(segment_type: str, heavy_vehicle_percent: float) -> float:
    """HCM Ch. 15 capacity for the Example Problem 3 segment types."""

    if segment_type in {PASSING_CONSTRAINED, PASSING_ZONE}:
        return passing_constrained_capacity()
    if segment_type == PASSING_LANE:
        if heavy_vehicle_percent != 8.0:
            raise MethodNotImplementedError(
                "Passing Lane capacity is implemented only for Example Problem 3."
            )
        return 1500.0
    raise MethodNotImplementedError(f"Unsupported two-lane segment type: {segment_type}")


def vertical_alignment_class(segment_length_mi: float, grade_percent: float) -> int:
    """HCM Exhibit 15-11 mapping for validated Examples 1 through 4."""

    decision = require_supported_vertical_scope(
        segment_type=PASSING_CONSTRAINED,
        grade_percent=grade_percent,
        grade_length_mi=segment_length_mi,
        segment_length_mi=segment_length_mi,
        heavy_vehicle_percent=8.0,
    )
    assert decision.vertical_class is not None
    return decision.vertical_class


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
    b3 = coefficients.b3
    b4 = coefficients.b4
    if vertical_class in SPEED_SLOPE_AUXILIARY_COEFFICIENTS:
        auxiliary = SPEED_SLOPE_AUXILIARY_COEFFICIENTS[vertical_class]
        b3 = (
            auxiliary.c0
            + auxiliary.c1 * sqrt(segment_length_mi)
            + auxiliary.c2 * free_flow_speed_mph
            + auxiliary.c3 * free_flow_speed_mph * sqrt(segment_length_mi)
        )
        b4 = (
            auxiliary.d0
            + auxiliary.d1 * sqrt(heavy_vehicle_percent)
            + auxiliary.d2 * free_flow_speed_mph
            + auxiliary.d3 * free_flow_speed_mph * sqrt(heavy_vehicle_percent)
        )
    modeled = (
        coefficients.b0
        + coefficients.b1 * free_flow_speed_mph
        + coefficients.b2 * sqrt(opposing_flow_veh_h / 1000.0)
        + max(0.0, b3) * sqrt(segment_length_mi)
        + max(0.0, b4) * sqrt(heavy_vehicle_percent)
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
        + HORIZONTAL_CURVE_BFFS_SLOPE * base_free_flow_speed_mph
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


def length_weighted_average(values_and_lengths: list[tuple[float, float]]) -> float:
    """HCM Eq. 15-39 length-weighted facility average pattern."""

    total_length = sum(length for _, length in values_and_lengths)
    if total_length <= 0:
        raise HCMCalcError("Total length must be positive.")
    return sum(value * length for value, length in values_and_lengths) / total_length


def passing_lane_average_speed_slope_coefficient(
    vertical_class: int,
    free_flow_speed_mph: float,
    opposing_flow_veh_h: float,
    segment_length_mi: float,
    heavy_vehicle_percent: float,
) -> float:
    """HCM Eq. 15-8 with Passing Lane coefficients from Exhibits 15-14/16/18."""

    coefficients = PASSING_LANE_SPEED_SLOPE_BASE_COEFFICIENTS[vertical_class]
    b3 = PASSING_LANE_SPEED_SLOPE_B3_C1[vertical_class] * sqrt(segment_length_mi)
    b4 = PASSING_LANE_SPEED_SLOPE_B4_D1[vertical_class] * sqrt(heavy_vehicle_percent)
    modeled = (
        coefficients.b0
        + coefficients.b1 * free_flow_speed_mph
        + coefficients.b2 * sqrt(opposing_flow_veh_h / 1000.0)
        + max(0.0, b3) * sqrt(segment_length_mi)
        + max(0.0, b4) * sqrt(heavy_vehicle_percent)
    )
    return max(coefficients.b5, modeled)


def passing_lane_average_speed_power_coefficient(
    vertical_class: int,
    free_flow_speed_mph: float,
    opposing_flow_veh_h: float,
    segment_length_mi: float,
    heavy_vehicle_percent: float,
) -> float:
    """HCM Eq. 15-11 with Passing Lane coefficients from Exhibit 15-20."""

    coefficients = PASSING_LANE_SPEED_POWER_COEFFICIENTS[vertical_class]
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


def passing_lane_percent_followers_at_capacity(
    vertical_class: int,
    segment_length_mi: float,
    free_flow_speed_mph: float,
    heavy_vehicle_percent: float,
) -> float:
    """HCM Eq. 15-19 PF at capacity for Passing Lane segments."""

    coefficients = PASSING_LANE_PF_CAPACITY_COEFFICIENTS[vertical_class]
    return _passing_lane_percent_followers_capacity_value(
        coefficients,
        segment_length_mi,
        free_flow_speed_mph,
        heavy_vehicle_percent,
    )


def passing_lane_percent_followers_at_25_percent_capacity(
    vertical_class: int,
    segment_length_mi: float,
    free_flow_speed_mph: float,
    heavy_vehicle_percent: float,
) -> float:
    """HCM Eq. 15-21 PF at 25 percent capacity for Passing Lane segments."""

    coefficients = PASSING_LANE_PF_25_CAPACITY_COEFFICIENTS[vertical_class]
    return _passing_lane_percent_followers_capacity_value(
        coefficients,
        segment_length_mi,
        free_flow_speed_mph,
        heavy_vehicle_percent,
    )


def _passing_lane_percent_followers_capacity_value(
    coefficients: PercentFollowersCapacityCoefficients,
    segment_length_mi: float,
    free_flow_speed_mph: float,
    heavy_vehicle_percent: float,
) -> float:
    return (
        coefficients.c0
        + coefficients.c1 * segment_length_mi
        + coefficients.c2 * sqrt(segment_length_mi)
        + coefficients.c3 * free_flow_speed_mph
        + coefficients.c4 * sqrt(free_flow_speed_mph)
        + coefficients.c5 * heavy_vehicle_percent
        + coefficients.c6 * sqrt(heavy_vehicle_percent)
        + coefficients.c7 * (free_flow_speed_mph * heavy_vehicle_percent)
    )


def passing_lane_midpoint_values(
    demand_flow_rate_veh_h: float,
    base_free_flow_speed_mph: float,
    heavy_vehicle_coefficient: float,
    lane_shoulder_adjustment_mph: float,
    access_point_adjustment_mph: float,
    vertical_class: int,
    segment_length_mi: float,
    heavy_vehicle_percent: float,
    capacity_veh_h: float,
) -> dict[str, float]:
    """HCM Eq. 15-24 through Eq. 15-34 for Example Problem 3 Passing Lane."""

    heavy_vehicle_count = demand_flow_rate_veh_h * heavy_vehicle_percent / 100.0
    faster_lane_proportion = passing_lane_faster_lane_flow_proportion(
        demand_flow_rate_veh_h,
        heavy_vehicle_count,
    )
    faster_lane_flow = demand_flow_rate_veh_h * faster_lane_proportion
    slower_lane_flow = demand_flow_rate_veh_h * (1.0 - faster_lane_proportion)
    faster_lane_hv_percent = passing_lane_faster_lane_heavy_vehicle_percent(
        heavy_vehicle_percent
    )
    slower_lane_hv_count = heavy_vehicle_count - (
        faster_lane_flow * faster_lane_hv_percent / 100.0
    )
    slower_lane_hv_percent = slower_lane_hv_count / slower_lane_flow * 100.0

    faster_lane_ffs = estimated_free_flow_speed(
        base_free_flow_speed_mph,
        heavy_vehicle_coefficient,
        faster_lane_hv_percent,
        lane_shoulder_adjustment_mph,
        access_point_adjustment_mph,
    )
    slower_lane_ffs = estimated_free_flow_speed(
        base_free_flow_speed_mph,
        heavy_vehicle_coefficient,
        slower_lane_hv_percent,
        lane_shoulder_adjustment_mph,
        access_point_adjustment_mph,
    )
    faster_lane_initial_speed = _passing_lane_lane_average_speed(
        vertical_class,
        faster_lane_ffs,
        faster_lane_flow,
        segment_length_mi,
        faster_lane_hv_percent,
    )
    slower_lane_initial_speed = _passing_lane_lane_average_speed(
        vertical_class,
        slower_lane_ffs,
        slower_lane_flow,
        segment_length_mi,
        slower_lane_hv_percent,
    )
    speed_difference = passing_lane_average_speed_differential_adjustment(
        demand_flow_rate_veh_h,
        heavy_vehicle_percent,
    )
    faster_lane_midpoint_speed = faster_lane_initial_speed + speed_difference / 2.0
    slower_lane_midpoint_speed = slower_lane_initial_speed - speed_difference / 2.0
    faster_lane_pf = _passing_lane_lane_percent_followers(
        vertical_class,
        segment_length_mi,
        faster_lane_ffs,
        faster_lane_hv_percent,
        faster_lane_flow,
        _passing_lane_lane_capacity(vertical_class, faster_lane_hv_percent),
    )
    slower_lane_pf = _passing_lane_lane_percent_followers(
        vertical_class,
        segment_length_mi,
        slower_lane_ffs,
        slower_lane_hv_percent,
        slower_lane_flow,
        _passing_lane_lane_capacity(vertical_class, slower_lane_hv_percent),
    )
    midpoint_density = passing_lane_midpoint_follower_density(
        faster_lane_flow,
        faster_lane_midpoint_speed,
        faster_lane_pf,
        slower_lane_flow,
        slower_lane_midpoint_speed,
        slower_lane_pf,
    )
    return {
        "heavy_vehicle_count_veh_h": heavy_vehicle_count,
        "faster_lane_flow_proportion": faster_lane_proportion,
        "faster_lane_flow_rate_veh_h_ln": faster_lane_flow,
        "slower_lane_flow_rate_veh_h_ln": slower_lane_flow,
        "faster_lane_heavy_vehicle_percent": faster_lane_hv_percent,
        "slower_lane_heavy_vehicle_count_veh_h": slower_lane_hv_count,
        "slower_lane_heavy_vehicle_percent": slower_lane_hv_percent,
        "faster_lane_free_flow_speed_mph": faster_lane_ffs,
        "slower_lane_free_flow_speed_mph": slower_lane_ffs,
        "faster_lane_initial_average_speed_mph": faster_lane_initial_speed,
        "slower_lane_initial_average_speed_mph": slower_lane_initial_speed,
        "average_speed_differential_adjustment_mph": speed_difference,
        "faster_lane_midpoint_average_speed_mph": faster_lane_midpoint_speed,
        "slower_lane_midpoint_average_speed_mph": slower_lane_midpoint_speed,
        "faster_lane_midpoint_percent_followers": faster_lane_pf,
        "slower_lane_midpoint_percent_followers": slower_lane_pf,
        "midpoint_follower_density_followers_mi_ln": midpoint_density,
    }


def passing_lane_faster_lane_flow_proportion(
    demand_flow_rate_veh_h: float,
    heavy_vehicle_count_veh_h: float,
) -> float:
    """HCM Eq. 15-25 faster-lane flow proportion."""

    return 0.92183 - 0.05022 * log(demand_flow_rate_veh_h) - (
        0.00030 * heavy_vehicle_count_veh_h
    )


def passing_lane_faster_lane_heavy_vehicle_percent(
    heavy_vehicle_percent: float,
) -> float:
    """HCM Eq. 15-28 faster-lane heavy vehicle percentage."""

    return heavy_vehicle_percent * 0.4


def passing_lane_average_speed_differential_adjustment(
    demand_flow_rate_veh_h: float,
    heavy_vehicle_percent: float,
) -> float:
    """HCM Eq. 15-31 midpoint lane speed differential adjustment."""

    return 2.750 + 0.00056 * demand_flow_rate_veh_h + (
        3.8521 * heavy_vehicle_percent / 100.0
    )


def passing_lane_midpoint_follower_density(
    faster_lane_flow_rate_veh_h_ln: float,
    faster_lane_midpoint_speed_mph: float,
    faster_lane_midpoint_percent_followers: float,
    slower_lane_flow_rate_veh_h_ln: float,
    slower_lane_midpoint_speed_mph: float,
    slower_lane_midpoint_percent_followers: float,
) -> float:
    """HCM Eq. 15-34 Passing Lane midpoint follower density."""

    faster_lane_density = (
        faster_lane_midpoint_percent_followers
        / 100.0
        * faster_lane_flow_rate_veh_h_ln
        / faster_lane_midpoint_speed_mph
    )
    slower_lane_density = (
        slower_lane_midpoint_percent_followers
        / 100.0
        * slower_lane_flow_rate_veh_h_ln
        / slower_lane_midpoint_speed_mph
    )
    return (faster_lane_density + slower_lane_density) / 2.0


def downstream_follower_density_adjustment(
    percent_followers_value: float,
    demand_flow_rate_veh_h: float,
    average_speed_mph: float,
    downstream_distance_mi: float,
    upstream_percent_followers: float,
    passing_lane_length_mi: float,
) -> dict[str, float]:
    """HCM Eq. 15-36 through Eq. 15-38 downstream passing-lane adjustment."""

    pf_improvement = downstream_percent_followers_improvement(
        downstream_distance_mi,
        upstream_percent_followers,
        passing_lane_length_mi,
        demand_flow_rate_veh_h,
    )
    speed_improvement = downstream_speed_improvement(
        downstream_distance_mi,
        upstream_percent_followers,
        passing_lane_length_mi,
        demand_flow_rate_veh_h,
    )
    adjusted_density = (
        percent_followers_value
        / 100.0
        * (1.0 - pf_improvement / 100.0)
        * demand_flow_rate_veh_h
        / (average_speed_mph * (1.0 + speed_improvement / 100.0))
    )
    return {
        "percent_followers_improvement_percent": pf_improvement,
        "speed_improvement_percent": speed_improvement,
        "adjusted_follower_density_followers_mi_ln": adjusted_density,
    }


def downstream_percent_followers_improvement(
    downstream_distance_mi: float,
    upstream_percent_followers: float,
    passing_lane_length_mi: float,
    demand_flow_rate_veh_h: float,
) -> float:
    """HCM Eq. 15-36 percent-followers improvement downstream of a passing lane."""

    return max(
        0.0,
        27.0
        - 8.75 * log(max(0.1, downstream_distance_mi))
        + 0.1 * max(0.0, upstream_percent_followers - 30.0)
        + 3.5 * log(max(0.3, passing_lane_length_mi))
        - 0.01 * demand_flow_rate_veh_h,
    )


def downstream_speed_improvement(
    downstream_distance_mi: float,
    upstream_percent_followers: float,
    passing_lane_length_mi: float,
    demand_flow_rate_veh_h: float,
) -> float:
    """HCM Eq. 15-37 speed improvement downstream of a passing lane."""

    return max(
        0.0,
        3.0
        - 0.8 * downstream_distance_mi
        + 0.1 * max(0.0, upstream_percent_followers - 30.0)
        + 0.75 * passing_lane_length_mi
        - 0.005 * demand_flow_rate_veh_h,
    )


def passing_lane_effective_length(
    upstream_follower_density_followers_mi_ln: float,
    upstream_percent_followers: float,
    upstream_demand_flow_rate_veh_h: float,
    upstream_average_speed_mph: float,
    passing_lane_length_mi: float,
) -> dict[str, float]:
    """Determine the Example Problem 3 downstream passing-lane effective length."""

    zero_distance = _solve_monotonic_distance(
        lambda distance: downstream_percent_followers_improvement(
            distance,
            upstream_percent_followers,
            passing_lane_length_mi,
            upstream_demand_flow_rate_veh_h,
        ),
        target=0.0,
    )
    target_density = 0.95 * upstream_follower_density_followers_mi_ln
    density_distance = _solve_increasing_distance(
        lambda distance: downstream_follower_density_adjustment(
            percent_followers_value=upstream_percent_followers,
            demand_flow_rate_veh_h=upstream_demand_flow_rate_veh_h,
            average_speed_mph=upstream_average_speed_mph,
            downstream_distance_mi=distance,
            upstream_percent_followers=upstream_percent_followers,
            passing_lane_length_mi=passing_lane_length_mi,
        )["adjusted_follower_density_followers_mi_ln"],
        target=target_density,
    )
    return {
        "percent_followers_zero_mi": zero_distance,
        "density_95_percent_mi": density_distance,
        "effective_length_mi": min(zero_distance, density_distance),
    }


def _solve_monotonic_distance(
    function,
    target: float,
    lower: float = 0.1,
    upper: float = 30.0,
) -> float:
    low = lower
    high = upper
    for _ in range(80):
        midpoint = (low + high) / 2.0
        value = function(midpoint)
        if value > target:
            low = midpoint
        else:
            high = midpoint
    return (low + high) / 2.0


def _solve_increasing_distance(
    function,
    target: float,
    lower: float = 0.1,
    upper: float = 30.0,
) -> float:
    low = lower
    high = upper
    for _ in range(80):
        midpoint = (low + high) / 2.0
        value = function(midpoint)
        if value < target:
            low = midpoint
        else:
            high = midpoint
    return (low + high) / 2.0


def _passing_lane_lane_average_speed(
    vertical_class: int,
    free_flow_speed_mph: float,
    lane_flow_rate_veh_h_ln: float,
    segment_length_mi: float,
    lane_heavy_vehicle_percent: float,
) -> float:
    speed_m = passing_lane_average_speed_slope_coefficient(
        vertical_class,
        free_flow_speed_mph,
        0.0,
        segment_length_mi,
        lane_heavy_vehicle_percent,
    )
    speed_p = passing_lane_average_speed_power_coefficient(
        vertical_class,
        free_flow_speed_mph,
        0.0,
        segment_length_mi,
        lane_heavy_vehicle_percent,
    )
    return average_speed(free_flow_speed_mph, lane_flow_rate_veh_h_ln, speed_m, speed_p)


def _passing_lane_lane_percent_followers(
    vertical_class: int,
    segment_length_mi: float,
    free_flow_speed_mph: float,
    lane_heavy_vehicle_percent: float,
    lane_flow_rate_veh_h_ln: float,
    capacity_veh_h: float,
) -> float:
    pf_cap = passing_lane_percent_followers_at_capacity(
        vertical_class,
        segment_length_mi,
        free_flow_speed_mph,
        lane_heavy_vehicle_percent,
    )
    pf_25_cap = passing_lane_percent_followers_at_25_percent_capacity(
        vertical_class,
        segment_length_mi,
        free_flow_speed_mph,
        lane_heavy_vehicle_percent,
    )
    pf_m = percent_followers_slope_coefficient(PASSING_LANE, pf_cap, pf_25_cap, capacity_veh_h)
    pf_p = percent_followers_power_coefficient(PASSING_LANE, pf_cap, pf_25_cap, capacity_veh_h)
    return percent_followers(lane_flow_rate_veh_h_ln, pf_m, pf_p)


def _passing_lane_lane_capacity(
    vertical_class: int,
    lane_heavy_vehicle_percent: float,
) -> float:
    """HCM Exhibit 15-5 capacity reapplied to a Passing Lane lane."""

    if vertical_class != 1:
        raise MethodNotImplementedError(
            "Passing Lane lane-level capacity is implemented only for vertical class 1."
        )
    if lane_heavy_vehicle_percent < 10.0:
        return 1500.0
    if lane_heavy_vehicle_percent < 15.0:
        return 1400.0
    if lane_heavy_vehicle_percent < 25.0:
        return 1300.0
    return 1100.0


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
        thresholds = (2.5, 5.0, 10.0, 15.0)
    else:
        thresholds = (2.0, 4.0, 8.0, 12.0)

    if follower_density_followers_mi_ln <= thresholds[0]:
        return "A"
    if follower_density_followers_mi_ln <= thresholds[1]:
        return "B"
    if follower_density_followers_mi_ln <= thresholds[2]:
        return "C"
    if follower_density_followers_mi_ln <= thresholds[3]:
        return "D"
    return "E"
