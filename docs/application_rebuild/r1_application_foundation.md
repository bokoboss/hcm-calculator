# R1 Application Foundation

R1 establishes the rebuilt HCM workspace boundary without moving any
calculation workflow into React.

## Runtime boundary

```text
React + TypeScript + Vite (build-time only)
        │ same-origin JSON / local HTTP
        ▼
FastAPI boundary (`hcmcalc.api`)
        │
        ▼
framework-independent application contracts (`hcmcalc.application`)
        │
        ▼
qualified Python HCM engines and the existing Streamlit application
```

`hcmcalc.application` has no FastAPI, Streamlit, React, or browser imports.
The FastAPI package is a thin adapter that exposes health and language-neutral
method metadata. R1 does not expose a calculation endpoint and does not make a
rebuilt method workflow actionable.

## Application contracts

- `hcmcalc.application.registry` is the backend-authoritative registry for all
  seven current engineering methods: two-lane segment, two-lane facility,
  multilane segment, basic freeway segment, weaving, merge, and diverge.
- `hcmcalc.application.workflow_state` is the canonical home for the existing
  fingerprint/current/stale contract. The legacy `hcmcalc.ui.workflow_state`
  module re-exports it to preserve existing imports and behavior.
- `hcmcalc.application.contracts` carries method/input identity and result
  presentation state without coupling to a UI.
- `hcmcalc.application.interpretation` provides stable, language-neutral
  interpretation codes. Localized prose remains in the presentation layer.

The registry keeps the accepted project/fingerprint identity in
`method_identifier` and `input_contract`. `engine_method_identifier` records
the qualified engine/result identity separately where a legacy adapter uses a
method family or a workflow identity at the persistence boundary. `project_type`
records the current compatible project format. This is an evidence-backed
identity mapping, not a new calculation contract.

### R1 authority matrix

The following matrix is derived from the qualified engine facades, manual
adapters, `hcmcalc.ui.project_io`, and the supported-method documentation.
The frontend module contract is not a second authority in R1: when a module is
eventually delivered, its `moduleContract` must equal the backend
`input_contract` before the method can become actionable. R1 delivers no such
module.

| `method_id` | Public/engine method identity | Persistence/fingerprint identity | Input contract | Current `project_type` | R1 frontend/application module contract |
| --- | --- | --- | --- | --- | --- |
| `two_lane_segment` | `hcm7_ch15_two_lane_motorized` | `method_identifier=hcm7_two_lane_highway_segment` | `phase_5_product_integration` | `manual_single_segment` | No delivered module; future `moduleContract` must match `phase_5_product_integration` |
| `two_lane_facility` | `hcm7_ch15_two_lane_motorized` (shared Chapter 15 engine facade) | `method_identifier=hcm7_two_lane_highway_facility` | `phase_5_product_integration` | `manual_two_lane_facility_v1` (legacy `manual_facility_v0` remains load-compatible) | No delivered module; future `moduleContract` must match `phase_5_product_integration` |
| `multilane_segment` | `hcm7_multilane_los` | `method_identifier=hcm7_multilane_los` | `phase_8` | `manual_multilane_v0` | No delivered module; future `moduleContract` must match `phase_8` |
| `basic_freeway_segment` | `hcm7_basic_freeway_segment` | `method_identifier=hcm7_basic_freeway_segment` | `phase_10_product_integration` | `manual_basic_freeway_v0` | No delivered module; future `moduleContract` must match `phase_10_product_integration` |
| `weaving_segment` | `hcm7_v70_freeway_weaving_segment` (`hcm_7_0`) | `method_family=weaving_segment` | `hcm_7_0_weaving_segment_operational_v1` | `manual_freeway_weaving_segment_v1` | No delivered module; future `moduleContract` must match `hcm_7_0_weaving_segment_operational_v1` |
| `merge_segment` | `hcm7_v70_freeway_merge_segment` (`hcm_7_0`) | `method_family=merge_segment` | `hcm7_v70_chapter_14_isolated_right_side_one_lane_merge_operational` | `manual_freeway_merge_segment_v1` | No delivered module; future `moduleContract` must match the Chapter 14 merge contract |
| `diverge_segment` | `hcm7_v70_freeway_diverge_segment` (`hcm_7_0`) | `method_family=diverge_segment` | `hcm7_v70_chapter_14_isolated_right_side_one_lane_diverge_operational` | `manual_freeway_diverge_segment_v1` | No delivered module; future `moduleContract` must match the Chapter 14 diverge contract |

The engine method names and result payload details remain unchanged. Existing
schema 1.2 project files and v0.9 fingerprints continue to use their original
method/fingerprint identities.

## API

The local API is loopback-bound by default at `127.0.0.1:8765`:

- `GET /api/v1/health`
- `GET /api/v1/methods`
- `GET /api/v1/methods/{method_id}`

There is no wildcard CORS configuration. Development CORS is an explicit
allowlist parameter, and the structured 404 error envelope is part of the
OpenAPI contract. `scripts/check_openapi_contract.py` verifies the checked-in
`frontend/src/api/openapi.json` snapshot.

## Frontend delivery handshake

`frontend/src/registry/modules.ts` is intentionally separate from the backend
registry. A method becomes actionable only when both engineering availability
and a delivered frontend module with a matching input contract are true. R1
registers all seven methods as `not_delivered`, so the rebuilt UI exposes
reference metadata only. The existing Streamlit workflows remain the active
legacy application surface during migration.

The shared shell includes the R0 header/sidebar/main/status geometry, semantic
form/result primitives, keyboard focus treatment, reduced-motion handling, and
English/Thai catalog-backed labels. No Recent Projects persistence or database
is introduced.

## Release-like qualification

From a clean checkout:

```powershell
python -m pip install -e .[dev]
python scripts/check_openapi_contract.py
pnpm --dir frontend install --frozen-lockfile --ignore-scripts
pnpm --dir frontend run generate:api
pnpm --dir frontend run typecheck
pnpm --dir frontend run test
pnpm --dir frontend run build
pnpm --dir frontend exec playwright install chromium
pnpm --dir frontend run test:e2e
```

The browser configuration starts `python -m hcmcalc.api.main` with
`--static-dir frontend/dist`. The compiled SPA and `/api/v1/*` therefore share
one loopback origin, and the browser smoke does not require a Node/Vite server
at runtime.
