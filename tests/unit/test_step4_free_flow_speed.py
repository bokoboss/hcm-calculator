import pytest

from hcmcalc.core import HCMCalcError
from hcmcalc.methods.two_lane_highway_ch15 import (
    TwoLaneHighwayChapter15Method,
    access_point_adjustment,
    base_free_flow_speed,
    estimate_free_flow_speed,
    estimated_free_flow_speed,
    heavy_vehicle_ffs_coefficient,
    lane_shoulder_adjustment,
)


def _step4_inputs(**overrides):
    inputs = {
        "posted_speed_mph": 50.0,
        "vertical_class": 1,
        "segment_length_mi": 0.75,
        "opposing_flow_veh_h": 1500.0,
        "heavy_vehicle_percent": 5.0,
        "lane_width_ft": 12.0,
        "shoulder_width_ft": 6.0,
        "access_point_density_per_mi": 0.0,
    }
    inputs.update(overrides)
    return inputs


def test_eq_15_2_base_free_flow_speed_from_posted_speed() -> None:
    assert base_free_flow_speed(50.0) == pytest.approx(57.0)


def test_eq_15_5_lane_shoulder_adjustment() -> None:
    assert lane_shoulder_adjustment(10.0, 2.0) == pytest.approx(4.0)


@pytest.mark.parametrize(
    ("access_point_density", "expected"),
    [(0.0, 0.0), (20.0, 5.0), (100.0, 10.0)],
)
def test_eq_15_6_access_point_adjustment(
    access_point_density: float,
    expected: float,
) -> None:
    assert access_point_adjustment(access_point_density) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("vertical_class", "expected"),
    [
        (1, 0.0333),
        (2, 0.0455625),
        (3, 0.14629),
        (4, 0.2387025),
        (5, 0.2523175),
    ],
)
def test_eq_15_4_exhibit_15_12_coefficients(
    vertical_class: int,
    expected: float,
) -> None:
    assert heavy_vehicle_ffs_coefficient(
        vertical_class=vertical_class,
        base_free_flow_speed_mph=57.0,
        segment_length_mi=0.75,
        opposing_flow_veh_h=1500.0,
    ) == pytest.approx(expected)


def test_eq_15_3_final_free_flow_speed() -> None:
    assert estimated_free_flow_speed(57.0, 0.0333, 5.0, 1.0, 2.0) == pytest.approx(
        53.8335
    )


def test_step4_level_class_1_preserves_minimum_coefficient_behavior() -> None:
    result = estimate_free_flow_speed(**_step4_inputs())

    assert result.base_free_flow_speed_mph == pytest.approx(57.0)
    assert result.heavy_vehicle_speed_adjustment_coefficient == pytest.approx(0.0333)
    assert result.lane_shoulder_adjustment_mph == 0.0
    assert result.access_point_adjustment_mph == 0.0
    assert result.free_flow_speed_mph == pytest.approx(56.8335)
    assert result.source_references == (
        "HCM Eq. 15-2",
        "HCM Eq. 15-3",
        "HCM Eq. 15-4",
        "HCM Exhibit 15-12",
        "HCM Eq. 15-5",
        "HCM Eq. 15-6",
    )


def test_step4_class_4_matches_tlh_ch15_004_segment_3_ffs() -> None:
    result = estimate_free_flow_speed(
        **_step4_inputs(
            posted_speed_mph=55.0,
            vertical_class=4,
            segment_length_mi=0.5,
            heavy_vehicle_percent=8.0,
        )
    )

    assert result.heavy_vehicle_speed_adjustment_coefficient == pytest.approx(
        0.3285265
    )
    assert result.free_flow_speed_mph == pytest.approx(60.1, abs=0.1)


def test_successful_single_segment_audit_exposes_step4_values() -> None:
    result = TwoLaneHighwayChapter15Method().calculate_single_segment(
        {
            "segment_type": "passing_constrained",
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

    intermediate_names = {value.name for value in result.intermediate_values}
    assert {
        "base_free_flow_speed",
        "heavy_vehicle_speed_adjustment_coefficient",
        "lane_shoulder_adjustment",
        "access_point_adjustment",
        "free_flow_speed",
    } <= intermediate_names
    assert result.outputs["heavy_vehicle_speed_adjustment_coefficient"] == pytest.approx(
        0.0333
    )


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"posted_speed_mph": None}, "Posted/base speed is required"),
        ({"posted_speed_mph": 0.0}, "Posted/base speed must be a positive"),
        ({"vertical_class": None}, "Vertical class is required"),
        ({"vertical_class": 6}, "Unsupported vertical class"),
        ({"segment_length_mi": None}, "Segment length must be a positive"),
        ({"segment_length_mi": 0.0}, "Segment length must be a positive"),
        ({"opposing_flow_veh_h": None}, "Opposing flow must be a nonnegative"),
        ({"opposing_flow_veh_h": -1.0}, "Opposing flow must be a nonnegative"),
        ({"heavy_vehicle_percent": None}, "Heavy-vehicle percentage"),
        ({"heavy_vehicle_percent": float("nan")}, "Heavy-vehicle percentage"),
        ({"heavy_vehicle_percent": 100.1}, "Heavy-vehicle percentage"),
        ({"lane_width_ft": None}, "lane_width_ft must be a finite"),
        ({"lane_width_ft": 8.9}, "lane_width_ft must be within"),
        ({"shoulder_width_ft": None}, "shoulder_width_ft must be a finite"),
        ({"shoulder_width_ft": 6.1}, "shoulder_width_ft must be within"),
        ({"access_point_density_per_mi": None}, "must be a finite"),
        ({"access_point_density_per_mi": -0.1}, "must not be negative"),
    ],
)
def test_step4_rejects_invalid_inputs(overrides: dict, message: str) -> None:
    with pytest.raises(HCMCalcError, match=message):
        estimate_free_flow_speed(**_step4_inputs(**overrides))
