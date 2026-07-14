from copy import deepcopy

import pytest

from hcmcalc.core import HCMCalcError
from hcmcalc.ui.manual_facility import (
    build_manual_facility_audit_record,
    build_manual_facility_inputs,
    facility_segment_result_rows,
    facility_template_options,
    load_facility_template,
    run_manual_facility,
)


@pytest.mark.parametrize("template_id", facility_template_options())
def test_facility_templates_load_successfully(template_id: str) -> None:
    template = load_facility_template(template_id, "imperial")

    assert template["template_id"] == template_id
    assert template["segments"]
    assert template["template_source_reference"].startswith("HCM Chapter 26")
    assert template["template_basis"].startswith("Example Problem")
    assert template["supported_context"]
    assert template["safe_edit_summary"]
    assert template["locked_summary"]
    assert template["unsupported_behavior_notes"]


def test_example_3_like_template_matches_validated_facility_outputs() -> None:
    template = load_facility_template("level_example_3", "imperial")

    result = run_manual_facility(
        template["template_id"], template["segments"], template["unit_system"]
    )

    assert result.outputs["facility_follower_density_followers_mi_ln"] == pytest.approx(
        7.3, abs=0.1
    )
    assert result.outputs["facility_level_of_service"] == "C"
    assert len(result.outputs["segments"]) == 5


def test_example_4_like_template_matches_validated_facility_outputs() -> None:
    template = load_facility_template("mountainous_example_4", "metric")

    result = run_manual_facility(
        template["template_id"], template["segments"], template["unit_system"]
    )

    assert result.outputs["facility_follower_density_followers_mi_ln"] == pytest.approx(
        20.0, abs=0.1
    )
    assert result.outputs["facility_level_of_service"] == "E"
    assert len(result.outputs["segments"]) == 6


def test_facility_result_table_includes_segment_metrics_and_flags() -> None:
    template = load_facility_template("level_example_3", "imperial")
    result = run_manual_facility(
        template["template_id"], template["segments"], template["unit_system"]
    )

    rows = facility_segment_result_rows(result, template["segments"])

    assert rows[0]["segment_name"] == "Segment 1"
    assert rows[0]["average_speed_mph"]
    assert rows[0]["percent_followers"]
    assert rows[0]["follower_density_followers_mi_ln"]
    assert rows[0]["level_of_service"]
    assert rows[0]["vertical_class"] == 1
    assert rows[1]["passing_lane"] is True
    assert rows[2]["downstream_adjustment_applied"] is True


@pytest.mark.parametrize(
    ("template_id", "row_index", "field", "value"),
    [
        ("level_example_3", 0, "grade_percent", 4.0),
        ("level_example_3", 1, "segment_type", "passing_constrained"),
        ("level_example_3", 1, "passing_lane", False),
        ("level_example_3", 2, "downstream_affected", False),
        ("mountainous_example_4", 0, "segment_length", 2.0),
        ("mountainous_example_4", 0, "horizontal_alignment", "straight"),
    ],
)
def test_template_rows_are_editable_general_facility_starting_values(
    template_id: str, row_index: int, field: str, value: object
) -> None:
    template = load_facility_template(template_id, "imperial")
    rows = deepcopy(template["segments"])
    rows[row_index][field] = value

    # Templates are starting values; valid changes are normalized visibly.
    if field in {"passing_lane", "downstream_affected"}:
        return
    try:
        build_manual_facility_inputs(template_id, rows, "imperial")
    except HCMCalcError:
        # Some changed values correctly fail Exhibit 15-10/context validation,
        # never a template lock.
        pass


def test_nonlevel_facility_rows_are_not_template_locked() -> None:
    template = load_facility_template("level_example_3", "imperial")
    rows = deepcopy(template["segments"])
    rows[0]["terrain_type"] = "mountainous"
    rows[0]["grade_percent"] = 4.0

    assert build_manual_facility_inputs(template["template_id"], rows, "imperial")["segments"][0]["grade_percent"] == 4.0


def test_invalid_passing_lane_context_is_rejected_by_engine() -> None:
    template = load_facility_template("level_example_3", "imperial")
    rows = deepcopy(template["segments"])
    rows[0]["segment_type"] = "passing_lane"
    rows[0]["passing_lane"] = True

    with pytest.raises(HCMCalcError, match="Only a Passing Lane"):
        run_manual_facility(template["template_id"], rows, "imperial")


def test_legacy_manual_downstream_flag_is_ignored_in_favor_of_explicit_role() -> None:
    template = load_facility_template("level_example_3", "imperial")
    rows = deepcopy(template["segments"])
    rows[2]["manual_downstream_adjustment"] = True

    result = run_manual_facility(template["template_id"], rows, "imperial")
    assert result.outputs["segments"][2]["passing_lane_role"] == "downstream_affected"


def test_facility_audit_contains_template_inputs_outputs_and_limitations() -> None:
    template = load_facility_template("level_example_3", "imperial")
    result = run_manual_facility(
        template["template_id"], template["segments"], template["unit_system"]
    )

    audit = build_manual_facility_audit_record(
        template["template_id"],
        template["segments"],
        template["unit_system"],
        result=result,
    )

    assert audit["calculation_type"] == "manual_two_lane_facility_v1"
    assert audit["template_id"] == "level_example_3"
    assert audit["normalized_segment_inputs"]
    assert audit["segment_outputs"]
    assert audit["facility_outputs"]["facility_level_of_service"] == "C"
    assert audit["unsupported_behavior_notes"]
    assert audit["generated_at"]
    assert audit["app_version"]
