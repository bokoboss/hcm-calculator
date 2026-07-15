from pathlib import Path

import pytest

from hcmcalc.validation import load_yaml_fixture
from hcmcalc.weaving import WeavingSegmentMethod


ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("case_id", ["WVG-CH27-001", "WVG-CH27-002", "WVG-CH27-003"])
def test_chapter_27_examples_match_independently_transcribed_values(case_id: str) -> None:
    fixture = load_yaml_fixture(ROOT / "references" / "weaving_example_inputs.yaml")
    case = next(item for item in fixture["cases"] if item["id"] == case_id)
    result = WeavingSegmentMethod("hcm_7_0").calculate(case["inputs"])
    actual, expected, tolerance = result.outputs, case["expected"], case["tolerances"]
    for name in ("volume_ratio", "weaving_intensity"):
        assert actual[name] == pytest.approx(expected[name], abs=tolerance["ratio"])
    for name in ("minimum_lane_changes_lc_h", "maximum_weaving_length_ft", "density_governed_capacity_veh_h", "weaving_lane_changes_lc_h", "nonweaving_lane_changes_lc_h", "total_lane_changes_lc_h"):
        assert actual[name] == pytest.approx(expected[name], abs=tolerance["rate"])
    for name in ("weaving_speed_mph", "nonweaving_speed_mph", "mean_speed_mph"):
        assert actual[name] == pytest.approx(expected[name], abs=tolerance["speed"])
    assert actual["density_pc_mi_ln"] == pytest.approx(expected["density_pc_mi_ln"], abs=tolerance["density"])
    assert actual["level_of_service"] == expected["level_of_service"]
    assert actual["method_version"] == "hcm_7_0"
    assert all(item.source for item in result.intermediate_values)


def test_example_3_uses_equation_defined_nonweaving_flow_not_printed_inconsistency() -> None:
    fixture = load_yaml_fixture(ROOT / "references" / "weaving_example_inputs.yaml")
    case = fixture["cases"][2]
    output = WeavingSegmentMethod().calculate(case["inputs"]).outputs
    # The printed 4,995 pc/h is rounded from the source fHV=.82; the engine
    # retains the unrounded Chapter 12 factor and must not use 5,015 pc/h.
    assert 4990.0 < output["nonweaving_flow_pc_h"] < 5000.0
    assert output["nonweaving_lane_changes_lc_h"] < 860.0
