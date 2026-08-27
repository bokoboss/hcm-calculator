import ast
from pathlib import Path

import pytest

from hcmcalc.freeway import BasicFreewaySegmentMethod
from hcmcalc.multilane import MultilaneHighwayLOSMethod
from hcmcalc.application import (
    CalculationState,
    CalculationIdentity,
    InterpretationCode,
    ResultPresentationState,
    calculation_input_fingerprint,
    get_analysis_definition,
    list_analysis_definitions,
    normalized_input_fingerprint,
    interpretations_for_state,
    resolve_result_presentation_state,
)
from hcmcalc.methods.two_lane_highway_ch15 import TwoLaneHighwayChapter15Method
from hcmcalc.ramp_influence.diverge.v7_0.method import HCM70DivergeSegmentMethod
from hcmcalc.ramp_influence.merge.v7_0.method import HCM70MergeSegmentMethod
from hcmcalc.ui import project_io
from hcmcalc.weaving.v7_0.method import HCM70WeavingSegmentMethod


EXPECTED_METHOD_IDS = {
    "two_lane_segment",
    "two_lane_facility",
    "multilane_segment",
    "basic_freeway_segment",
    "weaving_segment",
    "merge_segment",
    "diverge_segment",
}


AUTHORITATIVE_METHOD_CONTRACTS = {
    "two_lane_segment": {
        "engine_method_identifier": TwoLaneHighwayChapter15Method.method_name,
        "method_identifier": project_io.TWO_LANE_SEGMENT_METHOD,
        "input_contract": project_io.TWO_LANE_SEGMENT_CONTRACT,
        "project_type": project_io.MANUAL_SINGLE_SEGMENT_PROJECT_TYPE,
    },
    "two_lane_facility": {
        "engine_method_identifier": TwoLaneHighwayChapter15Method.method_name,
        "method_identifier": project_io.TWO_LANE_FACILITY_METHOD,
        "input_contract": project_io.TWO_LANE_FACILITY_CONTRACT,
        "project_type": project_io.MANUAL_FACILITY_PROJECT_TYPE,
    },
    "multilane_segment": {
        "engine_method_identifier": MultilaneHighwayLOSMethod.method_name,
        "method_identifier": project_io.MULTILANE_METHOD,
        "input_contract": project_io.MULTILANE_CONTRACT,
        "project_type": project_io.MANUAL_MULTILANE_PROJECT_TYPE,
    },
    "basic_freeway_segment": {
        "engine_method_identifier": BasicFreewaySegmentMethod.method_name,
        "method_identifier": project_io.FREEWAY_METHOD,
        "input_contract": project_io.FREEWAY_CONTRACT,
        "project_type": project_io.MANUAL_BASIC_FREEWAY_PROJECT_TYPE,
    },
    "weaving_segment": {
        "engine_method_identifier": HCM70WeavingSegmentMethod.method_name,
        "method_identifier": project_io.WEAVING_METHOD_IDENTIFIER,
        "input_contract": project_io.WEAVING_CALCULATION_CONTRACT,
        "project_type": project_io.MANUAL_WEAVING_PROJECT_TYPE,
    },
    "merge_segment": {
        "engine_method_identifier": HCM70MergeSegmentMethod.method_name,
        "method_identifier": project_io.ramp_method_family("merge"),
        "input_contract": project_io.ramp_calculation_contract("merge"),
        "project_type": project_io.ramp_project_type("merge"),
    },
    "diverge_segment": {
        "engine_method_identifier": HCM70DivergeSegmentMethod.method_name,
        "method_identifier": project_io.ramp_method_family("diverge"),
        "input_contract": project_io.ramp_calculation_contract("diverge"),
        "project_type": project_io.ramp_project_type("diverge"),
    },
}


def test_backend_registry_contains_all_current_methods_with_stable_identity() -> None:
    definitions = list_analysis_definitions()
    assert {definition.method_id for definition in definitions} == EXPECTED_METHOD_IDS
    assert len({definition.method_identifier for definition in definitions}) == 7
    assert all(definition.engineering_available if hasattr(definition, "engineering_available") else True for definition in definitions)
    assert all(definition.supported_unit_systems == ("metric", "imperial") for definition in definitions)
    assert all(definition.name_key.startswith("method.") for definition in definitions)
    assert all(definition.description_key.startswith("method.") for definition in definitions)


@pytest.mark.parametrize("method_id", sorted(EXPECTED_METHOD_IDS))
def test_registry_reuses_engine_and_project_io_authority(method_id: str) -> None:
    """Registry metadata must not drift from qualified engine/project contracts."""

    definition = get_analysis_definition(method_id)
    assert definition is not None
    assert {
        "engine_method_identifier": definition.engine_method_identifier,
        "method_identifier": definition.method_identifier,
        "input_contract": definition.input_contract,
        "project_type": definition.project_type,
    } == AUTHORITATIVE_METHOD_CONTRACTS[method_id]


def test_registry_lookup_is_language_neutral_and_missing_ids_are_explicit() -> None:
    assert get_analysis_definition("multilane_segment").method_identifier == "hcm7_multilane_los"
    assert get_analysis_definition("MULTILANE_SEGMENT") is None
    with pytest.raises(KeyError):
        from hcmcalc.application.registry import get_analysis_registry

        get_analysis_registry().require("not-a-method")


def test_application_identity_preserves_existing_fingerprint_contract() -> None:
    inputs = {"demand_volume_veh_h": 900.0, "nested": [{"b": 2, "a": 1}]}
    identity = CalculationIdentity("multilane", "phase_8", inputs)
    assert identity.fingerprint == calculation_input_fingerprint("multilane", "phase_8", inputs)
    assert identity.to_mapping()["calculation_fingerprint"] == identity.fingerprint
    assert normalized_input_fingerprint(inputs) == normalized_input_fingerprint({"nested": [{"a": 1, "b": 2}], "demand_volume_veh_h": 900.0})


def test_application_state_enum_has_all_r0_canonical_states() -> None:
    assert {state.value for state in ResultPresentationState} == {
        "prerun",
        "valid_current_result",
        "valid_current_result_with_warning",
        "capacity_failure",
        "hcm_stopping_or_handoff",
        "stale_result",
        "invalid_input",
        "unsupported_scope",
        "internal_error",
    }


def test_legacy_workflow_state_reexports_the_application_contract() -> None:
    from hcmcalc.application import workflow_state as application_state
    from hcmcalc.ui import workflow_state as legacy_state

    assert legacy_state.normalized_input_fingerprint is application_state.normalized_input_fingerprint
    assert legacy_state.ResultPresentationState is application_state.ResultPresentationState
    assert legacy_state.resolve_result_presentation_state is application_state.resolve_result_presentation_state


def test_calculation_state_and_interpretation_codes_are_serializable() -> None:
    state = resolve_result_presentation_state(freshness="Input changed — recalculate required")
    calculation_state = CalculationState(
        presentation_state=state,
        calculation_fingerprint="abc123",
        has_result=True,
    )
    assert calculation_state.is_stale
    assert calculation_state.to_mapping()["presentation_state"] == "stale_result"
    interpretations = interpretations_for_state(state)
    assert interpretations[0].code is InterpretationCode.RESULT_STALE
    assert interpretations[0].to_mapping()["message_key"] == "interpretation.result_stale"


def test_application_package_has_no_framework_imports() -> None:
    source_root = Path(__file__).parents[2] / "src" / "hcmcalc" / "application"
    forbidden = {"fastapi", "streamlit", "react"}
    for path in source_root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {
            alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported.update(
            node.module.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        )
        assert not forbidden.intersection(imported), path
