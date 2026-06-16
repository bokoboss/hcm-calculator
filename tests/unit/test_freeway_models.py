import pytest

from hcmcalc.freeway.models import BasicFreewaySegmentInputs


def _base_inputs() -> dict:
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


def test_basic_freeway_inputs_from_mapping_requires_all_fields() -> None:
    with pytest.raises(ValueError, match="facility_type"):
        BasicFreewaySegmentInputs.from_mapping({"case_id": "BFW-FORMULA-001"})


def test_basic_freeway_inputs_from_mapping_parses_required_fields() -> None:
    parsed = BasicFreewaySegmentInputs.from_mapping(_base_inputs())

    assert parsed.case_id == "BFW-FORMULA-001"
    assert parsed.facility_type == "basic_freeway"
    assert parsed.ffs_source == "estimated"
    assert parsed.free_flow_speed_mph is None
