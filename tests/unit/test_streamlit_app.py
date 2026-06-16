from hcmcalc.ui.result_view import compact_rows, format_display_metric, los_colors
from hcmcalc.ui.schematics import get_segment_schematic_path
from hcmcalc.ui.manual_facility import clear_manual_facility_result_state
from hcmcalc.ui.supported_workflows import (
    APP_MODE_LABELS,
    APP_MODE_TO_VIEW,
    AUDIT_EXPANDER_LABEL,
    BASIC_FREEWAY_RAMP_DENSITY_HELP,
    BASIC_FREEWAY_RAMP_DENSITY_LABEL,
    CALCULATION_DETAILS_LABEL,
    EXPORT_REPORT_LABEL,
    EXAMPLE_WORKFLOW_NOTE,
    PROJECT_LOAD_LABEL,
    PROJECT_OUTPUT_LABEL,
    PRERUN_RESULTS_PLACEHOLDER,
    STARTING_VALUES_CAPTION,
    STARTING_VALUES_LABEL,
    SUPPORTED_WORKFLOW_SECTIONS,
    VALIDATION_EXPANDER_LABEL,
)


def test_supported_segment_types_map_to_existing_schematics() -> None:
    expected_filenames = {
        "passing_constrained": "passing_constrained.png",
        "passing_zone": "passing_zone.png",
        "passing_lane": "passing_lane.png",
    }

    for segment_type, expected_filename in expected_filenames.items():
        schematic_path = get_segment_schematic_path(segment_type)

        assert schematic_path is not None
        assert schematic_path.name == expected_filename
        assert schematic_path.is_file()


def test_unknown_segment_type_has_no_schematic() -> None:
    assert get_segment_schematic_path("unknown") is None


def test_required_two_lane_schematic_assets_exist() -> None:
    schematic_paths = {
        get_segment_schematic_path(segment_type)
        for segment_type in ("passing_constrained", "passing_zone", "passing_lane")
    }

    assert {path.name for path in schematic_paths if path is not None} == {
        "passing_constrained.png",
        "passing_zone.png",
        "passing_lane.png",
    }
    assert all(path is not None and path.is_file() for path in schematic_paths)


def test_compact_rows_excludes_nested_outputs() -> None:
    outputs = {
        "level_of_service": "D",
        "average_speed_mph": 45.2,
        "segments": [{"segment_id": 1}],
        "metadata": {"status": "validated"},
    }

    assert compact_rows(outputs) == [
        {"output": "level_of_service", "value": "D"},
        {"output": "average_speed_mph", "value": 45.2},
    ]


def test_los_colors_use_distinct_professional_palette() -> None:
    assert los_colors("A") == ("#17643a", "#e8f4ec")
    assert los_colors("F") == ("#721c24", "#f5dddd")
    assert los_colors("unknown") == ("#374151", "#f3f4f6")


def test_primary_metric_formatting_is_consistent() -> None:
    assert format_display_metric(
        "average_speed", {"value": 80.4672, "unit": "km/h"}, "metric"
    ) == "80.5 km/h"
    assert format_display_metric(
        "follower_density", {"value": 12.345, "unit": "fol/km/ln"}, "metric"
    ) == "12.35 fol/km/ln"
    assert format_display_metric(
        "follower_density", {"value": 12.345, "unit": "fol/mi/ln"}, "imperial"
    ) == "12.3 fol/mi/ln"
    assert format_display_metric(
        "demand_flow_rate", {"value": 800.0, "unit": "veh/h"}, "metric"
    ) == "800 veh/h"


def test_template_switching_clears_stale_facility_results() -> None:
    state = {
        "manual_facility_result": {"outputs": {}},
        "manual_facility_result_context": ("level_example_3", "imperial"),
        "manual_facility_result_rows": [{"segment_id": 1}],
        "manual_facility_audit": {"template_id": "level_example_3"},
        "manual_facility_error": "old error",
        "unrelated": "preserved",
    }

    clear_manual_facility_result_state(state)

    assert state == {"unrelated": "preserved"}


def test_app_mode_list_includes_supported_workflows() -> None:
    assert APP_MODE_LABELS == (
        "Two-Lane Segment",
        "Two-Lane Facility",
        "Multilane Segment",
        "Basic Freeway Segment",
        "Supported Workflows",
        "Validation Examples",
    )
    assert APP_MODE_TO_VIEW["Supported Workflows"] == "supported_workflows"
    assert APP_MODE_TO_VIEW["Two-Lane Segment"] == "manual_single_segment"
    assert APP_MODE_TO_VIEW["Basic Freeway Segment"] == "manual_basic_freeway"


def test_calculator_ui_shared_grammar_labels_are_standardized() -> None:
    assert VALIDATION_EXPANDER_LABEL == "Validation basis and limitations"
    assert CALCULATION_DETAILS_LABEL == "Calculation details"
    assert AUDIT_EXPANDER_LABEL == "Audit / intermediate values"
    assert STARTING_VALUES_LABEL == "Optional defaults"
    assert PROJECT_LOAD_LABEL == "Load saved project"
    assert PROJECT_OUTPUT_LABEL == "Project output"
    assert EXPORT_REPORT_LABEL == "Export / Report"
    assert PRERUN_RESULTS_PLACEHOLDER == "Results will appear after calculation."
    assert STARTING_VALUES_CAPTION == (
        "Optional defaults only prefill supported inputs. You may edit values before "
        "running the calculation."
    )
    assert BASIC_FREEWAY_RAMP_DENSITY_LABEL == "Ramp density for FFS adjustment"
    assert BASIC_FREEWAY_RAMP_DENSITY_HELP == (
        "Used for Basic Freeway speed adjustment only; not a ramp analysis workflow."
    )


def test_supported_workflows_content_names_current_scope() -> None:
    sections = {section["title"]: section for section in SUPPORTED_WORKFLOW_SECTIONS}

    assert set(sections) == {
        "Two-Lane Highway",
        "Two-Lane Facility",
        "Multilane Highway",
        "Basic Freeway",
        "Examples / Validation",
    }
    assert "Manual Single Segment Calculator" in sections["Two-Lane Highway"]["supported"]
    assert "Manual Facility Calculator" in sections["Two-Lane Facility"]["supported"]
    assert "Save/Load" in sections["Two-Lane Highway"]["save_load_export"]
    assert (
        "Chapter 26 Example 4 EB/WB-compatible validated path"
        in sections["Multilane Highway"]["supported"]
    )
    assert (
        "Chapter 26 Example 1-compatible validated path"
        in sections["Basic Freeway"]["supported"]
    )
    assert "not a general freeway facility calculator" in sections["Basic Freeway"]["limitations"]
    assert "not a Basic Freeway calculator" in sections["Multilane Highway"]["limitations"]
    assert "Reference-backed checks" in sections["Examples / Validation"]["supported"]
    assert "not the main product model" in EXAMPLE_WORKFLOW_NOTE
