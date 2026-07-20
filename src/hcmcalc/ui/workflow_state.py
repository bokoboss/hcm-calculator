"""Framework-independent calculation freshness state for UI workflows."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from hashlib import sha256
import json
from enum import StrEnum
from typing import Any


READY = "Ready"
MISSING_REQUIRED_INPUT = "Missing required input"
CALCULATED = "Calculated"
STALE = "Input changed — recalculate required"

_STATE_KEY = "calculation_workflow_state"


class ResultPresentationState(StrEnum):
    """Streamlit-independent states used to present a calculator outcome."""

    PRERUN = "prerun"
    VALID_CURRENT_RESULT = "valid_current_result"
    VALID_CURRENT_RESULT_WITH_WARNING = "valid_current_result_with_warning"
    CAPACITY_FAILURE = "capacity_failure"
    HCM_STOPPING_OR_HANDOFF = "hcm_stopping_or_handoff"
    STALE_RESULT = "stale_result"
    INVALID_INPUT = "invalid_input"
    UNSUPPORTED_SCOPE = "unsupported_scope"
    INTERNAL_ERROR = "internal_error"


def resolve_result_presentation_state(
    *,
    freshness: str,
    has_result: bool = False,
    warnings: Sequence[str] = (),
    capacity_failure: bool = False,
    stopping_or_handoff: bool = False,
    unsupported_scope: bool = False,
    internal_error: bool = False,
) -> ResultPresentationState:
    """Classify UI presentation without altering engine result contracts."""

    if internal_error:
        return ResultPresentationState.INTERNAL_ERROR
    if unsupported_scope:
        return ResultPresentationState.UNSUPPORTED_SCOPE
    if stopping_or_handoff:
        return ResultPresentationState.HCM_STOPPING_OR_HANDOFF
    if freshness == MISSING_REQUIRED_INPUT:
        return ResultPresentationState.INVALID_INPUT
    if freshness == STALE:
        return ResultPresentationState.STALE_RESULT
    if capacity_failure:
        return ResultPresentationState.CAPACITY_FAILURE
    if has_result and warnings:
        return ResultPresentationState.VALID_CURRENT_RESULT_WITH_WARNING
    if has_result:
        return ResultPresentationState.VALID_CURRENT_RESULT
    return ResultPresentationState.PRERUN


def normalized_input_fingerprint(inputs: Mapping[str, Any]) -> str:
    """Return a stable fingerprint without changing the supplied inputs."""

    payload = json.dumps(
        _normalize(inputs), sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def calculation_input_fingerprint(
    method_identifier: str, input_contract: str, inputs: Mapping[str, Any]
) -> str:
    """Fingerprint a result identity including method and input contract."""

    if not isinstance(method_identifier, str) or not method_identifier.strip():
        raise ValueError("method_identifier must be a nonempty string.")
    if not isinstance(input_contract, str) or not input_contract.strip():
        raise ValueError("input_contract must be a nonempty string.")
    return normalized_input_fingerprint(
        {
            "method_identifier": method_identifier,
            "input_contract": input_contract,
            "inputs": inputs,
        }
    )


def workflow_status(
    session_state: Mapping[str, Any], workflow: str, inputs: Mapping[str, Any], *,
    required_fields: Sequence[str] = (),
) -> str:
    """Return the shared visible status for one session-scoped workflow."""

    if any(_is_missing(inputs.get(field)) for field in required_fields):
        return MISSING_REQUIRED_INPUT
    calculated = session_state.get(_STATE_KEY, {}).get(workflow)
    if not isinstance(calculated, Mapping):
        return READY
    return (
        CALCULATED
        if calculated.get("fingerprint") == normalized_input_fingerprint(inputs)
        else STALE
    )


def localized_workflow_status(status: str, locale: str | None = None) -> str:
    """Render a calculation status without changing its canonical state value."""

    from hcmcalc.ui.i18n import translate

    keys = {
        READY: "status.ready",
        MISSING_REQUIRED_INPUT: "status.missing_required",
        CALCULATED: "status.calculated",
        STALE: "status.stale",
    }
    return translate(keys.get(status, "status.ready"), locale)


def mark_calculated(
    session_state: MutableMapping[str, Any], workflow: str, inputs: Mapping[str, Any]
) -> None:
    """Capture the successful calculation fingerprint in session state only."""

    records = session_state.setdefault(_STATE_KEY, {})
    records[workflow] = {"fingerprint": normalized_input_fingerprint(inputs)}


def is_current_calculation(
    session_state: Mapping[str, Any], workflow: str, inputs: Mapping[str, Any], *,
    required_fields: Sequence[str] = (),
) -> bool:
    """Whether exports may represent the stored result as current."""

    return workflow_status(
        session_state, workflow, inputs, required_fields=required_fields
    ) == CALCULATED


def _normalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _normalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if isinstance(value, float):
        return format(value, ".17g")
    if value is None or isinstance(value, (str, int, bool)):
        return value
    return str(value)


def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())
