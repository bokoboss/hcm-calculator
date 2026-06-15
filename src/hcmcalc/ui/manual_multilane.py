"""Streamlit-independent adapter for the guarded Multilane v0.1 worksheet."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from hcmcalc.cli import find_case, load_input_file
from hcmcalc.multilane import MultilaneHighwayLOSMethod


ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = ROOT / "references" / "multilane_example_inputs.yaml"
TEMPLATE_LABELS = {
    "MLH-CH26-004-EB": "Chapter 26 Example 4 EB",
    "MLH-CH26-004-WB": "Chapter 26 Example 4 WB",
}


def multilane_template_options() -> dict[str, str]:
    """Return the two validated Multilane starter templates."""

    return dict(TEMPLATE_LABELS)


def load_multilane_template(case_id: str) -> dict[str, Any]:
    """Load a copy of a validated Example Problem 4 input template."""

    if case_id not in TEMPLATE_LABELS:
        raise ValueError(f"Unsupported Multilane template: {case_id}.")
    case = find_case(load_input_file(FIXTURE_PATH), case_id)
    return {
        "case_id": case_id,
        "template_label": TEMPLATE_LABELS[case_id],
        "description": case["description"],
        "validation_status": case["validation_status"],
        "inputs": deepcopy(case["inputs"]),
    }


def run_manual_multilane(inputs: dict[str, Any]):
    """Run submitted worksheet values through the existing Multilane engine."""

    return MultilaneHighwayLOSMethod().calculate(inputs)


def build_manual_multilane_audit_record(
    template_id: str,
    inputs: dict[str, Any],
    *,
    result: Any | None = None,
    error: Exception | None = None,
) -> dict[str, Any]:
    """Build a compact audit record without adding calculation behavior."""

    return {
        "calculation_type": "manual_multilane_segment_v0_1",
        "template_id": template_id,
        "unit_system": "imperial",
        "support_status": "implemented_example_only",
        "submitted_inputs": deepcopy(inputs),
        "calculation_succeeded": result is not None,
        "validation_error": str(error) if error is not None else None,
    }
