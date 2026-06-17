from math import inf, isfinite, nan

import pytest

from hcmcalc.core import HCMCalcError, UnsupportedScopeError
from hcmcalc.freeway import BasicFreewaySegmentMethod
from hcmcalc.freeway.method import (
    adjusted_capacity_pc_h_ln,
    adjusted_free_flow_speed,
    basic_freeway_capacity,
    breakpoint_flow_rate,
    demand_flow_rate,
    estimated_free_flow_speed,
    general_terrain_passenger_car_equivalent,
    heavy_vehicle_adjustment_factor,
    lane_width_adjustment,
    level_of_service,
    right_lateral_clearance_adjustment,
    speed_from_flow_rate,
    total_ramp_density_adjustment,
    traffic_density,
)


def _estimated_inputs() -> dict:
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


def test_basic_freeway_free_flow_speed_adjustments_and_capacity() -> None:
    assert lane_width_adjustment(12.0) == 0.0
    assert lane_width_adjustment(11.0) == 1.9
    assert lane_width_adjustment(10.0) == 6.6
    assert right_lateral_clearance_adjustment(6.0, 2) == 0.0
    assert right_lateral_clearance_adjustment(3.5, 3) == pytest.approx(1.0)
    assert right_lateral_clearance_adjustment(0.0, 5) == 0.6
    assert total_ramp_density_adjustment(0.0) == 0.0
    assert total_ramp_density_adjustment(1.0) == pytest.approx(3.22)

    ffs = estimated_free_flow_speed(75.4, 0.0, 0.0, 1.0)
    assert ffs == pytest.approx(72.18)
    assert adjusted_free_flow_speed(ffs, 1.0) == pytest.approx(72.18)
    assert basic_freeway_capacity(72.18) == 2400.0
    assert adjusted_capacity_pc_h_ln(2400.0, 0.95) == 2280.0
    assert breakpoint_flow_rate(75.0) == 1000.0
    assert breakpoint_flow_rate(55.0) == 1800.0
    assert breakpoint_flow_rate(75.0, 0.9) == pytest.approx(810.0)


def test_heavy_vehicle_flow_speed_density_and_los() -> None:
    pce = general_terrain_passenger_car_equivalent("level")
    hv_factor = heavy_vehicle_adjustment_factor(5.0, pce)
    flow = demand_flow_rate(4200.0, 0.94, 3, hv_factor)
    ffs = adjusted_free_flow_speed(72.18, 1.0)
    capacity = basic_freeway_capacity(ffs)
    breakpoint = breakpoint_flow_rate(ffs)
    speed = speed_from_flow_rate(flow, ffs, breakpoint, capacity)
    density = traffic_density(flow, speed)

    assert pce == 2.0
    assert hv_factor == pytest.approx(0.95238, abs=0.00001)
    assert flow == pytest.approx(1563.8, abs=0.1)
    assert speed == pytest.approx(69.9, abs=0.1)
    assert density == pytest.approx(22.4, abs=0.1)
    assert level_of_service(density) == "C"


def test_basic_freeway_method_returns_auditable_result() -> None:
    result = BasicFreewaySegmentMethod().calculate(_estimated_inputs())
    outputs = result.outputs

    assert result.method == "hcm7_basic_freeway_segment"
    assert result.facility_type == "basic_freeway"
    assert outputs["calculation_type"] == "basic_freeway_segment_v0_1"
    assert outputs["support_status"] == "supported_basic_freeway_segment_v0_1"
    assert outputs["scope_status"] == "supported_basic_freeway_segment_v0_1"
    assert outputs["input_summary"]["case_id"] == "BFW-FORMULA-001"
    assert outputs["driver_population_factor"] == 1.0
    assert outputs["adjusted_free_flow_speed_mph"] == pytest.approx(72.18)
    assert outputs["capacity_pc_h_ln"] == 2400.0
    assert outputs["demand_flow_rate_pc_h_ln"] == pytest.approx(1563.8, abs=0.1)
    assert outputs["density_pc_mi_ln"] == pytest.approx(22.4, abs=0.1)
    assert outputs["level_of_service"] == "C"
    assert outputs["capacity_check"] == "within_capacity"
    assert outputs["assumptions"] == result.assumptions
    assert outputs["warnings"] == result.warnings
    assert outputs["source_references"]
    assert outputs["unsupported_scope_notes"]
    assert len(result.intermediate_values) >= 20
    assert all(item.source for item in result.intermediate_values)


@pytest.mark.parametrize(
    ("case_id", "updates"),
    [
        (
            "BFW-NONEXAMPLE-MEASURED-LEVEL",
            {
                "ffs_source": "measured",
                "free_flow_speed_mph": 68.0,
                "base_free_flow_speed_mph": None,
                "lane_width_ft": None,
                "right_side_lateral_clearance_ft": None,
                "total_ramp_density_per_mi": None,
                "terrain_type": "level",
                "number_of_lanes": 4,
                "segment_length_mi": 2.2,
                "demand_volume_veh_h": 5600.0,
                "peak_hour_factor": 0.9,
                "heavy_vehicle_percent": 8.0,
            },
        ),
        (
            "BFW-NONEXAMPLE-ESTIMATED-ROLLING",
            {
                "ffs_source": "estimated",
                "free_flow_speed_mph": None,
                "base_free_flow_speed_mph": 75.0,
                "lane_width_ft": 12.0,
                "right_side_lateral_clearance_ft": 4.0,
                "total_ramp_density_per_mi": 2.0,
                "terrain_type": "rolling",
                "number_of_lanes": 3,
                "segment_length_mi": 3.5,
                "demand_volume_veh_h": 3900.0,
                "peak_hour_factor": 0.93,
                "heavy_vehicle_percent": 6.0,
            },
        ),
    ],
)
def test_non_example_basic_freeway_cases_inside_supported_envelope(
    case_id: str, updates: dict
) -> None:
    inputs = _estimated_inputs()
    inputs.update({"case_id": case_id, **updates})

    outputs = BasicFreewaySegmentMethod().calculate(inputs).outputs

    assert outputs["input_summary"]["case_id"] == case_id
    assert outputs["support_status"] == "supported_basic_freeway_segment_v0_1"
    assert outputs["level_of_service"]
    assert isfinite(outputs["density_pc_mi_ln"])
    assert outputs["density_pc_mi_ln"] >= 0
    assert isfinite(outputs["demand_flow_rate_pc_h_ln"])
    assert outputs["demand_flow_rate_pc_h_ln"] > 0
    assert isfinite(outputs["capacity_pc_h_ln"])
    assert outputs["capacity_pc_h_ln"] > 0
    assert isfinite(outputs["adjusted_capacity_pc_h_ln"])
    assert outputs["adjusted_capacity_pc_h_ln"] > 0


def test_measured_ffs_path_omits_estimation_adjustments() -> None:
    inputs = _estimated_inputs()
    inputs.update(
        {
            "ffs_source": "measured",
            "free_flow_speed_mph": 65.0,
            "base_free_flow_speed_mph": None,
            "lane_width_ft": None,
            "right_side_lateral_clearance_ft": None,
            "total_ramp_density_per_mi": None,
        }
    )

    outputs = BasicFreewaySegmentMethod().calculate(inputs).outputs

    assert outputs["base_free_flow_speed_mph"] == 65.0
    assert outputs["lane_width_adjustment_mph"] is None
    assert outputs["right_lateral_clearance_adjustment_mph"] is None
    assert outputs["total_ramp_density_adjustment_mph"] is None
    assert outputs["adjusted_free_flow_speed_mph"] == 65.0


def test_over_capacity_result_is_los_f_with_capacity_warning() -> None:
    inputs = _estimated_inputs()
    inputs["demand_volume_veh_h"] = 9000.0

    outputs = BasicFreewaySegmentMethod().calculate(inputs).outputs

    assert outputs["demand_exceeds_capacity"] is True
    assert outputs["capacity_check"] == "demand_exceeds_capacity"
    assert outputs["level_of_service"] == "F"
    assert outputs["mean_speed_mph"] == pytest.approx(2400.0 / 45.0)
    assert any("exceeds adjusted capacity" in warning for warning in outputs["warnings"])


def test_phf_one_zero_heavy_vehicles_and_minimum_positive_volume_are_valid() -> None:
    inputs = _estimated_inputs()
    inputs.update(
        {
            "demand_volume_veh_h": 1.0,
            "peak_hour_factor": 1.0,
            "heavy_vehicle_percent": 0.0,
        }
    )

    outputs = BasicFreewaySegmentMethod().calculate(inputs).outputs

    assert outputs["heavy_vehicle_adjustment_factor"] == 1.0
    assert outputs["demand_flow_rate_pc_h_ln"] == pytest.approx(1.0 / 3.0)
    assert outputs["level_of_service"] == "A"


def test_capacity_boundary_is_within_capacity_at_capacity_and_exceeded_above() -> None:
    speed = speed_from_flow_rate(2400.0, 75.0, 1000.0, 2400.0)
    density = traffic_density(2400.0, speed)

    assert speed == pytest.approx(2400.0 / 45.0)
    assert density == pytest.approx(45.0)
    assert level_of_service(density, demand_exceeds_capacity=False) == "E"
    assert level_of_service(density, demand_exceeds_capacity=True) == "F"


@pytest.mark.parametrize(
    ("density", "expected"),
    [
        (11.0, "A"),
        (11.001, "B"),
        (18.0, "B"),
        (18.001, "C"),
        (26.0, "C"),
        (26.001, "D"),
        (35.0, "D"),
        (35.001, "E"),
        (45.0, "E"),
        (45.001, "F"),
    ],
)
def test_los_boundaries(density: float, expected: str) -> None:
    assert level_of_service(density) == expected


@pytest.mark.parametrize("value", [nan, inf, -inf])
def test_formula_helpers_reject_non_finite_values(value: float) -> None:
    with pytest.raises(HCMCalcError, match="finite"):
        demand_flow_rate(value, 1.0, 2, 1.0)
    with pytest.raises(HCMCalcError, match="finite"):
        adjusted_free_flow_speed(value, 1.0)
    with pytest.raises(HCMCalcError, match="finite"):
        level_of_service(value)


@pytest.mark.parametrize(
    ("free_flow_speed", "expected_capacity", "expected_breakpoint"),
    [
        (55.0, 2250.0, 1800.0),
        (75.0, 2400.0, 1000.0),
    ],
)
def test_free_flow_speed_boundary_values(
    free_flow_speed: float, expected_capacity: float, expected_breakpoint: float
) -> None:
    assert adjusted_free_flow_speed(free_flow_speed, 1.0) == free_flow_speed
    assert basic_freeway_capacity(free_flow_speed) == expected_capacity
    assert breakpoint_flow_rate(free_flow_speed) == expected_breakpoint


def test_formula_helpers_reject_unimplemented_branches() -> None:
    with pytest.raises(UnsupportedScopeError, match="below 10 ft"):
        lane_width_adjustment(9.9)
    with pytest.raises(UnsupportedScopeError, match="0 to 6"):
        total_ramp_density_adjustment(6.1)
    with pytest.raises(UnsupportedScopeError, match="55 and 75"):
        adjusted_free_flow_speed(54.9, 1.0)
    with pytest.raises(UnsupportedScopeError, match="level and rolling"):
        general_terrain_passenger_car_equivalent("mountainous")
