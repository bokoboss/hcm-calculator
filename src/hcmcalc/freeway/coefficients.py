"""Reference-backed constants for HCM7 Chapter 12 Basic Freeway Segments."""

FREEWAY_MIN_FFS_MPH = 55.0
FREEWAY_MAX_FFS_MPH = 75.0
FREEWAY_MAX_CAPACITY_PC_H_LN = 2400.0
FREEWAY_DENSITY_AT_CAPACITY_PC_MI_LN = 45.0
FREEWAY_SPEED_FLOW_EXPONENT = 2.0

LANE_WIDTH_REDUCTIONS_MPH = {
    "at_least_12": 0.0,
    "at_least_11_less_than_12": 1.9,
    "at_least_10_less_than_11": 6.6,
}

RIGHT_LATERAL_CLEARANCE_REDUCTIONS_MPH = {
    2: {
        6.0: 0.0,
        5.0: 0.6,
        4.0: 1.2,
        3.0: 1.8,
        2.0: 2.4,
        1.0: 3.0,
        0.0: 3.6,
    },
    3: {
        6.0: 0.0,
        5.0: 0.4,
        4.0: 0.8,
        3.0: 1.2,
        2.0: 1.6,
        1.0: 2.0,
        0.0: 2.4,
    },
    4: {
        6.0: 0.0,
        5.0: 0.2,
        4.0: 0.4,
        3.0: 0.6,
        2.0: 0.8,
        1.0: 1.0,
        0.0: 1.2,
    },
    5: {
        6.0: 0.0,
        5.0: 0.1,
        4.0: 0.2,
        3.0: 0.3,
        2.0: 0.4,
        1.0: 0.5,
        0.0: 0.6,
    },
}

GENERAL_TERRAIN_PCE = {
    "level": 2.0,
    "rolling": 3.0,
}

LOS_DENSITY_UPPER_BOUNDS = (
    ("A", 11.0),
    ("B", 18.0),
    ("C", 26.0),
    ("D", 35.0),
    ("E", 45.0),
)
