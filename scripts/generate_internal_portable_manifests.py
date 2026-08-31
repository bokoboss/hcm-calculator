"""Generate provenance, dependency, notice, and checksum files for a stage."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import sys
from typing import Any


PROJECT_NAME = "HCM Calculator"
PROJECT_VERSION = "0.9.0"
PROJECT_URL = "https://github.com/bokoboss/hcm-calculator"


def canonical_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def requirement_names(path: Path) -> set[str]:
    names: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        match = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==", line)
        if match:
            names.add(canonical_name(match.group(1)))
    return names


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def license_files_for_distribution(
    distribution: importlib.metadata.Distribution,
    app_root: Path,
) -> list[Path]:
    candidates: set[Path] = set()
    for relative in distribution.files or ():
        relative_path = Path(str(relative))
        if any(
            marker in relative_path.name.casefold()
            for marker in ("license", "copying", "notice")
        ):
            candidate = Path(distribution.locate_file(relative_path))
            if candidate.is_file() and inside(candidate, app_root):
                candidates.add(candidate.resolve())
    for declared in distribution.metadata.get_all("License-File") or ():
        candidate = Path(distribution.locate_file(declared))
        if candidate.is_file() and inside(candidate, app_root):
            candidates.add(candidate.resolve())
    return sorted(candidates, key=lambda item: item.as_posix().casefold())


def copy_license_files(
    distribution: importlib.metadata.Distribution,
    app_root: Path,
    license_root: Path,
) -> list[str]:
    name = distribution.metadata.get("Name") or "unknown-package"
    destination_root = license_root / "third-party" / safe_name(canonical_name(name))
    copied: list[str] = []
    for source in license_files_for_distribution(distribution, app_root):
        relative = source.relative_to(app_root)
        destination = destination_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        copied.append(destination.relative_to(license_root.parent).as_posix())
    return copied


def metadata_record(
    distribution: importlib.metadata.Distribution,
    app_root: Path,
    license_root: Path,
) -> dict[str, Any]:
    metadata = distribution.metadata
    name = metadata.get("Name") or "unknown-package"
    project_urls = sorted(metadata.get_all("Project-URL") or [])
    return {
        "name": name,
        "normalized_name": canonical_name(name),
        "version": metadata.get("Version") or "unknown",
        "license_expression": metadata.get("License-Expression"),
        "license_metadata": metadata.get("License"),
        "home_page": metadata.get("Home-page"),
        "project_urls": project_urls,
        "requires_python": metadata.get("Requires-Python"),
        "license_files": copy_license_files(distribution, app_root, license_root),
    }


def write_checksums(root: Path) -> None:
    checksum_path = root / "SHA256SUMS.txt"
    files = sorted(
        (item for item in root.rglob("*") if item.is_file() and item != checksum_path),
        key=lambda item: (
            item.relative_to(root).as_posix().casefold(),
            item.relative_to(root).as_posix(),
        ),
    )

    def digest_file(path: Path) -> str:
        digest = sha256()
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
        return f"{digest.hexdigest()}  {path.relative_to(root).as_posix()}"

    worker_count = min(16, max(4, (os.cpu_count() or 4) * 2))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        entries = list(executor.map(digest_file, files))
    checksum_path.write_text("\n".join(entries) + "\n", encoding="utf-8")


def generate_manifests(
    *,
    root: Path,
    source_sha: str,
    branch: str,
    source_dirty: bool,
    runtime_pin_path: Path,
    requirements_path: Path,
) -> None:
    root = root.resolve()
    app_root = root / "app"
    runtime_root = root / "runtime"
    license_root = root / "licenses"
    runtime_license = license_root / "PYTHON-LICENSE.txt"
    if not app_root.is_dir() or not runtime_root.is_dir():
        raise ValueError("Portable stage must contain app and runtime directories.")
    if not runtime_license.is_file():
        raise ValueError("The Python runtime license was not copied into the stage.")

    pin = json.loads(runtime_pin_path.read_text(encoding="utf-8"))
    expected_runtime = root / "runtime" / "python.exe"
    actual_runtime = Path(sys.executable).resolve()
    if actual_runtime != expected_runtime.resolve():
        raise RuntimeError(
            "Manifest generation must run with the bundled runtime: "
            f"expected {expected_runtime}, got {actual_runtime}"
        )
    if platform.python_version() != pin["python_version"]:
        raise RuntimeError(
            f"Bundled runtime version mismatch: {platform.python_version()} != {pin['python_version']}"
        )

    distributions = sorted(
        importlib.metadata.distributions(path=[str(app_root)]),
        key=lambda item: canonical_name(item.metadata.get("Name") or ""),
    )
    expected_packages = requirement_names(requirements_path) | {"hcm-calculator"}
    installed_packages = {
        canonical_name(item.metadata.get("Name") or "") for item in distributions
    }
    if installed_packages != expected_packages:
        missing = sorted(expected_packages - installed_packages)
        unexpected = sorted(installed_packages - expected_packages)
        raise RuntimeError(
            "Portable dependency closure differs from the pinned runtime requirements. "
            f"missing={missing}; unexpected={unexpected}"
        )

    package_records = [
        metadata_record(item, app_root, license_root) for item in distributions
    ]
    package_records.sort(key=lambda item: item["normalized_name"])

    version_path = root / "VERSION.txt"
    if PROJECT_VERSION not in version_path.read_text(encoding="utf-8"):
        raise ValueError("VERSION.txt does not identify HCM Calculator 0.9.0.")

    runtime_provenance = {
        "schema_version": 1,
        "component": "vendored_application_runtime",
        "project": {
            "name": PROJECT_NAME,
            "version": PROJECT_VERSION,
            "source_commit": source_sha,
            "branch": branch,
            "source_dirty": source_dirty,
            "homepage": PROJECT_URL,
        },
        "runtime": {
            "python_version": pin["python_version"],
            "platform": pin["platform"],
            "architecture": pin["architecture"],
            "target_triple": pin["target_triple"],
            "distribution": pin["provider"],
            "distribution_flavor": pin["distribution_flavor"],
            "distribution_linkage": pin["distribution_linkage"],
            "release_tag": pin["release_tag"],
            "release_url": pin["release_url"],
            "release_commit": pin["release_commit"],
            "asset_name": pin["asset_name"],
            "asset_url": pin["asset_url"],
            "archive_format": pin["archive_format"],
            "sha256": pin["sha256"],
            "sys_executable": actual_runtime.relative_to(root).as_posix(),
        },
    }
    write_json(runtime_root / "RUNTIME-PROVENANCE.json", runtime_provenance)

    inventory = {
        "schema_version": 1,
        "project": {
            "name": PROJECT_NAME,
            "version": PROJECT_VERSION,
            "source_commit": source_sha,
            "homepage": PROJECT_URL,
            "license_expression": "Proprietary",
        },
        "install_root": "app",
        "packages": package_records,
        "excluded_dependency_families": [
            "development",
            "pytest",
            "Playwright",
            "Node/Vite/pnpm",
            "Streamlit",
        ],
    }
    write_json(root / "DEPENDENCY-INVENTORY.json", inventory)

    notice_lines = [
        f"{PROJECT_NAME} {PROJECT_VERSION} — internal portable Windows x64 distribution",
        "",
        "This notice records package metadata observed in the staged application.",
        "It is not a legal opinion or a claim of legal review.",
        "",
        "Project",
        "-------",
        f"Name: {PROJECT_NAME}",
        f"Version: {PROJECT_VERSION}",
        "License metadata: Proprietary",
        f"Homepage: {PROJECT_URL}",
        f"Source commit: {source_sha}",
        "",
        "Python runtime",
        "---------------",
        f"Version: {pin['python_version']}",
        f"Provider: {pin['provider']}",
        f"Release tag: {pin['release_tag']}",
        f"Asset: {pin['asset_name']}",
        f"URL: {pin['asset_url']}",
        f"SHA-256: {pin['sha256']}",
        "License text: licenses/PYTHON-LICENSE.txt",
        "",
        "Installed application packages",
        "------------------------------",
    ]
    for package in package_records:
        notice_lines.extend(
            [
                f"- {package['name']} {package['version']}",
                f"  License expression: {package['license_expression'] or 'not declared'}",
                f"  License metadata: {package['license_metadata'] or 'not declared'}",
                f"  Homepage: {package['home_page'] or 'not declared'}",
            ]
        )
        if package["project_urls"]:
            notice_lines.append(f"  Project URLs: {'; '.join(package['project_urls'])}")
        if package["license_files"]:
            notice_lines.append(
                f"  Included license files: {', '.join(package['license_files'])}"
            )
        else:
            notice_lines.append("  Included license files: none recorded by package metadata")
    (license_root / "THIRD-PARTY-NOTICES.txt").write_text(
        "\n".join(notice_lines) + "\n", encoding="utf-8"
    )

    write_checksums(root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--source-dirty", action="store_true")
    parser.add_argument("--runtime-pin", type=Path, required=True)
    parser.add_argument("--requirements", type=Path, required=True)
    args = parser.parse_args()
    generate_manifests(
        root=args.root,
        source_sha=args.source_sha,
        branch=args.branch,
        source_dirty=args.source_dirty,
        runtime_pin_path=args.runtime_pin,
        requirements_path=args.requirements,
    )
    print(f"Generated portable manifests in {args.root.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
