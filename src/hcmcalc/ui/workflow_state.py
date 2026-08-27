"""Legacy compatibility imports for Streamlit workflow freshness state.

The canonical implementation now lives in :mod:`hcmcalc.application`, which
has no UI framework dependency. Keeping this module preserves all existing
``hcmcalc.ui.workflow_state`` imports while ensuring legacy and rebuilt flows
use the same fingerprint/state behavior.
"""

from __future__ import annotations

from hcmcalc.application.workflow_state import (
    CALCULATED,
    MISSING_REQUIRED_INPUT,
    READY,
    STALE,
    ResultPresentationState,
    calculation_input_fingerprint,
    is_current_calculation,
    mark_calculated,
    normalized_input_fingerprint,
    resolve_result_presentation_state,
    workflow_status,
)


def localized_workflow_status(status: str, locale: str | None = None) -> str:
    """Render a calculation status without changing its canonical value."""

    from hcmcalc.ui.i18n import translate

    keys = {
        READY: "status.ready",
        MISSING_REQUIRED_INPUT: "status.missing_required",
        CALCULATED: "status.calculated",
        STALE: "status.stale",
    }
    return translate(keys.get(status, "status.ready"), locale)


__all__ = [
    "CALCULATED",
    "MISSING_REQUIRED_INPUT",
    "READY",
    "STALE",
    "ResultPresentationState",
    "calculation_input_fingerprint",
    "is_current_calculation",
    "localized_workflow_status",
    "mark_calculated",
    "normalized_input_fingerprint",
    "resolve_result_presentation_state",
    "workflow_status",
]
