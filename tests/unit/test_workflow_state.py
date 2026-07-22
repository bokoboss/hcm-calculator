import math

from hcmcalc.ui.manual_facility import canonicalize_manual_facility_rows
from hcmcalc.ui.workflow_state import (
    CALCULATED,
    MISSING_REQUIRED_INPUT,
    READY,
    STALE,
    calculation_input_fingerprint,
    is_current_calculation,
    mark_calculated,
    normalized_input_fingerprint,
    workflow_status,
    ResultPresentationState,
    resolve_result_presentation_state,
)


def test_fingerprint_is_deterministic_and_does_not_mutate_inputs() -> None:
    inputs = {"speed": 55.0, "segments": [{"id": 1, "length": 1.5}]}
    equivalent = {"segments": [{"length": 1.5, "id": 1}], "speed": 55.0}

    assert normalized_input_fingerprint(inputs) == normalized_input_fingerprint(equivalent)
    assert inputs == {"speed": 55.0, "segments": [{"id": 1, "length": 1.5}]}


def test_facility_fingerprint_ignores_inactive_opposing_nan_after_canonicalization() -> None:
    rows_with_nan = canonicalize_manual_facility_rows(
        [
            {
                "segment_id": 1,
                "segment_type": "passing_constrained",
                "opposing_direction_volume_veh_h": math.nan,
            },
            {
                "segment_id": 2,
                "segment_type": "passing_zone",
                "opposing_direction_volume_veh_h": 500.0,
            },
        ]
    )
    rows_without_nan = canonicalize_manual_facility_rows(
        [
            {
                "segment_id": 1,
                "segment_type": "passing_constrained",
                "opposing_direction_volume_veh_h": None,
            },
            {
                "segment_id": 2,
                "segment_type": "passing_zone",
                "opposing_direction_volume_veh_h": 500.0,
            },
        ]
    )
    changed_active = canonicalize_manual_facility_rows(
        [
            {
                "segment_id": 1,
                "segment_type": "passing_constrained",
                "opposing_direction_volume_veh_h": math.nan,
            },
            {
                "segment_id": 2,
                "segment_type": "passing_zone",
                "opposing_direction_volume_veh_h": 575.0,
            },
        ]
    )

    assert normalized_input_fingerprint(rows_with_nan) == normalized_input_fingerprint(
        rows_without_nan
    )
    assert normalized_input_fingerprint(rows_with_nan) != normalized_input_fingerprint(
        changed_active
    )


def test_workflow_status_transitions_are_session_scoped() -> None:
    state: dict[str, object] = {}
    inputs = {"speed": 55.0, "unit_system": "imperial"}

    assert workflow_status(state, "two_lane", inputs, required_fields=("speed",)) == READY
    assert workflow_status(state, "two_lane", {"speed": None}, required_fields=("speed",)) == MISSING_REQUIRED_INPUT

    mark_calculated(state, "two_lane", inputs)
    assert workflow_status(state, "two_lane", inputs) == CALCULATED
    assert is_current_calculation(state, "two_lane", inputs)
    assert workflow_status(state, "two_lane", {**inputs, "speed": 56.0}) == STALE
    assert not is_current_calculation(state, "two_lane", {**inputs, "speed": 56.0})


def test_each_workflow_keeps_its_own_calculation_fingerprint() -> None:
    state: dict[str, object] = {}
    inputs = {"speed": 55.0}
    mark_calculated(state, "two_lane", inputs)

    assert workflow_status(state, "multilane", inputs) == READY


def test_calculation_fingerprint_includes_method_and_contract() -> None:
    inputs = {"demand_volume_veh_h": 900.0}
    baseline = calculation_input_fingerprint("multilane", "phase_8", inputs)

    assert baseline != calculation_input_fingerprint("freeway", "phase_8", inputs)
    assert baseline != calculation_input_fingerprint("multilane", "phase_10", inputs)
    assert baseline == calculation_input_fingerprint(
        "multilane", "phase_8", {"demand_volume_veh_h": 900.0}
    )


def test_result_presentation_states_distinguish_engine_failure_from_ui_errors() -> None:
    assert resolve_result_presentation_state(freshness=READY) == ResultPresentationState.PRERUN
    assert resolve_result_presentation_state(freshness=STALE, has_result=True) == ResultPresentationState.STALE_RESULT
    assert resolve_result_presentation_state(freshness=CALCULATED, has_result=True, capacity_failure=True) == ResultPresentationState.CAPACITY_FAILURE
    assert resolve_result_presentation_state(freshness=CALCULATED, stopping_or_handoff=True) == ResultPresentationState.HCM_STOPPING_OR_HANDOFF
    assert resolve_result_presentation_state(freshness=MISSING_REQUIRED_INPUT) == ResultPresentationState.INVALID_INPUT
