"""Supported workflow content for the app and documentation-oriented tests."""

from __future__ import annotations

from typing import Any, TypedDict


class WorkflowSection(TypedDict):
    """User-facing support scope for one workflow family."""

    title: str
    supported: list[str]
    limitations: list[str]
    save_load_export: str


APP_MODE_LABELS = (
    "Two-Lane Segment",
    "Two-Lane Facility",
    "Multilane Segment",
    "Basic Freeway Segment",
    "Supported Workflows",
)

APP_MODE_TO_VIEW = {
    "Supported Workflows": "supported_workflows",
    "Two-Lane Segment": "manual_single_segment",
    "Two-Lane Facility": "manual_facility",
    "Multilane Segment": "manual_multilane",
    "Basic Freeway Segment": "manual_basic_freeway",
}

INTERNAL_VALIDATION_QUERY_PARAM = "qa_view"
INTERNAL_VALIDATION_QUERY_VALUE = "validated_examples"


def resolve_app_view(mode_label: str, query_params: Any | None = None) -> str:
    """Resolve the active view, including internal QA-only routes."""

    if query_params is not None:
        requested_view = query_params.get(INTERNAL_VALIDATION_QUERY_PARAM)
        if isinstance(requested_view, list):
            requested_view = requested_view[0] if requested_view else None
        if requested_view == INTERNAL_VALIDATION_QUERY_VALUE:
            return INTERNAL_VALIDATION_QUERY_VALUE
    return APP_MODE_TO_VIEW[mode_label]

VALIDATION_EXPANDER_LABEL = "Validation basis and limitations"
CALCULATION_DETAILS_LABEL = "Calculation details"
AUDIT_EXPANDER_LABEL = "Audit / intermediate values"
STARTING_VALUES_LABEL = "Optional defaults"
PROJECT_LOAD_LABEL = "Load saved project"
PROJECT_OUTPUT_LABEL = "Project output"
EXPORT_REPORT_LABEL = "Export / Report"
STARTING_VALUES_CAPTION = (
    "Optional defaults only prefill supported inputs. You may edit values before "
    "running the calculation."
)
PRERUN_RESULTS_PLACEHOLDER = "Results will appear after calculation."
BASIC_FREEWAY_RAMP_DENSITY_LABEL = "Ramp density for FFS adjustment"
BASIC_FREEWAY_RAMP_DENSITY_HELP = (
    "Used for Basic Freeway speed adjustment only; not a ramp analysis workflow."
)

SUPPORTED_WORKFLOW_SECTIONS: tuple[WorkflowSection, ...] = (
    {
        "title": "Two-Lane Highway",
        "supported": [
            "Manual Single Segment Calculator",
            "Manual Facility Calculator",
            "validated Chapter 26 example-backed paths where available",
            "Project Save/Load and reporting exports",
        ],
        "limitations": [
            "implemented HCM7 Chapter 15 paths only",
            "unsupported combinations are guarded in the calculators",
        ],
        "save_load_export": (
            "Project JSON Save/Load and CSV, Excel, Markdown, and report JSON exports."
        ),
    },
    {
        "title": "Two-Lane Facility",
        "supported": [
            "Manual Facility Calculator",
            "Chapter 26 Example 3 and 4 facility-backed starting values",
            "guarded segment table edits",
        ],
        "limitations": [
            "not full general Chapter 15 facility support",
            "arbitrary segment sequences and passing-lane contexts remain guarded",
        ],
        "save_load_export": (
            "Project JSON Save/Load with table-oriented segment results and report exports."
        ),
    },
    {
        "title": "Multilane Highway",
        "supported": [
            "Manual Multilane Segment Calculator",
            "Chapter 26 Example 4 EB/WB-compatible validated path",
            "Metric/Imperial UI-boundary conversion",
            "Project Save/Load and reporting exports",
        ],
        "limitations": [
            "not a Basic Freeway calculator",
            "ramp, weaving, merge/diverge, and facility workflows are outside this page",
            "unsupported combinations are guarded in the calculator",
        ],
        "save_load_export": (
            "Project JSON Save/Load and CSV, Excel, Markdown, and report JSON exports."
        ),
    },
    {
        "title": "Basic Freeway",
        "supported": [
            "Manual Basic Freeway Segment Calculator",
            "Chapter 26 Example 1-compatible validated path",
            "Metric/Imperial UI-boundary conversion",
            "Project Save/Load and reporting exports",
        ],
        "limitations": [
            "not a general freeway facility calculator",
            "ramps, weaving, merge/diverge, managed lanes, work zones, reliability, and corridor workflows are outside this page",
        ],
        "save_load_export": (
            "Project JSON Save/Load and CSV, Excel, Markdown, and report JSON exports."
        ),
    },
    {
        "title": "Validation Evidence",
        "supported": [
            "Regression/reference evidence for implemented fixture cases",
            "Chapter 26 example-backed checks where available",
            "Internal QA review of validated case outputs",
        ],
        "limitations": [
            "not a user-facing workflow or product mode",
            "limited to implemented fixture cases",
        ],
        "save_load_export": (
            "Fixture-backed results remain available through internal QA access."
        ),
    },
)

EXAMPLE_WORKFLOW_NOTE = (
    "Validation examples provide regression and reference evidence for "
    "implemented fixture cases. They are not user-facing workflows: the product "
    "workflow is choose calculator, enter inputs, run calculation, review "
    "results, inspect audit, then save or export."
)

