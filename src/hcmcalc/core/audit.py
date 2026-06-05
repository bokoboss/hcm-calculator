"""Audit-oriented result structures."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class IntermediateValue:
    """Named intermediate value produced during a calculation."""

    name: str
    value: Any
    units: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class CalculationResult:
    """Auditable result container returned by calculation methods."""

    method: str
    facility_type: str
    outputs: dict[str, Any]
    intermediate_values: list[IntermediateValue] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AuditRecord:
    """Complete record suitable for validation and review."""

    case_id: str
    inputs: dict[str, Any]
    result: CalculationResult
