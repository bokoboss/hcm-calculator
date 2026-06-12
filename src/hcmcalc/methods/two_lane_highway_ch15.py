"""HCM 7th Edition Chapter 15 Two-Lane Highway method.

The implemented calculation paths are scoped to Chapter 26 Example Problems 1
through 4 and are intentionally kept independent from any UI.
"""

from dataclasses import dataclass
from math import exp, isfinite, log, sqrt
from numbers import Real
from typing import Any

from hcmcalc.core import (
    CalculationResult,
    HCMCalcError,
    IntermediateValue,
    MethodNotImplementedError,
)
from hcmcalc.methods.two_lane_highway_coefficients import (
    HEAVY_VEHICLE_COEFFICIENTS,
    HEAVY_VEHICLE_SPEED_COEFFICIENTS,
    HORIZONTAL_CURVE_BFFS_SLOPE,
    HORIZONTAL_CURVE_CLASS_SPEED_INTERCEPT,
    HORIZONTAL_CURVE_CLASS_SPEED_SLOPE,
    HORIZONTAL_CURVE_HEAVY_VEHICLE_COEFFICIENT,
    HORIZONTAL_CURVE_SPEED_COEFFICIENTS,
    PASSING_LANE_PF_25_CAPACITY_COEFFICIENTS,
    PASSING_LANE_PF_CAPACITY_COEFFICIENTS,
    PASSING_LANE_SPEED_POWER_COEFFICIENTS,
    PASSING_LANE_HEAVY_VEHICLE_SPEED_COEFFICIENTS,
    PASSING_LANE_SEGMENT_LENGTH_SPEED_COEFFICIENTS,
    PASSING_LANE_SPEED_SLOPE_BASE_COEFFICIENTS,
    PF_25_CAPACITY_COEFFICIENTS,
    PF_CAPACITY_COEFFICIENTS,
    PF_POWER_COEFFICIENTS,
    PF_SLOPE_COEFFICIENTS,
    PercentFollowersCapacityCoefficients,
    SPEED_POWER_COEFFICIENTS,
    SEGMENT_LENGTH_SPEED_COEFFICIENTS,
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
from hcmcalc.methods.vertical_lookup import find_vertical_class_record


@dataclass(frozen=True)
class FreeFlowSpeedEstimate:
    """Auditable HCM Chapter 15 Step 4 free-flow speed estimate."""

    base_free_flow_speed_mph: float
    heavy_vehicle_speed_adjustment_coefficient: float
    lane_shoulder_adjustment_mph: float
    access_point_adjustment_mph: float
    free_flow_speed_mph: float
    source_references: tuple[str, ...] = (
        "HCM Eq. 15-2",
        "HCM Eq. 15-3",
        "HCM Eq. 15-4",
        "HCM Exhibit 15-12",
        "HCM Eq. 15-5",
        "HCM Eq. 15-6",
    )


@dataclass(frozen=True)
class AverageSpeedEstimate:
    """Auditable HCM Chapter 15 Step 5 tangent average-speed estimate."""

    average_speed_mph: float
    speed_slope_coefficient_m: float
    speed_power_coefficient_p: float
    segment_length_coefficient_b3: float
    heavy_vehicle_speed_coefficient_b4: float
    source_references: tuple[str, ...]


@dataclass(frozen=True)
class PercentFollowersEstimate:
    """Auditable HCM Chapter 15 Step 6 percent-followers estimate."""

    percent_followers: float
    percent_followers_at_capacity: float
    percent_followers_at_25_capacity: float
    percent_followers_slope_coefficient_m: float
    percent_followers_power_coefficient_p: float
    source_references: tuple[str, ...]


@dataclass(frozen=True)
class FollowerDensityEstimate:
    """Auditable HCM Chapter 15 Step 8 follower-density estimate."""

    follower_density: float
    source_reference: str
    formula: str
    faster_lane_component: float | None = None
    slower_lane_component: float | None = None
    faster_lane_flow_rate: float | None = None
    slower_lane_flow_rate: float | None = None
    faster_lane_midpoint_speed: float | None = None
    slower_lane_midpoint_speed: float | None = None
    faster_lane_percent_followers: float | None = None
    slower_lane_percent_followers: float | None = None


@dataclass(frozen=True)
class MotorizedLOSDetermination:
    """Auditable HCM Chapter 15 Step 10 motorized-vehicle LOS result."""

    level_of_service: str
    los_threshold_group: str
    los_thresholds_used: dict[str, float | None]
    follower_density_for_los: float
    posted_speed_limit_for_los: float
    source_reference: str = "HCM7 Exhibit 15-6"


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
        if segment.grade_percent != 0.0:
            lookup = find_vertical_class_record(
                terrain_type=segment.terrain_type or "mountainous",
                segment_type=segment.segment_type,
                grade_percent=segment.grade_percent,
                grade_length_mi=segment.grade_length_mi or segment.segment_length_mi,
                heavy_vehicle_percent=segment.heavy_vehicle_percent,
            )
            assert lookup.record is not None
            assumptions.append(
                "Validated vertical scope is limited to the exact "
                f"{lookup.record.source} segment path; {lookup.record.validation_basis}."
            )
            warnings.append(
                "No general mountainous, vertical-class, or grade-length support is claimed."
            )
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
    step4 = estimate_free_flow_speed(
        posted_speed_mph=parsed_inputs.posted_speed_mph,
        vertical_class=vertical_class,
        segment_length_mi=parsed_inputs.segment_length_mi,
        opposing_flow_veh_h=OPPOSING_FLOW_EXAMPLE_1_VEH_H,
        heavy_vehicle_percent=parsed_inputs.heavy_vehicle_percent,
        lane_width_ft=parsed_inputs.lane_width_ft,
        shoulder_width_ft=parsed_inputs.shoulder_width_ft,
        access_point_density_per_mi=parsed_inputs.access_point_density_per_mi,
    )
    bffs = step4.base_free_flow_speed_mph
    f_ls = step4.lane_shoulder_adjustment_mph
    f_a = step4.access_point_adjustment_mph
    hv_coefficient = step4.heavy_vehicle_speed_adjustment_coefficient
    ffs = step4.free_flow_speed_mph
    step5 = estimate_average_speed(
        segment_type=parsed_inputs.segment_type,
        vertical_class=vertical_class,
        segment_length_mi=parsed_inputs.segment_length_mi,
        free_flow_speed_mph=ffs,
        heavy_vehicle_percent=parsed_inputs.heavy_vehicle_percent,
        demand_flow_rate_veh_h=demand,
        opposing_flow_veh_h=OPPOSING_FLOW_EXAMPLE_1_VEH_H,
    )
    speed_m = step5.speed_slope_coefficient_m
    speed_p = step5.speed_power_coefficient_p
    speed = step5.average_speed_mph
    step6 = estimate_percent_followers(
        segment_type=parsed_inputs.segment_type,
        vertical_class=vertical_class,
        segment_length_mi=parsed_inputs.segment_length_mi,
        free_flow_speed_mph=ffs,
        heavy_vehicle_percent=parsed_inputs.heavy_vehicle_percent,
        demand_flow_rate_veh_h=demand,
        opposing_flow_veh_h=OPPOSING_FLOW_EXAMPLE_1_VEH_H,
        capacity_veh_h=capacity,
    )
    pf_cap = step6.percent_followers_at_capacity
    pf_25_cap = step6.percent_followers_at_25_capacity
    pf_m = step6.percent_followers_slope_coefficient_m
    pf_p = step6.percent_followers_power_coefficient_p
    followers = step6.percent_followers
    step8 = estimate_follower_density(
        segment_type=parsed_inputs.segment_type,
        percent_followers=followers,
        demand_flow_rate_veh_h=demand,
        average_speed_mph=speed,
    )
    density = step8.follower_density
    step10 = determine_motorized_los(density, parsed_inputs.posted_speed_mph)

    return {
        "demand_flow_rate_veh_h": demand,
        "capacity_veh_h": capacity,
        "demand_capacity_ratio": demand_capacity_ratio,
        "vertical_class": vertical_class,
        "base_free_flow_speed_mph": bffs,
        "lane_shoulder_adjustment_mph": f_ls,
        "access_point_adjustment_mph": f_a,
        "heavy_vehicle_ffs_coefficient": hv_coefficient,
        "heavy_vehicle_speed_adjustment_coefficient": hv_coefficient,
        "free_flow_speed_mph": ffs,
        "average_speed_slope_coefficient": speed_m,
        "average_speed_power_coefficient": speed_p,
        "segment_length_coefficient_b3": step5.segment_length_coefficient_b3,
        "heavy_vehicle_speed_coefficient_b4": step5.heavy_vehicle_speed_coefficient_b4,
        "average_speed_source_reference": "; ".join(step5.source_references),
        "average_speed_mph": speed,
        "percent_followers_at_capacity": pf_cap,
        "percent_followers_at_25_percent_capacity": pf_25_cap,
        "percent_followers_slope_coefficient": pf_m,
        "percent_followers_power_coefficient": pf_p,
        "percent_followers_slope_coefficient_m": pf_m,
        "percent_followers_power_coefficient_p": pf_p,
        "percent_followers_source_reference": "; ".join(step6.source_references),
        "percent_followers": followers,
        "follower_density_followers_mi_ln": density,
        "follower_density_source_reference": step8.source_reference,
        "follower_density_formula": step8.formula,
        **_step10_output_fields(step10),
    }


def _calculate_example_problem_1_result(
    parsed_inputs: TwoLaneExampleProblem1Inputs,
    base: dict[str, Any],
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
                "heavy_vehicle_speed_adjustment_coefficient": base[
                    "heavy_vehicle_speed_adjustment_coefficient"
                ],
                "free_flow_speed_mph": base["free_flow_speed_mph"],
                "average_speed_slope_coefficient": base[
                    "average_speed_slope_coefficient"
                ],
                "average_speed_power_coefficient": base[
                    "average_speed_power_coefficient"
                ],
                "segment_length_coefficient_b3": base["segment_length_coefficient_b3"],
                "heavy_vehicle_speed_coefficient_b4": base[
                    "heavy_vehicle_speed_coefficient_b4"
                ],
                "average_speed_source_reference": base[
                    "average_speed_source_reference"
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
                "follower_density_source_reference": base[
                    "follower_density_source_reference"
                ],
                "follower_density_formula": base["follower_density_formula"],
                "level_of_service": base["level_of_service"],
                "los_source_reference": base["los_source_reference"],
                "los_threshold_group": base["los_threshold_group"],
                "los_thresholds_used": base["los_thresholds_used"],
                "follower_density_for_los": base["follower_density_for_los"],
                "posted_speed_limit_for_los": base["posted_speed_limit_for_los"],
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
                    "heavy_vehicle_speed_adjustment_coefficient",
                    base["heavy_vehicle_speed_adjustment_coefficient"],
                    source="HCM Eq. 15-4 and Exhibit 15-12",
                ),
                IntermediateValue(
                    "free_flow_speed",
                    base["free_flow_speed_mph"],
                    "mph",
                    "HCM Eq. 15-3",
                ),
                IntermediateValue(
                    "segment_length_coefficient_b3",
                    base["segment_length_coefficient_b3"],
                    source="HCM Eq. 15-9 and Exhibit 15-15",
                ),
                IntermediateValue(
                    "heavy_vehicle_speed_coefficient_b4",
                    base["heavy_vehicle_speed_coefficient_b4"],
                    source="HCM Eq. 15-10 and Exhibit 15-17",
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
                IntermediateValue(
                    "follower_density_source_reference",
                    base["follower_density_source_reference"],
                    source="HCM Chapter 15 Step 8",
                ),
                IntermediateValue(
                    "follower_density_formula",
                    base["follower_density_formula"],
                    source="HCM Chapter 15 Step 8",
                ),
                *_step10_intermediate_values(base),
            ],
            assumptions=[
                "Validated only for HCM Chapter 26 Two-Lane Highway Example Problem 1.",
                "Applies to a level, straight Passing Constrained segment.",
                "Example Problem 1 opposing flow is 1,500 veh/h.",
            ],
        )


def _calculate_example_problem_2_result(
    parsed_inputs: TwoLaneExampleProblem2Inputs,
    base: dict[str, Any],
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
            result["unadjusted_follower_density_source_reference"] = result[
                "follower_density_source_reference"
            ]
            result["unadjusted_follower_density_formula"] = result[
                "follower_density_formula"
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
            result["follower_density_source_reference"] = "HCM Eq. 15-38"
            result["follower_density_formula"] = (
                "FDadj = (PF / 100) * (1 - percent_improvement_PF / 100) * "
                "demand_flow_rate / (average_speed * "
                "(1 + percent_improvement_speed / 100))"
            )
            _apply_step10_output_fields(
                result,
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
    step4 = estimate_free_flow_speed(
        posted_speed_mph=segment.posted_speed_mph,
        vertical_class=vertical_class,
        segment_length_mi=segment.segment_length_mi,
        opposing_flow_veh_h=opposing_flow,
        heavy_vehicle_percent=segment.heavy_vehicle_percent,
        lane_width_ft=segment.lane_width_ft,
        shoulder_width_ft=segment.shoulder_width_ft,
        access_point_density_per_mi=segment.access_point_density_per_mi,
    )
    bffs = step4.base_free_flow_speed_mph
    f_ls = step4.lane_shoulder_adjustment_mph
    f_a = step4.access_point_adjustment_mph
    hv_coefficient = step4.heavy_vehicle_speed_adjustment_coefficient
    ffs = step4.free_flow_speed_mph

    step5 = estimate_average_speed(
        segment_type=segment.segment_type,
        vertical_class=vertical_class,
        segment_length_mi=segment.segment_length_mi,
        free_flow_speed_mph=ffs,
        heavy_vehicle_percent=segment.heavy_vehicle_percent,
        demand_flow_rate_veh_h=demand,
        opposing_flow_veh_h=opposing_flow,
    )
    speed_m = step5.speed_slope_coefficient_m
    speed_p = step5.speed_power_coefficient_p

    speed = step5.average_speed_mph
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
    step6 = estimate_percent_followers(
        segment_type=segment.segment_type,
        vertical_class=vertical_class,
        segment_length_mi=segment.segment_length_mi,
        free_flow_speed_mph=ffs,
        heavy_vehicle_percent=segment.heavy_vehicle_percent,
        demand_flow_rate_veh_h=demand,
        opposing_flow_veh_h=opposing_flow,
        capacity_veh_h=capacity,
    )
    pf_cap = step6.percent_followers_at_capacity
    pf_25_cap = step6.percent_followers_at_25_capacity
    pf_m = step6.percent_followers_slope_coefficient_m
    pf_p = step6.percent_followers_power_coefficient_p
    followers = step6.percent_followers
    density = follower_density(demand, speed, followers)
    step10 = determine_motorized_los(density, segment.posted_speed_mph)

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
        "heavy_vehicle_speed_adjustment_coefficient": hv_coefficient,
        "free_flow_speed_mph": ffs,
        "average_speed_slope_coefficient": speed_m,
        "average_speed_power_coefficient": speed_p,
        "segment_length_coefficient_b3": step5.segment_length_coefficient_b3,
        "heavy_vehicle_speed_coefficient_b4": step5.heavy_vehicle_speed_coefficient_b4,
        "average_speed_source_reference": "; ".join(step5.source_references),
        "average_speed_mph": speed,
        "horizontal_curve_subsegments": horizontal_results,
        "percent_followers_at_capacity": pf_cap,
        "percent_followers_at_25_percent_capacity": pf_25_cap,
        "percent_followers_slope_coefficient": pf_m,
        "percent_followers_power_coefficient": pf_p,
        "percent_followers_slope_coefficient_m": pf_m,
        "percent_followers_power_coefficient_p": pf_p,
        "percent_followers_source_reference": "; ".join(step6.source_references),
        "percent_followers": followers,
        "follower_density_followers_mi_ln": density,
        "follower_density_source_reference": "HCM Eq. 15-35",
        "follower_density_formula": "FD = (PF / 100) * demand_flow_rate / average_speed",
        **_step10_output_fields(step10),
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
        _apply_step10_output_fields(
            result,
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
        (
            "heavy_vehicle_speed_adjustment_coefficient",
            "heavy_vehicle_speed_adjustment_coefficient",
            None,
            "HCM Eq. 15-4 and Exhibit 15-12",
        ),
        (
            "lane_shoulder_adjustment",
            "lane_shoulder_adjustment_mph",
            "mph",
            "HCM Eq. 15-5",
        ),
        (
            "access_point_adjustment",
            "access_point_adjustment_mph",
            "mph",
            "HCM Eq. 15-6",
        ),
        ("free_flow_speed", "free_flow_speed_mph", "mph", "HCM Eq. 15-3"),
        (
            "segment_length_coefficient_b3",
            "segment_length_coefficient_b3",
            None,
            "HCM Eq. 15-9 and Exhibit 15-15 or Exhibit 15-16",
        ),
        (
            "heavy_vehicle_speed_coefficient_b4",
            "heavy_vehicle_speed_coefficient_b4",
            None,
            "HCM Eq. 15-10 and Exhibit 15-17 or Exhibit 15-18",
        ),
        (
            "average_speed_slope_coefficient",
            "average_speed_slope_coefficient",
            None,
            "HCM Eq. 15-8 and Exhibit 15-13 or Exhibit 15-14",
        ),
        (
            "average_speed_power_coefficient",
            "average_speed_power_coefficient",
            None,
            "HCM Eq. 15-11 and Exhibit 15-19 or Exhibit 15-20",
        ),
        (
            "average_speed_source_reference",
            "average_speed_source_reference",
            None,
            "HCM Eq. 15-7 through Eq. 15-11 and Exhibits 15-13 through 15-20",
        ),
        ("average_speed", "average_speed_mph", "mph", "HCM Eq. 15-7"),
        (
            "percent_followers_at_capacity",
            "percent_followers_at_capacity",
            "%",
            "HCM Eq. 15-18 or Eq. 15-19",
        ),
        (
            "percent_followers_at_25_capacity",
            "percent_followers_at_25_percent_capacity",
            "%",
            "HCM Eq. 15-20 or Eq. 15-21",
        ),
        (
            "percent_followers_slope_coefficient_m",
            "percent_followers_slope_coefficient_m",
            None,
            "HCM Eq. 15-22 and Exhibit 15-28",
        ),
        (
            "percent_followers_power_coefficient_p",
            "percent_followers_power_coefficient_p",
            None,
            "HCM Eq. 15-23 and Exhibit 15-29",
        ),
        (
            "percent_followers_source_reference",
            "percent_followers_source_reference",
            None,
            "HCM Eq. 15-17 through Eq. 15-23 and Exhibits 15-24 through 15-29",
        ),
        ("percent_followers", "percent_followers", "%", "HCM Eq. 15-17"),
        (
            "follower_density",
            "follower_density_followers_mi_ln",
            "followers/mi/ln",
            "HCM Eq. 15-35 or Eq. 15-34 for Passing Lane midpoint",
        ),
        (
            "follower_density_source_reference",
            "follower_density_source_reference",
            None,
            "HCM Chapter 15 Step 8",
        ),
        (
            "follower_density_formula",
            "follower_density_formula",
            None,
            "HCM Chapter 15 Step 8",
        ),
    ]
    values = [
        IntermediateValue(name, outputs[key], units, source)
        for name, key, units, source in specs
    ]
    values.extend(_step10_intermediate_values(outputs))
    if outputs["segment_type"] == PASSING_LANE:
        values.extend(
            [
                IntermediateValue(
                    "faster_lane_component",
                    outputs["faster_lane_component"],
                    "followers/mi/ln",
                    "HCM Eq. 15-34",
                ),
                IntermediateValue(
                    "slower_lane_component",
                    outputs["slower_lane_component"],
                    "followers/mi/ln",
                    "HCM Eq. 15-34",
                ),
            ]
        )
    return values


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
                    f"segment_{segment_id}_base_free_flow_speed",
                    segment["base_free_flow_speed_mph"],
                    "mph",
                    "HCM Eq. 15-2",
                ),
                IntermediateValue(
                    f"segment_{segment_id}_heavy_vehicle_speed_adjustment_coefficient",
                    segment["heavy_vehicle_speed_adjustment_coefficient"],
                    source="HCM Eq. 15-4 and Exhibit 15-12",
                ),
                IntermediateValue(
                    f"segment_{segment_id}_lane_shoulder_adjustment",
                    segment["lane_shoulder_adjustment_mph"],
                    "mph",
                    "HCM Eq. 15-5",
                ),
                IntermediateValue(
                    f"segment_{segment_id}_access_point_adjustment",
                    segment["access_point_adjustment_mph"],
                    "mph",
                    "HCM Eq. 15-6",
                ),
                IntermediateValue(
                    f"segment_{segment_id}_free_flow_speed",
                    segment["free_flow_speed_mph"],
                    "mph",
                    "HCM Eq. 15-3",
                ),
                IntermediateValue(
                    f"segment_{segment_id}_segment_length_coefficient_b3",
                    segment["segment_length_coefficient_b3"],
                    source="HCM Eq. 15-9 and Exhibit 15-15 or Exhibit 15-16",
                ),
                IntermediateValue(
                    f"segment_{segment_id}_heavy_vehicle_speed_coefficient_b4",
                    segment["heavy_vehicle_speed_coefficient_b4"],
                    source="HCM Eq. 15-10 and Exhibit 15-17 or Exhibit 15-18",
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
                    f"segment_{segment_id}_percent_followers_slope_coefficient_m",
                    segment["percent_followers_slope_coefficient_m"],
                    source="HCM Eq. 15-22 and Exhibit 15-28",
                ),
                IntermediateValue(
                    f"segment_{segment_id}_percent_followers_power_coefficient_p",
                    segment["percent_followers_power_coefficient_p"],
                    source="HCM Eq. 15-23 and Exhibit 15-29",
                ),
                IntermediateValue(
                    f"segment_{segment_id}_percent_followers_source_reference",
                    segment["percent_followers_source_reference"],
                    source=(
                        "HCM Eq. 15-17 through Eq. 15-23 and "
                        "Exhibits 15-24 through 15-29"
                    ),
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
                    segment["follower_density_source_reference"],
                ),
                IntermediateValue(
                    f"segment_{segment_id}_follower_density_source_reference",
                    segment["follower_density_source_reference"],
                    source="HCM Chapter 15 Step 8",
                ),
                IntermediateValue(
                    f"segment_{segment_id}_follower_density_formula",
                    segment["follower_density_formula"],
                    source="HCM Chapter 15 Step 8",
                ),
                *_step10_intermediate_values(segment, prefix=f"segment_{segment_id}_"),
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
                        f"segment_{segment_id}_faster_lane_component",
                        segment["faster_lane_component"],
                        "followers/mi/ln",
                        "HCM Eq. 15-34",
                    ),
                    IntermediateValue(
                        f"segment_{segment_id}_slower_lane_component",
                        segment["slower_lane_component"],
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
            segment.segment_length_mi
            if segment.grade_percent == 0.0
            else segment.grade_length_mi
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
        validated_facility_example=True,
    )
    assert decision.vertical_class is not None
    return decision.vertical_class


def base_free_flow_speed(posted_speed_mph: float | None) -> float:
    """HCM Eq. 15-2 BFFS estimate."""

    if posted_speed_mph is None:
        raise HCMCalcError("Posted/base speed is required for HCM Step 4.")
    if not isfinite(posted_speed_mph) or posted_speed_mph <= 0.0:
        raise HCMCalcError("Posted/base speed must be a positive finite value.")
    return 1.14 * posted_speed_mph


def lane_shoulder_adjustment(
    lane_width_ft: float | None,
    shoulder_width_ft: float | None,
) -> float:
    """HCM Eq. 15-5 lane and shoulder width adjustment."""

    if lane_width_ft is None or not isfinite(lane_width_ft):
        raise HCMCalcError("lane_width_ft must be a finite numeric value.")
    if shoulder_width_ft is None or not isfinite(shoulder_width_ft):
        raise HCMCalcError("shoulder_width_ft must be a finite numeric value.")
    if not 9.0 <= lane_width_ft <= 12.0:
        raise HCMCalcError("lane_width_ft must be within the HCM range of 9 to 12 ft.")
    if not 0.0 <= shoulder_width_ft <= 6.0:
        raise HCMCalcError(
            "shoulder_width_ft must be within the HCM range of 0 to 6 ft."
        )
    return 0.6 * (12.0 - lane_width_ft) + 0.7 * (6.0 - shoulder_width_ft)


def access_point_adjustment(access_point_density_per_mi: float | None) -> float:
    """HCM Eq. 15-6 access point density adjustment."""

    if access_point_density_per_mi is None or not isfinite(access_point_density_per_mi):
        raise HCMCalcError(
            "access_point_density_per_mi must be a finite numeric value."
        )
    if access_point_density_per_mi < 0:
        raise HCMCalcError("access_point_density_per_mi must not be negative.")
    return min(access_point_density_per_mi / 4.0, 10.0)


def heavy_vehicle_ffs_coefficient(
    vertical_class: int | None,
    base_free_flow_speed_mph: float | None,
    segment_length_mi: float | None,
    opposing_flow_veh_h: float | None,
) -> float:
    """HCM Eq. 15-4 coefficient for the HV% term in Eq. 15-3."""

    if vertical_class is None:
        raise HCMCalcError("Vertical class is required for HCM Step 4.")
    if vertical_class not in HEAVY_VEHICLE_COEFFICIENTS:
        raise HCMCalcError(
            f"Unsupported vertical class for HCM Step 4: {vertical_class}. "
            "Expected Class 1 through 5."
        )
    if (
        base_free_flow_speed_mph is None
        or not isfinite(base_free_flow_speed_mph)
        or base_free_flow_speed_mph <= 0.0
    ):
        raise HCMCalcError("Base free-flow speed must be a positive finite value.")
    if (
        segment_length_mi is None
        or not isfinite(segment_length_mi)
        or segment_length_mi <= 0.0
    ):
        raise HCMCalcError("Segment length must be a positive finite value.")
    if (
        opposing_flow_veh_h is None
        or not isfinite(opposing_flow_veh_h)
        or opposing_flow_veh_h < 0.0
    ):
        raise HCMCalcError("Opposing flow must be a nonnegative finite value.")
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


def estimate_free_flow_speed(
    *,
    posted_speed_mph: float | None,
    vertical_class: int | None,
    segment_length_mi: float | None,
    opposing_flow_veh_h: float | None,
    heavy_vehicle_percent: float | None,
    lane_width_ft: float | None,
    shoulder_width_ft: float | None,
    access_point_density_per_mi: float | None,
) -> FreeFlowSpeedEstimate:
    """Calculate and expose all HCM Chapter 15 Step 4 values."""

    if (
        heavy_vehicle_percent is None
        or not isfinite(heavy_vehicle_percent)
        or not 0.0 <= heavy_vehicle_percent <= 100.0
    ):
        raise HCMCalcError(
            "Heavy-vehicle percentage must be a finite value between 0 and 100."
        )

    bffs = base_free_flow_speed(posted_speed_mph)
    coefficient = heavy_vehicle_ffs_coefficient(
        vertical_class,
        bffs,
        segment_length_mi,
        opposing_flow_veh_h,
    )
    f_ls = lane_shoulder_adjustment(lane_width_ft, shoulder_width_ft)
    f_a = access_point_adjustment(access_point_density_per_mi)
    ffs = estimated_free_flow_speed(
        bffs,
        coefficient,
        heavy_vehicle_percent,
        f_ls,
        f_a,
    )
    return FreeFlowSpeedEstimate(
        base_free_flow_speed_mph=bffs,
        heavy_vehicle_speed_adjustment_coefficient=coefficient,
        lane_shoulder_adjustment_mph=f_ls,
        access_point_adjustment_mph=f_a,
        free_flow_speed_mph=ffs,
    )


def average_speed_slope_coefficient(
    vertical_class: int,
    free_flow_speed_mph: float,
    opposing_flow_veh_h: float,
    segment_length_mi: float,
    heavy_vehicle_percent: float,
) -> float:
    """HCM Eq. 15-8 slope coefficient for Eq. 15-7."""

    return estimate_speed_slope_coefficient(
        PASSING_CONSTRAINED,
        vertical_class,
        free_flow_speed_mph,
        opposing_flow_veh_h,
        segment_length_mi,
        heavy_vehicle_percent,
    )


def estimate_segment_length_coefficient(
    segment_type: str,
    vertical_class: int,
    free_flow_speed_mph: float,
    segment_length_mi: float,
) -> float:
    """HCM Eq. 15-9 segment-length coefficient b3."""

    _validate_step5_common_inputs(
        segment_type=segment_type,
        vertical_class=vertical_class,
        free_flow_speed_mph=free_flow_speed_mph,
        segment_length_mi=segment_length_mi,
    )
    table = (
        PASSING_LANE_SEGMENT_LENGTH_SPEED_COEFFICIENTS
        if segment_type == PASSING_LANE
        else SEGMENT_LENGTH_SPEED_COEFFICIENTS
    )
    coefficients = table[vertical_class]
    root_length = sqrt(segment_length_mi)
    return (
        coefficients.c0
        + coefficients.c1 * root_length
        + coefficients.c2 * free_flow_speed_mph
        + coefficients.c3 * free_flow_speed_mph * root_length
    )


def estimate_heavy_vehicle_speed_coefficient(
    segment_type: str,
    vertical_class: int,
    free_flow_speed_mph: float,
    heavy_vehicle_percent: float,
) -> float:
    """HCM Eq. 15-10 heavy-vehicle percentage coefficient b4."""

    _validate_step5_common_inputs(
        segment_type=segment_type,
        vertical_class=vertical_class,
        free_flow_speed_mph=free_flow_speed_mph,
        heavy_vehicle_percent=heavy_vehicle_percent,
    )
    table = (
        PASSING_LANE_HEAVY_VEHICLE_SPEED_COEFFICIENTS
        if segment_type == PASSING_LANE
        else HEAVY_VEHICLE_SPEED_COEFFICIENTS
    )
    coefficients = table[vertical_class]
    root_heavy_vehicles = sqrt(heavy_vehicle_percent)
    return (
        coefficients.d0
        + coefficients.d1 * root_heavy_vehicles
        + coefficients.d2 * free_flow_speed_mph
        + coefficients.d3 * free_flow_speed_mph * root_heavy_vehicles
    )


def estimate_speed_slope_coefficient(
    segment_type: str,
    vertical_class: int,
    free_flow_speed_mph: float,
    opposing_flow_veh_h: float,
    segment_length_mi: float,
    heavy_vehicle_percent: float,
) -> float:
    """HCM Eq. 15-8 slope coefficient m."""

    _validate_step5_common_inputs(
        segment_type=segment_type,
        vertical_class=vertical_class,
        free_flow_speed_mph=free_flow_speed_mph,
        segment_length_mi=segment_length_mi,
        heavy_vehicle_percent=heavy_vehicle_percent,
        opposing_flow_veh_h=opposing_flow_veh_h,
    )
    coefficients = (
        PASSING_LANE_SPEED_SLOPE_BASE_COEFFICIENTS[vertical_class]
        if segment_type == PASSING_LANE
        else SPEED_SLOPE_COEFFICIENTS[vertical_class]
    )
    b3 = estimate_segment_length_coefficient(
        segment_type, vertical_class, free_flow_speed_mph, segment_length_mi
    )
    b4 = estimate_heavy_vehicle_speed_coefficient(
        segment_type, vertical_class, free_flow_speed_mph, heavy_vehicle_percent
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

    return estimate_speed_power_coefficient(
        PASSING_CONSTRAINED,
        vertical_class,
        free_flow_speed_mph,
        opposing_flow_veh_h,
        segment_length_mi,
        heavy_vehicle_percent,
    )


def estimate_speed_power_coefficient(
    segment_type: str,
    vertical_class: int,
    free_flow_speed_mph: float,
    opposing_flow_veh_h: float,
    segment_length_mi: float,
    heavy_vehicle_percent: float,
) -> float:
    """HCM Eq. 15-11 power coefficient p."""

    _validate_step5_common_inputs(
        segment_type=segment_type,
        vertical_class=vertical_class,
        free_flow_speed_mph=free_flow_speed_mph,
        segment_length_mi=segment_length_mi,
        heavy_vehicle_percent=heavy_vehicle_percent,
        opposing_flow_veh_h=opposing_flow_veh_h,
    )
    coefficients = (
        PASSING_LANE_SPEED_POWER_COEFFICIENTS[vertical_class]
        if segment_type == PASSING_LANE
        else SPEED_POWER_COEFFICIENTS[vertical_class]
    )
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


def estimate_average_speed(
    *,
    segment_type: str,
    vertical_class: int,
    segment_length_mi: float,
    free_flow_speed_mph: float,
    heavy_vehicle_percent: float,
    demand_flow_rate_veh_h: float,
    opposing_flow_veh_h: float,
) -> AverageSpeedEstimate:
    """Calculate and expose all HCM Chapter 15 Step 5 tangent-speed values."""

    required_values = (
        ("free-flow speed", free_flow_speed_mph),
        ("segment length", segment_length_mi),
        ("heavy-vehicle percentage", heavy_vehicle_percent),
        ("demand flow rate", demand_flow_rate_veh_h),
        ("opposing flow rate", opposing_flow_veh_h),
    )
    for label, value in required_values:
        if value is None:
            raise HCMCalcError(f"Step 5 {label} is required.")

    _validate_step5_common_inputs(
        segment_type=segment_type,
        vertical_class=vertical_class,
        free_flow_speed_mph=free_flow_speed_mph,
        segment_length_mi=segment_length_mi,
        heavy_vehicle_percent=heavy_vehicle_percent,
        demand_flow_rate_veh_h=demand_flow_rate_veh_h,
        opposing_flow_veh_h=opposing_flow_veh_h,
    )
    b3 = estimate_segment_length_coefficient(
        segment_type, vertical_class, free_flow_speed_mph, segment_length_mi
    )
    b4 = estimate_heavy_vehicle_speed_coefficient(
        segment_type, vertical_class, free_flow_speed_mph, heavy_vehicle_percent
    )
    slope = estimate_speed_slope_coefficient(
        segment_type,
        vertical_class,
        free_flow_speed_mph,
        opposing_flow_veh_h,
        segment_length_mi,
        heavy_vehicle_percent,
    )
    power = estimate_speed_power_coefficient(
        segment_type,
        vertical_class,
        free_flow_speed_mph,
        opposing_flow_veh_h,
        segment_length_mi,
        heavy_vehicle_percent,
    )
    speed = average_speed(free_flow_speed_mph, demand_flow_rate_veh_h, slope, power)
    exhibits = (
        (
            "HCM Exhibit 15-14",
            "HCM Exhibit 15-16",
            "HCM Exhibit 15-18",
            "HCM Exhibit 15-20",
        )
        if segment_type == PASSING_LANE
        else (
            "HCM Exhibit 15-13",
            "HCM Exhibit 15-15",
            "HCM Exhibit 15-17",
            "HCM Exhibit 15-19",
        )
    )
    return AverageSpeedEstimate(
        average_speed_mph=speed,
        speed_slope_coefficient_m=slope,
        speed_power_coefficient_p=power,
        segment_length_coefficient_b3=b3,
        heavy_vehicle_speed_coefficient_b4=b4,
        source_references=(
            "HCM Eq. 15-7",
            "HCM Eq. 15-8",
            "HCM Eq. 15-9",
            "HCM Eq. 15-10",
            "HCM Eq. 15-11",
            *exhibits,
        ),
    )


def _validate_step5_common_inputs(
    *,
    segment_type: str,
    vertical_class: int,
    free_flow_speed_mph: float,
    segment_length_mi: float | None = None,
    heavy_vehicle_percent: float | None = None,
    demand_flow_rate_veh_h: float | None = None,
    opposing_flow_veh_h: float | None = None,
) -> None:
    if segment_type not in {PASSING_CONSTRAINED, PASSING_ZONE, PASSING_LANE}:
        raise HCMCalcError(f"Unsupported Step 5 segment type: {segment_type!r}.")
    if vertical_class not in {1, 2, 3, 4, 5}:
        raise HCMCalcError("Step 5 vertical class must be an integer from 1 through 5.")
    if (
        free_flow_speed_mph is None
        or not isfinite(free_flow_speed_mph)
        or free_flow_speed_mph <= 0
    ):
        raise HCMCalcError(
            "Step 5 free-flow speed must be a finite value greater than zero."
        )
    if segment_length_mi is not None and (
        not isfinite(segment_length_mi) or segment_length_mi <= 0
    ):
        raise HCMCalcError(
            "Step 5 segment length must be a finite value greater than zero."
        )
    if heavy_vehicle_percent is not None and (
        not isfinite(heavy_vehicle_percent) or not 0 <= heavy_vehicle_percent <= 100
    ):
        raise HCMCalcError(
            "Step 5 heavy-vehicle percentage must be a finite value between 0 and 100."
        )
    if demand_flow_rate_veh_h is not None and (
        not isfinite(demand_flow_rate_veh_h) or demand_flow_rate_veh_h < 0
    ):
        raise HCMCalcError("Step 5 demand flow rate must be a finite nonnegative value.")
    if opposing_flow_veh_h is not None and (
        not isfinite(opposing_flow_veh_h) or opposing_flow_veh_h < 0
    ):
        raise HCMCalcError("Step 5 opposing flow rate must be a finite nonnegative value.")


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

    return estimate_speed_slope_coefficient(
        PASSING_LANE,
        vertical_class,
        free_flow_speed_mph,
        opposing_flow_veh_h,
        segment_length_mi,
        heavy_vehicle_percent,
    )


def passing_lane_average_speed_power_coefficient(
    vertical_class: int,
    free_flow_speed_mph: float,
    opposing_flow_veh_h: float,
    segment_length_mi: float,
    heavy_vehicle_percent: float,
) -> float:
    """HCM Eq. 15-11 with Passing Lane coefficients from Exhibit 15-20."""

    return estimate_speed_power_coefficient(
        PASSING_LANE,
        vertical_class,
        free_flow_speed_mph,
        opposing_flow_veh_h,
        segment_length_mi,
        heavy_vehicle_percent,
    )


def estimate_percent_followers(
    *,
    segment_type: str,
    vertical_class: int,
    segment_length_mi: float,
    free_flow_speed_mph: float,
    heavy_vehicle_percent: float,
    demand_flow_rate_veh_h: float,
    opposing_flow_veh_h: float,
    capacity_veh_h: float,
) -> PercentFollowersEstimate:
    """Calculate and expose all HCM Chapter 15 Step 6 values."""

    required_values = (
        ("segment length", segment_length_mi),
        ("free-flow speed", free_flow_speed_mph),
        ("heavy-vehicle percentage", heavy_vehicle_percent),
        ("demand flow rate", demand_flow_rate_veh_h),
        ("opposing flow rate", opposing_flow_veh_h),
        ("capacity", capacity_veh_h),
    )
    for label, value in required_values:
        if value is None:
            raise HCMCalcError(f"Step 6 {label} is required.")

    _validate_step6_common_inputs(
        segment_type=segment_type,
        vertical_class=vertical_class,
        segment_length_mi=segment_length_mi,
        free_flow_speed_mph=free_flow_speed_mph,
        heavy_vehicle_percent=heavy_vehicle_percent,
        demand_flow_rate_veh_h=demand_flow_rate_veh_h,
        opposing_flow_veh_h=opposing_flow_veh_h,
        capacity_veh_h=capacity_veh_h,
    )
    if segment_type == PASSING_LANE:
        pf_cap = passing_lane_percent_followers_at_capacity(
            vertical_class,
            segment_length_mi,
            free_flow_speed_mph,
            heavy_vehicle_percent,
        )
        pf_25_cap = passing_lane_percent_followers_at_25_percent_capacity(
            vertical_class,
            segment_length_mi,
            free_flow_speed_mph,
            heavy_vehicle_percent,
        )
        capacity_exhibits = ("HCM Exhibit 15-25", "HCM Exhibit 15-27")
    else:
        pf_cap = percent_followers_at_capacity(
            vertical_class,
            segment_length_mi,
            free_flow_speed_mph,
            heavy_vehicle_percent,
            opposing_flow_veh_h,
        )
        pf_25_cap = percent_followers_at_25_percent_capacity(
            vertical_class,
            segment_length_mi,
            free_flow_speed_mph,
            heavy_vehicle_percent,
            opposing_flow_veh_h,
        )
        capacity_exhibits = ("HCM Exhibit 15-24", "HCM Exhibit 15-26")

    pf_m = percent_followers_slope_coefficient(
        segment_type, pf_cap, pf_25_cap, capacity_veh_h
    )
    pf_p = percent_followers_power_coefficient(
        segment_type, pf_cap, pf_25_cap, capacity_veh_h
    )
    followers = percent_followers(demand_flow_rate_veh_h, pf_m, pf_p)
    return PercentFollowersEstimate(
        percent_followers=followers,
        percent_followers_at_capacity=pf_cap,
        percent_followers_at_25_capacity=pf_25_cap,
        percent_followers_slope_coefficient_m=pf_m,
        percent_followers_power_coefficient_p=pf_p,
        source_references=(
            "HCM Eq. 15-17",
            "HCM Eq. 15-18" if segment_type != PASSING_LANE else "HCM Eq. 15-19",
            "HCM Eq. 15-20" if segment_type != PASSING_LANE else "HCM Eq. 15-21",
            "HCM Eq. 15-22",
            "HCM Eq. 15-23",
            *capacity_exhibits,
            "HCM Exhibit 15-28",
            "HCM Exhibit 15-29",
        ),
    )


def passing_lane_percent_followers_at_capacity(
    vertical_class: int,
    segment_length_mi: float,
    free_flow_speed_mph: float,
    heavy_vehicle_percent: float,
) -> float:
    """HCM Eq. 15-19 PF at capacity for Passing Lane segments."""

    _require_step6_values(
        ("segment length", segment_length_mi),
        ("free-flow speed", free_flow_speed_mph),
        ("heavy-vehicle percentage", heavy_vehicle_percent),
    )
    _validate_step6_common_inputs(
        segment_type=PASSING_LANE,
        vertical_class=vertical_class,
        segment_length_mi=segment_length_mi,
        free_flow_speed_mph=free_flow_speed_mph,
        heavy_vehicle_percent=heavy_vehicle_percent,
    )
    coefficients = PASSING_LANE_PF_CAPACITY_COEFFICIENTS[vertical_class]
    return _validate_step6_capacity_percent(
        _passing_lane_percent_followers_capacity_value(
            coefficients,
            segment_length_mi,
            free_flow_speed_mph,
            heavy_vehicle_percent,
        ),
        "PFcap",
    )


def passing_lane_percent_followers_at_25_percent_capacity(
    vertical_class: int,
    segment_length_mi: float,
    free_flow_speed_mph: float,
    heavy_vehicle_percent: float,
) -> float:
    """HCM Eq. 15-21 PF at 25 percent capacity for Passing Lane segments."""

    _require_step6_values(
        ("segment length", segment_length_mi),
        ("free-flow speed", free_flow_speed_mph),
        ("heavy-vehicle percentage", heavy_vehicle_percent),
    )
    _validate_step6_common_inputs(
        segment_type=PASSING_LANE,
        vertical_class=vertical_class,
        segment_length_mi=segment_length_mi,
        free_flow_speed_mph=free_flow_speed_mph,
        heavy_vehicle_percent=heavy_vehicle_percent,
    )
    coefficients = PASSING_LANE_PF_25_CAPACITY_COEFFICIENTS[vertical_class]
    return _validate_step6_capacity_percent(
        _passing_lane_percent_followers_capacity_value(
            coefficients,
            segment_length_mi,
            free_flow_speed_mph,
            heavy_vehicle_percent,
        ),
        "PF25cap",
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
) -> dict[str, Any]:
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
    step8 = estimate_follower_density(
        segment_type=PASSING_LANE,
        faster_lane_percent_followers=faster_lane_pf,
        slower_lane_percent_followers=slower_lane_pf,
        faster_lane_flow_rate_veh_h_ln=faster_lane_flow,
        slower_lane_flow_rate_veh_h_ln=slower_lane_flow,
        faster_lane_midpoint_speed_mph=faster_lane_midpoint_speed,
        slower_lane_midpoint_speed_mph=slower_lane_midpoint_speed,
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
        "faster_lane_component": step8.faster_lane_component,
        "slower_lane_component": step8.slower_lane_component,
        "midpoint_follower_density_followers_mi_ln": step8.follower_density,
        "follower_density_source_reference": step8.source_reference,
        "follower_density_formula": step8.formula,
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

    return estimate_passing_lane_midpoint_follower_density(
        segment_type=PASSING_LANE,
        faster_lane_percent_followers=faster_lane_midpoint_percent_followers,
        slower_lane_percent_followers=slower_lane_midpoint_percent_followers,
        faster_lane_flow_rate_veh_h_ln=faster_lane_flow_rate_veh_h_ln,
        slower_lane_flow_rate_veh_h_ln=slower_lane_flow_rate_veh_h_ln,
        faster_lane_midpoint_speed_mph=faster_lane_midpoint_speed_mph,
        slower_lane_midpoint_speed_mph=slower_lane_midpoint_speed_mph,
    ).follower_density


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
    """HCM Eq. 15-18 PF at capacity for Passing Constrained/Zone segments."""

    _require_step6_values(
        ("segment length", segment_length_mi),
        ("free-flow speed", free_flow_speed_mph),
        ("heavy-vehicle percentage", heavy_vehicle_percent),
        ("opposing flow rate", opposing_flow_veh_h),
    )
    _validate_step6_common_inputs(
        segment_type=PASSING_CONSTRAINED,
        vertical_class=vertical_class,
        segment_length_mi=segment_length_mi,
        free_flow_speed_mph=free_flow_speed_mph,
        heavy_vehicle_percent=heavy_vehicle_percent,
        opposing_flow_veh_h=opposing_flow_veh_h,
    )
    coefficients = PF_CAPACITY_COEFFICIENTS[vertical_class]
    return _validate_step6_capacity_percent(
        _percent_followers_capacity_value(
            coefficients,
            segment_length_mi,
            free_flow_speed_mph,
            heavy_vehicle_percent,
            opposing_flow_veh_h,
        ),
        "PFcap",
    )


def percent_followers_at_25_percent_capacity(
    vertical_class: int,
    segment_length_mi: float,
    free_flow_speed_mph: float,
    heavy_vehicle_percent: float,
    opposing_flow_veh_h: float,
) -> float:
    """HCM Eq. 15-20 PF at 25 percent capacity for Passing Constrained/Zone."""

    _require_step6_values(
        ("segment length", segment_length_mi),
        ("free-flow speed", free_flow_speed_mph),
        ("heavy-vehicle percentage", heavy_vehicle_percent),
        ("opposing flow rate", opposing_flow_veh_h),
    )
    _validate_step6_common_inputs(
        segment_type=PASSING_CONSTRAINED,
        vertical_class=vertical_class,
        segment_length_mi=segment_length_mi,
        free_flow_speed_mph=free_flow_speed_mph,
        heavy_vehicle_percent=heavy_vehicle_percent,
        opposing_flow_veh_h=opposing_flow_veh_h,
    )
    coefficients = PF_25_CAPACITY_COEFFICIENTS[vertical_class]
    return _validate_step6_capacity_percent(
        _percent_followers_capacity_value(
            coefficients,
            segment_length_mi,
            free_flow_speed_mph,
            heavy_vehicle_percent,
            opposing_flow_veh_h,
        ),
        "PF25cap",
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

    _require_step6_values(
        ("PFcap", percent_followers_capacity),
        ("PF25cap", percent_followers_25_capacity),
        ("capacity", capacity_veh_h),
    )
    _validate_step6_curve_inputs(
        segment_type,
        percent_followers_capacity,
        percent_followers_25_capacity,
        capacity_veh_h,
    )
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

    _require_step6_values(
        ("PFcap", percent_followers_capacity),
        ("PF25cap", percent_followers_25_capacity),
        ("capacity", capacity_veh_h),
    )
    _validate_step6_curve_inputs(
        segment_type,
        percent_followers_capacity,
        percent_followers_25_capacity,
        capacity_veh_h,
    )
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


def _validate_step6_common_inputs(
    *,
    segment_type: str,
    vertical_class: int,
    segment_length_mi: float | None = None,
    free_flow_speed_mph: float | None = None,
    heavy_vehicle_percent: float | None = None,
    demand_flow_rate_veh_h: float | None = None,
    opposing_flow_veh_h: float | None = None,
    capacity_veh_h: float | None = None,
) -> None:
    if segment_type not in {PASSING_CONSTRAINED, PASSING_ZONE, PASSING_LANE}:
        raise HCMCalcError(f"Unsupported Step 6 segment type: {segment_type!r}.")
    if vertical_class not in {1, 2, 3, 4, 5}:
        raise HCMCalcError("Step 6 vertical class must be an integer from 1 through 5.")
    if segment_length_mi is not None and (
        not isfinite(segment_length_mi) or segment_length_mi <= 0
    ):
        raise HCMCalcError(
            "Step 6 segment length must be a finite value greater than zero."
        )
    if free_flow_speed_mph is not None and (
        not isfinite(free_flow_speed_mph) or free_flow_speed_mph <= 0
    ):
        raise HCMCalcError(
            "Step 6 free-flow speed must be a finite value greater than zero."
        )
    if heavy_vehicle_percent is not None and (
        not isfinite(heavy_vehicle_percent) or not 0 <= heavy_vehicle_percent <= 100
    ):
        raise HCMCalcError(
            "Step 6 heavy-vehicle percentage must be a finite value between 0 and 100."
        )
    if demand_flow_rate_veh_h is not None and (
        not isfinite(demand_flow_rate_veh_h) or demand_flow_rate_veh_h < 0
    ):
        raise HCMCalcError("Step 6 demand flow rate must be a finite nonnegative value.")
    if opposing_flow_veh_h is not None and (
        not isfinite(opposing_flow_veh_h) or opposing_flow_veh_h < 0
    ):
        raise HCMCalcError(
            "Step 6 opposing flow rate must be a finite nonnegative value."
        )
    if capacity_veh_h is not None and (
        not isfinite(capacity_veh_h) or capacity_veh_h <= 0
    ):
        raise HCMCalcError("Step 6 capacity must be a finite value greater than zero.")


def _require_step6_values(*values: tuple[str, object]) -> None:
    for label, value in values:
        if value is None:
            raise HCMCalcError(f"Step 6 {label} is required.")


def _validate_step6_capacity_percent(value: float, label: str) -> float:
    if not isfinite(value) or not 0.0 <= value < 100.0:
        raise HCMCalcError(
            f"Step 6 {label} must be finite and at least 0 but less than 100 "
            "for Eq. 15-22 and Eq. 15-23 logarithms."
        )
    return value


def _validate_step6_curve_inputs(
    segment_type: str,
    percent_followers_capacity: float,
    percent_followers_25_capacity: float,
    capacity_veh_h: float,
) -> None:
    _validate_step6_common_inputs(
        segment_type=segment_type,
        vertical_class=1,
        capacity_veh_h=capacity_veh_h,
    )
    _validate_step6_capacity_percent(percent_followers_capacity, "PFcap")
    _validate_step6_capacity_percent(percent_followers_25_capacity, "PF25cap")


def percent_followers(
    demand_flow_rate_veh_h: float,
    slope_coefficient: float,
    power_coefficient: float,
) -> float:
    """HCM Eq. 15-17 percent followers."""

    _require_step6_values(
        ("demand flow rate", demand_flow_rate_veh_h),
        ("slope coefficient m", slope_coefficient),
        ("power coefficient p", power_coefficient),
    )
    if not isfinite(demand_flow_rate_veh_h) or demand_flow_rate_veh_h < 0:
        raise HCMCalcError("Step 6 demand flow rate must be a finite nonnegative value.")
    if not isfinite(slope_coefficient) or slope_coefficient >= 0:
        raise HCMCalcError("Step 6 slope coefficient m must be finite and negative.")
    if not isfinite(power_coefficient) or power_coefficient <= 0:
        raise HCMCalcError("Step 6 power coefficient p must be finite and positive.")
    value = 100.0 * (
        1.0
        - exp(slope_coefficient * (demand_flow_rate_veh_h / 1000.0) ** power_coefficient)
    )
    if not isfinite(value) or not 0.0 <= value <= 100.0:
        raise HCMCalcError("Step 6 percent followers must be finite and between 0 and 100.")
    return value


def follower_density(
    demand_flow_rate_veh_h: float,
    average_speed_mph: float,
    percent_followers_value: float,
) -> float:
    """HCM Eq. 15-35 follower density."""

    return estimate_passing_constrained_or_zone_follower_density(
        segment_type=PASSING_CONSTRAINED,
        percent_followers=percent_followers_value,
        demand_flow_rate_veh_h=demand_flow_rate_veh_h,
        average_speed_mph=average_speed_mph,
    ).follower_density


def estimate_follower_density(
    *,
    segment_type: str,
    percent_followers: float | None = None,
    demand_flow_rate_veh_h: float | None = None,
    average_speed_mph: float | None = None,
    faster_lane_percent_followers: float | None = None,
    slower_lane_percent_followers: float | None = None,
    faster_lane_flow_rate_veh_h_ln: float | None = None,
    slower_lane_flow_rate_veh_h_ln: float | None = None,
    faster_lane_midpoint_speed_mph: float | None = None,
    slower_lane_midpoint_speed_mph: float | None = None,
) -> FollowerDensityEstimate:
    """Estimate Step 8 follower density using the segment-type equation."""

    if segment_type in {PASSING_CONSTRAINED, PASSING_ZONE}:
        return estimate_passing_constrained_or_zone_follower_density(
            segment_type=segment_type,
            percent_followers=percent_followers,
            demand_flow_rate_veh_h=demand_flow_rate_veh_h,
            average_speed_mph=average_speed_mph,
        )
    if segment_type == PASSING_LANE:
        return estimate_passing_lane_midpoint_follower_density(
            segment_type=segment_type,
            faster_lane_percent_followers=faster_lane_percent_followers,
            slower_lane_percent_followers=slower_lane_percent_followers,
            faster_lane_flow_rate_veh_h_ln=faster_lane_flow_rate_veh_h_ln,
            slower_lane_flow_rate_veh_h_ln=slower_lane_flow_rate_veh_h_ln,
            faster_lane_midpoint_speed_mph=faster_lane_midpoint_speed_mph,
            slower_lane_midpoint_speed_mph=slower_lane_midpoint_speed_mph,
        )
    raise HCMCalcError(f"Unsupported Step 8 segment type: {segment_type!r}.")


def estimate_passing_constrained_or_zone_follower_density(
    *,
    segment_type: str,
    percent_followers: float | None,
    demand_flow_rate_veh_h: float | None,
    average_speed_mph: float | None,
) -> FollowerDensityEstimate:
    """Estimate Passing Constrained or Passing Zone density with Eq. 15-35."""

    if segment_type not in {PASSING_CONSTRAINED, PASSING_ZONE}:
        raise HCMCalcError(
            "Step 8 Eq. 15-35 requires a Passing Constrained or Passing Zone "
            f"segment type, not {segment_type!r}."
        )
    percent_followers_value = _validate_step8_percent(
        percent_followers, "percent followers"
    )
    demand_flow_rate = _validate_step8_number(
        demand_flow_rate_veh_h,
        "demand flow rate",
        allow_zero=True,
    )
    average_speed = _validate_step8_number(
        average_speed_mph,
        "average speed",
        allow_zero=False,
    )
    density = percent_followers_value / 100.0 * demand_flow_rate / average_speed
    return FollowerDensityEstimate(
        follower_density=density,
        source_reference="HCM Eq. 15-35",
        formula="FD = (PF / 100) * demand_flow_rate / average_speed",
    )


def estimate_passing_lane_midpoint_follower_density(
    *,
    segment_type: str,
    faster_lane_percent_followers: float | None,
    slower_lane_percent_followers: float | None,
    faster_lane_flow_rate_veh_h_ln: float | None,
    slower_lane_flow_rate_veh_h_ln: float | None,
    faster_lane_midpoint_speed_mph: float | None,
    slower_lane_midpoint_speed_mph: float | None,
) -> FollowerDensityEstimate:
    """Estimate Passing Lane midpoint follower density with Eq. 15-34."""

    if segment_type != PASSING_LANE:
        raise HCMCalcError(
            "Step 8 Eq. 15-34 requires a Passing Lane segment type, "
            f"not {segment_type!r}."
        )
    faster_pf = _validate_step8_percent(
        faster_lane_percent_followers, "faster-lane midpoint percent followers"
    )
    slower_pf = _validate_step8_percent(
        slower_lane_percent_followers, "slower-lane midpoint percent followers"
    )
    faster_flow = _validate_step8_number(
        faster_lane_flow_rate_veh_h_ln,
        "faster-lane flow rate",
        allow_zero=False,
    )
    slower_flow = _validate_step8_number(
        slower_lane_flow_rate_veh_h_ln,
        "slower-lane flow rate",
        allow_zero=False,
    )
    faster_speed = _validate_step8_number(
        faster_lane_midpoint_speed_mph,
        "faster-lane midpoint speed",
        allow_zero=False,
    )
    slower_speed = _validate_step8_number(
        slower_lane_midpoint_speed_mph,
        "slower-lane midpoint speed",
        allow_zero=False,
    )
    faster_component = faster_pf / 100.0 * faster_flow / faster_speed
    slower_component = slower_pf / 100.0 * slower_flow / slower_speed
    return FollowerDensityEstimate(
        follower_density=(faster_component + slower_component) / 2.0,
        source_reference="HCM Eq. 15-34",
        formula=(
            "FDPLmid = ((PFPLmid_FL / 100 * FlowRateFL / SPLmid_FL) + "
            "(PFPLmid_SL / 100 * FlowRateSL / SPLmid_SL)) / 2"
        ),
        faster_lane_component=faster_component,
        slower_lane_component=slower_component,
        faster_lane_flow_rate=faster_flow,
        slower_lane_flow_rate=slower_flow,
        faster_lane_midpoint_speed=faster_speed,
        slower_lane_midpoint_speed=slower_speed,
        faster_lane_percent_followers=faster_pf,
        slower_lane_percent_followers=slower_pf,
    )


def _validate_step8_percent(value: object, label: str) -> float:
    if value is None:
        raise HCMCalcError(f"Step 8 {label} is required.")
    if not isinstance(value, Real) or not isfinite(float(value)) or not 0 <= value <= 100:
        raise HCMCalcError(
            f"Step 8 {label} must be a finite value between 0 and 100."
        )
    return float(value)


def _validate_step8_number(value: object, label: str, *, allow_zero: bool) -> float:
    if value is None:
        raise HCMCalcError(f"Step 8 {label} is required.")
    if not isinstance(value, Real) or not isfinite(float(value)):
        raise HCMCalcError(f"Step 8 {label} must be a finite numeric value.")
    numeric_value = float(value)
    if numeric_value < 0 or (numeric_value == 0 and not allow_zero):
        required_range = "nonnegative" if allow_zero else "greater than zero"
        raise HCMCalcError(f"Step 8 {label} must be {required_range}.")
    return numeric_value


def level_of_service(
    follower_density_followers_mi_ln: float,
    posted_speed_mph: float,
) -> str:
    """Return the HCM7 Exhibit 15-6 motorized-vehicle LOS grade."""

    return determine_motorized_los(
        follower_density=follower_density_followers_mi_ln,
        posted_speed_limit_mph=posted_speed_mph,
    ).level_of_service


def determine_motorized_los(
    follower_density: float,
    posted_speed_limit_mph: float,
) -> MotorizedLOSDetermination:
    """Determine and audit Step 10 LOS using HCM7 Exhibit 15-6."""

    density = _validate_step10_follower_density(follower_density)
    posted_speed = _validate_step10_posted_speed(posted_speed_limit_mph)

    if posted_speed < 50.0:
        threshold_group = "posted_speed_limit_below_50_mph"
        thresholds = {"A": 2.5, "B": 5.0, "C": 10.0, "D": 15.0, "E": None}
    else:
        threshold_group = "posted_speed_limit_at_least_50_mph"
        thresholds = {"A": 2.0, "B": 4.0, "C": 8.0, "D": 12.0, "E": None}

    level = "E"
    for candidate in ("A", "B", "C", "D"):
        upper_boundary = thresholds[candidate]
        if upper_boundary is not None and density <= upper_boundary:
            level = candidate
            break

    return MotorizedLOSDetermination(
        level_of_service=level,
        los_threshold_group=threshold_group,
        los_thresholds_used=thresholds,
        follower_density_for_los=density,
        posted_speed_limit_for_los=posted_speed,
    )


def _validate_step10_follower_density(value: object) -> float:
    if value is None:
        raise HCMCalcError("Step 10 follower density is required.")
    if not isinstance(value, Real) or not isfinite(float(value)):
        raise HCMCalcError("Step 10 follower density must be a finite numeric value.")
    numeric_value = float(value)
    if numeric_value < 0:
        raise HCMCalcError("Step 10 follower density must be nonnegative.")
    return numeric_value


def _validate_step10_posted_speed(value: object) -> float:
    if value is None:
        raise HCMCalcError("Step 10 posted speed limit is required.")
    if not isinstance(value, Real) or not isfinite(float(value)):
        raise HCMCalcError("Step 10 posted speed limit must be a finite numeric value.")
    numeric_value = float(value)
    if numeric_value <= 0:
        raise HCMCalcError("Step 10 posted speed limit must be greater than zero.")
    return numeric_value


def _step10_output_fields(step10: MotorizedLOSDetermination) -> dict[str, Any]:
    return {
        "level_of_service": step10.level_of_service,
        "los_source_reference": step10.source_reference,
        "los_threshold_group": step10.los_threshold_group,
        "los_thresholds_used": step10.los_thresholds_used,
        "follower_density_for_los": step10.follower_density_for_los,
        "posted_speed_limit_for_los": step10.posted_speed_limit_for_los,
    }


def _step10_intermediate_values(
    outputs: dict[str, Any],
    *,
    prefix: str = "",
) -> list[IntermediateValue]:
    source = str(outputs["los_source_reference"])
    return [
        IntermediateValue(
            f"{prefix}level_of_service",
            outputs["level_of_service"],
            source=source,
        ),
        IntermediateValue(
            f"{prefix}los_source_reference",
            outputs["los_source_reference"],
            source=source,
        ),
        IntermediateValue(
            f"{prefix}los_threshold_group",
            outputs["los_threshold_group"],
            source=source,
        ),
        IntermediateValue(
            f"{prefix}los_thresholds_used",
            outputs["los_thresholds_used"],
            "followers/mi/ln",
            source,
        ),
        IntermediateValue(
            f"{prefix}follower_density_for_los",
            outputs["follower_density_for_los"],
            "followers/mi/ln",
            source,
        ),
        IntermediateValue(
            f"{prefix}posted_speed_limit_for_los",
            outputs["posted_speed_limit_for_los"],
            "mph",
            source,
        ),
    ]


def _apply_step10_output_fields(
    outputs: dict[str, Any],
    follower_density: float,
    posted_speed_limit_mph: float,
) -> None:
    outputs.update(
        _step10_output_fields(
            determine_motorized_los(follower_density, posted_speed_limit_mph)
        )
    )
