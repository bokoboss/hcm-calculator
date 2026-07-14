"""Reference-backed constants for HCM7 Multilane Highway Segments."""

MULTILANE_BREAKPOINT_PC_H_LN = 1400.0
MULTILANE_MAX_CAPACITY_PC_H_LN = 2300.0
MULTILANE_DENSITY_AT_CAPACITY_PC_MI_LN = 45.0
MULTILANE_SPEED_FLOW_EXPONENT = 1.31

FOUR_LANE_TLC_REDUCTIONS_MPH = {
    12.0: 0.0,
    10.0: 0.4,
    8.0: 0.9,
    6.0: 1.3,
    4.0: 1.8,
    2.0: 3.6,
    0.0: 5.4,
}

SIX_LANE_TLC_REDUCTIONS_MPH = {
    12.0: 0.0,
    10.0: 0.4,
    8.0: 0.9,
    6.0: 1.3,
    4.0: 1.7,
    2.0: 2.8,
    0.0: 3.9,
}

MEDIAN_FFS_REDUCTIONS_MPH = {
    "undivided": 1.6,
    "twltl": 0.0,
    "divided": 0.0,
}

LOS_DENSITY_UPPER_BOUNDS = (
    ("A", 11.0),
    ("B", 18.0),
    ("C", 26.0),
    ("D", 35.0),
    ("E", 45.0),
)
