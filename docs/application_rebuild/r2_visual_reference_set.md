# Phase 2 visual reference set

The release-like browser suite captures six deterministic reference views for
the rebuilt application:

- `01-home.png` — Home / entry surface;
- `02-new-analysis.png` — analysis selection with delivered/reference status;
- `03-multilane-result.png` — calculated Multilane result hierarchy;
- `04-facility-grid.png` — bounded Two-Lane Facility engineering grid;
- `05-facility-result.png` — facility answer with segment evidence;
- `06-project-compare.png` — Project v2 scenario comparison.

Run the capture with:

```powershell
pnpm --dir frontend test:e2e -- phase2.visual.spec.ts
```

The current captures are written to the ignored `.agent-work/visual-reference`
directory. The Project view masks its timestamp and generated identifier so
the layout and engineering content remain comparable across runs.
