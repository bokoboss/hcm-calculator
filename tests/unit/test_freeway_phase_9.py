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
    assert outputs["capacity_pc_h_ln"] == pytest.approx(2317.5)
    assert outputs["adjusted_capacity_pc_h_ln"] == pytest.approx(2176.1325)
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

    assert saf["capacity_pc_h_ln"] < baseline["capacity_pc_h_ln"]  # FFS defines base capacity.
    assert saf["capacity_adjustment_factor"] == 1.0
    assert caf["adjusted_free_flow_speed_mph"] == baseline["adjusted_free_flow_speed_mph"]
    assert caf["capacity_pc_h_ln"] == baseline["capacity_pc_h_ln"]
    assert caf["adjusted_capacity_pc_h_ln"] < baseline["adjusted_capacity_pc_h_ln"]


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
