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

The two-lane facility entry has its own application method identity and input
contract even though the existing qualified engine uses a shared Chapter 15
calculation implementation. This keeps the application registry explicit and
does not alter numerical engine behavior.

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
