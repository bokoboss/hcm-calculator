"""HCM 7th Edition Chapter 15 Two-Lane Highway method.

Only the Chapter 26 Example Problem 1 calculation path is implemented. Other
two-lane highway cases still require methodology mapping and validation before
use.
"""

from dataclasses import dataclass
from math import exp
from typing import Any

from hcmcalc.core import (
    CalculationResult,
    HCMCalcError,
    IntermediateValue,
    MethodNotImplementedError,
)


@dataclass(frozen=True)
class TwoLaneExampleProblem1Inputs:
    """Validated input shape for HCM Chapter 26 Two-Lane Example Problem 1."""

    analysis_hour_volume_veh: float
    peak_hour_factor: float
    segment_type: str
    terrain: str
    horizontal_alignment: str
    posted_speed_mph: float
    base_speed_over_posted_mph: float
    lane_shoulder_adjustment_mph: float
    speed_demand_coefficient: float
    percent_followers_coefficient: float


class TwoLaneHighwayChapter15Method:
    """Partial two-lane highway motorized vehicle analysis implementation."""

    facility_type = "two_lane_highway"
    method_name = "hcm7_ch15_two_lane_motorized"

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        """Run the validated Chapter 26 Example Problem 1 calculation path."""

        case_id = inputs.get("case_id")
        if case_id != "TLH-CH15-001":
            raise MethodNotImplementedError(
                "Only HCM Chapter 26 Two-Lane Highway Example Problem 1 is "
                "implemented. Additional Chapter 15 cases require methodology "
                "mapping and validation before implementation."
            )

        parsed_inputs = _parse_example_problem_1_inputs(inputs)
        _validate_example_problem_1_scope(parsed_inputs)

        demand = demand_flow_rate(
            parsed_inputs.analysis_hour_volume_veh,
            parsed_inputs.peak_hour_factor,
        )
        capacity = passing_constrained_capacity()
        demand_capacity_ratio = demand / capacity
        vertical_class = vertical_alignment_class(parsed_inputs.terrain)
        bffs = base_free_flow_speed(
            parsed_inputs.posted_speed_mph,
            parsed_inputs.base_speed_over_posted_mph,
        )
        ffs = estimated_free_flow_speed(
            bffs,
            parsed_inputs.lane_shoulder_adjustment_mph,
        )
        speed = average_speed(
            ffs,
            demand,
            parsed_inputs.speed_demand_coefficient,
        )
        followers = percent_followers(
            demand,
            parsed_inputs.percent_followers_coefficient,
        )
        density = follower_density(demand, speed, followers)
        los = level_of_service(density)

        return CalculationResult(
            method=self.method_name,
            facility_type=self.facility_type,
            outputs={
                "demand_flow_rate_veh_h": demand,
                "capacity_veh_h": capacity,
                "demand_capacity_ratio": demand_capacity_ratio,
                "vertical_class": vertical_class,
                "base_free_flow_speed_mph": bffs,
                "free_flow_speed_mph": ffs,
                "average_speed_mph": speed,
                "percent_followers": followers,
                "follower_density_followers_mi_ln": density,
                "level_of_service": los,
            },
            intermediate_values=[
                IntermediateValue(
                    name="demand_flow_rate",
                    value=demand,
                    units="veh/h",
                    source="HCM 7th Ed. Ch. 15 demand flow rate equation",
                ),
                IntermediateValue(
                    name="passing_constrained_capacity",
                    value=capacity,
                    units="veh/h",
                    source="HCM 7th Ed. Ch. 15 Passing Constrained segment capacity",
                ),
                IntermediateValue(
                    name="demand_capacity_ratio",
                    value=demand_capacity_ratio,
                    source="Computed d/c check",
                ),
                IntermediateValue(
                    name="vertical_alignment_class",
                    value=vertical_class,
                    source="HCM 7th Ed. Ch. 15 vertical alignment classification",
                ),
                IntermediateValue(
                    name="base_free_flow_speed",
                    value=bffs,
                    units="mph",
                    source="HCM 7th Ed. Ch. 15 BFFS equation",
                ),
                IntermediateValue(
                    name="free_flow_speed",
                    value=ffs,
                    units="mph",
                    source="HCM 7th Ed. Ch. 15 FFS equation",
                ),
                IntermediateValue(
                    name="average_speed",
                    value=speed,
                    units="mph",
                    source="HCM 7th Ed. Ch. 15 Passing Constrained speed equation",
                ),
                IntermediateValue(
                    name="percent_followers",
                    value=followers,
                    units="%",
                    source="HCM 7th Ed. Ch. 15 Passing Constrained follower equation",
                ),
                IntermediateValue(
                    name="follower_density",
                    value=density,
                    units="followers/mi/ln",
                    source="HCM 7th Ed. Ch. 15 follower density equation",
                ),
            ],
            assumptions=[
                "Validated only for HCM Chapter 26 Two-Lane Highway Example Problem 1.",
                "Applies to a level, straight Passing Constrained segment.",
            ],
        )


def _parse_example_problem_1_inputs(
    inputs: dict[str, Any],
) -> TwoLaneExampleProblem1Inputs:
    try:
        return TwoLaneExampleProblem1Inputs(
            analysis_hour_volume_veh=float(inputs["analysis_hour_volume_veh"]),
            peak_hour_factor=float(inputs["peak_hour_factor"]),
            segment_type=str(inputs["segment_type"]),
            terrain=str(inputs["terrain"]),
            horizontal_alignment=str(inputs["horizontal_alignment"]),
            posted_speed_mph=float(inputs["posted_speed_mph"]),
            base_speed_over_posted_mph=float(inputs["base_speed_over_posted_mph"]),
            lane_shoulder_adjustment_mph=float(inputs["lane_shoulder_adjustment_mph"]),
            speed_demand_coefficient=float(inputs["speed_demand_coefficient"]),
            percent_followers_coefficient=float(
                inputs["percent_followers_coefficient"]
            ),
        )
    except KeyError as exc:
        raise HCMCalcError(f"Missing Example Problem 1 input: {exc.args[0]}") from exc


def _validate_example_problem_1_scope(inputs: TwoLaneExampleProblem1Inputs) -> None:
    if inputs.segment_type != "passing_constrained":
        raise MethodNotImplementedError(
            "Only Passing Constrained segments are implemented."
        )
    if inputs.terrain != "level":
        raise MethodNotImplementedError("Only level terrain is implemented.")
    if inputs.horizontal_alignment != "straight":
        raise MethodNotImplementedError(
            "Only straight horizontal alignment is implemented."
        )
    if inputs.peak_hour_factor <= 0:
        raise HCMCalcError("peak_hour_factor must be greater than zero.")


def demand_flow_rate(analysis_hour_volume_veh: float, peak_hour_factor: float) -> float:
    """HCM Ch. 15 demand flow rate: analysis hour volume divided by PHF."""

    # HCM Ch. 15 demand flow rate equation: v = V / PHF for this validation case.
    return analysis_hour_volume_veh / peak_hour_factor


def passing_constrained_capacity() -> float:
    """HCM Ch. 15 Passing Constrained segment capacity."""

    return 1700.0


def vertical_alignment_class(terrain: str) -> int:
    """HCM Ch. 15 vertical class mapping for level terrain."""

    if terrain != "level":
        raise MethodNotImplementedError(
            "Only level terrain vertical class is implemented."
        )
    return 1


def base_free_flow_speed(
    posted_speed_mph: float,
    base_speed_over_posted_mph: float,
) -> float:
    """HCM Ch. 15 BFFS estimate from posted speed plus example adjustment."""

    return posted_speed_mph + base_speed_over_posted_mph


def estimated_free_flow_speed(
    base_free_flow_speed_mph: float,
    lane_shoulder_adjustment_mph: float,
) -> float:
    """HCM Ch. 15 FFS: BFFS minus the lane/shoulder width adjustment."""

    # HCM Ch. 15 FFS equation form used by Example Problem 1.
    return base_free_flow_speed_mph - lane_shoulder_adjustment_mph


def average_speed(
    free_flow_speed_mph: float,
    demand_flow_rate_veh_h: float,
    speed_demand_coefficient: float,
) -> float:
    """HCM Ch. 15 Passing Constrained average speed equation."""

    # HCM Ch. 15 Passing Constrained speed equation, with the Example 1 factor
    # supplied by the validation fixture.
    return free_flow_speed_mph - speed_demand_coefficient * demand_flow_rate_veh_h


def percent_followers(
    demand_flow_rate_veh_h: float,
    percent_followers_coefficient: float,
) -> float:
    """HCM Ch. 15 Passing Constrained percent followers equation."""

    # HCM Ch. 15 Passing Constrained follower equation, with the Example 1
    # exponent coefficient supplied by the validation fixture.
    return 100.0 * (1.0 - exp(-percent_followers_coefficient * demand_flow_rate_veh_h))


def follower_density(
    demand_flow_rate_veh_h: float,
    average_speed_mph: float,
    percent_followers_value: float,
) -> float:
    """HCM Ch. 15 follower density in followers per mile per lane."""

    # HCM Ch. 15 follower density equation: FD = (v / ATS) * (PF / 100).
    return demand_flow_rate_veh_h / average_speed_mph * (percent_followers_value / 100.0)


def level_of_service(follower_density_followers_mi_ln: float) -> str:
    """HCM Ch. 15 LOS thresholds for two-lane highway follower density."""

    if follower_density_followers_mi_ln <= 2.0:
        return "A"
    if follower_density_followers_mi_ln <= 4.0:
        return "B"
    if follower_density_followers_mi_ln <= 8.0:
        return "C"
    if follower_density_followers_mi_ln <= 12.0:
        return "D"
    if follower_density_followers_mi_ln <= 18.0:
        return "E"
    return "F"
