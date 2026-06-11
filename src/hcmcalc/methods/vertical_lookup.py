"""Table-driven metadata structures for future Chapter 15 vertical lookups.

This module does not enable calculation support. Records describe only paths
already represented by the repository's validation fixtures and contain no HCM
table values or coefficients.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from typing import Self


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
) -> VerticalClassLookupRecord:
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
        validation_basis="Existing repository validation fixture",
        status=LookupStatus.VALIDATED_EXAMPLE_PATH,
        notes="Metadata only; no HCM lookup table values or coefficients are represented.",
    )


# Metadata mirrors only existing validated paths. It is intentionally not used
# by the production scope checker or calculation engine.
VERTICAL_CLASS_LOOKUP_RECORDS = (
    _validated_example_record(
        segment_type="passing_constrained",
        grade_percent=-3.0,
        grade_length_mi=0.5,
        vertical_class=1,
    ),
    _validated_example_record(
        segment_type="passing_lane",
        grade_percent=-3.0,
        grade_length_mi=0.5,
        vertical_class=1,
    ),
    _validated_example_record(
        segment_type="passing_constrained",
        grade_percent=4.0,
        grade_length_mi=1.3,
        vertical_class=4,
    ),
    _validated_example_record(
        segment_type="passing_constrained",
        grade_percent=6.0,
        grade_length_mi=0.5,
        vertical_class=4,
    ),
    _validated_example_record(
        segment_type="passing_constrained",
        grade_percent=6.0,
        grade_length_mi=1.0,
        vertical_class=5,
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
