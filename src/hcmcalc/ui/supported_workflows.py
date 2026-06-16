"""Supported workflow content for the app and documentation-oriented tests."""

from __future__ import annotations

from typing import TypedDict


class WorkflowSection(TypedDict):
    """User-facing support scope for one workflow family."""

    title: str
    supported: list[str]
    limitations: list[str]


APP_MODE_LABELS = (
    "Supported Workflows",
    "Two-Lane Segment",
    "Two-Lane Facility",
    "Multilane Segment",
    "Basic Freeway Segment",
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

SUPPORTED_WORKFLOW_SECTIONS: tuple[WorkflowSection, ...] = (
    {
        "title": "Two-Lane Highway",
        "supported": [
            "Manual Single Segment Calculator",
            "Manual Facility Calculator",
            "validated Chapter 26 example-backed paths where available",
            "Save/Load",
            "Export/reporting",
        ],
        "limitations": [
            "only implemented HCM7 Chapter 15 paths",
            "unsupported combinations remain guarded",
        ],
    },
    {
        "title": "Multilane Highway",
        "supported": [
            "Manual Multilane Segment Calculator",
            "Chapter 26 Example 4 EB/WB-compatible validated path",
            "Metric/Imperial UI-boundary conversion",
            "Save/Load",
            "Export/reporting",
        ],
        "limitations": [
            "not a Basic Freeway calculator",
            "not ramp/weaving/merge/diverge/facility workflow",
            "unsupported combinations remain guarded",
        ],
    },
    {
        "title": "Basic Freeway",
        "supported": [
            "Manual Basic Freeway Segment Calculator",
            "Chapter 26 Example 1-compatible validated path",
            "Metric/Imperial UI-boundary conversion",
            "Save/Load",
            "Export/reporting",
        ],
        "limitations": [
            "not a general freeway facility calculator",
            "no ramps",
            "no weaving",
            "no merge/diverge",
            "no managed lanes",
            "no work zones",
            "no reliability",
            "no facility/corridor workflow",
        ],
    },
)

EXAMPLE_WORKFLOW_NOTE = (
    "Example and validation workflows provide validation references and starting "
    "values. They are not the main product model: the calculator workflow is "
    "choose calculator, enter inputs, run calculation, review results, inspect "
    "audit, then save or export."
)

