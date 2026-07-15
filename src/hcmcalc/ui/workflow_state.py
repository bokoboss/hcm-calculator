"""Framework-independent calculation freshness state for UI workflows."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from hashlib import sha256
import json
from typing import Any


READY = "Ready"
MISSING_REQUIRED_INPUT = "Missing required input"
CALCULATED = "Calculated"
STALE = "Input changed — recalculate required"

_STATE_KEY = "calculation_workflow_state"


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
