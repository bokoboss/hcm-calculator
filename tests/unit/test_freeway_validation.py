import pytest

from hcmcalc.core import HCMCalcError, UnsupportedScopeError
from hcmcalc.freeway import BasicFreewaySegmentMethod


def _inputs() -> dict:
    return {
        "case_id": "BFW-FORMULA-001",
        "facility_type": "basic_freeway",
        "analysis_type": "basic_segment",
        "direction": "eastbound",
        "number_of_lanes": 3,
        "segment_length_mi": 1.0,
        "demand_volume_veh_h": 4200.0,
        "peak_hour_factor": 0.94,
        "heavy_vehicle_percent": 5.0,
        "truck_mix": "default_30_sut_70_tt",
        "terrain_type": "level",
        "ffs_source": "estimated",
        "free_flow_speed_mph": None,
        "base_free_flow_speed_mph": 75.4,
        "lane_width_ft": 12.0,
        "right_side_lateral_clearance_ft": 6.0,
        "total_ramp_density_per_mi": 1.0,
        "speed_adjustment_factor": 1.0,
        "capacity_adjustment_factor": 1.0,
    }


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("demand_volume_veh_h", 0.0, "demand_volume_veh_h"),
        ("demand_volume_veh_h", -1.0, "demand_volume_veh_h"),
        ("peak_hour_factor", 0.0, "peak_hour_factor"),
        ("peak_hour_factor", 1.01, "peak_hour_factor"),
        ("heavy_vehicle_percent", -0.1, "heavy_vehicle_percent"),
        ("heavy_vehicle_percent", 100.1, "heavy_vehicle_percent"),
        ("segment_length_mi", 0.0, "segment_length_mi"),
        ("right_side_lateral_clearance_ft", -0.1, "right_side_lateral_clearance_ft"),
        ("speed_adjustment_factor", 0.0, "speed_adjustment_factor"),
        ("capacity_adjustment_factor", 0.0, "capacity_adjustment_factor"),
    ],
)
def test_invalid_physical_inputs_have_clear_errors(
    field: str, value: float, message: str
) -> None:
    inputs = _inputs()
    inputs[field] = value

    with pytest.raises(HCMCalcError, match=message):
        BasicFreewaySegmentMethod().calculate(inputs)


def test_non_finite_input_is_rejected() -> None:
    inputs = _inputs()
    inputs["demand_volume_veh_h"] = float("nan")

    with pytest.raises(HCMCalcError, match="finite"):
        BasicFreewaySegmentMethod().calculate(inputs)


def test_non_finite_optional_input_is_rejected() -> None:
    inputs = _inputs()
    inputs["base_free_flow_speed_mph"] = float("inf")

    with pytest.raises(HCMCalcError, match="finite"):
        BasicFreewaySegmentMethod().calculate(inputs)


def test_missing_required_input_is_rejected() -> None:
    inputs = _inputs()
    del inputs["terrain_type"]

    with pytest.raises(HCMCalcError, match="terrain_type"):
        BasicFreewaySegmentMethod().calculate(inputs)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("number_of_lanes", 1, "at least two lanes"),
        ("facility_type", "multilane_highway", "basic_freeway"),
        ("analysis_type", "facility", "basic segment"),
        ("truck_mix", "custom", "30% SUT / 70% TT"),
        ("terrain_type", "specific_grade", "specific grades"),
        ("ffs_source", "posted_speed", "measured"),
        ("lane_width_ft", 9.9, "lane widths below 10 ft"),
        ("right_side_lateral_clearance_ft", 10.1, "0 to 10 ft"),
        ("total_ramp_density_per_mi", 6.1, "0 to 6 ramps/mi"),
    ],
)
def test_supported_scope_boundaries_are_enforced(
    field: str, value: float | str, message: str
) -> None:
    inputs = _inputs()
    inputs[field] = value

    with pytest.raises(UnsupportedScopeError, match=message):
        BasicFreewaySegmentMethod().calculate(inputs)


def test_estimated_ffs_requires_estimation_fields() -> None:
    inputs = _inputs()
    inputs["lane_width_ft"] = None

    with pytest.raises(HCMCalcError, match="lane_width_ft"):
        BasicFreewaySegmentMethod().calculate(inputs)


def test_measured_ffs_rejects_estimation_fields() -> None:
    inputs = _inputs()
    inputs["ffs_source"] = "measured"
    inputs["free_flow_speed_mph"] = 65.0

    with pytest.raises(HCMCalcError, match="Measured FFS"):
        BasicFreewaySegmentMethod().calculate(inputs)


def test_measured_ffs_requires_measured_speed() -> None:
    inputs = _inputs()
    inputs.update(
        {
            "ffs_source": "measured",
            "free_flow_speed_mph": None,
            "base_free_flow_speed_mph": None,
            "lane_width_ft": None,
            "right_side_lateral_clearance_ft": None,
            "total_ramp_density_per_mi": None,
        }
    )

    with pytest.raises(HCMCalcError, match="free_flow_speed_mph"):
        BasicFreewaySegmentMethod().calculate(inputs)
