import pytest

from hcmcalc.methods.vertical_lookup import (
    LookupStatus,
    classify_vertical_lookup_status,
    find_vertical_class_record,
    normalize_grade_length,
    normalize_grade_percent,
)


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
