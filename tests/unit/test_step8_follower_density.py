import pytest

from hcmcalc.core import HCMCalcError
from hcmcalc.methods.two_lane_highway_ch15 import (
    PASSING_CONSTRAINED,
    PASSING_LANE,
    PASSING_ZONE,
    TwoLaneHighwayChapter15Method,
    estimate_follower_density,
    estimate_passing_constrained_or_zone_follower_density,
    estimate_passing_lane_midpoint_follower_density,
)


def test_eq_15_35_passing_constrained_follower_density() -> None:
    estimate = estimate_passing_constrained_or_zone_follower_density(
        segment_type=PASSING_CONSTRAINED,
        percent_followers=67.7,
        demand_flow_rate_veh_h=800.0,
        average_speed_mph=53.7,
    )

    assert estimate.follower_density == pytest.approx(10.08566)
    assert estimate.source_reference == "HCM Eq. 15-35"
    assert "PF / 100" in estimate.formula


def test_eq_15_35_passing_zone_follower_density() -> None:
    estimate = estimate_follower_density(
        segment_type=PASSING_ZONE,
        percent_followers=60.0,
        demand_flow_rate_veh_h=900.0,
        average_speed_mph=50.0,
    )

    assert estimate.follower_density == pytest.approx(10.8)
    assert estimate.source_reference == "HCM Eq. 15-35"


def test_eq_15_34_passing_lane_midpoint_follower_density_and_components() -> None:
    estimate = estimate_passing_lane_midpoint_follower_density(
        segment_type=PASSING_LANE,
        faster_lane_percent_followers=44.5,
        slower_lane_percent_followers=35.6,
        faster_lane_flow_rate_veh_h_ln=487.0,
        slower_lane_flow_rate_veh_h_ln=381.0,
        faster_lane_midpoint_speed_mph=62.5,
        slower_lane_midpoint_speed_mph=58.8,
    )

    assert estimate.faster_lane_component == pytest.approx(3.46744)
    assert estimate.slower_lane_component == pytest.approx(2.30673469)
    assert estimate.follower_density == pytest.approx(2.88708735)
    assert estimate.source_reference == "HCM Eq. 15-34"


def test_representative_level_class_1_step8_audit_values() -> None:
    result = TwoLaneHighwayChapter15Method().calculate_single_segment(
        {
            "segment_type": PASSING_CONSTRAINED,
            "segment_length_mi": 0.75,
            "posted_speed_mph": 50.0,
            "analysis_direction_volume_veh_h": 752.0,
            "peak_hour_factor": 0.94,
            "heavy_vehicle_percent": 5.0,
            "grade_percent": 0.0,
            "horizontal_alignment": "straight",
            "lane_width_ft": 12.0,
            "shoulder_width_ft": 6.0,
            "access_point_density_per_mi": 0.0,
        }
    )
    names = {value.name for value in result.intermediate_values}

    assert result.outputs["follower_density_followers_mi_ln"] == pytest.approx(
        10.1, abs=0.1
    )
    assert result.outputs["follower_density_source_reference"] == "HCM Eq. 15-35"
    assert {
        "follower_density",
        "follower_density_source_reference",
        "follower_density_formula",
    } <= names


def test_guarded_example_4_segment_3_step8_value_is_preserved() -> None:
    result = TwoLaneHighwayChapter15Method().calculate_single_segment(
        {
            "segment_type": PASSING_CONSTRAINED,
            "segment_length_mi": 0.5,
            "posted_speed_mph": 55.0,
            "analysis_direction_volume_veh_h": 1100.0,
            "peak_hour_factor": 0.90,
            "heavy_vehicle_percent": 8.0,
            "grade_percent": 6.0,
            "grade_length_mi": 0.5,
            "terrain_type": "mountainous",
            "horizontal_alignment": "straight",
            "lane_width_ft": 12.0,
            "shoulder_width_ft": 6.0,
            "access_point_density_per_mi": 0.0,
        }
    )

    assert result.outputs["follower_density_followers_mi_ln"] == pytest.approx(
        20.2, abs=0.1
    )
    assert result.outputs["follower_density_source_reference"] == "HCM Eq. 15-35"


def test_supported_passing_lane_exposes_step8_components_and_audit_values() -> None:
    result = TwoLaneHighwayChapter15Method().calculate_single_segment(
        {
            "segment_type": PASSING_LANE,
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
        }
    )
    names = {value.name for value in result.intermediate_values}

    assert result.outputs["follower_density_source_reference"] == "HCM Eq. 15-34"
    assert result.outputs["faster_lane_component"] > 0
    assert result.outputs["slower_lane_component"] > 0
    assert {"faster_lane_component", "slower_lane_component"} <= names


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"segment_type": "unknown"}, "Unsupported Step 8 segment type"),
        ({"percent_followers": None}, "percent followers is required"),
        ({"percent_followers": -0.1}, "percent followers"),
        ({"percent_followers": 100.1}, "percent followers"),
        ({"demand_flow_rate_veh_h": None}, "demand flow rate is required"),
        ({"demand_flow_rate_veh_h": -1.0}, "demand flow rate"),
        ({"average_speed_mph": None}, "average speed is required"),
        ({"average_speed_mph": 0.0}, "average speed"),
        ({"average_speed_mph": -1.0}, "average speed"),
    ],
)
def test_eq_15_35_invalid_inputs_are_rejected_clearly(
    overrides: dict[str, object], message: str
) -> None:
    inputs = {
        "segment_type": PASSING_CONSTRAINED,
        "percent_followers": 60.0,
        "demand_flow_rate_veh_h": 900.0,
        "average_speed_mph": 50.0,
    }
    inputs.update(overrides)

    with pytest.raises(HCMCalcError, match=message):
        estimate_follower_density(**inputs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {"faster_lane_percent_followers": None},
            "faster-lane midpoint percent followers is required",
        ),
        (
            {"slower_lane_percent_followers": 101.0},
            "slower-lane midpoint percent followers",
        ),
        ({"faster_lane_flow_rate_veh_h_ln": None}, "faster-lane flow rate is required"),
        ({"slower_lane_flow_rate_veh_h_ln": 0.0}, "slower-lane flow rate"),
        ({"faster_lane_midpoint_speed_mph": 0.0}, "faster-lane midpoint speed"),
        ({"slower_lane_midpoint_speed_mph": -1.0}, "slower-lane midpoint speed"),
    ],
)
def test_eq_15_34_invalid_midpoint_inputs_are_rejected_clearly(
    overrides: dict[str, object], message: str
) -> None:
    inputs = {
        "segment_type": PASSING_LANE,
        "faster_lane_percent_followers": 44.5,
        "slower_lane_percent_followers": 35.6,
        "faster_lane_flow_rate_veh_h_ln": 487.0,
        "slower_lane_flow_rate_veh_h_ln": 381.0,
        "faster_lane_midpoint_speed_mph": 62.5,
        "slower_lane_midpoint_speed_mph": 58.8,
    }
    inputs.update(overrides)

    with pytest.raises(HCMCalcError, match=message):
        estimate_follower_density(**inputs)  # type: ignore[arg-type]
