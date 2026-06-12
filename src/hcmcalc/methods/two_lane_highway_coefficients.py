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
class SegmentLengthSpeedCoefficients:
    c0: float
    c1: float
    c2: float
    c3: float


@dataclass(frozen=True)
class HeavyVehicleSpeedCoefficients:
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
    2: HeavyVehicleCoefficients(-0.45036, 0.00814, 0.01543, 0.01358, 0.0, 0.0),
    3: HeavyVehicleCoefficients(-0.29591, 0.00743, 0.0, 0.01246, 0.0, 0.0),
    4: HeavyVehicleCoefficients(-0.40902, 0.00975, 0.00767, -0.18363, 0.00423, 0.0),
    5: HeavyVehicleCoefficients(-0.38360, 0.01074, 0.01945, -0.69848, 0.01069, 0.12700),
}

# HCM Ch. 15 Exhibit 15-13 coefficients for Eq. 15-8, Passing Zone and
# Passing Constrained segments.
SPEED_SLOPE_COEFFICIENTS = {
    1: SpeedSlopeCoefficients(0.0558, 0.0542, 0.3278, 0.1029, 0.0, 0.0),
    2: SpeedSlopeCoefficients(5.7280, -0.0809, 0.7404, 0.0, 0.0, 3.1155),
    3: SpeedSlopeCoefficients(9.3079, -0.1706, 1.1292, 0.0, 0.0, 3.1155),
    4: SpeedSlopeCoefficients(9.0115, -0.1994, 1.8252, 0.0, 0.0, 3.2685),
    5: SpeedSlopeCoefficients(23.9144, -0.6925, 1.9473, 0.0, 0.0, 3.5115),
}

# HCM Ch. 15 Exhibit 15-14 coefficients for Eq. 15-8, Passing Lane segments.
PASSING_LANE_SPEED_SLOPE_BASE_COEFFICIENTS = {
    1: SpeedSlopeCoefficients(-1.1379, 0.0941, 0.0, 0.0, 0.0, 0.0),
    2: SpeedSlopeCoefficients(-2.0688, 0.1053, 0.0, 0.0, 0.0, 0.0),
    3: SpeedSlopeCoefficients(-0.5074, 0.0935, 0.0, 0.0, 0.0, 0.0),
    4: SpeedSlopeCoefficients(8.0354, -0.0860, 0.0, 0.0, 0.0, 4.1900),
    5: SpeedSlopeCoefficients(7.2991, -0.3535, 0.0, 0.0, 0.0, 4.8700),
}

# HCM Ch. 15 Exhibits 15-15 and 15-16 coefficients for Eq. 15-9.
SEGMENT_LENGTH_SPEED_COEFFICIENTS = {
    1: SegmentLengthSpeedCoefficients(0.1029, 0.0, 0.0, 0.0),
    2: SegmentLengthSpeedCoefficients(-13.8036, 0.0, 0.2446, 0.0),
    3: SegmentLengthSpeedCoefficients(-11.9703, 0.0, 0.2542, 0.0),
    4: SegmentLengthSpeedCoefficients(-12.5113, 0.0, 0.2656, 0.0),
    5: SegmentLengthSpeedCoefficients(-14.8961, 0.0, 0.4370, 0.0),
}
PASSING_LANE_SEGMENT_LENGTH_SPEED_COEFFICIENTS = {
    1: SegmentLengthSpeedCoefficients(0.0, 0.2667, 0.0, 0.0),
    2: SegmentLengthSpeedCoefficients(0.0, 0.4479, 0.0, 0.0),
    3: SegmentLengthSpeedCoefficients(0.0, 0.0, 0.0, 0.0),
    4: SegmentLengthSpeedCoefficients(-27.1244, 11.5196, 0.4681, -0.1873),
    5: SegmentLengthSpeedCoefficients(-45.3391, 17.3749, 1.0587, -0.3729),
}

# HCM Ch. 15 Exhibits 15-17 and 15-18 coefficients for Eq. 15-10.
HEAVY_VEHICLE_SPEED_COEFFICIENTS = {
    1: HeavyVehicleSpeedCoefficients(0.0, 0.0, 0.0, 0.0),
    2: HeavyVehicleSpeedCoefficients(-1.7765, 0.0, 0.0392, 0.0),
    3: HeavyVehicleSpeedCoefficients(-3.5550, 0.0, 0.0826, 0.0),
    4: HeavyVehicleSpeedCoefficients(-5.7775, 0.0, 0.1373, 0.0),
    5: HeavyVehicleSpeedCoefficients(-18.2910, 2.3875, 0.4494, -0.0520),
}
PASSING_LANE_HEAVY_VEHICLE_SPEED_COEFFICIENTS = {
    1: HeavyVehicleSpeedCoefficients(0.0, 0.1252, 0.0, 0.0),
    2: HeavyVehicleSpeedCoefficients(0.0, 0.1631, 0.0, 0.0),
    3: HeavyVehicleSpeedCoefficients(0.0, -0.2201, 0.0, 0.0072),
    4: HeavyVehicleSpeedCoefficients(0.0, -0.7506, 0.0, 0.0193),
    5: HeavyVehicleSpeedCoefficients(3.8457, -0.9112, 0.0, 0.0170),
}

# HCM Ch. 15 Exhibit 15-19 coefficients for Eq. 15-11, Passing Zone and
# Passing Constrained segments.
SPEED_POWER_COEFFICIENTS = {
    1: SpeedPowerCoefficients(0.67576, 0.0, 0.0, 0.1206, -0.35919, 0.0, 0.0, 0.0, 0.0),
    2: SpeedPowerCoefficients(
        0.34524, 0.00591, 0.02031, 0.14911, -0.43784, -0.00296, 0.02956, 0.0, 0.41622
    ),
    3: SpeedPowerCoefficients(
        0.17291, 0.00917, 0.05698, 0.27734, -0.61893, -0.00918, 0.09184, 0.0, 0.41622
    ),
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
    2: SpeedPowerCoefficients(
        0.65105, 0.0, 0.34931, 0.0, 0.0, 0.00722, 0.0, -0.00391, 0.0
    ),
    3: SpeedPowerCoefficients(
        0.40117, 0.0, 0.68633, 0.0, 0.0, 0.02350, 0.0, -0.02088, 0.0
    ),
    4: SpeedPowerCoefficients(
        1.13282, -0.00798, 0.35425, 0.0, 0.0, 0.01521, 0.0, -0.00987, 0.0
    ),
    5: SpeedPowerCoefficients(
        1.12077, -0.00550, 0.25431, 0.0, 0.0, 0.01269, 0.0, -0.01053, 0.0
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
    2: PercentFollowersCapacityCoefficients(
        58.21104, 5.73387, -13.66293, -0.66126, 9.08575, -0.00950, -0.03602, 7.14619
    ),
    3: PercentFollowersCapacityCoefficients(
        113.20439, 10.01778, -18.90000, 0.46542, -6.75338, -0.03000, -0.05800, 10.03239
    ),
    4: PercentFollowersCapacityCoefficients(
        58.29978, -0.53611, 7.35076, -0.27046, 4.49850, -0.01100, -0.02968, 8.89680
    ),
    5: PercentFollowersCapacityCoefficients(
        3.32968, -0.84377, 7.08952, -1.32089, 19.98477, -0.01250, -0.02960, 9.99453
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
    2: PercentFollowersCapacityCoefficients(
        12.30096, 9.57465, -30.79427, -1.79448, 25.76436, -0.66350, 1.26039, -0.00323
    ),
    3: PercentFollowersCapacityCoefficients(
        206.07369, -4.29885, 0.00000, 1.96483, -30.32556, -0.75812, 1.06453, -0.00839
    ),
    4: PercentFollowersCapacityCoefficients(
        263.13428, 5.38749, -19.04859, 2.73018, -42.76919, -1.31277, -0.32242, 0.01412
    ),
    5: PercentFollowersCapacityCoefficients(
        126.95629, 5.95754, -19.22229, 0.43238, -7.35636, -1.03017, -2.66026, 0.01389
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
    2: PercentFollowersCapacityCoefficients(
        47.83887, 12.80000, -28.20000, -0.61758, 5.80000, -0.04550, -0.03344, 11.35573
    ),
    3: PercentFollowersCapacityCoefficients(
        125.40000, 19.50000, -34.90000, 0.90672, -16.10000, -0.11000, -0.06200, 14.71136
    ),
    4: PercentFollowersCapacityCoefficients(
        103.13534, 14.68459, -23.72704, 0.66444, -11.95763, -0.10000, 0.00172, 14.70067
    ),
    5: PercentFollowersCapacityCoefficients(
        89.00000, 19.02642, -34.54240, 0.29792, -6.62528, -0.16000, 0.00480, 17.56611
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
    2: PercentFollowersCapacityCoefficients(
        18.37886, 14.71856, -47.78892, -1.43373, 18.32040, -0.13226, 0.77217, -0.00778
    ),
    3: PercentFollowersCapacityCoefficients(
        239.98930, 15.90683, -46.87525, 2.73582, -42.88130, -0.53746, 0.76271, -0.00428
    ),
    4: PercentFollowersCapacityCoefficients(
        223.68435, 10.26908, -35.60830, 2.31877, -38.30034, -0.60275, -0.67758, 0.00117
    ),
    5: PercentFollowersCapacityCoefficients(
        137.37633, 11.00106, -38.89043, 0.78501, -14.88672, -0.72576, -2.49546, 0.00872
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
