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
    assert inputs["cases"][0]["id"] == expected["cases"][0]["id"]


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
    assert result.outputs["base_free_flow_speed_mph"] == expected["base_free_flow_speed_mph"]
    assert result.outputs["free_flow_speed_mph"] == pytest.approx(
        expected["free_flow_speed_mph"],
        abs=tolerances["speed_mph_absolute"],
    )
    assert result.outputs["average_speed_mph"] == pytest.approx(
        expected["average_speed_mph"],
        abs=tolerances["speed_mph_absolute"],
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
    assert len(result.intermediate_values) >= 9
