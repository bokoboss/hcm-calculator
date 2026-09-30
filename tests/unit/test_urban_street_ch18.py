from copy import deepcopy

import pytest

from hcmcalc.core import HCMCalcError
from hcmcalc.urban_street_ch18 import (
    UrbanStreetSegmentMethod,
    level_of_service,
    vehicle_proximity_factor,
)


def example_inputs():
    return {
        "segment_length_ft": 1800.0,
        "upstream_intersection_width_ft": 50.0,
        "signal_control_spacing_ft": 1800.0,
        "subject_direction": "eastbound",
        "through_movement_id": "EB_TH",
        "through_lane_count": 2,
        "posted_speed_limit_mph": 35.0,
        "s_calib_mph": 0.0,
        "restrictive_median_proportion": 0.0,
        "curb_proportion": 0.70,
        "parking_proportion": 0.0,
        "subject_side_access_count": 4,
        "opposing_side_access_count": 4,
        "v_m_veh_h": 1150.0,
        "access_point_delays_s_veh": [0.193, 0.194],
        "d_other_s_veh": 0.0,
        "analysis_period_min": 15,
        "control_type": "signalized",
        "demand_balanced": True,
        "demand_adjustments_resolved": True,
        "capacity_effects_resolved": True,
        "spillback_present": False,
        "external_through": {
            "source_class": "qualified_external_signal_analysis",
            "source_tool": "HCM 7 Chapter 30 Example Problem 1",
            "source_method_note": "HCM 7 Chapter 30 Example Problem 1",
            "hcm_edition_note": "HCM 7.0",
            "direction": "eastbound",
            "control_type": "signalized",
            "through_movement_id": "EB_TH",
            "analysis_period_min": 15,
            "scenario_note": "Chapter 30 Example Problem 1",
            "v_th_veh_h": 968.0,
            "c_th_veh_h": 1848.0,
            "d_t_s_veh": 18.310,
        },
    }


def test_chapter_30_example_problem_1_reproduces_reference_values():
    result = UrbanStreetSegmentMethod().calculate(example_inputs())
    out = result.outputs

    assert out["link_length_ft"] == 1750.0
    assert out["s0_mph"] == pytest.approx(42.05, abs=0.005)
    assert out["f_cs_mph"] == pytest.approx(-0.329, abs=0.0005)
    assert out["access_density_per_mi"] == pytest.approx(24.137142857, abs=1e-9)
    assert out["f_a_mph"] == pytest.approx(-0.941, abs=0.0005)
    assert out["f_pk_mph"] == 0.0
    assert out["base_free_flow_speed_mph"] == pytest.approx(40.78, abs=0.005)
    assert out["f_l"] == pytest.approx(0.9644, abs=0.00005)
    assert out["free_flow_speed_mph"] == pytest.approx(39.33, abs=0.005)
    assert out["f_v"] == pytest.approx(1.034, abs=0.0005)
    assert out["f_x"] == 1.0
    assert out["l_1_s"] == 2.0
    assert out["total_access_delay_s_veh"] == pytest.approx(0.387, abs=0.0005)
    assert out["running_time_s"] == pytest.approx(33.54, abs=0.005)
    assert out["running_speed_mph"] == pytest.approx(36.59, abs=0.005)
    assert out["external_through_delay_used_s_veh"] == 18.310
    assert out["total_travel_time_s"] == pytest.approx(51.85, abs=0.005)
    assert out["travel_speed_mph"] == pytest.approx(23.67, abs=0.005)
    assert out["through_v_c"] == pytest.approx(968 / 1848, abs=1e-12)
    assert out["level_of_service"] == "C"
    assert result.method == "urban_street_segment_ch18_v0_1"
    assert all(value.source for value in result.intermediate_values)


def test_midsegment_flow_is_required_and_distinct_from_external_through_flow():
    values = example_inputs()
    original = UrbanStreetSegmentMethod().calculate(values).outputs
    values["v_m_veh_h"] = 968.0
    changed = UrbanStreetSegmentMethod().calculate(values).outputs
    assert changed["f_v"] != original["f_v"]
    assert changed["running_time_s"] != original["running_time_s"]

    values.pop("v_m_veh_h")
    with pytest.raises(HCMCalcError, match="v_m_veh_h"):
        UrbanStreetSegmentMethod().calculate(values)


@pytest.mark.parametrize(
    "v_m,lanes,speed",
    [(10000.0, 1, 40.0), (100.0, 0, 40.0), (100.0, 1, 0.0)],
)
def test_equation_18_6_rejects_nonreal_domain_or_invalid_denominator(v_m, lanes, speed):
    with pytest.raises(HCMCalcError):
        vehicle_proximity_factor(v_m, lanes, speed)


def test_equation_18_6_computes_valid_values_without_clamping():
    assert vehicle_proximity_factor(1150.0, 2, 39.33) == pytest.approx(1.034, abs=0.0005)
    assert vehicle_proximity_factor(52.8 * 2 * 40, 2, 40) == pytest.approx(2.0)


def test_exhibit_18_1_uses_strict_greater_than_and_interpolates_bffs():
    assert level_of_service(32.0, 40.0, 0.5) == "B"
    assert level_of_service(32.000001, 40.0, 0.5) == "A"
    # At BFFS 42 mph, the LOS A threshold is interpolated from 40 and 45 mph columns.
    assert level_of_service(33.6, 42.0, 0.5) == "B"
    assert level_of_service(33.600001, 42.0, 0.5) == "A"


def test_exhibit_18_1_v_c_forcing_rule_and_bffs_domain():
    assert level_of_service(35.0, 40.0, 0.999) == "A"
    assert level_of_service(35.0, 40.0, 1.0) == "A"
    assert level_of_service(40.0, 40.0, 1.000001) == "F"
    for bffs in (24.999, 55.001):
        with pytest.raises(HCMCalcError, match="25.*55"):
            level_of_service(30.0, bffs, 0.5)
    assert level_of_service(21.0, 25.0, 0.5) == "A"
    assert level_of_service(45.0, 55.0, 0.5) == "A"
    with pytest.raises(HCMCalcError, match="25.*55"):
        level_of_service(30.0, 24.0, 1.1)


def test_external_final_through_delay_is_consumed_once():
    first = UrbanStreetSegmentMethod().calculate(example_inputs()).outputs
    changed_inputs = example_inputs()
    changed_inputs["external_through"]["d_t_s_veh"] += 5.0
    second = UrbanStreetSegmentMethod().calculate(changed_inputs).outputs
    assert second["running_time_s"] == first["running_time_s"]
    assert second["total_travel_time_s"] - first["total_travel_time_s"] == 5.0


def test_access_delays_and_d_other_are_explicit_and_added_once():
    base = example_inputs()
    base_out = UrbanStreetSegmentMethod().calculate(base).outputs
    assert base_out["total_access_delay_s_veh"] == pytest.approx(sum([0.193, 0.194]))

    other = deepcopy(base)
    other["d_other_s_veh"] = 2.0
    other_out = UrbanStreetSegmentMethod().calculate(other).outputs
    assert other_out["running_time_s"] - base_out["running_time_s"] == 2.0

    invalid = deepcopy(base)
    invalid["access_point_delays_s_veh"] = [0.193, -0.194]
    with pytest.raises(HCMCalcError, match="at least 0"):
        UrbanStreetSegmentMethod().calculate(invalid)

    invalid = deepcopy(base)
    invalid["access_point_delays_s_veh"] = []
    with pytest.raises(HCMCalcError, match="access point delay"):
        UrbanStreetSegmentMethod().calculate(invalid)

    no_access = deepcopy(base)
    no_access["subject_side_access_count"] = 0
    no_access["opposing_side_access_count"] = 0
    no_access["access_point_delays_s_veh"] = []
    assert UrbanStreetSegmentMethod().calculate(no_access).outputs["total_access_delay_s_veh"] == 0.0

    no_access["access_point_delays_s_veh"] = [0.193]
    with pytest.raises(HCMCalcError, match="must be empty"):
        UrbanStreetSegmentMethod().calculate(no_access)


@pytest.mark.parametrize(
    "field,value",
    [
        ("segment_length_ft", 0.0),
        ("upstream_intersection_width_ft", 1800.0),
        ("through_lane_count", 0),
        ("restrictive_median_proportion", 1.01),
        ("curb_proportion", -0.01),
        ("parking_proportion", 1.01),
        ("posted_speed_limit_mph", 0.0),
        ("signal_control_spacing_ft", 0.0),
        ("d_other_s_veh", -1.0),
    ],
)
def test_invalid_inputs_fail_closed(field, value):
    values = example_inputs()
    values[field] = value
    with pytest.raises(HCMCalcError):
        UrbanStreetSegmentMethod().calculate(values)


@pytest.mark.parametrize(
    "field,value",
    [
        ("control_type", "two_way_stop"),
        ("analysis_period_min", 60),
        ("demand_balanced", False),
        ("demand_adjustments_resolved", False),
        ("capacity_effects_resolved", False),
        ("spillback_present", True),
    ],
)
def test_unsupported_or_unqualified_operational_state_fails_closed(field, value):
    values = example_inputs()
    values[field] = value
    with pytest.raises(HCMCalcError):
        UrbanStreetSegmentMethod().calculate(values)


def test_external_provenance_must_match_subject_direction_and_analysis_period():
    values = example_inputs()
    values["external_through"]["analysis_period_min"] = 60
    with pytest.raises(HCMCalcError, match="period"):
        UrbanStreetSegmentMethod().calculate(values)

    values = example_inputs()
    values["external_through"]["direction"] = "westbound"
    with pytest.raises(HCMCalcError, match="direction"):
        UrbanStreetSegmentMethod().calculate(values)


def test_external_control_type_is_required_and_must_match_signalized_boundary():
    values = example_inputs()
    values["external_through"].pop("control_type")
    with pytest.raises(HCMCalcError, match="control_type"):
        UrbanStreetSegmentMethod().calculate(values)

    values = example_inputs()
    values["external_through"]["control_type"] = "stop_controlled"
    with pytest.raises(HCMCalcError, match="control type"):
        UrbanStreetSegmentMethod().calculate(values)


def test_external_through_movement_id_must_match_segment():
    matching = UrbanStreetSegmentMethod().calculate(example_inputs()).outputs
    assert matching["through_v_c"] == pytest.approx(968 / 1848)

    values = example_inputs()
    values["external_through"]["through_movement_id"] = "EB_LEFT"
    with pytest.raises(HCMCalcError, match="movement"):
        UrbanStreetSegmentMethod().calculate(values)


def test_zero_external_through_demand_is_accepted_and_los_uses_speed():
    values = example_inputs()
    values["external_through"]["v_th_veh_h"] = 0.0

    outputs = UrbanStreetSegmentMethod().calculate(values).outputs

    assert outputs["through_v_c"] == 0.0
    assert outputs["level_of_service"] == "C"


@pytest.mark.parametrize(
    "field,value",
    [
        ("demand_balanced", "yes"),
        ("capacity_effects_resolved", 1),
        ("spillback_present", "no"),
    ],
)
def test_operational_preconditions_must_be_explicit_booleans(field, value):
    values = example_inputs()
    values[field] = value
    with pytest.raises(HCMCalcError, match="boolean"):
        UrbanStreetSegmentMethod().calculate(values)


@pytest.mark.parametrize(
    "field",
    ["subject_side_access_count", "opposing_side_access_count", "access_point_delays_s_veh"],
)
def test_access_counts_and_qualified_delays_are_required(field):
    values = example_inputs()
    values.pop(field)
    with pytest.raises(HCMCalcError, match=field):
        UrbanStreetSegmentMethod().calculate(values)


def test_segment_at_hcm_two_mile_limit_is_supported():
    values = example_inputs()
    values["segment_length_ft"] = 10_560.0
    values["signal_control_spacing_ft"] = 10_560.0

    outputs = UrbanStreetSegmentMethod().calculate(values).outputs

    assert outputs["segment_length_ft"] == 10_560.0
    assert outputs["support_status"] == "supported_bounded_hcm7_signalized_15min"


def test_segment_above_hcm_two_mile_limit_is_rejected():
    values = example_inputs()
    values["segment_length_ft"] = 10_560.001
    values["signal_control_spacing_ft"] = 10_560.001

    with pytest.raises(HCMCalcError, match="2 mi|10,560"):
        UrbanStreetSegmentMethod().calculate(values)
