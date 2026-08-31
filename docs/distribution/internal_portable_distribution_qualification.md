# Internal Portable Distribution Qualification

Status: implementation and local qualification in progress. Company-machine
UAT status: **PENDING HUMAN UAT**.

This record covers GitHub Issue [#142](https://github.com/bokoboss/hcm-calculator/issues/142)
and the additional internal portable distribution path. It does not change HCM
methodology, numerical engines, application contracts, or the normal
developer/source launchers.

## Baseline and source

- Repository: `https://github.com/bokoboss/hcm-calculator`
- Accepted source baseline: `28c1a76ad379c332a5c50fc756bdcdf6975cd957`
- Implementation branch: `codex/internal-portable-distribution`
- Artifact version: `0.9.0`
- Artifact source commit: recorded in `runtime/RUNTIME-PROVENANCE.json`
- Final repository HEAD at record closeout: recorded below after the final
  qualification-document commit.

## Runtime provenance

- Provider: `astral-sh/python-build-standalone`
- Release tag: `20260814`
- Release commit: `38d35dcf0e212ca02eed8ebc11d0c92906387d56`
- Python: `3.12.14`
- Platform/architecture: Windows x86_64
- Distribution flavor/linkage: `install_only` / shared MSVC
- Asset: `cpython-3.12.14+20260814-x86_64-pc-windows-msvc-install_only.tar.gz`
- Asset URL: `https://github.com/astral-sh/python-build-standalone/releases/download/20260814/cpython-3.12.14%2B20260814-x86_64-pc-windows-msvc-install_only.tar.gz`
- Asset SHA-256: `7330282b47cd43a66b702d39078d2e5a88e580cee351d82f95045f21f5ee042a`
- Committed pin: `distribution/internal/runtime-pin.json`

## Build and artifact

- Build command: `.\scripts\build_internal_portable.ps1`
- Final ZIP: `HCM-Calculator-v0.9.0-Internal-Windows-x64.zip`
- ZIP path/size/SHA-256: recorded from the final local build below.
- ZIP payload is generated under an ignored `.tmp/internal-portable/` path and
  is not committed or uploaded as a public GitHub artifact.
- ZIP container metadata is normalized by the deterministic ZIP helper; the
  staged file set and `SHA256SUMS.txt` are the content authority.

Expected extracted tree:

```text
HCM-Calculator-v0.9.0-Internal-Windows-x64/
├─ Run HCM Calculator.bat
├─ README-TH.txt
├─ VERSION.txt
├─ SHA256SUMS.txt
├─ DEPENDENCY-INVENTORY.json
├─ licenses/
│  ├─ PYTHON-LICENSE.txt
│  ├─ THIRD-PARTY-NOTICES.txt
│  └─ third-party/...
├─ runtime/
│  ├─ python.exe
│  ├─ RUNTIME-PROVENANCE.json
│  └─ private CPython runtime files
└─ app/
   ├─ hcmcalc/
   └─ runtime dependency packages and metadata
```

## Dependency and licensing evidence

- Normal runtime dependencies are the exact closure in
  `distribution/internal/runtime-requirements.txt`.
- Dev/test dependencies, Playwright, Node/Vite/pnpm, and Streamlit are not
  installed into `app`.
- The builder generates `DEPENDENCY-INVENTORY.json` from staged distribution
  metadata, including versions, license metadata, project URLs, and practical
  license-file copies.
- `licenses/PYTHON-LICENSE.txt` is copied from the bundled runtime.
- `licenses/THIRD-PARTY-NOTICES.txt` records the observed metadata. No legal
  review or legal-compliance claim is made.

## Qualification evidence

| Gate | Result | Evidence |
|---|---|---|
| G1 deterministic build | Pending local closeout | Two-build normalized staged-file comparison and `SHA256SUMS.txt` |
| G2 no Python/Node prerequisite | Pending local closeout | Bundled `runtime/python.exe`; minimal PATH smoke |
| G3 offline execution | Pending local closeout | Loopback smoke with external proxy blocked |
| G4 seven-method smoke | Pending local closeout | Bundled-runtime API smoke against the accepted reference identities/values |
| G5 save/load/export | Pending local closeout | Project v2 current/stale/recalculate and CSV/XLSX/Markdown/JSON smoke |
| G6 isolation/security | Pending local closeout | Explicit 127.0.0.1 launcher/API and no package-manager runtime path |
| G7 artifact hygiene | Pending local closeout | ZIP inventory and validator exclusion checks |
| G8 provenance/licenses | Pending local closeout | Runtime provenance, inventory, notices, checksums |
| G9 normal regression | Pending local closeout | Python, API/OpenAPI, compileall, frontend, Playwright, diff checks |
| G10 company-machine UAT | **PENDING HUMAN UAT** | No representative company-machine evidence is available in this environment |

Portable validation must report `runtime/python.exe` as `sys.executable` and
must not use the machine Python or Node for application execution. The launcher
binds the application to `127.0.0.1:8765`; it does not modify registry/PATH,
install a service, create firewall rules, elevate privileges, or kill unrelated
processes.

## Closeout values

To be filled from the clean build and regression run:

- Artifact build source commit: `PENDING`
- Final repository HEAD: `PENDING`
- ZIP size: `PENDING`
- ZIP SHA-256: `PENDING`
- Bundled `sys.executable`: `PENDING`
- Seven-method result table: `PENDING`
- Save/load/export result: `PENDING`
- Offline/no-Python/no-Node result: `PENDING`
- Artifact hygiene result: `PENDING`
- CI run/status: `PENDING`
- Company-machine UAT: **PENDING HUMAN UAT**
- Known warnings: unsigned/unapproved executables may be blocked by corporate
  endpoint policy; if observed, record the exact policy message and contact IT.
