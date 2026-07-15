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
)


def test_fingerprint_is_deterministic_and_does_not_mutate_inputs() -> None:
    inputs = {"speed": 55.0, "segments": [{"id": 1, "length": 1.5}]}
    equivalent = {"segments": [{"length": 1.5, "id": 1}], "speed": 55.0}

    assert normalized_input_fingerprint(inputs) == normalized_input_fingerprint(equivalent)
    assert inputs == {"speed": 55.0, "segments": [{"id": 1, "length": 1.5}]}


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
