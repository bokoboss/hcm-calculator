import math

import pytest

from hcmcalc.methods.two_lane_highway_applicability import (
    EXHIBIT_15_10_LENGTH_RANGES,
    validate_exhibit_15_10_segment_length,
)


@pytest.mark.parametrize("record", EXHIBIT_15_10_LENGTH_RANGES)
def test_every_exhibit_15_10_row_has_inclusive_boundaries(record) -> None:
    minimum = validate_exhibit_15_10_segment_length(
        segment_type=record.segment_type,
        vertical_class=record.vertical_class,
        segment_length_mi=record.minimum_mi,
    )
    maximum = validate_exhibit_15_10_segment_length(
        segment_type=record.segment_type,
        vertical_class=record.vertical_class,
        segment_length_mi=record.maximum_mi,
    )

    assert minimum.compliant and maximum.compliant
    assert minimum.minimum_mi == record.minimum_mi
    assert maximum.maximum_mi == record.maximum_mi
    assert minimum.source_reference == "HCM7 Exhibit 15-10"


@pytest.mark.parametrize("record", EXHIBIT_15_10_LENGTH_RANGES)
def test_every_exhibit_15_10_row_rejects_immediately_outside_boundaries(record) -> None:
    below = validate_exhibit_15_10_segment_length(
        segment_type=record.segment_type,
        vertical_class=record.vertical_class,
        segment_length_mi=record.minimum_mi - 1e-9,
    )
    above = validate_exhibit_15_10_segment_length(
        segment_type=record.segment_type,
        vertical_class=record.vertical_class,
        segment_length_mi=record.maximum_mi + 1e-9,
    )

    assert not below.compliant and not above.compliant
    assert below.submitted_segment_length_mi < below.minimum_mi
    assert above.submitted_segment_length_mi > above.maximum_mi


@pytest.mark.parametrize(
    ("segment_type", "vertical_class", "length"),
    [
        ("bad", 1, 1.0),
        ("passing_constrained", 0, 1.0),
        ("passing_constrained", 6, 1.0),
        ("passing_constrained", 1, 0.0),
        ("passing_constrained", 1, -1.0),
        ("passing_constrained", 1, math.nan),
        ("passing_constrained", 1, math.inf),
    ],
)
def test_exhibit_15_10_rejects_invalid_inputs(segment_type, vertical_class, length) -> None:
    with pytest.raises(ValueError):
        validate_exhibit_15_10_segment_length(
            segment_type=segment_type,
            vertical_class=vertical_class,
            segment_length_mi=length,
        )
