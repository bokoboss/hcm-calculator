import pytest

from hcmcalc.core import HCMCalcError
from hcmcalc.methods.two_lane_highway_ch15 import (
    PASSING_CONSTRAINED,
    PASSING_LANE,
    PASSING_ZONE,
    TwoLaneHighwayChapter15Method,
    estimate_percent_followers,
    passing_lane_percent_followers_at_25_percent_capacity,
    passing_lane_percent_followers_at_capacity,
    percent_followers,
    percent_followers_at_25_percent_capacity,
    percent_followers_at_capacity,
    percent_followers_power_coefficient,
    percent_followers_slope_coefficient,
)


def _step6_inputs(**overrides):
    inputs = {
        "segment_type": PASSING_CONSTRAINED,
        "vertical_class": 1,
        "segment_length_mi": 0.75,
        "free_flow_speed_mph": 56.8335,
        "heavy_vehicle_percent": 5.0,
        "demand_flow_rate_veh_h": 800.0,
        "opposing_flow_veh_h": 1500.0,
        "capacity_veh_h": 1700.0,
    }
    inputs.update(overrides)
    return inputs


@pytest.mark.parametrize(
    ("vertical_class", "expected_cap", "expected_25_cap"),
    [
        (1, 85.69373446, 49.18347574),
        (2, 86.41875643, 50.84494889),
        (3, 86.76303166, 51.25079896),
        (4, 91.86917134, 58.69525649),
        (5, 94.60014214, 60.70602492),
    ],
)
def test_eq_15_18_and_eq_15_20_tables_cover_vertical_classes_1_through_5(
    vertical_class: int,
    expected_cap: float,
    expected_25_cap: float,
) -> None:
    args = (vertical_class, 1.0, 60.0, 8.0, 1500.0)

    assert percent_followers_at_capacity(*args) == pytest.approx(expected_cap)
    assert percent_followers_at_25_percent_capacity(*args) == pytest.approx(
        expected_25_cap
    )


@pytest.mark.parametrize(
    ("vertical_class", "expected_cap", "expected_25_cap"),
    [
        (1, 81.16153652, 39.52073768),
        (2, 79.68893568, 38.58545476),
        (3, 77.68264784, 36.81614812),
        (4, 77.35875732, 34.62128640),
        (5, 73.55370892, 32.59681597),
    ],
)
def test_eq_15_19_and_eq_15_21_tables_cover_vertical_classes_1_through_5(
    vertical_class: int,
    expected_cap: float,
    expected_25_cap: float,
) -> None:
    args = (vertical_class, 1.0, 60.0, 8.0)

    assert passing_lane_percent_followers_at_capacity(*args) == pytest.approx(
        expected_cap
    )
    assert passing_lane_percent_followers_at_25_percent_capacity(
        *args
    ) == pytest.approx(expected_25_cap)


@pytest.mark.parametrize(
    ("segment_type", "expected_m", "expected_p"),
    [
        (PASSING_CONSTRAINED, -1.3419608051, 0.7456873340),
        (PASSING_ZONE, -1.3419608051, 0.7456873340),
        (PASSING_LANE, -1.0083145819, 0.8953967396),
    ],
)
def test_eq_15_22_and_eq_15_23_use_segment_type_tables(
    segment_type: str,
    expected_m: float,
    expected_p: float,
) -> None:
    if segment_type == PASSING_LANE:
        pf_cap, pf_25_cap, capacity = 77.35875732487779, 34.62128640065086, 1500.0
    else:
        pf_cap, pf_25_cap, capacity = 86.41875642809794, 50.84494889441364, 1700.0

    assert percent_followers_slope_coefficient(
        segment_type, pf_cap, pf_25_cap, capacity
    ) == pytest.approx(expected_m)
    assert percent_followers_power_coefficient(
        segment_type, pf_cap, pf_25_cap, capacity
    ) == pytest.approx(expected_p)


def test_eq_15_17_level_class_1_and_step6_audit_values() -> None:
    estimate = estimate_percent_followers(**_step6_inputs())

    assert estimate.percent_followers == pytest.approx(67.71349)
    assert estimate.percent_followers_at_capacity == pytest.approx(86.413, abs=0.01)
    assert estimate.percent_followers_at_25_capacity == pytest.approx(50.518, abs=0.01)
    assert "HCM Exhibit 15-24" in estimate.source_references
    assert "HCM Exhibit 15-29" in estimate.source_references


def test_guarded_example_4_segment_3_step6_values_are_preserved() -> None:
    estimate = estimate_percent_followers(
        **_step6_inputs(
            vertical_class=4,
            segment_length_mi=0.5,
            free_flow_speed_mph=60.1,
            heavy_vehicle_percent=8.0,
            demand_flow_rate_veh_h=1100.0 / 0.90,
        )
    )

    assert estimate.percent_followers == pytest.approx(83.9, abs=0.2)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"segment_type": "unknown"}, "Unsupported Step 6 segment type"),
        ({"vertical_class": 6}, "vertical class"),
        ({"segment_length_mi": 0.0}, "segment length"),
        ({"free_flow_speed_mph": 0.0}, "free-flow speed"),
        ({"heavy_vehicle_percent": -0.1}, "heavy-vehicle percentage"),
        ({"demand_flow_rate_veh_h": -1.0}, "demand flow rate"),
        ({"capacity_veh_h": 0.0}, "capacity"),
        ({"segment_length_mi": None}, "segment length is required"),
        ({"free_flow_speed_mph": None}, "free-flow speed is required"),
        ({"heavy_vehicle_percent": None}, "heavy-vehicle percentage is required"),
        ({"demand_flow_rate_veh_h": None}, "demand flow rate is required"),
        ({"capacity_veh_h": None}, "capacity is required"),
    ],
)
def test_step6_invalid_inputs_are_rejected_clearly(
    overrides: dict[str, object], message: str
) -> None:
    with pytest.raises(HCMCalcError, match=message):
        estimate_percent_followers(**_step6_inputs(**overrides))  # type: ignore[arg-type]


@pytest.mark.parametrize("invalid_percent", [-0.1, 100.0, 100.1])
def test_eq_15_22_and_eq_15_23_reject_invalid_logarithm_inputs(
    invalid_percent: float,
) -> None:
    with pytest.raises(HCMCalcError, match="logarithms"):
        percent_followers_slope_coefficient(
            PASSING_CONSTRAINED, invalid_percent, 50.0, 1700.0
        )
    with pytest.raises(HCMCalcError, match="logarithms"):
        percent_followers_power_coefficient(
            PASSING_CONSTRAINED, 80.0, invalid_percent, 1700.0
        )


def test_eq_15_17_rejects_invalid_inputs() -> None:
    with pytest.raises(HCMCalcError, match="demand flow rate"):
        percent_followers(-1.0, -1.0, 0.8)
    with pytest.raises(HCMCalcError, match="slope coefficient"):
        percent_followers(800.0, 0.0, 0.8)
    with pytest.raises(HCMCalcError, match="power coefficient"):
        percent_followers(800.0, -1.0, 0.0)


def test_single_segment_audit_exposes_step6_intermediates() -> None:
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

    assert {
        "percent_followers_at_capacity",
        "percent_followers_at_25_capacity",
        "percent_followers_slope_coefficient_m",
        "percent_followers_power_coefficient_p",
        "percent_followers_source_reference",
        "percent_followers",
    } <= names
