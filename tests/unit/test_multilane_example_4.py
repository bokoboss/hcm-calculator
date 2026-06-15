from pathlib import Path

import pytest

from hcmcalc.multilane import MultilaneHighwayLOSMethod
from hcmcalc.validation import load_yaml_fixture


ROOT = Path(__file__).resolve().parents[2]


def _case_by_id(document: dict, case_id: str) -> dict:
    return next(case for case in document["cases"] if case["id"] == case_id)


@pytest.mark.parametrize("case_id", ["MLH-CH26-004-EB", "MLH-CH26-004-WB"])
def test_chapter_26_multilane_example_4(case_id: str) -> None:
    inputs_fixture = load_yaml_fixture(
        ROOT / "references" / "multilane_example_inputs.yaml"
    )
    expected_fixture = load_yaml_fixture(
        ROOT / "references" / "multilane_expected_outputs.yaml"
    )
    inputs = _case_by_id(inputs_fixture, case_id)["inputs"]
    expected_case = _case_by_id(expected_fixture, case_id)
    expected = expected_case["expected_outputs"]
    tolerance = expected_case["tolerances"]

    result = MultilaneHighwayLOSMethod().calculate(inputs)
    actual = result.outputs

    assert actual["base_free_flow_speed_mph"] == expected["base_free_flow_speed_mph"]
    assert actual["access_point_adjustment_mph"] == expected["access_point_adjustment_mph"]
    assert actual["adjusted_free_flow_speed_mph"] == expected["adjusted_free_flow_speed_mph"]
    assert actual["capacity_pc_h_ln"] == expected["capacity_pc_h_ln"]
    assert actual["passenger_car_equivalent"] == expected["passenger_car_equivalent"]
    assert actual["heavy_vehicle_adjustment_factor"] == pytest.approx(
        expected["heavy_vehicle_adjustment_factor"],
        abs=tolerance["adjustment_factor_absolute"],
    )
    assert actual["demand_flow_rate_pc_h_ln"] == pytest.approx(
        expected["demand_flow_rate_pc_h_ln"],
        abs=tolerance["flow_rate_pc_h_ln_absolute"],
    )
    assert actual["mean_speed_mph"] == pytest.approx(
        expected["mean_speed_mph"], abs=tolerance["speed_mph_absolute"]
    )
    assert actual["density_pc_mi_ln"] == pytest.approx(
        expected["density_pc_mi_ln"], abs=tolerance["density_pc_mi_ln_absolute"]
    )
    assert actual["level_of_service"] == expected["level_of_service"]
    assert actual["demand_exceeds_capacity"] is False
    assert actual["calculation_type"] == "multilane_basic_segment_v0_1"
    assert actual["support_status"] == "implemented_example_only"
    assert actual["scope_status"] == "supported_exact_example_problem_4"
    assert actual["capacity_check"] == "within_capacity"
    assert actual["speed_used_for_density_mph"] == actual["mean_speed_mph"]
    assert actual["assumptions"] == result.assumptions
    assert actual["warnings"] == result.warnings
    assert actual["unsupported_scope_notes"]
    assert len(result.intermediate_values) >= 18
    assert all(item.source for item in result.intermediate_values)
    assert result.assumptions
    assert result.warnings
    assert actual["source_references"]
