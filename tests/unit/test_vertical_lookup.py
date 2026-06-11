import pytest

from hcmcalc.methods.vertical_lookup import (
    LookupStatus,
    classify_vertical_alignment,
    classify_vertical_lookup_status,
    find_vertical_class_record,
    normalize_grade_length,
    normalize_grade_percent,
)


@pytest.mark.parametrize(
    ("length", "grade", "expected_class"),
    [
        (0.1, 1.0, 1),
        (0.1, 8.0, 2),
        (0.2, 8.0, 3),
        (0.3, 8.0, 4),
        (0.3, 10.0, 5),
    ],
)
def test_exhibit_15_11_representative_upgrade_classes(
    length: float,
    grade: float,
    expected_class: int,
) -> None:
    result = classify_vertical_alignment(length, grade)

    assert result.vertical_class == expected_class
    assert result.direction == "upgrade"
    assert result.lookup_row_range
    assert result.lookup_column_range
    assert "Exhibit 15-11" in result.source_reference


def test_exhibit_15_11_uses_parenthetical_values_for_downgrades() -> None:
    signed_result = classify_vertical_alignment(0.1, -8.0)
    contextual_result = classify_vertical_alignment(0.1, 8.0, "downgrade")

    assert signed_result.vertical_class == 1
    assert contextual_result == signed_result
    assert signed_result.direction == "downgrade"


@pytest.mark.parametrize(
    ("length", "expected_row", "expected_class"),
    [
        (0.1 - 1e-9, "<=0.1 mi", 1),
        (0.1, "<=0.1 mi", 1),
        (0.1 + 1e-9, ">0.1 to <=0.2 mi", 2),
        (0.2 - 1e-9, ">0.1 to <=0.2 mi", 2),
        (0.2, ">0.1 to <=0.2 mi", 2),
        (0.2 + 1e-9, ">0.2 to <=0.3 mi", 3),
        (1.1 - 1e-9, ">1.0 to <=1.1 mi", 5),
        (1.1, ">1.0 to <=1.1 mi", 5),
        (1.1 + 1e-9, ">1.1 mi", 5),
    ],
)
def test_exhibit_15_11_length_boundaries_are_lower_exclusive_upper_inclusive(
    length: float,
    expected_row: str,
    expected_class: int,
) -> None:
    result = classify_vertical_alignment(length, 6.0)

    assert result.lookup_row_range == expected_row
    assert result.vertical_class == expected_class


@pytest.mark.parametrize(
    ("threshold", "at_or_below_row", "above_row"),
    [
        (0.1, "<=0.1 mi", ">0.1 to <=0.2 mi"),
        (0.2, ">0.1 to <=0.2 mi", ">0.2 to <=0.3 mi"),
        (0.3, ">0.2 to <=0.3 mi", ">0.3 to <=0.4 mi"),
        (0.4, ">0.3 to <=0.4 mi", ">0.4 to <=0.5 mi"),
        (0.5, ">0.4 to <=0.5 mi", ">0.5 to <=0.6 mi"),
        (0.6, ">0.5 to <=0.6 mi", ">0.6 to <=0.7 mi"),
        (0.7, ">0.6 to <=0.7 mi", ">0.7 to <=0.8 mi"),
        (0.8, ">0.7 to <=0.8 mi", ">0.8 to <=0.9 mi"),
        (0.9, ">0.8 to <=0.9 mi", ">0.9 to <=1.0 mi"),
        (1.0, ">0.9 to <=1.0 mi", ">1.0 to <=1.1 mi"),
        (1.1, ">1.0 to <=1.1 mi", ">1.1 mi"),
    ],
)
def test_exhibit_15_11_every_length_threshold_selects_exact_bin(
    threshold: float,
    at_or_below_row: str,
    above_row: str,
) -> None:
    epsilon = 1e-9

    assert (
        classify_vertical_alignment(threshold - epsilon, 4.0).lookup_row_range
        == at_or_below_row
    )
    assert (
        classify_vertical_alignment(threshold, 4.0).lookup_row_range
        == at_or_below_row
    )
    assert (
        classify_vertical_alignment(threshold + epsilon, 4.0).lookup_row_range
        == above_row
    )


@pytest.mark.parametrize(
    ("grade", "expected_column", "expected_class"),
    [
        (1.0 - 1e-9, "<=1%", 1),
        (1.0, "<=1%", 1),
        (1.0 + 1e-9, ">1% to <=2%", 1),
        (3.0 - 1e-9, ">2% to <=3%", 2),
        (3.0, ">2% to <=3%", 2),
        (3.0 + 1e-9, ">3% to <=4%", 3),
        (9.0 - 1e-9, ">8% to <=9%", 5),
        (9.0, ">8% to <=9%", 5),
        (9.0 + 1e-9, ">9%", 5),
    ],
)
def test_exhibit_15_11_grade_boundaries_are_lower_exclusive_upper_inclusive(
    grade: float,
    expected_column: str,
    expected_class: int,
) -> None:
    result = classify_vertical_alignment(0.6, grade)

    assert result.lookup_column_range == expected_column
    assert result.vertical_class == expected_class


@pytest.mark.parametrize(
    ("threshold", "at_or_below_column", "above_column"),
    [
        (1.0, "<=1%", ">1% to <=2%"),
        (2.0, ">1% to <=2%", ">2% to <=3%"),
        (3.0, ">2% to <=3%", ">3% to <=4%"),
        (4.0, ">3% to <=4%", ">4% to <=5%"),
        (5.0, ">4% to <=5%", ">5% to <=6%"),
        (6.0, ">5% to <=6%", ">6% to <=7%"),
        (7.0, ">6% to <=7%", ">7% to <=8%"),
        (8.0, ">7% to <=8%", ">8% to <=9%"),
        (9.0, ">8% to <=9%", ">9%"),
    ],
)
def test_exhibit_15_11_every_grade_threshold_selects_exact_bin(
    threshold: float,
    at_or_below_column: str,
    above_column: str,
) -> None:
    epsilon = 1e-9

    assert (
        classify_vertical_alignment(0.6, threshold - epsilon).lookup_column_range
        == at_or_below_column
    )
    assert (
        classify_vertical_alignment(0.6, threshold).lookup_column_range
        == at_or_below_column
    )
    assert (
        classify_vertical_alignment(0.6, threshold + epsilon).lookup_column_range
        == above_column
    )


@pytest.mark.parametrize(
    ("length", "grade", "expected_class"),
    [(1.3, 4.0, 4), (1.0, 6.0, 5), (0.5, 6.0, 4), (0.5, -3.0, 1)],
)
def test_exhibit_15_11_matches_tlh_ch15_004_segment_classes(
    length: float,
    grade: float,
    expected_class: int,
) -> None:
    assert classify_vertical_alignment(length, grade).vertical_class == expected_class


@pytest.mark.parametrize("length", [None, 0.0, -0.1, float("inf"), float("nan"), "bad"])
def test_exhibit_15_11_rejects_invalid_or_missing_segment_length(
    length: object,
) -> None:
    with pytest.raises(ValueError, match="Segment length"):
        classify_vertical_alignment(length, 4.0)  # type: ignore[arg-type]


@pytest.mark.parametrize("grade", [None, float("inf"), float("nan"), "bad"])
def test_exhibit_15_11_rejects_invalid_or_missing_grade(grade: object) -> None:
    with pytest.raises(ValueError, match="Grade percent"):
        classify_vertical_alignment(0.5, grade)  # type: ignore[arg-type]


def test_exhibit_15_11_rejects_unsupported_direction_context() -> None:
    with pytest.raises(ValueError, match="Direction context"):
        classify_vertical_alignment(0.5, 4.0, "level")  # type: ignore[arg-type]


def test_missing_lookup_data_returns_structured_status() -> None:
    result = find_vertical_class_record(
        terrain_type="mountainous",
        segment_type="passing_constrained",
        grade_percent=5.0,
        grade_length_mi=0.75,
        heavy_vehicle_percent=8.0,
    )

    assert result.status == LookupStatus.MISSING_DATA
    assert result.record is None
    assert not result.found
    assert result.reason


def test_exact_validated_example_path_metadata_can_be_found() -> None:
    result = find_vertical_class_record(
        terrain_type="mountainous",
        segment_type="passing_constrained",
        grade_percent=4.0,
        grade_length_mi=1.3,
        heavy_vehicle_percent=8.0,
    )

    assert result.status == LookupStatus.VALIDATED_EXAMPLE_PATH
    assert result.record is not None
    assert result.record.vertical_class == 4
    assert "Example Problem 4" in result.record.source
    assert "no HCM lookup table values" in result.record.notes


def test_selected_vertical_path_metadata_names_exact_validation_fixture_segment() -> None:
    result = find_vertical_class_record(
        terrain_type="mountainous",
        segment_type="passing_constrained",
        grade_percent=6.0,
        grade_length_mi=0.5,
        heavy_vehicle_percent=8.0,
    )

    assert result.record is not None
    assert result.record.vertical_class == 4
    assert "TLH-CH15-004 segment 3" in result.record.validation_basis
    assert result.record.manual_single_segment_validated


@pytest.mark.parametrize(
    ("segment_type", "grade", "length", "basis_text", "notes_text"),
    [
        ("passing_constrained", 4.0, 1.3, "segments 1 and 4", "horizontal-curve"),
        ("passing_constrained", 6.0, 1.0, "segment 2", "horizontal-curve"),
        ("passing_lane", -3.0, 0.5, "segment 5", "Passing Lane"),
        ("passing_constrained", -3.0, 0.5, "segment 6", "upstream Passing Lane"),
    ],
)
def test_remaining_example_4_metadata_is_explicitly_facility_only(
    segment_type: str,
    grade: float,
    length: float,
    basis_text: str,
    notes_text: str,
) -> None:
    result = find_vertical_class_record(
        terrain_type="mountainous",
        segment_type=segment_type,
        grade_percent=grade,
        grade_length_mi=length,
        heavy_vehicle_percent=8.0,
    )

    assert result.record is not None
    assert basis_text in result.record.validation_basis
    assert notes_text in result.record.notes
    assert not result.record.manual_single_segment_validated


def test_unsupported_grade_length_combination_remains_missing_data() -> None:
    status = classify_vertical_lookup_status(
        terrain_type="mountainous",
        segment_type="passing_constrained",
        grade_percent=4.0,
        grade_length_mi=1.0,
        heavy_vehicle_percent=8.0,
    )

    assert status == LookupStatus.MISSING_DATA


@pytest.mark.parametrize("value", [0.0, -0.5, float("inf"), float("nan"), "bad"])
def test_invalid_grade_length_is_handled_clearly(value: object) -> None:
    with pytest.raises(ValueError, match="Grade length"):
        normalize_grade_length(value)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan"), "bad"])
def test_invalid_grade_percent_is_handled_clearly(value: object) -> None:
    with pytest.raises(ValueError, match="Grade percent"):
        normalize_grade_percent(value)  # type: ignore[arg-type]


def test_heavy_vehicle_percent_mismatch_has_no_validated_fixture_metadata() -> None:
    result = find_vertical_class_record(
        terrain_type="mountainous",
        segment_type="passing_constrained",
        grade_percent=4.0,
        grade_length_mi=1.3,
        heavy_vehicle_percent=10.0,
    )

    assert result.status == LookupStatus.MISSING_DATA
    assert result.record is None
