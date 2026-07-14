"""HCM Chapter 15 Step 1 applicability tables for two-lane highways."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Literal

from hcmcalc.methods.two_lane_highway_models import (
    PASSING_CONSTRAINED,
    PASSING_LANE,
    PASSING_ZONE,
)


EXHIBIT_15_10_SOURCE = "HCM7 Exhibit 15-10"
SegmentLengthApplicabilityStatus = Literal["within_exhibit_15_10", "outside_exhibit_15_10"]


@dataclass(frozen=True)
class Exhibit1510LengthRange:
    """An inclusive minimum/maximum row from Exhibit 15-10."""

    vertical_class: int
    segment_type: str
    minimum_mi: float
    maximum_mi: float
    source_reference: str = EXHIBIT_15_10_SOURCE


@dataclass(frozen=True)
class SegmentLengthApplicability:
    """Auditable Exhibit 15-10 segment-length applicability result."""

    segment_type: str
    vertical_class: int
    submitted_segment_length_mi: float
    minimum_mi: float
    maximum_mi: float
    status: SegmentLengthApplicabilityStatus
    source_reference: str

    @property
    def compliant(self) -> bool:
        return self.status == "within_exhibit_15_10"


_LENGTHS = {
    1: ((0.25, 3.0), (0.25, 2.0), (0.5, 3.0)),
    2: ((0.25, 3.0), (0.25, 2.0), (0.5, 3.0)),
    3: ((0.25, 1.1), (0.25, 1.1), (0.5, 1.1)),
    4: ((0.5, 3.0), (0.5, 2.0), (0.5, 3.0)),
    5: ((0.5, 3.0), (0.5, 2.0), (0.5, 3.0)),
}
_SEGMENT_TYPES = (PASSING_CONSTRAINED, PASSING_ZONE, PASSING_LANE)

EXHIBIT_15_10_LENGTH_RANGES = tuple(
    Exhibit1510LengthRange(vertical_class, segment_type, *bounds)
    for vertical_class, row in _LENGTHS.items()
    for segment_type, bounds in zip(_SEGMENT_TYPES, row, strict=True)
)


def validate_exhibit_15_10_segment_length(
    *, segment_type: str, vertical_class: int, segment_length_mi: float
) -> SegmentLengthApplicability:
    """Validate an actual segment length against Exhibit 15-10 without clamping.

    The caller receives an explicit noncompliant result for a length outside the
    exhibit range. Invalid input is rejected with ``ValueError``.
    """

    if segment_type not in _SEGMENT_TYPES:
        raise ValueError(f"Unsupported Chapter 15 segment type: {segment_type!r}.")
    if isinstance(vertical_class, bool) or vertical_class not in _LENGTHS:
        raise ValueError("Vertical class must be an integer from 1 through 5.")
    try:
        length = float(segment_length_mi)
    except (TypeError, ValueError) as exc:
        raise ValueError("Segment length must be a finite positive number.") from exc
    if not isfinite(length) or length <= 0.0:
        raise ValueError("Segment length must be a finite positive number.")

    record = next(
        item
        for item in EXHIBIT_15_10_LENGTH_RANGES
        if item.vertical_class == vertical_class and item.segment_type == segment_type
    )
    return SegmentLengthApplicability(
        segment_type=segment_type,
        vertical_class=vertical_class,
        submitted_segment_length_mi=length,
        minimum_mi=record.minimum_mi,
        maximum_mi=record.maximum_mi,
        status=(
            "within_exhibit_15_10"
            if record.minimum_mi <= length <= record.maximum_mi
            else "outside_exhibit_15_10"
        ),
        source_reference=record.source_reference,
    )
