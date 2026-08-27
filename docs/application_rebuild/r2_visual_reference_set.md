# Phase 2 visual reference set

The release-like browser suite captures these committed, deterministic views
for reviewer inspection:

- `01-home-desktop.png` — Home / entry surface;
- `02-new-analysis-desktop.png` — delivered and reference-only method status;
- `03-multilane-input.png` — Multilane engineering worksheet;
- `04-multilane-result.png` — calculated Multilane result hierarchy;
- `05-multilane-stale.png` — stale-result protection;
- `06-multilane-capacity-failure.png` — capacity failure and unavailable metrics;
- `07-facility-grid.png` — metric Two-Lane Facility engineering grid;
- `08-facility-validation.png` — invalid PHF validation state;
- `09-facility-result.png` — facility answer with segment evidence;
- `10-project-v2-overview.png` — saved Project v2 overview;
- `11-project-compare.png` — current Project v2 scenario comparison;
- `12-narrow-analysis.png` — narrow Multilane worksheet containment;
- `13-narrow-facility-grid.png` — narrow facility table scroll boundary;
- `14-thai-multilane-result.png` — Thai Multilane result;
- `15-thai-facility-result.png` — Thai facility result.

Run the capture with:

```powershell
pnpm --dir frontend test:e2e -- phase2.visual.spec.ts
```

The PNGs are written to the committed
`docs/application_rebuild/visual-reference` directory. Project screenshots
mask generated timestamps and identifiers so the layout and engineering
content remain comparable across runs. The visual set is evidence only; the
Python engine and API contract remain the calculation authority.
