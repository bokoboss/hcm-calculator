import pytest

from hcmcalc.core import HCMCalcError
from hcmcalc.methods.two_lane_highway_ch15 import TwoLaneHighwayChapter15Method


def segment(segment_id, segment_type="passing_constrained", **overrides):
    value = {
        "segment_id": segment_id, "segment_type": segment_type,
        "segment_length_mi": 0.5, "posted_speed_mph": 55.0,
        "analysis_direction_volume_veh_h": 700.0, "peak_hour_factor": 0.95,
        "heavy_vehicle_percent": 5.0, "grade_percent": 0.0,
        "horizontal_alignment": "straight", "lane_width_ft": 12.0,
        "shoulder_width_ft": 6.0, "access_point_density_per_mi": 0.0,
        "passing_lane_role": "none",
    }
    value.update(overrides)
    return value


def test_general_facility_uses_ordered_ids_and_step_11_length_weighting():
    result = TwoLaneHighwayChapter15Method().calculate_facility({"facility_id": "general", "segments": [segment("north"), segment("south", "passing_zone", opposing_direction_volume_veh_h=400.0, segment_length_mi=1.0), segment("east", segment_length_mi=0.75)]})
    outputs = result.outputs
    assert [row["segment_id"] for row in outputs["segments"]] == ["north", "south", "east"]
    assert outputs["facility_length_mi"] == pytest.approx(2.25)
    assert outputs["step_11_weighting"]["length_denominator_mi"] == pytest.approx(2.25)
    assert outputs["facility_follower_density_followers_mi_ln"] == pytest.approx(sum(row["final_follower_density_followers_mi_ln"] * row["segment_length_mi"] for row in outputs["segments"]) / 2.25)


def test_passing_lane_context_resets_and_only_explicit_rows_adjust():
    values = [segment("enter"), segment("lane1", "passing_lane", passing_lane_role="passing_lane"), segment("affected", passing_lane_role="downstream_affected"), segment("break", passing_lane_role="none"), segment("lane2", "passing_lane", passing_lane_role="passing_lane"), segment("affected2", passing_lane_role="downstream_affected")]
    result = TwoLaneHighwayChapter15Method().calculate_facility({"segments": values})
    rows = {row["segment_id"]: row for row in result.outputs["segments"]}
    assert rows["affected"]["upstream_passing_lane_id"] == "lane1"
    assert rows["affected2"]["upstream_passing_lane_id"] == "lane2"
    assert rows["break"]["final_density_basis"] == "HCM Eq. 15-35 segment density"


@pytest.mark.parametrize("segments", [[], [segment("same"), segment("same")], [segment("affected", passing_lane_role="downstream_affected")], [segment("lane", "passing_lane", passing_lane_role="passing_lane")]])
def test_general_facility_rejects_malformed_context(segments):
    with pytest.raises(HCMCalcError):
        TwoLaneHighwayChapter15Method().calculate_facility({"segments": segments})
