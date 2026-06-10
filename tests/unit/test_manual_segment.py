import ast
from pathlib import Path

import pytest

from hcmcalc.core import HCMCalcError, MethodNotImplementedError
from hcmcalc.methods.two_lane_highway_ch15 import TwoLaneHighwayChapter15Method
from hcmcalc.ui.manual_segment import run_manual_single_segment


def _manual_values(**overrides):
    values = {
        "segment_type": "passing_constrained",
        "terrain_type": "level",
        "posted_speed_mph": 50.0,
        "segment_length_mi": 0.75,
        "lane_width_ft": 12.0,
        "shoulder_width_ft": 6.0,
        "access_point_density_per_mi": 0.0,
        "analysis_direction_volume_veh_h": 752.0,
        "peak_hour_factor": 0.94,
        "heavy_vehicle_percent": 5.0,
        "grade_percent": 0.0,
        "opposing_direction_volume_veh_h": None,
    }
    values.update(overrides)
    return values


def test_manual_passing_constrained_example_1_equivalent_returns_los_d() -> None:
    result = run_manual_single_segment(_manual_values())

    assert result.outputs["demand_flow_rate_veh_h"] == 800.0
    assert result.outputs["level_of_service"] == "D"
    assert result.outputs["opposing_flow_rate_veh_h"] == 1500.0
    assert result.intermediate_values
    assert result.assumptions


def test_public_single_segment_api_example_1_equivalent_returns_los_d() -> None:
    inputs = {
        key: value
        for key, value in _manual_values().items()
        if key != "terrain_type"
    }
    inputs.update(
        {
            "horizontal_alignment": "straight",
            "horizontal_alignment_subsegments": [],
        }
    )

    result = TwoLaneHighwayChapter15Method().calculate_single_segment(inputs)

    assert result.outputs["level_of_service"] == "D"


def test_manual_adapter_does_not_import_private_engine_helpers() -> None:
    adapter_path = (
        Path(__file__).parents[2] / "src" / "hcmcalc" / "ui" / "manual_segment.py"
    )
    tree = ast.parse(adapter_path.read_text(encoding="utf-8"))
    private_engine_imports = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "hcmcalc.methods.two_lane_highway_ch15"
        for alias in node.names
        if alias.name.startswith("_")
    ]

    assert private_engine_imports == []


def test_manual_passing_zone_requires_opposing_direction_volume() -> None:
    with pytest.raises(HCMCalcError, match="requires opposing_direction_volume"):
        run_manual_single_segment(_manual_values(segment_type="passing_zone"))


def test_manual_passing_zone_with_opposing_direction_volume_returns_result() -> None:
    result = run_manual_single_segment(
        _manual_values(
            segment_type="passing_zone",
            opposing_direction_volume_veh_h=500.0,
        )
    )

    assert result.outputs["segment_type"] == "passing_zone"
    assert result.outputs["opposing_flow_rate_veh_h"] == pytest.approx(500.0 / 0.94)


def test_manual_passing_lane_returns_result_and_scope_warning() -> None:
    result = run_manual_single_segment(
        _manual_values(
            segment_type="passing_lane",
            posted_speed_mph=55.0,
            segment_length_mi=1.5,
            analysis_direction_volume_veh_h=825.0,
            peak_hour_factor=0.95,
            heavy_vehicle_percent=8.0,
        )
    )

    assert result.outputs["segment_type"] == "passing_lane"
    assert result.outputs["level_of_service"]
    assert "downstream passing-lane effects" in result.warnings[0]


def test_manual_mountainous_supported_grade_length_returns_result() -> None:
    result = run_manual_single_segment(
        _manual_values(
            terrain_type="mountainous",
            posted_speed_mph=55.0,
            segment_length_mi=1.3,
            grade_percent=4.0,
            analysis_direction_volume_veh_h=1100.0,
            peak_hour_factor=0.90,
            heavy_vehicle_percent=8.0,
        )
    )

    assert result.outputs["vertical_class"] == 4
    assert result.outputs["level_of_service"] == "E"


def test_manual_mountainous_unsupported_grade_length_is_rejected() -> None:
    with pytest.raises(
        MethodNotImplementedError,
        match="Unsupported mountainous grade/length combination",
    ):
        run_manual_single_segment(
            _manual_values(
                terrain_type="mountainous",
                segment_length_mi=1.0,
                grade_percent=4.0,
            )
        )


def test_manual_passing_lane_rejects_unvalidated_heavy_vehicle_percent() -> None:
    with pytest.raises(MethodNotImplementedError, match="only at 8% heavy vehicles"):
        run_manual_single_segment(
            _manual_values(segment_type="passing_lane", heavy_vehicle_percent=5.0)
        )


def test_manual_passing_lane_rejects_unvalidated_vertical_class() -> None:
    with pytest.raises(MethodNotImplementedError, match="vertical Class 1"):
        run_manual_single_segment(
            _manual_values(
                segment_type="passing_lane",
                terrain_type="mountainous",
                segment_length_mi=1.3,
                grade_percent=4.0,
                heavy_vehicle_percent=8.0,
            )
        )
