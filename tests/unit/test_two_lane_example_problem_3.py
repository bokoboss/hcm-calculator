import pytest

from hcmcalc.methods.two_lane_highway_ch15 import (
    TwoLaneHighwayChapter15Method,
    downstream_follower_density_adjustment,
    length_weighted_average,
    passing_lane_average_speed_differential_adjustment,
    passing_lane_effective_length,
    passing_lane_faster_lane_flow_proportion,
    passing_lane_midpoint_values,
)


EXAMPLE_3_INPUTS = {
    "case_id": "TLH-CH15-003",
    "facility_length_mi": 5.5,
    "upstream_passing_lane": False,
    "segments": [
        {
            "segment_id": 1,
            "segment_type": "passing_constrained",
            "segment_length_mi": 0.75,
            "posted_speed_mph": 55.0,
            "analysis_direction_volume_veh_h": 850.0,
            "peak_hour_factor": 0.94,
            "heavy_vehicle_percent": 8.0,
            "grade_percent": 0.0,
            "horizontal_alignment": "straight",
            "lane_width_ft": 12.0,
            "shoulder_width_ft": 6.0,
            "access_point_density_per_mi": 0.0,
        },
        {
            "segment_id": 2,
            "segment_type": "passing_lane",
            "segment_length_mi": 1.5,
            "posted_speed_mph": 55.0,
            "analysis_direction_volume_veh_h": 825.0,
            "peak_hour_factor": 0.95,
            "heavy_vehicle_percent": 8.0,
            "grade_percent": 0.0,
            "horizontal_alignment": "straight",
            "lane_width_ft": 12.0,
            "shoulder_width_ft": 6.0,
            "access_point_density_per_mi": 0.0,
        },
        {
            "segment_id": 3,
            "segment_type": "passing_constrained",
            "segment_length_mi": 1.0,
            "posted_speed_mph": 55.0,
            "analysis_direction_volume_veh_h": 820.0,
            "peak_hour_factor": 0.95,
            "heavy_vehicle_percent": 8.0,
            "grade_percent": 0.0,
            "horizontal_alignment": "straight",
            "lane_width_ft": 12.0,
            "shoulder_width_ft": 6.0,
            "access_point_density_per_mi": 0.0,
        },
        {
            "segment_id": 4,
            "segment_type": "passing_zone",
            "segment_length_mi": 0.5,
            "posted_speed_mph": 55.0,
            "analysis_direction_volume_veh_h": 800.0,
            "opposing_direction_volume_veh_h": 500.0,
            "peak_hour_factor": 0.94,
            "heavy_vehicle_percent": 7.5,
            "grade_percent": 0.0,
            "horizontal_alignment": "straight",
            "lane_width_ft": 12.0,
            "shoulder_width_ft": 6.0,
            "access_point_density_per_mi": 0.0,
        },
        {
            "segment_id": 5,
            "segment_type": "passing_constrained",
            "segment_length_mi": 1.75,
            "posted_speed_mph": 55.0,
            "analysis_direction_volume_veh_h": 795.0,
            "peak_hour_factor": 0.935,
            "heavy_vehicle_percent": 8.0,
            "grade_percent": 0.0,
            "horizontal_alignment": "straight",
            "lane_width_ft": 12.0,
            "shoulder_width_ft": 6.0,
            "access_point_density_per_mi": 0.0,
        },
    ],
}


def test_passing_lane_formula_level_intermediates() -> None:
    values = passing_lane_midpoint_values(
        demand_flow_rate_veh_h=825.0 / 0.95,
        base_free_flow_speed_mph=62.7,
        heavy_vehicle_coefficient=0.0333,
        lane_shoulder_adjustment_mph=0.0,
        access_point_adjustment_mph=0.0,
        vertical_class=1,
        segment_length_mi=1.5,
        heavy_vehicle_percent=8.0,
        capacity_veh_h=1500.0,
    )

    assert passing_lane_faster_lane_flow_proportion(
        demand_flow_rate_veh_h=825.0 / 0.95,
        heavy_vehicle_count_veh_h=(825.0 / 0.95) * 0.08,
    ) == pytest.approx(0.561, abs=0.001)
    assert values["faster_lane_flow_rate_veh_h_ln"] == pytest.approx(487.0, abs=1.0)
    assert values["slower_lane_flow_rate_veh_h_ln"] == pytest.approx(381.0, abs=1.0)
    assert values["faster_lane_heavy_vehicle_percent"] == pytest.approx(3.2, abs=0.1)
    assert values["slower_lane_heavy_vehicle_percent"] == pytest.approx(14.2, abs=0.1)
    assert passing_lane_average_speed_differential_adjustment(
        demand_flow_rate_veh_h=825.0 / 0.95,
        heavy_vehicle_percent=8.0,
    ) == pytest.approx(3.54, abs=0.1)
    assert values["faster_lane_midpoint_average_speed_mph"] == pytest.approx(
        62.5,
        abs=0.1,
    )
    assert values["slower_lane_midpoint_average_speed_mph"] == pytest.approx(
        58.8,
        abs=0.1,
    )
    assert values["faster_lane_midpoint_percent_followers"] == pytest.approx(
        44.5,
        abs=0.2,
    )
    assert values["midpoint_follower_density_followers_mi_ln"] == pytest.approx(
        2.9,
        abs=0.1,
    )


def test_downstream_adjustment_formula_level_intermediates() -> None:
    adjustment = downstream_follower_density_adjustment(
        percent_followers_value=68.0,
        demand_flow_rate_veh_h=820.0 / 0.95,
        average_speed_mph=58.9,
        downstream_distance_mi=2.5,
        upstream_percent_followers=69.7,
        passing_lane_length_mi=1.5,
    )

    assert adjustment["percent_followers_improvement_percent"] == pytest.approx(
        15.7,
        abs=0.1,
    )
    assert adjustment["speed_improvement_percent"] == pytest.approx(1.8, abs=0.1)
    assert adjustment["adjusted_follower_density_followers_mi_ln"] == pytest.approx(
        8.2,
        abs=0.1,
    )


def test_passing_lane_effective_length() -> None:
    effective_length = passing_lane_effective_length(
        upstream_follower_density_followers_mi_ln=10.709052407456566,
        upstream_percent_followers=69.68914037235186,
        upstream_demand_flow_rate_veh_h=850.0 / 0.94,
        upstream_average_speed_mph=58.84439955185795,
        passing_lane_length_mi=1.5,
    )

    assert effective_length["percent_followers_zero_mi"] == pytest.approx(
        14.4,
        abs=0.1,
    )
    assert effective_length["density_95_percent_mi"] == pytest.approx(8.1, abs=0.1)
    assert effective_length["effective_length_mi"] == pytest.approx(8.1, abs=0.1)


def test_example_problem_3_facility_outputs() -> None:
    result = TwoLaneHighwayChapter15Method().calculate(EXAMPLE_3_INPUTS)
    segments = {segment["segment_id"]: segment for segment in result.outputs["segments"]}

    assert segments[1]["follower_density_followers_mi_ln"] == pytest.approx(
        10.7,
        abs=0.1,
    )
    assert segments[1]["level_of_service"] == "D"
    assert segments[2]["midpoint_follower_density_followers_mi_ln"] == pytest.approx(
        2.9,
        abs=0.1,
    )
    assert segments[2]["level_of_service"] == "B"
    assert segments[3]["follower_density_followers_mi_ln"] == pytest.approx(
        8.2,
        abs=0.1,
    )
    assert segments[3]["level_of_service"] == "D"
    assert segments[4]["follower_density_followers_mi_ln"] == pytest.approx(
        8.2,
        abs=0.1,
    )
    assert segments[4]["level_of_service"] == "D"
    assert segments[5]["follower_density_followers_mi_ln"] == pytest.approx(
        8.8,
        abs=0.1,
    )
    assert segments[5]["level_of_service"] == "D"
    assert result.outputs["facility_follower_density_followers_mi_ln"] == pytest.approx(
        7.3,
        abs=0.1,
    )
    assert result.outputs["facility_level_of_service"] == "C"


def test_facility_length_weighted_average() -> None:
    assert length_weighted_average(
        [(10.7, 0.75), (2.9, 1.5), (8.2, 1.0), (8.2, 0.5), (8.8, 1.75)]
    ) == pytest.approx(7.3, abs=0.1)
