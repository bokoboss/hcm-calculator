# Internal Portable Distribution Qualification

Status: implementation and local qualification complete. Company-machine UAT
status: **PENDING HUMAN UAT**.

This record covers GitHub Issue [#142](https://github.com/bokoboss/hcm-calculator/issues/142)
and the additional internal portable distribution path. It does not change HCM
methodology, numerical engines, application contracts, or the normal
developer/source launchers.

## Baseline and source

- Repository: `https://github.com/bokoboss/hcm-calculator`
- Accepted source baseline: `28c1a76ad379c332a5c50fc756bdcdf6975cd957`
- Implementation branch: `codex/internal-portable-distribution`
- Artifact version: `0.9.0`
- Artifact source commit: `99d594cd0c536e0f0c8853ae3bc612ea9d02ecab`
- Final repository HEAD at record closeout: the commit that adds this
  qualification-document closeout; the exact SHA is reported with the PR
  because this document cannot embed its own Git object ID.

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
- ZIP path: `.tmp/internal-portable/HCM-Calculator-v0.9.0-Internal-Windows-x64.zip`
- ZIP size: `22,257,538` bytes
- ZIP SHA-256: `6c1ad5a11119d3adcbb30cece3186ad7d1b0f607d9fab7c0cb374db0c1f0aae6`
- Two independent clean builds produced identical staged file sets (3,117
  files), `SHA256SUMS.txt`, and ZIP SHA-256 values.
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
  license-file copies (15 third-party license files copied in the final stage).
- `licenses/PYTHON-LICENSE.txt` is copied from the bundled runtime.
- `licenses/THIRD-PARTY-NOTICES.txt` records the observed metadata. No legal
  review or legal-compliance claim is made.

## Qualification evidence

| Gate | Result | Evidence |
|---|---|---|
| G1 deterministic build | PASS | Two independent clean builds matched at 3,117 staged files, `SHA256SUMS.txt`, and ZIP SHA-256 `6c1ad5a1…` |
| G2 no Python/Node prerequisite | PASS | Bundled `runtime/python.exe` 3.12.14; launcher and validator used `PATH=C:\Windows\System32` |
| G3 offline execution | PASS | Packaged smoke completed with external proxies blocked and loopback proxy bypassed |
| G4 seven-method smoke | PASS | Bundled-runtime API smoke matched all seven accepted engine identities, LOS values, and numeric evidence below |
| G5 save/load/export | PASS | Project v2 current/stale/recalculate plus CSV/XLSX/Markdown/JSON exports; exports reported `recalculated=false` |
| G6 isolation/security | PASS locally | Launcher/API bound to `127.0.0.1:8765`; no install, elevation, registry/PATH, firewall, service, or unrelated-process termination |
| G7 artifact hygiene | PASS | ZIP validator found no source-control, test, cache, Node/Vite, Streamlit, credential, or package-manager payloads |
| G8 provenance/licenses | PASS | Exact runtime pin, SHA-256 provenance, dependency inventory, 15 third-party license copies, notices, and checksums |
| G9 normal regression | PARTIAL — known baseline limitation | 1,162 pytest pass; OpenAPI snapshot, compileall, frontend typecheck/unit/build pass; Playwright 33 passed/1 failed on an existing error-summary expectation |
| G10 company-machine UAT | **PENDING HUMAN UAT** | No representative company-machine evidence is available in this environment |

Portable validation must report `runtime/python.exe` as `sys.executable` and
must not use the machine Python or Node for application execution. The launcher
binds the application to `127.0.0.1:8765`; it does not modify registry/PATH,
install a service, create firewall rules, elevate privileges, or kill unrelated
processes.

Seven-method smoke results:

| Method | Engine identity | LOS | Numeric evidence |
|---|---|---|---|
| Two-Lane Segment | `hcm7_ch15_two_lane_motorized` | D | follower density `10.08622955622713` |
| Two-Lane Facility | `hcm7_ch15_two_lane_motorized` | C | facility follower density `7.286363636363637` |
| Multilane Segment | `hcm7_multilane_los` | C | density `18.08754208754209` |
| Basic Freeway Segment | `hcm7_basic_freeway_segment` | C | density `18.776944117286437` |
| Weaving Segment | `hcm7_v70_freeway_weaving_segment` | C | density `26.284440902466354` |
| Merge Segment | `hcm7_v70_freeway_merge_segment` | D | density `28.166583333333328` |
| Diverge Segment | `hcm7_v70_freeway_diverge_segment` | D | density `31.1264773844` |

Local regression detail:

- `python -m pytest`: `1162 passed`.
- `python -m compileall -q src tests scripts`: pass.
- `python scripts/check_openapi_contract.py`: snapshot matches FastAPI.
- Frontend typecheck, 7 frontend unit files / 22 tests, and production build:
  pass.
- Full Playwright suite: 33 passed, 1 failed. The failure is the existing
  `frontend/playwright/phase3.final-remediation.spec.ts` expectation for an
  error-summary message after invalid access-point-density input; no frontend
  source or test was changed for this portable-only issue.
- Final extracted ZIP validation from a path containing spaces, offline and
  with no Python/Node on `PATH`: pass. Direct `.bat` launcher smoke returned
  health `ok` and seven discoverable methods, then stopped cleanly with no
  listener left on port 8765.

## Closeout values

- Artifact build source commit: `99d594cd0c536e0f0c8853ae3bc612ea9d02ecab`
- Final repository HEAD: the closeout-document commit; exact SHA is reported
  in the PR/agent closeout.
- ZIP size: `22,257,538` bytes
- ZIP SHA-256: `6c1ad5a11119d3adcbb30cece3186ad7d1b0f607d9fab7c0cb374db0c1f0aae6`
- Bundled `sys.executable`: `runtime/python.exe` (CPython `3.12.14`, AMD64)
- Seven-method result table: all seven pass; see the table above.
- Save/load/export result: Project v2 current → stale → recalculated current;
  CSV/XLSX/Markdown/JSON exports pass without recalculation.
- Offline/no-Python/no-Node result: pass in validator and extracted path with
  spaces; direct launcher health/method smoke also pass.
- Artifact hygiene result: pass; 3,117 files and 15 copied third-party license
  files, with no forbidden payloads.
- CI run/status: recorded after PR creation; no merge is authorized here.
- Company-machine UAT: **PENDING HUMAN UAT**
- Known warnings: Starlette deprecation warnings are emitted by the qualified
  application dependency; the existing Playwright baseline failure remains
  documented above; unsigned/unapproved executables may be blocked by
  corporate endpoint policy. If observed, record the exact policy message and
  contact IT.
