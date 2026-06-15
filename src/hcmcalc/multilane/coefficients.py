"""Reference-backed constants used by Multilane Example Problem 4."""

MULTILANE_BREAKPOINT_PC_H_LN = 1400.0
MULTILANE_MAX_CAPACITY_PC_H_LN = 2300.0

FOUR_LANE_TLC_REDUCTIONS_MPH = {
    12.0: 0.0,
    10.0: 0.4,
    8.0: 0.9,
    6.0: 1.3,
    4.0: 1.8,
    2.0: 3.6,
    0.0: 5.4,
}

MEDIAN_FFS_REDUCTIONS_MPH = {
    "undivided": 1.6,
    "twltl": 0.0,
    "divided": 0.0,
}

# HCM7 Exhibit 12-26, default 30% SUT / 70% TT mix, 6% trucks.
EXAMPLE_4_PCE_BY_EFFECTIVE_GRADE = {
    -2.0: 2.24,
    3.5: 3.97,
}

LOS_DENSITY_UPPER_BOUNDS = (
    ("A", 11.0),
    ("B", 18.0),
    ("C", 26.0),
    ("D", 35.0),
    ("E", 45.0),
)
