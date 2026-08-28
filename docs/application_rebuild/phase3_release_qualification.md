# Phase 3 — Full Migration & Release Qualification

Status: implementation candidate on `codex/application-rebuild-phase-3-release`;
final review is pending the Phase 3 PR and ChatGPT acceptance.

This record is the release evidence index for Issue #139. The accepted Phase 2
base is `868c00616b6cb3b74308777c4753e1af80bb863e`; the Phase 3 branch started
from main `da64a662094458738f8c9cae7213bcf04a6f5007` in the repository
`D:\R&D\hcm-calculator`.

## Migration order and delivered identities

The five remaining methods use the same application boundary as the two Phase
2 representatives. The Python adapter/engine is authoritative; the React form
is metadata-driven and contains no HCM equations.

Preflight record: the worktree was clean after the owner-authorized, path-scoped
cleanup; local `main` was fast-forwarded only to `da64a662094458738f8c9cae7213bcf04a6f5007`; and the Phase 3 branch was created in the same
repository. The existing unrelated prunable worktree registrations were left
untouched.

| Order | `method_id` | Engine result identity | Application input contract | Project type |
| --- | --- | --- | --- | --- |
| 1 | `two_lane_segment` | `hcm7_ch15_two_lane_motorized` | `phase_5_product_integration` | `manual_single_segment` |
| 2 | `basic_freeway_segment` | `hcm7_basic_freeway_segment` | `phase_10_product_integration` | `manual_basic_freeway_v0` |
| 3 | `weaving_segment` | `hcm7_v70_freeway_weaving_segment` | `hcm_7_0_weaving_segment_operational_v1` | `manual_freeway_weaving_segment_v1` |
| 4 | `merge_segment` | `hcm7_v70_freeway_merge_segment` | `hcm7_v70_chapter_14_isolated_right_side_one_lane_merge_operational` | `manual_freeway_merge_segment_v1` |
| 5 | `diverge_segment` | `hcm7_v70_freeway_diverge_segment` | `hcm7_v70_chapter_14_isolated_right_side_one_lane_diverge_operational` | `manual_freeway_diverge_segment_v1` |

The frontend registry now reports all seven registered methods as delivered and
requires an exact backend input-contract match before enabling Select method.
The existing Multilane and Two-Lane Facility contracts remain unchanged.

## Acceptance evidence

1. Two-Lane Segment uses the existing Chapter 15 adapter and supports the
   straight/curve worksheet, template starters, units, audit evidence, and
   current-result exports.
2. Basic Freeway Segment uses the existing Chapter 12 adapter and preserves
   measured/estimated FFS, PCE provenance, SAF/CAF, and driver-population
   branches.
3. Weaving uses explicit one-sided/two-sided geometry, movement flows, and the
   existing HCM 7.0 engine. Long-segment `LS >= LMAX` is a handoff with no LOS
   assignment; above-capacity is a separate LOS F/capacity-failure state.
4. Merge and Diverge use the existing isolated right-side one-lane Chapter 14
   adapters and engines, with explicit acceleration/deceleration geometry
   evidence and separate freeway/ramp demand factors.
5. Project v2 canonical normalization covers all seven methods. Legacy 1.x
   imports retain a current result only when stored identity/fingerprints match;
   import, compare, and export never run an HCM engine.
6. English/Thai keys are kept in parity. Metric/Imperial values are converted
   at the application boundary and do not change engine authority.

## Browser and visual evidence

`frontend/playwright/phase3.spec.ts` covers the all-seven actionability count,
one calculate/result journey for each remaining method, geometry evidence, and
the weaving handoff state. The committed screenshots below are captured from
the rebuilt React UI served by the Python API; they are deterministic release
evidence, not recreated historical mockups:

- [Two-Lane Segment result](visual-reference/phase3-two_lane_segment-result.png)
- [Basic Freeway Segment result](visual-reference/phase3-basic_freeway_segment-result.png)
- [Weaving Segment result and geometry evidence](visual-reference/phase3-weaving_segment-result.png)
- [Merge Segment result and geometry evidence](visual-reference/phase3-merge_segment-result.png)
- [Diverge Segment result and geometry evidence](visual-reference/phase3-diverge_segment-result.png)

The pre-existing Phase 2 visual set remains separate and is not replaced by
these Phase 3 captures.

## Runtime and packaging

`run_app.ps1` and `run_app.bat` launch `python -m hcmcalc.api.main
--open-browser`, which serves the compiled SPA from the repository distribution
or the package fallback at `hcmcalc/ui/static`. Normal installed use therefore
has no Node/Vite runtime requirement. `run_streamlit.ps1` and
`run_streamlit.bat` retain an explicit legacy Streamlit compatibility path.

The wheel build includes `hcmcalc/ui/static` through the packaged Python
module tree. The release smoke must verify that the wheel contains
`index.html`, that the installed API serves `/`, and that `/api/v1/health` and
`/api/v1/methods` remain available from the same loopback origin.

## Command evidence

Observed final results:

- `python -m pytest`: **1,147 passed**.
- `python scripts/check_openapi_contract.py`: snapshot matches FastAPI.
- `pnpm --dir frontend run test`: **16 passed** across 7 files.
- `pnpm --dir frontend run typecheck`: passed.
- `pnpm --dir frontend run build`: passed; Vite emitted 309.14 kB JS and
  22.02 kB CSS.
- `pnpm --dir frontend run test:e2e`: **11 passed**.
- Wheel build: passed; the wheel contains `hcmcalc/ui/static/index.html` and
  the compiled assets. Installed-wheel HTTP smoke returned root/assets 200,
  health `ok`, and 7 methods. Streamlit compatibility health smoke returned
  200 / `ok`.
- `git diff --check`: passed.

The final PR description records the exact commands for:

- `python -m pytest`
- `python scripts/check_openapi_contract.py`
- `pnpm --dir frontend run test`
- `pnpm --dir frontend run typecheck`
- `pnpm --dir frontend run build`
- `pnpm --dir frontend run test:e2e`
- wheel contents and installed-wheel HTTP smoke
- `git diff --check`

Issue #139 is closed by the reviewable Phase 3 PR only after these gates pass;
the PR is intentionally not merged by the implementation task.
