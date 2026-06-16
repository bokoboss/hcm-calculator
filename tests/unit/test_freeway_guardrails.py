import pytest

from hcmcalc.core import UnsupportedScopeError
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
    "unsupported_key",
    [
        "multilane_highway",
        "multilane",
        "ramp",
        "ramps",
        "merge",
        "diverge",
        "merge_diverge",
        "weaving",
        "managed_lane",
        "managed_lanes",
        "work_zone",
        "work_zones",
        "reliability",
        "reliability_analysis",
        "facility",
        "facility_workflow",
        "corridor",
        "corridor_workflow",
    ],
)
def test_unsupported_workflows_are_rejected(unsupported_key: str) -> None:
    inputs = _inputs()
    inputs[unsupported_key] = True

    with pytest.raises(UnsupportedScopeError):
        BasicFreewaySegmentMethod().calculate(inputs)


@pytest.mark.parametrize(
    "unsupported_key",
    [
        "access_point_density_per_mi",
        "median_type",
        "total_lateral_clearance_ft",
        "left_side_lateral_clearance_ft",
        "grade_percent",
    ],
)
def test_adjacent_methodology_inputs_are_rejected_even_when_zero(
    unsupported_key: str,
) -> None:
    inputs = _inputs()
    inputs[unsupported_key] = 0.0

    with pytest.raises(UnsupportedScopeError):
        BasicFreewaySegmentMethod().calculate(inputs)


def test_basic_freeway_result_declares_no_ui_save_load_or_export_support() -> None:
    outputs = BasicFreewaySegmentMethod().calculate(_inputs()).outputs

    assert any("No UI" in note for note in outputs["unsupported_scope_notes"])
    assert any("No Multilane" in note for note in outputs["unsupported_scope_notes"])
