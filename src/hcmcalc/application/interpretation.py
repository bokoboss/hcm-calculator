"""Canonical, language-neutral interpretation-code foundation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable

from .workflow_state import ResultPresentationState


class InterpretationCode(StrEnum):
    """Stable codes; localized text belongs to the presentation layer."""

    CAPACITY_BELOW_LIMIT = "capacity_below_limit"
    CAPACITY_EXCEEDED = "capacity_exceeded"
    RESULT_STALE = "result_stale"
    FACILITY_LENGTH_WEIGHTED = "facility_length_weighted"
    FACILITY_CRITICAL_SEGMENT = "facility_critical_segment"
    WEAVING_HANDOFF = "weaving_handoff"
    UNAVAILABLE_RESULT = "unavailable_result"


CANONICAL_INTERPRETATION_CODES = tuple(code.value for code in InterpretationCode)


@dataclass(frozen=True)
class Interpretation:
    """A deterministic interpretation reference with no localized prose."""

    code: InterpretationCode
    severity: str = "informational"
    message_key: str = ""
    source_basis: str | None = None

    def to_mapping(self) -> dict[str, str | None]:
        return {
            "code": self.code.value,
            "severity": self.severity,
            "message_key": self.message_key,
            "source_basis": self.source_basis,
        }


def interpretations_for_state(
    state: ResultPresentationState,
    *,
    warning_codes: Iterable[InterpretationCode] = (),
) -> tuple[Interpretation, ...]:
    """Map canonical application states to safe, testable code references."""

    interpretations: list[Interpretation] = []
    if state == ResultPresentationState.STALE_RESULT:
        interpretations.append(
            Interpretation(
                InterpretationCode.RESULT_STALE,
                severity="blocking",
                message_key="interpretation.result_stale",
            )
        )
    elif state == ResultPresentationState.CAPACITY_FAILURE:
        interpretations.append(
            Interpretation(
                InterpretationCode.CAPACITY_EXCEEDED,
                severity="engineering_warning",
                message_key="interpretation.capacity_exceeded",
            )
        )
    elif state == ResultPresentationState.HCM_STOPPING_OR_HANDOFF:
        interpretations.append(
            Interpretation(
                InterpretationCode.WEAVING_HANDOFF,
                severity="handoff",
                message_key="interpretation.weaving_handoff",
            )
        )
    elif state in {
        ResultPresentationState.INVALID_INPUT,
        ResultPresentationState.UNSUPPORTED_SCOPE,
        ResultPresentationState.INTERNAL_ERROR,
    }:
        interpretations.append(
            Interpretation(
                InterpretationCode.UNAVAILABLE_RESULT,
                severity="blocking",
                message_key="interpretation.unavailable_result",
            )
        )

    interpretations.extend(
        Interpretation(
            code,
            severity="informational",
            message_key=f"interpretation.{code.value}",
        )
        for code in warning_codes
    )
    return tuple(interpretations)
