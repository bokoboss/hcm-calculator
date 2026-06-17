"""Supported workflow content for the app and documentation-oriented tests."""

from __future__ import annotations

from typing import TypedDict


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
    "Validation Examples",
)

APP_MODE_TO_VIEW = {
    "Supported Workflows": "supported_workflows",
    "Two-Lane Segment": "manual_single_segment",
    "Two-Lane Facility": "manual_facility",
    "Multilane Segment": "manual_multilane",
    "Basic Freeway Segment": "manual_basic_freeway",
    "Validation Examples": "validated_examples",
}

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
        "title": "Examples / Validation",
        "supported": [
            "Validation examples",
            "Reference-backed checks",
            "Example-backed regression cases",
        ],
        "limitations": [
            "not the primary calculator data-entry workflow",
            "limited to implemented fixture cases",
        ],
        "save_load_export": (
            "Selected-case result JSON remains available where current result rendering supports it."
        ),
    },
)

EXAMPLE_WORKFLOW_NOTE = (
    "Example and validation workflows provide validation references and starting "
    "values. They are not the main product model: the calculator workflow is "
    "choose calculator, enter inputs, run calculation, review results, inspect "
    "audit, then save or export."
)

