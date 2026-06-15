from copy import deepcopy
from pathlib import Path

import pytest

from hcmcalc.core import HCMCalcError, UnsupportedScopeError
from hcmcalc.multilane import MultilaneHighwayLOSMethod
from hcmcalc.validation import load_yaml_fixture


ROOT = Path(__file__).resolve().parents[2]


def _eastbound_inputs() -> dict:
    fixture = load_yaml_fixture(ROOT / "references" / "multilane_example_inputs.yaml")
    return deepcopy(fixture["cases"][0]["inputs"])


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
        "free_flow_speed_mph",
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


def test_unsupported_lane_count_is_rejected() -> None:
    inputs = _eastbound_inputs()
    inputs["number_of_lanes"] = 3

    with pytest.raises(UnsupportedScopeError, match="number_of_lanes"):
        MultilaneHighwayLOSMethod().calculate(inputs)


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
        ("number_of_lanes", 3),
        ("peak_hour_factor", 1.0),
        ("heavy_vehicle_percent", 0.0),
        ("demand_volume_veh_h", 1.0),
        ("posted_speed_limit_mph", 50.0),
        ("lane_width_ft", 11.0),
        ("roadside_lateral_clearance_ft", 6.0),
    ],
)
def test_valid_but_unvalidated_multilane_inputs_are_rejected_as_unsupported(
    field: str, value: float
) -> None:
    inputs = _eastbound_inputs()
    inputs[field] = value

    with pytest.raises(UnsupportedScopeError, match=field):
        MultilaneHighwayLOSMethod().calculate(inputs)


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


def test_arbitrary_case_id_is_rejected() -> None:
    inputs = _eastbound_inputs()
    inputs["case_id"] = "MLH-ARBITRARY-001"

    with pytest.raises(UnsupportedScopeError, match="eastbound and westbound"):
        MultilaneHighwayLOSMethod().calculate(inputs)


def test_missing_required_input_is_rejected() -> None:
    inputs = _eastbound_inputs()
    del inputs["median_type"]

    with pytest.raises(HCMCalcError, match="median_type"):
        MultilaneHighwayLOSMethod().calculate(inputs)
