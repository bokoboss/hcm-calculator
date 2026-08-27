# Project Profile

## Identity
- Project name: HCM Calculator
- Repository URL: https://github.com/bokoboss/hcm-calculator
- Authoritative local path: `C:\Users\kittipat_t\Documents\hcm-calculator` (workflow adoption executed in an isolated sibling worktree)
- Primary branch: `main`
- Package/application version: `0.9.0` (`pyproject.toml` at accepted Phase 2 baseline `868c00616b6cb3b74308777c4753e1af80bb863e`).

## Current accepted baseline
- Accepted branch: `main`
- Accepted HEAD SHA: `868c00616b6cb3b74308777c4753e1af80bb863e`
- Accepted date: 2026-08-27
- Current phase/milestone: **Phase 2 — Prototype & Architecture Validation accepted and merged; Phase 3 — Full Migration & Release authorized but not yet started.**
- Last accepted implementation PR / CI run: PR #137 merged at `868c00616b6cb3b74308777c4753e1af80bb863e`; GitHub Actions qualification run #255 passed all four jobs.
- Accepted Phase 2 adds production rebuilt Multilane and Two-Lane Facility workflows, Project v2 Project/Analysis/Scenario/Result persistence and comparison, legacy 1.0/1.1/1.2 migration, no-rerun exports, committed visual evidence, and browser-qualified bilingual representative workflows.
- Final Phase 2 UI-capable qualification on the accepted head: Streamlit 1.62.0; `1116 passed, 0 skipped, 0 failed`; wheel/runtime smoke passed.
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
- Streamlit remains runnable during migration; Phase 2 has proven release-like local same-origin serving of the compiled SPA and API for real Multilane and Two-Lane Facility workflows without a Node/Vite runtime server.

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
- Five current workflows remain reference-only in the rebuilt UI: Two-Lane Segment, Basic Freeway Segment, Weaving, Merge, and Diverge.
- The qualified Streamlit application remains runnable and is still required as the compatibility path until Phase 3 default-UI/release qualification is accepted.
- Project v2 is accepted for the rebuilt application; legacy schema 1.0/1.1/1.2 import compatibility remains protected.
- Phase 3 must migrate the remaining methods without weakening numerical equivalence, current/stale fingerprints, capacity/handoff semantics, reports/exports, or offline/local runtime assumptions.

## Current next objective
- Execute **Phase 3 — Full Migration & Release** as the final application-rebuild phase.
- Migrate Two-Lane Segment, Basic Freeway Segment, Weaving, Merge, and Diverge through the accepted Phase 2 application/API/frontend patterns.
- Complete all-seven-method parity, Project v2 integration, bilingual/browser/UAT qualification, packaging/runtime checks, default rebuilt-UI transition, release qualification, and milestone closure.
- Do not remove the Streamlit compatibility path or change release/default launch behavior until the final Phase 3 acceptance gate passes.
