"""Core contracts for auditable HCM calculation methods."""

from .audit import AuditRecord, CalculationResult, IntermediateValue
from .exceptions import HCMCalcError, MethodNotImplementedError, UnsupportedScopeError
from .interfaces import CalculationMethod

__all__ = [
    "AuditRecord",
    "CalculationMethod",
    "CalculationResult",
    "HCMCalcError",
    "IntermediateValue",
    "MethodNotImplementedError",
    "UnsupportedScopeError",
]
