"""Table-driven structures for Chapter 15 vertical lookups.

The Exhibit 15-11 lookup classifies vertical alignment independently from
calculation support. Validation-path records remain limited to paths already
represented by repository fixtures and are used by scope guardrails.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from typing import Literal, Self


VERTICAL_ALIGNMENT_CLASSIFICATION_SOURCE = (
    "NCHRP Research Report 1102 methodology document, Chapter 7, "
    "Step 3, Exhibit 15-11: Classifications for vertical alignment"
)

VerticalDirection = Literal["upgrade", "downgrade"]


class LookupStatus(StrEnum):
    """Availability status for a vertical lookup."""

    VALIDATED_EXAMPLE_PATH = "validated_example_path"
    MISSING_DATA = "missing_data"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class NumericBoundary:
    """Inclusive or exclusive numeric lookup boundary."""

    minimum: float
    maximum: float
    include_minimum: bool = True
    include_maximum: bool = True

    def __post_init__(self) -> None:
        if not isfinite(self.minimum) or not isfinite(self.maximum):
            raise ValueError("Lookup boundaries must be finite.")
        if self.minimum > self.maximum:
            raise ValueError("Lookup boundary minimum cannot exceed maximum.")

    @classmethod
    def exact(cls, value: float) -> Self:
        """Create an exact-value boundary."""

        return cls(value, value)

    def contains(self, value: float) -> bool:
        """Return whether a normalized value is inside this boundary."""

        above_minimum = value >= self.minimum if self.include_minimum else value > self.minimum
        below_maximum = value <= self.maximum if self.include_maximum else value < self.maximum
        return above_minimum and below_maximum


class GradePercentBoundary(NumericBoundary):
    """Signed grade-percent lookup boundary."""


class GradeLengthBoundary(NumericBoundary):
    """Grade-length lookup boundary in engine-native Imperial miles."""


class HeavyVehiclePercentBoundary(NumericBoundary):
    """Heavy-vehicle-percent lookup boundary."""


@dataclass(frozen=True)
class VerticalAlignmentLookupRange:
    """One lower-exclusive and upper-inclusive Exhibit 15-11 range."""

    label: str
    minimum_exclusive: float | None = None
    maximum_inclusive: float | None = None

    def contains(self, value: float) -> bool:
        """Return whether a normalized value is inside this range."""

        return (
            self.minimum_exclusive is None or value > self.minimum_exclusive
        ) and (
            self.maximum_inclusive is None or value <= self.maximum_inclusive
        )


@dataclass(frozen=True)
class VerticalAlignmentClassification:
    """Auditable result from the HCM Exhibit 15-11 classification lookup."""

    vertical_class: int
    lookup_row_range: str
    lookup_column_range: str
    source_reference: str
    direction: VerticalDirection


@dataclass(frozen=True)
class VerticalAlignmentLookupRow:
    """One segment-length row and its upgrade/downgrade class values."""

    length_range: VerticalAlignmentLookupRange
    upgrade_classes: tuple[int, ...]
    downgrade_classes: tuple[int, ...]


VERTICAL_ALIGNMENT_GRADE_COLUMNS = (
    VerticalAlignmentLookupRange("<=1%", maximum_inclusive=1.0),
    VerticalAlignmentLookupRange(">1% to <=2%", 1.0, 2.0),
    VerticalAlignmentLookupRange(">2% to <=3%", 2.0, 3.0),
    VerticalAlignmentLookupRange(">3% to <=4%", 3.0, 4.0),
    VerticalAlignmentLookupRange(">4% to <=5%", 4.0, 5.0),
    VerticalAlignmentLookupRange(">5% to <=6%", 5.0, 6.0),
    VerticalAlignmentLookupRange(">6% to <=7%", 6.0, 7.0),
    VerticalAlignmentLookupRange(">7% to <=8%", 7.0, 8.0),
    VerticalAlignmentLookupRange(">8% to <=9%", 8.0, 9.0),
    VerticalAlignmentLookupRange(">9%", minimum_exclusive=9.0),
)


def _vertical_alignment_row(
    label: str,
    minimum_exclusive: float | None,
    maximum_inclusive: float | None,
    upgrade_classes: tuple[int, ...],
    downgrade_classes: tuple[int, ...],
) -> VerticalAlignmentLookupRow:
    return VerticalAlignmentLookupRow(
        VerticalAlignmentLookupRange(label, minimum_exclusive, maximum_inclusive),
        upgrade_classes,
        downgrade_classes,
    )


# Values outside parentheses are upgrades; values in parentheses are downgrades.
VERTICAL_ALIGNMENT_CLASSIFICATION_ROWS = (
    _vertical_alignment_row(
        "<=0.1 mi", None, 0.1,
        (1, 1, 1, 1, 1, 1, 1, 2, 2, 2),
        (1, 1, 1, 1, 1, 1, 1, 1, 2, 2),
    ),
    _vertical_alignment_row(
        ">0.1 to <=0.2 mi", 0.1, 0.2,
        (1, 1, 1, 1, 2, 2, 2, 3, 3, 3),
        (1, 1, 1, 1, 1, 2, 2, 2, 3, 3),
    ),
    _vertical_alignment_row(
        ">0.2 to <=0.3 mi", 0.2, 0.3,
        (1, 1, 1, 2, 2, 3, 3, 4, 4, 5),
        (1, 1, 1, 1, 2, 2, 3, 3, 4, 5),
    ),
    _vertical_alignment_row(
        ">0.3 to <=0.4 mi", 0.3, 0.4,
        (1, 1, 2, 2, 3, 3, 4, 5, 5, 5),
        (1, 1, 1, 2, 2, 3, 4, 4, 5, 5),
    ),
    _vertical_alignment_row(
        ">0.4 to <=0.5 mi", 0.4, 0.5,
        (1, 1, 2, 2, 3, 4, 5, 5, 5, 5),
        (1, 1, 1, 2, 3, 3, 4, 5, 5, 5),
    ),
    _vertical_alignment_row(
        ">0.5 to <=0.6 mi", 0.5, 0.6,
        (1, 1, 2, 3, 3, 4, 5, 5, 5, 5),
        (1, 1, 1, 2, 3, 4, 5, 5, 5, 5),
    ),
    _vertical_alignment_row(
        ">0.6 to <=0.7 mi", 0.6, 0.7,
        (1, 1, 2, 3, 4, 4, 5, 5, 5, 5),
        (1, 1, 1, 2, 3, 4, 5, 5, 5, 5),
    ),
    _vertical_alignment_row(
        ">0.7 to <=0.8 mi", 0.7, 0.8,
        (1, 1, 2, 3, 4, 5, 5, 5, 5, 5),
        (1, 1, 1, 3, 4, 4, 5, 5, 5, 5),
    ),
    _vertical_alignment_row(
        ">0.8 to <=0.9 mi", 0.8, 0.9,
        (1, 1, 2, 3, 4, 5, 5, 5, 5, 5),
        (1, 1, 1, 3, 4, 5, 5, 5, 5, 5),
    ),
    _vertical_alignment_row(
        ">0.9 to <=1.0 mi", 0.9, 1.0,
        (1, 1, 2, 3, 4, 5, 5, 5, 5, 5),
        (1, 1, 2, 3, 4, 5, 5, 5, 5, 5),
    ),
    _vertical_alignment_row(
        ">1.0 to <=1.1 mi", 1.0, 1.1,
        (1, 1, 2, 3, 4, 5, 5, 5, 5, 5),
        (1, 1, 2, 3, 4, 5, 5, 5, 5, 5),
    ),
    _vertical_alignment_row(
        ">1.1 mi", 1.1, None,
        (1, 1, 2, 4, 4, 5, 5, 5, 5, 5),
        (1, 1, 2, 4, 4, 5, 5, 5, 5, 5),
    ),
)


def classify_vertical_alignment(
    segment_length_mi: float | None,
    grade_percent: float | None,
    direction_context: VerticalDirection | None = None,
) -> VerticalAlignmentClassification:
    """Classify vertical alignment using Step 3 and Exhibit 15-11.

    Signed grades infer direction when ``direction_context`` is omitted.
    A supplied direction context allows callers with unsigned grade magnitude
    inputs to select the upgrade or parenthetical downgrade table value.
    """

    if segment_length_mi is None:
        raise ValueError("Segment length is required for vertical classification.")
    if grade_percent is None:
        raise ValueError("Grade percent is required for vertical classification.")

    normalized_length = _normalize_finite_number(segment_length_mi, "Segment length")
    if normalized_length <= 0.0:
        raise ValueError("Segment length must be greater than zero.")
    normalized_grade = normalize_grade_percent(grade_percent)

    if direction_context is None:
        direction: VerticalDirection = (
            "downgrade" if normalized_grade < 0.0 else "upgrade"
        )
    elif direction_context in {"upgrade", "downgrade"}:
        direction = direction_context
    else:
        raise ValueError("Direction context must be 'upgrade' or 'downgrade'.")

    grade_magnitude = abs(normalized_grade)
    row = next(
        (
            candidate
            for candidate in VERTICAL_ALIGNMENT_CLASSIFICATION_ROWS
            if candidate.length_range.contains(normalized_length)
        ),
        None,
    )
    column_index = next(
        (
            index
            for index, candidate in enumerate(VERTICAL_ALIGNMENT_GRADE_COLUMNS)
            if candidate.contains(grade_magnitude)
        ),
        None,
    )
    if row is None or column_index is None:
        raise ValueError(
            "Segment length and grade percent are outside Exhibit 15-11."
        )

    classes = (
        row.downgrade_classes if direction == "downgrade" else row.upgrade_classes
    )
    return VerticalAlignmentClassification(
        vertical_class=classes[column_index],
        lookup_row_range=row.length_range.label,
        lookup_column_range=VERTICAL_ALIGNMENT_GRADE_COLUMNS[column_index].label,
        source_reference=VERTICAL_ALIGNMENT_CLASSIFICATION_SOURCE,
        direction=direction,
    )


@dataclass(frozen=True)
class VerticalClassLookupKey:
    """Inputs used to identify future vertical-class lookup records."""

    terrain_type: str
    segment_type: str
    grade_percent: GradePercentBoundary
    grade_length_mi: GradeLengthBoundary
    heavy_vehicle_percent: HeavyVehiclePercentBoundary

    def matches(
        self,
        *,
        terrain_type: str,
        segment_type: str,
        grade_percent: float,
        grade_length_mi: float,
        heavy_vehicle_percent: float,
    ) -> bool:
        """Return whether normalized inputs match this key."""

        return (
            self.terrain_type == terrain_type
            and self.segment_type == segment_type
            and self.grade_percent.contains(grade_percent)
            and self.grade_length_mi.contains(grade_length_mi)
            and self.heavy_vehicle_percent.contains(heavy_vehicle_percent)
        )


@dataclass(frozen=True)
class VerticalClassLookupRecord:
    """Source-attributed metadata for a vertical lookup path."""

    key: VerticalClassLookupKey
    vertical_class: int | None
    source: str
    validation_basis: str
    status: LookupStatus
    notes: str
    manual_single_segment_validated: bool = False


@dataclass(frozen=True)
class VerticalLookupResult:
    """Structured result that never implies missing HCM values."""

    status: LookupStatus
    reason: str
    record: VerticalClassLookupRecord | None = None

    @property
    def found(self) -> bool:
        return self.record is not None


def _validated_example_record(
    *,
    segment_type: str,
    grade_percent: float,
    grade_length_mi: float,
    vertical_class: int,
    validation_basis: str = "Existing repository validation fixture",
    manual_single_segment_validated: bool = False,
    notes: str | None = None,
) -> VerticalClassLookupRecord:
    metadata_note = (
        "Metadata only; no HCM lookup table values or coefficients are represented."
    )
    return VerticalClassLookupRecord(
        key=VerticalClassLookupKey(
            terrain_type="mountainous",
            segment_type=segment_type,
            grade_percent=GradePercentBoundary.exact(grade_percent),
            grade_length_mi=GradeLengthBoundary.exact(grade_length_mi),
            heavy_vehicle_percent=HeavyVehiclePercentBoundary.exact(8.0),
        ),
        vertical_class=vertical_class,
        source="HCM Chapter 26 Two-Lane Highway Example Problem 4",
        validation_basis=validation_basis,
        status=LookupStatus.VALIDATED_EXAMPLE_PATH,
        notes=f"{metadata_note} {notes}" if notes else metadata_note,
        manual_single_segment_validated=manual_single_segment_validated,
    )


# Metadata mirrors only existing validated paths. It does not add methodology
# data or authorize calculation formulas beyond the recorded validation scope.
VERTICAL_CLASS_LOOKUP_RECORDS = (
    _validated_example_record(
        segment_type="passing_constrained",
        grade_percent=-3.0,
        grade_length_mi=0.5,
        vertical_class=1,
        validation_basis=(
            "Existing repository fixture TLH-CH15-004 segment 6 expected outputs"
        ),
        notes=(
            "Facility-only path; published final follower density includes upstream "
            "Passing Lane adjustment and does not validate standalone output."
        ),
    ),
    _validated_example_record(
        segment_type="passing_lane",
        grade_percent=-3.0,
        grade_length_mi=0.5,
        vertical_class=1,
        validation_basis=(
            "Existing repository fixture TLH-CH15-004 segment 5 expected outputs"
        ),
        notes=(
            "Facility-only Passing Lane path; standalone and downstream effects are "
            "not independently validated."
        ),
    ),
    _validated_example_record(
        segment_type="passing_constrained",
        grade_percent=4.0,
        grade_length_mi=1.3,
        vertical_class=4,
        validation_basis=(
            "Existing repository fixture TLH-CH15-004 segments 1 and 4 expected outputs"
        ),
        notes=(
            "Facility-only nonlevel horizontal-curve path; no straight standalone "
            "validation fixture exists."
        ),
    ),
    _validated_example_record(
        segment_type="passing_constrained",
        grade_percent=6.0,
        grade_length_mi=0.5,
        vertical_class=4,
        validation_basis=(
            "Existing repository fixture TLH-CH15-004 segment 3 expected outputs"
        ),
        manual_single_segment_validated=True,
    ),
    _validated_example_record(
        segment_type="passing_constrained",
        grade_percent=6.0,
        grade_length_mi=1.0,
        vertical_class=5,
        validation_basis=(
            "Existing repository fixture TLH-CH15-004 segment 2 expected outputs"
        ),
        notes=(
            "Facility-only nonlevel horizontal-curve path; no straight standalone "
            "validation fixture exists."
        ),
    ),
)


def normalize_grade_percent(value: float) -> float:
    """Validate and normalize signed grade percent without rounding."""

    return _normalize_finite_number(value, "Grade percent")


def normalize_grade_length(value: float) -> float:
    """Validate and normalize engine-native grade length in miles."""

    normalized = _normalize_finite_number(value, "Grade length")
    if normalized <= 0.0:
        raise ValueError("Grade length must be greater than zero.")
    return normalized


def find_vertical_class_record(
    *,
    terrain_type: str,
    segment_type: str,
    grade_percent: float,
    grade_length_mi: float,
    heavy_vehicle_percent: float,
    records: tuple[VerticalClassLookupRecord, ...] = VERTICAL_CLASS_LOOKUP_RECORDS,
) -> VerticalLookupResult:
    """Find metadata for an exact validated path or report missing data."""

    normalized_grade = normalize_grade_percent(grade_percent)
    normalized_length = normalize_grade_length(grade_length_mi)
    normalized_heavy_vehicles = _normalize_heavy_vehicle_percent(heavy_vehicle_percent)

    for record in records:
        if record.key.matches(
            terrain_type=terrain_type,
            segment_type=segment_type,
            grade_percent=normalized_grade,
            grade_length_mi=normalized_length,
            heavy_vehicle_percent=normalized_heavy_vehicles,
        ):
            return VerticalLookupResult(
                status=record.status,
                reason="Matching validated example-path metadata found.",
                record=record,
            )

    return VerticalLookupResult(
        status=LookupStatus.MISSING_DATA,
        reason=(
            "No vertical lookup metadata matches this terrain, segment, grade, "
            "grade-length, and heavy-vehicle combination."
        ),
    )


def classify_vertical_lookup_status(**inputs: object) -> LookupStatus:
    """Return the lookup availability status for normalized inputs."""

    return find_vertical_class_record(**inputs).status  # type: ignore[arg-type]


def _normalize_finite_number(value: float, field_name: str) -> float:
    try:
        normalized = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a finite number.") from exc
    if not isfinite(normalized):
        raise ValueError(f"{field_name} must be a finite number.")
    return normalized


def _normalize_heavy_vehicle_percent(value: float) -> float:
    normalized = _normalize_finite_number(value, "Heavy vehicle percent")
    if not 0.0 <= normalized <= 100.0:
        raise ValueError("Heavy vehicle percent must be from 0 through 100.")
    return normalized
