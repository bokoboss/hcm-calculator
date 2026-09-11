"""Independent Phase 9 Basic Freeway engine qualification cases."""

import pytest

from hcmcalc.core import HCMCalcError, UnsupportedScopeError
from hcmcalc.freeway import BasicFreewaySegmentMethod


def _inputs() -> dict:
    return {
        "case_id": "BFW-PHASE9-001",
        "facility_type": "basic_freeway",
        "analysis_type": "basic_segment",
        "direction": "eastbound",
        "number_of_lanes": 3,
        "segment_length_mi": 0.625,
        "demand_volume_veh_h": 3000.0,
        "peak_hour_factor": 0.95,
        "heavy_vehicle_percent": 5.0,
        "truck_mix": "default_30_sut_70_tt",
        "terrain_type": "level",
        "ffs_source": "measured",
        "free_flow_speed_mph": 65.0,
        "base_free_flow_speed_mph": None,
        "lane_width_ft": None,
        "right_side_lateral_clearance_ft": None,
        "total_ramp_density_per_mi": None,
        "speed_adjustment_factor": 1.0,
        "capacity_adjustment_factor": 1.0,
    }


def test_specific_grade_pce_uses_printed_cell_and_auditable_path() -> None:
    values = _inputs() | {
        "terrain_type": "specific_grade",
        "grade_percent": 3.5,
        "truck_mix": "default_30_sut_70_tt",
    }

    outputs = BasicFreewaySegmentMethod().calculate(values).outputs

    # HCM7 Exhibit 12-26: 30/70 SUT/TT, 3.5%, 0.625 mi, 5% trucks = 3.87.
    assert outputs["passenger_car_equivalent"] == pytest.approx(3.87)
    assert outputs["pce_source"] == "internal_hcm7_exhibits_12_26_12_28"
    assert "specific_grade" in outputs["pce_lookup_path"]
    assert outputs["effective_grade_percent"] == 3.5
    assert outputs["heavy_vehicle_adjustment_factor"] == pytest.approx(
        1 / (1 + 0.05 * (3.87 - 1))
    )


def test_estimated_ffs_preserves_base_and_pre_saf_values_separately() -> None:
    values = _inputs() | {
        "ffs_source": "estimated",
        "number_of_lanes": 2,
        "free_flow_speed_mph": None,
        "base_free_flow_speed_mph": 75.4,
        "lane_width_ft": 11.0,
        "right_side_lateral_clearance_ft": 2.0,
        "total_ramp_density_per_mi": 4.0,
    }
    outputs = BasicFreewaySegmentMethod().calculate(values).outputs

    assert outputs["base_free_flow_speed_mph"] == 75.4
    assert outputs["free_flow_speed_before_saf_mph"] == pytest.approx(60.8, abs=0.1)


def test_specific_grade_interpolates_only_numeric_cells() -> None:
    values = _inputs() | {
        "terrain_type": "specific_grade",
        "grade_percent": 2.25,
        "segment_length_mi": 0.5,
        "heavy_vehicle_percent": 3.0,
        "truck_mix": "equal_50_sut_50_tt",
    }
    outputs = BasicFreewaySegmentMethod().calculate(values).outputs

    # Bilinear interpolation of Exhibit 12-27 cells: 2/2.5%, .375/.625 mi,
    # and 2/4% truck share.  The expected value is calculated independently.
    assert outputs["passenger_car_equivalent"] == pytest.approx(3.7325, abs=0.001)


def test_specific_grade_terminal_category_requires_external_override() -> None:
    values = _inputs() | {
        "terrain_type": "specific_grade",
        "grade_percent": 3.5,
        "heavy_vehicle_percent": 20.1,
    }
    with pytest.raises(UnsupportedScopeError, match="external PCE"):
        BasicFreewaySegmentMethod().calculate(values)


def test_external_pce_bypasses_internal_terrain_lookup() -> None:
    values = _inputs() | {
        "terrain_type": "specific_grade",
        "grade_percent": 7.0,
        "segment_length_mi": 2.0,
        "heavy_vehicle_percent": 40.0,
        "passenger_car_equivalent": 4.25,
        "passenger_car_equivalent_provenance": "agency field calibration 2026-06",
    }
    outputs = BasicFreewaySegmentMethod().calculate(values).outputs

    assert outputs["passenger_car_equivalent"] == 4.25
    assert outputs["pce_source"] == "external_user_supplied_override"
    assert "agency field calibration" in outputs["pce_lookup_path"]


def test_driver_population_uses_chapter_26_paired_adjustments_once() -> None:
    values = _inputs() | {
        "driver_population_category": "balanced",
        "speed_adjustment_factor": 0.950,
        "capacity_adjustment_factor": 0.939,
        "speed_adjustment_factor_source": "chapter_26_driver_population",
        "capacity_adjustment_factor_source": "chapter_26_driver_population",
    }
    outputs = BasicFreewaySegmentMethod().calculate(values).outputs

    assert outputs["adjusted_free_flow_speed_mph"] == pytest.approx(61.75)
    assert outputs["capacity_pc_h_ln"] == pytest.approx(2350.0)
    assert outputs["adjusted_capacity_pc_h_ln"] == pytest.approx(2206.65)
    assert outputs["calculation_revision"] == "hcm7_ch12_december_2022_correction"
    assert any(
        "HCM7 Chapter 12 December 2022 correction" in ref
        for ref in outputs["source_references"]
    )
    assert outputs["driver_population_factor"] == 1.0
    assert outputs["driver_population_category"] == "balanced"


def test_driver_population_rejects_swapped_saf_and_caf() -> None:
    values = _inputs() | {
        "driver_population_category": "balanced",
        "speed_adjustment_factor": 0.939,
        "capacity_adjustment_factor": 0.950,
        "speed_adjustment_factor_source": "chapter_26_driver_population",
        "capacity_adjustment_factor_source": "chapter_26_driver_population",
    }
    with pytest.raises(HCMCalcError, match="must match Exhibit 26-9"):
        BasicFreewaySegmentMethod().calculate(values)


def test_saf_changes_speed_not_base_capacity_and_caf_changes_capacity_not_ffs() -> None:
    baseline = BasicFreewaySegmentMethod().calculate(_inputs()).outputs
    saf = BasicFreewaySegmentMethod().calculate(
        _inputs() | {"speed_adjustment_factor": 0.95, "speed_adjustment_factor_source": "project_local_calibration"}
    ).outputs
    caf = BasicFreewaySegmentMethod().calculate(
        _inputs() | {"capacity_adjustment_factor": 0.9, "capacity_adjustment_factor_source": "project_local_calibration"}
    ).outputs

    assert saf["capacity_pc_h_ln"] == baseline["capacity_pc_h_ln"]
    assert saf["capacity_adjustment_factor"] == 1.0
    assert caf["adjusted_free_flow_speed_mph"] == baseline["adjusted_free_flow_speed_mph"]
    assert caf["capacity_pc_h_ln"] == baseline["capacity_pc_h_ln"]
    assert caf["adjusted_capacity_pc_h_ln"] < baseline["adjusted_capacity_pc_h_ln"]


@pytest.mark.parametrize(
    (
        "saf",
        "caf",
        "expected_ffs",
        "expected_capacity",
        "expected_adjusted_capacity",
        "expected_breakpoint",
    ),
    (
        (1.0, 1.0, 65.0, 2350.0, 2350.0, 1400.0),
        (0.95, 1.0, 61.75, 2350.0, 2350.0, 1530.0),
        (1.0, 0.9, 65.0, 2350.0, 2115.0, 1134.0),
        (0.95, 0.939, 61.75, 2350.0, 2206.65, 1349.03313),
    ),
)
def test_saf_caf_matrix_uses_pre_saf_capacity_and_adjusted_breakpoint(
    saf: float,
    caf: float,
    expected_ffs: float,
    expected_capacity: float,
    expected_adjusted_capacity: float,
    expected_breakpoint: float,
) -> None:
    outputs = BasicFreewaySegmentMethod().calculate(
        _inputs()
        | {
            "speed_adjustment_factor": saf,
            "capacity_adjustment_factor": caf,
            "speed_adjustment_factor_source": "project_local_calibration",
            "capacity_adjustment_factor_source": "project_local_calibration",
        }
    ).outputs

    assert outputs["adjusted_free_flow_speed_mph"] == pytest.approx(expected_ffs)
    assert outputs["capacity_pc_h_ln"] == pytest.approx(expected_capacity)
    assert outputs["adjusted_capacity_pc_h_ln"] == pytest.approx(expected_adjusted_capacity)
    assert outputs["breakpoint_flow_rate_pc_h_ln"] == pytest.approx(expected_breakpoint)


def test_corrected_capacity_changes_near_capacity_status_for_same_inputs() -> None:
    case = _inputs() | {
        "demand_volume_veh_h": 5945.0,
        "speed_adjustment_factor": 0.95,
        "capacity_adjustment_factor": 0.939,
        "speed_adjustment_factor_source": "project_local_calibration",
        "capacity_adjustment_factor_source": "project_local_calibration",
    }

    # Independently recompute Eq. 12-9 inputs for the level-terrain PCE = 2.0.
    heavy_vehicle_factor = 1.0 / (
        1.0
        + case["heavy_vehicle_percent"] / 100.0 * (2.0 - 1.0)
    )
    demand_flow = case["demand_volume_veh_h"] / (
        case["peak_hour_factor"] * case["number_of_lanes"] * heavy_vehicle_factor
    )
    old_defective_capacity = (
        2200.0 + 10.0 * (case["free_flow_speed_mph"] * case["speed_adjustment_factor"] - 50.0)
    ) * case["capacity_adjustment_factor"]
    corrected_capacity = (
        2200.0 + 10.0 * (case["free_flow_speed_mph"] - 50.0)
    ) * case["capacity_adjustment_factor"]
    old_status = {
        "demand_exceeds_capacity": demand_flow > old_defective_capacity,
        "level_of_service": "F" if demand_flow > old_defective_capacity else None,
        "speed_available": demand_flow <= old_defective_capacity,
        "density_available": demand_flow <= old_defective_capacity,
    }

    assert demand_flow == pytest.approx(2190.263157894737)
    assert old_defective_capacity == pytest.approx(2176.1325)
    assert corrected_capacity == pytest.approx(2206.65)
    assert old_defective_capacity < demand_flow < corrected_capacity
    assert old_status == {
        "demand_exceeds_capacity": True,
        "level_of_service": "F",
        "speed_available": False,
        "density_available": False,
    }

    outputs = BasicFreewaySegmentMethod().calculate(case).outputs

    assert outputs["demand_flow_rate_pc_h_ln"] == pytest.approx(demand_flow)
    assert outputs["adjusted_capacity_pc_h_ln"] == pytest.approx(corrected_capacity)
    assert outputs["demand_exceeds_capacity"] is False
    assert outputs["mean_speed_mph"] is not None
    assert outputs["density_pc_mi_ln"] is not None
    assert outputs["level_of_service"] != "F"


def test_nonunity_above_capacity_preserves_los_f_without_speed_or_density() -> None:
    outputs = BasicFreewaySegmentMethod().calculate(
        _inputs()
        | {
            "demand_volume_veh_h": 6050.0,
            "speed_adjustment_factor": 0.95,
            "capacity_adjustment_factor": 0.939,
            "speed_adjustment_factor_source": "project_local_calibration",
            "capacity_adjustment_factor_source": "project_local_calibration",
        }
    ).outputs

    assert outputs["demand_flow_rate_pc_h_ln"] > outputs["adjusted_capacity_pc_h_ln"]
    assert outputs["demand_exceeds_capacity"] is True
    assert outputs["level_of_service"] == "F"
    assert outputs["mean_speed_mph"] is None
    assert outputs["density_pc_mi_ln"] is None


@pytest.mark.parametrize("field", ["speed_adjustment_factor", "capacity_adjustment_factor"])
def test_factor_rejects_boolean(field: str) -> None:
    with pytest.raises(HCMCalcError, match="finite"):
        BasicFreewaySegmentMethod().calculate(_inputs() | {field: True})


def test_outputs_are_deterministic_and_contain_phase_9_audit_fields() -> None:
    first = BasicFreewaySegmentMethod().calculate(_inputs()).outputs
    second = BasicFreewaySegmentMethod().calculate(_inputs()).outputs

    assert first == second
    for field in (
        "method_version", "calculation_contract", "input_summary", "ffs_source", "speed_adjustment_factor_source",
        "capacity_adjustment_factor_source", "pce_source", "pce_lookup_path",
        "terrain_grade_classification", "driver_population_category",
        "breakpoint_flow_rate_pc_h_ln", "assumptions", "warnings",
        "unsupported_scope_notes", "source_references",
    ):
        assert field in first
