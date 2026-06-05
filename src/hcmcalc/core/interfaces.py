"""Shared interfaces for calculation methods."""

from typing import Any, Protocol

from .audit import CalculationResult


class CalculationMethod(Protocol):
    """Protocol implemented by facility-specific methods."""

    facility_type: str
    method_name: str

    def calculate(self, inputs: dict[str, Any]) -> CalculationResult:
        """Run a calculation and return an auditable result."""
