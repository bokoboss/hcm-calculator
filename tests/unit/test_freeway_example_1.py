from pathlib import Path

import pytest

from hcmcalc.freeway import BasicFreewaySegmentMethod
from hcmcalc.validation import load_yaml_fixture


ROOT = Path(__file__).resolve().parents[2]


def _case_by_id(document: dict, case_id: str) -> dict:
    return next(case for case in document["cases"] if case["id"] == case_id)


def test_chapter_26_basic_freeway_example_1() -> None:
    inputs_fixture = load_yaml_fixture(ROOT / "references" / "freeway_example_inputs.yaml")
    expected_fixture = load_yaml_fixture(
        ROOT / "references" / "freeway_expected_outputs.yaml"
    )
    inputs = _case_by_id(inputs_fixture, "BF-CH26-001")["inputs"]
    expected_case = _case_by_id(expected_fixture, "BF-CH26-001")
    expected = expected_case["expected_outputs"]
    tolerance = expected_case["tolerances"]

    result = BasicFreewaySegmentMethod().calculate(inputs)
    actual = result.outputs

    assert actual["lane_width_adjustment_mph"] == expected["lane_width_adjustment_mph"]
    assert actual["right_lateral_clearance_adjustment_mph"] == expected[
        "right_lateral_clearance_adjustment_mph"
    ]
    assert actual["adjusted_free_flow_speed_mph"] == pytest.approx(
        expected["adjusted_free_flow_speed_mph"],
        abs=tolerance["speed_mph_absolute"],
    )
    assert actual["capacity_pc_h_ln"] == pytest.approx(
        expected["capacity_pc_h_ln"],
        abs=tolerance["capacity_pc_h_ln_absolute"],
    )
    assert actual["adjusted_capacity_pc_h_ln"] == pytest.approx(
        expected["adjusted_capacity_pc_h_ln"],
        abs=tolerance["capacity_pc_h_ln_absolute"],
    )
    assert actual["passenger_car_equivalent"] == expected["passenger_car_equivalent"]
    assert actual["heavy_vehicle_adjustment_factor"] == pytest.approx(
        expected["heavy_vehicle_adjustment_factor"],
        abs=tolerance["adjustment_factor_absolute"],
    )
    assert actual["driver_population_factor"] == expected["driver_population_factor"]
    assert actual["demand_flow_rate_pc_h_ln"] == pytest.approx(
        expected["demand_flow_rate_pc_h_ln"],
        abs=tolerance["flow_rate_pc_h_ln_absolute"],
    )
    assert actual["breakpoint_flow_rate_pc_h_ln"] == pytest.approx(
        expected["breakpoint_flow_rate_pc_h_ln"],
        abs=tolerance["flow_rate_pc_h_ln_absolute"],
    )
    assert actual["speed_used_for_density_mph"] == pytest.approx(
        expected["speed_used_for_density_mph"],
        abs=tolerance["speed_mph_absolute"],
    )
    assert actual["density_pc_mi_ln"] == pytest.approx(
        expected["density_pc_mi_ln"],
        abs=tolerance["density_pc_mi_ln_absolute"],
    )
    assert actual["level_of_service"] == expected["level_of_service"]
    assert actual["capacity_check"] == expected["capacity_check"]
    assert actual["demand_exceeds_capacity"] is expected["demand_exceeds_capacity"]
    assert actual["calculation_type"] == "basic_freeway_segment_v0_1"
    assert actual["support_status"] == "chapter_26_example_validated_v0_1"
    assert actual["scope_status"] == "supported_basic_freeway_segment_v0_1"
    assert actual["input_summary"]["case_id"] == "BF-CH26-001"
    assert actual["assumptions"] == result.assumptions
    assert actual["warnings"] == result.warnings
    assert any("Chapter 26" in source for source in actual["source_references"])
    assert any("regular users" in item for item in actual["assumptions"])
    assert actual["unsupported_scope_notes"]
    assert len(result.intermediate_values) >= 21
    assert all(item.source for item in result.intermediate_values)
