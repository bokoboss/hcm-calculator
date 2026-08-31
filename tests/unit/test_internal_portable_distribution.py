import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
PORTABLE_SOURCE = ROOT / "distribution" / "internal"


def test_portable_runtime_pin_is_immutable_and_authoritative() -> None:
    pin = json.loads((PORTABLE_SOURCE / "runtime-pin.json").read_text(encoding="utf-8"))

    assert pin["provider"] == "astral-sh/python-build-standalone"
    assert pin["release_tag"] == "20260814"
    assert pin["release_commit"] == "38d35dcf0e212ca02eed8ebc11d0c92906387d56"
    assert pin["python_version"] == "3.12.14"
    assert pin["platform"] == "windows"
    assert pin["architecture"] == "x86_64"
    assert pin["target_triple"] == "x86_64-pc-windows-msvc"
    assert pin["distribution_flavor"] == "install_only"
    assert pin["distribution_linkage"] == "shared"
    assert pin["asset_name"] == "cpython-3.12.14+20260814-x86_64-pc-windows-msvc-install_only.tar.gz"
    assert re.fullmatch(r"[0-9a-f]{64}", pin["sha256"])
    assert pin["asset_url"].endswith(pin["asset_name"].replace("+", "%2B"))


def test_portable_dependency_closure_is_runtime_only() -> None:
    requirements = (PORTABLE_SOURCE / "runtime-requirements.txt").read_text(encoding="utf-8")
    names = {
        match.group(1).casefold().replace("_", "-")
        for match in re.finditer(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==", requirements, re.MULTILINE)
    }

    assert {"fastapi", "openpyxl", "pydantic", "pyyaml", "uvicorn"} <= names
    assert not names & {"pytest", "playwright", "streamlit", "httpx2", "build"}
    assert all("==" in line for line in requirements.splitlines() if line and not line.startswith("#"))


def test_portable_launcher_is_additional_and_loopback_only() -> None:
    launcher = (PORTABLE_SOURCE / "Run HCM Calculator.bat").read_text(encoding="utf-8").casefold()

    assert "%~dp0" in launcher
    assert "runtime\\python.exe" in launcher
    assert "hcmcalc.api.main" in launcher
    assert "--host 127.0.0.1" in launcher
    assert "--port 8765" in launcher
    assert "--open-browser" in launcher
    assert "taskkill" not in launcher
    assert "node" not in launcher
    assert "npm" not in launcher
    assert "pnpm" not in launcher
    assert "pip install" not in launcher
    assert "py.exe" not in launcher


def test_thai_user_guide_contains_only_end_user_portable_steps() -> None:
    guide = (PORTABLE_SOURCE / "README-TH.txt").read_text(encoding="utf-8")

    for required in (
        "Windows 10/11",
        "64-bit",
        "แตกไฟล์ ZIP",
        "ดับเบิลคลิก",
        "Run HCM Calculator.bat",
        "http://127.0.0.1:8765/",
        "Ctrl+C",
        "Project JSON",
        "Excel",
        "CSV",
        "ไม่ต้องติดตั้ง Python",
        "ไม่ต้องใช้สิทธิ์ Administrator",
        "ไม่ต้องใช้อินเทอร์เน็ต",
        "Windows Defender",
        "AppLocker",
        "EDR",
        "ติดต่อ IT",
        "ห้ามปิดหรือหลีกเลี่ยง",
        "0.9.0",
        "ผู้ติดต่อภายในบริษัท",
    ):
        assert required in guide

    assert "setup_app" not in guide
    assert "pip install" not in guide
