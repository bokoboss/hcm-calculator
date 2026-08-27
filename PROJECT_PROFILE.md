# Project Profile

## Identity
- Project name: HCM Calculator
- Repository URL: https://github.com/bokoboss/hcm-calculator
- Authoritative local path: `C:\Users\kittipat_t\Documents\hcm-calculator` (workflow adoption executed in an isolated sibling worktree)
- Primary branch: `main`
- Package/application version: `0.9.0` (`pyproject.toml` at accepted Phase 1 baseline `cfcfe7af14d821dadc04c4f067322ef5d3760c1c`).

## Current accepted baseline
- Accepted branch: `main`
- Accepted HEAD SHA: `cfcfe7af14d821dadc04c4f067322ef5d3760c1c`
- Accepted date: 2026-08-27
- Current phase/milestone: **Phase 1 — Application Foundation accepted and merged; Phase 2 — Prototype & Architecture Validation authorized but not yet started.**
- Last accepted implementation PR / CI run: PR #133 merged at `cfcfe7af14d821dadc04c4f067322ef5d3760c1c`; GitHub Actions R1 qualification run #249 passed all four jobs.
- R1 accepted foundation includes the framework-independent application layer, thin FastAPI boundary, React/TypeScript/Vite shell, seven-method backend registry, contract-safe frontend delivery registry, bilingual shared primitives, OpenAPI drift protection, and release-like Python-served SPA/browser qualification.
- Installed Engineering Development Workflow: v1.4.1 at exact source commit `3547ae260feacf8fc9a102b2abfdb13881e36dab`.

## Technology stack
- Languages: Python 3.12+; accepted rebuild target adds TypeScript.
- Frameworks: Pydantic and optional Streamlit remain; the accepted rebuild foundation now includes React + TypeScript + Vite and a FastAPI boundary on `main`.
- Package manager: `pip`/Hatchling for Python; frontend uses `pnpm` with the committed lockfile/package-manager declaration.
- Supported OS/runtime: local Python application; repository launcher and setup scripts provide Windows support; CI runs on Ubuntu with Python 3.12.

## Standard commands
### Install/bootstrap
```text
python -m pip install -e ".[dev]"
```
### Fast validation
```text
python -m pytest
git diff --check
```
### Full validation
```text
python -m pytest
python -m compileall -q src tests
```
### Build/package
```text
python -m build
```
### Local run
```text
python -m streamlit run src/hcmcalc/ui/streamlit_app.py
```

## Architecture / invariants
- Accepted R0 architecture: React + TypeScript + Vite -> FastAPI -> framework-independent Python application layer -> existing qualified HCM engines.
- Python is the calculation authority; TypeScript must not duplicate HCM formulas.
- `docs/application_rebuild/r0_architecture_acceptance_review.md` is the highest-authority R0 document, followed by its README, implementation plan, technology architecture, and remaining R0 specifications.
- Streamlit remains runnable during migration; Phase 1 has proven release-like local same-origin serving of the compiled SPA and API without a Node/Vite runtime server.

## Protected behavior
Changes must not alter the following unless explicitly approved:
- Qualified HCM engine formulas, numerical outputs, method contracts, and validation evidence.
- Project schema compatibility and fingerprint-derived current/stale result behavior.
- Reports/exports must represent accepted current results and must not silently rerun calculations.
- The seven existing engineering workflows and the qualified Streamlit migration path.

## Important paths
- Source: `src/hcmcalc/`
- Tests: `tests/`
- Documentation: `docs/`, especially `docs/application_rebuild/`
- Generated output: `output/`
- Local-only / sensitive / licensed data: `local_references/`, `references/`, and local environment directories; do not publish unless explicitly authorized.

## Validation matrix
| Gate | Command / Method | Required |
|---|---|---|
| Unit / targeted | `python -m pytest` | Required |
| Integration / regression | repository pytest suite and relevant Chapter 26/reference fixtures | Required for affected behavior |
| Browser/UI | Streamlit smoke/AppTest and browser qualification when UI is affected | Required for UI changes |
| Build/package/runtime | `python -m compileall -q src tests`; `python -m build` when packaging is in scope | Required for affected release/package work |
| Real-data/reference | HCM Chapter 26 fixtures and documented provenance | Required for calculation changes |
| CI | GitHub Actions `Tests` workflow on the PR | Required |

## Execution characteristics
- Typical task ambiguity: high when requirements touch HCM scope, accepted architecture, or migration compatibility; resolve against repository evidence before coding.
- High-risk areas: HCM formulas/tables, project schema/fingerprints, exports/reports, localization, Streamlit state, and R1 API/frontend seams.
- Modules safe to parallelize: isolated documentation, tests, and bounded application components after contracts are fixed.
- Modules tightly coupled / single-owner: engine behavior, project persistence, cross-workflow UI state, and release qualification.
- Preferred local execution constraints: work from a clean branch/worktree; keep the Streamlit path runnable; do not require cloud services for local operation.

## Git / release policy
- Branch naming: `codex/` for implementation branches unless a task-specific branch name is explicitly required.
- Commit policy: focused commits; no history rewriting.
- PR policy: all changes through a reviewable PR with commands, tests, diff summary, CI, and known limitations recorded.
- Merge policy: do not merge automatically; acceptance requires evidence beyond a commit or local test pass.
- Release policy: preserve accepted HCM behavior and record qualification evidence, exact relevant SHAs, and package/runtime results.

## Current known limitations / risks
- The rebuilt React/FastAPI application foundation is accepted, but no rebuilt HCM calculation workflow is delivered yet; all seven methods remain reference-only in the rebuilt UI until individually delivered and contract-qualified.
- The qualified Streamlit application remains the active calculation surface during representative-prototype migration.
- Project v2 durable persistence is not implemented or accepted; legacy v0.9 / schema 1.2 compatibility remains protected.
- Do not mass-port all seven methods before representative prototype architecture is accepted.

## Current next objective
- Execute **Phase 2 — Prototype & Architecture Validation** as one managed phase with internal checkpoints: Multilane representative workflow, Two-Lane Facility grid workflow, Project/Scenario/Compare closure, then architecture acceptance.
- Prefer one bounded Codex implementation cycle where architecture remains sound; stop only on genuine contract/architecture conflicts.
- Do not begin Phase 3 full seven-method migration until Phase 2 is explicitly accepted.
