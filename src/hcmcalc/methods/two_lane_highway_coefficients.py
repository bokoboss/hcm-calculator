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
class SpeedSlopeAuxiliaryCoefficients:
    c0: float
    c1: float
    c2: float
    c3: float
    d0: float
    d1: float
    d2: float
    d3: float


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
    4: HeavyVehicleCoefficients(-0.40902, 0.00975, 0.00767, -0.18363, 0.00423, 0.0),
    5: HeavyVehicleCoefficients(-0.38360, 0.01074, 0.01945, -0.69848, 0.01069, 0.12700),
}

# HCM Ch. 15 Exhibit 15-13 coefficients for Eq. 15-8, Passing Zone and
# Passing Constrained segments.
SPEED_SLOPE_COEFFICIENTS = {
    1: SpeedSlopeCoefficients(0.0558, 0.0542, 0.3278, 0.1029, 0.0, 0.0),
    4: SpeedSlopeCoefficients(9.0115, -0.1994, 1.8252, 0.0, 0.0, 3.2685),
    5: SpeedSlopeCoefficients(23.9144, -0.6925, 1.9473, 0.0, 0.0, 3.5115),
}
SPEED_SLOPE_AUXILIARY_COEFFICIENTS = {
    4: SpeedSlopeAuxiliaryCoefficients(
        -12.5113, 0.0, 0.2656, 0.0, -5.7775, 0.0, 0.1373, 0.0
    ),
    5: SpeedSlopeAuxiliaryCoefficients(
        -14.8961, 0.0, 0.4370, 0.0, -18.2910, 2.3875, 0.4494, -0.0520
    ),
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
    4: SpeedPowerCoefficients(
        0.67689, 0.00534, -0.13037, 0.25699, -0.68465, -0.00709, 0.07087, 0.0, 0.33950
    ),
    5: SpeedPowerCoefficients(
        1.13262, 0.0, -0.26367, 0.18811, -0.64304, -0.00867, 0.08675, 0.0, 0.30590
    ),
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
    4: PercentFollowersCapacityCoefficients(
        58.29978, -0.53611, 7.35076, -0.27046, 4.49850, -0.01100, -0.02968, 8.89680
    ),
    5: PercentFollowersCapacityCoefficients(
        3.32968, -0.84377, 7.08952, -1.32089, 19.98477, -0.01250, -0.02960, 9.99450
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
    4: PercentFollowersCapacityCoefficients(
        103.13534, 14.68459, -23.72704, 0.66444, -11.95763, -0.10000, 0.00172, 14.70074
    ),
    5: PercentFollowersCapacityCoefficients(
        89.00000, 19.02642, -34.54240, 0.29792, -6.62528, -0.16000, 0.00480, 17.56610
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
HORIZONTAL_CURVE_CLASS_SPEED_INTERCEPT = 44.32
HORIZONTAL_CURVE_BFFS_SLOPE = 0.3728
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
