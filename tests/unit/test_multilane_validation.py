from copy import deepcopy
from math import isfinite
from pathlib import Path

import pytest

from hcmcalc.core import HCMCalcError, UnsupportedScopeError
from hcmcalc.multilane import MultilaneHighwayLOSMethod
from hcmcalc.validation import load_yaml_fixture


ROOT = Path(__file__).resolve().parents[2]


def _eastbound_inputs() -> dict:
    fixture = load_yaml_fixture(ROOT / "references" / "multilane_example_inputs.yaml")
    return deepcopy(fixture["cases"][0]["inputs"])


def _assert_bounded_success(inputs: dict) -> None:
    outputs = MultilaneHighwayLOSMethod().calculate(inputs).outputs

    assert outputs["level_of_service"]
    assert isfinite(outputs["density_pc_mi_ln"])
    assert outputs["density_pc_mi_ln"] >= 0
    assert isfinite(outputs["speed_used_for_density_mph"])
    assert outputs["speed_used_for_density_mph"] > 0
    assert isfinite(outputs["demand_flow_rate_pc_h_ln"])
    assert outputs["demand_flow_rate_pc_h_ln"] > 0
    assert isfinite(outputs["capacity_pc_h_ln"])
    assert outputs["capacity_pc_h_ln"] > 0
    assert outputs["capacity_check"] in {"within_capacity", "demand_exceeds_capacity"}
    assert outputs["support_status"] == "bounded_multilane_segment_v0_1"
    assert outputs["scope_status"] == "bounded_multilane_segment_v0_1"


@pytest.mark.parametrize(
    "unsupported_key",
    [
        "basic_freeway",
        "ramp",
        "ramps",
        "merge",
        "diverge",
        "merge_diverge",
        "weaving",
        "managed_lanes",
        "work_zone",
        "reliability_analysis",
        "facility",
        "facility_workflow",
        "corridor",
        "corridor_workflow",
        "driver_population_factor",
        "base_free_flow_speed_mph",
        "adjusted_free_flow_speed_mph",
    ],
)
def test_unsupported_workflows_are_rejected(unsupported_key: str) -> None:
    inputs = _eastbound_inputs()
    inputs[unsupported_key] = True

    with pytest.raises(UnsupportedScopeError):
        MultilaneHighwayLOSMethod().calculate(inputs)


def test_present_but_zero_unsupported_input_is_rejected() -> None:
    inputs = _eastbound_inputs()
    inputs["driver_population_factor"] = 0.0

    with pytest.raises(UnsupportedScopeError, match="driver population"):
        MultilaneHighwayLOSMethod().calculate(inputs)


def test_three_lane_estimated_ffs_uses_six_lane_clearance_table() -> None:
    inputs = _eastbound_inputs()
    inputs["number_of_lanes"] = 3

    assert MultilaneHighwayLOSMethod().calculate(inputs).outputs["total_lateral_clearance_adjustment_mph"] == 0.0


def test_non_finite_and_physically_invalid_inputs_are_rejected() -> None:
    inputs = _eastbound_inputs()
    inputs["demand_volume_veh_h"] = float("nan")
    with pytest.raises(HCMCalcError, match="finite"):
        MultilaneHighwayLOSMethod().calculate(inputs)

    inputs = _eastbound_inputs()
    inputs["peak_hour_factor"] = 0.0
    with pytest.raises(HCMCalcError, match="peak_hour_factor"):
        MultilaneHighwayLOSMethod().calculate(inputs)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("demand_volume_veh_h", 0.0, "demand_volume_veh_h"),
        ("demand_volume_veh_h", -1.0, "demand_volume_veh_h"),
        ("peak_hour_factor", -0.1, "peak_hour_factor"),
        ("peak_hour_factor", 1.01, "peak_hour_factor"),
        ("heavy_vehicle_percent", -0.1, "heavy_vehicle_percent"),
        ("heavy_vehicle_percent", 100.1, "heavy_vehicle_percent"),
        ("number_of_lanes", 0, "number_of_lanes"),
        ("lane_width_ft", 0.0, "lane_width_ft"),
        ("roadside_lateral_clearance_ft", -0.1, "roadside_lateral_clearance_ft"),
        ("posted_speed_limit_mph", 0.0, "posted_speed_limit_mph"),
        ("access_point_density_per_mi", -0.1, "access_point_density_per_mi"),
    ],
)
def test_invalid_physical_inputs_have_clear_errors(
    field: str, value: float, message: str
) -> None:
    inputs = _eastbound_inputs()
    inputs[field] = value

    with pytest.raises(HCMCalcError, match=message):
        MultilaneHighwayLOSMethod().calculate(inputs)


def test_access_density_above_implemented_table_range_is_rejected() -> None:
    inputs = _eastbound_inputs()
    inputs["access_point_density_per_mi"] = 40.1

    with pytest.raises(UnsupportedScopeError, match="40 per mile"):
        MultilaneHighwayLOSMethod().calculate(inputs)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("posted_speed_limit_mph", 50.0),
    ],
)
def test_posted_speed_50_uses_documented_base_ffs_branch(
    field: str, value: float
) -> None:
    inputs = _eastbound_inputs()
    inputs[field] = value

    assert MultilaneHighwayLOSMethod().calculate(inputs).outputs["base_free_flow_speed_mph"] == 55.0


@pytest.mark.parametrize(
    "inputs",
    [
        {
            **_eastbound_inputs(),
            "case_id": "MLH-NONEXAMPLE-MEASURED-LEVEL-001",
            "direction": "northbound",
            "number_of_lanes": 2,
            "segment_length_ft": 5280.0,
            "demand_volume_veh_h": 1800.0,
            "peak_hour_factor": 0.94,
            "heavy_vehicle_percent": 8.0,
            "grade_percent": 0.0,
            "ffs_source": "measured",
            "free_flow_speed_mph": 54.0,
            "passenger_car_equivalent": 2.0,
        },
        {
            **_eastbound_inputs(),
            "case_id": "MLH-NONEXAMPLE-MEASURED-ROLLING-001",
            "direction": "westbound",
            "segment_length_ft": 5280.0,
            "demand_volume_veh_h": 1900.0,
            "peak_hour_factor": 0.88,
            "heavy_vehicle_percent": 14.0,
            "grade_percent": 1.5,
            "ffs_source": "measured",
            "free_flow_speed_mph": 52.0,
            "passenger_car_equivalent": 2.4,
        },
        {
            **_eastbound_inputs(),
            "case_id": "MLH-NONEXAMPLE-ESTIMATED-ADJUSTMENTS-001",
            "demand_volume_veh_h": 1200.0,
            "peak_hour_factor": 0.95,
            "lane_width_ft": 11.0,
            "roadside_lateral_clearance_ft": 4.0,
            "access_point_density_per_mi": 5.0,
            "grade_percent": 0.0,
            "passenger_car_equivalent": 2.2,
        },
        {
            **_eastbound_inputs(),
            "case_id": "MLH-NONEXAMPLE-ESTIMATED-SUPPLIED-PCE-001",
            "segment_length_ft": 5280.0,
            "demand_volume_veh_h": 1100.0,
            "peak_hour_factor": 0.88,
            "heavy_vehicle_percent": 15.0,
            "grade_percent": 0.0,
            "lane_width_ft": 12.0,
            "roadside_lateral_clearance_ft": 3.0,
            "access_point_density_per_mi": 3.0,
            "passenger_car_equivalent": 2.5,
        },
        {
            **_eastbound_inputs(),
            "case_id": "MLH-NONEXAMPLE-NEAR-BREAKPOINT-001",
            "direction": "southbound",
            "number_of_lanes": 2,
            "segment_length_ft": 5280.0,
            "demand_volume_veh_h": 2340.0,
            "peak_hour_factor": 0.92,
            "heavy_vehicle_percent": 10.0,
            "grade_percent": 0.0,
            "ffs_source": "measured",
            "free_flow_speed_mph": 55.0,
            "passenger_car_equivalent": 2.0,
        },
    ],
)
def test_non_example_multilane_segment_cases_succeed(inputs: dict) -> None:
    _assert_bounded_success(inputs)


def test_non_example_near_breakpoint_case_stays_on_supported_branch() -> None:
    inputs = {
        **_eastbound_inputs(),
        "case_id": "MLH-NONEXAMPLE-NEAR-BREAKPOINT-001",
        "direction": "southbound",
        "segment_length_ft": 5280.0,
        "demand_volume_veh_h": 2340.0,
        "peak_hour_factor": 0.92,
        "heavy_vehicle_percent": 10.0,
        "grade_percent": 0.0,
        "ffs_source": "measured",
        "free_flow_speed_mph": 55.0,
        "passenger_car_equivalent": 2.0,
    }

    outputs = MultilaneHighwayLOSMethod().calculate(inputs).outputs

    assert outputs["demand_flow_rate_pc_h_ln"] < 1400.0


def test_measured_ffs_omits_estimated_adjustment_audit_values() -> None:
    inputs = {
        **_eastbound_inputs(),
        "case_id": "MLH-NONEXAMPLE-MEASURED-AUDIT",
        "number_of_lanes": 3,
        "demand_volume_veh_h": 2400.0,
        "peak_hour_factor": 0.92,
        "heavy_vehicle_percent": 12.0,
        "grade_percent": 0.0,
        "ffs_source": "measured",
        "free_flow_speed_mph": 55.0,
        "passenger_car_equivalent": 2.0,
    }

    result = MultilaneHighwayLOSMethod().calculate(inputs)
    intermediate_names = {value.name for value in result.intermediate_values}

    assert "TWLTL supplies" not in " ".join(result.assumptions)
    assert "roadside clearance is capped" not in " ".join(result.assumptions)
    assert "Free-flow speed is measured or user supplied." in result.assumptions
    assert not {
        "lane_width_adjustment_mph",
        "total_lateral_clearance_ft",
        "total_lateral_clearance_adjustment_mph",
        "median_type_adjustment_mph",
        "access_point_adjustment_mph",
    } & intermediate_names


def test_estimated_ffs_audit_includes_used_adjustments_and_supplied_pce() -> None:
    inputs = {
        **_eastbound_inputs(),
        "case_id": "MLH-NONEXAMPLE-ESTIMATED-AUDIT",
        "demand_volume_veh_h": 1200.0,
        "peak_hour_factor": 0.95,
        "heavy_vehicle_percent": 15.0,
        "grade_percent": 0.0,
        "lane_width_ft": 11.0,
        "roadside_lateral_clearance_ft": 4.0,
        "access_point_density_per_mi": 5.0,
        "passenger_car_equivalent": 2.5,
    }

    result = MultilaneHighwayLOSMethod().calculate(inputs)
    intermediate_names = {value.name for value in result.intermediate_values}

    assert {
        "base_free_flow_speed_mph",
        "lane_width_adjustment_mph",
        "total_lateral_clearance_ft",
        "total_lateral_clearance_adjustment_mph",
        "median_type_adjustment_mph",
        "access_point_adjustment_mph",
    } <= intermediate_names
    assert any("Passenger-car equivalent is externally supplied" in item for item in result.assumptions)


@pytest.mark.parametrize(
    "analysis_type",
    [
        "basic_freeway_segment",
        "ramp",
        "merge",
        "diverge",
        "weaving",
        "managed_lane",
        "work_zone",
        "reliability",
        "facility",
        "corridor",
    ],
)
def test_unsupported_analysis_types_are_rejected(analysis_type: str) -> None:
    inputs = _eastbound_inputs()
    inputs["analysis_type"] = analysis_type

    with pytest.raises(UnsupportedScopeError, match="analysis_type"):
        MultilaneHighwayLOSMethod().calculate(inputs)


def test_basic_freeway_facility_type_is_rejected() -> None:
    inputs = _eastbound_inputs()
    inputs["facility_type"] = "basic_freeway"

    with pytest.raises(UnsupportedScopeError, match="Basic Freeway"):
        MultilaneHighwayLOSMethod().calculate(inputs)


def test_non_example_grade_without_supplied_pce_is_rejected() -> None:
    inputs = _eastbound_inputs()
    inputs["case_id"] = "MLH-ARBITRARY-001"
    inputs["grade_percent"] = 0.0
    del inputs["passenger_car_equivalent"]

    with pytest.raises(UnsupportedScopeError, match="PCE lookup"):
        MultilaneHighwayLOSMethod().calculate(inputs)


def test_missing_required_input_is_rejected() -> None:
    inputs = _eastbound_inputs()
    del inputs["median_type"]

    with pytest.raises(HCMCalcError, match="median_type"):
        MultilaneHighwayLOSMethod().calculate(inputs)
