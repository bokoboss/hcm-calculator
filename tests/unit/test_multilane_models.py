import pytest

from hcmcalc.multilane.models import MultilaneBasicSegmentInputs


def test_multilane_model_requires_explicit_fields() -> None:
    with pytest.raises(ValueError, match="requires"):
        MultilaneBasicSegmentInputs.from_mapping({"case_id": "MLH-CH26-004-EB"})


def test_multilane_model_preserves_typed_example_inputs() -> None:
    values = {
        "case_id": "MLH-CH26-004-EB",
        "facility_type": "multilane_highway",
        "analysis_type": "basic_segment",
        "direction": "eastbound",
        "number_of_lanes": 2,
        "segment_length_ft": 6600.0,
        "demand_volume_veh_h": 1500.0,
        "peak_hour_factor": 0.90,
        "heavy_vehicle_percent": 6.0,
        "truck_mix": "default_30_sut_70_tt",
        "grade_percent": -3.5,
        "posted_speed_limit_mph": 45.0,
        "lane_width_ft": 12.0,
        "roadside_lateral_clearance_ft": 12.0,
        "median_type": "twltl",
        "access_point_density_per_mi": 10.0,
    }

    parsed = MultilaneBasicSegmentInputs.from_mapping(values)

    assert parsed.direction == "eastbound"
    assert parsed.number_of_lanes == 2
    assert parsed.median_type == "twltl"
