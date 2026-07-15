"""Small shared guards for UI-boundary input contracts.

These helpers deliberately validate representation only.  Method-specific
normalization and HCM applicability remain in their respective adapters and
engines.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from math import isfinite
from numbers import Real
from typing import Any


def reject_unknown_keys(
    values: Mapping[str, Any], allowed_keys: Iterable[str], context: str
) -> None:
    """Reject UI state that does not belong to the selected worksheet."""

    unknown_keys = sorted(set(values) - set(allowed_keys))
    if unknown_keys:
        raise ValueError(f"Unrecognized {context} inputs: " + ", ".join(unknown_keys))


def require_finite_number(name: str, value: Any) -> float:
    """Return a finite number while rejecting bool, NaN, and infinity."""

    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
        raise ValueError(f"{name} must be a finite numeric value.")
    return float(value)
