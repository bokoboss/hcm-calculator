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
