from pathlib import Path

import pytest

from hcmcalc.methods.two_lane_highway_ch15 import (
    TwoLaneHighwayChapter15Method,
    average_speed,
    average_speed_power_coefficient,
    average_speed_slope_coefficient,
    heavy_vehicle_ffs_coefficient,
    length_weighted_average,
    percent_followers,
    percent_followers_at_25_percent_capacity,
    percent_followers_at_capacity,
    percent_followers_power_coefficient,
    percent_followers_slope_coefficient,
    vertical_alignment_class,
)
from hcmcalc.validation import load_yaml_fixture


ROOT = Path(__file__).resolve().parents[2]


def _example_4_result():
    fixture = load_yaml_fixture(ROOT / "references" / "example_inputs.yaml")
    case = next(case for case in fixture["cases"] if case["id"] == "TLH-CH15-004")
    return TwoLaneHighwayChapter15Method().calculate(case["inputs"])


@pytest.mark.parametrize(
    ("length", "grade", "expected_class"),
    [(1.3, 4.0, 4), (1.0, 6.0, 5), (0.5, 6.0, 4), (0.5, -3.0, 1)],
)
def test_example_4_vertical_classes(length, grade, expected_class) -> None:
    assert vertical_alignment_class(length, grade) == expected_class


def test_vertical_classifier_is_not_coupled_to_example_metadata() -> None:
    assert vertical_alignment_class(1.0, -3.0) == 2


def test_example_4_upgrade_and_downgrade_ffs() -> None:
    assert heavy_vehicle_ffs_coefficient(4, 62.7, 1.3, 1500.0) == pytest.approx(
        0.335, abs=0.001
    )
    result = _example_4_result()
    segments = result.outputs["segments"]
    assert segments[0]["free_flow_speed_mph"] == pytest.approx(60.0, abs=0.1)
    assert segments[5]["free_flow_speed_mph"] == pytest.approx(62.4, abs=0.1)


def test_example_4_mountainous_speed_and_percent_followers_formulas() -> None:
    ffs = 60.0227
    speed_m = average_speed_slope_coefficient(4, ffs, 1500.0, 1.3, 8.0)
    speed_p = average_speed_power_coefficient(4, ffs, 1500.0, 1.3, 8.0)
    speed = average_speed(ffs, 1100.0 / 0.90, speed_m, speed_p)
    pf_cap = percent_followers_at_capacity(4, 1.3, ffs, 8.0, 1500.0)
    pf_25 = percent_followers_at_25_percent_capacity(4, 1.3, ffs, 8.0, 1500.0)
    pf_m = percent_followers_slope_coefficient(
        "passing_constrained", pf_cap, pf_25, 1700.0
    )
    pf_p = percent_followers_power_coefficient(
        "passing_constrained", pf_cap, pf_25, 1700.0
    )

    assert speed_m == pytest.approx(10.147, abs=0.02)
    assert speed_p == pytest.approx(0.519, abs=0.001)
    assert speed == pytest.approx(49.2, abs=0.1)
    assert percent_followers(1100.0 / 0.90, pf_m, pf_p) == pytest.approx(
        86.9, abs=0.2
    )


def test_example_4_segment_and_facility_results() -> None:
    result = _example_4_result()
    segments = result.outputs["segments"]
    expected_densities = [22.2, 24.9, 20.2, 21.6, 6.2, 13.2]
    expected_los = ["E", "E", "E", "E", "C", "E"]

    for segment, density, los in zip(segments, expected_densities, expected_los):
        assert segment["follower_density_followers_mi_ln"] == pytest.approx(
            density, abs=0.1
        )
        assert segment["level_of_service"] == los
        assert segment["vertical_direction"] in {"upgrade", "downgrade"}
        assert segment["vertical_lookup_row_range"]
        assert segment["vertical_lookup_column_range"]
        assert "Exhibit 15-11" in segment["vertical_class_source_reference"]
        assert segment["segment_length_applicability_status"] == "within_exhibit_15_10"
        assert segment["segment_length_source_reference"] == "HCM7 Exhibit 15-10"

    assert length_weighted_average(
        list(zip(expected_densities, [1.3, 1.0, 0.5, 1.3, 0.5, 0.5]))
    ) == pytest.approx(20.0, abs=0.1)
    assert result.outputs["facility_follower_density_followers_mi_ln"] == pytest.approx(
        20.0, abs=0.1
    )
    assert result.outputs["facility_level_of_service"] == "E"
    assert result.warnings
