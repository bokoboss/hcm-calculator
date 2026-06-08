"""Coefficient tables for HCM 7th Edition Chapter 15 two-lane highways."""

from dataclasses import dataclass

from hcmcalc.methods.two_lane_highway_models import (
    PASSING_CONSTRAINED,
    PASSING_LANE,
    PASSING_ZONE,
)


@dataclass(frozen=True)
class HeavyVehicleCoefficients:
    a0: float
    a1: float
    a2: float
    a3: float
    a4: float
    a5: float


@dataclass(frozen=True)
class SpeedSlopeCoefficients:
    b0: float
    b1: float
    b2: float
    b3: float
    b4: float
    b5: float


@dataclass(frozen=True)
class SpeedPowerCoefficients:
    f0: float
    f1: float
    f2: float
    f3: float
    f4: float
    f5: float
    f6: float
    f7: float
    f8: float


@dataclass(frozen=True)
class PercentFollowersCapacityCoefficients:
    c0: float
    c1: float
    c2: float
    c3: float
    c4: float
    c5: float
    c6: float
    c7: float


@dataclass(frozen=True)
class PercentFollowersSlopeCoefficients:
    d1: float
    d2: float


@dataclass(frozen=True)
class PercentFollowersPowerCoefficients:
    e0: float
    e1: float
    e2: float
    e3: float
    e4: float


# HCM Ch. 15 Exhibit 15-12 coefficients for Eq. 15-4.
HEAVY_VEHICLE_COEFFICIENTS = {
    1: HeavyVehicleCoefficients(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
}

# HCM Ch. 15 Exhibit 15-13 coefficients for Eq. 15-8, Passing Zone and
# Passing Constrained segments.
SPEED_SLOPE_COEFFICIENTS = {
    1: SpeedSlopeCoefficients(0.0558, 0.0542, 0.3278, 0.1029, 0.0, 0.0),
}

# HCM Ch. 15 Exhibits 15-14, 15-16, and 15-18 coefficients for the
# Example Problem 3 level-terrain Passing Lane speed path.
PASSING_LANE_SPEED_SLOPE_BASE_COEFFICIENTS = {
    1: SpeedSlopeCoefficients(-1.138, 0.094, 0.0, 0.0, 0.0, 0.0),
}
PASSING_LANE_SPEED_SLOPE_B3_C1 = {1: 0.2667}
PASSING_LANE_SPEED_SLOPE_B4_D1 = {1: 0.1252}

# HCM Ch. 15 Exhibit 15-19 coefficients for Eq. 15-11, Passing Zone and
# Passing Constrained segments.
SPEED_POWER_COEFFICIENTS = {
    1: SpeedPowerCoefficients(0.67576, 0.0, 0.0, 0.1206, -0.35919, 0.0, 0.0, 0.0, 0.0),
}

# HCM Ch. 15 Exhibit 15-20 coefficients for Passing Lane segments.
PASSING_LANE_SPEED_POWER_COEFFICIENTS = {
    1: SpeedPowerCoefficients(
        0.91793,
        -0.00557,
        0.36862,
        0.0,
        0.0,
        0.00611,
        0.0,
        -0.00419,
        0.0,
    ),
}

# HCM Ch. 15 Exhibit 15-24 coefficients for Eq. 15-18.
PF_CAPACITY_COEFFICIENTS = {
    1: PercentFollowersCapacityCoefficients(
        37.6808,
        3.05089,
        -7.90866,
        -0.94321,
        13.64266,
        -0.00050,
        -0.05500,
        7.13758,
    ),
}

# HCM Ch. 15 Exhibit 15-25 coefficients for Passing Lane segments.
PASSING_LANE_PF_CAPACITY_COEFFICIENTS = {
    1: PercentFollowersCapacityCoefficients(
        61.73075,
        6.73922,
        -23.68853,
        -0.84126,
        11.44533,
        -1.05124,
        1.50390,
        0.00491,
    ),
}

# HCM Ch. 15 Exhibit 15-26 coefficients for Eq. 15-20.
PF_25_CAPACITY_COEFFICIENTS = {
    1: PercentFollowersCapacityCoefficients(
        18.01780,
        10.00000,
        -21.60000,
        -0.97853,
        12.05214,
        -0.00750,
        -0.06700,
        11.60405,
    ),
}

# HCM Ch. 15 Exhibit 15-27 coefficients for Passing Lane segments.
PASSING_LANE_PF_25_CAPACITY_COEFFICIENTS = {
    1: PercentFollowersCapacityCoefficients(
        80.37105,
        14.44997,
        -46.41831,
        -0.23367,
        0.84914,
        -0.56747,
        0.89427,
        0.00119,
    ),
}

# HCM Ch. 15 Exhibit 15-28 coefficients for Eq. 15-22.
PF_SLOPE_COEFFICIENTS = {
    PASSING_CONSTRAINED: PercentFollowersSlopeCoefficients(-0.29764, -0.71917),
    PASSING_ZONE: PercentFollowersSlopeCoefficients(-0.29764, -0.71917),
    PASSING_LANE: PercentFollowersSlopeCoefficients(-0.15808, -0.83732),
}

# HCM Ch. 15 Exhibit 15-29 coefficients for Eq. 15-23.
PF_POWER_COEFFICIENTS = {
    PASSING_CONSTRAINED: PercentFollowersPowerCoefficients(
        0.81165,
        0.3792,
        -0.49524,
        -2.11289,
        2.41146,
    ),
    PASSING_ZONE: PercentFollowersPowerCoefficients(
        0.81165,
        0.3792,
        -0.49524,
        -2.11289,
        2.41146,
    ),
    PASSING_LANE: PercentFollowersPowerCoefficients(
        -1.63246,
        1.64960,
        -4.45823,
        -4.89119,
        10.33057,
    ),
}

# HCM Eq. 15-14 horizontal curve base free-flow speed constants for the
# horizontal classes represented in Chapter 26 Example Problem 2.
HORIZONTAL_CURVE_CLASS_SPEED_INTERCEPT = 65.5696
HORIZONTAL_CURVE_CLASS_SPEED_SLOPE = 6.868

# HCM Eq. 15-13 heavy-vehicle adjustment coefficient for horizontal curves.
HORIZONTAL_CURVE_HEAVY_VEHICLE_COEFFICIENT = 0.0255

# HCM Eq. 15-15 curve speed coefficients by horizontal class.
HORIZONTAL_CURVE_SPEED_COEFFICIENTS = {
    1: 2.8036,
    2: 1.4905,
    3: 0.9145,
    4: 0.4081,
    5: 0.2770,
}
