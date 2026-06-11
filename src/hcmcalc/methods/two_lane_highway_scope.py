"""Explicit supported-scope decisions for Chapter 15 vertical behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from hcmcalc.core import UnsupportedScopeError
from hcmcalc.methods.two_lane_highway_models import (
    HORIZONTAL_CURVES_ALIGNMENT,
    PASSING_CONSTRAINED,
    PASSING_LANE,
    PASSING_ZONE,
    STRAIGHT_ALIGNMENT,
)
from hcmcalc.methods.vertical_lookup import (
    LookupStatus,
    VerticalClassLookupRecord,
    find_vertical_class_record,
)


ScopeStatus = Literal[
    "supported",
    "unsupported",
    "unsupported_needs_hcm_table_data",
    "unsupported_needs_validation_fixture",
]

@dataclass(frozen=True)
class VerticalScopeDecision:
    """Auditable Chapter 15 vertical-scope classification."""

    status: ScopeStatus
    reason: str
    vertical_class: int | None = None
    validation_basis: str | None = None

    @property
    def supported(self) -> bool:
        return self.status == "supported"


def classify_vertical_scope(
    *,
    segment_type: str,
    grade_percent: float,
    grade_length_mi: float | None,
    heavy_vehicle_percent: float,
    segment_length_mi: float | None = None,
    horizontal_alignment: str = STRAIGHT_ALIGNMENT,
    terrain_type: str | None = None,
    vertical_class: int | None = None,
    validated_facility_example: bool = False,
) -> VerticalScopeDecision:
    """Classify inputs without running Chapter 15 calculation formulas."""

    if grade_length_mi is None:
        return VerticalScopeDecision(
            "unsupported_needs_hcm_table_data",
            "Non-level Chapter 15 analysis requires grade length. The current "
            "engine uses the full segment length as grade length.",
        )

    if segment_length_mi is not None and grade_length_mi != segment_length_mi:
        return VerticalScopeDecision(
            "unsupported_needs_hcm_table_data",
            "Grade length must equal the full segment length in the currently "
            "supported Chapter 15 scope. Grade transitions require additional HCM "
            "methodology data and validation fixtures.",
        )

    if terrain_type not in {None, "level", "mountainous"}:
        return VerticalScopeDecision(
            "unsupported",
            f"Terrain type {terrain_type!r} is not mapped to validated Chapter 15 behavior.",
        )

    if terrain_type == "level" and grade_percent != 0.0:
        return VerticalScopeDecision(
            "unsupported",
            "Level terrain cannot be combined with a non-zero grade. This would "
            "otherwise fall back to level assumptions.",
        )
    if terrain_type == "mountainous" and grade_percent == 0.0:
        return VerticalScopeDecision(
            "unsupported",
            "Mountainous terrain cannot be combined with a zero grade in the "
            "currently validated Chapter 15 scope.",
        )

    if grade_percent == 0.0:
        derived_class = _derived_level_class(grade_length_mi)
        lookup_record = None
    else:
        lookup = find_vertical_class_record(
            terrain_type=terrain_type or "mountainous",
            segment_type=segment_type,
            grade_percent=grade_percent,
            grade_length_mi=grade_length_mi,
            heavy_vehicle_percent=heavy_vehicle_percent,
        )
        lookup_record = lookup.record
        class_lookup = (
            lookup
            if lookup_record is not None
            else find_vertical_class_record(
                terrain_type=terrain_type or "mountainous",
                segment_type=PASSING_CONSTRAINED,
                grade_percent=grade_percent,
                grade_length_mi=grade_length_mi,
                heavy_vehicle_percent=8.0,
            )
        )
        derived_class = (
            class_lookup.record.vertical_class
            if class_lookup.record is not None
            else None
        )

    if derived_class is None:
        return VerticalScopeDecision(
            "unsupported_needs_hcm_table_data",
            "Unsupported mountainous grade/length combination. This "
            "grade/length/vertical-class combination is outside the currently "
            "validated Chapter 15 scope. Broader vertical class support requires "
            "HCM grade-length lookup data and validation fixtures before calculation.",
        )

    if vertical_class is not None and vertical_class != derived_class:
        return VerticalScopeDecision(
            "unsupported",
            f"Submitted vertical class {vertical_class} does not match the currently "
            f"validated grade/length mapping to Class {derived_class}.",
            derived_class,
        )

    if grade_percent != 0.0 and heavy_vehicle_percent != 8.0:
        return VerticalScopeDecision(
            "unsupported_needs_validation_fixture",
            "Non-level Chapter 15 behavior is currently validated only at 8% heavy "
            "vehicles. A validation fixture is required before other percentages "
            "can be calculated.",
            derived_class,
        )

    if (
        grade_percent != 0.0
        and not validated_facility_example
        and not _is_manual_single_segment_validated(lookup_record)
    ):
        return VerticalScopeDecision(
            "unsupported_needs_validation_fixture",
            "This non-level combination is represented only in the validated "
            "Example Problem 4 facility context. Manual single-segment support is "
            "limited to the straight Passing Constrained 6% / 0.5 mi / Class 4 / "
            "8% heavy-vehicle path.",
            derived_class,
            _validation_basis(lookup_record),
        )

    if (
        horizontal_alignment == HORIZONTAL_CURVES_ALIGNMENT
        and grade_percent != 0.0
        and not validated_facility_example
    ):
        return VerticalScopeDecision(
            "unsupported_needs_validation_fixture",
            "General non-level horizontal-curve behavior is outside the validated "
            "manual Chapter 15 scope.",
            derived_class,
        )
    if horizontal_alignment not in {STRAIGHT_ALIGNMENT, HORIZONTAL_CURVES_ALIGNMENT}:
        return VerticalScopeDecision(
            "unsupported",
            f"Horizontal alignment {horizontal_alignment!r} is not mapped to validated "
            "Chapter 15 behavior.",
            derived_class,
        )

    if segment_type == PASSING_LANE:
        if heavy_vehicle_percent != 8.0:
            return VerticalScopeDecision(
                "unsupported_needs_validation_fixture",
                "Passing Lane is currently supported only at 8% heavy vehicles. It is "
                "limited to the validated Class 1 / 8% heavy-vehicle path and does not "
                "include downstream or facility effects.",
                derived_class,
            )
        if derived_class != 1:
            return VerticalScopeDecision(
                "unsupported_needs_hcm_table_data",
                "Passing Lane is currently supported only for vertical Class 1 at 8% "
                "heavy vehicles. Broader vertical class support requires HCM table "
                "data and validation fixtures.",
                derived_class,
            )

    if (
        grade_percent != 0.0
        and segment_type == PASSING_ZONE
        and not validated_facility_example
    ):
        return VerticalScopeDecision(
            "unsupported_needs_validation_fixture",
            "Non-level Passing Zone behavior does not have an independent validation "
            "fixture and is outside the currently supported Chapter 15 scope.",
            derived_class,
        )

    if segment_type not in {PASSING_CONSTRAINED, PASSING_ZONE, PASSING_LANE}:
        return VerticalScopeDecision(
            "unsupported",
            f"Segment type {segment_type!r} is not mapped to validated Chapter 15 behavior.",
            derived_class,
        )

    return VerticalScopeDecision(
        "supported",
        "Combination is within the currently supported Chapter 15 scope.",
        derived_class,
        _validation_basis(lookup_record),
    )


def require_supported_vertical_scope(**inputs: object) -> VerticalScopeDecision:
    """Raise a structured unsupported-scope error unless classification succeeds."""

    decision = classify_vertical_scope(**inputs)  # type: ignore[arg-type]
    if decision.supported:
        return decision
    context = dict(inputs)
    context["vertical_class"] = decision.vertical_class or context.get("vertical_class")
    raise UnsupportedScopeError(
        decision.reason,
        scope_status=decision.status,
        unsupported_reason=decision.reason,
        context=context,
    )


def _derived_level_class(grade_length_mi: float) -> int | None:
    if 0.25 <= grade_length_mi <= 3.0:
        return 1
    return None


def _is_manual_single_segment_validated(
    record: VerticalClassLookupRecord | None,
) -> bool:
    return (
        record is not None
        and record.status == LookupStatus.VALIDATED_EXAMPLE_PATH
        and record.manual_single_segment_validated
    )


def _validation_basis(record: VerticalClassLookupRecord | None) -> str | None:
    if record is None:
        return None
    return f"{record.source}; {record.validation_basis}"
