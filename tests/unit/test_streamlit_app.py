from hcmcalc.ui.result_view import compact_rows, format_display_metric, los_colors
from hcmcalc.ui.schematics import get_segment_schematic_path
from hcmcalc.ui.manual_facility import clear_manual_facility_result_state


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
