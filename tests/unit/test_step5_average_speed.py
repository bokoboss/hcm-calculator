import pytest

from hcmcalc.core import HCMCalcError
from hcmcalc.methods.two_lane_highway_ch15 import (
    PASSING_CONSTRAINED,
    PASSING_LANE,
    PASSING_ZONE,
    TwoLaneHighwayChapter15Method,
    estimate_average_speed,
    estimate_heavy_vehicle_speed_coefficient,
    estimate_segment_length_coefficient,
    estimate_speed_power_coefficient,
    estimate_speed_slope_coefficient,
)


def test_eq_15_9_segment_length_coefficient_by_segment_type() -> None:
    assert estimate_segment_length_coefficient(
        PASSING_CONSTRAINED, 2, 60.0, 1.0
    ) == pytest.approx(0.8724)
    assert estimate_segment_length_coefficient(
        PASSING_LANE, 4, 60.0, 1.0
    ) == pytest.approx(1.2432)


def test_eq_15_10_heavy_vehicle_coefficient_by_segment_type() -> None:
    assert estimate_heavy_vehicle_speed_coefficient(
        PASSING_ZONE, 5, 60.0, 8.0
    ) == pytest.approx(6.60117713)
    assert estimate_heavy_vehicle_speed_coefficient(
        PASSING_LANE, 3, 60.0, 8.0
    ) == pytest.approx(0.59934371)


def test_eq_15_8_slope_coefficient_by_segment_type() -> None:
    assert estimate_speed_slope_coefficient(
        PASSING_CONSTRAINED, 2, 60.0, 1500.0, 1.0, 8.0
    ) == pytest.approx(4.28096091)
    assert estimate_speed_slope_coefficient(
        PASSING_LANE, 4, 60.0, 0.0, 1.0, 8.0
    ) == pytest.approx(7.3778)


def test_eq_15_8_applies_b3_b4_and_final_minimum_max_behavior() -> None:
    # Class 5 Passing Lane b3 is negative for this input and contributes zero.
    assert estimate_speed_slope_coefficient(
        PASSING_LANE, 5, 60.0, 0.0, 0.25, 0.0
    ) == pytest.approx(4.87)


def test_eq_15_11_power_coefficient_by_segment_type() -> None:
    assert estimate_speed_power_coefficient(
        PASSING_ZONE, 2, 60.0, 500.0, 1.0, 8.0
    ) == pytest.approx(0.54503367)
    assert estimate_speed_power_coefficient(
        PASSING_LANE, 4, 60.0, 0.0, 1.0, 8.0
    ) == pytest.approx(1.05099)


def test_eq_15_7_level_class_1_average_speed_and_audit_values() -> None:
    estimate = estimate_average_speed(
        segment_type=PASSING_CONSTRAINED,
        vertical_class=1,
        segment_length_mi=0.75,
        free_flow_speed_mph=56.83,
        heavy_vehicle_percent=5.0,
        demand_flow_rate_veh_h=800.0,
        opposing_flow_veh_h=1500.0,
    )

    assert estimate.average_speed_mph == pytest.approx(53.70434)
    assert estimate.speed_slope_coefficient_m == pytest.approx(3.62657138)
    assert estimate.speed_power_coefficient_p == pytest.approx(0.41674389)
    assert estimate.segment_length_coefficient_b3 == pytest.approx(0.1029)
    assert estimate.heavy_vehicle_speed_coefficient_b4 == pytest.approx(0.0)
    assert "HCM Exhibit 15-19" in estimate.source_references


def test_eq_15_7_returns_ffs_at_or_below_100_veh_h() -> None:
    estimate = estimate_average_speed(
        segment_type=PASSING_CONSTRAINED,
        vertical_class=1,
        segment_length_mi=0.75,
        free_flow_speed_mph=56.83,
        heavy_vehicle_percent=5.0,
        demand_flow_rate_veh_h=100.0,
        opposing_flow_veh_h=1500.0,
    )

    assert estimate.average_speed_mph == 56.83


def test_guarded_example_4_segment_3_step5_values_are_preserved() -> None:
    estimate = estimate_average_speed(
        segment_type=PASSING_CONSTRAINED,
        vertical_class=4,
        segment_length_mi=0.5,
        free_flow_speed_mph=60.1,
        heavy_vehicle_percent=8.0,
        demand_flow_rate_veh_h=1100.0 / 0.90,
        opposing_flow_veh_h=1500.0,
    )

    assert estimate.average_speed_mph == pytest.approx(50.75, abs=0.01)
    assert estimate.segment_length_coefficient_b3 == pytest.approx(3.45126)
    assert estimate.heavy_vehicle_speed_coefficient_b4 == pytest.approx(2.47423)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"segment_type": "unknown"}, "Unsupported Step 5 segment type"),
        ({"vertical_class": 6}, "vertical class"),
        ({"free_flow_speed_mph": 0.0}, "free-flow speed"),
        ({"segment_length_mi": 0.0}, "segment length"),
        ({"heavy_vehicle_percent": -0.1}, "heavy-vehicle percentage"),
        ({"demand_flow_rate_veh_h": -1.0}, "demand flow rate"),
        ({"opposing_flow_veh_h": -1.0}, "opposing flow rate"),
        ({"free_flow_speed_mph": None}, "free-flow speed is required"),
        ({"segment_length_mi": None}, "segment length is required"),
        ({"heavy_vehicle_percent": None}, "heavy-vehicle percentage is required"),
        ({"demand_flow_rate_veh_h": None}, "demand flow rate is required"),
        ({"opposing_flow_veh_h": None}, "opposing flow rate is required"),
    ],
)
def test_step5_invalid_inputs_are_rejected_clearly(
    overrides: dict[str, object], message: str
) -> None:
    inputs = {
        "segment_type": PASSING_CONSTRAINED,
        "vertical_class": 1,
        "segment_length_mi": 0.75,
        "free_flow_speed_mph": 56.83,
        "heavy_vehicle_percent": 5.0,
        "demand_flow_rate_veh_h": 800.0,
        "opposing_flow_veh_h": 1500.0,
    }
    inputs.update(overrides)

    with pytest.raises(HCMCalcError, match=message):
        estimate_average_speed(**inputs)  # type: ignore[arg-type]


def test_single_segment_audit_exposes_step5_intermediates() -> None:
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
            "terrain_type": "level",
            "grade_length_mi": 0.75,
        }
    )
    names = {value.name for value in result.intermediate_values}

    assert "segment_length_coefficient_b3" in names
    assert "heavy_vehicle_speed_coefficient_b4" in names
    assert "average_speed_slope_coefficient" in names
    assert "average_speed_power_coefficient" in names
    assert "average_speed_source_reference" in result.outputs
