import pytest

from hcmcalc.methods.two_lane_highway_ch15 import (
    OPPOSING_FLOW_EXAMPLE_1_VEH_H,
    PASSING_CONSTRAINED,
    access_point_adjustment,
    average_speed,
    average_speed_power_coefficient,
    average_speed_slope_coefficient,
    base_free_flow_speed,
    demand_flow_rate,
    estimated_free_flow_speed,
    follower_density,
    heavy_vehicle_ffs_coefficient,
    lane_shoulder_adjustment,
    level_of_service,
    passing_constrained_capacity,
    percent_followers,
    percent_followers_at_25_percent_capacity,
    percent_followers_at_capacity,
    percent_followers_power_coefficient,
    percent_followers_slope_coefficient,
    vertical_alignment_class,
)


def test_example_problem_1_formula_level_intermediates() -> None:
    demand = demand_flow_rate(
        analysis_direction_volume_veh_h=752.0,
        peak_hour_factor=0.94,
    )
    capacity = passing_constrained_capacity()
    vertical_class = vertical_alignment_class(
        segment_length_mi=0.75,
        grade_percent=0.0,
    )
    bffs = base_free_flow_speed(posted_speed_mph=50.0)
    f_ls = lane_shoulder_adjustment(lane_width_ft=12.0, shoulder_width_ft=6.0)
    f_a = access_point_adjustment(access_point_density_per_mi=0.0)
    hv_coefficient = heavy_vehicle_ffs_coefficient(
        vertical_class=vertical_class,
        base_free_flow_speed_mph=bffs,
        segment_length_mi=0.75,
        opposing_flow_veh_h=OPPOSING_FLOW_EXAMPLE_1_VEH_H,
    )
    ffs = estimated_free_flow_speed(
        base_free_flow_speed_mph=bffs,
        heavy_vehicle_coefficient=hv_coefficient,
        heavy_vehicle_percent=5.0,
        lane_shoulder_adjustment_mph=f_ls,
        access_point_adjustment_mph=f_a,
    )
    speed_m = average_speed_slope_coefficient(
        vertical_class=vertical_class,
        free_flow_speed_mph=ffs,
        opposing_flow_veh_h=OPPOSING_FLOW_EXAMPLE_1_VEH_H,
        segment_length_mi=0.75,
        heavy_vehicle_percent=5.0,
    )
    speed_p = average_speed_power_coefficient(
        vertical_class=vertical_class,
        free_flow_speed_mph=ffs,
        opposing_flow_veh_h=OPPOSING_FLOW_EXAMPLE_1_VEH_H,
        segment_length_mi=0.75,
        heavy_vehicle_percent=5.0,
    )
    speed = average_speed(
        free_flow_speed_mph=ffs,
        demand_flow_rate_veh_h=demand,
        slope_coefficient=speed_m,
        power_coefficient=speed_p,
    )
    pf_cap = percent_followers_at_capacity(
        vertical_class=vertical_class,
        segment_length_mi=0.75,
        free_flow_speed_mph=ffs,
        heavy_vehicle_percent=5.0,
        opposing_flow_veh_h=OPPOSING_FLOW_EXAMPLE_1_VEH_H,
    )
    pf_25_cap = percent_followers_at_25_percent_capacity(
        vertical_class=vertical_class,
        segment_length_mi=0.75,
        free_flow_speed_mph=ffs,
        heavy_vehicle_percent=5.0,
        opposing_flow_veh_h=OPPOSING_FLOW_EXAMPLE_1_VEH_H,
    )
    pf_m = percent_followers_slope_coefficient(
        segment_type=PASSING_CONSTRAINED,
        percent_followers_capacity=pf_cap,
        percent_followers_25_capacity=pf_25_cap,
        capacity_veh_h=capacity,
    )
    pf_p = percent_followers_power_coefficient(
        segment_type=PASSING_CONSTRAINED,
        percent_followers_capacity=pf_cap,
        percent_followers_25_capacity=pf_25_cap,
        capacity_veh_h=capacity,
    )
    followers = percent_followers(
        demand_flow_rate_veh_h=demand,
        slope_coefficient=pf_m,
        power_coefficient=pf_p,
    )
    density = follower_density(
        demand_flow_rate_veh_h=demand,
        average_speed_mph=speed,
        percent_followers_value=followers,
    )

    assert demand == 800.0
    assert capacity == 1700.0
    assert demand / capacity < 1.0
    assert vertical_class == 1
    assert bffs == pytest.approx(57.0)
    assert f_ls == pytest.approx(0.0)
    assert f_a == pytest.approx(0.0)
    assert ffs == pytest.approx(56.83, abs=0.1)
    assert speed_m == pytest.approx(3.626, abs=0.001)
    assert speed_p == pytest.approx(0.41676, abs=0.0001)
    assert speed == pytest.approx(53.7, abs=0.1)
    assert pf_cap == pytest.approx(86.41, abs=0.01)
    assert pf_25_cap == pytest.approx(50.52, abs=0.01)
    assert pf_m == pytest.approx(-1.337, abs=0.001)
    assert pf_p == pytest.approx(0.7524, abs=0.0001)
    assert followers == pytest.approx(67.7, abs=0.2)
    assert density == pytest.approx(10.1, abs=0.1)
    assert level_of_service(density, posted_speed_mph=50.0) == "D"
