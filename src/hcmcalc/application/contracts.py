"""Small, serializable contracts shared by application services and APIs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .workflow_state import ResultPresentationState, calculation_input_fingerprint


@dataclass(frozen=True)
class CalculationIdentity:
    """Identity of a calculation, independent from how it is presented."""

    method_identifier: str
    input_contract: str
    normalized_inputs: Mapping[str, Any]

    @property
    def fingerprint(self) -> str:
        """Return the canonical fingerprint for this method/input identity."""

        return calculation_input_fingerprint(
            self.method_identifier, self.input_contract, self.normalized_inputs
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "method_identifier": self.method_identifier,
            "input_contract": self.input_contract,
            "normalized_inputs": dict(self.normalized_inputs),
            "calculation_fingerprint": self.fingerprint,
        }


@dataclass(frozen=True)
class CalculationState:
    """Current presentation state for a stored or not-yet-run calculation."""

    presentation_state: ResultPresentationState
    calculation_fingerprint: str | None = None
    has_result: bool = False
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_current(self) -> bool:
        return self.presentation_state in {
            ResultPresentationState.VALID_CURRENT_RESULT,
            ResultPresentationState.VALID_CURRENT_RESULT_WITH_WARNING,
            ResultPresentationState.CAPACITY_FAILURE,
            ResultPresentationState.HCM_STOPPING_OR_HANDOFF,
        }

    @property
    def is_stale(self) -> bool:
        return self.presentation_state == ResultPresentationState.STALE_RESULT

    def to_mapping(self) -> dict[str, Any]:
        return {
            "presentation_state": self.presentation_state.value,
            "calculation_fingerprint": self.calculation_fingerprint,
            "has_result": self.has_result,
            "warnings": list(self.warnings),
        }
