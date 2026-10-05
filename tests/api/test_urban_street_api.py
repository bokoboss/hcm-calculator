from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from hcmcalc.api.main import create_app


METHOD = "urban_street_segment"
TEMPLATE = "USS-CH30-EP1"


@pytest.mark.parametrize("field_key", ("analysis_period_min", "external_analysis_period_min"))
@pytest.mark.parametrize("endpoint", ("templates", "starting-values"))
def test_analysis_period_field_units_are_minutes_in_public_schema(endpoint, field_key):
    client = TestClient(create_app())
    if endpoint == "templates":
        fields = client.get(f"/api/v1/analyses/{METHOD}/templates").json()["fields"]
    else:
        fields = client.get(
            f"/api/v1/analyses/{METHOD}/starting-values",
            params={"template_id": TEMPLATE, "unit_system": "imperial"},
        ).json()["fields"]
    field = next(field for field in fields if field["key"] == field_key)

    assert field["kind"] == "integer"
    assert field.get("unit") == "min"
    assert field["required"] is True
    assert field["label_key"] == f"urban_street_segment.{field_key}"


def test_generic_api_chapter18_workflow_and_project_contract():
    client = TestClient(create_app())
    catalog = client.get("/api/v1/methods")
    assert catalog.status_code == 200
    assert len(catalog.json()["methods"]) == 9
    detail = client.get(f"/api/v1/methods/{METHOD}")
    assert detail.status_code == 200
    assert detail.json()["input_contract"] == "hcm7_ch18_bounded_signalized_15min_rht_reference_v1"

    templates = client.get(f"/api/v1/analyses/{METHOD}/templates").json()
    assert {template["template_id"] for template in templates["templates"]} == {TEMPLATE, "blank_custom"}
    fields_by_key = {field["key"]: field for field in templates["fields"]}
    assert all(field.get("label_key") for field in fields_by_key.values())
    assert {key: field["label_key"] for key, field in fields_by_key.items()} == {
        key: f"urban_street_segment.{key}" for key in fields_by_key
    }
    assert all(group.get("key") and group.get("label_key") and group.get("field_keys") for group in templates["groups"])
    starting = client.get(
        f"/api/v1/analyses/{METHOD}/starting-values",
        params={"template_id": TEMPLATE, "unit_system": "imperial"},
    ).json()
    assert {field["key"]: field["label_key"] for field in starting["fields"]} == {
        field["key"]: field["label_key"] for field in templates["fields"]
    }
    assert [(group["key"], group["label_key"]) for group in starting["groups"]] == [
        (group["key"], group["label_key"]) for group in templates["groups"]
    ]
    assert {key: value.get("kind") for key, value in fields_by_key.items()} == {
        field["key"]: field["kind"] for field in starting["fields"]
    }
    assert {key: value.get("options") for key, value in fields_by_key.items() if "options" in value} == {
        "control_type": ["signalized"],
        "external_control_type": ["signalized"],
    }
    assert fields_by_key["segment_length"].get("unit_metric") == "m"
    assert fields_by_key["segment_length"].get("unit_imperial") == "ft"
    assert fields_by_key["posted_speed_limit"].get("unit_metric") == "km/h"
    assert fields_by_key["posted_speed_limit"].get("unit_imperial") == "mi/h"
    assert fields_by_key["access_point_delays_s_veh"].get("item_unit") == "s/veh"
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


def test_chapter18_public_group_schema_has_stable_localization_identity():
    client = TestClient(create_app())
    templates = client.get(f"/api/v1/analyses/{METHOD}/templates").json()
    groups = templates["groups"]
    assert [(group["key"], group.get("label_key")) for group in groups] == [
        ("segment", "urban_street_segment.group_segment"),
        ("external_through", "urban_street_segment.group_external_through"),
    ]


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


def test_thailand_lht_public_contract_api_project_and_all_current_exports():
    client = TestClient(create_app())
    method = "urban_street_segment_th_lht"
    template = "USS-TH-LHT-CH30-EP1"
    methods = client.get("/api/v1/methods").json()["methods"]
    definition = next(item for item in methods if item["method_id"] == method)
    assert definition["method_identifier"] == "hcm7_urban_street_segment_th_lht"
    assert definition["input_contract"] == "hcm7_ch18_bounded_signalized_15min_th_lht_semantic_v1"
    templates = client.get(f"/api/v1/analyses/{method}/templates").json()
    fields = {field["key"]: field for field in templates["fields"]}
    assert {item["template_id"] for item in templates["templates"]} == {template, "blank_custom"}
    assert fields["calibration_status"]["options"] == ["hcm_reference_uncalibrated", "user_local_calibration"]
    assert "curb_proportion" not in fields
    starting = client.get(
        f"/api/v1/analyses/{method}/starting-values",
        params={"template_id": template, "unit_system": "imperial"},
    ).json()
    inputs = starting["displayed_inputs"]
    request = {"template_id": template, "unit_system": "imperial", "displayed_inputs": inputs}
    validated = client.post(f"/api/v1/analyses/{method}/validate", json=request)
    assert validated.status_code == 200 and validated.json()["ready"] is True
    snapshot_response = client.post(f"/api/v1/analyses/{method}/calculate", json=request)
    assert snapshot_response.status_code == 200
    snapshot = snapshot_response.json()
    assert snapshot["method_identifier"] == definition["method_identifier"]
    assert snapshot["normalized_inputs"]["curb_proportion"] == 0.70
    assert snapshot["audit"]["traffic_side"] == "left_hand_traffic"
    assert snapshot["audit"]["kerbside_physical_side"] == "left_for_each_travel_direction"

    for export_format in ("json", "markdown", "csv", "xlsx"):
        exported = client.post(
            f"/api/v1/analyses/{method}/export",
            json={**request, "calculation_fingerprint": snapshot["calculation_fingerprint"],
                  "input_snapshot_fingerprint": snapshot["input_snapshot_fingerprint"],
                  "result": snapshot["result"], "export_format": export_format},
        )
        assert exported.status_code == 200
        assert exported.json()["recalculated"] is False
        assert exported.json()["content"] or exported.json()["content_base64"]

    project_response = client.post(
        "/api/v1/projects/from-analysis",
        json={"project_name": "Thailand LHT API", "analysis_snapshot": snapshot},
    )
    assert project_response.status_code == 200
    project = project_response.json()["project"]
    assert project["schema_version"] == "2.0"
    opened = client.post("/api/v1/projects/validate", json={"project": project})
    assert opened.status_code == 200
    scenario = opened.json()["project"]["analyses"][0]["scenarios"][0]
    assert scenario["result_status"] == "current"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("access_point_delays_s_veh", [1e308, 1e308]),
        ("d_other_s_veh", 1e308),
        ("v_th_veh_h", 1.7e308),
    ],
)
def test_validation_rejects_nonfinite_derived_arithmetic(field, value):
    client = TestClient(create_app())
    displayed = client.get(
        f"/api/v1/analyses/{METHOD}/starting-values",
        params={"template_id": TEMPLATE, "unit_system": "imperial"},
    ).json()["displayed_inputs"]
    displayed[field] = value
    if field == "d_other_s_veh":
        displayed["d_t_s_veh"] = 1e308
    elif field == "v_th_veh_h":
        displayed["c_th_veh_h"] = 1e-308

    response = client.post(
        f"/api/v1/analyses/{METHOD}/validate",
        json={"template_id": TEMPLATE, "unit_system": "imperial", "displayed_inputs": displayed},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["valid"] is False
    assert body["ready"] is False
    assert body["errors"][0]["field"] == ("access_point_delays_s_veh" if field == "access_point_delays_s_veh" else None)


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


@pytest.mark.parametrize(
    ("display_field", "value"),
    [
        ("control_type", "two_way_stop"),
        ("analysis_period_min", 60),
        ("demand_balanced", False),
        ("demand_adjustments_resolved", False),
        ("capacity_effects_resolved", False),
        ("spillback_present", True),
        ("access_point_delays_s_veh", [-0.1, 0.2]),
        ("upstream_intersection_width", 1800),
        ("upstream_intersection_width", 1801),
        ("segment_length", 10561),
    ],
)
def test_validation_maps_chapter18_preconditions_to_the_offending_display_field(display_field, value):
    client = TestClient(create_app(), raise_server_exceptions=False)
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
    body = response.json()
    assert body["valid"] is False
    assert body["ready"] is False
    assert body["errors"][0]["code"] == "invalid_input"
    assert body["errors"][0]["field"] == display_field


@pytest.mark.parametrize(
    ("changes", "expected_field"),
    [
        ({"access_point_delays_s_veh": []}, "access_point_delays_s_veh"),
        ({"subject_side_access_count": 0, "opposing_side_access_count": 0}, "access_point_delays_s_veh"),
        ({"demand_balanced": False, "demand_adjustments_resolved": False}, "demand_balanced"),
    ],
)
def test_validation_attributes_access_delay_requirements_and_uses_flag_priority(changes, expected_field):
    client = TestClient(create_app(), raise_server_exceptions=False)
    displayed = client.get(
        f"/api/v1/analyses/{METHOD}/starting-values",
        params={"template_id": TEMPLATE, "unit_system": "imperial"},
    ).json()["displayed_inputs"]
    displayed.update(changes)

    response = client.post(
        f"/api/v1/analyses/{METHOD}/validate",
        json={"template_id": TEMPLATE, "unit_system": "imperial", "displayed_inputs": displayed},
    )

    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert response.json()["errors"][0]["field"] == expected_field
