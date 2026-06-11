"""Input helpers for the manual horizontal-curve editor."""

from __future__ import annotations

from typing import Any

from hcmcalc.core import HCMCalcError
from hcmcalc.ui.units import FEET_TO_METERS


DEFAULT_CURVE_SUBSEGMENT_COUNT = 11
MAX_CURVE_SUBSEGMENT_COUNT = 100


def curve_setup_defaults(
    unit_system: str, segment_length: float
) -> dict[str, float | int]:
    """Return user-facing defaults for the compact curve setup editor."""

    metric = str(unit_system).strip().lower() == "metric"
    total_curve_length = float(segment_length) * (1000.0 if metric else 5280.0)
    return {
        "total_curve_length": total_curve_length,
        "radius": 450.0 * FEET_TO_METERS if metric else 450.0,
        "superelevation_percent": 3.0,
        "central_angle_deg": 55.0,
        "horizontal_class": 3,
        "subsegment_count": DEFAULT_CURVE_SUBSEGMENT_COUNT,
    }


def generate_curve_subsegments(curve_setup: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate evenly distributed rows for the existing engine input path."""

    total_length = _positive_float(curve_setup, "total_curve_length", "curve length")
    radius = _positive_float(curve_setup, "radius", "curve radius")
    count = _subsegment_count(curve_setup.get("subsegment_count"))
    row_length = total_length / count
    central_angle = _float_value(curve_setup, "central_angle_deg", "central angle")

    return [
        {
            "type": "horizontal_curve",
            "length": row_length,
            "superelevation_percent": _float_value(
                curve_setup, "superelevation_percent", "superelevation"
            ),
            "radius": radius,
            "central_angle_deg": central_angle,
            "horizontal_class": _horizontal_class(
                curve_setup.get("horizontal_class")
            ),
        }
        for _ in range(count)
    ]


def validate_curve_setup(curve_setup: dict[str, Any]) -> None:
    """Validate an optional saved curve setup object."""

    if not isinstance(curve_setup, dict):
        raise HCMCalcError("curve_setup must be an object.")
    generate_curve_subsegments(curve_setup)


def _subsegment_count(value: Any) -> int:
    try:
        count = int(value)
    except (TypeError, ValueError) as exc:
        raise HCMCalcError("Number of subsegments must be a whole number.") from exc
    if isinstance(value, float) and not value.is_integer():
        raise HCMCalcError("Number of subsegments must be a whole number.")
    if count < 1 or count > MAX_CURVE_SUBSEGMENT_COUNT:
        raise HCMCalcError(
            f"Number of subsegments must be between 1 and "
            f"{MAX_CURVE_SUBSEGMENT_COUNT}."
        )
    return count


def _horizontal_class(value: Any) -> int:
    try:
        horizontal_class = int(value)
    except (TypeError, ValueError) as exc:
        raise HCMCalcError("Horizontal class must be a whole number.") from exc
    if horizontal_class not in range(1, 6):
        raise HCMCalcError("Horizontal class must be 1 through 5.")
    return horizontal_class


def _positive_float(values: dict[str, Any], key: str, label: str) -> float:
    value = _float_value(values, key, label)
    if value <= 0.0:
        raise HCMCalcError(f"{label.title()} must be positive.")
    return value


def _float_value(values: dict[str, Any], key: str, label: str) -> float:
    try:
        return float(values[key])
    except KeyError as exc:
        raise HCMCalcError(f"Curve setup requires {label}.") from exc
    except (TypeError, ValueError) as exc:
        raise HCMCalcError(f"{label.title()} must be numeric.") from exc
