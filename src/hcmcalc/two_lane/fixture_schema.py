"""Structural validation for future Chapter 15 vertical fixtures.

This module validates preparation fixtures only. It is not imported by the
calculation engine and does not authorize a fixture for runtime use.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


REQUIRED_FIXTURE_FIELDS = frozenset(
    {
        "fixture_id",
        "placeholder",
        "source",
        "source_reference",
        "calculation_type",
        "segment_type",
        "terrain_type",
        "horizontal_alignment",
        "grade_percent",
        "grade_length",
        "vertical_class",
        "heavy_vehicle_percent",
        "input_units",
        "expected_outputs",
        "expected_intermediate_values",
        "tolerance",
        "validation_status",
        "verification_status",
        "runtime_status",
        "implementation_status",
        "notes",
    }
)
RUNTIME_ENABLED_STATUSES = frozenset({"runtime_enabled", "runtime_validated"})
VERIFIED_STATUSES = frozenset({"verified", "independently_verified"})


class VerticalFixtureSchemaError(ValueError):
    """Raised when a vertical fixture does not satisfy the preparation schema."""


def validate_vertical_fixture(fixture: Mapping[str, Any]) -> None:
    """Validate one fixture dictionary without making it executable."""

    missing = sorted(REQUIRED_FIXTURE_FIELDS.difference(fixture))
    if missing:
        raise VerticalFixtureSchemaError(
            f"Vertical fixture is missing required fields: {', '.join(missing)}."
        )

    _require_explicit_text(fixture, "fixture_id")
    _require_explicit_text(fixture, "source_reference")
    _require_mapping(fixture, "expected_outputs")
    _require_mapping(fixture, "expected_intermediate_values")
    _require_mapping(fixture, "tolerance")
    _require_explicit_text(fixture, "validation_status")
    _require_explicit_text(fixture, "verification_status")
    _require_explicit_text(fixture, "runtime_status")
    _require_explicit_text(fixture, "implementation_status")

    placeholder = fixture["placeholder"]
    if not isinstance(placeholder, bool):
        raise VerticalFixtureSchemaError("Vertical fixture placeholder must be boolean.")

    validation_status = fixture["validation_status"]
    runtime_status = fixture["runtime_status"]
    verification_status = fixture["verification_status"]
    claims_runtime_validation = (
        runtime_status in RUNTIME_ENABLED_STATUSES
        or validation_status in RUNTIME_ENABLED_STATUSES
    )
    if claims_runtime_validation and (
        placeholder
        or verification_status not in VERIFIED_STATUSES
        or not validation_status.endswith("_validated")
    ):
        raise VerticalFixtureSchemaError(
            "Placeholder or unverified vertical fixtures cannot be runtime enabled."
        )


def validate_vertical_fixture_document(document: Mapping[str, Any]) -> None:
    """Validate a fixture-template or future fixture document."""

    fixtures = document.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        raise VerticalFixtureSchemaError(
            "Vertical fixture document must contain a non-empty fixtures list."
        )
    for fixture in fixtures:
        if not isinstance(fixture, Mapping):
            raise VerticalFixtureSchemaError("Each vertical fixture must be a mapping.")
        validate_vertical_fixture(fixture)


def _require_explicit_text(fixture: Mapping[str, Any], field: str) -> None:
    value = fixture[field]
    if not isinstance(value, str) or not value.strip():
        raise VerticalFixtureSchemaError(
            f"Vertical fixture {field} must be explicit non-empty text."
        )


def _require_mapping(fixture: Mapping[str, Any], field: str) -> None:
    if not isinstance(fixture[field], Mapping):
        raise VerticalFixtureSchemaError(f"Vertical fixture {field} must be a mapping.")
