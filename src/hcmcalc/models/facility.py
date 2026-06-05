"""Common facility identifiers."""

from enum import StrEnum


class FacilityType(StrEnum):
    """Supported and planned facility type identifiers."""

    TWO_LANE_HIGHWAY = "two_lane_highway"
    MULTILANE_HIGHWAY = "multilane_highway"
