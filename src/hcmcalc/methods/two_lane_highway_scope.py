"""Applicability and deliberately guarded calculation scope for Chapter 15."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Literal

from hcmcalc.core import UnsupportedScopeError
from hcmcalc.methods.two_lane_highway_applicability import (
    SegmentLengthApplicability,
    validate_exhibit_15_10_segment_length,
)
from hcmcalc.methods.two_lane_highway_models import (
    HORIZONTAL_CURVES_ALIGNMENT,
    PASSING_CONSTRAINED,
    PASSING_LANE,
    PASSING_ZONE,
    STRAIGHT_ALIGNMENT,
)
from hcmcalc.methods.vertical_lookup import (
    VerticalAlignmentClassification,
    VerticalDirection,
    find_vertical_class_record,
    classify_vertical_alignment,
)


ScopeStatus = Literal[
    "supported",
    "invalid_input",
    "outside_exhibit_15_10_applicability",
    "unsupported",
    "unsupported_downstream_methodology",
    "insufficient_validation_evidence",
]
CalculationScope = Literal["steps_1_3", "steps_4_10"]


@dataclass(frozen=True)
class VerticalScopeDecision:
    """Auditable Chapter 15 vertical classification and applicability decision."""

    status: ScopeStatus
    reason: str
    classification: VerticalAlignmentClassification | None = None
    segment_length_applicability: SegmentLengthApplicability | None = None
    validation_basis: str | None = None
    normalized_legacy_grade_length_mi: float | None = None

    @property
    def supported(self) -> bool:
        return self.status == "supported"

    @property
    def vertical_class(self) -> int | None:
        return self.classification.vertical_class if self.classification else None


def classify_vertical_scope(
    *,
    segment_type: str,
    grade_percent: float,
    grade_length_mi: float | None = None,
    heavy_vehicle_percent: float = 0.0,
    segment_length_mi: float | None = None,
    horizontal_alignment: str = STRAIGHT_ALIGNMENT,
    terrain_type: str | None = None,
    vertical_class: int | None = None,
    direction_context: VerticalDirection | None = None,
    calculation_scope: CalculationScope = "steps_1_3",
    validated_facility_example: bool = False,
) -> VerticalScopeDecision:
    """Classify Steps 1-3 independently of Chapter 26 validation metadata.

    ``grade_length_mi`` is a legacy import field. Exhibit 15-11 specifies the
    analysis segment length, so the field is accepted only for compatibility and
    never changes the derived class or Exhibit 15-10 applicability.
    """

    if calculation_scope not in {"steps_1_3", "steps_4_10"}:
        raise ValueError("Calculation scope must be 'steps_1_3' or 'steps_4_10'.")
    if segment_length_mi is None:
        raise ValueError("Segment length is required for Chapter 15 applicability.")
    if terrain_type not in {None, "level", "mountainous"}:
        return VerticalScopeDecision("unsupported", f"Unsupported terrain type: {terrain_type!r}.")
    if terrain_type == "level" and grade_percent != 0.0:
        return VerticalScopeDecision("unsupported", "Level terrain cannot be combined with a non-zero grade.")
    if terrain_type == "mountainous" and grade_percent == 0.0:
        return VerticalScopeDecision("unsupported", "Mountainous terrain cannot be combined with a zero grade.")
    if horizontal_alignment not in {STRAIGHT_ALIGNMENT, HORIZONTAL_CURVES_ALIGNMENT}:
        return VerticalScopeDecision("unsupported", f"Unsupported horizontal alignment: {horizontal_alignment!r}.")
    _validate_heavy_vehicle_percent(heavy_vehicle_percent)
    legacy_length = _normalize_legacy_grade_length(grade_length_mi)

    try:
        classification = classify_vertical_alignment(
            segment_length_mi, grade_percent, direction_context
        )
        applicability = validate_exhibit_15_10_segment_length(
            segment_type=segment_type,
            vertical_class=classification.vertical_class,
            segment_length_mi=segment_length_mi,
        )
    except ValueError as exc:
        return VerticalScopeDecision("invalid_input", str(exc), normalized_legacy_grade_length_mi=legacy_length)

    if vertical_class is not None and vertical_class != classification.vertical_class:
        return VerticalScopeDecision(
            "unsupported",
            f"Submitted vertical class {vertical_class} does not match Exhibit 15-11 Class {classification.vertical_class}.",
            classification,
            applicability,
            normalized_legacy_grade_length_mi=legacy_length,
        )
    if not applicability.compliant:
        return VerticalScopeDecision(
            "outside_exhibit_15_10_applicability",
            "Segment length is outside the applicable Exhibit 15-10 range; no length was clamped.",
            classification,
            applicability,
            normalized_legacy_grade_length_mi=legacy_length,
        )
    if calculation_scope == "steps_1_3":
        return VerticalScopeDecision(
            "supported",
            "Step 1-3 classification and applicability are supported by HCM Exhibits 15-10 and 15-11.",
            classification,
            applicability,
            normalized_legacy_grade_length_mi=legacy_length,
        )
    return _classify_downstream_scope(
        segment_type=segment_type,
        grade_percent=grade_percent,
        heavy_vehicle_percent=heavy_vehicle_percent,
        horizontal_alignment=horizontal_alignment,
        classification=classification,
        applicability=applicability,
        validated_facility_example=validated_facility_example,
        normalized_legacy_grade_length_mi=legacy_length,
    )


def require_supported_vertical_scope(**inputs: object) -> VerticalScopeDecision:
    """Raise a structured error unless the requested scope is supported."""

    decision = classify_vertical_scope(**inputs)  # type: ignore[arg-type]
    if decision.supported:
        return decision
    context = dict(inputs)
    context.update(_decision_context(decision))
    raise UnsupportedScopeError(
        decision.reason,
        scope_status=decision.status,
        unsupported_reason=decision.reason,
        context=context,
    )


def _classify_downstream_scope(**kwargs: object) -> VerticalScopeDecision:
    """Resolve the documented Phase 2 Step 4--10 single-segment envelope."""

    classification = kwargs["classification"]
    applicability = kwargs["applicability"]
    assert isinstance(classification, VerticalAlignmentClassification)
    assert isinstance(applicability, SegmentLengthApplicability)
    grade_percent = float(kwargs["grade_percent"])
    heavy_vehicle_percent = float(kwargs["heavy_vehicle_percent"])
    segment_type = str(kwargs["segment_type"])
    horizontal_alignment = str(kwargs["horizontal_alignment"])
    validated_facility_example = bool(kwargs["validated_facility_example"])
    legacy = kwargs["normalized_legacy_grade_length_mi"]
    # Exhibits 15-12 through 15-29 provide the Class 1--5 Passing
    # Constrained/Passing Zone sequence.  Chapter 26 records are validation
    # evidence only; they must not gate a fully specified HCM calculation.
    if segment_type in {PASSING_CONSTRAINED, PASSING_ZONE}:
        return VerticalScopeDecision(
            "supported",
            "Passing Constrained and Passing Zone Steps 4-10 are supported for "
            "the Exhibit 15-10/15-11 applicable single-segment envelope.",
            classification,
            applicability,
            "HCM method availability; Phase 2 method-conformance evidence",
            legacy,
        )

    lookup = find_vertical_class_record(
        terrain_type="mountainous",
        segment_type=segment_type,
        grade_percent=grade_percent,
        grade_length_mi=applicability.submitted_segment_length_mi,
        heavy_vehicle_percent=heavy_vehicle_percent,
    ) if grade_percent != 0.0 else None
    basis = _validation_basis(lookup.record) if lookup and lookup.record else None

    if segment_type == PASSING_LANE and heavy_vehicle_percent != 8.0:
        return VerticalScopeDecision("unsupported_downstream_methodology", "Passing Lane downstream calculation is supported only at 8% heavy vehicles.", classification, applicability, basis, legacy)  # type: ignore[arg-type]
    if grade_percent != 0.0 and heavy_vehicle_percent != 8.0:
        return VerticalScopeDecision("insufficient_validation_evidence", "Non-level downstream calculations are outside the currently validated Chapter 15 scope and remain validated only at 8% heavy vehicles.", classification, applicability, basis, legacy)  # type: ignore[arg-type]
    if grade_percent != 0.0 and not validated_facility_example and not (lookup and lookup.record and lookup.record.manual_single_segment_validated):
        reason = (
            "Unsupported mountainous grade/length combination for downstream calculation: "
            "Exhibit 15-11 classification is available, but it is outside the currently validated Chapter 15 scope."
            if not (lookup and lookup.record)
            else "Manual single-segment support is outside the currently validated facility-only path."
        )
        if segment_type == PASSING_LANE:
            reason = "Manual single-segment support is outside the currently validated Passing Lane path."
        return VerticalScopeDecision("insufficient_validation_evidence", reason, classification, applicability, basis, legacy)  # type: ignore[arg-type]
    if horizontal_alignment == HORIZONTAL_CURVES_ALIGNMENT and grade_percent != 0.0 and not validated_facility_example:
        return VerticalScopeDecision("insufficient_validation_evidence", "General non-level horizontal-curve calculations remain outside the validated downstream scope.", classification, applicability, basis, legacy)  # type: ignore[arg-type]
    if segment_type == PASSING_LANE and classification.vertical_class != 1:
        return VerticalScopeDecision("unsupported_downstream_methodology", "Passing Lane downstream calculations remain guarded outside the validated Class 1 path.", classification, applicability, basis, legacy)  # type: ignore[arg-type]
    return VerticalScopeDecision("supported", "Combination is within the deliberately limited downstream calculation scope.", classification, applicability, basis, legacy)  # type: ignore[arg-type]


def _validate_heavy_vehicle_percent(value: float) -> None:
    try:
        normalized = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Heavy vehicle percent must be a finite number from 0 through 100.") from exc
    if not isfinite(normalized) or not 0.0 <= normalized <= 100.0:
        raise ValueError("Heavy vehicle percent must be a finite number from 0 through 100.")


def _normalize_legacy_grade_length(value: float | None) -> float | None:
    if value is None:
        return None
    try:
        normalized = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Legacy grade length must be a finite positive number.") from exc
    if not isfinite(normalized) or normalized <= 0.0:
        raise ValueError("Legacy grade length must be a finite positive number.")
    return normalized


def _validation_basis(record: object) -> str | None:
    if record is None:
        return None
    return f"{record.source}; {record.validation_basis}"  # type: ignore[attr-defined]


def _decision_context(decision: VerticalScopeDecision) -> dict[str, object]:
    result: dict[str, object] = {"vertical_class": decision.vertical_class}
    if decision.classification:
        result.update({
            "vertical_direction": decision.classification.direction,
            "vertical_lookup_row_range": decision.classification.lookup_row_range,
            "vertical_lookup_column_range": decision.classification.lookup_column_range,
            "vertical_class_source_reference": decision.classification.source_reference,
        })
    if decision.segment_length_applicability:
        result.update({
            "segment_length_min_mi": decision.segment_length_applicability.minimum_mi,
            "segment_length_max_mi": decision.segment_length_applicability.maximum_mi,
            "segment_length_applicability_status": decision.segment_length_applicability.status,
            "segment_length_source_reference": decision.segment_length_applicability.source_reference,
        })
    return result
