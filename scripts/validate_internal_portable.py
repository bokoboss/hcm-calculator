"""Validate a staged or zipped internal portable distribution."""

from __future__ import annotations

import argparse
import base64
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import importlib.metadata
import json
import math
import os
from pathlib import Path, PurePosixPath
import platform
import re
import subprocess
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener
import zipfile


ARTIFACT_NAME = "HCM-Calculator-v0.9.0-Internal-Windows-x64"
EXPECTED_METHODS = {
    "two_lane_segment": {
        "template_id": "TLH-CH15-001",
        "engine_method": "hcm7_ch15_two_lane_motorized",
        "answer": "D",
        "numeric": {"follower_density_followers_mi_ln": 10.08622955622713},
    },
    "two_lane_facility": {
        "template_id": "level_example_3",
        "engine_method": "hcm7_ch15_two_lane_motorized",
        "answer": "C",
        "numeric": {"facility_follower_density_followers_mi_ln": 7.286363636363637},
    },
    "multilane_segment": {
        "template_id": "MLH-CH26-004-EB",
        "engine_method": "hcm7_multilane_los",
        "answer": "C",
        "numeric": {"density_pc_mi_ln": 18.08754208754209},
    },
    "basic_freeway_segment": {
        "template_id": "BF-CH26-001",
        "engine_method": "hcm7_basic_freeway_segment",
        "answer": "C",
        "numeric": {"density_pc_mi_ln": 18.776944117286437},
    },
    "weaving_segment": {
        "template_id": "WVG-CH27-001",
        "engine_method": "hcm7_v70_freeway_weaving_segment",
        "answer": "C",
        "numeric": {"density_pc_mi_ln": 26.284440902466354},
    },
    "merge_segment": {
        "template_id": "chapter_28_example_1_merge",
        "engine_method": "hcm7_v70_freeway_merge_segment",
        "answer": "D",
        "numeric": {"density_pc_mi_ln": 28.166583333333328},
    },
    "diverge_segment": {
        "template_id": "chapter_28_example_3_diverge_component",
        "engine_method": "hcm7_v70_freeway_diverge_segment",
        "answer": "D",
        "numeric": {"density_pc_mi_ln": 31.1264773844},
    },
}
EXPECTED_PACKAGE_NAMES = {
    "hcm-calculator",
    "anyio",
    "annotated-doc",
    "annotated-types",
    "click",
    "colorama",
    "et-xmlfile",
    "fastapi",
    "h11",
    "idna",
    "openpyxl",
    "pydantic",
    "pydantic-core",
    "pyyaml",
    "starlette",
    "typing-extensions",
    "typing-inspection",
    "uvicorn",
}
FORBIDDEN_PACKAGE_NAMES = {
    "build",
    "httpx",
    "httpx2",
    "playwright",
    "pytest",
    "streamlit",
    "vite",
}


class ValidationError(RuntimeError):
    """Raised when the portable contract is not met."""


def canonical_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def fail(message: str) -> None:
    raise ValidationError(message)


def relative_files(root: Path) -> set[str]:
    result: set[str] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            fail(f"Symlink found in artifact: {path}")
        if path.is_file():
            result.add(path.relative_to(root).as_posix())
    return result


def validate_hygiene(root: Path) -> None:
    forbidden_components = {
        ".git",
        ".github",
        ".agents",
        ".venv",
        "venv",
        "frontend",
        "node_modules",
        "tests",
        "worktrees",
        "backups",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tmp",
        ".codex",
        ".agent-work",
    }
    for relative in relative_files(root):
        path = PurePosixPath(relative)
        lowered_parts = {part.casefold() for part in path.parts}
        forbidden = lowered_parts & forbidden_components
        if forbidden:
            fail(f"Forbidden artifact path: {relative}")
        lowered = relative.casefold()
        if any(token in lowered for token in ("playwright", "pytest")):
            fail(f"Forbidden artifact filename: {relative}")
        if "credentials" in lowered and path.parts[0].casefold() != "runtime":
            fail(f"Credential-like artifact filename: {relative}")
        if path.name.casefold() in {".env", ".env.local", ".env.production"}:
            fail(f"Environment file found in artifact: {relative}")
        if path.suffix.casefold() in {".pem", ".key", ".pfx"}:
            fail(f"Credential-like file found in artifact: {relative}")


def read_checksums(root: Path) -> dict[str, str]:
    path = root / "SHA256SUMS.txt"
    if not path.is_file():
        fail("Missing SHA256SUMS.txt")
    result: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-fA-F]{64})  (.+)", line)
        if not match:
            fail(f"Malformed SHA256SUMS.txt line {line_number}")
        digest, relative = match.groups()
        normalized = PurePosixPath(relative)
        if normalized.is_absolute() or ".." in normalized.parts or "\\" in relative:
            fail(f"Unsafe checksum path: {relative}")
        if relative in result:
            fail(f"Duplicate checksum entry: {relative}")
        result[relative] = digest.casefold()
    return result


def validate_checksums(root: Path) -> None:
    checksums = read_checksums(root)
    actual = relative_files(root) - {"SHA256SUMS.txt"}
    if set(checksums) != actual:
        fail(
            "SHA256SUMS.txt file set mismatch: "
            f"missing={sorted(actual - set(checksums))}; "
            f"unlisted={sorted(set(checksums) - actual)}"
        )
    def digest_file(relative: str) -> tuple[str, str]:
        path = root / Path(*PurePosixPath(relative).parts)
        digest = sha256()
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
        return relative, digest.hexdigest()

    worker_count = min(16, max(4, (os.cpu_count() or 4) * 2))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        actual_digests = dict(executor.map(digest_file, checksums))
    for relative, expected in checksums.items():
        actual_digest = actual_digests[relative]
        if actual_digest != expected:
            fail(f"Checksum mismatch: {relative}")


def validate_zip(zip_path: Path) -> None:
    if not zip_path.is_file():
        fail(f"Missing final ZIP: {zip_path}")
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            fail("Final ZIP contains duplicate entries.")
        if not names:
            fail("Final ZIP is empty.")
        prefix = ARTIFACT_NAME + "/"
        if not all(name.startswith(prefix) for name in names):
            fail("Final ZIP contains files outside the required artifact directory.")
        if prefix + "SHA256SUMS.txt" not in names:
            fail("Final ZIP is missing SHA256SUMS.txt")
        for name in names:
            relative = name[len(prefix) :]
            path = PurePosixPath(relative)
            if path.is_absolute() or ".." in path.parts or "\\" in relative:
                fail(f"Unsafe ZIP path: {name}")
            lowered = relative.casefold()
            if any(token in lowered for token in (".git", ".venv", "node_modules", "playwright", "pytest")):
                fail(f"Forbidden ZIP entry: {name}")


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Could not read JSON {path}: {exc}")
    if not isinstance(payload, dict):
        fail(f"Expected JSON object in {path}")
    return payload


def validate_structure(root: Path) -> None:
    required_files = {
        "Run HCM Calculator.bat",
        "README-TH.txt",
        "VERSION.txt",
        "SHA256SUMS.txt",
        "DEPENDENCY-INVENTORY.json",
        "licenses/PYTHON-LICENSE.txt",
        "licenses/THIRD-PARTY-NOTICES.txt",
        "runtime/python.exe",
        "runtime/RUNTIME-PROVENANCE.json",
        "app/hcmcalc/__init__.py",
        "app/hcmcalc/ui/static/index.html",
    }
    files = relative_files(root)
    missing = sorted(required_files - files)
    if missing:
        fail(f"Portable structure is missing: {missing}")
    if "0.9.0" not in (root / "VERSION.txt").read_text(encoding="utf-8"):
        fail("VERSION.txt does not identify version 0.9.0")

    launcher = (root / "Run HCM Calculator.bat").read_text(encoding="utf-8-sig").casefold()
    if "%~dp0" not in launcher or "runtime\\python.exe" not in launcher:
        fail("Portable launcher must resolve and invoke the bundled runtime.")
    if "--host 127.0.0.1" not in launcher or "--port 8765" not in launcher:
        fail("Portable launcher must explicitly use the loopback port.")
    if "--open-browser" not in launcher:
        fail("Portable launcher must preserve the qualified browser-opening behavior.")
    launcher_without_bundled = launcher.replace("runtime\\python.exe", "")
    for forbidden in ("taskkill", "node", "npm", "pnpm", "pip install", "py.exe"):
        if forbidden in launcher_without_bundled:
            fail(f"Portable launcher contains forbidden runtime operation: {forbidden}")

    provenance = load_json(root / "runtime/RUNTIME-PROVENANCE.json")
    runtime = provenance.get("runtime")
    if not isinstance(runtime, dict):
        fail("Runtime provenance does not contain runtime metadata.")
    for key in (
        "python_version",
        "architecture",
        "distribution_flavor",
        "release_tag",
        "asset_name",
        "asset_url",
        "sha256",
        "sys_executable",
    ):
        if not runtime.get(key):
            fail(f"Runtime provenance is missing {key}.")
    if runtime["python_version"] != "3.12.14" or runtime["architecture"] != "x86_64":
        fail("Runtime provenance does not identify the pinned Python 3.12.14 x86_64 runtime.")
    if runtime["sys_executable"] != "runtime/python.exe":
        fail("Runtime provenance must identify the relative bundled executable.")

    inventory = load_json(root / "DEPENDENCY-INVENTORY.json")
    packages = inventory.get("packages")
    if not isinstance(packages, list):
        fail("Dependency inventory does not contain a package list.")
    installed = {
        canonical_name(item.get("name", ""))
        for item in packages
        if isinstance(item, dict)
    }
    if installed != EXPECTED_PACKAGE_NAMES:
        fail(
            "Unexpected portable dependency inventory: "
            f"missing={sorted(EXPECTED_PACKAGE_NAMES - installed)}; "
            f"unexpected={sorted(installed - EXPECTED_PACKAGE_NAMES)}"
        )
    forbidden_installed = installed & FORBIDDEN_PACKAGE_NAMES
    if forbidden_installed:
        fail(f"Forbidden packages are installed: {sorted(forbidden_installed)}")
    runtime_site = root / "runtime/Lib/site-packages"
    if runtime_site.is_dir():
        runtime_names = {item.name.casefold() for item in runtime_site.iterdir()}
        if any(name == "pip" or name.startswith("pip-") for name in runtime_names):
            fail("pip must not remain in the end-user runtime.")


def runtime_environment(root: Path, *, minimal_path: bool, offline: bool) -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONHOME"] = ""
    environment["PYTHONPATH"] = str(root / "app")
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    if minimal_path:
        system_root = environment.get("SystemRoot", r"C:\Windows")
        environment["PATH"] = str(Path(system_root) / "System32")
    if offline:
        environment["HTTP_PROXY"] = "http://127.0.0.1:9"
        environment["HTTPS_PROXY"] = "http://127.0.0.1:9"
        environment["ALL_PROXY"] = "http://127.0.0.1:9"
        environment["NO_PROXY"] = "127.0.0.1,localhost"
    return environment


def run_runtime(root: Path, code: str, *, minimal_path: bool = False) -> dict[str, Any]:
    runtime = root / "runtime/python.exe"
    if platform.system() != "Windows":
        fail("Bundled Windows runtime validation requires a Windows host.")
    if not runtime.is_file():
        fail(f"Bundled runtime is missing: {runtime}")
    completed = subprocess.run(
        [str(runtime), "-c", code],
        cwd=root,
        env=runtime_environment(root, minimal_path=minimal_path, offline=False),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        fail(
            "Bundled runtime identity check failed: "
            f"{completed.stdout}\n{completed.stderr}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        fail(f"Bundled runtime returned invalid identity JSON: {exc}")
    if not isinstance(payload, dict):
        fail("Bundled runtime identity was not an object.")
    expected = (root / "runtime/python.exe").resolve()
    actual = Path(str(payload.get("executable", ""))).resolve()
    if actual != expected:
        fail(f"Portable validation used the wrong executable: {actual} != {expected}")
    if payload.get("version") != "3.12.14":
        fail(f"Portable runtime reported unexpected Python version: {payload.get('version')}")
    return payload


def url_json(base_url: str, path: str, payload: dict[str, Any] | None = None) -> Any:
    url = base_url + path
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method="POST" if data else "GET")
    opener = build_opener(ProxyHandler({}))
    try:
        with opener.open(request, timeout=3) as response:
            if response.status != 200:
                fail(f"HTTP {response.status} for {path}")
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        fail(f"HTTP request failed for {path}: {exc}")


def wait_for_http(base_url: str, process: subprocess.Popen[str], timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            fail(
                "Portable server exited before becoming ready: "
                f"code={process.returncode}\n{stdout}\n{stderr}"
            )
        try:
            health = url_json(base_url, "/api/v1/health")
            if health.get("status") == "ok":
                return
        except ValidationError as exc:
            last_error = exc
        time.sleep(0.25)
    fail(f"Portable server did not become ready: {last_error}")


def start_server(root: Path, *, minimal_path: bool, offline: bool) -> tuple[subprocess.Popen[str], str]:
    runtime = root / "runtime/python.exe"
    process = subprocess.Popen(
        [str(runtime), "-m", "hcmcalc.api.main", "--host", "127.0.0.1", "--port", "8765"],
        cwd=root,
        env=runtime_environment(root, minimal_path=minimal_path, offline=offline),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    base_url = "http://127.0.0.1:8765"
    wait_for_http(base_url, process)
    return process, base_url


def calculate_case(base_url: str, method_id: str, expected: dict[str, Any]) -> dict[str, Any]:
    query = urlencode({"template_id": expected["template_id"], "unit_system": "imperial"})
    starting = url_json(base_url, f"/api/v1/analyses/{method_id}/starting-values?{query}")
    displayed = (
        {"rows": starting["segments"]}
        if method_id == "two_lane_facility"
        else starting["displayed_inputs"]
    )
    calculation = url_json(
        base_url,
        f"/api/v1/analyses/{method_id}/calculate",
        {
            "template_id": expected["template_id"],
            "unit_system": "imperial",
            "displayed_inputs": displayed,
        },
    )
    result = calculation.get("result") or {}
    if result.get("method") != expected["engine_method"]:
        fail(f"{method_id} returned the wrong engine identity: {result.get('method')}")
    answer = (calculation.get("presentation") or {}).get("answer") or {}
    if answer.get("value") != expected["answer"]:
        fail(f"{method_id} returned LOS {answer.get('value')}, expected {expected['answer']}")
    outputs = result.get("outputs") or {}
    for key, expected_value in expected["numeric"].items():
        actual_value = outputs.get(key)
        if not isinstance(actual_value, (int, float)) or not math.isclose(
            float(actual_value), float(expected_value), rel_tol=1e-9, abs_tol=1e-9
        ):
            fail(f"{method_id} numerical drift for {key}: {actual_value} != {expected_value}")
    return calculation


def validate_exports_and_projects(base_url: str, calculation: dict[str, Any]) -> None:
    method_id = "multilane_segment"
    request_base = {
        "template_id": calculation["template_id"],
        "unit_system": calculation["unit_system"],
        "displayed_inputs": calculation["displayed_inputs"],
        "calculation_fingerprint": calculation["calculation_fingerprint"],
        "input_snapshot_fingerprint": calculation["input_snapshot_fingerprint"],
        "result": calculation["result"],
    }
    for export_format in ("csv", "xlsx", "markdown", "json"):
        exported = url_json(
            base_url,
            f"/api/v1/analyses/{method_id}/export",
            request_base | {"export_format": export_format},
        )
        if exported.get("recalculated") is not False:
            fail(f"{export_format} export reported a recalculation.")
        if export_format == "xlsx":
            encoded = exported.get("content_base64")
            if not isinstance(encoded, str) or not base64.b64decode(encoded).startswith(b"PK"):
                fail("XLSX export did not return an OOXML payload.")
        else:
            content = exported.get("content")
            if not isinstance(content, str) or not content:
                fail(f"{export_format} export returned no text payload.")

    project_response = url_json(
        base_url,
        "/api/v1/projects/from-analysis",
        {"project_name": "Portable smoke", "analysis_snapshot": calculation},
    )
    project = project_response.get("project") or {}
    analysis = project.get("analyses", [])[0]
    scenario = analysis.get("scenarios", [])[0]
    validated = url_json(base_url, "/api/v1/projects/validate", {"project": project})
    if (validated.get("project") or {}).get("schema_version") != "2.0":
        fail("Project save/load validation did not retain Project v2.")

    changed_inputs = deepcopy(calculation["displayed_inputs"])
    changed_inputs["demand_volume_veh_h"] = float(changed_inputs["demand_volume_veh_h"]) + 100.0
    changed = url_json(
        base_url,
        f"/api/v1/analyses/{method_id}/calculate",
        {
            "template_id": calculation["template_id"],
            "unit_system": calculation["unit_system"],
            "displayed_inputs": changed_inputs,
        },
    )
    stale_response = url_json(
        base_url,
        "/api/v1/projects/update-scenario",
        {
            "project": project,
            "analysis_id": analysis["analysis_id"],
            "scenario_id": scenario["scenario_id"],
            "analysis_snapshot": changed,
        },
    )
    stale_project = stale_response.get("project") or {}
    stale_scenario = stale_project["analyses"][0]["scenarios"][0]
    if stale_scenario.get("result_status") != "stale" or stale_scenario.get("result") is not None:
        fail("Project current -> stale transition failed.")
    current_response = url_json(
        base_url,
        "/api/v1/projects/record-result",
        {
            "project": stale_project,
            "analysis_id": analysis["analysis_id"],
            "scenario_id": scenario["scenario_id"],
            "analysis_snapshot": changed,
        },
    )
    current_scenario = (current_response.get("project") or {})["analyses"][0]["scenarios"][0]
    if current_scenario.get("result_status") != "current":
        fail("Project stale -> recalculated current transition failed.")


def run_smoke(root: Path, *, offline: bool, minimal_path: bool) -> None:
    identity = run_runtime(
        root,
        "import json, platform, sys; print(json.dumps({'executable': sys.executable, 'version': platform.python_version(), 'machine': platform.machine()}))",
        minimal_path=minimal_path,
    )
    print(f"Bundled runtime: {identity['executable']} ({identity['version']}, {identity['machine']})")
    process, base_url = start_server(root, minimal_path=minimal_path, offline=offline)
    try:
        with build_opener(ProxyHandler({})).open(Request(base_url + "/", method="GET"), timeout=3) as response:
            if response.status != 200:
                fail(f"Root HTTP status was {response.status}")
        health = url_json(base_url, "/api/v1/health")
        if health.get("status") != "ok":
            fail("Health endpoint did not return status=ok")
        methods = url_json(base_url, "/api/v1/methods")
        method_ids = {item.get("method_id") for item in methods.get("methods", [])}
        if method_ids != set(EXPECTED_METHODS):
            fail(f"Method discovery mismatch: {sorted(method_ids)}")
        calculations = {
            method_id: calculate_case(base_url, method_id, expected)
            for method_id, expected in EXPECTED_METHODS.items()
        }
        validate_exports_and_projects(base_url, calculations["multilane_segment"])
        print("HTTP, seven-method calculation, export, and Project v2 smoke: PASS")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--zip", dest="zip_path", type=Path)
    parser.add_argument("--run-smoke", action="store_true")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--no-prerequisites", action="store_true")
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        if not root.is_dir():
            fail(f"Artifact root does not exist: {root}")
        validate_structure(root)
        validate_hygiene(root)
        validate_checksums(root)
        if args.zip_path:
            validate_zip(args.zip_path.resolve())
        if args.run_smoke:
            run_smoke(root, offline=args.offline, minimal_path=args.no_prerequisites)
        print(f"Portable artifact validation: PASS ({root})")
        return 0
    except ValidationError as exc:
        print(f"Portable artifact validation: FAIL — {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
