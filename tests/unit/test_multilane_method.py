from math import inf, nan

import pytest

from hcmcalc.core import HCMCalcError, UnsupportedScopeError
from hcmcalc.multilane.method import (
    access_point_adjustment,
    adjusted_free_flow_speed,
    demand_flow_rate,
    heavy_vehicle_adjustment_factor,
    lane_width_adjustment,
    level_of_service,
    mean_speed_below_breakpoint,
    multilane_capacity,
    speed_from_flow_rate,
    total_lateral_clearance,
    total_lateral_clearance_adjustment,
    traffic_density,
)


def test_example_4_free_flow_speed_adjustments_and_capacity() -> None:
    assert lane_width_adjustment(12.0) == 0.0
    assert total_lateral_clearance(12.0, "twltl") == 12.0
    assert total_lateral_clearance_adjustment(12.0) == 0.0
    assert total_lateral_clearance_adjustment(11.0) == pytest.approx(0.2)
    assert access_point_adjustment(0.0) == 0.0
    assert access_point_adjustment(10.0) == 2.5
    assert access_point_adjustment(40.0) == 10.0
    assert adjusted_free_flow_speed(52.0, 0.0, 0.0, 0.0, 2.5) == 49.5
    assert multilane_capacity(49.5) == 1990.0
    assert multilane_capacity(52.0) == 2040.0


def test_heavy_vehicle_flow_density_and_los() -> None:
    # Published Example 4 PCE supplied explicitly; it is not selected by the engine.
    pce = 2.24
    hv_factor = heavy_vehicle_adjustment_factor(6.0, pce)
    flow = demand_flow_rate(1500.0, 0.90, 2, hv_factor)
    speed = mean_speed_below_breakpoint(flow, 49.5)
    density = traffic_density(flow, speed)

    assert hv_factor == pytest.approx(0.93, abs=0.01)
    assert flow == pytest.approx(896.0, abs=1.0)
    assert density == pytest.approx(18.1, abs=0.1)
    assert level_of_service(density) == "C"


def test_supported_equation_boundaries() -> None:
    assert heavy_vehicle_adjustment_factor(0.0, 2.24) == 1.0
    assert heavy_vehicle_adjustment_factor(6.0, 2.24) == pytest.approx(
        1.0 / (1.0 + 0.06 * (2.24 - 1.0))
    )
    assert demand_flow_rate(1.0, 1.0, 2, 1.0) == 0.5
    assert mean_speed_below_breakpoint(1400.0, 50.0) == 50.0
    assert traffic_density(1.0, 50.0) == 0.02


@pytest.mark.parametrize(
    ("density", "expected"),
    [
        (10.999, "A"),
        (11.0, "A"),
        (11.001, "B"),
        (17.999, "B"),
        (18.0, "B"),
        (18.001, "C"),
        (25.999, "C"),
        (26.0, "C"),
        (26.001, "D"),
        (34.999, "D"),
        (35.0, "D"),
        (35.001, "E"),
        (44.999, "E"),
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
        adjusted_free_flow_speed(value, 0.0, 0.0, 0.0, 0.0)
    with pytest.raises(HCMCalcError, match="finite"):
        level_of_service(value)


@pytest.mark.parametrize(
    ("args", "message"),
    [
        ((0.0, 1.0, 2, 1.0), "Demand volume"),
        ((-1.0, 1.0, 2, 1.0), "Demand volume"),
        ((1.0, 0.0, 2, 1.0), "Peak hour factor"),
        ((1.0, 1.01, 2, 1.0), "Peak hour factor"),
        ((1.0, 1.0, 0, 1.0), "Lane count"),
        ((1.0, 1.0, 2, 0.0), "Heavy vehicle adjustment factor"),
    ],
)
def test_demand_flow_rate_rejects_invalid_inputs(
    args: tuple[float, float, int, float], message: str
) -> None:
    with pytest.raises(HCMCalcError, match=message):
        demand_flow_rate(*args)


@pytest.mark.parametrize("heavy_vehicle_percent", [-0.1, 100.1])
def test_heavy_vehicle_factor_rejects_invalid_percentage(
    heavy_vehicle_percent: float,
) -> None:
    with pytest.raises(HCMCalcError, match="between 0 and 100"):
        heavy_vehicle_adjustment_factor(heavy_vehicle_percent, 2.24)


def test_adjusted_free_flow_speed_rejects_nonpositive_result() -> None:
    with pytest.raises(HCMCalcError, match="Adjusted FFS"):
        adjusted_free_flow_speed(10.0, 10.0, 0.0, 0.0, 0.0)


def test_speed_flow_branches_are_continuous_and_deterministic() -> None:
    assert speed_from_flow_rate(1400.0, 50.0, 2000.0) == 50.0
    assert speed_from_flow_rate(2000.0, 50.0, 2000.0) == pytest.approx(2000.0 / 45.0)
    assert 2000.0 / 45.0 < speed_from_flow_rate(1700.0, 50.0, 2000.0) < 50.0
    with pytest.raises(UnsupportedScopeError, match="above the breakpoint"):
        mean_speed_below_breakpoint(1400.1, 50.0)
    with pytest.raises(UnsupportedScopeError, match="between 0 and 40"):
        access_point_adjustment(40.1)
