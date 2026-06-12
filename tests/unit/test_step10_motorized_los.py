import pytest

from hcmcalc.core import HCMCalcError
from hcmcalc.methods.two_lane_highway_ch15 import (
    TwoLaneHighwayChapter15Method,
    determine_motorized_los,
    level_of_service,
)


@pytest.mark.parametrize(
    ("follower_density", "expected_los"),
    [(1.0, "A"), (3.0, "B"), (6.0, "C"), (10.0, "D"), (13.0, "E")],
)
def test_higher_speed_los_bands(follower_density: float, expected_los: str) -> None:
    assert level_of_service(follower_density, posted_speed_mph=50.0) == expected_los


@pytest.mark.parametrize(
    ("follower_density", "expected_los"),
    [(1.0, "A"), (4.0, "B"), (7.0, "C"), (12.0, "D"), (16.0, "E")],
)
def test_lower_speed_los_bands(follower_density: float, expected_los: str) -> None:
    assert level_of_service(follower_density, posted_speed_mph=49.999) == expected_los


@pytest.mark.parametrize(
    ("posted_speed_mph", "boundary", "expected_los"),
    [
        (50.0, 2.0, "A"),
        (50.0, 4.0, "B"),
        (50.0, 8.0, "C"),
        (50.0, 12.0, "D"),
        (49.0, 2.5, "A"),
        (49.0, 5.0, "B"),
        (49.0, 10.0, "C"),
        (49.0, 15.0, "D"),
    ],
)
def test_exact_upper_boundary_belongs_to_better_los_band(
    posted_speed_mph: float,
    boundary: float,
    expected_los: str,
) -> None:
    assert level_of_service(boundary, posted_speed_mph) == expected_los


@pytest.mark.parametrize(
    ("posted_speed_mph", "boundary", "expected_los"),
    [
        (50.0, 2.0, "B"),
        (50.0, 4.0, "C"),
        (50.0, 8.0, "D"),
        (50.0, 12.0, "E"),
        (49.0, 2.5, "B"),
        (49.0, 5.0, "C"),
        (49.0, 10.0, "D"),
        (49.0, 15.0, "E"),
    ],
)
def test_just_above_boundary_moves_to_worse_los_band(
    posted_speed_mph: float,
    boundary: float,
    expected_los: str,
) -> None:
    assert level_of_service(boundary + 0.0001, posted_speed_mph) == expected_los


@pytest.mark.parametrize(
    ("follower_density", "message"),
    [
        (None, "Step 10 follower density is required"),
        (-0.0001, "Step 10 follower density must be nonnegative"),
        (float("nan"), "Step 10 follower density must be a finite numeric value"),
        (float("inf"), "Step 10 follower density must be a finite numeric value"),
    ],
)
def test_invalid_follower_density_is_rejected(
    follower_density: object,
    message: str,
) -> None:
    with pytest.raises(HCMCalcError, match=message):
        determine_motorized_los(follower_density, 50.0)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("posted_speed_mph", "message"),
    [
        (None, "Step 10 posted speed limit is required"),
        (0.0, "Step 10 posted speed limit must be greater than zero"),
        (-1.0, "Step 10 posted speed limit must be greater than zero"),
        (float("nan"), "Step 10 posted speed limit must be a finite numeric value"),
        (float("inf"), "Step 10 posted speed limit must be a finite numeric value"),
    ],
)
def test_invalid_posted_speed_is_rejected(
    posted_speed_mph: object,
    message: str,
) -> None:
    with pytest.raises(HCMCalcError, match=message):
        determine_motorized_los(2.0, posted_speed_mph)  # type: ignore[arg-type]


def test_step10_determination_exposes_audit_fields() -> None:
    result = determine_motorized_los(12.0001, 50.0)

    assert result.level_of_service == "E"
    assert result.los_threshold_group == "posted_speed_limit_at_least_50_mph"
    assert result.los_thresholds_used == {
        "A": 2.0,
        "B": 4.0,
        "C": 8.0,
        "D": 12.0,
        "E": None,
    }
    assert result.follower_density_for_los == 12.0001
    assert result.posted_speed_limit_for_los == 50.0
    assert result.source_reference == "HCM7 Exhibit 15-6"


def test_example_problem_1_outputs_include_step10_audit_fields() -> None:
    result = TwoLaneHighwayChapter15Method().calculate(
        {
            "case_id": "TLH-CH15-001",
            "facility_type": "two_lane_highway",
            "segment_type": "passing_constrained",
            "analysis_direction_volume_veh_h": 752.0,
            "peak_hour_factor": 0.94,
            "heavy_vehicle_percent": 5.0,
            "segment_length_mi": 0.75,
            "grade_percent": 0.0,
            "posted_speed_mph": 50.0,
            "lane_width_ft": 12.0,
            "shoulder_width_ft": 6.0,
            "access_point_density_per_mi": 0.0,
            "horizontal_alignment": "straight",
            "upstream_passing_lane": False,
        }
    )

    outputs = result.outputs
    assert outputs["level_of_service"] == "D"
    assert outputs["los_source_reference"] == "HCM7 Exhibit 15-6"
    assert outputs["los_threshold_group"] == "posted_speed_limit_at_least_50_mph"
    assert outputs["follower_density_for_los"] == outputs[
        "follower_density_followers_mi_ln"
    ]
    assert outputs["posted_speed_limit_for_los"] == 50.0
    assert {value.name for value in result.intermediate_values} >= {
        "level_of_service",
        "los_source_reference",
        "los_threshold_group",
        "los_thresholds_used",
        "follower_density_for_los",
        "posted_speed_limit_for_los",
    }
