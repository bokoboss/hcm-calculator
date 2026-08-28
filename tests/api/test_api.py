from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from hcmcalc.api.main import DEFAULT_HOST, create_app


def test_health_is_typed_and_exposes_no_engine_behavior() -> None:
    response = TestClient(create_app()).get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "hcmcalc-api"
    assert payload["api_version"] == "v1"
    assert "application_version" in payload


def test_method_discovery_returns_all_seven_backend_definitions() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/methods")
    assert response.status_code == 200
    payload = response.json()
    assert payload["registry_version"] == "r1"
    assert {method["method_id"] for method in payload["methods"]} == {
        "two_lane_segment",
        "two_lane_facility",
        "multilane_segment",
        "basic_freeway_segment",
        "weaving_segment",
        "merge_segment",
        "diverge_segment",
    }
    assert all(method["engineering_available"] for method in payload["methods"])
    assert all("frontend" not in method for method in payload["methods"])


def test_one_method_and_unknown_method_use_typed_contracts() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/methods/multilane_segment")
    assert response.status_code == 200
    assert response.json()["method_identifier"] == "hcm7_multilane_los"
    assert response.json()["engine_method_identifier"] == "hcm7_multilane_los"
    assert response.json()["input_contract"] == "phase_8"
    assert response.json()["project_type"] == "manual_multilane_v0"

    missing = client.get("/api/v1/methods/not-a-method")
    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "method_not_found"


def test_default_api_has_no_cors_and_rejects_wildcard_origins() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/health", headers={"Origin": "https://untrusted.example"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
    with pytest.raises(ValueError, match="Wildcard CORS"):
        create_app(allow_dev_origins=("*",))


def test_explicit_development_origin_is_allowlisted_without_wildcard() -> None:
    client = TestClient(create_app(allow_dev_origins=("http://127.0.0.1:5173",)))
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://127.0.0.1:5173"},
    )
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_compiled_spa_is_served_without_shadowing_api(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<html><body><div id='root'>R1</div></body></html>", encoding="utf-8")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log('r1')", encoding="utf-8")
    client = TestClient(create_app(static_dir=tmp_path))

    assert client.get("/").status_code == 200
    assert "R1" in client.get("/").text
    assert client.get("/reference/methods/multilane_segment").status_code == 200
    assert client.get("/assets/app.js").text == "console.log('r1')"
    assert client.get("/api/v1/health").json()["status"] == "ok"
    assert client.get("/api/v1/not-a-route").status_code == 404


def test_compiled_spa_serves_qualified_engineering_assets_from_the_package() -> None:
    client = TestClient(create_app())

    expected_assets = {
        "/engineering-assets/two_lane/passing_zone.png": "image/png",
        "/engineering-assets/weaving/one_sided_weave.png": "image/png",
        "/engineering-assets/weaving/two_sided_weave.png": "image/png",
        "/engineering-assets/ramp_influence/merge_right_on_ramp.svg": "image/svg+xml",
        "/engineering-assets/ramp_influence/diverge_right_off_ramp.svg": "image/svg+xml",
    }
    for path, media_type in expected_assets.items():
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith(media_type)
        assert response.content


def test_local_server_default_is_loopback() -> None:
    assert DEFAULT_HOST == "127.0.0.1"


def test_phase2_multilane_api_separates_readiness_from_calculation() -> None:
    client = TestClient(create_app())
    starting = client.get(
        "/api/v1/analyses/multilane_segment/starting-values",
        params={"template_id": "MLH-CH26-004-EB", "unit_system": "imperial"},
    ).json()
    request = {
        "template_id": "MLH-CH26-004-EB",
        "unit_system": "imperial",
        "displayed_inputs": starting["displayed_inputs"],
    }
    ready = client.post("/api/v1/analyses/multilane_segment/validate", json=request)
    assert ready.status_code == 200
    assert ready.json()["valid"] is True
    calculated = client.post("/api/v1/analyses/multilane_segment/calculate", json=request)
    assert calculated.status_code == 200
    payload = calculated.json()
    assert payload["result"]["outputs"]["level_of_service"] == "C"
    assert payload["presentation"]["answer"]["value"] == "C"
    assert payload["calculation_state"]["has_result"] is True
    assert payload["audit"]["calculation_succeeded"] is True


@pytest.mark.parametrize(
    "method_id, template_id, engine_method",
    (
        ("two_lane_segment", "TLH-CH15-001", "hcm7_ch15_two_lane_motorized"),
        ("basic_freeway_segment", "BF-CH26-001", "hcm7_basic_freeway_segment"),
        ("weaving_segment", "WVG-CH27-001", "hcm7_v70_freeway_weaving_segment"),
        ("merge_segment", "chapter_28_example_1_merge", "hcm7_v70_freeway_merge_segment"),
        ("diverge_segment", "chapter_28_example_3_diverge_component", "hcm7_v70_freeway_diverge_segment"),
    ),
)
def test_phase3_api_exposes_templates_readiness_and_calculation(
    method_id: str,
    template_id: str,
    engine_method: str,
) -> None:
    client = TestClient(create_app())
    templates = client.get(f"/api/v1/analyses/{method_id}/templates")
    assert templates.status_code == 200
    assert templates.json()["groups"]

    starting = client.get(
        f"/api/v1/analyses/{method_id}/starting-values",
        params={"template_id": template_id, "unit_system": "imperial"},
    )
    assert starting.status_code == 200
    request = {
        "template_id": template_id,
        "unit_system": "imperial",
        "displayed_inputs": starting.json()["displayed_inputs"],
    }
    ready = client.post(f"/api/v1/analyses/{method_id}/validate", json=request)
    assert ready.status_code == 200
    assert ready.json()["valid"] is True
    calculated = client.post(f"/api/v1/analyses/{method_id}/calculate", json=request)
    assert calculated.status_code == 200
    payload = calculated.json()
    assert payload["result"]["method"] == engine_method
    assert payload["calculation_state"]["has_result"] is True
    assert payload["audit"]


def test_phase2_facility_api_rejects_locked_context_and_returns_segment_evidence() -> None:
    client = TestClient(create_app())
    starting = client.get(
        "/api/v1/analyses/two_lane_facility/starting-values",
        params={"template_id": "level_example_3", "unit_system": "imperial"},
    ).json()
    rows = starting["segments"]
    rows[0]["terrain_type"] = "mountainous"
    locked = client.post(
        "/api/v1/analyses/two_lane_facility/validate",
        json={"template_id": "level_example_3", "unit_system": "imperial", "displayed_inputs": {"rows": rows}},
    )
    assert locked.status_code == 200
    assert locked.json()["valid"] is False
    assert locked.json()["validation_status"] == "unsupported_scope"

    fresh = client.get(
        "/api/v1/analyses/two_lane_facility/starting-values",
        params={"template_id": "level_example_3", "unit_system": "imperial"},
    ).json()
    calculated = client.post(
        "/api/v1/analyses/two_lane_facility/calculate",
        json={"template_id": "level_example_3", "unit_system": "imperial", "displayed_inputs": {"rows": fresh["segments"]}},
    )
    assert calculated.status_code == 200
    assert len(calculated.json()["presentation"]["segments"]) == 5


def test_phase2_project_endpoint_saves_a_snapshot_and_has_no_presentation_authority() -> None:
    client = TestClient(create_app())
    starting = client.get(
        "/api/v1/analyses/multilane_segment/starting-values",
        params={"template_id": "MLH-CH26-004-EB", "unit_system": "imperial"},
    ).json()
    calculated = client.post(
        "/api/v1/analyses/multilane_segment/calculate",
        json={"template_id": "MLH-CH26-004-EB", "unit_system": "imperial", "displayed_inputs": starting["displayed_inputs"]},
    ).json()
    saved = client.post(
        "/api/v1/projects/from-analysis",
        json={"project_name": "API project", "analysis_snapshot": calculated},
    )
    assert saved.status_code == 200
    project = saved.json()["project"]
    assert project["schema_version"] == "2.0"
    assert "presentation" not in project["analyses"][0]["scenarios"][0]["result"]
    loaded = client.post("/api/v1/projects/validate", json={"project": project})
    assert loaded.status_code == 200
    assert loaded.json()["project"]["project_id"] == project["project_id"]


def test_phase2_project_endpoint_updates_scenario_inputs_without_recalculation() -> None:
    client = TestClient(create_app())
    starting = client.get(
        "/api/v1/analyses/multilane_segment/starting-values",
        params={"template_id": "MLH-CH26-004-EB", "unit_system": "imperial"},
    ).json()
    original_request = {
        "template_id": "MLH-CH26-004-EB",
        "unit_system": "imperial",
        "displayed_inputs": starting["displayed_inputs"],
    }
    original = client.post("/api/v1/analyses/multilane_segment/calculate", json=original_request).json()
    project = client.post(
        "/api/v1/projects/from-analysis",
        json={"project_name": "API update project", "analysis_snapshot": original},
    ).json()["project"]
    changed_inputs = dict(starting["displayed_inputs"])
    changed_inputs["demand_volume_veh_h"] = 1800
    changed_request = {**original_request, "displayed_inputs": changed_inputs}
    changed = client.post("/api/v1/analyses/multilane_segment/calculate", json=changed_request).json()
    analysis = project["analyses"][0]
    scenario = analysis["scenarios"][0]
    updated = client.post(
        "/api/v1/projects/update-scenario",
        json={
            "project": project,
            "analysis_id": analysis["analysis_id"],
            "scenario_id": scenario["scenario_id"],
            "analysis_snapshot": changed,
        },
    )
    assert updated.status_code == 200
    updated_scenario = updated.json()["project"]["analyses"][0]["scenarios"][0]
    assert updated_scenario["result"] is None
    assert updated_scenario["result_status"] == "stale"
