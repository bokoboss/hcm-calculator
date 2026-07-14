"""Phase 3 sequence/context guards for HCM Chapter 15 Step 9."""

import pytest

from hcmcalc.core import HCMCalcError
from hcmcalc.methods.two_lane_highway_ch15 import TwoLaneHighwayChapter15Method, passing_lane_capacity


def _segment(segment_type: str, length: float = 0.5) -> dict[str, object]:
    return {"segment_type": segment_type, "segment_length_mi": length, "posted_speed_mph": 55.0,
            "analysis_direction_volume_veh_h": 800.0, "peak_hour_factor": 0.95,
            "heavy_vehicle_percent": 8.0, "grade_percent": 0.0, "horizontal_alignment": "straight",
            "lane_width_ft": 12.0, "shoulder_width_ft": 6.0, "access_point_density_per_mi": 0.0}


def test_exhibit_15_5_capacity_varies_by_class_and_heavy_vehicles() -> None:
    assert passing_lane_capacity(vertical_class=1, heavy_vehicle_percent=8) == 1500
    assert passing_lane_capacity(vertical_class=5, heavy_vehicle_percent=8) == 1400
    assert passing_lane_capacity(vertical_class=4, heavy_vehicle_percent=22) == 1200


def test_sequence_applies_step9_only_to_explicit_downstream_context() -> None:
    result = TwoLaneHighwayChapter15Method().calculate_sequence([
        {**_segment("passing_constrained"), "passing_lane_role": "none"},
        {**_segment("passing_lane", 0.5), "passing_lane_role": "passing_lane"},
        {**_segment("passing_constrained", 0.5), "passing_lane_role": "downstream_affected"},
    ])
    downstream = result.outputs["segments"][2]
    assert downstream["downstream_adjustment_applied"] is True
    assert downstream["upstream_passing_lane_id"] == 2
    assert downstream["downstream_distance_mi"] == pytest.approx(1.0)


def test_sequence_rejects_missing_or_impossible_context() -> None:
    with pytest.raises(HCMCalcError, match="preceding Passing Lane"):
        TwoLaneHighwayChapter15Method().calculate_sequence([
            {**_segment("passing_constrained"), "passing_lane_role": "downstream_affected"},
        ])
    with pytest.raises(HCMCalcError, match="cannot also be downstream affected"):
        TwoLaneHighwayChapter15Method().calculate_sequence([
            {**_segment("passing_constrained"), "passing_lane_role": "none"},
            {**_segment("passing_lane"), "passing_lane_role": "downstream_affected"},
        ])


def test_second_passing_lane_resets_closest_upstream_context() -> None:
    result = TwoLaneHighwayChapter15Method().calculate_sequence([
        {**_segment("passing_constrained"), "passing_lane_role": "none"},
        {**_segment("passing_lane"), "passing_lane_role": "passing_lane"},
        {**_segment("passing_constrained"), "passing_lane_role": "none"},
        {**_segment("passing_lane"), "passing_lane_role": "passing_lane"},
        {**_segment("passing_constrained"), "passing_lane_role": "downstream_affected"},
    ])
    assert result.outputs["segments"][4]["upstream_passing_lane_id"] == 4
