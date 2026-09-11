import importlib
from pathlib import Path
import tomllib

from fastapi.testclient import TestClient

from hcmcalc.api.vercel import app


def test_vercel_entrypoint_targets_source_adapter() -> None:
    with (Path(__file__).parents[2] / "pyproject.toml").open("rb") as file:
        entrypoint = tomllib.load(file)["tool"]["vercel"]["entrypoint"]
    module, name = entrypoint.split(":")

    assert module == "vercel_app"
    assert (Path(__file__).parents[2] / f"{module}.py").is_file()
    assert getattr(importlib.import_module(module), name) is app


def test_vercel_adapter_keeps_routes_and_reports_preview_identity(monkeypatch) -> None:
    monkeypatch.setenv("VERCEL_ENV", "preview")
    monkeypatch.setenv("VERCEL_GIT_COMMIT_SHA", "abc123")
    monkeypatch.setenv("VERCEL_DEPLOYMENT_ID", "dpl_test")

    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["application_version"]
    assert response.headers["x-hcmcalc-application-version"] == response.json()["application_version"]
    assert response.headers["x-hcmcalc-environment"] == "preview"
    assert response.headers["x-vercel-commit-sha"] == "abc123"
    assert response.headers["x-vercel-deployment-id"] == "dpl_test"
    root = client.get("/")
    assert root.status_code == 200
    assert '<div id="root"></div>' in root.text
    assert client.get("/reference/methods/multilane_segment").status_code == 200
    assert client.get("/assets/index-hlbGBPYR.js").status_code == 200
    assert client.get("/engineering-assets/ramp_influence/merge_right_on_ramp.svg").status_code == 200
    missing_api = client.get("/api/v1/not-a-route")
    assert missing_api.status_code == 404
    assert missing_api.headers["content-type"].startswith("application/json")
