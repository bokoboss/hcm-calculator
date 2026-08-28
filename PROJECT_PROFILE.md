# Project Profile

## Identity
- Project name: HCM Calculator
- Repository URL: https://github.com/bokoboss/hcm-calculator
- Authoritative local path: `D:\R&D\hcm-calculator`
- Primary branch: `main`
- Phase 3 branch: `codex/application-rebuild-phase-3-release`
- Package/application version: `0.9.0`

## Current accepted baseline and release state
- Authoritative remote `main` at Phase 3 preflight: `da64a662094458738f8c9cae7213bcf04a6f5007`.
- Accepted Phase 2 implementation ancestor: `868c00616b6cb3b74308777c4753e1af80bb863e`.
- Phase 3 is an implementation candidate carried by PR #141; it is not merged
  or accepted until the owner completes ChatGPT application-rebuild acceptance.
- The rebuilt React/FastAPI launcher is the intended normal installed-use path.
  Streamlit remains available as the qualified compatibility path.
- The owner-authorized stale local `.agent/` and `mockups/` paths were removed
  during preflight and are not Phase 3 authority; neither is recreated here.

## Technology stack
- Python 3.12+ package with qualified HCM engines and pytest.
- React + TypeScript + Vite frontend, served in release use by FastAPI.
- Python framework-independent application layer remains between the API and
  the existing qualified HCM engines.
- Package manager: pip/Hatchling for Python; pnpm with the committed lockfile
  for frontend development and qualification.
- Windows launchers: `run_app.ps1` / `run_app.bat` for the rebuilt UI and
  `run_streamlit.ps1` / `run_streamlit.bat` for compatibility.

## Standard commands
### Install/bootstrap
```text
python -m pip install -e ".[dev,ui]"
```

### Python and contract validation
```text
python -m pytest
python -m compileall -q src tests
python scripts/check_openapi_contract.py
git diff --check
```

### Frontend and browser validation
```text
pnpm --dir frontend run typecheck
pnpm --dir frontend run test
pnpm --dir frontend run build
pnpm --dir frontend exec playwright test --project=chromium
```

### Build/package and local run
```text
python -m build --wheel
.\run_app.ps1
.\run_streamlit.ps1
```

Normal installed use serves the compiled SPA from the Python distribution and
does not require Node or Vite at runtime. The Phase 3 qualification record
contains the release-like wheel, isolated-runtime, launcher, and browser
evidence for PR #141.

## Architecture and invariants
- Accepted R0 architecture: React + TypeScript + Vite -> FastAPI -> a
  framework-independent Python application layer -> qualified HCM engines.
- Python is the sole HCM numerical authority; TypeScript contains no HCM
  formulas.
- Existing method identifiers, input contracts, Project v2 schema/fingerprints,
  current/stale result semantics, export no-rerun behavior, and Streamlit
  compatibility remain protected.
- Handoff, unavailable, and capacity-failure states remain distinct; the UI
  does not invent LOS, speed, density, or other numerical outputs.
- No qualified engine methodology, numerical behavior, or scope was expanded
  by the Phase 3 application migration.
- Engineering diagrams are sourced from the existing Python package asset set;
  React does not maintain a duplicate engineering asset set.

## Phase 3 delivery scope
The rebuilt application now exposes all seven delivered calculation methods
through one persistent bilingual workspace navigation model:

- Two-Lane Segment
- Two-Lane Facility (distinct locked Facility template semantics)
- Multilane Segment
- Basic Freeway Segment
- Weaving Segment
- Merge Segment
- Diverge Segment

Phase 3 also qualifies direct method routing, safe draft/project transitions,
explicit validated starters and blank/custom semantics, structured horizontal
curve editing, progressive Weaving evidence disclosure, existing schematics,
results-first current/stale flows, Project v2/legacy closure, grouped exports,
linked validation recovery, responsive EN/TH presentation, and the default
rebuilt launcher. Detailed evidence is maintained in
`docs/application_rebuild/phase3_release_qualification.md`.

## Validation and release policy
- Every change goes through a reviewable PR; PR #141 links the Phase 3 work to
  Issue #139 with `Closes #139` and is intentionally not merged by this task.
- Release claims require objective local and CI evidence, including the full
  pytest suite, frontend tests/build, full Playwright coverage, package/runtime
  smoke, both launchers, OpenAPI drift, compileall, and diff checks.
- HCM Chapter 26/27/28 evidence and existing qualified engine fixtures remain
  the authority for supported calculation paths. UI work must not be used to
  imply broader methodology support.
