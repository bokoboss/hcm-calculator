from pathlib import Path
import re
import json

from fastapi.testclient import TestClient

from hcmcalc.api.main import (
    HASHED_ASSET_CACHE_CONTROL,
    SPA_SHELL_CACHE_CONTROL,
    create_app,
)


def _build_test_spa(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text(
        "<html><body><div id='root'>cache-test</div></body></html>",
        encoding="utf-8",
    )
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "index-AbCd1234.js").write_text(
        "console.log('cache-test')",
        encoding="utf-8",
    )


def test_spa_shell_is_not_stored_or_conditionally_reused(tmp_path: Path) -> None:
    _build_test_spa(tmp_path)
    client = TestClient(create_app(static_dir=tmp_path))

    root = client.get("/")
    assert root.status_code == 200
    assert root.headers["cache-control"] == SPA_SHELL_CACHE_CONTROL
    assert "etag" not in root.headers
    assert "last-modified" not in root.headers

    conditional = client.get("/", headers={"If-None-Match": '"stale-deployment"'})
    assert conditional.status_code == 200
    assert conditional.headers["cache-control"] == SPA_SHELL_CACHE_CONTROL
    assert "cache-test" in conditional.text

    deep_link = client.get("/reference/methods/multilane_segment")
    assert deep_link.status_code == 200
    assert deep_link.headers["cache-control"] == SPA_SHELL_CACHE_CONTROL
    assert "etag" not in deep_link.headers


def test_hashed_frontend_assets_are_long_lived_and_immutable(tmp_path: Path) -> None:
    _build_test_spa(tmp_path)
    client = TestClient(create_app(static_dir=tmp_path))

    asset = client.get("/assets/index-AbCd1234.js")
    assert asset.status_code == 200
    assert asset.headers["cache-control"] == HASHED_ASSET_CACHE_CONTROL
    assert asset.text == "console.log('cache-test')"

    missing_asset = client.get("/assets/index-OLDHASH.js")
    assert missing_asset.status_code == 404

    missing_api = client.get("/api/v1/not-a-route")
    assert missing_api.status_code == 404
    assert missing_api.headers["content-type"].startswith("application/json")


def test_packaged_fallback_serves_current_reference_only_spa_and_api() -> None:
    packaged_static = Path(__file__).resolve().parents[2] / "src" / "hcmcalc" / "ui" / "static"
    client = TestClient(create_app(static_dir=packaged_static))

    shell = client.get("/")
    deep_link = client.get("/analysis/urban_street_segment")
    asset_paths = re.findall(r'(?:src|href)="(/assets/[^\"]+\.js)"', shell.text)
    assert shell.status_code == 200
    assert asset_paths
    assert deep_link.text == shell.text
    bundle = client.get(asset_paths[0])
    assert bundle.status_code == 200
    assert "urban_street_segment" in bundle.text
    assert "Reference only" in bundle.text

    methods = client.get("/api/v1/methods").json()["methods"]
    assert any(method["method_id"] == "urban_street_segment" for method in methods)


def test_packaged_lht_worksheet_handbook_and_dist_are_synchronized() -> None:
    root = Path(__file__).resolve().parents[2]
    packaged = root / "src/hcmcalc/ui/static"
    client = TestClient(create_app(static_dir=packaged))
    shell = client.get("/analysis/urban_street_segment_th_lht")
    assert shell.status_code == 200
    assert client.get("/reference/urban_street_segment_th_lht").text == shell.text
    assets = re.findall(r'(?:src|href)="(/assets/[^\"]+\.js)"', shell.text)
    bundle = client.get(assets[0]).text
    for evidence in (
        "hcm7_ch18_bounded_signalized_15min_th_lht_semantic_v1",
        "number-list-editor", "Evaluate one bounded signalized 15-minute urban street segment",
        "Travel speed", "ความเร็วเดินทาง", "semantic-mirror / adapter-verification fixture",
    ):
        assert evidence in bundle or json.dumps(evidence, ensure_ascii=True)[1:-1] in bundle
    dist = root / "frontend/dist"
    if dist.exists():
        packaged_files = {file.relative_to(packaged): file.read_bytes() for file in packaged.rglob("*") if file.is_file()}
        dist_files = {file.relative_to(dist): file.read_bytes() for file in dist.rglob("*") if file.is_file()}
        assert packaged_files == dist_files
