from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from hcmcalc.api.main import create_app


METHOD = "urban_street_segment"
TEMPLATE = "USS-CH30-EP1"


def test_generic_api_chapter18_workflow_and_project_contract():
    client = TestClient(create_app())
    catalog = client.get("/api/v1/methods")
    assert catalog.status_code == 200
    assert len(catalog.json()["methods"]) == 8
    detail = client.get(f"/api/v1/methods/{METHOD}")
    assert detail.status_code == 200
    assert detail.json()["input_contract"] == "hcm7_ch18_bounded_signalized_15min_rht_reference_v1"

    templates = client.get(f"/api/v1/analyses/{METHOD}/templates").json()
    assert {template["template_id"] for template in templates["templates"]} == {TEMPLATE, "blank_custom"}
    starting = client.get(
        f"/api/v1/analyses/{METHOD}/starting-values",
        params={"template_id": TEMPLATE, "unit_system": "imperial"},
    ).json()
    displayed = starting["displayed_inputs"]
    request = {"template_id": TEMPLATE, "unit_system": "imperial", "displayed_inputs": displayed}
    validation = client.post(f"/api/v1/analyses/{METHOD}/validate", json=request)
    assert validation.status_code == 200
    assert validation.json()["ready"] is True

    invalid = deepcopy(request)
    invalid["displayed_inputs"]["external_source_tool"] = None
    rejected = client.post(f"/api/v1/analyses/{METHOD}/validate", json=invalid)
    assert rejected.status_code == 200
    assert rejected.json()["ready"] is False
    assert rejected.json()["errors"][0]["code"] == "invalid_input"

    calculated_response = client.post(f"/api/v1/analyses/{METHOD}/calculate", json=request)
    assert calculated_response.status_code == 200
    snapshot = calculated_response.json()
    assert snapshot["result"]["outputs"]["level_of_service"] == "C"
    assert snapshot["normalized_inputs"]["v_m_veh_h"] == 1150
    assert snapshot["normalized_inputs"]["external_through"]["v_th_veh_h"] == 968

    exported = client.post(
        f"/api/v1/analyses/{METHOD}/export",
        json={**request, "calculation_fingerprint": snapshot["calculation_fingerprint"],
              "input_snapshot_fingerprint": snapshot["input_snapshot_fingerprint"],
              "result": snapshot["result"], "export_format": "json"},
    )
    assert exported.status_code == 200
    assert exported.json()["recalculated"] is False
    assert "external_through_provenance" in exported.json()["content"]

    created = client.post(
        "/api/v1/projects/from-analysis",
        json={"project_name": "Chapter 18 API", "analysis_snapshot": snapshot},
    )
    assert created.status_code == 200
    project = created.json()["project"]
    analysis = project["analyses"][0]
    scenario = analysis["scenarios"][0]
    opened = client.post("/api/v1/projects/validate", json={"project": project})
    assert opened.status_code == 200
    assert opened.json()["project"]["analyses"][0]["scenarios"][0]["result_status"] == "current"

    edited_inputs = deepcopy(displayed)
    edited_inputs["curb_proportion"] = 0.71
    edited = client.post(
        f"/api/v1/analyses/{METHOD}/validate",
        json={"template_id": TEMPLATE, "unit_system": "imperial", "displayed_inputs": edited_inputs},
    ).json()
    stale = client.post(
        "/api/v1/projects/update-scenario",
        json={"project": project, "analysis_id": analysis["analysis_id"],
              "scenario_id": scenario["scenario_id"], "analysis_snapshot": edited},
    )
    assert stale.status_code == 200
    changed = stale.json()["project"]["analyses"][0]["scenarios"][0]
    assert changed["result_status"] == "stale"
    assert changed["result"] is None


@pytest.mark.parametrize("field", ["segment_length", "posted_speed_limit"])
def test_nonnumeric_scaled_fields_return_structured_validation_and_calculation_errors(field):
    client = TestClient(create_app(), raise_server_exceptions=False)
    displayed = client.get(
        f"/api/v1/analyses/{METHOD}/starting-values",
        params={"template_id": TEMPLATE, "unit_system": "imperial"},
    ).json()["displayed_inputs"]
    displayed[field] = "abc"
    request = {"template_id": TEMPLATE, "unit_system": "imperial", "displayed_inputs": displayed}

    validation = client.post(f"/api/v1/analyses/{METHOD}/validate", json=request)
    assert validation.status_code == 200
    assert validation.json()["valid"] is False
    assert validation.json()["errors"][0]["field"] == field

    calculated = client.post(f"/api/v1/analyses/{METHOD}/calculate", json=request)
    assert calculated.status_code == 422
    assert calculated.json()["detail"]["code"] == "invalid_input"
    assert calculated.json()["detail"]["details"]["field"] == field


def test_export_normalization_maps_nonnumeric_scaled_field_to_422():
    client = TestClient(create_app(), raise_server_exceptions=False)
    displayed = client.get(
        f"/api/v1/analyses/{METHOD}/starting-values",
        params={"template_id": TEMPLATE, "unit_system": "imperial"},
    ).json()["displayed_inputs"]
    calculated = client.post(
        f"/api/v1/analyses/{METHOD}/calculate",
        json={"template_id": TEMPLATE, "unit_system": "imperial", "displayed_inputs": displayed},
    ).json()
    invalid = deepcopy(displayed)
    invalid["segment_length"] = "abc"
    response = client.post(
        f"/api/v1/analyses/{METHOD}/export",
        json={
            "template_id": TEMPLATE,
            "unit_system": "imperial",
            "displayed_inputs": invalid,
            "calculation_fingerprint": calculated["calculation_fingerprint"],
            "input_snapshot_fingerprint": calculated["input_snapshot_fingerprint"],
            "result": calculated["result"],
            "export_format": "json",
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"]["details"]["field"] == "segment_length"


@pytest.mark.parametrize(
    ("display_field", "value"),
    [
        ("external_source_tool", None),
        ("external_direction", "westbound"),
        ("external_control_type", "unsignalized"),
        ("external_analysis_period_min", 30),
        ("v_th_veh_h", "abc"),
    ],
)
def test_validation_maps_external_engine_errors_to_displayed_fields(display_field, value):
    client = TestClient(create_app())
    displayed = client.get(
        f"/api/v1/analyses/{METHOD}/starting-values",
        params={"template_id": TEMPLATE, "unit_system": "imperial"},
    ).json()["displayed_inputs"]
    displayed[display_field] = value

    response = client.post(
        f"/api/v1/analyses/{METHOD}/validate",
        json={"template_id": TEMPLATE, "unit_system": "imperial", "displayed_inputs": displayed},
    )
    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert response.json()["errors"][0]["field"] == display_field
