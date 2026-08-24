"""Framework-independent application contracts for the rebuilt HCM workspace.

The application package owns stable workflow/state vocabulary and the backend
analysis registry.  It deliberately has no dependency on FastAPI, Streamlit,
React, or any other presentation framework.
"""

from .contracts import CalculationIdentity, CalculationState
from .interpretation import (
    CANONICAL_INTERPRETATION_CODES,
    Interpretation,
    InterpretationCode,
    interpretations_for_state,
)
from .registry import (
    AnalysisDefinition,
    AnalysisRegistry,
    get_analysis_definition,
    get_analysis_registry,
    list_analysis_definitions,
)
from .workflow_state import (
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

__all__ = [
    "AnalysisDefinition",
    "AnalysisRegistry",
    "CALCULATED",
    "CANONICAL_INTERPRETATION_CODES",
    "CalculationIdentity",
    "CalculationState",
    "Interpretation",
    "InterpretationCode",
    "MISSING_REQUIRED_INPUT",
    "READY",
    "ResultPresentationState",
    "STALE",
    "calculation_input_fingerprint",
    "get_analysis_definition",
    "get_analysis_registry",
    "interpretations_for_state",
    "is_current_calculation",
    "list_analysis_definitions",
    "mark_calculated",
    "normalized_input_fingerprint",
    "resolve_result_presentation_state",
    "workflow_status",
]
