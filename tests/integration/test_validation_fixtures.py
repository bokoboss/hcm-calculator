from pathlib import Path

import pytest

from hcmcalc.methods.two_lane_highway_ch15 import TwoLaneHighwayChapter15Method
from hcmcalc.validation import load_yaml_fixture


ROOT = Path(__file__).resolve().parents[2]


def test_example_problem_1_validation_fixtures_load() -> None:
    inputs = load_yaml_fixture(ROOT / "references" / "example_inputs.yaml")
    expected = load_yaml_fixture(ROOT / "references" / "expected_outputs.yaml")

    assert inputs["metadata"]["status"] == "validation_fixture"
    assert expected["metadata"]["status"] == "validation_fixture"
    assert {case["id"] for case in inputs["cases"]} == {
        case["id"] for case in expected["cases"]
    }


def test_example_problem_1_matches_hcm_chapter_26_expected_values() -> None:
    inputs_fixture = load_yaml_fixture(ROOT / "references" / "example_inputs.yaml")
    expected_fixture = load_yaml_fixture(ROOT / "references" / "expected_outputs.yaml")

    case = inputs_fixture["cases"][0]
    expected_case = expected_fixture["cases"][0]
    expected = expected_case["expected_outputs"]
    tolerances = expected_case["tolerances"]

    result = TwoLaneHighwayChapter15Method().calculate(case["inputs"])

    assert result.outputs["demand_flow_rate_veh_h"] == expected["demand_flow_rate_veh_h"]
    assert result.outputs["capacity_veh_h"] == expected["capacity_veh_h"]
    assert result.outputs["demand_capacity_ratio"] < 1.0
    assert result.outputs["vertical_class"] == expected["vertical_class"]
    assert result.outputs["base_free_flow_speed_mph"] == pytest.approx(
        expected["base_free_flow_speed_mph"],
        abs=tolerances["speed_mph_absolute"],
    )
    assert (
        result.outputs["lane_shoulder_adjustment_mph"]
        == expected["lane_shoulder_adjustment_mph"]
    )
    assert (
        result.outputs["access_point_adjustment_mph"]
        == expected["access_point_adjustment_mph"]
    )
    assert result.outputs["free_flow_speed_mph"] == pytest.approx(
        expected["free_flow_speed_mph"],
        abs=tolerances["speed_mph_absolute"],
    )
    assert result.outputs["average_speed_slope_coefficient"] == pytest.approx(
        expected["average_speed_slope_coefficient"],
        abs=0.001,
    )
    assert result.outputs["average_speed_power_coefficient"] == pytest.approx(
        expected["average_speed_power_coefficient"],
        abs=0.0001,
    )
    assert result.outputs["average_speed_mph"] == pytest.approx(
        expected["average_speed_mph"],
        abs=tolerances["speed_mph_absolute"],
    )
    assert result.outputs["percent_followers_at_capacity"] == pytest.approx(
        expected["percent_followers_at_capacity"],
        abs=0.01,
    )
    assert result.outputs["percent_followers_at_25_percent_capacity"] == pytest.approx(
        expected["percent_followers_at_25_percent_capacity"],
        abs=0.01,
    )
    assert result.outputs["percent_followers_slope_coefficient"] == pytest.approx(
        expected["percent_followers_slope_coefficient"],
        abs=0.001,
    )
    assert result.outputs["percent_followers_power_coefficient"] == pytest.approx(
        expected["percent_followers_power_coefficient"],
        abs=0.0001,
    )
    assert result.outputs["percent_followers"] == pytest.approx(
        expected["percent_followers"],
        abs=tolerances["percent_followers_absolute"],
    )
    assert result.outputs["follower_density_followers_mi_ln"] == pytest.approx(
        expected["follower_density_followers_mi_ln"],
        abs=tolerances["follower_density_followers_mi_ln_absolute"],
    )
    assert result.outputs["level_of_service"] == expected["level_of_service"]
    assert len(result.intermediate_values) >= 18


def test_example_problem_2_matches_hcm_chapter_26_expected_values() -> None:
    inputs_fixture = load_yaml_fixture(ROOT / "references" / "example_inputs.yaml")
    expected_fixture = load_yaml_fixture(ROOT / "references" / "expected_outputs.yaml")

    case = _case_by_id(inputs_fixture, "TLH-CH15-002")
    expected_case = _case_by_id(expected_fixture, "TLH-CH15-002")
    expected = expected_case["expected_outputs"]
    tolerances = expected_case["tolerances"]

    result = TwoLaneHighwayChapter15Method().calculate(case["inputs"])

    assert result.outputs["base_free_flow_speed_mph"] == pytest.approx(
        expected["base_free_flow_speed_mph"],
        abs=tolerances["speed_mph_absolute"],
    )
    assert result.outputs["tangent_free_flow_speed_mph"] == pytest.approx(
        expected["tangent_free_flow_speed_mph"],
        abs=tolerances["speed_mph_absolute"],
    )
    assert result.outputs["tangent_average_speed_mph"] == pytest.approx(
        expected["tangent_average_speed_mph"],
        abs=tolerances["speed_mph_absolute"],
    )
    assert result.outputs["adjusted_average_speed_mph"] == pytest.approx(
        expected["adjusted_average_speed_mph"],
        abs=tolerances["speed_mph_absolute"],
    )

    curve_outputs = {
        subsegment["index"]: subsegment
        for subsegment in result.outputs["horizontal_curve_subsegments"]
        if subsegment["subsegment_type"] == "horizontal_curve"
    }
    for expected_subsegment in expected["horizontal_curve_subsegments"]:
        actual = curve_outputs[expected_subsegment["index"]]
        assert actual["base_free_flow_speed_mph"] == pytest.approx(
            expected_subsegment["base_free_flow_speed_mph"],
            abs=tolerances["speed_mph_absolute"],
        )
        assert actual["free_flow_speed_mph"] == pytest.approx(
            expected_subsegment["free_flow_speed_mph"],
            abs=tolerances["speed_mph_absolute"],
        )
        assert actual["speed_coefficient_m"] == pytest.approx(
            expected_subsegment["speed_coefficient_m"],
            abs=tolerances["coefficient_absolute"],
        )
        assert actual["average_speed_mph"] == pytest.approx(
            expected_subsegment["average_speed_mph"],
            abs=tolerances["speed_mph_absolute"],
        )

    assert len(result.intermediate_values) >= 40


def test_example_problem_3_matches_hcm_chapter_26_expected_values() -> None:
    inputs_fixture = load_yaml_fixture(ROOT / "references" / "example_inputs.yaml")
    expected_fixture = load_yaml_fixture(ROOT / "references" / "expected_outputs.yaml")

    case = _case_by_id(inputs_fixture, "TLH-CH15-003")
    expected_case = _case_by_id(expected_fixture, "TLH-CH15-003")
    expected = expected_case["expected_outputs"]
    tolerances = expected_case["tolerances"]

    result = TwoLaneHighwayChapter15Method().calculate(case["inputs"])
    actual_segments = {
        segment["segment_id"]: segment for segment in result.outputs["segments"]
    }

    for expected_segment in expected["segments"]:
        actual = actual_segments[expected_segment["segment_id"]]
        assert actual["segment_type"] == expected_segment["segment_type"]
        assert actual["demand_flow_rate_veh_h"] == pytest.approx(
            expected_segment["demand_flow_rate_veh_h"],
            abs=tolerances["demand_flow_rate_veh_h_absolute"],
        )
        assert actual["capacity_veh_h"] == expected_segment["capacity_veh_h"]
        assert actual["free_flow_speed_mph"] == pytest.approx(
            expected_segment["free_flow_speed_mph"],
            abs=tolerances["speed_mph_absolute"],
        )
        assert actual["average_speed_mph"] == pytest.approx(
            expected_segment["average_speed_mph"],
            abs=tolerances["speed_mph_absolute"],
        )
        assert actual["percent_followers"] == pytest.approx(
            expected_segment["percent_followers"],
            abs=tolerances["percent_followers_absolute"],
        )
        assert actual["follower_density_followers_mi_ln"] == pytest.approx(
            expected_segment["follower_density_followers_mi_ln"],
            abs=tolerances["follower_density_followers_mi_ln_absolute"],
        )
        assert actual["level_of_service"] == expected_segment["level_of_service"]

    segment_2 = actual_segments[2]
    expected_segment_2 = expected["segments"][1]
    assert segment_2["faster_lane_flow_rate_veh_h_ln"] == pytest.approx(
        expected_segment_2["faster_lane_flow_rate_veh_h_ln"],
        abs=tolerances["demand_flow_rate_veh_h_absolute"],
    )
    assert segment_2["slower_lane_flow_rate_veh_h_ln"] == pytest.approx(
        expected_segment_2["slower_lane_flow_rate_veh_h_ln"],
        abs=tolerances["demand_flow_rate_veh_h_absolute"],
    )
    assert segment_2["faster_lane_midpoint_average_speed_mph"] == pytest.approx(
        expected_segment_2["faster_lane_midpoint_average_speed_mph"],
        abs=tolerances["speed_mph_absolute"],
    )
    assert segment_2["slower_lane_midpoint_average_speed_mph"] == pytest.approx(
        expected_segment_2["slower_lane_midpoint_average_speed_mph"],
        abs=tolerances["speed_mph_absolute"],
    )
    assert segment_2["faster_lane_midpoint_percent_followers"] == pytest.approx(
        expected_segment_2["faster_lane_midpoint_percent_followers"],
        abs=tolerances["percent_followers_absolute"],
    )
    assert segment_2["slower_lane_midpoint_percent_followers"] == pytest.approx(
        expected_segment_2["slower_lane_midpoint_percent_followers"],
        abs=tolerances["percent_followers_absolute"],
    )
    assert segment_2["midpoint_follower_density_followers_mi_ln"] == pytest.approx(
        expected_segment_2["midpoint_follower_density_followers_mi_ln"],
        abs=tolerances["follower_density_followers_mi_ln_absolute"],
    )
    assert segment_2["downstream_effective_length_mi"] == pytest.approx(
        expected_segment_2["downstream_effective_length_mi"],
        abs=0.1,
    )

    assert result.outputs["facility_follower_density_followers_mi_ln"] == pytest.approx(
        expected["facility_follower_density_followers_mi_ln"],
        abs=tolerances["follower_density_followers_mi_ln_absolute"],
    )
    assert (
        result.outputs["facility_level_of_service"]
        == expected["facility_level_of_service"]
    )
    assert len(result.intermediate_values) >= 40


def test_example_problem_4_matches_hcm_chapter_26_expected_values() -> None:
    inputs_fixture = load_yaml_fixture(ROOT / "references" / "example_inputs.yaml")
    expected_fixture = load_yaml_fixture(ROOT / "references" / "expected_outputs.yaml")
    case = _case_by_id(inputs_fixture, "TLH-CH15-004")
    expected_case = _case_by_id(expected_fixture, "TLH-CH15-004")
    expected = expected_case["expected_outputs"]
    tolerances = expected_case["tolerances"]

    result = TwoLaneHighwayChapter15Method().calculate(case["inputs"])
    actual_segments = {
        segment["segment_id"]: segment for segment in result.outputs["segments"]
    }
    for expected_segment in expected["segments"]:
        actual = actual_segments[expected_segment["segment_id"]]
        assert actual["vertical_class"] == expected_segment["vertical_class"]
        assert actual["demand_flow_rate_veh_h"] == pytest.approx(
            expected_segment["demand_flow_rate_veh_h"],
            abs=tolerances["demand_flow_rate_veh_h_absolute"],
        )
        assert actual["capacity_veh_h"] == expected_segment["capacity_veh_h"]
        assert actual["free_flow_speed_mph"] == pytest.approx(
            expected_segment["free_flow_speed_mph"],
            abs=tolerances["speed_mph_absolute"],
        )
        assert actual["average_speed_mph"] == pytest.approx(
            expected_segment["average_speed_mph"],
            abs=tolerances["speed_mph_absolute"],
        )
        assert actual["percent_followers"] == pytest.approx(
            expected_segment["percent_followers"],
            abs=tolerances["percent_followers_absolute"],
        )
        assert actual["follower_density_followers_mi_ln"] == pytest.approx(
            expected_segment["follower_density_followers_mi_ln"],
            abs=tolerances["follower_density_followers_mi_ln_absolute"],
        )
        assert actual["level_of_service"] == expected_segment["level_of_service"]

    assert result.outputs["facility_follower_density_followers_mi_ln"] == pytest.approx(
        expected["facility_follower_density_followers_mi_ln"],
        abs=tolerances["follower_density_followers_mi_ln_absolute"],
    )
    assert result.outputs["facility_level_of_service"] == expected["facility_level_of_service"]
    assert result.outputs["segments"][4]["downstream_effective_length_mi"] == pytest.approx(
        4.4, abs=0.1
    )
    assert result.outputs["segments"][5]["percent_followers_improvement_percent"] == pytest.approx(
        18.0, abs=0.1
    )
    assert result.outputs["segments"][5]["speed_improvement_percent"] == pytest.approx(
        2.2, abs=0.1
    )
    assert result.warnings
    assert len(result.intermediate_values) >= 70


def _case_by_id(fixture: dict, case_id: str) -> dict:
    return next(case for case in fixture["cases"] if case["id"] == case_id)
