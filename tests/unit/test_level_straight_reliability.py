"""Reliability matrix for the practical level, straight baseline case."""

from dataclasses import asdict
from math import isfinite

import pytest

from hcmcalc.core import HCMCalcError, MethodNotImplementedError
from hcmcalc.ui.audit import build_manual_calculation_audit_record
from hcmcalc.ui.manual_segment import run_manual_single_segment
from hcmcalc.ui.project_io import create_manual_project_json, load_manual_project_json


def _manual_values(unit_system: str = "imperial", **overrides) -> dict:
    if unit_system == "metric":
        values = {
            "unit_system": "metric",
            "posted_speed": 80.0,
            "segment_length": 1.2,
            "lane_width": 3.5,
            "shoulder_width": 1.8,
        }
    else:
        values = {
            "unit_system": "imperial",
            "posted_speed": 50.0,
            "segment_length": 0.75,
            "lane_width": 12.0,
            "shoulder_width": 6.0,
        }
    values.update(
        {
            "segment_type": "passing_constrained",
            "terrain_type": "level",
            "horizontal_alignment": "straight",
            "access_point_density": 0.0,
            "analysis_direction_volume": 752.0,
            "peak_hour_factor": 0.94,
            "heavy_vehicle_percent": 5.0,
            "grade_percent": 0.0,
            "opposing_direction_volume": None,
            "horizontal_alignment_subsegments": [],
        }
    )
    values.update(overrides)
    return values


def _assert_valid_level_straight_result(result) -> None:
    outputs = result.outputs

    assert outputs["level_of_service"]
    assert isfinite(outputs["follower_density_followers_mi_ln"])
    assert outputs["follower_density_followers_mi_ln"] >= 0.0
    assert isfinite(outputs["average_speed_mph"])
    assert outputs["average_speed_mph"] > 0.0
    assert isfinite(outputs["percent_followers"])
    assert 0.0 <= outputs["percent_followers"] <= 100.0
    assert isfinite(outputs["demand_flow_rate_veh_h"])
    assert outputs["demand_flow_rate_veh_h"] >= 0.0
    assert isfinite(outputs["capacity_veh_h"])
    assert outputs["capacity_veh_h"] > 0.0
    assert result.assumptions
    assert result.intermediate_values


@pytest.mark.parametrize(
    "overrides",
    [
        {"analysis_direction_volume": 0.0},
        {"analysis_direction_volume": 752.0},
        {"analysis_direction_volume": 1590.0},
        {"heavy_vehicle_percent": 0.0},
        {"heavy_vehicle_percent": 20.0},
        {"unit_system": "metric"},
    ],
    ids=[
        "low-volume",
        "medium-volume",
        "near-capacity",
        "zero-heavy-vehicles",
        "moderate-heavy-vehicles",
        "metric-input",
    ],
)
def test_passing_constrained_reliability_matrix(overrides: dict) -> None:
    overrides = dict(overrides)
    unit_system = overrides.pop("unit_system", "imperial")

    result = run_manual_single_segment(_manual_values(unit_system, **overrides))

    _assert_valid_level_straight_result(result)
    assert result.outputs["segment_type"] == "passing_constrained"
    assert result.outputs["opposing_flow_rate_veh_h"] == 1500.0
    assert result.warnings == []


@pytest.mark.parametrize(
    ("unit_system", "opposing_volume"),
    [
        ("imperial", 500.0),
        ("imperial", 1.0),
        ("imperial", 1600.0),
        ("metric", 500.0),
    ],
    ids=[
        "valid-opposing-flow-imperial",
        "low-opposing-flow-imperial",
        "high-opposing-flow-imperial",
        "valid-opposing-flow-metric",
    ],
)
def test_passing_zone_reliability_matrix(
    unit_system: str, opposing_volume: float
) -> None:
    result = run_manual_single_segment(
        _manual_values(
            unit_system,
            segment_type="passing_zone",
            opposing_direction_volume=opposing_volume,
        )
    )

    _assert_valid_level_straight_result(result)
    assert result.outputs["segment_type"] == "passing_zone"
    assert result.outputs["opposing_flow_rate_veh_h"] == pytest.approx(
        opposing_volume / 0.94
    )
    assert result.warnings == []


def test_passing_zone_missing_opposing_flow_is_rejected_clearly() -> None:
    with pytest.raises(HCMCalcError, match="requires an opposing-direction volume"):
        run_manual_single_segment(_manual_values(segment_type="passing_zone"))


def test_passing_zone_zero_opposing_flow_is_rejected_clearly() -> None:
    with pytest.raises(
        HCMCalcError, match="opposing-direction volume greater than zero"
    ):
        run_manual_single_segment(
            _manual_values(
                segment_type="passing_zone",
                opposing_direction_volume=0.0,
            )
        )


def test_supported_passing_lane_excludes_facility_effects() -> None:
    result = run_manual_single_segment(
        _manual_values(
            segment_type="passing_lane",
            posted_speed=55.0,
            segment_length=1.5,
            analysis_direction_volume=825.0,
            peak_hour_factor=0.95,
            heavy_vehicle_percent=8.0,
        )
    )

    _assert_valid_level_straight_result(result)
    assert result.outputs["segment_type"] == "passing_lane"
    assert any("downstream passing-lane effects" in warning for warning in result.warnings)
    assert any(
        "does not approximate downstream effects" in item
        for item in result.assumptions
    )
    assert any(
        "No upstream passing lane or downstream facility-wide effects" in item
        for item in result.assumptions
    )


def test_passing_lane_supports_heavy_vehicle_percentage_with_hcm_capacity() -> None:
    result = run_manual_single_segment(
        _manual_values(segment_type="passing_lane", heavy_vehicle_percent=5.0)
    )
    assert result.outputs["passing_lane_total_capacity_veh_h"] == 1500.0


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"segment_length": 0.0}, "Segment length must be greater than zero"),
        ({"segment_length": -0.1}, "Segment length must be greater than zero"),
        ({"posted_speed": 0.0}, "Posted/base speed must be greater than zero"),
        ({"posted_speed": -1.0}, "Posted/base speed must be greater than zero"),
        ({"peak_hour_factor": 0.0}, "Peak hour factor"),
        ({"peak_hour_factor": 1.01}, "Peak hour factor"),
        ({"heavy_vehicle_percent": -0.1}, "between 0 and 100"),
        ({"heavy_vehicle_percent": 100.1}, "between 0 and 100"),
        ({"analysis_direction_volume": -1.0}, "volume cannot be negative"),
        ({"lane_width": 8.9}, "Lane width must be within the supported range"),
        ({"lane_width": 12.1}, "Lane width must be within the supported range"),
        ({"shoulder_width": -0.1}, "Shoulder width must be within the supported range"),
        ({"shoulder_width": 6.1}, "Shoulder width must be within the supported range"),
    ],
)
def test_level_straight_validation_edges_are_engineer_readable(
    overrides: dict, message: str
) -> None:
    with pytest.raises(HCMCalcError, match=message):
        run_manual_single_segment(_manual_values(**overrides))


@pytest.mark.parametrize(
    ("field", "value", "label"),
    [
        ("segment_length", float("nan"), "Segment length"),
        ("posted_speed", float("inf"), "Posted/base speed"),
        ("analysis_direction_volume", float("-inf"), "Analysis-direction volume"),
        ("peak_hour_factor", float("nan"), "Peak hour factor"),
        ("heavy_vehicle_percent", float("inf"), "Heavy-vehicle percentage"),
        ("lane_width", float("nan"), "Lane width"),
        ("shoulder_width", float("inf"), "Shoulder width"),
        ("access_point_density", float("-inf"), "Access-point density"),
    ],
)
def test_level_straight_non_finite_inputs_are_rejected_clearly(
    field: str, value: float, label: str
) -> None:
    with pytest.raises(
        HCMCalcError, match=rf"{label}.*must be a finite numeric value"
    ):
        run_manual_single_segment(_manual_values(**{field: value}))


def test_passing_zone_non_finite_opposing_flow_is_rejected_clearly() -> None:
    with pytest.raises(
        HCMCalcError, match="Opposing-direction volume must be a finite numeric value"
    ):
        run_manual_single_segment(
            _manual_values(
                segment_type="passing_zone",
                opposing_direction_volume=float("nan"),
            )
        )


@pytest.mark.parametrize(
    "values",
    [
        _manual_values(),
        _manual_values(segment_type="passing_zone", opposing_direction_volume=500.0),
        _manual_values(
            segment_type="passing_lane",
            posted_speed=55.0,
            segment_length=1.5,
            analysis_direction_volume=825.0,
            peak_hour_factor=0.95,
            heavy_vehicle_percent=8.0,
        ),
    ],
    ids=["passing-constrained", "passing-zone", "passing-lane"],
)
def test_level_straight_success_audit_contains_complete_context(values: dict) -> None:
    result = run_manual_single_segment(values)

    audit = build_manual_calculation_audit_record(values, result=result)

    assert audit["user_inputs"] == values
    assert audit["normalized_engine_inputs"]
    assert audit["selected_segment_type"] == values["segment_type"]
    assert audit["selected_terrain_type"] == "level"
    assert audit["selected_horizontal_alignment"] == "straight"
    assert audit["outputs"] == result.outputs
    assert audit["intermediate_values"]
    assert audit["assumptions"] == result.assumptions
    assert audit["warnings"] == result.warnings


@pytest.mark.parametrize(
    "values",
    [
        _manual_values(),
        _manual_values(segment_type="passing_zone", opposing_direction_volume=500.0),
        _manual_values(
            segment_type="passing_lane",
            posted_speed=55.0,
            segment_length=1.5,
            analysis_direction_volume=825.0,
            peak_hour_factor=0.95,
            heavy_vehicle_percent=8.0,
        ),
    ],
    ids=["passing-constrained", "passing-zone", "passing-lane"],
)
def test_level_straight_project_json_round_trip_preserves_runnable_case(
    values: dict,
) -> None:
    result = run_manual_single_segment(values)
    audit = build_manual_calculation_audit_record(values, result=result)
    project_json = create_manual_project_json(
        values,
        result=asdict(result),
        audit_record=audit,
    )

    loaded = load_manual_project_json(project_json)
    restored_result = run_manual_single_segment(loaded["manual_inputs"])

    assert loaded["manual_inputs"] == values
    assert loaded["normalized_engine_inputs"] == audit["normalized_engine_inputs"]
    assert restored_result.outputs == result.outputs
