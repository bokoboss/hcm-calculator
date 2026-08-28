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
  explicit current/stale/handoff/capacity-failure states, answer/LOS where
  valid, metrics, warnings, schematic/evidence, assumptions, and audit data.
  There is one primary action at a time; Save is primary for a current result,
  Recalculate is secondary, and Export is grouped. Stale exports are disabled
  with a reason until recalculation. Validation summaries link to and focus the
  corresponding field.
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
- Merge/Diverge: existing detailed `ramps/merge_right_on_ramp.svg` and
  `ramps/diverge_right_off_ramp.svg`, shown with vF/vR/vFO, LA/LD, and the
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

The full Chromium gate includes the shared Phase 2 representative journeys,
the existing Phase 3 all-method journeys, and the consolidated remediation
journeys. The final run was:

```text
pnpm --dir frontend exec playwright test --project=chromium
18 passed
```

The remediation coverage includes direct routes and chooser navigation,
modified-draft protection, structured curves and Two-Lane schematics, both
Weaving variants and disclosure, Merge/Diverge SVG evidence, Multilane density
semantics, current/stale/export states, Thai, and a 390px responsive viewport.

Committed deterministic captures:

- [desktop persistent navigation](visual-reference/phase3-remediation-desktop-navigation.png)
- [Two-Lane passing schematic](visual-reference/phase3-remediation-two-lane-passing-schematic.png)
- [Two-Lane structured curve editor](visual-reference/phase3-remediation-two-lane-curve-editor.png)
- [Weaving one-sided reference](visual-reference/phase3-remediation-weaving-one-sided.png)
- [Weaving two-sided reference](visual-reference/phase3-remediation-weaving-two-sided.png)
- [Merge detailed SVG result](visual-reference/phase3-remediation-merge_segment-detailed-svg.png)
- [Diverge detailed SVG result](visual-reference/phase3-remediation-diverge_segment-detailed-svg.png)
- [current result actions](visual-reference/phase3-remediation-current-result.png)
- [stale result recovery](visual-reference/phase3-remediation-stale-result.png)
- [Thai result](visual-reference/phase3-remediation-thai-result.png)
- [narrow navigation](visual-reference/phase3-remediation-narrow-navigation.png)

The pre-existing Phase 2 visual set and the five Phase 3 result captures remain
committed separately; none is replaced by deleted historical mockups.

## Packaging and runtime qualification

- Editable install: `python -m pip install -e ".[dev,ui]"` passed.
- Fresh wheel: `hcm_calculator-0.9.0-py3-none-any.whl`,
  1,972,308 bytes, SHA-256
  `ab19a8eeac2d73b61328d4f0617a282ca919dae8069f4963af1f900de1809070`.
  The archive contains `hcmcalc/ui/static/index.html` and the required
  Two-Lane, Weaving, Merge, and Diverge engineering assets.
- Isolated Python 3.12 wheel runtime served `/` with HTTP 200, health `ok`,
  seven methods, and the packaged assets from a loopback-only API.
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
| Python regression | `python -m pytest` | **1,151 passed** |
| Compile | `python -m compileall -q src tests` | PASS |
| Workflow | v1.4.1 manifest and eight managed-file CRLF-normalized SHA-256 checks | PASS |
| OpenAPI | `python scripts/check_openapi_contract.py` | PASS; snapshot matches |
| Diff hygiene | `git diff --check` | PASS |
| Frontend types | `pnpm --dir frontend run typecheck` | PASS |
| Frontend units | `pnpm --dir frontend run test` | **17 passed** across 7 files |
| Frontend build | `pnpm --dir frontend run build` | PASS; Vite emitted 334.32 kB JS / 26.19 kB CSS |
| Browser/UAT | `pnpm --dir frontend exec playwright test --project=chromium` | **18 passed** |
| Wheel | `python -m build --wheel --outdir .tmp\phase3-wheel` | PASS; SHA above |
| Installed runtime | isolated wheel HTTP smoke | PASS; root/health/methods/assets |
| Windows rebuilt launcher | `run_app.ps1` live smoke | PASS |
| Streamlit compatibility | `run_streamlit.ps1` live health smoke | PASS |
| CI | PR #141 GitHub Actions `Tests` workflow | required to be green before acceptance; final check links are on the PR |

The release candidate preserves Python numerical authority, qualified engine
behavior, method identifiers/contracts, Project v2/fingerprint semantics,
handoff versus capacity distinctions, no-rerun imports/exports/compare, and
Streamlit compatibility. It does not claim methodology or scope expansion.
