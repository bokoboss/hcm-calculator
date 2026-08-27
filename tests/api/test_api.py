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


def test_local_server_default_is_loopback() -> None:
    assert DEFAULT_HOST == "127.0.0.1"
