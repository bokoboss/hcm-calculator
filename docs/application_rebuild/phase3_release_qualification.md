# Phase 3 — Full Migration & Release Qualification

Status: implementation candidate on `codex/application-rebuild-phase-3-release`;
PR #141 is open against `main`, links `Closes #139`, and is intentionally not
merged. Final application-rebuild acceptance remains with ChatGPT/the
repository owner.

This is the release evidence index for Issue #139 and the consolidated PR #141
remediation packet. The accepted Phase 2 implementation ancestor is
`868c00616b6cb3b74308777c4753e1af80bb863e`. The Phase 3 branch started from
remote `main` at `da64a662094458738f8c9cae7213bcf04a6f5007` in the authoritative
repository `D:\R&D\hcm-calculator`.

## Migration order and delivered identities

Phase 3 keeps the Python application/engine boundary as the numerical
authority. React owns presentation and interaction state; it does not contain
HCM equations or duplicate qualified engine logic.

| Order | `method_id` | Engine result identity | Application input contract | Project type |
| --- | --- | --- | --- | --- |
| 1 | `two_lane_segment` | `hcm7_ch15_two_lane_motorized` | `phase_5_product_integration` | `manual_single_segment` |
| 2 | `basic_freeway_segment` | `hcm7_basic_freeway_segment` | `phase_10_product_integration` | `manual_basic_freeway_v0` |
| 3 | `weaving_segment` | `hcm7_v70_freeway_weaving_segment` | `hcm_7_0_weaving_segment_operational_v1` | `manual_freeway_weaving_segment_v1` |
| 4 | `merge_segment` | `hcm7_v70_freeway_merge_segment` | `hcm7_v70_chapter_14_isolated_right_side_one_lane_merge_operational` | `manual_freeway_merge_segment_v1` |
| 5 | `diverge_segment` | `hcm7_v70_freeway_diverge_segment` | `hcm7_v70_chapter_14_isolated_right_side_one_lane_diverge_operational` | `manual_freeway_diverge_segment_v1` |

The two existing Phase 2 methods remain part of the same seven-method registry:

| `method_id` | Engine/result contract | Project type | Semantics |
| --- | --- | --- | --- |
| `two_lane_facility` | `hcm7_ch15_two_lane_motorized` / `phase_5_product_integration` | `manual_two_lane_facility_v1` | distinct locked Facility template |
| `multilane_segment` | `hcm7_multilane_los` / `phase_8` | `manual_multilane_v0` | bounded segment worksheet |

## Consolidated UX/IA remediation

The whole-application refinement authorized by PR #141 implements the
interaction/layout review #5052090168 and page-grammar review #5052568561.
It is a bounded React/FastAPI product pass; the accepted Python numerical,
method, Project v2, fingerprint, and warning/capacity/handoff semantics are
unchanged.

- The desktop workspace has persistent direct navigation for Workspace Home,
  Project Workspace, New Analysis, all three roadway methods, all four freeway
  methods, and Supported Methods. The narrow layout uses a compact selector;
  method switching preserves the active workflow and New Analysis reliably
  opens the chooser.
- Untouched/default worksheets switch immediately. Modified quick-analysis
  drafts ask for confirmation; dismissal preserves the draft. Project scenario
  edits keep the method immutable and a confirmed switch exits/cancels the
  edit without mutating the scenario method.
- Editable workflows lead with `Start with / เริ่มต้นด้วย`: an explicitly
  identified validated example, a neutral blank worksheet, or a custom starter.
  The default examples are `TLH-CH15-001`, `MLH-CH26-004-EB`,
  `BF-CH26-001`, `WVG-CH27-001`,
  `chapter_28_example_1_merge`, and
  `chapter_28_example_3_diverge_component`. Two-Lane Facility remains a
  distinct `Facility template` workflow.
- Example loading displays the bilingual notices `Example values loaded` /
  `กำลังใช้ค่าตัวอย่าง` and the required exploration/validation warning. A
  persistent `Example values / ค่าตัวอย่าง` disclosure identifies the source.
  Blank/custom starters are not labeled as examples and do not claim example
  validation identity.
- Multilane blank/custom Estimated-FFS inputs explicitly contain access-point
  density `0` with helper text. Clearing the field remains a validation error;
  it is never silently coerced to zero.
- Two-Lane horizontal-curve editing is structured (type, length,
  superelevation, radius, central angle, and horizontal class) with qualified
  setup/generation interactions. Raw JSON editing is not part of the normal
  workflow; JSON remains an API persistence format only.
- Weaving puts geometry, image, movements, FFS, and heavy-vehicle inputs in the
  primary path. Advanced geometry/evidence is progressively disclosed and
  includes flags, reachable lanes, NWL, lane-change inputs, and LC. One-sided
  NWL 2/3 selects the one-sided reference and two-sided selects the two-sided
  reference through the existing Python `get_weaving_diagram_subtype()`
  semantics.
- Results are presented first with method/chapter/scope/project/state context,
  explicit current/stale/warning/handoff/capacity-failure states, answer/LOS
  where valid, metrics, warnings, schematic/evidence, assumptions, and audit
  data.
  There is one primary action at a time: Save/Add to Project is primary for a
  current quick-analysis result, Export is grouped, and a stale result makes
  Recalculate primary while explaining why Export is unavailable. Validation
  summaries link to and focus the corresponding field.
- English/Thai catalog parity, responsive layout, and narrow-screen overflow
  are covered by browser tests and committed visual evidence.

## Qualified engineering assets

The rebuilt UI serves one packaged source of truth from `src/hcmcalc/ui/assets`
through FastAPI; React does not maintain a second engineering asset set.

- Two-Lane: `two_lane/passing_constrained.png`, `passing_zone.png`, and
  `passing_lane.png`, shown before calculation with bilingual title/caption,
  applicable length/unit/type/alignment/grade facts, and accessible image text.
- Weaving: `weaving/one_sided_weave.png` and `two_sided_weave.png`, shown
  before calculation with N/NWL, entry/exit, LC, FF/FR/RF/RR legend, and the
  conceptual geometry note.
- Merge/Diverge: existing detailed `ramp_influence/merge_right_on_ramp.svg`
  and `ramp_influence/diverge_right_off_ramp.svg`, shown with vF/vR/vFO, LA/LD, and the
  influence-area/conceptual meaning.

No deleted `.agent/` or `mockups/` content was recovered or reconstructed.
Visual evidence below is generated from the accepted rebuilt UI and the
existing qualified asset set.

## Project v2 and compatibility closure

Canonical Project v2 normalization now covers all seven methods. Legacy 1.x
imports preserve method/input/result identity and retain a current result only
when stored identity and fingerprints match. Import, compare, save, and export
do not silently rerun an HCM engine. Current/stale fingerprints remain the
source of truth; method switching cannot mutate a project scenario's method.
Streamlit remains runnable and is qualified as the compatibility path.

## Browser/UAT and deterministic visual evidence

The final serial Chromium gate includes the shared Phase 2 representative
journeys, all seven registered-method journeys, consolidated remediation
journeys, and the whole-product workstation UAT. The final run was:

```text
pnpm --dir frontend exec playwright test --project=chromium --workers=1 --reporter=line
30 passed
```

The pass covers direct routes and chooser navigation; browser Back/Forward and
dirty-draft protection; structured curves and Two-Lane schematics; both
Weaving variants and progressive disclosure; Merge/Diverge SVG evidence;
method-specific Basic Freeway and Weaving capacity failures; ordinary,
warning-only, and capacity Merge/Diverge states; Multilane density semantics;
current/stale/keyboard Export states; Project master-detail, duplicate,
rename, edit, calculate, and compare; EN/TH persistence; and 1920, 1366, 1024,
and 390 px layout checks without global horizontal overflow.

The whole-product captures were visually reviewed for clipping, global
overflow, reverse result flow, hierarchy, action competition, focus recovery,
Thai rendering, and developer-facing language:

- [Home, English, 1920 px](visual-reference/phase3-ux-home-en-1920.png)
- [Home, Thai, 1920 px](visual-reference/phase3-ux-home-th-1920.png)
- [New Analysis chooser, 1920 px](visual-reference/phase3-ux-new-analysis-1920.png)
- [Method Guide, 1920 px](visual-reference/phase3-ux-method-guide-1920.png)
- [segment workbench, 1920 px](visual-reference/phase3-ux-workbench-1920.png)
- [segment workbench, 1366 px](visual-reference/phase3-ux-workbench-1366.png)
- [stacked workbench, 1024 px](visual-reference/phase3-ux-workbench-stacked-1024.png)
- [validation focus recovery](visual-reference/phase3-ux-validation-recovery.png)
- [retained stale result](visual-reference/phase3-ux-stale-result.png)
- [keyboard Export menu](visual-reference/phase3-ux-export-menu.png)
- [Two-Lane Facility grid and result, 1366 px](visual-reference/phase3-ux-facility-1366.png)
- [Two-Lane structured curve editor](visual-reference/phase3-ux-two-lane-curve.png)
- [Weaving geometry/evidence, 1366 px](visual-reference/phase3-ux-weaving-1366.png)
- [Merge warning state](visual-reference/phase3-ux-merge-warning.png)
- [Diverge capacity state](visual-reference/phase3-ux-diverge-capacity.png)
- [empty Project Workspace](visual-reference/phase3-ux-project-empty.png)
- [populated Project Workspace](visual-reference/phase3-ux-project-populated.png)
- [Project comparison](visual-reference/phase3-ux-project-compare.png)
- [390 px method navigation](visual-reference/phase3-ux-mobile-navigation-390.png)

The pre-existing Phase 2 and method-specific Phase 3 captures remain committed
separately; none is replaced by deleted historical mockups.

## Packaging and runtime qualification

- Editable install: `python -m pip install -e ".[dev,ui]"` passed.
- The production `frontend/dist` bundle was synchronized into
  `src/hcmcalc/ui/static` before the wheel build. The package entrypoint and
  its two hashed React assets are therefore current without Node/Vite at
  runtime.
- Fresh wheel: `hcm_calculator-0.9.0-py3-none-any.whl`, 1,986,776 bytes,
  SHA-256
  `1e934b418cf26dc0a0e749b0c2a867adf42fde2e6a0e57456c452a15cf9aa6dc`.
  Its compiled-SPA entries are `index.html`, `index-CMd6T3Zt.css`, and
  `index-BC_o5WcY.js`, alongside the required packaged engineering assets.
- A fresh isolated Python 3.12 wheel runtime served `/` with HTTP 200, the
  current packaged bundle, health `ok`, seven methods, and a packaged Weaving
  image from a loopback-only API.
- The actual `run_app.ps1` Windows launcher served `/` with HTTP 200, health
  `ok`, and seven methods. Its process tree was stopped after the smoke and
  no HCM release process remained.
- The actual `run_streamlit.ps1` launcher returned `/_stcore/health` 200/`ok`
  and its process tree was stopped after the compatibility smoke.
- Normal installed use runs the compiled React shell from Python/FastAPI and
  does not require a Node/Vite runtime server.

## Final gate record

| Gate | Command / evidence | Result |
| --- | --- | --- |
| Python install | `python -m pip install -e ".[dev,ui]"` | PASS |
| Python regression | `python -m pytest` | **1,158 passed** |
| Application/API | `python -m pytest tests/application tests/api` | **89 passed** |
| Compile | `python -m compileall -q src tests` | PASS |
| Workflow | v1.4.1 reference plus eight CRLF-normalized managed-file SHA-256 checks against `7a33ff3` | PASS |
| OpenAPI | `python scripts/check_openapi_contract.py` | PASS; snapshot matches |
| Generated API types | `pnpm --dir frontend run generate:api` then `git diff --exit-code -- frontend/src/api/openapi.d.ts` | PASS |
| Diff hygiene | `git diff --check` | PASS |
| Frontend types | `pnpm --dir frontend run typecheck` | PASS |
| Frontend units | `pnpm --dir frontend run test` | **17 passed** across 7 files |
| Frontend build | `pnpm --dir frontend run build` | PASS; Vite emitted 359.83 kB JS / 36.58 kB CSS |
| Browser/UAT | `pnpm --dir frontend exec playwright test --project=chromium --workers=1 --reporter=line` | **30 passed** |
| Packaged SPA resource test | `python -m pytest tests/unit/test_package_assets.py` | **3 passed** |
| Wheel | fresh wheel to the temporary release-qualification directory | PASS; SHA above |
| Installed runtime | fresh isolated-wheel HTTP smoke | PASS; current root bundle, health, methods, and engineering asset |
| Windows rebuilt launcher | `run_app.ps1` live smoke | PASS; root HTTP 200, health `ok`, seven methods |
| Streamlit compatibility | `run_streamlit.ps1` live health smoke | PASS; `/_stcore/health` 200/`ok` |
| CI | PR #141 GitHub Actions `R1 qualification` workflow | Required after the final remediation commit and push; the PR body/final evidence records the exact green run |

The release candidate preserves Python numerical authority, qualified engine
behavior, method identifiers/contracts, Project v2/fingerprint semantics,
handoff versus capacity distinctions, no-rerun imports/exports/compare, and
Streamlit compatibility. It does not claim methodology or scope expansion.
