# Project Profile

## Identity
- Project name: HCM Calculator
- Repository URL: https://github.com/bokoboss/hcm-calculator
- Authoritative local path: `C:\Users\kittipat_t\Documents\hcm-calculator` (workflow adoption executed in an isolated sibling worktree)
- Primary branch: `main`
- Package/application version: `0.9.0` (`pyproject.toml` at accepted baseline `0fb3b8f43a99d6a0a167bedf588dcd2e27993782`).

## Current accepted baseline
- Accepted branch: `main`
- Accepted HEAD SHA: `0fb3b8f43a99d6a0a167bedf588dcd2e27993782`
- Accepted date: 2026-08-24
- Current phase/milestone: R0 accepted and merged; R1 Application Foundation authorized but not accepted.
- Last accepted PR / CI run: PR #129 merged at `6482808c06fd4bfc3f6d6ef246bd6efdc58c4e65`; GitHub Actions `Tests` run #241 for current `main` passed.
- PR #133 (`codex/application-rebuild-r1-foundation`) is open and in progress; it is not an accepted baseline for this project.
- Installed Engineering Development Workflow: v1.4.1 at exact source commit `3547ae260feacf8fc9a102b2abfdb13881e36dab`.

## Technology stack
- Languages: Python 3.12+; accepted rebuild target adds TypeScript.
- Frameworks: Pydantic and optional Streamlit today; React + Vite frontend and FastAPI boundary are the accepted rebuild target.
- Package manager: `pip`/Hatchling for Python; frontend package manager is not yet established on `main`.
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
- Streamlit remains runnable during migration; R1 must prove release-like local same-origin serving of the compiled SPA and API.

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
- `main` currently passes the repository `Tests` workflow.
- PR #133 is open and its checks were pending/merge state unstable at preflight; do not modify or resume it as part of workflow adoption.
- The frontend/API rebuild is authorized by R0 but is not yet a completed architecture implementation.

## Current next objective
- Complete R1 Application Foundation under the accepted R0 architecture through its own PR; keep workflow-adoption changes separate from PR #133.
