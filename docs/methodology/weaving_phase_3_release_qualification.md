# Phase 13.3 — product integration release qualification

## Baseline and product boundary

- Starting `main`: `253a17eb5541acd891bcf92b6c1b2106b57c28ad`.
- Navigation: **Weaving Segment** / `ช่วงทางด่วนแบบสานกระแส`.
- Public calculation boundary: `WeavingSegmentMethod(version="hcm_7_0").calculate(inputs)`.
- Project identity: `manual_freeway_weaving_segment_v1`; method family
  `weaving_segment`; method version `hcm_7_0`; contract
  `hcm_7_0_weaving_segment_operational_v1`.

## Release checks

- Adapter tests cover one-/two-sided inputs, Metric/Imperial equivalence,
  geometry provenance/inactive field clearing, and HCM 7.1 rejection.
- Project tests cover current and stale load behavior, version identity, and
  null preservation. The normalized-input fingerprint includes method,
  contract, geometry, movements, FFS path, heavy vehicles, and provenance; it
  excludes presentation locale and display units.
- CSV, Excel, Markdown, and JSON reports are generated from the stored engine
  result. Excel structure is inspected; handoff and above-capacity null values
  are retained.
- Reference presets reproduce qualified Chapter 27 Examples 1-3. No licensed
  HCM/HCS text, screenshots, templates, diagrams, or OCR output is committed.
- Product smoke checks cover the Streamlit Weaving Segment route, the default
  HCM 7.0 calculation, stale-result withholding after an input change, and a
  real Streamlit HTTP 200 response.

## Release evidence

- `python -m pytest tests/unit/test_manual_weaving.py tests/unit/test_streamlit_app.py tests/unit/test_project_io.py tests/unit/test_reporting.py -q`:
  112 passed.
- `python -m pytest -q` in the local development environment: 906 passed,
  1 skipped.
- Clean Python 3.12 temporary virtual environment with `pip install -e .[dev,ui]`
  followed by `python -m pytest -q`: 907 passed.
- `streamlit.testing.v1.AppTest` Weaving Segment smoke: default calculation
  renders LOS metrics; editing `FF (veh/h)` marks the result stale and withholds
  result metrics/exports until recalculation.
- `python -m streamlit run src/hcmcalc/ui/streamlit_app.py --server.headless=true`
  on a temporary local port returned HTTP 200.

## Release decision

The implementation is qualified only for the bounded HCM 7.0 freeway scope
documented in the Phase 1/2 records. HCM 7.1 and all listed exclusions remain
hard guards, not silently downgraded modes. Diff hygiene, publishing, PR, and CI
evidence are recorded with the release PR.
